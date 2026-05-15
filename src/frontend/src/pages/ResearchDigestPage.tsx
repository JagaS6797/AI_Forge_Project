import { useCallback, useRef, useState } from "react";

import { streamResearchDigest } from "../lib/api";
import type { ResearchDigestDonePayload, ResearchPaper } from "../types";

type Phase =
  | "idle"
  | "searching"
  | "evaluating"
  | "generating"
  | "done"
  | "error";

interface StatusMessage {
  step: number;
  message: string;
}

interface DigestSection {
  title: string;
  content: string;
}

function getPhaseLabel(phase: Phase): string {
  switch (phase) {
    case "searching":
      return "Searching";
    case "evaluating":
      return "Evaluating";
    case "generating":
      return "Writing";
    case "done":
      return "Completed";
    case "error":
      return "Error";
    default:
      return "Idle";
  }
}

function getPhaseClasses(phase: Phase): string {
  switch (phase) {
    case "done":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case "error":
      return "bg-red-100 text-red-700 border-red-200";
    case "searching":
    case "evaluating":
    case "generating":
      return "bg-violet-100 text-violet-700 border-violet-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function parseDigestSections(markdown: string): DigestSection[] {
  const normalized = markdown.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];

  const chunks = normalized.split(/\n##\s+/);
  const sections: DigestSection[] = [];

  for (let i = 0; i < chunks.length; i += 1) {
    const chunk = i === 0 ? chunks[i] : `## ${chunks[i]}`;
    if (!chunk.trim()) continue;

    const lines = chunk.split("\n");
    const heading = lines[0].replace(/^##\s*/, "").trim() || "Summary";
    const content = lines.slice(1).join("\n").trim();
    if (!content) continue;

    sections.push({ title: heading, content });
  }

  return sections;
}

export default function ResearchDigestPage() {
  const [topic, setTopic] = useState("");
  const [maxPapers, setMaxPapers] = useState(5);
  const [phase, setPhase] = useState<Phase>("idle");
  const [statusMessages, setStatusMessages] = useState<StatusMessage[]>([]);
  const [streamedDigest, setStreamedDigest] = useState("");
  const [finalResult, setFinalResult] = useState<ResearchDigestDonePayload | null>(null);
  const [selectedPapers, setSelectedPapers] = useState<ResearchPaper[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const addStatus = useCallback((step: number, message: string) => {
    setStatusMessages((prev) => {
      // Replace if same step exists, otherwise append
      const exists = prev.findIndex((s) => s.step === step);
      if (exists !== -1) {
        const updated = [...prev];
        updated[exists] = { step, message };
        return updated;
      }
      return [...prev, { step, message }];
    });
  }, []);

  const handleResearch = useCallback(async () => {
    if (!topic.trim()) return;

    // Reset state
    setPhase("searching");
    setStatusMessages([]);
    setStreamedDigest("");
    setFinalResult(null);
    setSelectedPapers([]);
    setErrorMessage(null);

    abortRef.current = new AbortController();

    try {
      await streamResearchDigest(
        topic.trim(),
        maxPapers,
        (eventName, data) => {
          switch (eventName) {
            case "status": {
              const step = (data.step as number) ?? 0;
              const message = (data.message as string) ?? "";
              addStatus(step, message);
              if (step <= 2) setPhase("searching");
              else if (step <= 4) setPhase("evaluating");
              else setPhase("generating");
              break;
            }
            case "papers_found":
              addStatus(data.step as number, data.message as string);
              break;
            case "selected_papers": {
              const papers = (data.papers as ResearchPaper[]) ?? [];
              setSelectedPapers(papers);
              addStatus(data.step as number, data.message as string);
              break;
            }
            case "digest_chunk":
              setStreamedDigest((prev) => prev + ((data.token as string) ?? ""));
              break;
            case "done": {
              const payload = data as unknown as ResearchDigestDonePayload;
              setFinalResult(payload);
              setStreamedDigest(payload.digest);
              setPhase("done");
              break;
            }
            case "error":
              setErrorMessage((data.message as string) ?? "Unknown error");
              setPhase("error");
              break;
          }
        },
        abortRef.current.signal,
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setErrorMessage((err as Error).message ?? "Unexpected error");
        setPhase("error");
      }
    }
  }, [topic, maxPapers, addStatus]);

  const handleStop = () => {
    abortRef.current?.abort();
    setPhase("idle");
  };

  const handleReset = () => {
    abortRef.current?.abort();
    setTopic("");
    setMaxPapers(5);
    setPhase("idle");
    setStatusMessages([]);
    setStreamedDigest("");
    setFinalResult(null);
    setSelectedPapers([]);
    setErrorMessage(null);
  };

  const isRunning = phase === "searching" || phase === "evaluating" || phase === "generating";
  const digestSections = parseDigestSections(streamedDigest);

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div className="rounded-3xl border border-violet-100 bg-white/90 p-6 shadow-lg backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-violet-900">Research Digest Agent</h1>
              <p className="mt-1 text-sm text-violet-600">
                Enter a topic and get a live, structured digest with sources and key findings.
              </p>
            </div>
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${getPhaseClasses(phase)}`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${isRunning ? "animate-pulse bg-current" : "bg-current"}`} />
              {getPhaseLabel(phase)}
            </span>
          </div>
        </div>

        {/* Input panel */}
        <div className="rounded-3xl border border-violet-100 bg-white/90 p-6 shadow-lg backdrop-blur">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-semibold text-violet-700 uppercase tracking-wide">
                Research Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !isRunning) void handleResearch(); }}
                placeholder="e.g. transformer models for protein structure prediction"
                disabled={isRunning}
                className="w-full rounded-xl border border-violet-200 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-200 disabled:opacity-50"
              />
            </div>
            <div className="flex-shrink-0 w-28">
              <label className="mb-1 block text-xs font-semibold text-violet-700 uppercase tracking-wide">
                Max Papers
              </label>
              <select
                value={maxPapers}
                onChange={(e) => setMaxPapers(Number(e.target.value))}
                disabled={isRunning}
                className="w-full rounded-xl border border-violet-200 bg-white px-3 py-2.5 text-sm text-slate-800 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-200 disabled:opacity-50"
              >
                {[3, 4, 5, 6, 7].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              {isRunning ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="rounded-xl bg-red-500 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-red-600 transition"
                >
                  Stop
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => void handleResearch()}
                  disabled={!topic.trim()}
                  className="rounded-xl bg-violet-600 px-5 py-2.5 text-sm font-semibold text-white shadow hover:bg-violet-700 transition disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Research
                </button>
              )}
              {(phase === "done" || phase === "error") && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="rounded-xl border border-violet-300 bg-white px-5 py-2.5 text-sm font-semibold text-violet-700 shadow hover:bg-violet-50 transition"
                >
                  Reset
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Error */}
        {phase === "error" && errorMessage && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <span className="font-semibold">Error: </span>{errorMessage}
          </div>
        )}

        {/* Insight cards */}
        {(topic || selectedPapers.length > 0 || finalResult) && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-violet-100 bg-white/90 p-4 shadow-sm">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-violet-500">Topic</p>
              <p className="mt-1 line-clamp-2 text-sm font-medium text-slate-700">
                {topic || "Not set"}
              </p>
            </div>
            <div className="rounded-2xl border border-violet-100 bg-white/90 p-4 shadow-sm">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-violet-500">Papers</p>
              <p className="mt-1 text-sm font-medium text-slate-700">
                {finalResult ? finalResult.papers_found : selectedPapers.length}
              </p>
            </div>
            <div className="rounded-2xl border border-violet-100 bg-white/90 p-4 shadow-sm">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-violet-500">Updated</p>
              <p className="mt-1 text-sm font-medium text-slate-700">
                {finalResult ? new Date(finalResult.generated_at).toLocaleString() : "In progress"}
              </p>
            </div>
          </div>
        )}

        {/* Progress steps */}
        {statusMessages.length > 0 && (
          <div className="rounded-3xl border border-violet-100 bg-white/90 p-5 shadow backdrop-blur">
            <h2 className="mb-3 text-xs font-semibold text-violet-700 uppercase tracking-wide">Progress</h2>
            <ul className="space-y-2">
              {[...statusMessages].sort((a, b) => a.step - b.step).map((s, idx, arr) => (
                <li key={s.step} className="flex items-start gap-3">
                  <div className="flex flex-col items-center">
                    <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-violet-100 text-[10px] font-bold text-violet-700">
                      {s.step}
                    </span>
                    {idx < arr.length - 1 && <span className="mt-1 h-4 w-px bg-violet-200" />}
                  </div>
                  <span className="text-sm text-slate-700">{s.message}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Selected papers */}
        {selectedPapers.length > 0 && (
          <div className="rounded-3xl border border-violet-100 bg-white/90 p-5 shadow backdrop-blur">
            <h2 className="mb-3 text-xs font-semibold text-violet-700 uppercase tracking-wide">
              Selected Papers ({selectedPapers.length})
            </h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {selectedPapers.map((paper, i) => (
                <div key={i} className="rounded-2xl border border-violet-100 bg-violet-50 p-4">
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="line-clamp-2 text-sm font-semibold text-violet-800 hover:underline"
                  >
                    {paper.title}
                  </a>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {paper.authors.join(", ")} · {paper.published}
                  </p>
                  <p className="mt-1.5 text-xs text-slate-600 leading-relaxed">{paper.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Streaming / final digest */}
        {(streamedDigest || isRunning) && (
          <div className="rounded-3xl border border-violet-100 bg-white/90 p-6 shadow backdrop-blur">
            <h2 className="mb-3 text-xs font-semibold text-violet-700 uppercase tracking-wide">
              Research Digest
              {phase === "generating" && (
                <span className="ml-2 inline-block h-2 w-2 animate-pulse rounded-full bg-violet-500" />
              )}
            </h2>
            {streamedDigest ? digestSections.length > 0 ? (
              <div className="space-y-3">
                {digestSections.map((section, idx) => (
                  <div key={`${section.title}-${idx}`} className="rounded-2xl border border-violet-100 bg-violet-50/60 p-4">
                    <h3 className="text-sm font-semibold text-violet-900">{section.title}</h3>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{section.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="whitespace-pre-wrap text-sm text-slate-800 leading-relaxed">{streamedDigest}</div>
            ) : (
              <p className="text-sm text-slate-400 italic">Generating digest…</p>
            )}

            {finalResult && (
              <p className="mt-4 text-xs text-slate-400">
                Generated at {new Date(finalResult.generated_at).toLocaleString()} ·{" "}
                {finalResult.papers_found} papers analysed
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

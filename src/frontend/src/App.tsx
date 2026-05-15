import { useEffect, useMemo, useState } from "react";

import { ChatWindow } from "./components/chat/ChatWindow";
import {
  clearAuthToken,
  createThread,
  deleteThread,
  getAuthToken,
  getCurrentUser,
  getThreads,
  renameThread,
} from "./lib/api";
import type { AuthUser, ChatThread } from "./types";
import ChatPage from "./pages/ChatPage";
import DataFrameQueryPage from "./pages/DataFrameQueryPage";
import ResearchDigestPage from "./pages/ResearchDigestPage";
import SqlQueryPage from "./pages/SqlQueryPage";
import TicTacToePage from "./pages/TicTacToePage";

type AppView = "chat" | "project8" | "project9" | "project10" | "project11";

type ModuleInfo = {
  id: AppView;
  name: string;
  short: string;
  description: string;
  accent: string;
};

const MODULES: ModuleInfo[] = [
  {
    id: "chat",
    name: "Chat Agent",
    short: "CA",
    description: "Multi-turn assistant with thread-based memory.",
    accent: "bg-slate-900",
  },
  {
    id: "project8",
    name: "NL-SQL Agent",
    short: "NS",
    description: "Natural language to SQL query generation and execution.",
    accent: "bg-indigo-600",
  },
  {
    id: "project9",
    name: "DataFrame Agent",
    short: "DF",
    description: "CSV/Sheets exploration with DataFrame reasoning.",
    accent: "bg-emerald-600",
  },
  {
    id: "project10",
    name: "Research Agent",
    short: "RD",
    description: "Streaming research digest with progress and citations.",
    accent: "bg-violet-600",
  },
  {
    id: "project11",
    name: "Tic Tac Toe Agent",
    short: "TT",
    description: "Play Tic Tac Toe against a server-side game agent.",
    accent: "bg-amber-600",
  },
];

function getUserInitials(email?: string | null): string {
  if (!email) return "JC";

  const localPart = email.split("@")[0] ?? "";
  const tokens = localPart.split(/[^a-zA-Z]+/).filter(Boolean);
  if (tokens.length >= 2) {
    return `${tokens[0][0] ?? ""}${tokens[1][0] ?? ""}`.toUpperCase();
  }

  const letters = localPart.replace(/[^a-zA-Z]/g, "").toUpperCase();
  if (letters.length >= 2) return letters.slice(0, 2);
  if (letters.length === 1) return `${letters}C`;
  return "JC";
}

export default function App() {
  const [view, setView] = useState<AppView>("chat");
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getAuthToken()));
  const [isBootstrapping, setIsBootstrapping] = useState(Boolean(getAuthToken()));

  const [user, setUser] = useState<AuthUser | null>(null);
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

  const currentModule = useMemo(
    () => MODULES.find((module) => module.id === view) ?? MODULES[0],
    [view],
  );

  useEffect(() => {
    if (!isAuthenticated) {
      setIsBootstrapping(false);
      setUser(null);
      setThreads([]);
      setActiveThreadId(null);
      return;
    }

    let cancelled = false;
    const bootstrap = async () => {
      setIsBootstrapping(true);
      try {
        const [currentUser, existingThreads] = await Promise.all([getCurrentUser(), getThreads()]);
        if (cancelled) return;
        setUser(currentUser);
        setThreads(existingThreads);
        setActiveThreadId(existingThreads[0]?.id ?? null);
      } catch {
        if (cancelled) return;
        clearAuthToken();
        setIsAuthenticated(false);
      } finally {
        if (!cancelled) setIsBootstrapping(false);
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  const handleNewThread = async () => {
    try {
      const thread = await createThread("New Chat");
      setThreads((prev) => [thread, ...prev]);
      setActiveThreadId(thread.id);
      setView("chat");
    } catch {
      // Ignore create errors in layout controls.
    }
  };

  const handleRenameThread = async (threadId: string, name: string) => {
    try {
      const updated = await renameThread(threadId, name);
      setThreads((prev) => prev.map((t) => (t.id === threadId ? updated : t)));
    } catch {
      // Ignore rename errors in layout controls.
    }
  };

  const handleDeleteThread = async (threadId: string) => {
    try {
      await deleteThread(threadId);
      setThreads((prev) => {
        const remaining = prev.filter((t) => t.id !== threadId);
        if (activeThreadId === threadId) {
          setActiveThreadId(remaining[0]?.id ?? null);
        }
        return remaining;
      });
    } catch {
      // Ignore delete errors in layout controls.
    }
  };

  const handleThreadNamed = (threadId: string, name: string) => {
    setThreads((prev) => prev.map((t) => (t.id === threadId ? { ...t, name } : t)));
  };

  const handleLogout = () => {
    clearAuthToken();
    setIsAuthenticated(false);
    setView("chat");
  };

  if (!isAuthenticated) {
    return <ChatPage onAuthStateChange={setIsAuthenticated} />;
  }

  if (isBootstrapping) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-100">
        <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-900 border-t-transparent" />
          <span className="text-sm font-medium text-slate-700">Loading workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen overflow-hidden bg-slate-100">
      <div className="flex h-full">
        <aside className="flex w-28 shrink-0 flex-col items-center border-r border-slate-800 bg-slate-950 py-4">
          <div className="mb-5 rounded-xl bg-white px-3 py-2 text-center text-[11px] font-bold uppercase tracking-wide text-slate-900">
            Modules
          </div>
          <nav className="flex flex-1 flex-col items-center gap-2">
            {MODULES.map((module) => {
              const isActive = module.id === view;
              return (
                <button
                  key={module.id}
                  type="button"
                  onClick={() => setView(module.id)}
                  className={`w-24 rounded-xl px-2 py-3 text-center transition ${
                    isActive ? "bg-white text-slate-900 shadow" : "text-slate-300 hover:bg-slate-800"
                  }`}
                >
                  <div className={`mx-auto mb-1 flex h-7 w-7 items-center justify-center rounded-md text-[10px] font-bold text-white ${module.accent}`}>
                    {module.short}
                  </div>
                  <p className="text-[11px] font-semibold leading-tight">{module.name.replace(" Agent", "")}</p>
                </button>
              );
            })}
          </nav>
        </aside>

        {view === "chat" && (
          <aside className="flex w-80 shrink-0 flex-col border-r border-slate-300 bg-slate-200/80">
            <div className="border-b border-slate-300 px-5 py-4">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-indigo-500">Chat Submodule</p>
              <h2 className="mt-1 text-base font-semibold text-slate-900">Chat History</h2>
              <p className="mt-1 text-xs text-slate-600">Pick, rename, or delete existing conversations.</p>
            </div>

            <div className="flex min-h-0 flex-1 flex-col">
              <div className="flex items-center justify-between px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-indigo-500">Threads</p>
                <button
                  type="button"
                  onClick={() => void handleNewThread()}
                  className="rounded-md bg-slate-900 px-2.5 py-1 text-xs font-semibold text-white transition hover:bg-slate-800"
                >
                  New
                </button>
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
                {threads.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-slate-300 bg-slate-100 p-3 text-xs text-slate-500">
                    No conversations yet. Create one to begin.
                  </div>
                ) : (
                  <ul className="space-y-1">
                    {threads.map((thread) => {
                      const isActive = thread.id === activeThreadId;
                      return (
                        <li key={thread.id}>
                          <button
                            type="button"
                            onClick={() => setActiveThreadId(thread.id)}
                            className={`w-full rounded-lg px-3 py-2 text-left transition ${
                              isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                            }`}
                          >
                            <p className="truncate text-sm font-medium">{thread.name}</p>
                            <p className={`mt-0.5 text-[11px] ${isActive ? "text-slate-300" : "text-slate-500"}`}>
                              {new Date(thread.updated_at).toLocaleDateString()}
                            </p>
                          </button>
                          {isActive && (
                            <div className="mt-1 flex items-center gap-2 px-2 pb-1">
                              <button
                                type="button"
                                onClick={() => {
                                  const name = window.prompt("Rename thread", thread.name)?.trim();
                                  if (name) void handleRenameThread(thread.id, name);
                                }}
                                className="text-xs text-slate-500 transition hover:text-slate-800"
                              >
                                Rename
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleDeleteThread(thread.id)}
                                className="text-xs text-red-500 transition hover:text-red-700"
                              >
                                Delete
                              </button>
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          </aside>
        )}

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-slate-200 bg-white px-6 py-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h1 className="text-lg font-semibold text-slate-900">{currentModule.name}</h1>
                <p className="mt-1 text-sm text-slate-600">
                  {view === "chat"
                    ? "Pick a conversation from the chat history panel, or create a new one."
                    : currentModule.description}
                </p>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-2 py-1">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
                  {getUserInitials(user?.email)}
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-md px-2 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
                >
                  Logout
                </button>
              </div>
            </div>
          </header>

          <main className="min-h-0 flex-1 overflow-hidden">
            {view === "chat" ? (
              activeThreadId ? (
                <ChatWindow threadId={activeThreadId} onThreadNamed={handleThreadNamed} />
              ) : (
                <div className="flex h-full items-center justify-center bg-slate-50">
                  <div className="rounded-2xl border border-slate-200 bg-white px-6 py-5 text-center shadow-sm">
                    <p className="text-sm font-medium text-slate-700">No active conversation selected</p>
                    <p className="mt-1 text-xs text-slate-500">Create or choose a thread from Chat History.</p>
                  </div>
                </div>
              )
            ) : view === "project8" ? (
              <SqlQueryPage />
            ) : view === "project9" ? (
              <DataFrameQueryPage />
            ) : view === "project10" ? (
              <ResearchDigestPage />
            ) : (
              <TicTacToePage />
            )}
          </main>
        </section>
      </div>
    </div>
  );
}

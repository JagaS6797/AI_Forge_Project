import { useMemo, useState } from "react";

import { askDatabaseQuestion } from "../lib/api";
import type { SqlQueryResult } from "../types";

function displayCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export default function SqlQueryPage() {
  const [question, setQuestion] = useState("");
  const [maxRows, setMaxRows] = useState(50);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SqlQueryResult | null>(null);

  const columns = useMemo(() => result?.columns ?? [], [result]);

  const handleRun = async () => {
    const trimmed = question.trim();
    if (!trimmed) {
      setError("Please enter a natural language question.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await askDatabaseQuestion(trimmed, maxRows);
      setResult(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to run query.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-5">
        <header className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">Ask Database in Natural Language</h1>
          <p className="mt-2 text-sm text-slate-600">
            Enter a question, inspect the generated SQL, and review the response data from your Supabase PostgreSQL tables.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <label className="mb-2 block text-sm font-medium text-slate-700">Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Example: what is the email of the name jagadesh"
            className="min-h-28 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
          />

          <div className="mt-4 flex flex-wrap items-end gap-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Max rows</label>
              <input
                type="number"
                min={1}
                max={200}
                value={maxRows}
                onChange={(e) => setMaxRows(Math.max(1, Math.min(200, Number(e.target.value) || 1)))}
                className="w-28 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              />
            </div>

            <button
              type="button"
              onClick={handleRun}
              disabled={isLoading}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? "Running..." : "Generate SQL + Run"}
            </button>
          </div>

          {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        </section>

        {result && (
          <>
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Generated SQL</h2>
              <pre className="mt-3 overflow-x-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">{result.generated_sql}</pre>
              <p className="mt-2 text-xs text-slate-500">
                Rows returned: <strong>{result.row_count}</strong>
              </p>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Response Data</h2>
              {result.row_count === 0 ? (
                <p className="mt-3 text-sm text-slate-500">No rows matched this query.</p>
              ) : (
                <div className="mt-3 overflow-x-auto rounded-xl border border-slate-200">
                  <table className="min-w-full border-collapse text-sm">
                    <thead className="bg-slate-100 text-left text-slate-700">
                      <tr>
                        {columns.map((column) => (
                          <th key={column} className="border-b border-slate-200 px-3 py-2 font-semibold">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.rows.map((row, index) => (
                        <tr key={`${index}-${JSON.stringify(row)}`} className="odd:bg-white even:bg-slate-50">
                          {columns.map((column) => (
                            <td key={`${index}-${column}`} className="border-b border-slate-100 px-3 py-2 align-top text-slate-700">
                              {displayCell(row[column])}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";

import { queryDataFrameWithNL, uploadCsvFile } from "../lib/api";
import type { DataFrameQueryResult } from "../types";

export default function DataFrameQueryPage() {
  const [question, setQuestion] = useState("");
  const [useGoogleSheets, setUseGoogleSheets] = useState(true);
  const [uploadedCsvId, setUploadedCsvId] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DataFrameQueryResult | null>(null);

  const switchSource = (toSheets: boolean) => {
    setUseGoogleSheets(toSheets);
    setQuestion("");
    setUploadedCsvId(null);
    setUploadedFileName(null);
    setResult(null);
    setError(null);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);

    try {
      const uploadResult = await uploadCsvFile(file);
      setUploadedCsvId(uploadResult.file_id);
      setUploadedFileName(uploadResult.file_name);
    } catch (err) {
      const message = err instanceof Error ? err.message : "File upload failed.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRun = async () => {
    const trimmed = question.trim();
    if (!trimmed) {
      setError("Please enter a question.");
      return;
    }

    if (!useGoogleSheets && !uploadedCsvId) {
      setError("Please upload a CSV file first or switch to Google Sheets.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await queryDataFrameWithNL(trimmed, useGoogleSheets, uploadedCsvId);
      setResult(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Query failed.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-100 p-6">
      <div className="mx-auto max-w-6xl space-y-5">
        <header className="rounded-3xl border border-emerald-200 bg-white/90 p-6 shadow-lg backdrop-blur-sm">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Query CSV/Google Sheets with Natural Language</h1>
          <p className="mt-2 text-sm text-slate-600">
            Analyze data from a CSV file or Google Sheet using natural language questions powered by a Pandas DataFrame agent.
          </p>
        </header>

        <section className="rounded-3xl border border-emerald-200 bg-white/90 p-5 shadow-lg backdrop-blur-sm">
          <div className="mb-4 flex gap-3">
            <label className="flex items-center gap-2 rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1.5">
              <input
                type="radio"
                checked={useGoogleSheets}
                onChange={() => switchSource(true)}
                disabled={isLoading}
              />
              <span className="text-sm font-medium text-emerald-800">Google Sheet</span>
            </label>
            <label className="flex items-center gap-2 rounded-full border border-cyan-300 bg-cyan-50 px-3 py-1.5">
              <input
                type="radio"
                checked={!useGoogleSheets}
                onChange={() => switchSource(false)}
                disabled={isLoading}
              />
              <span className="text-sm font-medium text-cyan-800">CSV / XLSX File</span>
            </label>
          </div>

          {!useGoogleSheets && (
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-slate-700">Upload CSV / XLSX</label>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
                disabled={isLoading}
                className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-lg file:border-0 file:bg-teal-600 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-teal-700"
              />
              {uploadedFileName && (
                <p className="mt-2 text-xs text-slate-600">Uploaded: <strong>{uploadedFileName}</strong></p>
              )}
            </div>
          )}

          <label className="mb-2 block text-sm font-medium text-slate-700">Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={`Example: "What is the average sales ${useGoogleSheets ? "in the Google Sheet" : "in this CSV"}?"`}
            className="min-h-28 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
          />

          <button
            type="button"
            onClick={handleRun}
            disabled={isLoading}
            className="mt-4 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading ? "Analyzing..." : "Analyze"}
          </button>

          {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        </section>

        {result && (
          <section className="rounded-3xl border border-emerald-200 bg-white/90 p-5 shadow-lg backdrop-blur-sm">
              <h2 className="text-lg font-semibold text-slate-900">Answer</h2>
              <p className="mt-3 text-sm text-slate-700">{result.answer}</p>
              <p className="mt-2 text-xs text-slate-500">
                Data: {result.data_summary} ({result.row_count} rows, {result.column_names.length} columns)
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Source: <strong>{result.source}</strong>
              </p>
            </section>
        )}
      </div>
    </div>
  );
}

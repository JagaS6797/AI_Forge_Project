import { useState } from "react";

import ChatPage from "./pages/ChatPage";
import DataFrameQueryPage from "./pages/DataFrameQueryPage";
import ResearchDigestPage from "./pages/ResearchDigestPage";
import SqlQueryPage from "./pages/SqlQueryPage";
import { getAuthToken } from "./lib/api";

type AppView = "chat" | "project8" | "project9" | "project10";

export default function App() {
  const [view, setView] = useState<AppView>("chat");
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getAuthToken()));

  return (
    <div>
      {isAuthenticated && (
        <div className="fixed right-4 top-4 z-50 flex items-center gap-2 rounded-full border border-slate-200 bg-white/95 p-1 shadow-lg backdrop-blur">
          <button
            type="button"
            onClick={() => setView("chat")}
            className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
              view === "chat" ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setView("project8")}
            className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
              view === "project8" ? "bg-indigo-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            NL-SQL
          </button>
          <button
            type="button"
            onClick={() => setView("project9")}
            className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
              view === "project9" ? "bg-emerald-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            DataFrame
          </button>
          <button
            type="button"
            onClick={() => setView("project10")}
            className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
              view === "project10" ? "bg-violet-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            Research
          </button>
        </div>
      )}

      {view === "chat" ? (
        <ChatPage onAuthStateChange={setIsAuthenticated} />
      ) : view === "project8" ? (
        <SqlQueryPage />
      ) : view === "project9" ? (
        <DataFrameQueryPage />
      ) : (
        <ResearchDigestPage />
      )}
    </div>
  );
}

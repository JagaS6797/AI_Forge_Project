import { useState } from "react";

import ChatPage from "./pages/ChatPage";
import SqlQueryPage from "./pages/SqlQueryPage";

type AppView = "chat" | "project8";

export default function App() {
  const [view, setView] = useState<AppView>("chat");

  return (
    <div>
      <div className="fixed right-4 top-4 z-50 flex items-center gap-2 rounded-full border border-slate-200 bg-white/95 p-1 shadow-lg backdrop-blur">
        <button
          type="button"
          onClick={() => setView("chat")}
          className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
            view === "chat" ? "bg-slate-900 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
          }`}
        >
          Existing Chat
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
      </div>

      {view === "chat" ? <ChatPage /> : <SqlQueryPage />}
    </div>
  );
}

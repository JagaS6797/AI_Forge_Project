import { useState } from "react";
import type { ChatThread } from "../../types";

type Props = {
  threads: ChatThread[];
  activeThreadId: string | null;
  onSelect: (thread: ChatThread) => void;
  onCreate: () => void;
  onRename: (threadId: string, newName: string) => void;
  onDelete: (threadId: string) => void;
  userEmail: string;
  onLogout: () => void;
};

export function ThreadSidebar({
  threads,
  activeThreadId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
  userEmail,
  onLogout,
}: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

  const startEdit = (thread: ChatThread) => {
    setEditingId(thread.id);
    setEditValue(thread.name);
    setMenuOpenId(null);
  };

  const commitEdit = (threadId: string) => {
    const trimmed = editValue.trim();
    if (trimmed) onRename(threadId, trimmed);
    setEditingId(null);
  };

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-slate-900 text-slate-100">
      {/* Brand */}
      <div className="flex items-center gap-2.5 border-b border-slate-700 px-4 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500 text-sm font-bold text-white">
          A
        </div>
        <span className="text-sm font-semibold">Amzur AI Chat</span>
      </div>

      {/* New chat button */}
      <div className="px-3 pt-3">
        <button
          className="flex w-full items-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-700"
          onClick={onCreate}
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Thread list */}
      <nav className="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
        {threads.length === 0 && (
          <p className="px-2 py-3 text-xs text-slate-500">No conversations yet</p>
        )}
        {threads.map((thread) => (
          <div
            key={thread.id}
            className={`group relative flex items-center rounded-lg px-2 py-2 cursor-pointer transition ${
              thread.id === activeThreadId
                ? "bg-slate-700 text-white"
                : "text-slate-300 hover:bg-slate-800"
            }`}
            onClick={() => { if (editingId !== thread.id) onSelect(thread); }}
          >
            {editingId === thread.id ? (
              <input
                autoFocus
                className="flex-1 rounded bg-slate-600 px-2 py-0.5 text-sm text-white outline-none"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={() => commitEdit(thread.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitEdit(thread.id);
                  if (e.key === "Escape") setEditingId(null);
                }}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="mr-2 h-3.5 w-3.5 shrink-0 text-slate-400">
                  <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H6.414l-2.707 2.707A1 1 0 012 17V5z" clipRule="evenodd" />
                </svg>
                <span className="flex-1 truncate text-sm">{thread.name}</span>

                {/* Actions menu */}
                <div
                  className="ml-1 hidden shrink-0 group-hover:flex items-center"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="rounded p-0.5 hover:bg-slate-600"
                    title="Options"
                    onClick={() => setMenuOpenId(menuOpenId === thread.id ? null : thread.id)}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
                      <path d="M10 3a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM10 8.5a1.5 1.5 0 110 3 1.5 1.5 0 010-3zM11.5 15.5a1.5 1.5 0 10-3 0 1.5 1.5 0 003 0z" />
                    </svg>
                  </button>
                  {menuOpenId === thread.id && (
                    <div className="absolute right-0 top-8 z-20 w-32 rounded-lg border border-slate-600 bg-slate-800 py-1 shadow-lg">
                      <button
                        className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700"
                        onClick={() => startEdit(thread)}
                      >
                        Rename
                      </button>
                      <button
                        className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-slate-700"
                        onClick={() => { onDelete(thread.id); setMenuOpenId(null); }}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </nav>

      {/* User footer */}
      <div className="border-t border-slate-700 px-3 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-500 text-xs font-bold text-white">
            {userEmail.charAt(0).toUpperCase()}
          </div>
          <span className="flex-1 truncate text-xs text-slate-400">{userEmail}</span>
          <button
            className="rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition"
            onClick={onLogout}
            title="Logout"
          >
            Logout
          </button>
        </div>
      </div>
    </aside>
  );
}

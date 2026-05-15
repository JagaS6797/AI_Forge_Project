import { useMemo, useState } from "react";

import { playTicTacToeMove, startTicTacToeGame } from "../lib/api";
import type { TicTacToeCell, TicTacToeGameState } from "../types";

const EMPTY_BOARD: TicTacToeCell[] = ["", "", "", "", "", "", "", "", ""];

function statusBadgeClasses(status: TicTacToeGameState["status"] | "idle") {
  switch (status) {
    case "user_won":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case "agent_won":
      return "bg-red-100 text-red-700 border-red-200";
    case "draw":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "in_progress":
      return "bg-indigo-100 text-indigo-700 border-indigo-200";
    default:
      return "bg-slate-100 text-slate-600 border-slate-200";
  }
}

function statusLabel(status: TicTacToeGameState["status"] | "idle") {
  switch (status) {
    case "in_progress":
      return "In Progress";
    case "user_won":
      return "You Won";
    case "agent_won":
      return "Agent Won";
    case "draw":
      return "Draw";
    default:
      return "Ready";
  }
}

export default function TicTacToePage() {
  const [game, setGame] = useState<TicTacToeGameState | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userSymbol, setUserSymbol] = useState<"X" | "O">("X");
  const [agentStarts, setAgentStarts] = useState(false);

  const board = game?.board ?? EMPTY_BOARD;
  const isFinished = game ? game.status !== "in_progress" : false;
  const canPlay = Boolean(game && !isFinished && game.next_turn === "user" && !isLoading);

  const highlighted = useMemo(() => new Set(game?.winning_line ?? []), [game?.winning_line]);

  const handleStart = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const started = await startTicTacToeGame(userSymbol, agentStarts);
      setGame(started);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start game");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCellClick = async (index: number) => {
    if (!canPlay || board[index] !== "") return;

    setIsLoading(true);
    setError(null);
    try {
      const next = await playTicTacToeMove(board, game!.user_symbol, index);
      setGame(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Move failed");
    } finally {
      setIsLoading(false);
    }
  };

  const status = game?.status ?? "idle";

  return (
    <div className="h-full overflow-y-auto bg-[radial-gradient(circle_at_top_right,#eff6ff_12%,#f8fafc_45%,#e2e8f0_100%)] p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="rounded-3xl border border-indigo-100 bg-white/90 p-6 shadow-lg backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Tic Tac Toe Agent</h1>
              <p className="mt-1 text-sm text-slate-600">
                Play against an intelligent agent. Your moves are validated server-side and the agent responds instantly.
              </p>
            </div>
            <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${statusBadgeClasses(status)}`}>
              {statusLabel(status)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]">
          <aside className="rounded-3xl border border-slate-200 bg-white/90 p-5 shadow">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Game Controls</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Your Symbol</label>
                <div className="flex gap-2">
                  {(["X", "O"] as const).map((symbol) => (
                    <button
                      key={symbol}
                      type="button"
                      onClick={() => setUserSymbol(symbol)}
                      disabled={isLoading}
                      className={`rounded-lg border px-4 py-2 text-sm font-semibold transition ${
                        userSymbol === symbol
                          ? "border-indigo-600 bg-indigo-600 text-white"
                          : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                      }`}
                    >
                      {symbol}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={agentStarts}
                  onChange={(e) => setAgentStarts(e.target.checked)}
                  disabled={isLoading}
                  className="h-4 w-4 rounded border-slate-300"
                />
                Agent starts first
              </label>

              <button
                type="button"
                onClick={() => void handleStart()}
                disabled={isLoading}
                className="w-full rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isLoading ? "Processing..." : game ? "Restart Match" : "Start Match"}
              </button>

              {error && (
                <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">{error}</p>
              )}
            </div>

            <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Agent Note</p>
              <p className="mt-2 text-sm text-slate-700">
                {game?.message ?? "Start a match to begin."}
              </p>
              {game && !isFinished && (
                <p className="mt-2 text-xs text-slate-500">
                  Next turn: <span className="font-semibold text-slate-700">{game.next_turn === "user" ? "You" : "Agent"}</span>
                </p>
              )}
            </div>
          </aside>

          <section className="rounded-3xl border border-indigo-100 bg-white/90 p-6 shadow">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Board</h2>
            <div className="mx-auto mt-5 grid max-w-[360px] grid-cols-3 gap-3">
              {board.map((cell, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => void handleCellClick(idx)}
                  disabled={!canPlay || cell !== ""}
                  className={`aspect-square rounded-2xl border text-3xl font-bold transition ${
                    highlighted.has(idx)
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-slate-300 bg-white text-slate-800 hover:bg-slate-50"
                  } disabled:cursor-not-allowed disabled:opacity-80`}
                >
                  {cell || "·"}
                </button>
              ))}
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">You</p>
                <p className="mt-1 font-semibold text-slate-800">{game?.user_symbol ?? userSymbol}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">Agent</p>
                <p className="mt-1 font-semibold text-slate-800">{game?.agent_symbol ?? (userSymbol === "X" ? "O" : "X")}</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

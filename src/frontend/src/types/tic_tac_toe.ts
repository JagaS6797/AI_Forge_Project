export type TicTacToeCell = "" | "X" | "O";
export type TicTacToeStatus = "in_progress" | "user_won" | "agent_won" | "draw";

export interface TicTacToeGameState {
  board: TicTacToeCell[];
  user_symbol: "X" | "O";
  agent_symbol: "X" | "O";
  next_turn: "user" | "agent" | "none";
  status: TicTacToeStatus;
  winner: "user" | "agent" | "none";
  winning_line: number[];
  user_move: number | null;
  agent_move: number | null;
  message: string;
}

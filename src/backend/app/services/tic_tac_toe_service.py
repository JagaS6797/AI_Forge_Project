from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException

from app.schemas.tic_tac_toe import CellValue, PlayerSymbol, TicTacToeGameState

WinningLine = tuple[int, int, int]

WINNING_LINES: tuple[WinningLine, ...] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass(frozen=True)
class Evaluation:
    score: int
    move: int | None


def _agent_symbol(user_symbol: PlayerSymbol) -> PlayerSymbol:
    return "O" if user_symbol == "X" else "X"


def _check_winner(board: list[CellValue]) -> tuple[CellValue | None, list[int]]:
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], [a, b, c]
    return None, []


def _is_draw(board: list[CellValue]) -> bool:
    return all(cell in ("X", "O") for cell in board)


def _available_moves(board: list[CellValue]) -> list[int]:
    return [idx for idx, value in enumerate(board) if value == ""]


def _evaluate_terminal_state(
    board: list[CellValue],
    user_symbol: PlayerSymbol,
    agent_symbol: PlayerSymbol,
    depth: int,
) -> Evaluation | None:
    winner, _line = _check_winner(board)
    if winner == agent_symbol:
        return Evaluation(score=10 - depth, move=None)
    if winner == user_symbol:
        return Evaluation(score=depth - 10, move=None)
    if _is_draw(board):
        return Evaluation(score=0, move=None)
    return None


def _minimax(
    board: list[CellValue],
    is_agent_turn: bool,
    user_symbol: PlayerSymbol,
    agent_symbol: PlayerSymbol,
    depth: int,
) -> Evaluation:
    terminal = _evaluate_terminal_state(board, user_symbol, agent_symbol, depth)
    if terminal is not None:
        return terminal

    moves = _available_moves(board)
    if is_agent_turn:
        best = Evaluation(score=-999, move=None)
        for move in moves:
            board[move] = agent_symbol
            result = _minimax(board, False, user_symbol, agent_symbol, depth + 1)
            board[move] = ""
            if result.score > best.score:
                best = Evaluation(score=result.score, move=move)
        return best

    best = Evaluation(score=999, move=None)
    for move in moves:
        board[move] = user_symbol
        result = _minimax(board, True, user_symbol, agent_symbol, depth + 1)
        board[move] = ""
        if result.score < best.score:
            best = Evaluation(score=result.score, move=move)
    return best


def _best_agent_move(board: list[CellValue], user_symbol: PlayerSymbol, agent_symbol: PlayerSymbol) -> int:
    # A deterministic first move makes games feel more natural.
    if board == ["", "", "", "", "", "", "", "", ""]:
        return 4

    evaluation = _minimax(board, True, user_symbol, agent_symbol, depth=0)
    if evaluation.move is None:
        raise HTTPException(status_code=400, detail="No valid move left for agent")
    return evaluation.move


def start_new_game(user_symbol: PlayerSymbol = "X", agent_starts: bool = False) -> TicTacToeGameState:
    board: list[CellValue] = ["", "", "", "", "", "", "", "", ""]
    agent_symbol = _agent_symbol(user_symbol)

    agent_move: int | None = None
    next_turn: Literal["user", "agent", "none"] = "user"
    message = "Your turn. Pick a cell."

    if agent_starts:
        agent_move = _best_agent_move(board, user_symbol, agent_symbol)
        board[agent_move] = agent_symbol
        next_turn = "user"
        message = "Agent started the game. Your turn now."

    return TicTacToeGameState(
        board=board,
        user_symbol=user_symbol,
        agent_symbol=agent_symbol,
        next_turn=next_turn,
        status="in_progress",
        winner="none",
        winning_line=[],
        user_move=None,
        agent_move=agent_move,
        message=message,
    )


def play_user_move(board: list[CellValue], user_symbol: PlayerSymbol, user_move: int) -> TicTacToeGameState:
    if len(board) != 9:
        raise HTTPException(status_code=400, detail="Board must contain exactly 9 cells")

    if any(cell not in ("", "X", "O") for cell in board):
        raise HTTPException(status_code=400, detail="Board has invalid symbols")

    agent_symbol = _agent_symbol(user_symbol)
    local_board = board.copy()

    winner, winning_line = _check_winner(local_board)
    if winner or _is_draw(local_board):
        raise HTTPException(status_code=400, detail="Game is already complete. Start a new game.")

    if local_board[user_move] != "":
        raise HTTPException(status_code=400, detail="Cell is already occupied")

    local_board[user_move] = user_symbol

    winner, winning_line = _check_winner(local_board)
    if winner == user_symbol:
        return TicTacToeGameState(
            board=local_board,
            user_symbol=user_symbol,
            agent_symbol=agent_symbol,
            next_turn="none",
            status="user_won",
            winner="user",
            winning_line=winning_line,
            user_move=user_move,
            agent_move=None,
            message="You won! Great play.",
        )

    if _is_draw(local_board):
        return TicTacToeGameState(
            board=local_board,
            user_symbol=user_symbol,
            agent_symbol=agent_symbol,
            next_turn="none",
            status="draw",
            winner="none",
            winning_line=[],
            user_move=user_move,
            agent_move=None,
            message="Draw game.",
        )

    agent_move = _best_agent_move(local_board, user_symbol, agent_symbol)
    local_board[agent_move] = agent_symbol

    winner, winning_line = _check_winner(local_board)
    if winner == agent_symbol:
        return TicTacToeGameState(
            board=local_board,
            user_symbol=user_symbol,
            agent_symbol=agent_symbol,
            next_turn="none",
            status="agent_won",
            winner="agent",
            winning_line=winning_line,
            user_move=user_move,
            agent_move=agent_move,
            message="Agent won this round.",
        )

    if _is_draw(local_board):
        return TicTacToeGameState(
            board=local_board,
            user_symbol=user_symbol,
            agent_symbol=agent_symbol,
            next_turn="none",
            status="draw",
            winner="none",
            winning_line=[],
            user_move=user_move,
            agent_move=agent_move,
            message="Draw game.",
        )

    return TicTacToeGameState(
        board=local_board,
        user_symbol=user_symbol,
        agent_symbol=agent_symbol,
        next_turn="user",
        status="in_progress",
        winner="none",
        winning_line=[],
        user_move=user_move,
        agent_move=agent_move,
        message="Your turn.",
    )

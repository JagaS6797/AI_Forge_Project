from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

CellValue = Literal["", "X", "O"]
PlayerSymbol = Literal["X", "O"]
GameStatus = Literal["in_progress", "user_won", "agent_won", "draw"]


class TicTacToeNewGameRequest(BaseModel):
    user_symbol: PlayerSymbol = "X"
    agent_starts: bool = False


class TicTacToeMoveRequest(BaseModel):
    board: list[CellValue] = Field(..., min_length=9, max_length=9)
    user_symbol: PlayerSymbol = "X"
    user_move: int = Field(..., ge=0, le=8)

    @field_validator("board")
    @classmethod
    def validate_board_size(cls, value: list[CellValue]) -> list[CellValue]:
        if len(value) != 9:
            raise ValueError("Board must contain exactly 9 cells")
        return value


class TicTacToeGameState(BaseModel):
    board: list[CellValue]
    user_symbol: PlayerSymbol
    agent_symbol: PlayerSymbol
    next_turn: Literal["user", "agent", "none"]
    status: GameStatus
    winner: Literal["user", "agent", "none"]
    winning_line: list[int] = Field(default_factory=list)
    user_move: int | None = None
    agent_move: int | None = None
    message: str

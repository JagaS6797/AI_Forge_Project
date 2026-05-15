from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, get_current_user
from app.schemas.tic_tac_toe import (
    TicTacToeGameState,
    TicTacToeMoveRequest,
    TicTacToeNewGameRequest,
)
from app.services.tic_tac_toe_service import play_user_move, start_new_game

router = APIRouter(prefix="/api/tic-tac-toe", tags=["tic-tac-toe"])


@router.post("/new", response_model=TicTacToeGameState)
async def new_game(
    payload: TicTacToeNewGameRequest,
    _current_user: CurrentUser = Depends(get_current_user),
) -> TicTacToeGameState:
    return start_new_game(user_symbol=payload.user_symbol, agent_starts=payload.agent_starts)


@router.post("/move", response_model=TicTacToeGameState)
async def play_move(
    payload: TicTacToeMoveRequest,
    _current_user: CurrentUser = Depends(get_current_user),
) -> TicTacToeGameState:
    return play_user_move(board=payload.board, user_symbol=payload.user_symbol, user_move=payload.user_move)

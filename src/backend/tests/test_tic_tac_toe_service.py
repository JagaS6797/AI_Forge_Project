from __future__ import annotations

from fastapi import HTTPException

from app.services.tic_tac_toe_service import play_user_move, start_new_game


def test_start_new_game_default_user_starts() -> None:
    state = start_new_game(user_symbol="X", agent_starts=False)
    assert state.status == "in_progress"
    assert state.next_turn == "user"
    assert state.board == ["", "", "", "", "", "", "", "", ""]
    assert state.agent_move is None


def test_start_new_game_agent_starts_center() -> None:
    state = start_new_game(user_symbol="X", agent_starts=True)
    assert state.status == "in_progress"
    assert state.board[4] == "O"
    assert state.agent_move == 4


def test_play_user_move_marks_board_and_agent_replies() -> None:
    initial = start_new_game(user_symbol="X", agent_starts=False)
    state = play_user_move(initial.board, initial.user_symbol, user_move=0)
    assert state.board[0] == "X"
    assert state.agent_move is not None
    assert state.status in ("in_progress", "agent_won", "draw")


def test_play_user_move_rejects_occupied_cell() -> None:
    board = ["X", "", "", "", "", "", "", "", ""]
    try:
        play_user_move(board, "X", user_move=0)
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "occupied" in str(exc.detail)
    else:
        raise AssertionError("Expected HTTPException for occupied move")

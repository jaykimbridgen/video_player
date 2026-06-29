"""플레이어 예외 — 각 예외는 매핑되는 종료 코드를 가진다."""

from __future__ import annotations

from video_player.constants import EXIT_ARG_ERROR, EXIT_DECODE_ERROR


class PlayerError(Exception):
    """플레이어 일반 오류(종료 코드 1)."""

    exit_code: int = 1


class ArgumentError(PlayerError):
    """인자·파일 오류(종료 코드 2)."""

    exit_code: int = EXIT_ARG_ERROR


class DecodeError(PlayerError):
    """디코드·재생 불가(종료 코드 3)."""

    exit_code: int = EXIT_DECODE_ERROR

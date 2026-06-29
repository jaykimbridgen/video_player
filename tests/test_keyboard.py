"""키 입력 매핑 단위 테스트 (계층 1).

플랫폼 의존 모듈(termios 등)을 import 시점에 끌어오지 않아야 하므로, 이 import 자체가
Windows/CI 에서 성공하는 것도 함께 검증한다.
"""

from __future__ import annotations

import video_player.keyboard as keyboard
from video_player.controller import Action
from video_player.keyboard import parse_key


def test_space_is_pause() -> None:
    assert parse_key(b" ") is Action.PAUSE


def test_arrow_right_is_seek_forward() -> None:
    assert parse_key(b"\x1b[C") is Action.SEEK_FORWARD


def test_arrow_left_is_seek_backward() -> None:
    assert parse_key(b"\x1b[D") is Action.SEEK_BACKWARD


def test_arrow_up_is_volume_up() -> None:
    assert parse_key(b"\x1b[A") is Action.VOLUME_UP


def test_arrow_down_is_volume_down() -> None:
    assert parse_key(b"\x1b[B") is Action.VOLUME_DOWN


def test_m_is_toggle_mute() -> None:
    assert parse_key(b"m") is Action.TOGGLE_MUTE


def test_q_is_quit() -> None:
    assert parse_key(b"q") is Action.QUIT


def test_lone_escape_is_quit() -> None:
    assert parse_key(b"\x1b") is Action.QUIT


def test_unknown_key_is_none() -> None:
    assert parse_key(b"z") is None
    assert parse_key(b"") is None


def test_module_imports_without_platform_modules() -> None:
    # 모듈 import 가 termios 같은 플랫폼 모듈을 끌어오지 않아 어디서든 import 가능해야 한다.
    assert hasattr(keyboard, "parse_key")

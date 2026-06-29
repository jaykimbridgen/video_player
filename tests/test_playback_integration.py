"""Player 통합 테스트 (계층 2) — 실제 libmpv 로 ``--vo=null --ao=null`` 재생.

mpv/libmpv 가 없는 환경에서는 모듈 전체를 건너뛴다(컬렉션 단계에서 importorskip).
실행: ``pytest -m integration``
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

# libmpv 가 없으면(예: CI 단위 전용·Windows 미설치) 이 모듈 전체를 건너뛴다.
# python-mpv 는 DLL 을 못 찾으면 ImportError 가 아니라 OSError 를 던지므로 둘 다 잡는다.
try:
    import mpv  # noqa: F401
except (ImportError, OSError):
    pytest.skip("libmpv 를 찾을 수 없어 통합 테스트를 건너뜁니다.", allow_module_level=True)

from video_player.config import Config  # noqa: E402
from video_player.errors import DecodeError  # noqa: E402
from video_player.player import Player  # noqa: E402

pytestmark = pytest.mark.integration

# 통합 테스트는 화면/소리 없이 동작하도록 vo/ao 를 null 로 덮어쓴다.
_NULL_OUTPUT = {"vo": "null", "ao": "null"}


def _make_player() -> Player:
    return Player(Config(), overrides=_NULL_OUTPUT)


def test_volume_property_changes() -> None:
    p = _make_player()
    try:
        p.set_volume(40)
        assert round(p.volume) == 40
    finally:
        p.terminate()


def test_mute_toggles() -> None:
    p = _make_player()
    try:
        assert p.muted is False
        p.toggle_mute()
        assert p.muted is True
        p.toggle_mute()
        assert p.muted is False
    finally:
        p.terminate()


def test_pause_and_resume_property() -> None:
    p = _make_player()
    try:
        p.pause()
        assert p.paused is True
        p.resume()
        assert p.paused is False
    finally:
        p.terminate()


def test_load_succeeds_and_time_pos_readable(test_video: Path) -> None:
    p = _make_player()
    try:
        p.pause()  # 재생이 끝나버리지 않도록 정지 상태로 로드
        p.load(test_video)
        # 파일이 로드되면 time_pos 가 사용 가능해진다(최대 5초 대기).
        deadline = time.time() + 5.0
        while p.time_pos is None and time.time() < deadline:
            time.sleep(0.02)
        assert p.time_pos is not None
        assert p.time_pos >= 0.0
        # seek 가 멈춤 없이 동작하고 time_pos 가 여전히 읽혀야 한다.
        p.seek(5)
        assert isinstance(p.time_pos, float)
    finally:
        p.terminate()


def test_eof_completes_without_error(test_video: Path) -> None:
    p = _make_player()
    try:
        p.load(test_video)
        p.wait_for_playback()  # 정상 종료(EOF)면 예외 없이 반환
    finally:
        p.terminate()


def test_broken_file_raises_decode_error(broken_video: Path) -> None:
    p = _make_player()
    try:
        p.load(broken_video)
        with pytest.raises(DecodeError):
            p.wait_for_playback()
    finally:
        p.terminate()


def test_missing_file_raises_decode_error(tmp_path: Path) -> None:
    p = _make_player()
    try:
        p.load(tmp_path / "does_not_exist.mp4")
        with pytest.raises(DecodeError):
            p.wait_for_playback()
    finally:
        p.terminate()

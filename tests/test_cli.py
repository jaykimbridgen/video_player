"""CLI 단위 테스트 (계층 1) — 인자/파일 검증, 종료 코드 매핑.

실제 mpv 없이 가짜 Player·입력원을 주입해 run 루프의 종료 코드 규칙을 검증한다.
"""

from __future__ import annotations

from pathlib import Path

from video_player import cli
from video_player.constants import EXIT_ARG_ERROR, EXIT_DECODE_ERROR, EXIT_OK
from video_player.controller import Action
from video_player.errors import DecodeError


# --- 가짜 입력원/Player ----------------------------------------------------
class FakeInput:
    def __init__(self, actions: list[Action] | None = None) -> None:
        self._actions = list(actions or [])

    def __enter__(self) -> FakeInput:
        return self

    def __exit__(self, *exc: object) -> None:
        pass

    def read_action(self, timeout: float | None = None) -> Action | None:
        if self._actions:
            return self._actions.pop(0)
        return None


class FakePlayer:
    def __init__(self, *, raises: Exception | None = None) -> None:
        self._raises = raises
        self.loaded: object | None = None
        self.terminated = False

    def load(self, path: object) -> None:
        self.loaded = path

    def wait_for_playback(self) -> None:
        if self._raises is not None:
            raise self._raises

    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def seek(self, delta: float) -> None: ...
    def set_volume(self, volume: int) -> None: ...
    def toggle_mute(self) -> None: ...

    def quit(self) -> None: ...

    def terminate(self) -> None:
        self.terminated = True


# --- 인자/파일 검증 --------------------------------------------------------
def test_no_args_returns_arg_error() -> None:
    assert cli.main([]) == EXIT_ARG_ERROR


def test_missing_file_returns_arg_error(tmp_path: Path) -> None:
    assert cli.main([str(tmp_path / "nope.mp4")]) == EXIT_ARG_ERROR


def test_directory_path_returns_arg_error(tmp_path: Path) -> None:
    assert cli.main([str(tmp_path)]) == EXIT_ARG_ERROR


def test_valid_path_delegates_to_play(tmp_path: Path, monkeypatch) -> None:
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x")
    called: dict[str, object] = {}

    def fake_play(path: Path) -> int:
        called["path"] = path
        return EXIT_OK

    monkeypatch.setattr(cli, "play", fake_play)
    assert cli.main([str(media)]) == EXIT_OK
    assert called["path"] == media


# --- play() 종료 코드 매핑 -------------------------------------------------
def _play(media: Path, player: FakePlayer, actions: list[Action] | None = None) -> int:
    return cli.play(
        media,
        player_factory=lambda config: player,
        input_factory=lambda: FakeInput(actions),
    )


def test_play_eof_returns_ok(tmp_path: Path) -> None:
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x")
    player = FakePlayer()
    assert _play(media, player) == EXIT_OK
    assert player.loaded == media
    assert player.terminated is True


def test_play_decode_error_returns_decode_code(tmp_path: Path) -> None:
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x")
    player = FakePlayer(raises=DecodeError("깨진 파일"))
    assert _play(media, player) == EXIT_DECODE_ERROR
    assert player.terminated is True


def test_play_quit_action_returns_ok(tmp_path: Path) -> None:
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"x")
    player = FakePlayer()
    assert _play(media, player, actions=[Action.QUIT]) == EXIT_OK

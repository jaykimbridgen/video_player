"""Controller 단위 테스트 (계층 1) — 가짜 Player 로 액션→메서드 매핑 검증."""

from __future__ import annotations

from video_player.config import Config
from video_player.controller import Action, Controller


class FakePlayer:
    """Player 인터페이스를 흉내내며 호출 순서를 기록한다."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def pause(self) -> None:
        self.calls.append(("pause", None))

    def resume(self) -> None:
        self.calls.append(("resume", None))

    def seek(self, delta: float) -> None:
        self.calls.append(("seek", delta))

    def set_volume(self, volume: int) -> None:
        self.calls.append(("set_volume", volume))

    def toggle_mute(self) -> None:
        self.calls.append(("toggle_mute", None))

    def quit(self) -> None:
        self.calls.append(("quit", None))


def test_pause_toggles_between_pause_and_resume() -> None:
    p = FakePlayer()
    c = Controller(p, Config())
    c.handle(Action.PAUSE)
    c.handle(Action.PAUSE)
    assert p.calls == [("pause", None), ("resume", None)]


def test_seek_forward_uses_positive_step() -> None:
    p = FakePlayer()
    c = Controller(p, Config())
    c.handle(Action.SEEK_FORWARD)
    assert p.calls == [("seek", 5)]


def test_seek_backward_uses_negative_step() -> None:
    p = FakePlayer()
    c = Controller(p, Config())
    c.handle(Action.SEEK_BACKWARD)
    assert p.calls == [("seek", -5)]


def test_volume_up_increments_by_step() -> None:
    p = FakePlayer()
    c = Controller(p, Config(initial_volume=50))
    c.handle(Action.VOLUME_UP)
    assert p.calls == [("set_volume", 55)]


def test_volume_up_clamps_at_max() -> None:
    p = FakePlayer()
    c = Controller(p, Config(initial_volume=100))
    c.handle(Action.VOLUME_UP)
    assert p.calls == [("set_volume", 100)]


def test_volume_down_clamps_at_min() -> None:
    p = FakePlayer()
    c = Controller(p, Config(initial_volume=3))
    c.handle(Action.VOLUME_DOWN)
    assert p.calls == [("set_volume", 0)]


def test_toggle_mute_calls_player() -> None:
    p = FakePlayer()
    c = Controller(p, Config())
    c.handle(Action.TOGGLE_MUTE)
    assert p.calls == [("toggle_mute", None)]


def test_quit_calls_player_and_signals_stop() -> None:
    p = FakePlayer()
    c = Controller(p, Config())
    keep_going = c.handle(Action.QUIT)
    assert p.calls == [("quit", None)]
    assert keep_going is False


def test_non_quit_actions_signal_continue() -> None:
    p = FakePlayer()
    c = Controller(p, Config())
    assert c.handle(Action.PAUSE) is True

"""Controller — 추상 action 을 받아 Player 메서드를 호출하는 분리막.

입력원(키보드 등)과 Player 사이를 끊어, 입력원만 교체하면 나머지를 재사용할 수 있다.
재생/음소거 토글 상태와 볼륨 값을 여기서 관리한다(볼륨은 0~100 으로 클램프).
"""

from __future__ import annotations

import enum
from typing import Protocol

from video_player.config import Config
from video_player.constants import VOLUME_MAX, VOLUME_MIN


class Action(enum.Enum):
    """입력원이 만들어 Controller 에 전달하는 추상 동작."""

    PAUSE = enum.auto()
    SEEK_FORWARD = enum.auto()
    SEEK_BACKWARD = enum.auto()
    VOLUME_UP = enum.auto()
    VOLUME_DOWN = enum.auto()
    TOGGLE_MUTE = enum.auto()
    QUIT = enum.auto()


class PlayerLike(Protocol):
    """Controller 가 의존하는 Player 인터페이스(테스트 시 가짜로 대체 가능)."""

    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def seek(self, delta: float) -> None: ...
    def set_volume(self, volume: int) -> None: ...
    def toggle_mute(self) -> None: ...
    def quit(self) -> None: ...


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


class Controller:
    def __init__(self, player: PlayerLike, config: Config) -> None:
        self._player = player
        self._config = config
        self._volume = config.initial_volume
        self._paused = False

    def handle(self, action: Action) -> bool:
        """action 을 처리한다. 계속 재생할지 여부(QUIT 면 False)를 돌려준다."""
        if action is Action.PAUSE:
            self._toggle_pause()
        elif action is Action.SEEK_FORWARD:
            self._player.seek(self._config.seek_step_sec)
        elif action is Action.SEEK_BACKWARD:
            self._player.seek(-self._config.seek_step_sec)
        elif action is Action.VOLUME_UP:
            self._change_volume(self._config.volume_step)
        elif action is Action.VOLUME_DOWN:
            self._change_volume(-self._config.volume_step)
        elif action is Action.TOGGLE_MUTE:
            self._player.toggle_mute()
        elif action is Action.QUIT:
            self._player.quit()
            return False
        return True

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        if self._paused:
            self._player.pause()
        else:
            self._player.resume()

    def _change_volume(self, delta: int) -> None:
        self._volume = _clamp(self._volume + delta, VOLUME_MIN, VOLUME_MAX)
        self._player.set_volume(self._volume)

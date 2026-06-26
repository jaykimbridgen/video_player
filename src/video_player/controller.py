"""Controller — 추상 action 을 받아 Player 메서드를 호출하는 분리막.

입력원(키보드 등)과 Player 사이를 끊어, 입력원만 교체하면 나머지를 재사용할 수 있다.
재생/음소거 토글 상태와 볼륨 값을 여기서 관리한다(볼륨은 0~100 으로 클램프).
"""

from __future__ import annotations

import enum
from typing import Protocol

from video_player.config import Config
from video_player.constants import VOLUME_MAX, VOLUME_MIN

# 이 모듈의 공개 표면(외부가 의존해도 되는 것). 나머지(_접두)는 내부 부품이다.
__all__ = ["Action", "PlayerLike", "Controller"]


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
    """Controller 가 의존하는 Player 인터페이스(테스트 시 가짜로 대체 가능).

    Controller 는 이 메서드들만 호출한다 — 실제 Player 는 이 계약을 만족하면 된다.
    """

    def pause(self) -> None:
        """재생을 일시정지한다."""

    def resume(self) -> None:
        """일시정지를 풀고 재생을 재개한다."""

    def seek(self, delta: float) -> None:
        """현재 위치에서 delta 초만큼 이동한다(음수면 뒤로)."""

    def set_volume(self, volume: int) -> None:
        """볼륨을 주어진 값(0~100)으로 설정한다."""

    def toggle_mute(self) -> None:
        """음소거를 켜고 끈다."""

    def quit(self) -> None:
        """재생을 멈추고 종료한다."""


def _clamp(value: int, low: int, high: int) -> int:
    """value 를 [low, high] 범위로 가둔다(볼륨 경계 유지를 위한 작은 순수 헬퍼)."""
    return max(low, min(high, value))


class Controller:
    """추상 Action 을 Player 메서드 호출로 번역하는 상태 보유 객체.

    입력원이 무엇이든(키보드·IPC 등) 같은 Action 어휘만 넘기면 동작하도록
    입력원과 Player 를 분리한다. 일시정지 토글과 볼륨 값은 여기서 보유한다.

    상태:
        _player: 명령을 위임할 Player(테스트 시 가짜로 대체).
        _config: seek 폭·볼륨 단계 등 정책 값의 출처.
        _volume: 현재 볼륨(0~100 으로 클램프 유지).
        _paused: 일시정지 여부(PAUSE 토글이 일시정지/재개를 가르는 기준).
    """

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
        """_paused 를 뒤집어, 같은 PAUSE 동작이 일시정지/재개를 번갈아 호출하게 한다."""
        self._paused = not self._paused
        if self._paused:
            self._player.pause()
        else:
            self._player.resume()

    def _change_volume(self, delta: int) -> None:
        """현재 볼륨에 delta 를 더해 0~100 으로 클램프한 뒤 Player 에 반영한다."""
        self._volume = _clamp(self._volume + delta, VOLUME_MIN, VOLUME_MAX)
        self._player.set_volume(self._volume)

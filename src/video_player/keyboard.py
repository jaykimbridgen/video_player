"""키보드 입력원 — 키 입력을 추상 Action 으로 변환한다.

- ``parse_key`` 는 순수 함수로, 어떤 플랫폼에서도 import·테스트 가능하다.
- 실제 TTY 원시 입력 읽기(``KeyboardInput``)는 리눅스 전용(termios/tty/select)이며,
  해당 모듈은 import 시점이 아니라 사용 시점(메서드 안)에서만 끌어온다.
  → 순수 로직은 Windows/CI 에서도 import 가능.
추후 evdev/IPC 같은 다른 입력원도 같은 (bytes→Action) 패턴으로 추가할 수 있다.
"""

from __future__ import annotations

import os
from types import TracebackType
from typing import Any

from video_player.controller import Action

# 원시 키 바이트열 → Action 매핑. 방향키는 ANSI 이스케이프 시퀀스.
_KEY_BINDINGS: dict[bytes, Action] = {
    b" ": Action.PAUSE,
    b"\x1b[C": Action.SEEK_FORWARD,  # →
    b"\x1b[D": Action.SEEK_BACKWARD,  # ←
    b"\x1b[A": Action.VOLUME_UP,  # ↑
    b"\x1b[B": Action.VOLUME_DOWN,  # ↓
    b"m": Action.TOGGLE_MUTE,
    b"q": Action.QUIT,
    b"\x1b": Action.QUIT,  # 단독 Esc
}


def parse_key(data: bytes) -> Action | None:
    """원시 키 바이트열을 Action 으로 변환한다. 매핑이 없으면 None."""
    return _KEY_BINDINGS.get(data)


class KeyboardInput:
    """리눅스 TTY 를 원시 모드로 두고 키를 Action 으로 읽어오는 입력원.

    컨텍스트 매니저로 사용해 원시 모드 진입/복구를 보장한다(콘솔 상태 복구).

    상태:
        _fd: 읽을 대상 파일 디스크립터(기본은 표준입력, __enter__ 에서 확정).
        _saved: 원시 모드 진입 전 단말 속성 — __exit__ 에서 이 값으로 콘솔을 복구.
    """

    def __init__(self, fd: int | None = None) -> None:
        self._fd = fd
        # 단말 속성(termios.tcgetattr 결과) — 타입 스텁이 복잡해 Any 로 둔다.
        self._saved: Any = None

    def __enter__(self) -> KeyboardInput:
        import sys
        import termios
        import tty

        if self._fd is None:
            self._fd = sys.stdin.fileno()
        self._saved = termios.tcgetattr(self._fd)
        # cbreak: 줄단위 버퍼링/에코 끄되, 신호(Ctrl+C)는 살려 graceful 종료 유도.
        tty.setcbreak(self._fd)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        import termios

        if self._saved is not None and self._fd is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)

    def read_action(self, timeout: float | None = None) -> Action | None:
        """키 하나를 읽어 Action 으로 변환한다.

        ``timeout`` 이 주어지면 그 시간 안에 입력이 없을 때 None 을 돌려준다
        (재생 루프가 EOF 등 다른 종료 조건을 주기적으로 확인할 수 있도록).
        매핑되지 않는 키 역시 None.
        """
        import select

        assert self._fd is not None
        if timeout is not None and not select.select([self._fd], [], [], timeout)[0]:
            return None
        data = os.read(self._fd, 1)
        if data == b"\x1b":
            data += self._read_escape_tail()
        return parse_key(data)

    def _read_escape_tail(self) -> bytes:
        """Esc 직후 짧은 시간 안에 따라오는 시퀀스 바이트를 읽는다.

        뒤따르는 바이트가 없으면(단독 Esc) 빈 바이트열을 돌려준다.
        """
        import select

        assert self._fd is not None
        tail = b""
        # 이스케이프 시퀀스는 즉시 도착한다. 50ms 안에 안 오면 단독 Esc 로 본다.
        while select.select([self._fd], [], [], 0.05)[0]:
            tail += os.read(self._fd, 1)
            if len(tail) >= 2:  # '[' + 방향문자
                break
        return tail

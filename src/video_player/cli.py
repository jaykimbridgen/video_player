"""CLI — 인자 파싱, 검증, 그리고 Config·Player·Controller·키보드 입력원 조립.

흐름: 입력원 → Controller → Player → mpv (단방향). 재생에 필요한 시점에만 Player(mpv)
를 import 해, 인자/파일 검증 같은 경로에서는 libmpv 의존성을 끌어오지 않는다.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from video_player.config import Config
from video_player.constants import EXIT_OK
from video_player.controller import Controller
from video_player.errors import ArgumentError, DecodeError, PlayerError
from video_player.logging_setup import setup_logging

log = logging.getLogger(__name__)

# 재생 루프가 종료 조건(EOF·종료키)을 주기적으로 확인하는 간격(초).
_POLL_INTERVAL_SEC = 0.2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="player",
        description="동영상 파일 하나를 HDMI 로 재생한다.",
    )
    parser.add_argument("path", help="재생할 영상 파일 경로")
    return parser


def _validate_media_path(path: Path) -> None:
    """파일 존재·종류·접근성을 검증한다. 문제가 있으면 ArgumentError(코드 2)."""
    if not path.exists():
        raise ArgumentError(f"파일을 찾을 수 없습니다: {path}")
    if not path.is_file():
        raise ArgumentError(f"파일이 아닙니다: {path}")
    if not os.access(path, os.R_OK):
        raise ArgumentError(f"파일에 접근할 수 없습니다: {path}")


@contextmanager
def _stop_on_signals() -> Iterator[threading.Event]:
    """SIGINT/SIGTERM 을 받으면 set 되는 이벤트를 제공하고, 원래 핸들러를 복구한다."""
    stop = threading.Event()
    previous: dict[int, Any] = {}

    def _request_stop(signum: int, frame: Any) -> None:
        log.info("종료 신호 수신(%s) — graceful shutdown.", signum)
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            previous[sig] = signal.signal(sig, _request_stop)
        except (ValueError, OSError, AttributeError):
            # 메인 스레드가 아니거나 플랫폼 미지원이면 건너뛴다.
            pass
    try:
        yield stop
    finally:
        for saved_sig, handler in previous.items():
            try:
                signal.signal(saved_sig, handler)
            except (ValueError, OSError):
                pass


def _run_loop(
    player: Any,
    controller: Controller,
    input_factory: Callable[[], Any],
    stop: threading.Event,
) -> None:
    """키 입력을 받아 재생을 제어한다. 디코드 실패 시 DecodeError 를 올린다.

    재생 종료(EOF)는 별도 스레드에서 감지한다. 종료키(q/Esc)·신호·EOF 중
    무엇이든 발생하면 루프를 빠져나와 graceful 하게 정리한다.
    """
    done = threading.Event()
    error: dict[str, DecodeError] = {}

    def _waiter() -> None:
        try:
            player.wait_for_playback()
        except DecodeError as exc:
            error["decode"] = exc
        finally:
            done.set()

    waiter = threading.Thread(target=_waiter, daemon=True)
    waiter.start()

    with input_factory() as keyboard:
        while not done.is_set() and not stop.is_set():
            action = keyboard.read_action(timeout=_POLL_INTERVAL_SEC)
            if action is None:
                continue
            if controller.handle(action) is False:
                break

    player.quit()  # 종료키/EOF 어느 경우든 mpv 정지를 보장.
    waiter.join(timeout=2.0)
    if "decode" in error:
        raise error["decode"]


def play(
    path: Path,
    config: Config | None = None,
    *,
    player_factory: Callable[[Config], Any] | None = None,
    input_factory: Callable[[], Any] | None = None,
) -> int:
    """영상을 재생하고 종료 코드를 돌려준다."""
    config = config or Config()

    if player_factory is None:
        # 실제 재생 시점에만 libmpv 를 끌어온다.
        from video_player.player import Player

        player_factory = Player
    if input_factory is None:
        from video_player.keyboard import KeyboardInput

        input_factory = KeyboardInput

    player: Any = None
    try:
        with _stop_on_signals() as stop:
            player = player_factory(config)
            controller = Controller(player, config)
            player.load(path)
            _run_loop(player, controller, input_factory, stop)
        return EXIT_OK
    except DecodeError as exc:
        log.error("재생 실패: %s", exc)
        return exc.exit_code
    except PlayerError as exc:
        log.error("오류: %s", exc)
        return exc.exit_code
    finally:
        if player is not None:
            try:
                player.terminate()
            except Exception as exc:  # noqa: BLE001 - 정리 실패가 종료를 막지 않게.
                log.debug("mpv 정리 중 오류 무시: %s", exc)


def main(argv: list[str] | None = None) -> int:
    """진입점. 종료 코드를 돌려준다(console_scripts 가 sys.exit 로 감쌈)."""
    setup_logging()
    parser = _build_parser()
    try:
        namespace = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse: 인자 없음/오류 → 사용법 출력 후 코드 2, 도움말(-h) → 0.
        return int(exc.code) if isinstance(exc.code, int) else EXIT_OK

    path = Path(namespace.path)
    try:
        _validate_media_path(path)
    except ArgumentError as exc:
        log.error("%s", exc)
        return exc.exit_code

    return play(path)

#!/usr/bin/env python3
"""계층 3 — 실기기 스모크 테스트 (미니 PC, 실제 DRM/HDMI).

자동 검증(계층 0·1·2)으로는 잡지 못하는 '진짜 화면/소리' 경로를 미니 PC 에서 확인한다.
확인 항목:
  1. 짧은 클립을 끝까지 재생하고 종료 코드 0 으로 끝나는가.
  2. 생명주기 로그(로드→재생→HW/SW 디코드 경로→EOF→정상 종료)가 보이는가.
  3. 재생 도중 프레임을 파일로 저장해, '검은 화면이 아닌 실제 디코드 프레임'인지 확인.

사용법:
    python scripts/smoke_test.py <영상파일경로> [--screenshot out.png]

주의: 이 스크립트는 DRM/KMS·HDMI 가 있는 리눅스 실기기에서만 의미가 있다.
root 로 실행하지 말 것(video·audio·render 그룹 권한으로 충분).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from video_player.config import Config
from video_player.constants import EXIT_DECODE_ERROR, EXIT_OK
from video_player.errors import DecodeError
from video_player.logging_setup import setup_logging
from video_player.player import Player

log = logging.getLogger("smoke_test")


def _report_decode_path(player: Player) -> None:
    """현재 활성 디코드 경로(HW/SW)를 로그로 남긴다."""
    # 내부 mpv 핸들에서 hwdec-current 를 직접 읽는다(스모크 진단 목적).
    try:
        hwdec = player._mpv.hwdec_current  # noqa: SLF001 - 진단용 접근
    except Exception as exc:  # noqa: BLE001
        log.warning("디코드 경로 확인 실패: %s", exc)
        return
    if hwdec and hwdec not in ("no", b"no"):
        log.info("디코드 경로: 하드웨어(VA-API) — hwdec-current=%s", hwdec)
    else:
        log.info("디코드 경로: 소프트웨어(FFmpeg) 폴백")


def _capture_frame(player: Player, out: Path) -> None:
    """재생 도중 한 프레임을 파일로 저장한다(실제 디코드 증거)."""
    deadline = time.time() + 5.0
    while (player.time_pos or 0.0) < 0.3 and time.time() < deadline:
        time.sleep(0.05)
    try:
        player._mpv.command("screenshot-to-file", str(out), "video")  # noqa: SLF001
        log.info("프레임 저장: %s (검은 화면이 아닌지 사람이 확인)", out)
    except Exception as exc:  # noqa: BLE001
        log.warning("프레임 저장 실패: %s", exc)


def main(argv: list[str] | None = None) -> int:
    setup_logging(logging.DEBUG)
    parser = argparse.ArgumentParser(prog="smoke_test", description=__doc__)
    parser.add_argument("path", help="재생할 영상 파일 경로")
    parser.add_argument("--screenshot", default="smoke_frame.png", help="프레임 저장 경로")
    ns = parser.parse_args(argv)

    path = Path(ns.path)
    if not path.is_file():
        log.error("파일을 찾을 수 없습니다: %s", path)
        return EXIT_DECODE_ERROR

    player = Player(Config())
    try:
        player.load(path)
        time.sleep(0.5)
        _report_decode_path(player)
        _capture_frame(player, Path(ns.screenshot))
        player.wait_for_playback()
        log.info("스모크 테스트 성공: 정상 재생 후 종료(코드 0).")
        return EXIT_OK
    except DecodeError as exc:
        log.error("스모크 테스트 실패(디코드 오류): %s", exc)
        return exc.exit_code
    finally:
        player.terminate()


if __name__ == "__main__":
    sys.exit(main())

"""Player — libmpv(python-mpv) 래퍼 = 재생 엔진.

mpv 초기화, 파일 로드, pause/resume/seek/set_volume/toggle_mute/quit,
EOF·디코드 오류 이벤트 처리를 담당한다. 조작 시 mpv 내장 OSD 로 짧게 정보를 표시한다.

이 모듈은 ``import mpv`` 로 libmpv 에 의존하므로, 인자·파일 검증처럼 mpv 가 필요 없는
경로에서는 import 하지 않는다(통합 테스트와 cli 의 실제 재생 경로에서만 import).
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType
from typing import Any

import mpv

from video_player.config import Config
from video_player.errors import DecodeError

log = logging.getLogger(__name__)

# end-file 사유(바이트). 'error' 만 디코드 실패로 취급한다.
_REASON_ERROR = b"error"
_REASON_EOF = b"eof"


class Player:
    """libmpv 인스턴스를 감싸 재생을 조작하는 엔진(PlayerLike 계약의 실제 구현).

    조작 메서드는 모두 mpv 내장 OSD 로 상태를 짧게 표시한다. 종료 사유는 end-file
    이벤트 콜백이 비동기로 기록하고, wait_for_playback() 이 그 값을 읽어 디코드
    실패면 DecodeError 로 올린다(콜백→상태→예외의 단방향 흐름).

    상태:
        _config: OSD 표시 시간·초기 볼륨 등 정책 값의 출처.
        _mpv: 실제 libmpv 인스턴스.
        _end_reason: end-file 이 남긴 종료 사유(eof/error) — 콜백이 쓰고 wait_for_playback 이 읽음.
        _file_error: 디코드 실패 시 mpv 가 준 상세 메시지.
    """

    def __init__(self, config: Config, overrides: dict[str, Any] | None = None) -> None:
        self._config = config
        self._mpv = mpv.MPV(**config.mpv_options(overrides))
        self._end_reason: bytes | None = None
        self._file_error: str | None = None

        @self._mpv.event_callback("end-file")  # type: ignore[untyped-decorator]
        def _on_end_file(event: Any) -> None:
            data = event.as_dict()
            self._end_reason = data.get("reason")
            file_error = data.get("file_error")
            if isinstance(file_error, bytes):
                self._file_error = file_error.decode(errors="replace")
            log.debug("end-file 이벤트: reason=%r file_error=%r", self._end_reason, file_error)

        self._mpv.volume = config.initial_volume

    # --- 생애주기 ---------------------------------------------------------
    def load(self, path: Path | str) -> None:
        """파일을 로드해 재생을 시작한다(자동 재생)."""
        target = str(path)
        log.info("파일 로드: %s", target)
        self._end_reason = None
        self._file_error = None
        self._mpv.play(target)
        # 시작 시 파일명/길이를 OSD 로 잠깐 표시.
        self._safe_command("show-text", f"{Path(target).name}", self._config.osd_duration_ms)

    def wait_for_playback(self) -> None:
        """재생이 끝날 때까지 블록한다. 디코드 실패면 DecodeError 를 던진다."""
        self._mpv.wait_for_playback()
        if self._end_reason == _REASON_ERROR:
            detail = self._file_error or "알 수 없는 디코드 오류"
            log.error("재생 불가(디코드 실패): %s", detail)
            raise DecodeError(detail)
        log.info("재생 정상 종료(EOF).")

    def quit(self) -> None:
        """재생을 graceful 하게 중단한다(q/Esc 액션)."""
        self._safe_command("quit")

    def terminate(self) -> None:
        """mpv 자원을 정리한다(콘솔/TTY 복구는 입력원 쪽 책임)."""
        self._mpv.terminate()

    def __enter__(self) -> Player:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.terminate()

    # --- 조작 액션 --------------------------------------------------------
    def pause(self) -> None:
        """일시정지하고 OSD 에 ⏸ 를 잠깐 표시한다."""
        self._mpv.pause = True
        self._safe_command("show-text", "⏸", self._config.osd_duration_ms)

    def resume(self) -> None:
        """재생을 재개하고 OSD 에 ▶ 를 표시한다."""
        self._mpv.pause = False
        self._safe_command("show-text", "▶", self._config.osd_duration_ms)

    def seek(self, delta: float) -> None:
        """delta 초만큼 이동하고 진행 상태를 OSD 로 표시한다(경계는 mpv 가 클램프)."""
        # 키프레임 모드 탐색(빠름). 경계는 mpv 가 0~끝으로 클램프한다.
        self._safe_command("seek", delta, "relative+keyframes")
        self._safe_command("show-progress")

    def set_volume(self, volume: int) -> None:
        """볼륨을 설정하고 OSD 에 현재 볼륨을 표시한다."""
        self._mpv.volume = volume
        self._safe_command("show-text", f"볼륨: {volume}%", self._config.osd_duration_ms)

    def toggle_mute(self) -> None:
        """음소거를 토글하고 상태를 OSD 로 표시한다."""
        self._mpv.mute = not self._mpv.mute
        label = "음소거" if self._mpv.mute else "음소거 해제"
        self._safe_command("show-text", label, self._config.osd_duration_ms)

    # --- 읽기 전용 속성(검증·표시용) --------------------------------------
    @property
    def paused(self) -> bool:
        """현재 일시정지 상태."""
        return bool(self._mpv.pause)

    @property
    def muted(self) -> bool:
        """현재 음소거 상태."""
        return bool(self._mpv.mute)

    @property
    def volume(self) -> float:
        """현재 볼륨(0~100)."""
        return float(self._mpv.volume)

    @property
    def time_pos(self) -> float | None:
        """현재 재생 위치(초). 아직 시작 전이면 None."""
        pos = self._mpv.time_pos
        return None if pos is None else float(pos)

    # --- 내부 ------------------------------------------------------------
    def _safe_command(self, *args: Any) -> None:
        """OSD/탐색 등 보조 명령은 종료 직전 등 상황에서 실패할 수 있어 삼킨다."""
        try:
            self._mpv.command(*args)
        except Exception as exc:  # noqa: BLE001 - 보조 명령 실패는 재생을 막지 않는다.
            log.debug("mpv 명령 무시(%r): %s", args, exc)

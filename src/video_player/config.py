"""재생 설정 — mpv 옵션(보안·성능·출력)과 조작 단위를 한곳에 모은다.

mpv 옵션 키는 python-mpv 에 ``**kwargs`` 로 전달되므로 모두 파이썬 식별자(밑줄)로
표기한다. python-mpv 가 내부에서 밑줄을 하이픈으로 바꿔 실제 mpv 옵션명에 맞춘다.
출력 옵션(DRM/KMS·HDMI 오디오)은 리눅스 실기기용 기본값이며, 통합 테스트나 다른
환경에서는 ``mpv_options(overrides=...)`` 로 덮어쓴다(예: ``vo='null'``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from video_player.constants import SEEK_STEP_SEC, VOLUME_MAX, VOLUME_STEP


@dataclass(frozen=True)
class Config:
    """재생에 필요한 설정 값을 한데 묶은 불변(frozen) 번들.

    두 종류를 구분해 담는다 — (1) 우리 코드가 직접 쓰는 조작 단위(seek 폭·볼륨),
    (2) libmpv 에 넘길 출력·디코딩 옵션(후자는 ``mpv_options()`` 가 보안 기본값과
    합쳐 조립). frozen 이라 생성 후 못 바꾼다 — 재생 도중 설정이 바뀌는 혼란을 막는다.
    필드별 의미는 각 필드의 주석을 본다.
    """

    # 조작 단위.
    seek_step_sec: int = SEEK_STEP_SEC
    volume_step: int = VOLUME_STEP
    initial_volume: int = VOLUME_MAX

    # 출력(리눅스 실기기 기본값) — DRM/KMS 직접 렌더링 → HDMI 영상+음성.
    vo: str = "gpu"
    gpu_context: str = "drm"
    ao: str = "alsa"

    # 디코딩 정책(성능·자원 노트).
    hwdec: str = "auto-safe"

    # 시작 OSD 표시 시간(밀리초) 및 조작 OSD 표시 시간(밀리초).
    osd_duration_ms: int = 1500

    # 추가/실험용 mpv 옵션 override.
    extra: dict[str, Any] = field(default_factory=dict)

    def mpv_options(self, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        """python-mpv 에 splat 할 mpv 옵션 딕셔너리를 만든다."""
        opts: dict[str, Any] = {
            # --- 보안: 우리가 정의한 키만, 외부 스크립트 차단 ---
            "input_default_bindings": "no",
            "input_vo_keyboard": "no",
            "load_scripts": "no",
            "osc": "no",
            # --- 디코딩·프레임 드롭 ---
            "hwdec": self.hwdec,
            "framedrop": "vo",
            # --- 디코더 선행 버퍼(SW 디코딩 스파이크 흡수) ---
            "vd_queue_enable": "yes",
            "ad_queue_enable": "yes",
            "vd_queue_max_secs": 15,
            "vd_queue_max_bytes": "2000MiB",
            # --- 압축 데이터 읽기 캐시(I/O 지터 완화) ---
            "cache": "yes",
            "demuxer_max_bytes": "512MiB",
            # --- 출력 ---
            "vo": self.vo,
            "ao": self.ao,
            # --- OSD 표시 시간 ---
            "osd_duration": self.osd_duration_ms,
        }
        opts.update(self.extra)
        if overrides:
            opts.update(overrides)
        # gpu-context 는 vo=gpu 일 때만 유효하다(다른 vo 에선 libmpv 가 거부).
        # override 까지 반영한 최종 vo 를 기준으로 판단한다.
        if opts.get("vo") == "gpu":
            opts["gpu_context"] = self.gpu_context
        return opts

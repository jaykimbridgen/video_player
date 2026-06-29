"""도메인 전역 상수 — 키 조작 단위, 볼륨 범위, 종료 코드."""

from __future__ import annotations

# 탐색(seek) 한 번에 이동하는 시간(초).
SEEK_STEP_SEC: int = 5

# 볼륨 한 번에 조절하는 폭(%).
VOLUME_STEP: int = 5

# 볼륨 허용 범위(부스트 없음).
VOLUME_MIN: int = 0
VOLUME_MAX: int = 100

# 종료 코드.
EXIT_OK: int = 0
EXIT_ARG_ERROR: int = 2
EXIT_DECODE_ERROR: int = 3

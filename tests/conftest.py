"""pytest 공용 설정 및 픽스처.

- Windows 개발 머신에서 통합 테스트(계층 2)를 돌릴 때, ``MPV_DLL_DIR`` 환경변수로
  libmpv DLL 디렉터리를 알려주면 ``import mpv`` 전에 PATH 에 추가한다.
  (리눅스 실기기에서는 시스템 로더가 libmpv 를 찾으므로 이 처리가 필요 없다.)
- 테스트용 영상 픽스처는 저장소에 바이너리를 넣지 않고 ffmpeg 로 즉석 생성한다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# --- Windows: import mpv 전에 libmpv DLL 디렉터리를 PATH 에 주입 ---------------
if sys.platform == "win32":
    _dll_dir = os.environ.get("MPV_DLL_DIR")
    if _dll_dir and os.path.isdir(_dll_dir):
        os.add_dll_directory(_dll_dir)
        os.environ["PATH"] = _dll_dir + os.pathsep + os.environ["PATH"]


def _ffmpeg() -> str:
    """ffmpeg 실행 파일 경로. 없으면 통합 테스트를 건너뛴다."""
    exe = shutil.which("ffmpeg")
    if exe is None:
        pytest.skip("ffmpeg 가 PATH 에 없어 테스트 영상을 생성할 수 없습니다.")
    return exe


@pytest.fixture(scope="session")
def test_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """재생 가능한 짧은 테스트 영상(영상+음성)을 ffmpeg 로 생성한다."""
    out = tmp_path_factory.mktemp("media") / "test.mp4"
    subprocess.run(
        [
            _ffmpeg(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=320x240:rate=10",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(out),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


@pytest.fixture(scope="session")
def broken_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """디코드 불가 파일: .mp4 확장자에 쓰레기 바이트만 채운다."""
    out = tmp_path_factory.mktemp("media") / "broken.mp4"
    out.write_bytes(b"\x00\x01\x02not a real video\xff\xfe" * 64)
    return out

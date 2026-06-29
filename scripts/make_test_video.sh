#!/usr/bin/env bash
# 테스트용 짧은 영상(영상+음성)을 ffmpeg 로 생성한다.
# 저장소에는 바이너리를 넣지 않으므로, 수동 검증·스모크 테스트 시 이 스크립트로 만든다.
#
# 사용법: scripts/make_test_video.sh [출력경로]   (기본: ./test.mp4)
set -euo pipefail

out="${1:-test.mp4}"

ffmpeg -y \
    -f lavfi -i "testsrc=duration=5:size=1280x720:rate=30" \
    -f lavfi -i "sine=frequency=440:duration=5" \
    -c:v libx264 -pix_fmt yuv420p \
    -c:a aac \
    -shortest \
    "$out"

echo "생성 완료: $out"

# OVERVIEW — video_player

## 목적
독립적으로 재사용 가능한 동영상 재생 프로그램. 1차 목표는 **파일럿**으로서
계획(Claude Desktop) → 구현(claude-cli) 워크플로우를 검증하고, 결과물이 괜찮으면 코드를 재사용한다.

## 실행 환경
- **H/W**: Dell 미니 PC (x86-64, Intel 내장 그래픽 가정)
- **OS**: Ubuntu Linux, **GUI 없는 헤드리스** 설치 (데스크톱 환경 없음)
- **출력**: DRM/KMS 직접 렌더링 → **HDMI로 영상 + 음성**
- **실행 형태**: 터미널에서 `player <파일>`로 실행하는 **단발 실행형**
- **기기 성격**: (현재) 영상 재생 전용

## 범위 (이번 파일럿)

**포함:**
- 단일 동영상 파일 재생 — "뭐든 재생"(광범위한 포맷/코덱)
- 재생 중 키보드 조작: 일시정지/재생, 탐색(±5초), 볼륨, 음소거, 종료
- 간단한 OSD (조작 시 잠깐 표시 후 자동 사라짐)
- 하드웨어 디코딩(VA-API) + 소프트웨어 자동 폴백

**범위 밖 (이번 파일럿 제외 → PM_NOTES의 추후 항목):**
- 자막, 재생목록/큐, 이어보기(상태 저장)
- 오디오 패스스루(돌비/DTS 비트스트림) — PCM 디코드 출력만
- 프론트엔드, IPC, 블루투스 리모컨

## 저장소
- https://github.com/jaykimbridgen/video_player
- HTTPS: `https://github.com/jaykimbridgen/video_player.git`
- SSH: `git@github.com:jaykimbridgen/video_player.git`

## 개발 환경 (잠정 — 확정 전)
- 개발: Windows + VS Code. Python 코드 생성 자체는 플랫폼 무관.
- 검증: DRM/KMS·VA-API·TTY·evdev는 **리눅스 전용**이라 실하드웨어 검증은 미니 PC에서만 가능.
- 현재 유력안: **VS Code Remote-SSH로 미니 PC에 접속해 미니 PC에서 직접 개발·검증**
  (claude-cli도 미니 PC에서 실행). → 최종 확정 시 이 절을 갱신.

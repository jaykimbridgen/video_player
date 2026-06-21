# CLAUDE.md — video_player

헤드리스 Ubuntu 미니 PC에서 터미널로 실행해 동영상 파일을 HDMI(모니터+스피커)로 재생하는 **단발 실행형** 플레이어.

- 저장소: https://github.com/jaykimbridgen/video_player

## 구현 전 반드시 읽을 것
구현을 시작하기 전에 `docs/`의 다음 문서를 먼저 읽고 그 결정을 따른다.

- `docs/OVERVIEW.md` — 목적·환경·범위
- `docs/SPEC.md` — 핵심 재생 기능 세부, 디렉터리 구조, 검증 전략, 보안 가이드 **(구현의 핵심)**
- `docs/성능_자원_노트.md` — 성능·자원 정책 (디코딩·버퍼 설정)
- `docs/PM_NOTES.md` — PM 인지용(라이선스 등). **구현 대상 아님 — 참고만.**

## 기술 스택
- 언어: **Python**
- 재생 코어: **mpv / libmpv** (python-mpv 바인딩), 내부적으로 FFmpeg
- 출력: **DRM/KMS 직접 렌더링 → HDMI**(영상+음성). 데스크톱 환경 없음(헤드리스).
- 레이아웃: **src-layout** (`src/video_player/`)

## 코드 규칙
- 스타일: **PEP 8**
  - 파일/모듈 `snake_case.py`, 패키지 `lowercase`, 클래스 `PascalCase`,
    함수·변수 `snake_case`, 상수 `UPPER_SNAKE_CASE`, 비공개 `_leading`
- 도메인 용어(일관 유지): `Player`, `Controller`, `Config`
  - 액션: `pause` · `resume` · `seek` · `set_volume` · `toggle_mute` · `quit`
  - 진입점 `main.py`, CLI 명령 `player`
  - 상수: `SEEK_STEP_SEC`(=5), `VOLUME_STEP`(=5),
    종료 코드 `EXIT_OK` · `EXIT_ARG_ERROR` · `EXIT_DECODE_ERROR`
- **언어 정책**:
  - 코드·식별자 = **영어**
  - 주석·독스트링·로그·에러 메시지 = **한국어**
- 테스트 파일: `test_*.py`

## 빌드 / 실행 / 검증
```bash
# 설치 (개발 모드)
pip install -e .

# 실행
player <영상파일경로>

# 검증
ruff check . && black --check . && mypy src    # 계층 0: 정적
pytest -m "not integration"                     # 계층 1: 단위(mock Player)
pytest -m integration                           # 계층 2: 통합(실 mpv, --vo=null)
python scripts/smoke_test.py <영상파일경로>      # 계층 3: 실기기(미니 PC, DRM/HDMI)
```

## 핵심 제약 (상세는 docs/SPEC.md)
- 키 입력은 **우리가 정의한 키만** 활성(mpv 기본 키 비활성, `input-default-bindings=no`).
- 재생 불가 파일은 죽지 말고(hang 금지) 명확한 로그 + 정상 종료(코드 3).
- **root로 실행하지 않는다**(최소 권한).
- 플랫폼 의존 코드(DRM·TTY·evdev 등)는 얇은 경계 뒤에 격리해, 순수 로직은 어디서든 import·테스트 가능하게 한다.

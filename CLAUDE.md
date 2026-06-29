# CLAUDE.md — video_player

헤드리스 Ubuntu 미니 PC에서 터미널로 실행해 동영상 파일을 HDMI(모니터+스피커)로 재생하는 **단발 실행형** 플레이어.

- 저장소: https://github.com/jaykimbridgen/video_player

## 구현 전 반드시 읽을 것
구현을 시작하기 전에 `docs/`의 다음 문서를 먼저 읽고 그 결정을 따른다.

- `docs/OVERVIEW.md` — 목적·환경·범위
- `docs/SPEC.md` — 핵심 재생 기능 세부, 디렉터리 구조, 검증 전략, 보안 가이드 **(구현의 핵심)**
- `docs/성능_자원_노트.md` — 성능·자원 정책 (디코딩·버퍼 설정)
- `docs/PM_NOTES.md` — PM 인지용(라이선스 등). **구현 대상 아님 — 참고만.**

## 코드 변경·설계 규칙 (항상 적용)
- **기존 코드를 수정하거나 기능을 추가할 때는 먼저 `docs/ARCHITECTURE.md`(압축된 모듈 맵·데이터 흐름·불변 규칙)를 참조해 계획한다.** 전체 소스를 처음부터 다시 읽기 전에 이 지도로 영향 범위를 먼저 파악한다.
- 모듈 책임·데이터 흐름·불변 규칙을 바꾸는 변경은 **같은 작업에서 `docs/ARCHITECTURE.md`도 함께 갱신**한다(문서가 코드와 어긋나면 안 됨).

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
- **주석 규칙** (이름·타입·구조로 *무엇*을 드러내고, 주석은 *왜*에 아껴 쓴다):
  - 코드가 *무엇을* 하는지 그대로 옮긴 주석은 금지 (코드 변경 시 거짓말이 됨).
  - 코드에 안 드러나는 것만 주석으로 남긴다 — **의도·이유, 트레이드오프, 암묵적 제약, 왜 이 방식인가**.
    (예: "cbreak: …신호(Ctrl+C)는 살려 graceful 종료 유도" 처럼 *왜 그 선택인지*.)
  - 좋은 이름은 주석의 필요를 줄인다. 모호한 이름을 주석으로 때우지 말고 이름을 고친다.
  - 도메인 어휘는 위 "도메인 용어"를 따른다(임의 동의어 금지). 새 도메인 개념은 합의 후 용어집에 추가.
- **docstring 규칙**:
  - 공개(밑줄 없는) 모듈·클래스·메서드엔 docstring을 단다. 내용은 위 주석 규칙과 같다 —
    코드를 옮기지 말고 *역할·왜·제약*을 적는다(시그니처는 코드/타입힌트가 이미 말한다).
  - 상태를 보유한 클래스는 docstring에 `상태:` 섹션으로 인스턴스 속성의 *의미*를 적는다.
  - 모듈의 공개 표면은 `__all__` 로 선언하고 **실제 공개와 일치**시킨다(검증은 계층 0·1).
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

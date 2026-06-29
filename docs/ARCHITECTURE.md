# ARCHITECTURE.md — 코드 지도

소스 전체를 다시 읽지 않고 **기능 추가·설계 시 빠르게 참조**하기 위한 압축 지도다.
서술형 학습 자료가 필요하면 `docs/소스코드_가이드.md`, 왜·무엇은 `docs/SPEC.md` 를 본다.

> **갱신 규칙**: 이 문서는 코드와 어긋나면 위험하다. 모듈 책임·데이터 흐름·불변 규칙을
> 바꾸는 변경은 **같은 작업(PR)에서 이 문서도 함께 고친다.**

## 모듈 맵 (`src/video_player/`)

| 모듈 | 책임 | 의존 / 비고 |
|---|---|---|
| `__main__.py` | `python -m video_player` 진입 → `cli.main` 호출 | — |
| `cli.py` | 인자 파싱·파일 검증, `Config`/`Player`/`Controller`/키보드 **조립**, 재생 루프, 예외→종료코드 매핑 | mpv 는 재생 시점에만 lazy import |
| `controller.py` | `Action` enum, `PlayerLike` Protocol, `Controller`(일시정지 토글·볼륨 0~100 클램프 **상태 보유**) | 순수(플랫폼 무관) |
| `keyboard.py` | `parse_key(bytes)->Action`(**순수**), `KeyboardInput`(리눅스 TTY 원시 모드 입력원) | termios/tty/select 는 메서드 안에서 lazy import |
| `player.py` | libmpv(python-mpv) 래퍼 = 재생 엔진. 로드·조작·EOF/디코드 이벤트 처리, OSD 표시 | `import mpv` (모듈 최상단) |
| `config.py` | `Config` dataclass, `mpv_options()` = 보안·성능·출력 옵션 조립 | mpv 옵션은 밑줄 표기(python-mpv 가 변환) |
| `constants.py` | `SEEK_STEP_SEC=5`, `VOLUME_STEP=5`, `VOLUME_MIN/MAX=0/100`, 종료코드 | — |
| `errors.py` | `PlayerError`(1) / `ArgumentError`(2) / `DecodeError`(3), 각자 `exit_code` 보유 | — |
| `logging_setup.py` | 한국어 메시지 stderr 로깅(중복 호출 안전) | — |

## 데이터 흐름 (단방향)

```
[키 입력 TTY bytes]
      │ keyboard.parse_key
      ▼
   Action ──► Controller.handle ──► PlayerLike(Player) ──► mpv ──► DRM/KMS → HDMI
                  │                        ▲
       (pause 토글·볼륨 클램프 상태)        │
                                  cli.play 가 조립·주입
                                  (player_factory / input_factory)
```

재생 종료 경로(별도 스레드):

```
player.wait_for_playback()  ── EOF(reason=eof) ─► 정상 종료(0)
   (cli._run_loop 의 _waiter)  └ 디코드 실패(reason=error) ─► DecodeError ─► 종료코드 3
```

`_run_loop` 은 **종료키(q/Esc)·신호(SIGINT/TERM)·EOF** 중 무엇이든 발생하면 루프를 빠져나와
`player.quit()` → `terminate()` 로 graceful 정리한다(0.2초 폴링으로 종료 조건 확인).

## 불변 규칙 (설계 시 위반 금지)

1. **순수 로직 / 플랫폼 경계 분리** — `parse_key`·`Controller`·`Config` 는 어디서든 import·테스트 가능.
   플랫폼 의존(termios·mpv·DRM)은 얇은 경계 뒤로 격리하고 **사용 시점 lazy import**.
2. **의존성 주입** — `play(player_factory=, input_factory=)` 로 가짜를 끼워 계층 1 단위 테스트.
   새 입력원(evdev·IPC 등)은 같은 `(bytes/이벤트 → Action)` 패턴으로 추가.
3. **우리가 정의한 키만** — `input_default_bindings=no` 등(`config.py`). mpv 기본 키 활성 금지.
4. **재생 불가 시 hang 금지** — 명확한 로그 + `DecodeError`(종료코드 3)로 정상 종료.
5. **종료코드 계약** — 정상 0 / 인자·파일 오류 2 / 디코드 실패 3. 예외는 `errors.py` 에서 매핑.
6. **최소 권한** — root 실행 금지.
7. **언어 정책** — 코드·식별자 = 영어, 주석·독스트링·로그·메시지 = 한국어.
8. **출력 기본값은 실기기용** — `vo=gpu`/`gpu_context=drm`(vo=gpu 일 때만)/`ao=alsa`.
   테스트·타 환경은 `mpv_options(overrides=...)` 로 덮어쓴다(예: `vo='null'`).

## 검증 계층 (상세는 `README.md`·`CLAUDE.md`)

| 계층 | 대상 | 명령 |
|---|---|---|
| 0 | 정적 | `ruff check . && black --check . && mypy src` |
| 1 | 단위(mock Player) | `pytest -m "not integration"` |
| 2 | 통합(실 libmpv, vo/ao=null) | `pytest -m integration` |
| 3 | 실기기(미니 PC, DRM/HDMI) | `python scripts/smoke_test.py <파일>` |

# SPEC — video_player

핵심 재생 기능 세부, 디렉터리 구조, 검증 전략, 보안 가이드. **이 문서는 구현 대상이다.**

---

## 1. 실행 인터페이스
- 명령: `player <영상파일경로>` — 인자 1개(파일 경로).
- 인자 없음 → 사용법(usage) 출력 후 종료(코드 2).
- 파일 없음 / 접근 불가 → 명확한 에러 메시지 후 종료(코드 2).
- 단일 파일만 지원 (여러 파일·재생목록은 범위 밖).

## 2. 시작 동작
- 실행 즉시 mpv 초기화 → 파일 로드 → **자동 재생(autoplay)**.
- mpv 초기화: DRM/KMS 출력, HDMI 오디오, `hwdec=auto-safe`, 디코드 버퍼(7절 및 성능 노트).
- 시작 시 OSD로 파일명/길이를 잠깐 표시.

## 3. 키 조작 (재생 중) — *우리가 정의한 키만* 활성
mpv 기본 키바인딩은 끈다(`input-default-bindings=no`). 아래 키만 동작한다.

| 키 | 액션 | 비고 |
|---|---|---|
| Space | 일시정지 ⇄ 재생 토글 | OSD ⏸ |
| ← / → | `seek` ∓ `SEEK_STEP_SEC`(=5초) | **키프레임 모드**, 경계 0~끝 클램프, OSD 진행바+시간 |
| ↑ / ↓ | `set_volume` ±`VOLUME_STEP`(=5%) | 범위 **0~100**(부스트 없음), OSD 볼륨바 |
| m | `toggle_mute` | OSD |
| q, Esc | `quit` | graceful shutdown |

## 4. OSD
- 트리거: 일시정지·탐색·볼륨·음소거.
- 각 조작 시 관련 정보(진행바/시간/볼륨/아이콘)를 표시 후 **약 1~2초 뒤 자동 사라짐**.
- **mpv 내장 OSD 사용.** (목업은 '지향하는 모습' 참고용이며 픽셀 단위 일치는 불필요.)

## 5. 재생 종료 동작
- 영상 끝 도달 → 프로그램 **정상 종료(코드 0)**, 터미널 복귀.
- (마지막 프레임 유지·반복·다음 영상은 범위 밖.)

## 6. 종료 · 신호 · 로그
- `q`/`Esc`, 영상 끝, `SIGINT`(Ctrl+C), `SIGTERM` 모두 **graceful shutdown**:
  mpv 정리 + 콘솔/TTY 상태 복구 후 종료. (SIGTERM 처리는 추후 프론트가 자식을 종료시킬 때 중요.)
- **종료 코드**:

  | 상수 / 값 | 의미 |
  |---|---|
  | `EXIT_OK` = 0 | 정상 종료 |
  | 1 | 일반 오류 |
  | `EXIT_ARG_ERROR` = 2 | 인자·파일 오류 |
  | `EXIT_DECODE_ERROR` = 3 | 디코드·재생 불가 |

- 로그: 사람이 읽기 쉬운 **한국어** 메시지를 stderr로. (로그파일 옵션은 추후.)

## 7. 디코딩 · 오류 처리 ("뭐든 재생")
- 소프트웨어 디코딩(FFmpeg)을 만능 기본값으로, VA-API 하드웨어 디코딩은 가능 시 사용하고
  실패 시 **자동 SW 폴백**(로그에 사용 경로 표시).
- 깨진 파일/희귀 코덱으로 디코드 불가 → mpv 오류 이벤트 포착 → 명확 로그 + graceful 종료(코드 3). **멈춤(hang) 금지.**
- 권장 mpv 옵션·디코드 선행 버퍼 상세는 `docs/성능_자원_노트.md` 참고.

## 8. 코드 구조 (재사용 지향)
흐름: **`입력원 → Controller → Player → mpv`** (단방향). 입력원만 교체하면 나머지를 재사용할 수 있게 설계한다.

- **`Player`** (`player.py`): mpv/libmpv 래퍼 = 재생 엔진. mpv 초기화, 파일 로드,
  `pause`/`resume`/`seek`/`set_volume`/`toggle_mute`/`quit`, EOF·오류 이벤트 처리.
- **`Controller`** (`controller.py`): 추상 action을 받아 `Player` 메서드를 호출. **입력원과 Player의 분리막.**
- **입력원** (`keyboard.py`): 키 입력을 action으로 변환해 Controller에 전달.
  (추후 evdev/IPC를 같은 패턴으로 추가할 수 있도록 입력원 인터페이스를 깔끔히 둘 것.)
- **`cli.py`**: 인자 파싱, `Config`·`Player`·`Controller`·키보드 입력원 조립, 실행 루프.

### 디렉터리 구조 (src-layout)
```
video_player/
├── CLAUDE.md
├── README.md
├── pyproject.toml            # 의존성 + 엔트리포인트(player)
├── .github/workflows/ci.yml  # CI (계층 0·1·2)
├── scripts/
│   ├── make_test_video.sh    # ffmpeg로 테스트 영상 생성
│   └── smoke_test.py         # 실기기 스모크 테스트 (계층 3)
├── docs/
│   ├── OVERVIEW.md
│   ├── SPEC.md
│   ├── 성능_자원_노트.md
│   └── PM_NOTES.md
├── src/
│   └── video_player/
│       ├── __init__.py
│       ├── __main__.py       # python -m video_player
│       ├── cli.py
│       ├── player.py
│       ├── controller.py
│       ├── config.py
│       ├── constants.py
│       ├── errors.py
│       ├── logging_setup.py
│       └── keyboard.py
└── tests/
    ├── conftest.py
    ├── test_controller.py
    ├── test_config.py
    ├── test_cli.py
    └── test_playback_integration.py
```

## 9. 검증 전략
계층별로 나누어, 가능한 한 claude-cli가 **스스로** 검증한다.

- **계층 0 — 정적 검사**: `ruff`(PEP 8), `black --check`(포맷), `mypy`(타입).
- **계층 1 — 단위 테스트** (mpv 없이, mock `Player`):
  - 키→액션 매핑(Space→일시정지 토글, →→`seek(+5)` 등), `Config` 기본값·상수, 종료 코드,
    CLI 인자(없음→사용법+코드2, 없는 파일→에러+코드2).
  - **주의**: 플랫폼 의존 모듈(`termios`, `/dev/*` 등)을 import 시점에 끌어오지 않도록 격리
    (Windows/CI에서도 import 가능해야 함). 마커 없이 항상 실행.
- **계층 2 — 통합 테스트** (실 mpv, `--vo=null --ao=null`):
  - 파일 로드 성공, `pause`/`time-pos`/`volume`/`mute` 속성 변화, EOF→코드0,
    깨진/없는 파일→올바른 에러·종료 코드.
  - pytest 마커 `integration`으로 분리(평소 단위만 빠르게, CI에선 둘 다).
- **계층 3 — 실기기 스모크 테스트** (미니 PC, 실제 DRM/HDMI): `scripts/smoke_test.py`
  - 짧은 클립 재생 후 코드 0 종료, 로그 생명주기(로드→재생→HW/SW 경로→EOF→정상 종료) 확인,
    프레임을 파일로 출력해 *검은 화면이 아닌 실제 프레임 디코드* 확인(정확한 방법은 mpv 옵션으로 확정).
- **테스트 영상 픽스처**: 저장소에 바이너리를 넣지 않고 `conftest`에서 ffmpeg로 즉석 생성.
  예: `ffmpeg -f lavfi -i testsrc=duration=2 -f lavfi -i sine=duration=2 test.mp4`
- **CI** (`.github/workflows/ci.yml`): mpv/libmpv 설치 후 계층 0·1·2 자동 실행.
  계층 3은 하드웨어가 필요해 CI 밖(미니 PC에서 수동/별도 실행).
- **사람의 최종 확인**: 모니터 영상(색·아티팩트), 스피커 소리, 체감 부드러움. — 이 부분만 사람 몫.

## 10. 보안 가이드 (구현 대상)
현재 스코프(로컬·수동 실행·네트워크 없음)는 공격 표면이 작다. 다음을 적용한다.

- **신뢰할 수 없는 미디어 = 주 표면**: mpv·FFmpeg·시스템 라이브러리를 최신 보안 패치 상태로 유지.
- **root로 실행 금지**: 전용 사용자에 필요한 그룹(video·audio·input·render)만 부여.
- **셸 인젝션 회피**: 파일명을 셸로 넘기지 않는다. `shell=True`/문자열 조립 금지, 인자 배열 사용.
  (python-mpv는 셸을 거치지 않아 기본 안전 — 스모크 스크립트 등에서도 동일 원칙.)
- **mpv 설정·스크립트 로딩 잠금**: 우리 설정만 사용, 외부 스크립트 로딩 끔(`load-scripts=no` 등).
- **의존성 관리**: 버전 고정·잠금파일, 주기적 업데이트.
- (샌드박싱·서비스 하드닝·IPC 표면 등 *추후* 보안 항목은 `docs/PM_NOTES.md` 참고.)

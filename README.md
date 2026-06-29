# video_player

헤드리스 Ubuntu 미니 PC에서 터미널로 실행해, 파일시스템의 동영상 파일을 HDMI(모니터+스피커)로 재생하는 **단발 실행형** 플레이어.

- 저장소: https://github.com/jaykimbridgen/video_player

## 요구 환경
- Ubuntu Linux (헤드리스 / 데스크톱 환경 불필요)
- mpv / libmpv, FFmpeg
- Python 3.x
- (하드웨어 디코딩 시) Intel VA-API 드라이버

## 설치
```bash
# 시스템 의존성
sudo apt install mpv libmpv-dev
sudo apt install intel-media-va-driver vainfo   # (선택) 하드웨어 디코딩

# 패키지 설치 (개발 모드)
pip install -e .
```

## 실행
```bash
player <영상파일경로>
```

재생 중 조작 키:

| 키 | 동작 |
|---|---|
| Space | 일시정지 / 재생 |
| ← / → | 5초 뒤로 / 앞으로 |
| ↑ / ↓ | 볼륨 내림 / 올림 |
| m | 음소거 |
| q, Esc | 종료 |

## 개발 / 검증
검증은 계층으로 나뉜다(자세한 전략은 `docs/SPEC.md` 9절).
```bash
ruff check . && black --check . && mypy src    # 계층 0: 정적 검사
pytest -m "not integration"                     # 계층 1: 단위 (mpv 불필요)
pytest -m integration                           # 계층 2: 통합 (실 mpv, --vo/ao=null)
python scripts/smoke_test.py <영상파일경로>      # 계층 3: 실기기 (미니 PC, DRM/HDMI)
```

### Windows 개발 머신에서 계층 2(통합 테스트) 돌리기
계층 2는 실제 libmpv 가 필요하다. 리눅스/CI 는 시스템 libmpv 를 자동으로 찾으므로 추가
설정이 없지만, Windows 에서는 libmpv DLL 을 직접 준비하고 그 위치를 알려줘야 한다.

1. **libmpv 받기** — mpv-player-windows 의 libmpv dev 빌드(예: SourceForge)에서
   `libmpv-2.dll` 을 받아 한 폴더(예: `C:\libmpv\`)에 둔다. python-mpv 가 `mpv-2.dll`
   이름도 찾으므로, 같은 폴더에 `mpv-2.dll` 로 복사본을 하나 더 둔다.
2. **환경변수로 알려주기** — 그 폴더를 `MPV_DLL_DIR` 로 지정한다. `tests/conftest.py` 가
   `import mpv` *전에* 이 경로를 PATH 에 끼워 넣는다.
   ```powershell
   $env:MPV_DLL_DIR = "C:\libmpv"
   pytest -m integration
   ```
   `MPV_DLL_DIR` 가 없거나 libmpv 를 못 찾으면, 통합 테스트 모듈은 오류 없이 **자동 skip** 된다.

> 참고: Windows + 최신 Python 에서 통합 테스트 중 `Windows fatal exception: code 0x...`
> 와 C 스택 덤프가 찍힐 수 있으나, 이는 libmpv 의 비치명적 노이즈이며 테스트는 통과한다
> (종료 코드 0). 깔끔히 보려면 `pytest -m integration -p no:faulthandler`. 리눅스 실기기·
> CI 에서는 나타나지 않는다.

## 문서
설계·명세·정책은 `docs/`를 참고:
- `docs/OVERVIEW.md` — 목적·환경·범위
- `docs/SPEC.md` — 핵심 기능·구조·검증·보안
- `docs/성능_자원_노트.md` — 성능·자원 정책
- `docs/PM_NOTES.md` — 라이선스 등 PM 인지용

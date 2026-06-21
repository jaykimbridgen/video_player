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
```bash
ruff check . && black --check . && mypy src    # 정적 검사
pytest                                          # 테스트 (단위 + 통합)
```

## 문서
설계·명세·정책은 `docs/`를 참고:
- `docs/OVERVIEW.md` — 목적·환경·범위
- `docs/SPEC.md` — 핵심 기능·구조·검증·보안
- `docs/성능_자원_노트.md` — 성능·자원 정책
- `docs/PM_NOTES.md` — 라이선스 등 PM 인지용

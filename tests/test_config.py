"""상수·예외·Config 단위 테스트 (계층 1, mpv 불필요)."""

from __future__ import annotations

from video_player import constants
from video_player.config import Config
from video_player.errors import ArgumentError, DecodeError, PlayerError


def test_step_constants() -> None:
    assert constants.SEEK_STEP_SEC == 5
    assert constants.VOLUME_STEP == 5


def test_volume_bounds() -> None:
    assert constants.VOLUME_MIN == 0
    assert constants.VOLUME_MAX == 100


def test_exit_codes() -> None:
    assert constants.EXIT_OK == 0
    assert constants.EXIT_ARG_ERROR == 2
    assert constants.EXIT_DECODE_ERROR == 3


def test_error_exit_codes() -> None:
    assert ArgumentError("x").exit_code == constants.EXIT_ARG_ERROR
    assert DecodeError("x").exit_code == constants.EXIT_DECODE_ERROR
    # 일반 오류는 기본 종료 코드 1.
    assert PlayerError("x").exit_code == 1


def test_config_defaults() -> None:
    cfg = Config()
    assert cfg.seek_step_sec == constants.SEEK_STEP_SEC
    assert cfg.volume_step == constants.VOLUME_STEP
    assert cfg.initial_volume == constants.VOLUME_MAX


def test_mpv_options_security() -> None:
    opts = Config().mpv_options()
    # 우리가 정의한 키만 활성: mpv 기본 키바인딩을 끈다.
    assert opts["input_default_bindings"] == "no"
    # 외부 스크립트 로딩 잠금.
    assert opts["load_scripts"] == "no"


def test_mpv_options_performance() -> None:
    opts = Config().mpv_options()
    # 성능 노트의 디코딩 정책이 반영되어야 한다.
    assert opts["hwdec"] == "auto-safe"
    assert opts["framedrop"] == "vo"
    assert opts["cache"] == "yes"


def test_gpu_context_present_only_for_vo_gpu() -> None:
    # 실기기 기본값(vo=gpu)에서는 gpu_context 가 포함된다.
    assert Config().mpv_options()["gpu_context"] == "drm"
    # vo 를 다른 값으로 바꾸면 gpu_context 는 빠진다(다른 vo 에선 오류이므로).
    assert "gpu_context" not in Config().mpv_options(overrides={"vo": "null"})


def test_mpv_options_keys_are_python_identifiers() -> None:
    # python-mpv 에 **kwargs 로 splat 하므로 키는 모두 식별자(밑줄)여야 한다.
    opts = Config().mpv_options()
    assert opts
    for key in opts:
        assert key.isidentifier(), key

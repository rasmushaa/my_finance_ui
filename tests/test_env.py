"""Basic tests for environment helper functions."""

from __future__ import annotations

import pytest

from src.core.env import app_environment, environment_badge_suffix, require_env


def test_require_env_returns_value_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    """`require_env` returns value for existing env var."""
    monkeypatch.setenv("UNIT_TEST_ENV", "value")
    assert require_env("UNIT_TEST_ENV") == "value"


def test_require_env_raises_for_missing_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """`require_env` raises RuntimeError for missing env var."""
    monkeypatch.delenv("UNIT_TEST_ENV", raising=False)
    with pytest.raises(RuntimeError):
        require_env("UNIT_TEST_ENV")


def test_app_environment_defaults_to_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    """`app_environment` uses dev default when ENV is missing."""
    monkeypatch.delenv("ENV", raising=False)
    assert app_environment() == "dev"


def test_environment_badge_suffix_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """`environment_badge_suffix` formats expected suffix."""
    monkeypatch.setenv("ENV", "stg")
    assert environment_badge_suffix() == ": STG"
    assert environment_badge_suffix("prod") == ""

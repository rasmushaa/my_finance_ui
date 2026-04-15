"""Environment variable helpers for the Streamlit frontend.

This module centralizes environment-variable access to keep validation and defaults
consistent across pages.
"""

from __future__ import annotations

import os

RUNTIME_REQUIRED_ENV_VARS: tuple[str, ...] = (
    "API_BASE_URL",
    "GOOGLE_CLIENT_ID",
    "REDIRECT_URI",
)
"""Runtime environment variables required by the Streamlit application."""


def require_env(name: str) -> str:
    """Read a required environment variable.

    Parameters
    ----------
    name : str
        Environment variable name.

    Returns
    -------
    str
        Environment variable value.

    Raises
    ------
    RuntimeError
        Raised when the variable is missing or empty.
    """
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable '{name}'. "
            "Set it in your .env file for local development or in Cloud Run."
        )
    return value


def app_environment() -> str:
    """Return the runtime environment label.

    Returns
    -------
    str
        Lowercased runtime environment. Defaults to ``\"dev\"``.
    """
    return os.getenv("ENV", "dev").strip().lower()


def environment_badge_suffix(environment: str | None = None) -> str:
    """Format a short environment suffix for UI headers.

    Parameters
    ----------
    environment : str | None, optional
        Runtime environment label. When omitted, it is read from ``ENV``.

    Returns
    -------
    str
        Empty string for production, otherwise a ``\": <ENV>\"`` suffix.
    """
    env = (environment or app_environment()).lower()
    if env == "prod":
        return ""
    return f": {env.upper()}"

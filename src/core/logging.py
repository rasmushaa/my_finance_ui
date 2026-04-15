"""UI-facing logging utilities backed by Streamlit session state."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


INFO = "INFO"
SUCCESS = "SUCCESS"
ERROR = "ERROR"


def _append_log(msg: str, log_type: str = INFO) -> None:
    """Append a log message to the in-memory Streamlit log buffer.

    Parameters
    ----------
    msg : str
        Message to append.
    log_type : str, optional
        Log category. Typical values are ``INFO``, ``SUCCESS``, and ``ERROR``.
    """
    if "__logs" not in st.session_state:
        st.session_state["__logs"] = []
    st.session_state["__logs"].append(
        {"message": msg, "type": log_type, "timestamp": time.time()}
    )


def append_info(msg: str) -> None:
    """Append an informational message to UI logs and Python logs.

    Parameters
    ----------
    msg : str
        Informational message.
    """
    _append_log(msg, INFO)
    logger.info(msg)


def append_success(msg: str) -> None:
    """Append a success message to UI logs and Python logs.

    Parameters
    ----------
    msg : str
        Success message.
    """
    _append_log(msg, SUCCESS)
    logger.info(msg)


def append_error(msg: str) -> None:
    """Append an error message to UI logs and Python logs.

    Parameters
    ----------
    msg : str
        Error message.
    """
    _append_log(msg, ERROR)
    logger.error(msg)


def append_api_error(response: Any) -> None:
    """Append a backend API error in a user-friendly format.

    Parameters
    ----------
    response : Any
        Object compatible with ``requests.Response`` methods and attributes.
    """
    try:
        response_json = response.json()
        message = response_json.get("message", "")
        details = response_json.get("details", {})
        hint = details.get("hint", "")
        text = f"""**Error:** {message}\n\n{hint}"""

    except Exception:  # noqa: BLE001 - must tolerate arbitrary response types.
        text = (
            f"An unknown error occurred. Status code: {response.status_code} "
            f"Response: {response.text}"
        )

    append_error(text)
    logger.error(f"API Error: {text}")


def get_logs() -> list[dict[str, Any]]:
    """Return all collected UI log entries.

    Returns
    -------
    list[dict[str, Any]]
        Log entries with ``message``, ``type``, and ``timestamp`` fields.
    """
    return st.session_state.get("__logs", [])


def clear_logs() -> None:
    """Clear all collected UI log entries.

    Notes
    -----
    This is useful when entering a page with a fresh workflow.
    """
    st.session_state["__logs"] = []


def prune_logs(older_than_seconds: int) -> None:
    """Delete log entries older than the provided age threshold.

    Parameters
    ----------
    older_than_seconds : int
        Maximum age in seconds for retained logs.
    """
    cutoff_time = time.time() - older_than_seconds
    st.session_state["__logs"] = [
        log for log in get_logs() if log["timestamp"] >= cutoff_time
    ]


def render_logs(latest_first: bool = False, limit: int | None = None) -> None:
    """Render logs into the current Streamlit container.

    Parameters
    ----------
    latest_first : bool, optional
        Whether to display the newest entries first.
    limit : int | None, optional
        Maximum number of entries to render. ``None`` renders all.
    """
    logs: Sequence[dict[str, Any]] = get_logs()

    if latest_first:
        logs = list(reversed(logs))

    if limit is not None:
        logs = list(logs)[: max(limit, 0)]

    for log in logs:
        if log["type"] == INFO:
            st.info(log["message"])

        elif log["type"] == SUCCESS:
            st.success(log["message"])

        elif log["type"] == ERROR:
            st.error(log["message"])

        else:
            st.write(log["message"])

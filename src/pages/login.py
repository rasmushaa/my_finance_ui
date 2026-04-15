"""Google OAuth login page for the My Finance frontend."""

from __future__ import annotations

import logging
import time
import urllib.parse as up
from typing import Any

import requests
import streamlit as st

from src.core.env import environment_badge_suffix, require_env
from src.core.user import User

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 15


def _first_query_value(value: Any) -> str | None:
    """Extract the first value from a query parameter entry.

    Parameters
    ----------
    value : Any
        Query parameter value from ``st.query_params.get``.

    Returns
    -------
    str | None
        First string value if present, otherwise ``None``.
    """
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        return str(value[0])
    return str(value)


def build_google_auth_url() -> str:
    """Build the Google OAuth authorization URL.

    Returns
    -------
    str
        URL for the Google consent screen.
    """
    params = {
        "client_id": require_env("GOOGLE_CLIENT_ID"),
        "redirect_uri": require_env("REDIRECT_URI"),
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/auth?{up.urlencode(params)}"


def request_session_from_api(code: str) -> requests.Response:
    """Exchange an OAuth authorization code for a backend user session.

    Parameters
    ----------
    code : str
        Authorization code returned by Google OAuth.

    Returns
    -------
    requests.Response
        Backend API response containing the authenticated user payload.
    """
    payload = {
        "code": code,
        "redirect_uri": require_env("REDIRECT_URI"),
    }
    return requests.post(
        f"{require_env('API_BASE_URL')}/app/v1/auth/google/code",
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def render_page_header() -> st.delta_generator.DeltaGenerator:
    """Render the page title area and return the primary content column.

    Returns
    -------
    st.delta_generator.DeltaGenerator
        Column used for primary page content.
    """
    col1, col2 = st.columns([3, 1])
    col2.image("src/assets/logo.png")
    suffix = environment_badge_suffix()
    col1.title(f"My Finance App{suffix}")
    return col1


def handle_google_redirect() -> None:
    """Handle OAuth redirect query parameters and authenticate the user."""
    if not st.query_params:
        return

    code = _first_query_value(st.query_params.get("code"))
    error = _first_query_value(st.query_params.get("error"))

    if error:
        st.error(f"Authentication failed: {error}")
        st.stop()

    if not code:
        return

    try:
        response = request_session_from_api(code)
    except requests.RequestException as exc:
        logger.exception("Failed to reach authentication endpoint.", exc_info=exc)
        st.error("Could not reach the authentication service. Please try again.")
        st.stop()

    if response.status_code != 200:
        logger.exception("Unexpected authentication payload: %s", response.text)
        st.error("Authentication payload was invalid. Please contact support.")
        st.stop()

    try:
        st.session_state["user"] = User(**response.json())
    except TypeError:
        logger.exception("Unexpected authentication payload: %s", response.text)
        st.error("Authentication payload was invalid. Please contact support.")
        st.stop()

    st.success(f"Successfully authenticated as {st.session_state['user'].user_name}.")
    time.sleep(0.5)
    st.switch_page("pages/transaction_input.py")


def main() -> None:
    """Render and run the login page."""
    st.set_page_config(layout="centered")
    primary_column = render_page_header()
    primary_column.link_button(
        "Login with Google",
        url=build_google_auth_url(),
        icon=":material/account_circle:",
    )
    handle_google_redirect()


main()

"""Authentication helpers for Streamlit page scripts."""

from __future__ import annotations

import streamlit as st

from src.core.user import User


def current_user() -> User | None:
    """Return the authenticated user from session state.

    The function also normalizes legacy session objects created before code
    reloads, reducing accidental logouts during development.

    Returns
    -------
    User | None
        Authenticated user if present and logged in, otherwise ``None``.
    """
    user = st.session_state.get("user")

    if isinstance(user, dict):
        try:
            user = User(**user)
            st.session_state["user"] = user
        except TypeError:
            return None

    if isinstance(user, User):
        return user if user.is_logged_in() else None

    # Support user objects from older code versions during hot reload.
    token = getattr(user, "token", None)
    if not isinstance(token, str) or not token:
        return None

    try:
        normalized_user = User(
            user_name=str(getattr(user, "user_name")),
            user_picture_url=str(getattr(user, "user_picture_url")),
            user_role=str(getattr(user, "user_role")),
            encoded_jwt_token=token,
        )
    except Exception:  # noqa: BLE001 - tolerate unknown session object shape.
        return None

    st.session_state["user"] = normalized_user
    return normalized_user


def require_authenticated_user() -> User:
    """Return the authenticated user or redirect to login.

    Returns
    -------
    User
        Logged-in user.
    """
    user = current_user()
    if user is None:
        st.warning("Please sign in to continue.")
        st.switch_page("pages/login.py")
        st.stop()
    return user

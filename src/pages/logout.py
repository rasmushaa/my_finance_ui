"""Logout page that clears session state and redirects to login."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Clear the active session and redirect the user to the login page."""
    st.session_state.clear()
    st.switch_page("pages/login.py")


main()

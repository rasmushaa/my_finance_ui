"""Application entry point for the My Finance Streamlit frontend."""

from __future__ import annotations

import logging

import streamlit as st

from src.core import focus
from src.core.setup_logging import setup_logging
from src.core.sidebar import render_sidebar_to_user_access_level

APP_TITLE = "My Finance"
APP_ICON_PATH = "src/assets/logo.png"


def build_pages() -> list[st.Page]:
    """Build the complete list of navigable Streamlit pages.

    Returns
    -------
    list[st.Page]
        Page definitions used by ``st.navigation``.
    """
    return [
        st.Page("pages/login.py", default=True),
        st.Page("pages/logout.py"),
        st.Page("pages/transaction_input.py"),
        st.Page("pages/transaction_labeling.py"),
        st.Page("pages/assets.py"),
        st.Page("pages/filetypes.py"),
        st.Page("pages/ai.py"),
    ]


def main() -> None:
    """Configure and run the Streamlit multi-page application."""
    setup_logging(level=logging.INFO)
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON_PATH)

    page_group = st.navigation(build_pages(), position="hidden")
    focus.update(page_group)
    render_sidebar_to_user_access_level()
    page_group.run()


main()

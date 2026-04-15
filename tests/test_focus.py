"""Basic tests for page focus helpers."""

from __future__ import annotations

from types import SimpleNamespace

import streamlit as st

from src.core import focus


def test_focus_update_tracks_page_changes() -> None:
    """`update` marks changes when URL path changes."""
    st.session_state.clear()

    focus.update(SimpleNamespace(url_path="page-a"))
    assert focus.page() == "page-a"
    assert focus.changed() is True

    focus.update(SimpleNamespace(url_path="page-a"))
    assert focus.changed() is False

    focus.update(SimpleNamespace(url_path="page-b"))
    assert focus.page() == "page-b"
    assert focus.changed() is True


def test_reset_on_page_change_forces_change_next_time() -> None:
    """Resetting current page forces next update to be considered changed."""
    st.session_state.clear()
    focus.update(SimpleNamespace(url_path="page-a"))
    focus.reset_on_page_change()
    focus.update(SimpleNamespace(url_path="page-a"))

    assert focus.changed() is True

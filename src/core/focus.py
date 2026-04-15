"""Page-focus utilities to detect navigation changes between reruns."""

from __future__ import annotations

from typing import Any

import streamlit as st

_CURRENT_PAGE_KEY = "__current_page"
_PAGE_CHANGED_KEY = "__page_changed"


def update(st_page_group: Any) -> None:
    """Update current page tracking metadata.

    Parameters
    ----------
    st_page_group : Any
        Object returned by ``st.navigation`` with a ``url_path`` attribute.
    """
    old_page = st.session_state.get(_CURRENT_PAGE_KEY)
    st.session_state[_CURRENT_PAGE_KEY] = st_page_group.url_path
    st.session_state[_PAGE_CHANGED_KEY] = (
        old_page != st.session_state[_CURRENT_PAGE_KEY]
    )


def changed() -> bool:
    """Return whether the page changed during the latest navigation update.

    Returns
    -------
    bool
        ``True`` when the current page differs from the previous rerun.
    """
    return st.session_state.get(_PAGE_CHANGED_KEY, False)


def page() -> str:
    """Return the current Streamlit URL path.

    Returns
    -------
    str
        Current page URL path.
    """
    return st.session_state.get(_CURRENT_PAGE_KEY, "")


def reset_on_page_change() -> None:
    """Force focus tracking to report a page change on the next rerun."""
    st.session_state[_CURRENT_PAGE_KEY] = None

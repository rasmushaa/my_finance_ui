""" Focus management for Streamlit pages. 

This module provides utilities to track the current page and detect when the page has changed, 
allowing pages to react to page changes, like fetching new data from the API when the user navigates to a page,
initializing page-specific session state, or resetting some state when leaving a page.

Usage:
- Call `focus.update(st_page_group)` in the main app.py, to update the current page and whether the page has changed.
- In any page, call `focus.changed()` to check if the page has changed since the last update
- Call `focus.page()` to get the current page name.

"""
import streamlit as st


def update(st_page_group: st.Page) -> None:
    """ Called every time on app.py, to update the current page and whether the page has changed.
    
    Parameters
    ----------
    st_page_group : st.Page
        The st.Page group that is currently active, from which the current page can be read.
    """
    old_page = st.session_state.get("__current_page", None)
    st.session_state["__current_page"] = st_page_group.url_path
    st.session_state["__page_changed"] = (old_page != st.session_state["__current_page"])


def changed() -> bool:
    """ Returns whether the page has changed since the last update_focus call. """
    return st.session_state.get("__page_changed", False)


def page() -> str:
    """ Returns the current page. """
    return st.session_state.get("__current_page", "")


def reset_on_page_change() -> None:
    """ Force a full page reload on page change, to reset all state. Should be called at the end of the page script. """
    st.session_state["__current_page"] = None 
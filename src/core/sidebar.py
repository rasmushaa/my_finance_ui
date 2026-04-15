"""Sidebar navigation rendering based on user access level."""

from __future__ import annotations

import streamlit as st

from src.core.auth import current_user
from src.core.user import User


def _render_authenticated_menu(user: User) -> None:
    """Render navigation and account details for an authenticated user.

    Parameters
    ----------
    user : User
        Authenticated user from session state.
    """
    st.sidebar.image(user.user_picture_url)
    st.sidebar.subheader(user.user_name)
    st.sidebar.divider()

    st.sidebar.subheader("Account")
    st.sidebar.page_link(
        st.Page("pages/logout.py"),
        label="Logout",
        icon=":material/logout:",
    )

    st.sidebar.subheader("Upload Files")
    st.sidebar.page_link(
        st.Page("pages/transaction_input.py"),
        label="Transactions",
        icon=":material/payments:",
    )
    st.sidebar.page_link(
        st.Page("pages/assets.py"),
        label="Assets",
        icon=":material/account_balance:",
    )

    disabled = not user.is_admin()
    st.sidebar.subheader("Manage Application")
    st.sidebar.page_link(
        st.Page("pages/filetypes.py"),
        label="File Types",
        icon=":material/inbox_text_asterisk:",
        disabled=disabled,
    )
    st.sidebar.page_link(
        st.Page("pages/ai.py"),
        label="AI",
        icon=":material/robot_2:",
        disabled=disabled,
    )


def _render_unauthenticated_menu() -> None:
    """Render the minimal sidebar for unauthenticated users."""
    st.sidebar.title("Welcome to My Finance App")
    st.sidebar.write(
        "Please log in to access your financial dashboard and manage your finances."
    )
    st.sidebar.page_link("pages/login.py", label="Login", icon=":material/login:")


def render_sidebar_to_user_access_level() -> None:
    """Render the sidebar according to authentication state."""
    user = current_user()
    if user is not None:
        _render_authenticated_menu(user)
    else:
        _render_unauthenticated_menu()

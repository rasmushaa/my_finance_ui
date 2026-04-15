"""Layout utilities shared across Streamlit pages."""

from __future__ import annotations

import st_yled as sty
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from src.core.logging import prune_logs, render_logs

sty.init()

_MAIN_COL_KEY = "__main_col"
_INFO_COL_KEY = "__info_col"


def init_base_layout(
    info_col_ratio: float = 0.25,
    delete_old_logs_after_seconds: int = 10,
    logs_limit: int = 5,
) -> tuple[DeltaGenerator, DeltaGenerator]:
    """Create a two-column page layout with a live log sidebar.

    Parameters
    ----------
    info_col_ratio : float, optional
        Relative width of the info column. Must be between 0 and 1.
    delete_old_logs_after_seconds : int, optional
        Log pruning threshold in seconds.
    logs_limit : int, optional
        Maximum number of log messages shown in the sidebar.

    Returns
    -------
    tuple[DeltaGenerator, DeltaGenerator]
        Main content column and info column.

    Raises
    ------
    ValueError
        Raised when ``info_col_ratio`` is outside ``(0, 1)``.
    """
    if not 0 < info_col_ratio < 1:
        raise ValueError("info_col_ratio must be between 0 and 1.")

    st.set_page_config(layout="wide")

    int_scaler = 100
    main_col_generator, info_col_generator = st.columns(
        [
            int((1 - info_col_ratio) * int_scaler),
            int(info_col_ratio * int_scaler),
        ],
        gap="large",
    )

    with info_col_generator:
        with st.expander("Logs", expanded=True):
            render_logs(latest_first=True, limit=logs_limit)
            prune_logs(older_than_seconds=delete_old_logs_after_seconds)

    st.session_state[_MAIN_COL_KEY] = main_col_generator
    st.session_state[_INFO_COL_KEY] = info_col_generator
    return main_col_generator, info_col_generator


def main_col() -> DeltaGenerator:
    """Return the initialized main column container.

    Returns
    -------
    DeltaGenerator
        Main layout column used for page content.

    Raises
    ------
    RuntimeError
        Raised when the base layout has not been initialized.
    """
    if _MAIN_COL_KEY not in st.session_state:
        raise RuntimeError(
            "Base layout not initialized. Call init_base_layout() first."
        )
    return st.session_state[_MAIN_COL_KEY]


def info_col() -> DeltaGenerator:
    """Return the initialized info column container.

    Returns
    -------
    DeltaGenerator
        Secondary layout column for contextual information and logs.

    Raises
    ------
    RuntimeError
        Raised when the base layout has not been initialized.
    """
    if _INFO_COL_KEY not in st.session_state:
        raise RuntimeError(
            "Base layout not initialized. Call init_base_layout() first."
        )
    return st.session_state[_INFO_COL_KEY]

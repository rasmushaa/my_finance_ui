from typing import Tuple
import streamlit as st
import st_yled as sty
from .logging import render_logs, prune_logs

sty.init()


def init_base_layout(info_col_ratio: float = 0.25, delete_old_logs_after_seconds: int = 10, logs_limit: int = 5) -> Tuple[st.delta_generator.DeltaGenerator, st.delta_generator.DeltaGenerator]:
    """ Initializes the base layout of the page, 
    with a main column and an info column. 

    The main column should be used for the main content of the page.
    The info column is automatically rendered with the messages 
    from the logging module and persists over reruns.
    
    Parameters
    ----------
    info_col_ratio : float, optional
        The ratio of the info column width to the total width, by default 0.3
    delete_old_logs_after_seconds : int, optional
        The age in seconds after which logs should be pruned, by default 10
    logs_limit : int, optional
        The maximum number of logs to render, by default 5

    Returns
    -------
    Tuple[st.delta_generator.DeltaGenerator, st.delta_generator.DeltaGenerator]
        The main column and the info column as Streamlit delta generators.
    """

    st.set_page_config(layout="wide")

    int_scaler = 100

    main_col, info_col = st.columns([int((1 - info_col_ratio) * int_scaler), int(info_col_ratio * int_scaler)], gap="large")

    with info_col:
        with st.expander("Logs", expanded=True):
            render_logs(latest_first=True, limit=logs_limit)
            prune_logs(older_than_seconds=delete_old_logs_after_seconds)

    st.session_state["__main_col"] = main_col
    st.session_state["__info_col"] = info_col
    return main_col, info_col


def main_col():
    """ Returns the main column, that should be used for the main content of the page. """
    assert "__main_col" in st.session_state, "Base layout not initialized. Call init_base_layout() first."
    return st.session_state["__main_col"]

def info_col():
    """ Returns the info column, that should be used for secondary content of the page, like info boxes, help texts, etc. """
    assert "__info_col" in st.session_state, "Base layout not initialized. Call init_base_layout() first."
    return st.session_state["__info_col"]
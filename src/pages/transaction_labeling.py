"""Label transformed transactions before persisting them to the backend."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests
import st_yled as sty
import streamlit as st

from src.core import focus, layout, logging
from src.core.auth import require_authenticated_user
from src.core.env import require_env
from src.core.logging import append_api_error

sty.init()
layout.init_base_layout(info_col_ratio=0.2)

REQUEST_TIMEOUT_SECONDS = 30
STATE_EDITING = 0
STATE_SAVING = 1
STATE_REDIRECTING = 2


@st.cache_data
def get_labels() -> list[dict[str, str]]:
    """Fetch transaction labels from the backend API.

    Returns
    -------
    list[dict[str, str]]
        Label records containing keys such as ``key`` and ``description``.
    """
    user = require_authenticated_user()
    response = requests.get(
        f"{require_env('API_BASE_URL')}/app/v1/transactions/labels",
        headers={"Authorization": f"Bearer {user.token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        return response.json().get("labels", [])

    append_api_error(response)
    return []


def category_formatter(category: str) -> str:
    """Decorate category labels with optional emoji prefixes.

    Parameters
    ----------
    category : str
        Raw category key from the backend.

    Returns
    -------
    str
        Human-friendly category display label.
    """
    mapping = {
        "HOUSEHOLD-ITEMS": "🛋️ - " + category,
        "TECHNOLOGY": "💻 - " + category,
        "HEALTH": "💊 - " + category,
        "COMMUTING": "🚃 - " + category,
        "CLOTHING": "👕 - " + category,
        "SALARY": "💶 - " + category,
        "HOBBIES": "💪🏻 - " + category,
        "UNCATEGORIZED": "❔ - " + category,
        "FOOD": "🛒 - " + category,
        "LIVING": "🏠 - " + category,
        "OTHER-INCOME": "🤝 - " + category,
        "ENTERTAINMENT": "🎉 - " + category,
        "INVESTING": "📈 - " + category,
    }
    return mapping.get(category, category)


@st.dialog("Labeling Help")
def help_dialog() -> None:
    """Render a modal with label descriptions from backend metadata."""
    labels = get_labels()
    if not labels:
        st.write("No label metadata available.")
        return

    message = "Here you can label your transactions. Available categories:\n\n"
    for label in labels:
        message += f"- **{label['key']}**: {label['description']}\n"
    st.markdown(message)


def get_latest_entry() -> str | None:
    """Fetch the latest stored transaction date from the backend.

    Returns
    -------
    str | None
        Latest entry date in ISO format or ``None`` when unavailable.
    """
    user = require_authenticated_user()
    response = requests.get(
        f"{require_env('API_BASE_URL')}/app/v1/transactions/latest-entry",
        headers={"Authorization": f"Bearer {user.token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        return response.json().get("latest_entry_date")

    logging.append_api_error(response)
    return None


def initialize_page_state() -> None:
    """Initialize session state that should refresh on page navigation."""
    if not focus.changed():
        return

    logging.clear_logs()

    if "processed_file_df" not in st.session_state:
        st.error("No processed file found. Please upload a file first.")
        time.sleep(2)
        st.switch_page("pages/transaction_input.py")
        st.stop()

    dataframe = st.session_state["processed_file_df"]
    dataframe["Date"] = pd.to_datetime(dataframe["Date"])
    month_names = dataframe["Date"].dt.month_name().unique()
    if len(month_names) == 1:
        logging.append_info(f"Transactions contain data only for {month_names[0]}.")
    else:
        logging.append_error(
            "Transactions contain data for multiple months: "
            f"{', '.join(month_names)}. Please review dates carefully."
        )

    latest_entry_date = get_latest_entry()
    if latest_entry_date is not None:
        if dataframe["Date"].min() <= pd.to_datetime(latest_entry_date):
            logging.append_error(
                "The oldest transaction in this file is "
                f"{dataframe['Date'].min().date()}, but existing data already extends "
                f"to {latest_entry_date}. Please review to avoid duplicates."
            )

    st.session_state["state"] = STATE_EDITING


def build_layout() -> tuple[Any, Any]:
    """Build the page's primary card and button row.

    Returns
    -------
    tuple[Any, Any]
        Base content container and button container.
    """
    _, base_col, _ = layout.main_col().columns([2, 7, 1], gap="large")
    with base_col:
        base_container = sty.container(
            border=True,
            background_color="rgb(250, 250, 246)",
            padding=30,
        )
        button_container = base_container.container(horizontal=True)
    return base_container, button_container


def render_data_editor(base_container: Any) -> pd.DataFrame:
    """Render editable transaction table.

    Parameters
    ----------
    base_container : Any
        Streamlit or st-yled container for page content.

    Returns
    -------
    pd.DataFrame
        User-edited dataframe.
    """
    labels = get_labels()
    label_keys = [label["key"] for label in labels]
    if not label_keys:
        st.error("No transaction labels are available. Please configure labels first.")
        st.stop()
    return base_container.data_editor(
        st.session_state["processed_file_df"],
        column_config={
            "Date": st.column_config.Column("Date", disabled=True),
            "Receiver": st.column_config.Column("Receiver", disabled=True),
            "Amount": st.column_config.Column("Amount", disabled=True),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=label_keys,
                format_func=category_formatter,
            ),
            "RowProcessingID": None,
        },
        hide_index=True,
        height=35 * 20 + 38,
    )


def save_labeled_transactions(edited_df: pd.DataFrame) -> bool:
    """Upload labeled transactions to backend storage.

    Parameters
    ----------
    edited_df : pd.DataFrame
        Labeled transactions from the table editor.

    Returns
    -------
    bool
        ``True`` on successful upload, otherwise ``False``.
    """
    user = require_authenticated_user()
    response = requests.post(
        f"{require_env('API_BASE_URL')}/app/v1/transactions/upload",
        files={
            "file": (
                "transformed_data.csv",
                edited_df.to_csv(index=False),
                "text/csv",
            )
        },
        headers={"Authorization": f"Bearer {user.token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        logging.append_success("Changes saved successfully.")
        return True

    logging.append_api_error(response)
    return False


def run_state_machine(button_container: Any, edited_df: pd.DataFrame) -> None:
    """Run the page-level save state machine.

    Parameters
    ----------
    button_container : Any
        Streamlit container hosting action buttons.
    edited_df : pd.DataFrame
        Edited dataframe to save when requested.
    """
    button_container.header("Label your transactions")
    button_container.button("Help", on_click=help_dialog)

    st.session_state.setdefault("state", STATE_EDITING)
    match st.session_state["state"]:
        case 0:
            if button_container.button("Save changes", width="content", type="primary"):
                st.session_state["state"] = STATE_SAVING
                st.rerun()

        case 1:
            button_container.button(
                "Saving...",
                width="content",
                type="primary",
                disabled=True,
            )
            save_labeled_transactions(edited_df)
            st.session_state["state"] = STATE_REDIRECTING
            st.rerun()

        case 2:
            logging.clear_logs()
            time.sleep(2)
            st.switch_page("pages/transaction_input.py")

        case _:
            st.error("Unknown state. Please refresh the page.")


def main() -> None:
    """Render and run the transaction labeling page."""
    require_authenticated_user()
    initialize_page_state()
    base_container, button_container = build_layout()
    edited_df = render_data_editor(base_container)
    run_state_machine(button_container, edited_df)


main()

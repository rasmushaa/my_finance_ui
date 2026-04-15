"""Asset and liability entry page for quarterly balance tracking."""

from __future__ import annotations

import datetime
import time
from typing import Any

import requests
import st_yled as sty
import streamlit as st

from src.core import focus, logging
from src.core.auth import require_authenticated_user
from src.core.env import require_env
from src.core.layout import init_base_layout

sty.init()

REQUEST_TIMEOUT_SECONDS = 30
STATE_EDITING = 0
STATE_SAVING = 1
STATE_REDIRECTING = 2


def push_data(values: dict[str, int | str]) -> bool:
    """Send balance data to the backend API.

    Parameters
    ----------
    values : dict[str, int | str]
        Payload to persist.

    Returns
    -------
    bool
        ``True`` when save succeeded, otherwise ``False``.
    """
    user = require_authenticated_user()
    response = requests.post(
        f"{require_env('API_BASE_URL')}/app/v1/assets/upload",
        headers={"Authorization": f"Bearer {user.token}"},
        json=values,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 200:
        logging.append_success("Data saved successfully.")
        return True

    logging.append_api_error(response)
    return False


def get_latest_entry() -> dict[str, int | str]:
    """Fetch latest saved balance entry for form prefilling.

    Returns
    -------
    dict[str, int | str]
        Latest entry payload, empty dictionary on failure.
    """
    user = require_authenticated_user()
    response = requests.get(
        f"{require_env('API_BASE_URL')}/app/v1/assets/latest-entry",
        headers={"Authorization": f"Bearer {user.token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 200:
        return {
            key: int(value) if isinstance(value, (int, float)) else value
            for key, value in response.json().items()
        }

    logging.append_api_error(response)
    return {}


def _quarter(value: datetime.date) -> int:
    """Return quarter number for a date.

    Parameters
    ----------
    value : datetime.date
        Date value.

    Returns
    -------
    int
        Quarter in range ``1..4``.
    """
    return (value.month - 1) // 3 + 1


def _last_day_of_quarter(year: int, quarter: int) -> datetime.date:
    """Return last calendar date of the provided quarter.

    Parameters
    ----------
    year : int
        Calendar year.
    quarter : int
        Quarter number in range ``1..4``.

    Returns
    -------
    datetime.date
        Last date of the selected quarter.
    """
    end_month = quarter * 3
    if end_month == 12:
        return datetime.date(year, 12, 31)
    return datetime.date(year, end_month + 1, 1) - datetime.timedelta(days=1)


def _next_quarter(year: int, quarter: int) -> tuple[int, int]:
    """Return the next quarter pair as ``(year, quarter)``.

    Parameters
    ----------
    year : int
        Current year.
    quarter : int
        Current quarter.

    Returns
    -------
    tuple[int, int]
        Next quarter represented as year and quarter.
    """
    return (year + 1, 1) if quarter == 4 else (year, quarter + 1)


def determine_default_date(latest_entry_date: datetime.date) -> datetime.date:
    """Determine default book date for new entries.

    Parameters
    ----------
    latest_entry_date : datetime.date
        Date of the latest persisted entry.

    Returns
    -------
    datetime.date
        Suggested date for the new entry form.
    """
    today = datetime.date.today()
    latest = latest_entry_date
    next_year, next_quarter = _next_quarter(latest.year, _quarter(latest))
    if (next_year, next_quarter) < (today.year, _quarter(today)):
        default_date = _last_day_of_quarter(next_year, next_quarter)
        logging.append_info(
            f"Latest entry is from {latest} ({latest.year}Q{_quarter(latest)}). "
            f"Default date set to {default_date} ({default_date.year}Q{_quarter(default_date)})."
        )
        return default_date
    return today


def initialize_page_state() -> None:
    """Initialize page-specific session state when navigation changes."""
    if not focus.changed():
        return

    logging.clear_logs()
    st.session_state["latest_entry"] = get_latest_entry()
    fallback_date = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    st.session_state["latest_date"] = datetime.date.fromisoformat(
        st.session_state["latest_entry"].get("date", fallback_date)
    )
    st.session_state["default_date"] = determine_default_date(
        st.session_state["latest_date"]
    )
    st.session_state["state"] = STATE_EDITING


def build_base_container() -> Any:
    """Build and return the page's primary styled container.

    Returns
    -------
    Any
        Styled container for the assets page body.
    """
    main_col, _ = init_base_layout(info_col_ratio=0.2)
    _, base_col, _ = main_col.columns([2, 7, 1], gap="large")
    with base_col:
        return sty.container(
            border=True, background_color="rgb(250, 250, 246)", padding=30
        )


def run_page() -> None:
    """Render and run the assets entry page."""
    require_authenticated_user()
    initialize_page_state()
    balance_container = build_base_container()

    header_container = balance_container.container(
        horizontal=True, vertical_alignment="center"
    )
    header_container.title("Your financial balance")

    balance_container.divider()
    balance_container.subheader("Book date of the data")
    date_container = balance_container.container(
        horizontal=True, vertical_alignment="bottom"
    )

    input_date = date_container.date_input(
        label="Select date",
        help=(
            "The selected date is used as the book date for all entered data. "
            "Choose a new period to avoid duplicate entries."
        ),
        value=st.session_state["default_date"],
    )

    latest_date = st.session_state["latest_date"]
    if (latest_date.year, _quarter(latest_date)) >= (
        input_date.year,
        _quarter(input_date),
    ):
        logging.append_error(
            f"Latest recorded quarter is {latest_date.year}Q{_quarter(latest_date)} "
            f"({latest_date}). Please choose a later quarter than "
            f"{input_date.year}Q{_quarter(input_date)} ({input_date})."
        )

    balance_container.divider()
    col1, col2, col3 = balance_container.columns([3, 3, 2], gap="large")
    with col1:
        st.subheader("Assets")
        input_asset_cash = st.number_input(
            label="Cash",
            help="Sum of all liquid assets across accounts and platforms.",
            value=st.session_state["latest_entry"].get("cash", 0),
            step=100,
            min_value=0,
            format="%d",
        )
        input_asset_apartment = st.number_input(
            label="Apartment",
            help="Estimated market value of apartment or other real estate.",
            value=st.session_state["latest_entry"].get("apartment", 0),
            step=1000,
            min_value=0,
            format="%d",
        )
        input_asset_other = st.number_input(
            label="Other",
            help="Other tangible assets such as vehicles, boats, or collectibles.",
            value=st.session_state["latest_entry"].get("other_assets", 0),
            step=1000,
            min_value=0,
            format="%d",
        )
        input_asset_capital_market = st.number_input(
            label="Capital Assets",
            help="Current market value of stocks, bonds, crypto, and similar assets.",
            value=st.session_state["latest_entry"].get("capital_assets_value", 0),
            step=100,
            min_value=0,
            format="%d",
        )
        total_assets = (
            input_asset_cash
            + input_asset_apartment
            + input_asset_other
            + input_asset_capital_market
        )
        st.space(size="stretch")
        st.metric(label="Total assets", value=f"{total_assets:,.0f} €")

    with col2:
        st.subheader("Liabilities")
        input_liability_mortgage = st.number_input(
            label="Mortgage",
            help="Outstanding mortgage or housing loan balances.",
            value=st.session_state["latest_entry"].get("mortgage", 0),
            step=100,
            max_value=0,
            format="%d",
        )
        input_liability_student_loan = st.number_input(
            label="Student Loan",
            help="Outstanding student loan balances.",
            value=st.session_state["latest_entry"].get("student_loan", 0),
            step=100,
            max_value=0,
            format="%d",
        )
        input_liability_other = st.number_input(
            label="Other",
            help="Other liabilities such as credit cards, car loans, and personal loans.",
            value=st.session_state["latest_entry"].get("other_liabilities", 0),
            step=100,
            max_value=0,
            format="%d",
        )
        total_liabilities = (
            input_liability_mortgage
            + input_liability_student_loan
            + input_liability_other
        )
        st.space(size="stretch")
        st.metric(label="Total liabilities", value=f"{total_liabilities:,.0f} €")

    with col3:
        st.subheader("Net worth")
        st.number_input(
            label="Total assets",
            help="Sum of all asset categories.",
            value=total_assets,
            format="%d",
            disabled=True,
        )
        st.number_input(
            label="Total liabilities",
            help="Sum of all liability categories.",
            value=total_liabilities,
            format="%d",
            disabled=True,
        )
        net_worth = total_assets + total_liabilities
        st.space(size="stretch")
        st.metric(label="Net worth", value=f"{net_worth:,.0f} €")

    balance_container.divider()
    balance_container.subheader("Capital gains")
    input_asset_capital_unrealized = balance_container.number_input(
        label="Unrealized Capital Gains",
        help=(
            "Current unrealized gains from capital assets. "
            "Used for context, not included in total assets."
        ),
        value=st.session_state["latest_entry"].get(
            "capital_assets_unrealized_gains", 0
        ),
        step=100,
        min_value=0,
        format="%d",
    )
    input_asset_capital_realized = balance_container.number_input(
        label="Realized capital gains",
        help="Realized gains from sold capital assets in the selected period.",
        value=0,
        step=100,
        format="%d",
        min_value=0,
    )
    input_asset_capital_losses_realized = balance_container.number_input(
        label="Realized capital losses",
        help="Realized losses from sold capital assets in the selected period.",
        value=0,
        step=100,
        format="%d",
        max_value=0,
    )

    input_values = {
        "date": input_date.strftime("%Y-%m-%d"),
        "cash": input_asset_cash,
        "apartment": input_asset_apartment,
        "other_assets": input_asset_other,
        "capital_assets_value": input_asset_capital_market,
        "capital_assets_unrealized_gains": input_asset_capital_unrealized,
        "mortgage": input_liability_mortgage,
        "student_loan": input_liability_student_loan,
        "other_liabilities": input_liability_other,
        "realized_capital_gains": input_asset_capital_realized,
        "realized_capital_losses": input_asset_capital_losses_realized,
    }

    st.session_state.setdefault("state", STATE_EDITING)
    match st.session_state["state"]:
        case 0:
            if header_container.button("Insert Data", width="content", type="primary"):
                st.session_state["state"] = STATE_SAVING
                st.rerun()

        case 1:
            header_container.button(
                "Saving...",
                width="content",
                type="primary",
                disabled=True,
            )
            push_data(input_values)
            st.session_state["state"] = STATE_REDIRECTING
            st.rerun()

        case 2:
            logging.clear_logs()
            time.sleep(2)
            st.switch_page("pages/transaction_input.py")

        case _:
            st.error("Unknown state. Please refresh the page.")


run_page()

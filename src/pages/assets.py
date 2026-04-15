from src.core.layout import init_base_layout
import streamlit as st
import st_yled as sty
import requests
import time
import datetime
import os
from src.core import focus, logging

sty.init()


# -- Helpers ---------------------------------------
def push_data(values: dict):
    """ Pushes the data to the backend API."""
    r = requests.post(
        os.environ['API_BASE_URL'] + "/app/v1/assets/upload", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"},
        json=values
        )
    
    if r.status_code == 200:
        logging.append_success("Data saved successfully.")
    else:
        logging.append_api_error(r)

def get_latest_entry() -> dict:
    """ Gets the latest entry from the backend API to prefill the form with the last known values."""
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/assets/latest-entry", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
    
    if r.status_code == 200:
        return {k: int(v) if isinstance(v, (int, float)) else v for k, v in r.json().items()}
    else:
        logging.append_api_error(r)
        return {}

def _quarter(d: datetime.date) -> int:
    return (d.month - 1) // 3 + 1

def _last_day_of_quarter(year: int, q: int) -> datetime.date:
    end_month = q * 3
    if end_month == 12:
        return datetime.date(year, 12, 31)
    return datetime.date(year, end_month + 1, 1) - datetime.timedelta(days=1)

def _next_quarter(year: int, q: int) -> tuple[int, int]:
    return (year + 1, 1) if q == 4 else (year, q + 1)


def determine_default_date(latest_entry_date: datetime.date) -> datetime.date:
    """ Determines the default date for the date input based on the latest entry date.
    
    If the latest entry is from a previous quarter, the default date is set to the end of the next quarter.
    If the latest entry is from the current quarter, the default date is set to today's date.

    Parameters
    ----------
    latest_entry_date : str
        The date of the latest entry in ISO format (YYYY-MM-DD).

    Returns
    -------
    datetime.date
        The default date for the date input.
    """
    _today = datetime.date.today()
    _latest = latest_entry_date
    _ny, _nq = _next_quarter(_latest.year, _quarter(_latest))
    if (_ny, _nq) < (_today.year, _quarter(_today)):
        _default_date = _last_day_of_quarter(_ny, _nq)
        logging.append_info(f"Your latest entry is from {_latest} ({_latest.year}Q{_quarter(_latest)}). The default date is set to the end of the next quarter, which is {_default_date} ({_default_date.year}Q{_quarter(_default_date)}).")
    else:
        _default_date = _today
    return _default_date


# -- Init page state ---------------------------------------
if focus.changed():
    logging.clear_logs()
    st.session_state["latest_entry"] = get_latest_entry()
    st.session_state["latest_date"] = datetime.date.fromisoformat(st.session_state["latest_entry"].get("date", (datetime.date.today() - datetime.timedelta(days=1)).isoformat()))
    st.session_state["default_date"] = determine_default_date(st.session_state["latest_date"])
    st.session_state["state"] = 0 # 0 = editing, 1 = saving, 2 = redirecting
 

# -- Base layout ---------------------------------------
main_col, _ = init_base_layout(info_col_ratio=0.2)
_, base_col, _ = main_col.columns([2, 7, 1], gap="large")
with base_col:
    balance_container = sty.container(border=True, background_color="rgb(250, 250, 246)", padding=30)


# -- Header and button ---------------------------------------
header_container = balance_container.container(horizontal=True, vertical_alignment="center")
header_container.title("Your financial balance")
# Button is at defined at the end on this place to use the input values


# -- Date range selector ---------------------------------------
balance_container.divider()
balance_container.subheader("Book date of the data")
date_container = balance_container.container(horizontal=True, vertical_alignment="bottom")

input_date = date_container.date_input(
    label="Select date",
    help="The date you select here will be used as the book date for all the transactions and assets you enter. This means that if you select a date in the past, all your data will be recorded as if it happened on that date. If you select today's date, it will be recorded as if it happened today.",
    value=st.session_state["default_date"],
)

if (st.session_state["latest_date"].year, _quarter(st.session_state["latest_date"])) >= (input_date.year, _quarter(input_date)):
    logging.append_error(f"Your latest entry is from {st.session_state['latest_date']} ({st.session_state['latest_date'].year}Q{_quarter(st.session_state['latest_date'])}), and you have selected {input_date} ({input_date.year}Q{_quarter(input_date)}). Please select a date that that have not been recorded yet, to avoid duplicate entries.")


# -- Asset inputs ---------------------------------------
balance_container.divider()
col1, col2, col3 = balance_container.columns([3, 3, 2], gap="large")
with col1:
    
    st.subheader("Assets")
    input_asset_cash = st.number_input(
        label="Cash", 
        help="Sum of all liquid assets on all accounts and financial platforms.",
        value=st.session_state["latest_entry"].get("cash", 0),
        step=100, 
        min_value=0,
        format="%d"
        )
    input_asset_apartment = st.number_input(
        label="Apartment", 
        help="Market value of your apartment or real estate properties.",
        value=st.session_state["latest_entry"].get("apartment", 0),
        step=1000, 
        min_value=0,
        format="%d"
        )
    input_asset_other = st.number_input(
        label="Other", 
        help="Any other tangible assets you have, like a car, boat, art collection.",
        value=st.session_state["latest_entry"].get("other_assets", 0),
        step=1000, 
        min_value=0,
        format="%d"
        )
    input_asset_capital_market = st.number_input(
        label="Capital Assets", 
        help="Curent market value of your stocks, bonds, crypto, and other capital assets.",
        value=st.session_state["latest_entry"].get("capital_assets_value", 0),
        step=100, 
        min_value=0,
        format="%d"
        )
    total_assets = input_asset_cash + input_asset_apartment + input_asset_other + input_asset_capital_market
    st.space(size="stretch")
    st.metric(label="Total assets", value=f"{total_assets:,.0f} €")


# -- Liability inputs ---------------------------------------
with col2:
    st.subheader("Liabilities")
    input_liability_mortgage = st.number_input(
        label="Mortgage", 
        help="Outstanding mortgage or loan balances.",
        value=st.session_state["latest_entry"].get("mortgage", 0),
        step=100, 
        max_value=0,
        format="%d"
        )
    input_liability_student_loan = st.number_input(
        label="Student Loan", 
        help="Outstanding student loan balances.",
        value=st.session_state["latest_entry"].get("student_loan", 0), 
        step=100, 
        max_value=0,
        format="%d"
        )
    input_liability_other = st.number_input(
        label="Other", 
        help="Outstanding balances for other liabilities. This can include credit card debt, car loans, personal loans, etc.",
        value=st.session_state["latest_entry"].get("other_liabilities", 0),
        step=100, 
        max_value=0,
        format="%d"
        )

    total_liabilities = input_liability_mortgage + input_liability_student_loan + input_liability_other
    st.space(size="stretch")
    st.metric(label="Total liabilities", value=f"{total_liabilities:,.0f} €")


# -- Net worth ---------------------------------------
with col3:
    st.subheader("Net worth")
    input_net_worth_assets = st.number_input(
        label="Total assets", 
        help="Total sum of all your assets from the right column.",
        value=total_assets, 
        format="%d",
        disabled=True
        )
    input_net_worth_liabilities = st.number_input(
        label="Total liabilities", 
        help="Total sum of all your liabilities from the right column.",
        value=total_liabilities, 
        format="%d",
        disabled=True
        )
    net_worth = total_assets + total_liabilities
    st.space(size="stretch")
    st.metric(label="Net worth", value=f"{net_worth:,.0f} €")


# -- Realized and unrealized capital gains ---------------------------------------
balance_container.divider()
balance_container.subheader("Capital gains")

input_asset_capital_unrealized = balance_container.number_input(
    label="Unrealized Capital Gains", 
    help="Curent market value of your unrealized gains from stocks, bonds, crypto, and other capital assets. Not included in total assets, but used for calculating net worth.",
    value=st.session_state["latest_entry"].get("capital_assets_unrealized_gains", 0), 
    step=100, 
    min_value=0,
    format="%d"
    )
input_asset_capital_realized = balance_container.number_input(
    label="Realized capital gains", 
    help="Total amount of realized capital gains from selling stocks, bonds, crypto, and other capital assets in the current period.",
    value=0,
    step=100,
    format="%d",
    min_value=0,
    )
input_asset_capital_losses_realized = balance_container.number_input(
    label="Realized capital losses", 
    help="Total amount of realized capital losses from selling stocks, bonds, crypto, and other capital assets in the current period.",
    value=0,
    step=100,
    format="%d",
    max_value=0,
    )


# -- Save button ---------------------------------------
input_values ={
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

match st.session_state["state"]:
    case 0:  # 0 = editing
        if header_container.button("Insert Data", width="content", type="primary"):
            st.session_state["state"] += 1
            st.rerun()
        
    case 1:  # 1 = saving
        header_container.button('Saving...', width="content", type='primary', disabled=True)
        push_data(input_values)
        st.session_state["state"] += 1
        st.rerun()

    case 2:  # 2 = redirecting  
        logging.clear_logs()
        time.sleep(2)
        st.switch_page("pages/transaction_input.py")

    case _:
        st.error("Unknown state. Please refresh the page.")
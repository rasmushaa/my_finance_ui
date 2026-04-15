""" Label processed dataframe from API.

This page shows the processed dataframe from the API 
and allows the user to label the transactions with categories. 
The categories are fetched from the API and shown in a selectbox. 
The user can also see a help box with the category descriptions.
"""
import streamlit as st
import requests
import os
import time
import st_yled as sty
from src.core import focus, layout, logging
import pandas as pd
from src.core.logging import append_api_error

sty.init()
layout.init_base_layout(info_col_ratio=0.2)


# -- Helpers ---------------------------------------
@st.cache_data
def get_labels() -> dict:
    """ The labels are never updated in the UI
    
    Returns
    -------
    dict
        A dictionary of label: comment pairs
    """
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/transactions/labels", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
    return r.json().get('labels', {}) if r.status_code == 200 else append_api_error(r)

def category_formatter(category: str) -> str:
    """ Adds emojis to the category names for better UX.

    If a new label is added in the backend, 
    it will be shown without an emoji.
    """
    mapping = {
        'HOUSEHOLD-ITEMS': '🛋️ - ' + category,
        'TECHNOLOGY': '💻 - ' + category,
        'HEALTH': '💊 - ' + category,
        'COMMUTING': '🚃 - ' + category,
        'CLOTHING': '👕 - ' + category,
        'SALARY': '💶 - ' + category,
        'HOBBIES': '💪🏻 - ' + category,
        'UNCATEGORIZED': '❔ - ' + category,
        'FOOD': '🛒 - ' + category,
        'LIVING': '🏠 - ' + category,
        'OTHER-INCOME': '🤝 - ' + category,
        'ENTERTAINMENT': '🎉 - ' + category,
        'INVESTING': '📈 - ' + category,
    }
    return mapping.get(category, category)

@st.dialog("Labeling Help")
def help():
    """ Shows the help box for label comments
    """
    message = "Here you can label your transactions. The categories are:\n\n"
    for label in get_labels():
        message += f"- **{label['key']}**: {label['description']}\n"
    st.markdown(message)

def get_latest_entry() -> str:
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/transactions/latest-entry", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
    if r.status_code == 200:
        return r.json().get('latest_entry_date', None)
    logging.append_api_error(r)
    return None


# -- Init page state ---------------------------------------
if focus.changed():
    if 'processed_file_df' not in st.session_state: # This should never happen, but check anyway
        st.error("No processed file found. Please upload a file first.")
        time.sleep(2)
        st.switch_page("pages/transaction_input.py")

    st.session_state["processed_file_df"]["Date"] = pd.to_datetime(st.session_state["processed_file_df"]["Date"])
    month_names_in_data = st.session_state["processed_file_df"]["Date"].dt.month_name().unique()

    if len(month_names_in_data) == 1:
        logging.append_info(f"Transactions contains data only for {month_names_in_data[0]}. Ok to label.")
    else:
        logging.append_error(f"Transactions contains data for multiple months: {', '.join(month_names_in_data)}. Ok to label, but check the dates carefully.")

    if get_latest_entry() is not None and st.session_state["processed_file_df"]["Date"].min() <= pd.to_datetime(get_latest_entry()):
        logging.append_error(f"The oldest entry in your transactions is from {st.session_state['processed_file_df']['Date'].min().date()}, but you have already recorded transactions up to {get_latest_entry()}. Please check the dates carefully to avoid duplicate entries.")

    st.session_state["state"] = 0 # 0 = editing, 1 = saving, 2 = redirecting


# -- The page layout ---------------------------------------
_, base_col, _ = layout.main_col().columns([2, 7, 1], gap="large")
with base_col:
    base_container = sty.container(border=True, background_color="rgb(250, 250, 246)", padding=30)
    button_container = base_container.container(horizontal=True)


# -- Data editor -------------------------------------
edited_df = base_container.data_editor(
    st.session_state['processed_file_df'],
    column_config={
        'Date': st.column_config.Column(
            'Date',
            disabled=True,
        ),
        'Receiver': st.column_config.Column(
            'Receiver',
            disabled=True,
        ),
        'Amount': st.column_config.Column(
            'Amount',
            disabled=True,
        ),
        "Category": st.column_config.SelectboxColumn(
            'Category',
            options=[label["key"] for label in get_labels()],
            format_func=category_formatter,
        ),
        "RowProcessingID": None,  # Hidden column for processing the data later
    },
    hide_index=True,
    height=35*20+38
)


# -- Buttons ---------------------------------------
button_container.header("Label your transactions")
button_container.button("Help", on_click=help)

match st.session_state["state"]:
    case 0:  # 0 = editing
        if button_container.button('Save changes', width="content", type='primary'):
            st.session_state["state"] += 1
            st.rerun()
        
    case 1:  # 1 = saving
        button_container.button('Saving...', width="content", type='primary', disabled=True)
        r = requests.post(
            os.environ['API_BASE_URL'] + "/app/v1/transactions/upload",
            files={
            "file": (
                "transformed_data.csv",
                edited_df.to_csv(index=False),
                "text/csv",
                )
            },
            headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
        if r.status_code == 200:
            logging.append_success('Changes saved successfully!')
        else:
            logging.append_api_error(r)
        st.session_state["state"] += 1
        st.rerun()

    case 2:  # 2 = redirecting  
        logging.clear_logs()
        time.sleep(2)
        st.switch_page("pages/transaction_input.py")

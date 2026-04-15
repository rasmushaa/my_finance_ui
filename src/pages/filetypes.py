"""Admin page for managing transaction file type definitions."""

from __future__ import annotations

import csv
import time

import pandas as pd
import requests
import st_yled as sty
import streamlit as st

from src.core.auth import require_authenticated_user
from src.core.env import require_env
from src.core.logging import append_api_error

sty.init()

REQUEST_TIMEOUT_SECONDS = 30


@st.cache_data
def get_file_types_json() -> list[dict[str, str]]:
    """Fetch registered file types from the backend API.

    Returns
    -------
    list[dict[str, str]]
        File type entries. Returns an empty list when the request fails.
    """
    user = require_authenticated_user()
    response = requests.get(
        f"{require_env('API_BASE_URL')}/app/v1/filetypes/list",
        headers={"Authorization": f"Bearer {user.token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        return response.json().get("filetypes", [])

    append_api_error(response)
    return []


def infer_csv_columns(file: st.runtime.uploaded_file_manager.UploadedFile) -> list[str]:
    """Infer CSV header columns from an uploaded sample file.

    Parameters
    ----------
    file : st.runtime.uploaded_file_manager.UploadedFile
        Sample CSV file used for format registration.

    Returns
    -------
    list[str]
        Discovered column names. Returns an empty list when detection fails.
    """
    sample = file.read(4096).decode("utf-8", errors="replace")
    file.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
    except csv.Error:
        dialect = csv.excel

    rows = list(csv.reader(sample.splitlines(), dialect=dialect))
    if not rows:
        return []
    return rows[0]


def create_file_type(
    file_name: str,
    amount_column: str,
    date_column: str,
    date_column_format: str,
    receiver_column: str,
    columns: list[str],
) -> bool:
    """Create a new file type definition in the backend.

    Parameters
    ----------
    file_name : str
        Display name for the file type.
    amount_column : str
        Source column containing transaction amounts.
    date_column : str
        Source column containing transaction dates.
    date_column_format : str
        Date format string used by ``date_column``.
    receiver_column : str
        Source column containing receiver names.
    columns : list[str]
        All columns discovered from the sample file.

    Returns
    -------
    bool
        ``True`` when file type was created successfully, otherwise ``False``.
    """
    user = require_authenticated_user()
    payload = {
        "file_name": file_name,
        "date_col": date_column,
        "date_col_format": date_column_format,
        "receiver_col": receiver_column,
        "amount_col": amount_column,
        "cols": columns,
    }

    response = requests.post(
        f"{require_env('API_BASE_URL')}/app/v1/filetypes/register",
        headers={"Authorization": f"Bearer {user.token}"},
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        return True

    append_api_error(response)
    return False


def delete_file_type(file_name: str) -> bool:
    """Delete one file type entry by name.

    Parameters
    ----------
    file_name : str
        Registered file type name to delete.

    Returns
    -------
    bool
        ``True`` when deletion succeeded, otherwise ``False``.
    """
    user = require_authenticated_user()
    response = requests.post(
        f"{require_env('API_BASE_URL')}/app/v1/filetypes/delete",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"file_name": file_name},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 200:
        return True

    append_api_error(response)
    return False


def main() -> None:
    """Render and run the file types administration page."""
    require_authenticated_user()
    st.set_page_config(layout="wide")
    _, col, _ = st.columns([1, 3, 1])
    with col:
        df_container = sty.container(
            border=True, background_color="rgb(250, 250, 246)", padding=30
        )
        df_container_header = df_container.container(horizontal=True)
        input_container = sty.container(
            border=True, background_color="rgb(250, 250, 246)", padding=30
        )

    values = get_file_types_json()
    dataframe = pd.DataFrame.from_dict(values)
    if not dataframe.empty:
        dataframe["selection"] = False
    else:
        dataframe = pd.DataFrame(columns=["selection"])

    df_container_header.header("Existing File Types")
    edited_df = df_container.data_editor(
        dataframe.reset_index(drop=True),
        column_config={
            "file_id": st.column_config.Column("File ID", disabled=True, width="small"),
            "file_name": st.column_config.Column("File Name", disabled=True),
            "date_column": st.column_config.Column("Date Column", disabled=True),
            "receiver_column": st.column_config.Column(
                "Receiver Column", disabled=True
            ),
            "amount_column": st.column_config.Column("Amount Column", disabled=True),
            "row_created_at": st.column_config.Column("Row Created At", disabled=True),
            "selection": st.column_config.CheckboxColumn(
                "Selection",
                help="Select rows for deletion",
                default=False,
            ),
        },
        hide_index=True,
        height=35 * max(dataframe.shape[0], 1) + 38,
    )

    if df_container_header.button(
        f"Delete Selected rows ({int(edited_df['selection'].sum())})",
        type="tertiary",
        disabled=not edited_df["selection"].any(),
    ):
        selected_file_names = edited_df[edited_df["selection"]]["file_name"]
        for file_name in selected_file_names:
            if delete_file_type(file_name):
                st.toast(f"{file_name} has been deleted", icon="🗑️")
        get_file_types_json.clear()
        time.sleep(1)
        st.rerun()

    with input_container:
        st.header("Register New File Type")
        sample_file = st.file_uploader(
            "Upload a sample file",
            type=["csv"],
            key="file_type_sample_file",
        )
        columns = infer_csv_columns(sample_file) if sample_file is not None else []

        with st.form("create_file_type_form", border=False):
            col1, col2, col3 = st.columns(3)
            file_name = col1.text_input("File Name", placeholder="e.g. Nordea CSV")
            amount_column = col1.selectbox(
                "Amount Column",
                options=columns,
                help="Select the column that contains transaction amounts.",
                disabled=not columns,
            )
            date_column = col2.selectbox(
                "Date Column",
                options=columns,
                help="Select the column that contains transaction dates.",
                disabled=not columns,
            )
            date_column_format = col2.selectbox(
                "Date Column Format",
                options=["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"],
                help="Select the date format used in the date column.",
            )
            receiver_column = col3.selectbox(
                "Receiver Column",
                options=columns,
                help="Select the column that contains transaction receivers.",
                disabled=not columns,
            )
            submitted = st.form_submit_button("Create File Type", type="primary")

        if submitted:
            if not columns:
                st.warning("Upload a sample CSV file before creating a file type.")
            elif not file_name.strip():
                st.warning("File name is required.")
            else:
                with st.spinner("Creating new file type...", show_time=True):
                    if create_file_type(
                        file_name=file_name.strip(),
                        amount_column=amount_column,
                        date_column=date_column,
                        date_column_format=date_column_format,
                        receiver_column=receiver_column,
                        columns=columns,
                    ):
                        st.success(f'File type "{file_name}" has been created.')
                        get_file_types_json.clear()
                        time.sleep(1)
                        st.rerun()


main()

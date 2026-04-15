"""Upload and transform transaction CSV files."""

from __future__ import annotations

import io
import time

import pandas as pd
import requests
import streamlit as st

from src.core.auth import require_authenticated_user
from src.core.env import require_env

REQUEST_TIMEOUT_SECONDS = 60


def process_uploaded_file(file: st.runtime.uploaded_file_manager.UploadedFile) -> None:
    """Send uploaded CSV file to the backend transform endpoint.

    Parameters
    ----------
    file : st.runtime.uploaded_file_manager.UploadedFile
        Uploaded CSV file from the Streamlit file uploader.
    """
    user = require_authenticated_user()
    response = requests.post(
        f"{require_env('API_BASE_URL')}/app/v1/transactions/transform",
        files={"file": ("transactions.csv", file, "text/csv")},
        headers={"Authorization": f"Bearer {user.token}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code != 200:
        fields = response.json()
        message = fields.get("message", "Unknown error")
        hint = fields.get("details", {}).get("hint", "No additional details")
        st.error(f"{message}\n\n{hint}")
        return

    st.success("File processed successfully.")
    time.sleep(1)
    dataframe = pd.read_csv(io.StringIO(response.text))
    st.session_state["processed_file_df"] = dataframe
    st.switch_page("pages/transaction_labeling.py")


def main() -> None:
    """Render and run the transaction input page."""
    require_authenticated_user()
    st.set_page_config(layout="centered")
    st.title("Banking File Processing")

    uploaded_file = st.file_uploader(
        "Choose a Banking CSV file",
        type=["csv"],
        key="input_file",
    )
    if uploaded_file is None:
        return

    with st.spinner("Processing file...", show_time=True):
        process_uploaded_file(uploaded_file)


main()

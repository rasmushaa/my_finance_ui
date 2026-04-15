import streamlit as st
import requests
import os
import io
import pandas as pd
import time
from src.core.logging import append_api_error


# The Page 
st.set_page_config(layout='centered')
st.title('Banking File Processing')

file = st.file_uploader('Choose a Banking CSV-file', type=['csv'], key='input_file')


# Process the file if it is uploaded
if file is not None:
    with st.spinner('Processing file...', show_time=True):

        r = requests.post(
            os.environ['API_BASE_URL'] + "/app/v1/transactions/transform",
            files={"file": ("mock_data.csv", file, "text/csv")},
            headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
            )
        
        if r.status_code == 200:
            st.success('File processed successfully!')
            time.sleep(1)
            df = pd.read_csv(io.StringIO(r.text))
            st.session_state['processed_file_df'] = df
            st.switch_page("pages/transaction_labeling.py")

        else:
            append_api_error(r)

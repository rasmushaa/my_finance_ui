import streamlit as st
import requests
import os
import pandas as pd
import time
import csv
from src.core.logging import append_api_error


@st.cache_data
def get_file_types_json():
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/transactions/list-filetypes", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"})
    return r.json().get('filetypes', []) if r.status_code == 200 else append_api_error(r)


# The page layout
st.set_page_config(layout="wide")
_, col, _ = st.columns([1, 4, 1])


# Get the file types from the API and show them in a data editor
values = get_file_types_json()
df = pd.DataFrame.from_dict(values)
df['selection'] = False

col.header('Existing File Types')
edited_df = col.data_editor(
    df.reset_index(drop=True),
    column_config={
        'file_id': st.column_config.Column(
            'File ID',
            disabled=True,
            width='small'
        ),
        'file_name': st.column_config.Column(
            'File Name',
            disabled=True,
        ),
        'date_column': st.column_config.Column(
            'Date Column',
            disabled=True,
        ),
        'receiver_column': st.column_config.Column(
            'Receiver Column',
            disabled=True,
        ),
        'amount_column': st.column_config.Column(
            'Amount Column',
            disabled=True,
        ),
        'row_created_at': st.column_config.Column(
            'Row Created At',
            disabled=True,
        ),
        'selection': st.column_config.CheckboxColumn(
            "Selection",
            help="Select rows for deletion",
            default=False,
        )
    },
    hide_index=True,
    height=35*df.shape[0] + 38
)

col.divider()


# Show the form to create a new file type in an expander
with col.expander("Create a new File Type", expanded=False):
    file = st.file_uploader('Upload a sample file', type=['csv'], key='file_type_sample_file')
    cols = []
    if file is not None:
        sample = file.read(4096).decode('utf-8', errors='replace')
        file.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=',;|\t')
        cols = next(csv.reader(sample.splitlines(), dialect=dialect))

    with st.form('create_file_type_form'):

        col1, col2, col3 = st.columns(3)
        file_name = col1.text_input('File Name', placeholder='e.g. Nordea CSV')
        amount_column = col1.selectbox('Amount Column', options=cols, help='Select the column that contains the transaction amounts')
        date_column = col2.selectbox('Date Column', options=cols, help='Select the column that contains the transaction dates')
        date_column_format = col2.selectbox('Date Column Format', options=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'], help='Select the date format used in the date column')
        receiver_column = col3.selectbox('Receiver Column', options=cols, help='Select the column that contains the transaction receivers')
        submitted = st.form_submit_button('Create File Type')

    if submitted:
        with st.spinner('Creating new file type...', show_time=True):

            payload = {
                "file_name": file_name,
                "date_col": date_column,
                "date_col_format": date_column_format,
                "receiver_col": receiver_column,
                "amount_col": amount_column,
                "cols": cols
            }

            r = requests.post(
                os.environ['API_BASE_URL'] + "/app/v1/transactions/register-filetype/", 
                headers={"Authorization": f"Bearer {st.session_state['user'].token}"},
                json=payload
                )
            
            if r.status_code == 200:
                st.success(f'File type "{file_name}" has been created!')
                get_file_types_json.clear()
                time.sleep(1)
                st.rerun() 

            else:
                append_api_error(r)


# If any rows are selected, show the selection and a button to delete the selected file types
if edited_df['selection'].any():
    with col:
        st.divider()
        st.subheader(f'You have selected {edited_df["selection"].sum()} file types for deletion')

        if st.button('Delete Selected File Types', width='stretch'):

            with st.spinner('Removing data...', show_time=True):

                for file_name in edited_df[edited_df['selection']]['file_name']:

                    r = requests.post(
                        os.environ['API_BASE_URL'] + f"/app/v1/transactions/delete-filetype/", 
                        headers={"Authorization": f"Bearer {st.session_state['user'].token}"},
                        json={"file_name": file_name}
                        )
                    
                    if r.status_code == 200:
                        st.toast(f'{file_name} has been deleted', icon='🗑️', duration='infinite')
                    
                    else:
                        append_api_error(r)

            get_file_types_json.clear()
            time.sleep(1)
            st.rerun() 
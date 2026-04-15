import streamlit as st
import logging
from src.core.sidebar import render_sidebar_to_user_access_level
from src.core.setup_logging import setup_logging
from src.core import focus, layout

setup_logging(level=logging.INFO)

# Main entry-point and the event-loop, that runs only once.
# Everything on this file is executed before all other Pages.

# Define all existing st.Page 'Pages' that are navigateable (required to do so), by the st.switch_page and st.page_link functions.
st.set_page_config(page_title='My Finance', page_icon='src/assets/logo.png')

all_pages = [
    st.Page('pages/login.py', default=True),
    st.Page('pages/logout.py'),
    st.Page('pages/transaction_input.py'),
    st.Page('pages/transaction_labeling.py'),
    st.Page('pages/assets.py'),
    st.Page('pages/filetypes.py'),
    st.Page('pages/ai.py'),
]

# Hide the default navigation, because that is dynamically changed in the code.
pg = st.navigation(
    all_pages,
    position='hidden'
)

# Detect page changes: compare current page to the one from the previous rerun.
focus.update(pg)

# Update the navigation accordingly to the user access level after each reload/page switch
render_sidebar_to_user_access_level()

# Main Event Run
pg.run()
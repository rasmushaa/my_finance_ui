import os
import urllib.parse as up
import requests
from src.core.user import User
import streamlit as st
import logging
import time
from src.core.logging import append_api_error

logger = logging.getLogger(__name__)


# Page layout
st.set_page_config(layout='centered')
col1, col2 = st.columns([3, 1])
col2.image('src/assets/logo.png')
env = os.getenv('ENV', 'dev')
env_siffix = '' if env=='prod' else ': STG' if env=='stg' else ': DEV'
col1.title(f'My Finance App{env_siffix}')


# 1. Go to the Google OAuth2 authentication page when the user clicks the button
params = {
    'client_id': os.environ['GOOGLE_CLIENT_ID'],
    'redirect_uri': os.environ['REDIRECT_URI'],
    'response_type': 'code',
    'scope': 'openid email profile',
    "prompt": "select_account"
}
auth_url = f"https://accounts.google.com/o/oauth2/auth?{up.urlencode(params)}"
col1.link_button('Login with Google', url=auth_url, icon=':material/account_circle:')


# 2. Handle the redirect back from Google OAuth2 with the authorization code
if st.query_params:
    query = st.query_params
    code = query.get('code')
    error = query.get('error')

    if error:
        st.error(f"Authentication failed: {error[0]}")
        st.stop()

    payload = {
        'code': code,
        "redirect_uri": os.environ['REDIRECT_URI']
    }

    r = requests.post(f"{os.environ['API_BASE_URL']}/app/v1/auth/google/code", json=payload, timeout=15)

    # Creat a user session if the authentication was successful
    if r.status_code == 200:
        st.session_state['user'] = User(**r.json())
        st.success(f"Successfully authenticated as {st.session_state['user'].user_name}!")
        time.sleep(0.5)
        st.switch_page('pages/transaction_input.py')

    # Show API error response if the authentication failed
    else:
        append_api_error(r)
        logger.error(f"Failed to authenticate with Google: {r.json()}")
        st.stop()

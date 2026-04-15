import streamlit as st


def __authenticated_menu():
    """ Show only the login menu  for unauthenticated users, and different admin levels
    """

    # Logged in user info in the sidebar
    st.sidebar.image(st.session_state['user'].user_picture_url)
    st.sidebar.subheader(st.session_state['user'].user_name)
    st.sidebar.divider()

    # Account and Logout
    st.sidebar.subheader('Account:')
    st.sidebar.page_link(st.Page('pages/logout.py'), label='Logout', icon=':material/logout:')

    # File Uploads
    st.sidebar.subheader('Uppload Files:')
    st.sidebar.page_link(st.Page('pages/transaction_input.py'), label='Transactions', icon=':material/payments:')
    st.sidebar.page_link(st.Page('pages/assets.py'), label='Assets', icon=':material/account_balance:')

    # Admin Pages
    disabled = st.session_state['user'].role != 'admin'
    st.sidebar.subheader('Manage Application:')
    st.sidebar.page_link(st.Page('pages/filetypes.py'), label='File Types', icon=':material/inbox_text_asterisk:', disabled=disabled)
    st.sidebar.page_link(st.Page('pages/ai.py'), label='AI', icon=':material/robot_2:', disabled=disabled)


def __unauthenticated_menu():
    """ Show only the login menu for unauthenticated users
    """
    st.sidebar.title('Welcome to My Finance App!')
    st.sidebar.write('Please log in to access your financial dashboard and manage your finances effectively.')
    st.sidebar.page_link('pages/login.py', label='Login', icon=':material/login:')


def render_sidebar_to_user_access_level():
    """ Determine if a user is logged in or not, 
    then show the correct navigation menu
    """
    if 'user' in st.session_state and st.session_state['user'].is_logged_in(): # Only if 'user' exists and is logged in!
        __authenticated_menu()
    else:
        __unauthenticated_menu()
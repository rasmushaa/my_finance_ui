import enum
import time
import streamlit as st
from typing import List, Dict
import logging


logger = logging.getLogger(__name__)


INFO = "INFO"
SUCCESS = "SUCCESS"
ERROR = "ERROR"


def _append_log(msg: str, log_type: str = INFO):
    """ Appends a log message to the logs in the session state.
    
    The method realys on the private streamlit session state to store the logs, 
    which are then rendered in the info column of the layout.
    Each log entry also includes a timestamp indicating when it was created.

    Parameters
    ----------
    msg : str
        The log message to append.
    log_type : str, optional
        The type of the log message, by default INFO
    """
    if "__logs" not in st.session_state:
        st.session_state["__logs"] = []
    st.session_state["__logs"].append({"message": msg, "type": log_type, "timestamp": time.time()})


def append_info(msg: str):
    _append_log(msg, INFO)
    logger.info(msg)


def append_success(msg: str):
    _append_log(msg, SUCCESS)
    logger.info(msg)


def append_error(msg: str):
    _append_log(msg, ERROR)
    logger.error(msg)


def append_api_error(response):
    """ Appends st-finance-api AppError to the logs.
    
    The st-finance-api returns errors in a specific format, with a message and a hint.
    This method extracts the relevant information from the API response and appends it as an error log.
    If the response does not match the expected format, 
    it appends a generic error message with the status code and response text.

    Parameters
    ----------
    response : requests.Response
        The response object from the API call that resulted in an error.
    """
    try: # Only the AppError has both
        response_json = response.json()
        message = response_json.get('message', '')
        details = response_json.get('details', {})
        hint = details.get('hint', '')
        text = f"""**Error:** {message}\n\n{hint}"""
        
    except Exception as e:
        text = f"An unknown error occurred. Status code: {response.status_code} Response: {response.text}"

    append_error(text)
    logger.error(f"API Error: {text}")


def get_logs() -> List[Dict[str, str]]:
    """ Returns the logs. """
    return st.session_state.get("__logs", [])


def clear_logs():
    """ Clears the logs. 
    
    Call this when you want to clear the log messages, 
    like when entering a new page or after an error is resolved. 
    """
    st.session_state["__logs"] = []


def prune_logs(older_than_seconds: int):
    """ Prunes logs that are older than the specified number of seconds. 
    
    This is useful to prevent the logs from growing indefinitely and to keep the log messages relevant.
    Call this periodically, like when entering a new page or after a certain action.

    Parameters
    ----------
    older_than_seconds : int
        The age in seconds after which logs should be pruned.
    """
    cutoff_time = time.time() - older_than_seconds
    st.session_state["__logs"] = [log for log in get_logs() if log["timestamp"] >= cutoff_time]


def render_logs(latest_first: bool = False, limit: int = None):
    """ Renders the logs in sequence to any current Streamlit container. 
    
    Call this in the info column of the layout to show the logs there. 

    Parameters
    ----------
    latest_first : bool, optional
        Whether to render the latest logs first, by default False
    limit : int, optional
        The maximum number of logs to render, by default None (render all)
    """
    logs = get_logs()

    if latest_first:
        logs = reversed(logs)

    if limit is not None:
        logs = list(logs)[:limit]

    for log in logs:
        if log["type"] == INFO:
            st.info(log["message"])

        elif log["type"] == SUCCESS:
            st.success(log["message"])

        elif log["type"] == ERROR:
            st.error(log["message"])

        else:
            st.write(log["message"])
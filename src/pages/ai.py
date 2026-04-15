"""Admin dashboard for model metadata and historical performance."""

from __future__ import annotations

import datetime
from typing import Any

import numpy as np
import pandas as pd
import requests
import st_yled as sty
import streamlit as st
from plotly import graph_objects as go

from src.core import focus, logging
from src.core.auth import require_authenticated_user
from src.core.env import require_env

st.set_page_config(layout="wide")
sty.init()

REQUEST_TIMEOUT_SECONDS = 30
PERFORMANCE_LOOKBACK_YEARS = 5


def fetch_json(
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    method: str = "GET",
) -> dict[str, Any]:
    """Call the backend API and return JSON payload on success.

    Parameters
    ----------
    endpoint : str
        API endpoint path relative to ``API_BASE_URL``.
    params : dict[str, Any] | None, optional
        Query parameters for GET requests.
    method : str, optional
        HTTP method, either ``\"GET\"`` or ``\"POST\"``.

    Returns
    -------
    dict[str, Any]
        JSON payload when request succeeds, otherwise an empty dictionary.
    """
    user = require_authenticated_user()
    url = f"{require_env('API_BASE_URL')}{endpoint}"
    headers = {"Authorization": f"Bearer {user.token}"}

    if method == "POST":
        response = requests.post(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    else:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

    if response.status_code == 200:
        return response.json()

    st.toast(response.text, icon="⚠️")
    return {}


def initialize_page_state() -> None:
    """Initialize model dashboard state when navigating to this page."""
    if not focus.changed():
        return

    logging.clear_logs()
    st.session_state["model_metadata"] = fetch_json("/app/v1/model/metadata")
    st.session_state["model_manifest"] = fetch_json("/app/v1/model/manifest")
    performance_payload = fetch_json(
        "/app/v1/reporting/model-accuracy",
        params={
            "starting_from": (
                datetime.date.today()
                - datetime.timedelta(days=PERFORMANCE_LOOKBACK_YEARS * 365)
            ).isoformat()
        },
    )
    rows = performance_payload.get("rows", [])
    st.session_state["model_performance"] = (
        pd.DataFrame.from_dict(rows) if rows else pd.DataFrame()
    )


def prepare_performance_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize performance dataframe columns for charting.

    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw dataframe from the API payload.

    Returns
    -------
    pd.DataFrame
        Chart-ready dataframe.
    """
    dataframe = raw_df.copy()
    dataframe["model_commit_sha"] = dataframe["model_commit_sha"].str[:5]
    dataframe["model_commit_head_sha"] = dataframe["model_commit_head_sha"].str[:5]
    dataframe["category"] = dataframe["category"].str.lower().str.capitalize()
    dataframe["env"] = dataframe["model_name"].apply(
        lambda value: value.split("-")[-1].capitalize()
    )
    return dataframe


def apply_filters_and_smoothing(
    dataframe: pd.DataFrame,
    env_selection: str,
    category_selection: str,
    smoothing_selection: str,
    smoothing_window: int,
) -> pd.DataFrame:
    """Apply environment, category, and smoothing options to chart data.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Performance dataframe.
    env_selection : list[str]
        Environment filter options.
    category_selection : str
        Selected category option.
    smoothing_selection : str
        Smoothing method selection.
    smoothing_window : int
        Window parameter for smoothing operations.

    Returns
    -------
    pd.DataFrame
        Filtered and optionally smoothed dataframe.
    """
    filtered = dataframe.copy()

    filtered = filtered[
        filtered["model_name"]
        .str.lower()
        .str.endswith(tuple(env.lower() for env in env_selection))
    ]
    filtered = filtered.sort_values(by=["year_month"], ascending=False).reset_index(
        drop=True
    )

    filtered = filtered[filtered["category"] == category_selection]

    model_ids = filtered["model_commit_sha"].unique()
    filtered["model_parent"] = filtered["model_commit_head_sha"].apply(
        lambda value: value if value in model_ids else None
    )
    filtered["model_chain_id"] = filtered["model_parent"].fillna(
        filtered["model_commit_sha"]
    )

    if smoothing_selection != "Raw" and not filtered.empty:
        filtered = filtered.sort_values(by=["model_chain_id", "year_month"])
        if smoothing_selection == "EMA":
            filtered["accuracy"] = filtered.groupby("model_commit_sha")[
                "accuracy"
            ].transform(
                lambda values: values.ewm(span=smoothing_window, adjust=False).mean()
            )
        elif smoothing_selection == "SMA":
            filtered["accuracy"] = filtered.groupby("model_commit_sha")[
                "accuracy"
            ].transform(
                lambda values: values.rolling(
                    window=smoothing_window, min_periods=1
                ).mean()
            )

    return filtered


def create_performance_figure(
    dataframe: pd.DataFrame, smoothing_selection: str
) -> go.Figure:
    """Build a Plotly figure for model accuracy performance.

    Parameters
    ----------
    dataframe : pd.DataFrame
        Dataframe to visualize.
    smoothing_selection : str
        Active smoothing mode used to choose line interpolation.

    Returns
    -------
    go.Figure
        Plotly figure with one trace per model/category combination.
    """
    figure = go.Figure()
    colors = [
        "#E06565",
        "#7E78EE",
        "#00CC96",
        "#FA63CF",
        "#FFA15A",
        "#19D3F3",
        "#FF6692",
        "#B6E880",
        "#FF97FF",
        "#FECB52",
    ]

    if dataframe.empty:
        return figure

    chain_stats = dataframe.groupby("model_chain_id").agg(
        latest=("year_month", "max"),
        has_prod=("env", lambda values: values.str.lower().eq("prod").any()),
    )
    chain_order = list(
        chain_stats.sort_values(
            by=["has_prod", "latest"], ascending=[False, False]
        ).index
    )

    for index, chain_id in enumerate(chain_order):
        model_chain_data = dataframe[dataframe["model_chain_id"] == chain_id]
        env_order = {"prod": 0, "stg": 1}
        sorted_model_names = sorted(
            model_chain_data["model_name"].unique(),
            key=lambda value: env_order.get(value.split("-")[-1].lower(), 2),
        )
        for model_name in sorted_model_names:
            model_env_data = model_chain_data[
                model_chain_data["model_name"] == model_name
            ]
            for category in model_env_data["category"].unique():
                category_data = model_env_data[
                    model_env_data["category"] == category
                ].copy()
                line_style = (
                    "solid"
                    if "prod" in model_name.lower()
                    else "dot" if "stg" in model_name.lower() else "dash"
                )
                color = colors[index % len(colors)]
                figure.add_trace(
                    go.Scatter(
                        x=category_data["year_month"],
                        y=category_data["accuracy"],
                        customdata=np.stack(
                            (
                                category_data["model_commit_sha"],
                                category_data["model_alias"],
                                category_data["model_name"],
                                category_data["model_version"],
                                category_data["model_commit_head_sha"],
                                category_data["model_architecture"],
                            ),
                            axis=-1,
                        ),
                        mode="lines+markers",
                        name=f"<b>{model_name}</b> ({category})",
                        line=dict(
                            color=color,
                            dash=line_style,
                            shape=(
                                "linear" if smoothing_selection == "Raw" else "spline"
                            ),
                        ),
                        hovertemplate=(
                            "<b>Arch:</b> %{customdata[5]}<br>"
                            "<b>Version:</b> %{customdata[3]}<br>"
                            "<b>Hash:</b> %{customdata[0]}<br>"
                            "<b>Parent:</b> %{customdata[4]}<br>"
                            "<b>Alias:</b> %{customdata[1]}<br>"
                            f"<b>Category:</b> {category}<br>"
                            "<b>Accuracy:</b> %{y:.2%}<br>"
                            "<extra></extra>"
                        ),
                    )
                )
    figure.update_layout(
        hovermode="x unified",
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        margin=dict(l=20, r=20, t=30, b=20),
    )
    return figure


def render_metadata_card(column: Any) -> None:
    """Render model metadata/manifest card and reload action.

    Parameters
    ----------
    column : Any
        Streamlit column where metadata card is rendered.
    """
    with column:
        with sty.container(
            border=True, background_color="rgb(250, 250, 246)", padding=20
        ):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.header("Active Model")
                metadata_selection = st.segmented_control(
                    "Metadata view",
                    options=["Metadata", "Manifest"],
                    selection_mode="single",
                    default="Metadata",
                    label_visibility="collapsed",
                )
                reload_clicked = st.button(
                    "Reload",
                    help="Reload latest models from storage and refresh this page.",
                )

            if reload_clicked:
                fetch_json("/app/v1/model/reload", method="POST")
                focus.reset_on_page_change()
                st.rerun()

            if metadata_selection == "Metadata":
                st.json(st.session_state.get("model_metadata", {}))
            else:
                st.json(st.session_state.get("model_manifest", {}))


def render_performance_card(column: Any) -> None:
    """Render model performance dashboard card.

    Parameters
    ----------
    column : Any
        Streamlit column where performance card is rendered.
    """
    raw_df = st.session_state.get("model_performance", pd.DataFrame())
    with column:
        with sty.container(
            border=True, background_color="rgb(250, 250, 246)", padding=20
        ):
            if raw_df.empty:
                st.header("Model Performance Dashboard")
                st.info("No model performance data is available yet.")
                return

            dataframe = prepare_performance_dataframe(raw_df)
            category_options = [*sorted(dataframe["category"].unique())]

            with st.container(horizontal=True, vertical_alignment="center"):
                st.header("Model Performance Dashboard")
                env_selection = st.segmented_control(
                    "Environment",
                    options=["Prod", "Stg"],
                    selection_mode="multi",
                    default="Prod",
                    label_visibility="collapsed",
                )
                smoothing_selection = st.segmented_control(
                    "Smoothing",
                    options=["Raw", "EMA", "SMA"],
                    selection_mode="single",
                    default="Raw",
                    label_visibility="collapsed",
                )
                smoothing_window = st.number_input(
                    "Smoothing window",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1,
                    label_visibility="collapsed",
                    disabled=(smoothing_selection == "Raw"),
                    width=150,
                )
                category_selection = st.selectbox(
                    "Category filter",
                    options=category_options,
                    index=0,
                    label_visibility="collapsed",
                )
                show_raw_table = st.checkbox("Raw", value=False)

            chart_df = apply_filters_and_smoothing(
                dataframe=dataframe,
                env_selection=env_selection,
                category_selection=category_selection,
                smoothing_selection=smoothing_selection,
                smoothing_window=int(smoothing_window),
            )

            if show_raw_table:
                st.table(
                    chart_df.sort_values(
                        by=["year_month", "model_alias"], ascending=False
                    ).reset_index(drop=True),
                    height=800,
                    width="stretch",
                )
                return

            figure = create_performance_figure(
                chart_df, smoothing_selection=smoothing_selection
            )
            st.plotly_chart(figure, height=690, width="stretch")


def main() -> None:
    """Render and run the AI administration page."""
    require_authenticated_user()
    initialize_page_state()
    col1, col2 = st.columns([3, 7])
    render_metadata_card(col1)
    render_performance_card(col2)


main()

import requests
import os
import datetime
import streamlit as st
import st_yled as sty
from src.core import focus, logging, layout
import pandas as pd
import numpy as np
from plotly import graph_objects as go

sty.init()


# -- Init page state ---------------------------------------
if focus.changed():

    logging.clear_logs()

    # Model metadata
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/model/metadata", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
    if r.status_code != 200:
        st.toast(r.text, icon="⚠️")
    st.session_state["model_metadata"] = r.json() if r.status_code == 200 else {}

    # Model manifest
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/model/manifest", 
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
    if r.status_code != 200:
        st.toast(r.text, icon="⚠️")
    st.session_state["model_manifest"] = r.json() if r.status_code == 200 else {}

    # Model performance
    r = requests.get(
        os.environ['API_BASE_URL'] + "/app/v1/reporting/model-accuracy", 
        params={"starting_from": (datetime.date.today() - datetime.timedelta(days=5*365)).isoformat()}, # Last 5 years
        headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
        )
    if r.status_code != 200:
        st.toast(r.text, icon="⚠️")
    st.session_state["model_performance"] = pd.DataFrame.from_dict(r.json()["rows"]) if r.status_code == 200 else None


# -- Base layout ---------------------------------------
st.set_page_config(layout="wide")
col1, col2 = st.columns([3, 7])


# -- Metadata card ---------------------------------------
with col1:
    with sty.container(border=True, background_color="rgb(250, 250, 246)", padding=20):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.header("Active Model")
            meta_data_selection = st.segmented_control(
                "Metadata view", 
                options=["Metadata", "Manifest"], 
                selection_mode="single", 
                default="Metadata", 
                label_visibility="collapsed",
            )   
            reload = st.button("Reload", help="Force reload latest moodels to API from GCS, and reset page state")

        # Load button
        if reload:
            r = requests.post(
                os.environ['API_BASE_URL'] + "/app/v1/model/reload", 
                headers={"Authorization": f"Bearer {st.session_state['user'].token}"}
                )
            if r.status_code != 200:
                st.toast(r.text, icon="⚠️")
            focus.reset_on_page_change()
            st.rerun()

        # Data selection
        if meta_data_selection == "Metadata":
            st.json(st.session_state["model_metadata"])
        else:
            st.json(st.session_state["model_manifest"])


# -- Performance dashboard ---------------------------------------
with col2:
    with sty.container(border=True, background_color="rgb(250, 250, 246)", padding=20):

        # Format the performance data for plotting
        df = st.session_state["model_performance"].copy()
        df["model_commit_sha"] = df["model_commit_sha"].apply(lambda x: x[:5])  # Shorten commit hash for display
        df["model_commit_head_sha"] = df["model_commit_head_sha"].apply(lambda x: x[:5]) 
        df["category"] = df["category"].str.lower().str.capitalize()

        # Header and category selection
        with st.container(horizontal=True, vertical_alignment="center"):
            st.header("Model Performance Dashboard")
            env_selection = st.segmented_control(
                "Environment", 
                options=["Prod", "All"], 
                selection_mode="single", 
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
            category_selection = st.multiselect(
                "Category filter", 
                sorted(df["category"].unique()), 
                default="All",
                label_visibility="collapsed",
                max_selections=1,
            )
            show_raw = st.checkbox("Raw", value=False)

        # Transform the data to plotting format
        if env_selection == "Prod":
             df = df[df["model_name"].str.lower().str.endswith("-prod")]
             df = df.sort_values(by=["year_month"], ascending=False).reset_index(drop=True)

        df = df[df["category"].isin(category_selection)]
        model_ids = df["model_commit_sha"].unique()
        df["model_parent"] = df["model_commit_head_sha"].apply(lambda x: x if x in model_ids else None)
        df["model_chain_id"] = df["model_parent"].fillna(df["model_commit_sha"])
        df["env"] = df["model_name"].apply(lambda x: x.split("-")[-1].capitalize())
        if smoothing_selection != "Raw":
            df = df.sort_values(by=["model_chain_id", "year_month"])
            if smoothing_selection == "EMA":
                df["accuracy"] = df.groupby("model_commit_sha")["accuracy"].transform(lambda x: x.ewm(span=smoothing_window, adjust=False).mean())
            elif smoothing_selection == "SMA":
                df["accuracy"] = df.groupby("model_commit_sha")["accuracy"].transform(lambda x: x.rolling(window=smoothing_window, min_periods=1).mean())


        # Dashboard plotting
        fig = go.Figure()
        colors = [
            "#E06565", "#7E78EE", "#00CC96", "#FA63CF", "#FFA15A",
            "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
        ]

        # Iterate over model chains (grouping by parent commit or self if no parent)
        chain_stats = df.groupby("model_chain_id").agg(
            latest=("year_month", "max"),
            has_prod=("env", lambda x: x.str.lower().eq("prod").any())
        ).sort_values(by=["has_prod", "latest"], ascending=[False, False])
        chain_order_list = list(chain_stats.index)
        for i, model_id in enumerate(chain_order_list):
            model_chain_data = df[df["model_chain_id"] == model_id]

            # Iterate over model names (environments) for the current model chain, prod first
            env_order = {"prod": 0, "stg": 1}
            sorted_model_names = sorted(
                model_chain_data["model_name"].unique(),
                key=lambda x: env_order.get(x.split("-")[-1].lower(), 2)
            )
            for model_name in sorted_model_names:
                model_env_data = model_chain_data[model_chain_data["model_name"] == model_name]
                env_suffix = model_name.split("-")[-1].lower()

                # Itetrate over all categories for the current model and alias
                for category in model_env_data["category"].unique():
                    model_env_category_data = model_env_data[model_env_data["category"] == category].copy()

                    ls = "solid" if "prod" in model_name.lower() else "dot" if "stg" in model_name.lower() else "dash"
                    color = colors[i % len(colors)]

                    fig.add_trace(
                        go.Scatter(
                            x=model_env_category_data["year_month"], 
                            y=model_env_category_data["accuracy"], 
                            customdata=np.stack((
                                model_env_category_data["model_commit_sha"], 
                                model_env_category_data["model_alias"], 
                                model_env_category_data["model_name"],
                                model_env_category_data["model_version"],
                                model_env_category_data["model_commit_head_sha"], 
                                model_env_category_data["model_architecture"], 
                                ), axis=-1),
                            mode='lines+markers', 
                            name=f'<b>{model_name}</b> ({category})',
                            line=dict(color=color, dash=ls, shape="linear" if smoothing_selection == "Raw" else "spline"),
                            hovertemplate=
                            "<b>Arch:</b> %{customdata[5]}<br>" +
                            "<b>Version:</b> %{customdata[3]}<br>" +
                            "<b>Hash:</b> %{customdata[0]}<br>" +
                            "<b>Parent:</b> %{customdata[4]}<br>" +
                            "<b>Alias:</b> %{customdata[1]}<br>" +
                            f"<b>Category:</b> {category}<br>" +
                            "<b>Accuracy:</b> %{y:.2%}<br>" +
                            "<extra></extra>"
                        )
                    )
            
        fig.update_layout(
            hovermode='x unified',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            margin=dict(l=20, r=20, t=30, b=20),
        )
            
        if not show_raw:
            st.plotly_chart(fig, height=690, width="stretch")
        else:
            st.table(st.session_state["model_performance"].sort_values(by=["year_month", "model_alias"], ascending=False).reset_index(drop=True), height=800, width="stretch")


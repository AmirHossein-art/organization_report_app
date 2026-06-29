from pathlib import Path

import streamlit as st


def load_css():
    css_path = Path("assets/styles/main.css")
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def setup_page(
    title: str,
    icon: str = "📊",
    layout: str = "wide",
    sidebar_state: str = "expanded",
):
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=sidebar_state,
    )
    load_css()
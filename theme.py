"""
Configuración de tema visual / apariencia de la aplicación.
"""
import streamlit as st


def _apply_theme_override(theme_mode):
    """Permite forzar apariencia clara u oscura sin depender del modo del sistema."""
    if theme_mode == "Claro":
        st.markdown("""
        <style>
            .stApp, [data-testid="stAppViewContainer"] {
                background-color: #f8fafc !important;
                color: #0f172a !important;
            }
            [data-testid="stHeader"], [data-testid="stToolbar"] {
                background-color: #f8fafc !important;
            }
            [data-testid="stSidebar"] {
                background-color: #eef2f7 !important;
                color: #0f172a !important;
            }
            h1, h2, h3, h4, h5, h6, p, span, label, div {
                color: #0f172a;
            }
            .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
            .stNumberInput input {
                background-color: #ffffff !important;
                color: #0f172a !important;
                border-color: #cbd5e1 !important;
            }
            /* Dropdown popup del selectbox/multiselect — portal nivel body */
            [data-baseweb="popover"], [data-baseweb="popover"] > div,
            div[data-baseweb="menu"], ul[data-baseweb="menu"],
            [data-baseweb="select-dropdown"],
            div[class*="Menu"], div[class*="menu"],
            div[data-baseweb="popover"] * {
                background-color: #ffffff !important;
                color: #0f172a !important;
            }
            li[data-baseweb="option"], li[data-baseweb="option"] > div,
            li[data-baseweb="option"] * {
                background-color: #ffffff !important;
                color: #0f172a !important;
            }
            li[data-baseweb="option"]:hover,
            li[data-baseweb="option"]:hover *,
            [data-baseweb="option"][aria-selected="true"],
            [data-baseweb="option"][aria-selected="true"] * {
                background-color: #e2e8f0 !important;
                color: #0f172a !important;
            }
            /* File uploader */
            [data-testid="stFileUploader"] section,
            [data-testid="stFileUploadDropzone"],
            [data-testid="stFileUploader"] > div {
                background-color: #f8fafc !important;
                color: #0f172a !important;
                border-color: #cbd5e1 !important;
            }
            [data-testid="stFileUploader"] small,
            [data-testid="stFileUploader"] span,
            [data-testid="stFileUploader"] p {
                color: #64748b !important;
            }
            /* Expander header y contenido */
            [data-testid="stExpander"],
            [data-testid="stExpander"] > details,
            [data-testid="stExpander"] > details > summary,
            [data-testid="stExpander"] > details > div {
                background-color: #f8fafc !important;
                color: #0f172a !important;
                border-color: #cbd5e1 !important;
            }
            [data-testid="stExpander"] > details > summary svg {
                fill: #0f172a !important;
            }
            .stButton > button,
            [data-testid="stDownloadButton"] > button,
            [data-testid="stFormSubmitButton"] > button,
            button[kind="formSubmit"],
            button[kind="secondaryFormSubmit"] {
                background: #ffffff !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
            }
            [data-testid="stDownloadButton"] > button:hover,
            [data-testid="stFormSubmitButton"] > button:hover,
            .stButton > button:hover {
                background: #f1f5f9 !important;
                border-color: #94a3b8 !important;
            }
            ::selection {
                background-color: #bfdbfe !important;
                color: #1e3a5f !important;
            }
            div[data-testid="stMetric"] {
                background: #ffffff !important;
                border: 1px solid #dbe3ef !important;
            }
            div[data-testid="stMetricLabel"],
            div[data-testid="stMetricValue"],
            div[data-testid="stMetricDelta"],
            div[data-testid="stMetricLabel"] *,
            div[data-testid="stMetricValue"] *,
            div[data-testid="stMetricDelta"] * {
                color: #0f172a !important;
            }
        </style>
        """, unsafe_allow_html=True)
    elif theme_mode == "Oscuro":
        st.markdown("""
        <style>
            .stApp, [data-testid="stAppViewContainer"] {
                background-color: #0b1220 !important;
                color: #e2e8f0 !important;
            }
            [data-testid="stHeader"], [data-testid="stToolbar"] {
                background-color: #0b1220 !important;
            }
            [data-testid="stSidebar"] {
                background-color: #101a2e !important;
                color: #e2e8f0 !important;
            }
            div[data-testid="stMetric"] {
                background: #111827 !important;
                border: 1px solid #334155 !important;
            }
            div[data-testid="stMetricLabel"],
            div[data-testid="stMetricValue"],
            div[data-testid="stMetricDelta"],
            div[data-testid="stMetricLabel"] *,
            div[data-testid="stMetricValue"] *,
            div[data-testid="stMetricDelta"] * {
                color: #e2e8f0 !important;
            }
            /* Dropdown popup oscuro */
            [data-baseweb="popover"], [data-baseweb="popover"] > div,
            div[data-baseweb="menu"], ul[data-baseweb="menu"] {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            li[data-baseweb="option"], li[data-baseweb="option"] > div {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
            }
            li[data-baseweb="option"]:hover,
            [data-baseweb="option"][aria-selected="true"] {
                background-color: #334155 !important;
                color: #e2e8f0 !important;
            }
            .stTextInput input, .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stNumberInput input {
                background-color: #1e293b !important;
                color: #e2e8f0 !important;
                border-color: #475569 !important;
            }
        </style>
        """, unsafe_allow_html=True)


def _render_theme_switcher():
    """Control global de apariencia."""
    if "ui_theme_mode" not in st.session_state:
        st.session_state["ui_theme_mode"] = "Sistema"

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🎨 Apariencia")
        st.radio(
            "Tema visual",
            options=["Sistema", "Claro", "Oscuro"],
            key="ui_theme_mode",
            horizontal=False,
            help="Elige 'Claro' para ver la app con colores normales aunque tu PC esté en modo oscuro.",
        )

    _apply_theme_override(st.session_state.get("ui_theme_mode", "Sistema"))

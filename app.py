import streamlit as st
import os
from utils import nav

# =========================================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================================
st.set_page_config(
    page_title="Evaluaciones Psicométricas RH",
    layout="wide",
    page_icon="🧠",
)

st.markdown("""
<style>
    .stApp { max-width: 100% !important; padding: 0 !important; }
    .block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    .stButton>button { font-weight: bold; }
    /* Ocultar navegación automática de páginas de Streamlit */
    [data-testid="stSidebarNav"] { display: none !important; }
    /* Reducir espacio superior del sidebar */
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }
    [data-testid="stSidebarContent"] { padding-top: 0.5rem !important; }
    div[data-testid="stMetric"] {
        background: var(--secondary-background-color, #f8fafc);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        min-height: 110px;
    }
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricValue"] *,
    div[data-testid="stMetricDelta"] * {
        color: var(--text-color, #0f172a) !important;
    }
</style>
""", unsafe_allow_html=True)


from theme import _apply_theme_override, _render_theme_switcher

_render_theme_switcher()

from auth import (
    ADMIN_IDLE_TIMEOUT_MINUTES, ADMIN_SESSION_SECRET,
    _get_admin_token_from_query, _set_admin_token_in_query,
    _create_admin_session_token, _parse_admin_session_token,
    _get_admin_by_id, _start_admin_session, _touch_admin_session,
    _restore_admin_session, _logout_admin,
)




# =========================================================================
# PÁGINAS
# =========================================================================

def page_home():
    # Logo HESEGO centrado con HTML
    _logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(_logo_path):
        import base64
        with open(_logo_path, "rb") as _lf:
            _logo_b64 = base64.b64encode(_lf.read()).decode()
        st.markdown(
            f"<div style='display:flex;justify-content:center;margin-bottom:8px'>"
            f"<img src='data:image/png;base64,{_logo_b64}' style='width:200px;height:auto'/>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown("<h1 style='text-align:center; color:#1e3a5f;'>Plataforma de Evaluaciones Psicométricas</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#555;'>Sistema de evaluación para Recursos Humanos</p>", unsafe_allow_html=True)
    st.markdown("---")

    text_col1, text_col2, text_col3 = st.columns(3, gap="large")
    with text_col1:
        st.markdown(
            """
            ### 👤 Soy Candidato / Empleado
            Ingresa con tu número de cédula para realizar la evaluación asignada por Recursos Humanos.
            """
        )

    with text_col2:
        st.markdown(
            """
            ### 👔 Soy Jefe / Evaluador
            Ingresa para completar las evaluaciones de tus colaboradores una vez que ellos hayan realizado su auto-evaluación.
            """
        )

    with text_col3:
        st.markdown(
            """
            ### 🔒 Soy Administrador RH
            Accede al panel de administración para gestionar evaluaciones y ver resultados.
            """
        )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    btn_col1, btn_col2, btn_col3 = st.columns(3, gap="large")
    with btn_col1:
        if st.button("🔑 Ingresar como Candidato / Empleado", use_container_width=True, key="btn_candidate"):
            nav("candidate_login")
            st.rerun()

    with btn_col2:
        if st.button("✏️ Ingresar como Evaluador", use_container_width=True, key="btn_evaluador"):
            nav("evaluador_login")
            st.rerun()

    with btn_col3:
        if st.button("🛡️ Ingresar como Administrador", use_container_width=True, key="btn_admin"):
            nav("admin_login")
            st.rerun()


# =========================================================================
# PÁGINAS → pages/
# =========================================================================
from pages.admin import (
    page_admin_login, page_admin_dashboard,
    page_shared_result_view,
    show_disc_results_admin, show_valanti_results_admin,
    show_wpi_results_admin, show_eri_results_admin,
)
from pages.talent_map import page_talent_map_test, show_talent_map_results_admin
from pages.desempeno import (
    page_desempeno_eval, show_desempeno_results_admin,
    page_desempeno_lider_eval, show_desempeno_lider_results_admin,
    page_periodo_prueba_eval, show_periodo_prueba_results_admin,
)
from pages.evaluador import (
    page_evaluador_login, page_evaluador_dashboard,
    page_desempeno_lider_employee_eval, page_periodo_prueba_employee_eval,
    page_desempeno_medios_employee_eval, page_desempeno_lider_jefe_eval,
    page_desempeno_medios_jefe_eval, page_periodo_prueba_jefe_eval,
)
from pages.candidate import (
    page_candidate_login, page_candidate_select_test,
    page_disc_test, page_valanti_test, page_wpi_test,
    page_eri_test, page_candidate_done,
)


# =========================================================================
# MAIN ROUTING
# =========================================================================

_restore_admin_session()

try:
    _qp_page = st.query_params.get("page")
    _qp_rv = st.query_params.get("rv")
except Exception:
    _qp_page = None
    _qp_rv = None

if _qp_page == "shared_result" and _qp_rv:
    st.session_state["shared_result_token"] = _qp_rv
    st.session_state["page"] = "shared_result_view"

if "page" not in st.session_state:
    st.session_state.page = "admin_dashboard" if st.session_state.get("admin") else "home"
else:
    if st.session_state.get("admin"):
        _touch_admin_session()

page = st.session_state.page

PAGE_MAP = {
    "home": page_home,
    "admin_login": page_admin_login,
    "admin_dashboard": page_admin_dashboard,
    "shared_result_view": page_shared_result_view,
    "evaluador_login": page_evaluador_login,
    "evaluador_dashboard": page_evaluador_dashboard,
    "candidate_login": page_candidate_login,
    "candidate_select_test": page_candidate_select_test,
    "disc_test": page_disc_test,
    "valanti_test": page_valanti_test,
    "wpi_test": page_wpi_test,
    "eri_test": page_eri_test,
    "talent_map_test": page_talent_map_test,
    "desempeno_eval": page_desempeno_eval,
    "desempeno_lider_eval": page_desempeno_lider_eval,
    "desempeno_lider_employee_eval": page_desempeno_lider_employee_eval,
    "desempeno_lider_jefe_eval": page_desempeno_lider_jefe_eval,
    "desempeno_medios_employee_eval": page_desempeno_medios_employee_eval,
    "desempeno_medios_jefe_eval": page_desempeno_medios_jefe_eval,
    "periodo_prueba_eval": page_periodo_prueba_eval,
    "periodo_prueba_employee_eval": page_periodo_prueba_employee_eval,
    "periodo_prueba_jefe_eval": page_periodo_prueba_jefe_eval,
    "candidate_done": page_candidate_done,
}

if page in PAGE_MAP:
    PAGE_MAP[page]()
else:
    nav("home")
    st.rerun()

st.markdown("""
---
<div style="text-align:center; color: #888;">
    <small>Plataforma de Evaluaciones Psicométricas | Recursos Humanos</small>
</div>
""", unsafe_allow_html=True)

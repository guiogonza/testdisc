import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import os
import math
import base64
from io import BytesIO
from datetime import datetime, timedelta, timezone as _tz_mod

_GMT5 = _tz_mod(timedelta(hours=-5))
def _now_gmt5(): return datetime.now(_GMT5)

import database as db
from constants import *
from calculations import (
    normalize_disc_scores,
    calculate_disc_results,
    calculate_behavioral_styles,
    get_disc_temperament,
    generate_disc_mega_summary,
    calculate_valanti_results,
    calculate_wpi_results,
    load_eri_questions,
    calculate_eri_results,
    load_talent_map_questions,
    calculate_talent_map_results,
    calculate_desempeno_results,
    calculate_desempeno_lider_results,
    calculate_periodo_prueba_results,
)
from analysis import (
    analyze_disc_aptitude,
    analyze_valanti_aptitude,
    analyze_wpi_aptitude,
    analyze_eri_aptitude,
    analyze_talent_map_match,
)
from charts import (
    create_disc_plot, create_behavioral_styles_chart,
    create_valanti_radar, create_valanti_bars,
    create_wpi_radar, create_wpi_bars,
    create_eri_radar, create_eri_bars,
    create_talent_map_radar, create_talent_map_bars,
    create_talent_map_comparison,
    create_desempeno_radar, create_desempeno_bars,
)
from pdfs import (
    generate_disc_pdf, generate_valanti_pdf, generate_wpi_pdf,
    generate_eri_pdf, generate_talent_map_pdf, generate_desempeno_pdf,
    generate_desempeno_lider_pdf, generate_periodo_prueba_pdf,
)
from utils import load_disc_questions, load_disc_descriptions, load_wpi_questions, nav
from auth import (
    _restore_admin_session, _touch_admin_session,
    _logout_admin, _start_admin_session,
)

def page_evaluador_login():
    st.markdown("## 👔 Acceso Evaluador / Jefe")
    st.info("Ingresa tu cédula para ver y completar las evaluaciones de tus colaboradores.")
    if st.button("⬅️ Volver al inicio"):
        nav("home")
        st.rerun()

    with st.form("evaluador_login_form"):
        cedula = st.text_input("Tu Cédula", placeholder="Número de cédula del evaluador/jefe")
        submitted = st.form_submit_button("🔑 Ingresar")
        if submitted:
            cedula = cedula.strip()
            if not cedula:
                st.error("Ingresa tu cédula.")
            else:
                sessions = db.get_sessions_for_evaluador(cedula)
                candidate_info = db.get_candidate_by_cedula(cedula)
                assigned_name = None
                if sessions:
                    assigned_name = next((s.get("evaluador_nombre") for s in sessions if s.get("evaluador_nombre")), None)
                name = candidate_info["name"] if candidate_info else (assigned_name or cedula)
                if not sessions:
                    st.warning("No tienes evaluaciones pendientes de tu parte en este momento.")
                    st.caption("Las evaluaciones aparecerán aquí una vez que el empleado complete su auto-evaluación.")
                st.session_state["evaluador"] = {"cedula": cedula, "name": name}
                nav("evaluador_dashboard")
                st.rerun()


# -------------------------------------------------------------------------
# EVALUADOR/JEFE: DASHBOARD
# -------------------------------------------------------------------------
def page_evaluador_dashboard():
    evaluador = st.session_state.get("evaluador")
    if not evaluador:
        nav("evaluador_login")
        st.rerun()
        return

    st.markdown(f"## 👔 Panel del Evaluador / Jefe")
    st.caption(f"Bienvenido, **{evaluador['name']}** | Cédula: {evaluador['cedula']}")

    if st.button("🚪 Cerrar Sesión"):
        st.session_state.pop("evaluador", None)
        nav("home")
        st.rerun()

    sessions = db.get_sessions_for_evaluador(evaluador["cedula"])

    if not sessions:
        st.info("📋 No tienes evaluaciones pendientes de tu parte en este momento.")
        st.caption("Las evaluaciones aparecerán aquí una vez que el empleado complete su auto-evaluación. Vuelve más tarde.")
        return

    st.success("✅ Tienes evaluaciones asignadas para completar.")
    st.markdown(f"### Evaluaciones Pendientes de tu Parte ({len(sessions)})")
    st.markdown("---")

    for sess in sessions:
        test_label = {
            "desempeno": "📈 Evaluación de Desempeño — Operativo",
            "desempeno_lider": "📊 Evaluación de Desempeño — Líderes",
            "periodo_prueba": "📋 Evaluación Período de Prueba",
        }.get(sess["test_type"], sess["test_type"])

        with st.container():
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(f"### {test_label}")
                st.markdown(f"**Empleado:** {sess['candidate_name']} | **Cédula:** {sess['cedula']}")
                st.caption(f"ID: {sess['id']} | Creado: {sess.get('created_at', 'N/A')[:10]}")
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                if sess["test_type"] == "desempeno":
                    st.info("Pendiente ⏳")
                else:
                    st.success("Listo ✅")
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✏️ Completar mi Evaluación", key=f"ev_{sess['id']}", use_container_width=True):
                    st.session_state["evaluador_session_id"] = sess["id"]
                    if sess["test_type"] == "desempeno":
                        st.session_state["desempeno_session_id"] = sess["id"]
                        nav("desempeno_eval")
                    elif sess["test_type"] == "desempeno_lider":
                        nav("desempeno_lider_jefe_eval")
                    elif sess["test_type"] == "periodo_prueba":
                        nav("periodo_prueba_jefe_eval")
                    st.rerun()
            st.markdown("---")


# -------------------------------------------------------------------------
# CANDIDATO: AUTO-EVALUACIÓN DESEMPEÑO LÍDERES
# -------------------------------------------------------------------------
def page_desempeno_lider_employee_eval():
    """Auto-evaluación del empleado para Desempeño Líderes (7 competencias)."""
    session = st.session_state.get("test_session")
    candidate = st.session_state.get("candidate")

    if not session or not candidate:
        nav("candidate_login")
        st.rerun()
        return

    session_id = session["id"]
    nivel_cargo = candidate.get("nivel_cargo", "ANALISTA") or "ANALISTA"

    st.markdown("## 📊 Auto-Evaluación de Competencias")
    st.markdown(f"**Candidato:** {candidate['name']}")
    st.info("Evalúa con honestidad el nivel que consideras que has alcanzado en cada competencia organizacional.")
    st.markdown("---")

    with st.form("employee_competencias_form"):
        st.markdown("### Competencias Organizacionales — Autoevaluación")
        st.markdown("Selecciona el nivel que mejor describe tu desempeño actual:")

        nivel_req_info = COMPETENCIAS_NIVEL_REQUERIDO.get(nivel_cargo.upper(), None)
        competencias_scores = {}

        for comp in COMPETENCIAS_ORGANIZACIONALES:
            req = nivel_req_info["niveles"][comp["id"] - 1] if nivel_req_info else None
            req_text = f" _(Nivel requerido para tu cargo: {req})_" if req else ""
            st.markdown(f"**{comp['nombre']}**{req_text}")
            st.caption(comp["descripcion"])
            nivel_sel = st.radio(
                f"Nivel {comp['nombre']}",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x, c=comp: f"Nivel {x} — {c['niveles'][x][:80]}...",
                horizontal=True,
                key=f"emp_comp_{comp['id']}",
                label_visibility="collapsed",
                index=2,
            )
            competencias_scores[comp["id"]] = nivel_sel
            with st.expander("Ver descripción completa de este nivel"):
                st.info(comp["niveles"][nivel_sel])
            st.markdown("---")

        submitted = st.form_submit_button("✅ Enviar Auto-Evaluación", use_container_width=True, type="primary")

        if submitted:
            partial_results = {
                "employee_self": {
                    "competencias_scores": {str(k): v for k, v in competencias_scores.items()},
                    "nivel_cargo": nivel_cargo,
                }
            }
            db.save_results(session_id, partial_results)
            db.set_employee_done_status(session_id)

            for key in ["test_session"]:
                st.session_state.pop(key, None)

            nav("candidate_done")
            st.rerun()


# -------------------------------------------------------------------------
# CANDIDATO: AUTO-EVALUACIÓN PERÍODO DE PRUEBA
# -------------------------------------------------------------------------
def page_periodo_prueba_employee_eval():
    """Auto-evaluación del empleado para Período de Prueba (18 actuaciones)."""
    session = st.session_state.get("test_session")
    candidate = st.session_state.get("candidate")

    if not session or not candidate:
        nav("candidate_login")
        st.rerun()
        return

    session_id = session["id"]

    st.markdown("## 📋 Auto-Evaluación — Período de Prueba")
    st.markdown(f"**Candidato:** {candidate['name']}")
    st.info("Evalúa con honestidad con qué frecuencia realizas cada comportamiento en tu trabajo.")
    st.markdown("---")

    with st.form("employee_periodo_prueba_form"):
        st.markdown("### Actuaciones y Comportamientos — Autoevaluación")
        st.markdown("**Siempre=4 | Casi Siempre=3 | Algunas Veces=2 | Nunca=1**")

        actuaciones_scores = {}
        for idx, actuacion in enumerate(PERIODO_PRUEBA_ACTUACIONES):
            col_act, col_score = st.columns([4, 1])
            with col_act:
                st.markdown(f"**{idx + 1}.** {actuacion}")
            with col_score:
                actuaciones_scores[idx] = st.selectbox(
                    f"Actuación {idx+1}",
                    options=[4, 3, 2, 1],
                    format_func=lambda x: PERIODO_PRUEBA_ESCALA_ACTUACIONES[x]["label"],
                    key=f"emp_act_{idx}",
                    label_visibility="collapsed",
                )
            st.markdown("---")

        submitted = st.form_submit_button("✅ Enviar Auto-Evaluación", use_container_width=True, type="primary")

        if submitted:
            partial_results = {
                "employee_self": {
                    "actuaciones_scores": {str(k): v for k, v in actuaciones_scores.items()},
                }
            }
            db.save_results(session_id, partial_results)
            db.set_employee_done_status(session_id)

            for key in ["test_session"]:
                st.session_state.pop(key, None)

            nav("candidate_done")
            st.rerun()


# -------------------------------------------------------------------------
# JEFE: EVALUACIÓN DESEMPEÑO LÍDERES (con referencia auto-eval empleado)
# -------------------------------------------------------------------------
def page_desempeno_lider_jefe_eval():
    """Evaluación del jefe para Desempeño Líderes — muestra auto-evaluación del empleado como referencia."""
    session_id = st.session_state.get("evaluador_session_id") or st.session_state.get("desempeno_lider_session_id")
    evaluador = st.session_state.get("evaluador")
    admin = st.session_state.get("admin")

    if not session_id:
        st.error("No se encontró una sesión de evaluación activa.")
        return

    session = db.get_session_by_id(session_id)
    if not session:
        st.error("Sesión no válida.")
        return

    candidate = db.get_candidate_by_cedula(
        db.get_connection().execute("SELECT cedula FROM candidates WHERE id = ?", (session["candidate_id"],)).fetchone()["cedula"]
    )
    evaluador_nombre = (evaluador.get("name") if evaluador else None) or (admin.get("name") if admin else "Evaluador")
    nivel_cargo = candidate.get("nivel_cargo", "ANALISTA") or "ANALISTA"

    # Cargar auto-evaluación del empleado
    existing_results = db.get_results(session_id) or {}
    employee_self = existing_results.get("employee_self", {})
    emp_comp_scores = {int(k): v for k, v in employee_self.get("competencias_scores", {}).items()}

    # Botón de regreso
    if evaluador:
        if st.button("⬅️ Volver al Dashboard del Evaluador"):
            st.session_state.pop("evaluador_session_id", None)
            nav("evaluador_dashboard")
            st.rerun()
    elif admin:
        if st.button("⬅️ Volver al Dashboard Admin"):
            st.session_state.pop("desempeno_lider_session_id", None)
            nav("admin_dashboard")
            st.rerun()

    st.markdown("## 📊 Evaluación de Desempeño — Líderes (Evaluación del Jefe)")
    st.markdown(f"**Colaborador:** {candidate['name']} (Cédula: {candidate['cedula']})")
    st.markdown(f"**Cargo:** {candidate.get('position', 'N/A')} | **Nivel:** {nivel_cargo}")
    st.markdown(f"**Evaluador:** {evaluador_nombre}")

    if emp_comp_scores:
        with st.expander("📋 Ver Auto-Evaluación del Empleado (Referencia)", expanded=False):
            st.markdown("**El empleado se evaluó así en cada competencia:**")
            cols_ref = st.columns(2)
            for i, comp in enumerate(COMPETENCIAS_ORGANIZACIONALES):
                cid = comp["id"]
                emp_score = emp_comp_scores.get(cid, 0)
                with cols_ref[i % 2]:
                    if emp_score:
                        st.markdown(f"- **{comp['nombre']}**: Nivel {emp_score}")
    st.markdown("---")

    with st.form("evaluacion_desempeno_lider_jefe_form"):
        # ---- SECCIÓN 1: COMPETENCIAS (evaluación del jefe) ----
        st.markdown("### 🏆 SECCIÓN 1: Evaluación de Competencias (Tu evaluación como jefe)")
        st.markdown("Selecciona el nivel alcanzado por el colaborador según tu observación:")

        nivel_req_info = COMPETENCIAS_NIVEL_REQUERIDO.get(nivel_cargo.upper(), None)
        competencias_scores = {}

        for comp in COMPETENCIAS_ORGANIZACIONALES:
            req = nivel_req_info["niveles"][comp["id"] - 1] if nivel_req_info else None
            req_text = f" _(Requerido: Nivel {req})_" if req else ""
            emp_score = emp_comp_scores.get(comp["id"])
            emp_ref = f" | _Auto-eval empleado: Nivel {emp_score}_" if emp_score else ""
            st.markdown(f"**{comp['nombre']}**{req_text}{emp_ref}")
            st.caption(comp["descripcion"])
            nivel_sel = st.radio(
                f"Nivel {comp['nombre']}",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x, c=comp: f"Nivel {x} — {c['niveles'][x][:80]}...",
                horizontal=True,
                key=f"jefe_comp_{comp['id']}",
                label_visibility="collapsed",
                index=2,
            )
            competencias_scores[comp["id"]] = nivel_sel
            st.markdown("---")

        # ---- SECCIÓN 2: RENDIMIENTO ----
        st.markdown("### 📝 SECCIÓN 2: Evaluación de Rendimiento")
        st.markdown("**5** = Sobresaliente | **4** = Supera | **3** = Cumple | **2** = Debajo | **1** = Insatisfactorio")

        rendimiento_scores = {}
        for obj in DESEMPENO_OBJETIVOS:
            st.markdown(f"**{obj['titulo']}**")
            st.caption(obj["descripcion"])
            rendimiento_scores[obj["id"]] = st.select_slider(
                f"Calificación Objetivo {obj['id']}",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: DESEMPENO_ESCALA_RENDIMIENTO[x]["label"],
                key=f"jefe_rend_{obj['id']}",
                label_visibility="collapsed",
            )
            st.markdown("---")

        # ---- SECCIÓN 3: POTENCIAL ----
        st.markdown("### 🎯 SECCIÓN 3: Evaluación de Potencial (0-3)")
        potencial_scores = {}
        for dim in DESEMPENO_DIMENSIONES:
            st.markdown(f"**{dim['nombre']}**")
            st.caption(dim["descripcion"])
            nivel_sel = st.radio(
                f"Nivel {dim['nombre']}",
                options=[3, 2, 1, 0],
                format_func=lambda x, d=dim: f"Nivel {x}: {d['niveles'][x][:80]}...",
                key=f"jefe_pot_{dim['id']}",
                label_visibility="collapsed",
            )
            potencial_scores[dim["id"]] = nivel_sel
            st.markdown("---")

        # ---- INICIATIVAS ----
        st.markdown("### 🚀 Iniciativas de Mejora")
        n_iniciativas = st.selectbox("Número de iniciativas", [0, 1, 2, 3], index=1, key="n_init_jefe_lider")
        iniciativas = []
        for i in range(n_iniciativas):
            ini = st.text_area(f"Iniciativa {i+1}", key=f"ini_jefe_lider_{i}", height=80)
            if ini.strip():
                iniciativas.append(ini.strip())

        submitted = st.form_submit_button("✅ Guardar Evaluación Completa", use_container_width=True, type="primary")

        if submitted:
            results_calc = calculate_desempeno_lider_results(
                competencias_scores=competencias_scores,
                rendimiento_scores=rendimiento_scores,
                potencial_scores=potencial_scores,
                nivel_cargo=nivel_cargo,
                iniciativas=iniciativas,
            )
            results_to_save = {
                "test_type": "desempeno_lider",
                "evaluador": evaluador_nombre,
                "nivel_cargo": nivel_cargo,
                "competencias_scores": {str(k): v for k, v in competencias_scores.items()},
                "rendimiento_scores": {str(k): v for k, v in rendimiento_scores.items()},
                "potencial_scores": {str(k): v for k, v in potencial_scores.items()},
                "iniciativas": iniciativas,
                "analysis": results_calc,
                "employee_self": employee_self,
            }
            db.save_results(session_id, results_to_save)
            db.complete_test_session(session_id)
            st.success("✅ Evaluación de desempeño (líderes) guardada exitosamente.")
            st.balloons()
            st.session_state.pop("evaluador_session_id", None)
            st.session_state.pop("desempeno_lider_session_id", None)
            if evaluador:
                nav("evaluador_dashboard")
            else:
                nav("admin_dashboard")
            st.rerun()


# -------------------------------------------------------------------------
# JEFE: EVALUACIÓN PERÍODO DE PRUEBA (con referencia auto-eval empleado)
# -------------------------------------------------------------------------
def page_periodo_prueba_jefe_eval():
    """Evaluación del jefe para Período de Prueba — muestra auto-evaluación del empleado como referencia."""
    session_id = st.session_state.get("evaluador_session_id") or st.session_state.get("periodo_prueba_session_id")
    evaluador = st.session_state.get("evaluador")
    admin = st.session_state.get("admin")

    if not session_id:
        st.error("No se encontró una sesión de evaluación activa.")
        return

    session = db.get_session_by_id(session_id)
    if not session:
        st.error("Sesión no válida.")
        return

    candidate = db.get_candidate_by_cedula(
        db.get_connection().execute("SELECT cedula FROM candidates WHERE id = ?", (session["candidate_id"],)).fetchone()["cedula"]
    )
    evaluador_nombre = (evaluador.get("name") if evaluador else None) or (admin.get("name") if admin else "Evaluador")

    # Cargar auto-evaluación del empleado
    existing_results = db.get_results(session_id) or {}
    employee_self = existing_results.get("employee_self", {})
    emp_act_scores = {int(k): v for k, v in employee_self.get("actuaciones_scores", {}).items()}

    # Botón de regreso
    if evaluador:
        if st.button("⬅️ Volver al Dashboard del Evaluador"):
            st.session_state.pop("evaluador_session_id", None)
            nav("evaluador_dashboard")
            st.rerun()
    elif admin:
        if st.button("⬅️ Volver al Dashboard Admin"):
            st.session_state.pop("periodo_prueba_session_id", None)
            nav("admin_dashboard")
            st.rerun()

    st.markdown("## 📋 Evaluación Período de Prueba (Evaluación del Jefe)")
    st.markdown(f"**Trabajador:** {candidate['name']} (Cédula: {candidate['cedula']})")
    st.markdown(f"**Cargo:** {candidate.get('position', 'N/A')} | **Área:** {candidate.get('regional', 'N/A')}")
    st.markdown(f"**Evaluador:** {evaluador_nombre}")
    st.info("Marque la frecuencia con la que observa cada comportamiento durante el desempeño laboral.")

    if emp_act_scores:
        with st.expander("📋 Ver Auto-Evaluación del Empleado (Referencia)", expanded=False):
            st.markdown("**El empleado se evaluó así:**")
            for idx, actuacion in enumerate(PERIODO_PRUEBA_ACTUACIONES):
                emp_score = emp_act_scores.get(idx)
                if emp_score:
                    escala = PERIODO_PRUEBA_ESCALA_ACTUACIONES.get(emp_score, {})
                    st.markdown(f"- **{idx+1}. {actuacion[:60]}...**: {escala.get('label', emp_score)}")
    st.markdown("---")

    with st.form("jefe_periodo_prueba_form"):
        st.markdown("### 📝 Sección 1: Actuaciones y Comportamientos (Tu evaluación como jefe)")
        st.markdown("**Siempre=4 | Casi Siempre=3 | Algunas Veces=2 | Nunca=1**")

        actuaciones_scores = {}
        for idx, actuacion in enumerate(PERIODO_PRUEBA_ACTUACIONES):
            emp_score = emp_act_scores.get(idx)
            emp_ref = f" *(Auto-eval: {PERIODO_PRUEBA_ESCALA_ACTUACIONES.get(emp_score, {}).get('label', emp_score)})*" if emp_score else ""
            col_act, col_score = st.columns([4, 1])
            with col_act:
                st.markdown(f"**{idx + 1}.** {actuacion}{emp_ref}")
            with col_score:
                actuaciones_scores[idx] = st.selectbox(
                    f"Actuación {idx+1}",
                    options=[4, 3, 2, 1],
                    format_func=lambda x: PERIODO_PRUEBA_ESCALA_ACTUACIONES[x]["label"],
                    key=f"jefe_act_{idx}",
                    label_visibility="collapsed",
                )
            st.markdown("---")

        st.markdown("### ⭐ Sección 2: Calificaciones Específicas")
        st.markdown("**Excelente=5 | Bueno=4 | Regular=3 | Deficiente=2 | Insuficiente=1**")

        calificaciones_scores = {}
        for idx, calificacion in enumerate(PERIODO_PRUEBA_CALIFICACIONES):
            col_cal, col_cscore = st.columns([4, 1])
            with col_cal:
                st.markdown(f"**{calificacion}**")
            with col_cscore:
                calificaciones_scores[idx] = st.selectbox(
                    f"Cal {idx+1}",
                    options=[5, 4, 3, 2, 1],
                    format_func=lambda x: PERIODO_PRUEBA_ESCALA_CALIFICACIONES[x]["label"],
                    key=f"jefe_cal_{idx}",
                    label_visibility="collapsed",
                )
            st.markdown("---")

        st.markdown("### 📌 Sección 3: Información Adicional")
        col_lam, col_con = st.columns(2)
        with col_lam:
            llamados = st.radio("¿Tuvo llamados de atención?", options=[False, True],
                                format_func=lambda x: "SÍ" if x else "NO",
                                key="jefe_llamados", horizontal=True)
        with col_con:
            conocimiento = st.radio("¿Su conocimiento se adecua al perfil del cargo?",
                                    options=[True, False],
                                    format_func=lambda x: "SÍ" if x else "NO",
                                    key="jefe_conocimiento", horizontal=True)

        observaciones = st.text_area("Observaciones adicionales", height=120, key="jefe_obs_pp",
                                     placeholder="Comentarios generales sobre el desempeño durante el período...")

        aprobo = st.radio("¿El evaluado aprobó el período de prueba?",
                          options=[True, False],
                          format_func=lambda x: "✅ SÍ, APROBÓ" if x else "❌ NO APROBÓ",
                          key="jefe_aprobo_pp", horizontal=True)

        submitted = st.form_submit_button("✅ Guardar Evaluación Completa", use_container_width=True, type="primary")

        if submitted:
            results_calc = calculate_periodo_prueba_results(
                actuaciones_scores=actuaciones_scores,
                calificaciones_scores=calificaciones_scores,
                aprobo=aprobo,
                llamados_atencion=llamados,
                conocimiento_adecuado=conocimiento,
                observaciones=observaciones,
            )
            results_to_save = {
                "test_type": "periodo_prueba",
                "evaluador": evaluador_nombre,
                "actuaciones_scores": {str(k): v for k, v in actuaciones_scores.items()},
                "calificaciones_scores": {str(k): v for k, v in calificaciones_scores.items()},
                "aprobo": aprobo,
                "llamados_atencion": llamados,
                "conocimiento_adecuado": conocimiento,
                "observaciones": observaciones,
                "analysis": results_calc,
                "employee_self": employee_self,
            }
            db.save_results(session_id, results_to_save)
            db.complete_test_session(session_id)
            st.success("✅ Evaluación de período de prueba guardada correctamente.")
            st.balloons()
            st.session_state.pop("evaluador_session_id", None)
            st.session_state.pop("periodo_prueba_session_id", None)
            if evaluador:
                nav("evaluador_dashboard")
            else:
                nav("admin_dashboard")
            st.rerun()


# -------------------------------------------------------------------------
# CANDIDATE: LOGIN
# -------------------------------------------------------------------------

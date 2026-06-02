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
from utils import load_disc_questions, load_disc_descriptions, load_wpi_questions, nav, render_timer
from auth import (
    _restore_admin_session, _touch_admin_session,
    _logout_admin, _start_admin_session,
)

def page_candidate_login():
    st.markdown("## 🔑 Acceso Candidato")
    if st.button("⬅️ Volver al inicio"):
        nav("home")
        st.rerun()

    st.markdown("Ingresa tu número de cédula para acceder a las evaluaciones asignadas.")

    with st.form("candidate_login_form"):
        cedula = st.text_input("Número de Cédula", placeholder="Ingresa tu cédula")
        submitted = st.form_submit_button("Ingresar")

        if submitted:
            if not cedula.strip():
                st.error("Por favor ingresa tu cédula.")
            else:
                candidate = db.get_candidate_by_cedula(cedula)
                if not candidate:
                    st.error("❌ No se encontró un candidato con esa cédula. Contacta a Recursos Humanos.")
                else:
                    pending = db.get_pending_sessions_for_candidate(candidate["id"])
                    if not pending:
                        st.warning("⚠️ No tienes evaluaciones pendientes asignadas. Contacta a Recursos Humanos.")
                    else:
                        st.session_state.candidate = candidate
                        st.session_state.pending_sessions = pending
                        nav("candidate_select_test")
                        st.rerun()


# -------------------------------------------------------------------------
# CANDIDATE: SELECT TEST
# -------------------------------------------------------------------------
def page_candidate_select_test():
    candidate = st.session_state.get("candidate")
    if not candidate:
        nav("candidate_login")
        st.rerun()
        return

    pending_all = db.get_pending_sessions_for_candidate(candidate["id"])
    # Estas evaluaciones existen, pero no son respondidas por el candidato.
    _ADMIN_ONLY_TEST_TYPES = {"desempeno"}
    pending = [s for s in pending_all if s["test_type"] not in _ADMIN_ONLY_TEST_TYPES]
    pending_info_only = [s for s in pending_all if s["test_type"] in _ADMIN_ONLY_TEST_TYPES]
    st.session_state.pending_sessions = pending

    st.markdown(f"## Bienvenido/a, {candidate['name']}")
    st.markdown("Tienes las siguientes evaluaciones asignadas:")

    if not pending and not pending_info_only:
        st.info("✅ No tienes evaluaciones pendientes. ¡Gracias!")
        if st.button("🔑 Cerrar Sesión"):
            for key in ["candidate", "pending_sessions", "test_session", "disc_questions", "disc_page", "disc_answers", "valanti_responses", "valanti_page"]:
                st.session_state.pop(key, None)
            nav("home")
            st.rerun()
        return

    if pending_info_only and not pending:
        st.info("ℹ️ Tienes evaluaciones pendientes asignadas, pero no requieren acción de tu parte por ahora.")

    for sess in pending:
        # Determinar emoji y nombre según tipo de test
        if sess["test_type"] == "disc":
            test_emoji = "🎯"
            test_name = "Evaluación DISC"
        elif sess["test_type"] == "valanti":
            test_emoji = "🧭"
            test_name = "Cuestionario VALANTI"
        elif sess["test_type"] == "wpi":
            test_emoji = "💼"
            test_name = "WPI - Work Personality Index"
        elif sess["test_type"] == "eri":
            test_emoji = "🔐"
            test_name = "ERI - Evaluación de Riesgo e Integridad"
        elif sess["test_type"] == "talent_map":
            test_emoji = "🌟"
            test_name = "Talent Map - Mapeo de Competencias"
        elif sess["test_type"] == "desempeno_lider":
            test_emoji = "📊"
            test_name = "Auto-Evaluación de Competencias (Desempeño Líderes)"
        elif sess["test_type"] == "desempeno_medios":
            test_emoji = "📊"
            test_name = "Auto-Evaluación de Competencias (Desempeño Medios)"
        elif sess["test_type"] == "periodo_prueba":
            test_emoji = "📋"
            test_name = "Auto-Evaluación Período de Prueba"
        else:
            test_emoji = "📝"
            test_name = "Evaluación"
        
        status_text = "En progreso ▶️" if sess["status"] == "in_progress" else "Pendiente ⏳"

        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"### {test_emoji} {test_name}")
                st.caption(f"ID: {sess['id']} | Tiempo: {sess['time_limit_minutes']} min | Estado: {status_text}")
                if sess.get("evaluador_nombre") or sess.get("evaluador_cedula"):
                    jefe_info = sess.get("evaluador_nombre") or "N/A"
                    jefe_ced = sess.get("evaluador_cedula") or "N/A"
                    st.caption(f"👔 Jefe asignado: {jefe_info} (CC: {jefe_ced})")
            with c2:
                st.metric("Tiempo", f"{sess['time_limit_minutes']} min")
            with c3:
                button_text = "▶️ Continuar" if sess["status"] == "in_progress" else "🚀 Iniciar"
                if st.button(button_text, key=f"start_{sess['id']}", use_container_width=True):
                    if sess["status"] == "in_progress":
                        remaining = db.check_session_time(sess)
                        if remaining == -1:
                            st.error("⏰ El tiempo de esta evaluación ha expirado.")
                            st.rerun()
                            return

                    if sess["status"] == "pending":
                        db.start_test_session(sess["id"])
                    st.session_state.test_session = db.get_session_by_id(sess["id"])

                    if sess["test_type"] == "disc":
                        nav("disc_test")
                    elif sess["test_type"] == "valanti":
                        nav("valanti_test")
                    elif sess["test_type"] == "wpi":
                        nav("wpi_test")
                    elif sess["test_type"] == "eri":
                        nav("eri_test")
                    elif sess["test_type"] == "talent_map":
                        nav("talent_map_test")
                    elif sess["test_type"] == "desempeno_lider":
                        nav("desempeno_lider_employee_eval")
                    elif sess["test_type"] == "desempeno_medios":
                        nav("desempeno_medios_employee_eval")
                    elif sess["test_type"] == "periodo_prueba":
                        nav("periodo_prueba_employee_eval")
                    st.rerun()

    if pending_info_only:
        st.markdown("---")
        st.markdown("### 📌 Pendientes informativas")
        st.caption("Estas evaluaciones están pendientes en el sistema, pero son gestionadas por Evaluador/RH.")
        for sess in pending_info_only:
            with st.container():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown("### 📊 Evaluación de Desempeño (Gestionada por evaluador)")
                    st.caption(f"ID: {sess['id']} | Tiempo: {sess['time_limit_minutes']} min | Estado: Pendiente ⏳")
                    if sess.get("evaluador_nombre") or sess.get("evaluador_cedula"):
                        jefe_info = sess.get("evaluador_nombre") or "N/A"
                        jefe_ced = sess.get("evaluador_cedula") or "N/A"
                        st.caption(f"👔 Jefe asignado: {jefe_info} (CC: {jefe_ced})")
                with c2:
                    st.metric("Acción", "N/A")

    st.markdown("---")
    if st.button("🔑 Cerrar Sesión"):
        for key in ["candidate", "pending_sessions", "test_session", 
                    "disc_questions", "disc_page", "disc_answers", 
                    "valanti_responses", "valanti_page",
                    "wpi_questions", "wpi_responses", "wpi_page",
                    "eri_questions", "eri_responses", "eri_page",
                    "tm_questions", "tm_responses", "tm_page",
                    "desempeno_session_id"]:
            st.session_state.pop(key, None)
        nav("home")
        st.rerun()


# -------------------------------------------------------------------------
# CANDIDATE: DISC TEST
# -------------------------------------------------------------------------
def page_disc_test():
    session = st.session_state.get("test_session")
    candidate = st.session_state.get("candidate")
    if not session or not candidate:
        nav("candidate_login")
        st.rerun()
        return

    session = db.get_session_by_id(session["id"])
    if not session or session["status"] not in ("in_progress",):
        if session and session["status"] == "expired":
            st.error("⏰ El tiempo de esta evaluación ha expirado.")
            if st.button("Volver"):
                nav("candidate_select_test")
                st.rerun()
            return
        nav("candidate_select_test")
        st.rerun()
        return

    remaining = db.check_session_time(session)
    if remaining == -1:
        st.error("⏰ El tiempo de esta evaluación ha expirado.")
        if st.button("Volver"):
            nav("candidate_select_test")
            st.rerun()
        return

    deadline_ts = db.get_session_deadline_timestamp(session)
    if deadline_ts:
        render_timer(deadline_ts, session["id"])

    st.markdown(f"### 🎯 Evaluación DISC")
    st.caption(f"Candidato: {candidate['name']} | ID: {session['id']}")

    if "disc_questions" not in st.session_state:
        all_questions = load_disc_questions()
        rng = random.Random(session["id"])
        rng.shuffle(all_questions)
        st.session_state.disc_questions = all_questions[:30]
        db.update_session_questions(session["id"], st.session_state.disc_questions)

    if "disc_page" not in st.session_state:
        st.session_state.disc_page = 0

    if "disc_answers" not in st.session_state:
        st.session_state.disc_answers = {}

    questions = st.session_state.disc_questions
    total = len(questions)
    page = st.session_state.disc_page

    progress = page / total
    st.progress(progress)
    st.markdown(f"**Pregunta {page + 1} de {total}**")

    options_map = {
        "Selecciona una opción": None,
        "1 - Totalmente en desacuerdo": 1,
        "2 - Algo en desacuerdo": 2,
        "3 - Neutral": 3,
        "4 - Algo de acuerdo": 4,
        "5 - Totalmente de acuerdo": 5,
    }

    if page < total:
        q = questions[page]
        with st.form(key=f"disc_form_{page}"):
            st.markdown(f"#### {page + 1}) {q['question']}")
            selected = st.radio("Tu respuesta:", list(options_map.keys()), index=0, horizontal=True, key=f"disc_radio_{page}")

            col_prev, col_space, col_next = st.columns([1, 4, 1])
            with col_prev:
                if page > 0:
                    if st.form_submit_button("⬅️ Anterior"):
                        st.session_state.disc_page -= 1
                        st.rerun()
            with col_next:
                if page < total - 1:
                    btn = st.form_submit_button("Siguiente ➡️")
                else:
                    btn = st.form_submit_button("✅ Finalizar")

        if btn:
            remaining = db.check_session_time(db.get_session_by_id(session["id"]))
            if remaining == -1:
                st.error("⏰ El tiempo ha expirado.")
                return

            if options_map[selected] is None:
                st.warning("⚠️ Por favor selecciona una respuesta.")
            else:
                st.session_state.disc_answers[page] = options_map[selected]
                if page < total - 1:
                    st.session_state.disc_page += 1
                    st.rerun()
                else:
                    answers_list = [st.session_state.disc_answers[i] for i in range(total)]
                    raw, normalized, relative = calculate_disc_results(answers_list, questions)

                    answer_records = []
                    for i in range(total):
                        answer_records.append({
                            "question_index": i,
                            "question_text": questions[i]["question"],
                            "answer_value": answers_list[i],
                        })
                    db.save_answers(session["id"], answer_records)

                    results = {"raw": raw, "normalized": normalized, "relative": relative}
                    db.save_results(session["id"], results)
                    db.complete_test_session(session["id"])

                    for key in ["disc_questions", "disc_page", "disc_answers", "test_session"]:
                        st.session_state.pop(key, None)

                    nav("candidate_done")
                    st.rerun()


# -------------------------------------------------------------------------
# CANDIDATE: VALANTI TEST
# -------------------------------------------------------------------------
def page_valanti_test():
    session = st.session_state.get("test_session")
    candidate = st.session_state.get("candidate")
    if not session or not candidate:
        nav("candidate_login")
        st.rerun()
        return

    session = db.get_session_by_id(session["id"])
    if not session or session["status"] not in ("in_progress",):
        if session and session["status"] == "expired":
            st.error("⏰ El tiempo de esta evaluación ha expirado.")
            if st.button("Volver"):
                nav("candidate_select_test")
                st.rerun()
            return
        nav("candidate_select_test")
        st.rerun()
        return

    remaining = db.check_session_time(session)
    if remaining == -1:
        st.error("⏰ El tiempo de esta evaluación ha expirado.")
        if st.button("Volver"):
            nav("candidate_select_test")
            st.rerun()
        return

    deadline_ts = db.get_session_deadline_timestamp(session)
    if deadline_ts:
        render_timer(deadline_ts, session["id"])

    st.markdown(f"### 🧭 Cuestionario VALANTI")
    st.caption(f"Candidato: {candidate['name']} | ID: {session['id']}")

    if "valanti_responses" not in st.session_state:
        st.session_state.valanti_responses = [None] * len(VALANTI_PREGUNTAS)

    if "valanti_page" not in st.session_state:
        st.session_state.valanti_page = 0

    total = len(VALANTI_PREGUNTAS)
    questions_per_page = 5
    page = st.session_state.valanti_page
    q_start = page * questions_per_page
    q_end = min(q_start + questions_per_page, total)

    progress = q_end / total
    st.progress(progress)
    st.markdown(f"**Preguntas {q_start + 1} - {q_end} de {total}**")

    if q_start < 9:
        st.info("**Primera Parte:** Distribuye 3 puntos entre las dos frases. El puntaje más alto para la frase más importante para ti.")
    else:
        st.warning("**Segunda Parte:** Distribuye 3 puntos entre las dos frases. El puntaje más alto para lo que consideres **peor**.")

    # Callbacks de auto-completado
    def make_cb_a(idx):
        def _cb():
            val = st.session_state.get(f"vq_{idx}_a", "--")
            if val != "--":
                st.session_state[f"vq_{idx}_b"] = 3 - int(val)
        return _cb

    def make_cb_b(idx):
        def _cb():
            val = st.session_state.get(f"vq_{idx}_b", "--")
            if val != "--":
                st.session_state[f"vq_{idx}_a"] = 3 - int(val)
        return _cb

    all_answered = True

    for i in range(q_start, q_end):
        par = VALANTI_PREGUNTAS[i]
        a_key = f"vq_{i}_a"
        b_key = f"vq_{i}_b"

        # Inicializar desde respuestas guardadas
        if a_key not in st.session_state:
            if st.session_state.valanti_responses[i] is not None:
                st.session_state[a_key] = st.session_state.valanti_responses[i]
                st.session_state[b_key] = 3 - st.session_state.valanti_responses[i]

        # Tarjeta visual
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        border-radius: 12px; padding: 20px; margin: 15px 0;
                        border-left: 4px solid #3b82f6;">
                <div style="margin-bottom: 8px;">
                    <span style="background: #3b82f6; color: white; padding: 4px 12px;
                                border-radius: 20px; font-size: 0.85em; font-weight: bold;">
                        Pregunta {i + 1}
                    </span>
                </div>
                <div style="display: flex; gap: 20px; margin-top: 10px;">
                    <div style="flex: 1; background: rgba(59,130,246,0.1); border-radius: 8px; padding: 12px;">
                        <span style="color: #60a5fa; font-weight: bold; font-size: 1.1em;">A)</span>
                        <span style="color: #e2e8f0; font-size: 1.05em;"> {par[0]}</span>
                    </div>
                    <div style="flex: 1; background: rgba(245,158,11,0.1); border-radius: 8px; padding: 12px;">
                        <span style="color: #fbbf24; font-weight: bold; font-size: 1.1em;">B)</span>
                        <span style="color: #e2e8f0; font-size: 1.05em;"> {par[1]}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_sa, col_sb, col_icon = st.columns([3, 3, 1])
        with col_sa:
            st.selectbox(
                f"Puntos para A (P{i+1})",
                options=["--", 0, 1, 2, 3],
                key=a_key,
                on_change=make_cb_a(i),
            )
        with col_sb:
            st.selectbox(
                f"Puntos para B (P{i+1})",
                options=["--", 0, 1, 2, 3],
                key=b_key,
                on_change=make_cb_b(i),
            )

        a_val = st.session_state.get(a_key, "--")
        b_val = st.session_state.get(b_key, "--")

        with col_icon:
            st.markdown("<br>", unsafe_allow_html=True)
            if a_val != "--" and b_val != "--" and int(a_val) + int(b_val) == 3:
                st.success("✅")
            else:
                st.warning("⚠️")
                all_answered = False

    # Navegación
    st.markdown("---")
    col_prev, col_space, col_next = st.columns([1, 4, 1])

    with col_prev:
        if page > 0:
            if st.button("⬅️ Anterior", key="valanti_prev"):
                for j in range(q_start, q_end):
                    a = st.session_state.get(f"vq_{j}_a", "--")
                    if a != "--":
                        st.session_state.valanti_responses[j] = int(a)
                st.session_state.valanti_page -= 1
                st.rerun()

    with col_next:
        is_last = q_end >= total
        btn_label = "✅ Finalizar Evaluación" if is_last else "Siguiente ➡️"
        if st.button(btn_label, key="valanti_next", disabled=not all_answered):
            remaining = db.check_session_time(db.get_session_by_id(session["id"]))
            if remaining == -1:
                st.error("⏰ El tiempo ha expirado.")
            else:
                for j in range(q_start, q_end):
                    a = st.session_state.get(f"vq_{j}_a", "--")
                    if a != "--":
                        st.session_state.valanti_responses[j] = int(a)

                if is_last:
                    if None in st.session_state.valanti_responses:
                        st.warning("⚠️ Hay preguntas sin responder. Revisa las páginas anteriores.")
                    else:
                        responses = st.session_state.valanti_responses
                        direct, standard = calculate_valanti_results(responses)

                        answer_records = []
                        for i in range(total):
                            answer_records.append({
                                "question_index": i,
                                "question_text": f"A: {VALANTI_PREGUNTAS[i][0]} / B: {VALANTI_PREGUNTAS[i][1]}",
                                "answer_value": responses[i],
                                "answer_b_value": 3 - responses[i],
                            })
                        db.save_answers(session["id"], answer_records)

                        results = {"direct": direct, "standard": standard}
                        db.save_results(session["id"], results)
                        db.complete_test_session(session["id"])

                        for key in ["valanti_responses", "valanti_page", "test_session"]:
                            st.session_state.pop(key, None)

                        nav("candidate_done")
                        st.rerun()
                else:
                    st.session_state.valanti_page += 1
                    st.rerun()


def page_wpi_test():
    """
    Página del test WPI (Work Personality Index) - 50 preguntas con escala Likert 1-5.
    """
    session = st.session_state.get("test_session")
    candidate = st.session_state.get("candidate")
    
    if not session or not candidate:
        nav("candidate_login")
        st.rerun()
        return

    session = db.get_session_by_id(session["id"])
    if not session or session["status"] not in ("in_progress",):
        if session and session["status"] == "expired":
            st.error("⏰ El tiempo de esta evaluación ha expirado.")
            if st.button("Volver"):
                nav("candidate_select_test")
                st.rerun()
            return
        nav("candidate_select_test")
        st.rerun()
        return

    # Verificar tiempo restante
    remaining = db.check_session_time(session)
    if remaining == -1:
        st.error("⏰ El tiempo de esta evaluación ha expirado.")
        if st.button("Volver"):
            nav("candidate_select_test")
            st.rerun()
        return

    # Mostrar timer
    deadline_ts = db.get_session_deadline_timestamp(session)
    if deadline_ts:
        render_timer(deadline_ts, session["id"])

    st.markdown(f"### 💼 WPI - Work Personality Index")
    st.caption(f"Candidato: {candidate['name']} | ID: {session['id']}")
    
    # Cargar preguntas si no están en session_state
    if "wpi_questions" not in st.session_state:
        all_questions = load_wpi_questions()
        # Mezclar preguntas de manera consistente por sesión
        rng = random.Random(session["id"])
        rng.shuffle(all_questions)
        st.session_state.wpi_questions = all_questions
        db.update_session_questions(session["id"], all_questions)

    # Inicializar respuestas
    if "wpi_responses" not in st.session_state:
        st.session_state.wpi_responses = [None] * len(st.session_state.wpi_questions)

    # Inicializar página
    if "wpi_page" not in st.session_state:
        st.session_state.wpi_page = 0

    questions = st.session_state.wpi_questions
    total = len(questions)
    questions_per_page = 10  # 10 preguntas por página
    page = st.session_state.wpi_page
    q_start = page * questions_per_page
    q_end = min(q_start + questions_per_page, total)

    # Barra de progreso
    progress = q_end / total
    st.progress(progress)
    st.markdown(f"**Preguntas {q_start + 1} - {q_end} de {total}**")

    # Instrucciones
    st.info("""
    **Instrucciones:** Responde con sinceridad a cada afirmación según la siguiente escala:
    - **1** = Totalmente en desacuerdo
    - **2** = En desacuerdo
    - **3** = Neutral
    - **4** = De acuerdo
    - **5** = Totalmente de acuerdo
    """)

    # Mostrar preguntas de la página actual
    all_answered = True
    
    for i in range(q_start, q_end):
        q = questions[i]
        q_text = q["question"]
        dim = q["dimension"]
        
        # Crear tarjeta visual para cada pregunta
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        border-radius: 12px; padding: 20px; margin: 15px 0;
                        border-left: 4px solid {WPI_COLORS.get(dim, '#3b82f6')};">
                <div style="margin-bottom: 8px;">
                    <span style="background: {WPI_COLORS.get(dim, '#3b82f6')}; color: white; 
                                padding: 4px 12px; border-radius: 20px; 
                                font-size: 0.85em; font-weight: bold;">
                        Pregunta {i + 1} - {dim}
                    </span>
                </div>
                <p style="color: #e2e8f0; font-size: 1.1em; margin: 12px 0;">
                    {q_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Radio buttons para la respuesta
        response_key = f"wpi_q_{i}"
        
        # Inicializar desde respuestas guardadas
        if response_key not in st.session_state and st.session_state.wpi_responses[i] is not None:
            st.session_state[response_key] = st.session_state.wpi_responses[i]
        
        col1, col2 = st.columns([4, 1])
        with col1:
            response = st.radio(
                f"Respuesta {i + 1}",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "1 - Totalmente en desacuerdo",
                    2: "2 - En desacuerdo",
                    3: "3 - Neutral",
                    4: "4 - De acuerdo",
                    5: "5 - Totalmente de acuerdo"
                }[x],
                key=response_key,
                horizontal=False,
                index=None if response_key not in st.session_state or st.session_state[response_key] is None else st.session_state[response_key] - 1
            )
        
        with col2:
            st.markdown("<br>" * 2, unsafe_allow_html=True)
            if response is not None:
                st.success("✅")
                st.session_state.wpi_responses[i] = response
            else:
                st.warning("⚠️")
                all_answered = False

    # Navegación
    st.markdown("---")
    col_prev, col_space, col_next = st.columns([1, 4, 1])

    with col_prev:
        if page > 0:
            if st.button("⬅️ Anterior", key="wpi_prev"):
                st.session_state.wpi_page -= 1
                st.rerun()

    with col_next:
        is_last = q_end >= total
        btn_label = "✅ Finalizar Evaluación" if is_last else "Siguiente ➡️"
        if st.button(btn_label, key="wpi_next", disabled=not all_answered):
            # Verificar tiempo nuevamente
            remaining = db.check_session_time(db.get_session_by_id(session["id"]))
            if remaining == -1:
                st.error("⏰ El tiempo ha expirado.")
                return

            if is_last:
                # Verificar que todas las preguntas estén respondidas
                if None in st.session_state.wpi_responses:
                    st.warning("⚠️ Hay preguntas sin responder. Revisa las páginas anteriores.")
                else:
                    # Calcular resultados
                    responses = st.session_state.wpi_responses
                    raw, normalized, percentages = calculate_wpi_results(responses, questions)

                    # Guardar respuestas
                    answer_records = []
                    for i in range(total):
                        answer_records.append({
                            "question_index": i,
                            "question_text": questions[i]["question"],
                            "answer_value": responses[i],
                            "answer_b_value": None,  # No aplica para WPI
                        })
                    db.save_answers(session["id"], answer_records)

                    # Guardar resultados
                    results = {
                        "raw": raw,
                        "normalized": normalized,
                        "percentages": percentages
                    }
                    db.save_results(session["id"], results)
                    db.complete_test_session(session["id"])

                    # Limpiar session state
                    for key in ["wpi_questions", "wpi_responses", "wpi_page", "eri_questions", "eri_responses", "eri_page", "test_session"]:
                        st.session_state.pop(key, None)

                    nav("candidate_done")
                    st.rerun()
            else:
                st.session_state.wpi_page += 1
                st.rerun()


def page_eri_test():
    """
    Página del test ERI (Evaluación de Riesgo e Integridad) - 60 preguntas con escala Likert 1-5.
    """
    session = st.session_state.get("test_session")
    candidate = st.session_state.get("candidate")
    
    if not session or not candidate:
        nav("candidate_login")
        st.rerun()
        return

    session = db.get_session_by_id(session["id"])
    if not session or session["status"] not in ("in_progress",):
        if session and session["status"] == "expired":
            st.error("⏰ El tiempo de esta evaluación ha expirado.")
            if st.button("Volver"):
                nav("candidate_select_test")
                st.rerun()
            return
        nav("candidate_select_test")
        st.rerun()
        return

    # Verificar tiempo restante
    remaining = db.check_session_time(session)
    if remaining == -1:
        st.error("⏰ El tiempo de esta evaluación ha expirado.")
        if st.button("Volver"):
            nav("candidate_select_test")
            st.rerun()
        return

    # Mostrar timer
    deadline_ts = db.get_session_deadline_timestamp(session)
    if deadline_ts:
        render_timer(deadline_ts, session["id"])

    st.markdown(f"### 🔐 ERI - Evaluación de Riesgo e Integridad")
    st.caption(f"Candidato: {candidate['name']} | ID: {session['id']}")
    
    # Cargar preguntas si no están en session_state
    if "eri_questions" not in st.session_state:
        all_questions = load_eri_questions()
        # Mezclar preguntas de manera consistente por sesión
        rng = random.Random(session["id"])
        rng.shuffle(all_questions)
        st.session_state.eri_questions = all_questions
        db.update_session_questions(session["id"], all_questions)

    # Inicializar respuestas
    if "eri_responses" not in st.session_state:
        st.session_state.eri_responses = [None] * len(st.session_state.eri_questions)

    # Inicializar página
    if "eri_page" not in st.session_state:
        st.session_state.eri_page = 0

    questions = st.session_state.eri_questions
    total = len(questions)
    questions_per_page = 10  # 10 preguntas por página
    page = st.session_state.eri_page
    q_start = page * questions_per_page
    q_end = min(q_start + questions_per_page, total)

    # Barra de progreso
    progress = q_end / total
    st.progress(progress)
    st.markdown(f"**Preguntas {q_start + 1} - {q_end} de {total}**")

    # Instrucciones
    st.info("""
    **Instrucciones:** Responde con la máxima SINCERIDAD a cada afirmación. No hay respuestas correctas o incorrectas.
    
    Escala:
    - **1** = Totalmente de acuerdo
    - **2** = De acuerdo
    - **3** = Neutral / No estoy seguro
    - **4** = En desacuerdo
    - **5** = Totalmente en desacuerdo
    
    ⚠️ **IMPORTANTE:** Esta evaluación detecta patrones de respuesta poco sinceros. Por favor, responde honestamente.
    """)

    # Mostrar preguntas de la página actual
    all_answered = True
    
    for i in range(q_start, q_end):
        q = questions[i]
        q_text = q["question"]
        dim = q["dimension"]
        
        # Crear tarjeta visual para cada pregunta con colores de ERI
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        border-radius: 12px; padding: 20px; margin: 15px 0;
                        border-left: 4px solid {ERI_COLORS.get(dim, '#3b82f6')};">
                <div style="margin-bottom: 8px;">
                    <span style="background: {ERI_COLORS.get(dim, '#3b82f6')}; color: white; 
                                padding: 4px 12px; border-radius: 20px; 
                                font-size: 0.85em; font-weight: bold;">
                        Pregunta {i + 1} - {dim}
                    </span>
                </div>
                <p style="color: #e2e8f0; font-size: 1.1em; margin: 12px 0;">
                    {q_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Radio buttons para la respuesta
        response_key = f"eri_q_{i}"
        
        # Inicializar desde respuestas guardadas
        if response_key not in st.session_state and st.session_state.eri_responses[i] is not None:
            st.session_state[response_key] = st.session_state.eri_responses[i]
        
        col1, col2 = st.columns([4, 1])
        with col1:
            response = st.radio(
                f"Respuesta {i + 1}",
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: {
                    1: "1 - Totalmente de acuerdo",
                    2: "2 - De acuerdo",
                    3: "3 - Neutral",
                    4: "4 - En desacuerdo",
                    5: "5 - Totalmente en desacuerdo"
                }[x],
                key=response_key,
                horizontal=False,
                index=None if response_key not in st.session_state or st.session_state[response_key] is None else st.session_state[response_key] - 1
            )
        
        with col2:
            st.markdown("<br>" * 2, unsafe_allow_html=True)
            if response is not None:
                st.success("✅")
                st.session_state.eri_responses[i] = response
            else:
                st.warning("⚠️")
                all_answered = False

    # Navegación
    st.markdown("---")
    col_prev, col_space, col_next = st.columns([1, 4, 1])

    with col_prev:
        if page > 0:
            if st.button("⬅️ Anterior", key="eri_prev"):
                st.session_state.eri_page -= 1
                st.rerun()

    with col_next:
        is_last = q_end >= total
        btn_label = "✅ Finalizar Evaluación" if is_last else "Siguiente ➡️"
        if st.button(btn_label, key="eri_next", disabled=not all_answered):
            # Verificar tiempo nuevamente
            remaining = db.check_session_time(db.get_session_by_id(session["id"]))
            if remaining == -1:
                st.error("⏰ El tiempo ha expirado.")
                return

            if is_last:
                # Verificar que todas las preguntas estén respondidas
                if None in st.session_state.eri_responses:
                    st.warning("⚠️ Hay preguntas sin responder. Revisa las páginas anteriores.")
                else:
                    # Calcular resultados
                    responses = st.session_state.eri_responses
                    raw, normalized, percentages, validity_score, validity_flags = calculate_eri_results(responses, questions)

                    # Guardar respuestas
                    answer_records = []
                    for i in range(total):
                        answer_records.append({
                            "question_index": i,
                            "question_text": questions[i]["question"],
                            "answer_value": responses[i],
                            "answer_b_value": None,  # No aplica para ERI
                        })
                    db.save_answers(session["id"], answer_records)

                    # Guardar resultados
                    results = {
                        "raw": raw,
                        "normalized": normalized,
                        "percentages": percentages,
                        "validity_score": validity_score,
                        "validity_flags": validity_flags
                    }
                    db.save_results(session["id"], results)
                    db.complete_test_session(session["id"])

                    # Limpiar session state
                    for key in ["eri_questions", "eri_responses", "eri_page", "test_session"]:
                        st.session_state.pop(key, None)

                    nav("candidate_done")
                    st.rerun()
            else:
                st.session_state.eri_page += 1
                st.rerun()


# -------------------------------------------------------------------------
# CANDIDATE: DONE
# -------------------------------------------------------------------------
def page_candidate_done():
    candidate = st.session_state.get("candidate")
    name = candidate["name"] if candidate else "Candidato"

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; padding: 60px 20px; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 20px; margin: 20px 0;">
        <h1 style="color: #065f46; font-size: 2.5em;">✅ ¡Evaluación Completada!</h1>
        <p style="color: #047857; font-size: 1.3em;">Gracias, <strong>{name}</strong>.</p>
        <p style="color: #047857; font-size: 1.1em;">Tu evaluación ha sido registrada exitosamente.<br>
        Los resultados serán revisados por el equipo de Recursos Humanos.</p>
        <p style="color: #6b7280; margin-top: 30px;">Puedes cerrar esta ventana o continuar con otra evaluación pendiente.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("📋 Ver otras evaluaciones pendientes", use_container_width=True):
            nav("candidate_select_test")
            st.rerun()

        if st.button("🚪 Salir", use_container_width=True):
            for key in ["candidate", "pending_sessions", "test_session", 
                       "disc_questions", "disc_page", "disc_answers", 
                       "valanti_responses", "valanti_page",
                       "wpi_questions", "wpi_responses", "wpi_page",
                       "eri_questions", "eri_responses", "eri_page"]:
                st.session_state.pop(key, None)
            nav("home")
            st.rerun()


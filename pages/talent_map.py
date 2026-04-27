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

def page_talent_map_test():
    """
    Página del test Talent Map (Mapeo de Competencias) - 80 preguntas con escala Likert 1-5.
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

    st.markdown(f"### 🎯 Talent Map - Mapeo de Competencias y Talentos")
    st.caption(f"Candidato: {candidate['name']} | ID: {session['id']}")
    
    # Cargar preguntas si no están en session_state
    if "tm_questions" not in st.session_state:
        all_questions = load_talent_map_questions()
        # Mezclar preguntas de manera consistente por sesión
        rng = random.Random(session["id"])
        rng.shuffle(all_questions)
        st.session_state.tm_questions = all_questions
        db.update_session_questions(session["id"], all_questions)

    # Inicializar respuestas
    if "tm_responses" not in st.session_state:
        st.session_state.tm_responses = [None] * len(st.session_state.tm_questions)

    # Inicializar página
    if "tm_page" not in st.session_state:
        st.session_state.tm_page = 0

    questions = st.session_state.tm_questions
    total = len(questions)
    questions_per_page = 10  # 10 preguntas por página
    page = st.session_state.tm_page
    q_start = page * questions_per_page
    q_end = min(q_start + questions_per_page, total)

    # Barra de progreso
    progress = q_end / total
    st.progress(progress)
    st.markdown(f"**Preguntas {q_start + 1} - {q_end} de {total}**")

    # Instrucciones
    st.info("""
    **Instrucciones:** Responde con HONESTIDAD sobre cómo te comportas habitualmente en situaciones laborales.
    
    Escala:
    - **5** = Totalmente de acuerdo (Siempre me describe)
    - **4** = De acuerdo (Frecuentemente me describe)
    - **3** = Neutral / A veces (Depende de la situación)
    - **2** = En desacuerdo (Raramente me describe)
    - **1** = Totalmente en desacuerdo (Nunca me describe)
    
    💡 No hay respuestas correctas o incorrectas. Este test evalúa tu perfil de competencias.
    """)

    # Mostrar preguntas de la página actual
    all_answered = True
    
    for i in range(q_start, q_end):
        q = questions[i]
        q_text = q["question"]
        comp = q["competency"]
        
        # Crear tarjeta visual para cada pregunta con colores de Talent Map
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
                        border-radius: 12px; padding: 20px; margin: 15px 0;
                        border-left: 4px solid {TALENT_MAP_COLORS.get(comp, '#3b82f6')};">
                <div style="margin-bottom: 8px;">
                    <span style="background: {TALENT_MAP_COLORS.get(comp, '#3b82f6')}; color: white; 
                                padding: 4px 12px; border-radius: 20px; 
                                font-size: 0.85em; font-weight: bold;">
                        Pregunta {i + 1} - {comp}
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
        response_key = f"tm_q_{i}"
        
        # Inicializar desde respuestas guardadas
        if response_key not in st.session_state and st.session_state.tm_responses[i] is not None:
            st.session_state[response_key] = st.session_state.tm_responses[i]
        
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
                st.session_state.tm_responses[i] = response
            else:
                st.warning("⚠️")
                all_answered = False

    # Navegación
    st.markdown("---")
    col_prev, col_space, col_next = st.columns([1, 4, 1])

    with col_prev:
        if page > 0:
            if st.button("⬅️ Anterior", key="tm_prev"):
                st.session_state.tm_page -= 1
                st.rerun()

    with col_next:
        is_last = q_end >= total
        btn_label = "✅ Finalizar Evaluación" if is_last else "Siguiente ➡️"
        if st.button(btn_label, key="tm_next", disabled=not all_answered):
            # Verificar tiempo nuevamente
            remaining = db.check_session_time(db.get_session_by_id(session["id"]))
            if remaining == -1:
                st.error("⏰ El tiempo ha expirado.")
                return

            if is_last:
                # Verificar que todas las preguntas estén respondidas
                if None in st.session_state.tm_responses:
                    st.warning("⚠️ Hay preguntas sin responder. Revisa las páginas anteriores.")
                else:
                    # Calcular resultados
                    responses = st.session_state.tm_responses
                    raw, normalized, percentages = calculate_talent_map_results(responses, questions)

                    # Guardar respuestas
                    answer_records = []
                    for i in range(total):
                        answer_records.append({
                            "question_index": i,
                            "question_text": questions[i]["question"],
                            "answer_value": responses[i],
                            "answer_b_value": None,  # No aplica para Talent Map
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
                    for key in ["tm_questions", "tm_responses", "tm_page", "test_session"]:
                        st.session_state.pop(key, None)

                    nav("candidate_done")
                    st.rerun()
            else:
                st.session_state.tm_page += 1
                st.rerun()


def show_talent_map_results_admin(results, candidate, session):
    """
    Muestra los resultados del Talent Map en el panel de administración.
    
    Args:
        results: Dict con raw, normalized, percentages
        candidate: Dict con información del candidato
        session: Dict con información de la sesión o str con session_id
    """
    raw = results.get("raw", {})
    normalized = results.get("normalized", {})
    percentages = results.get("percentages", {})
    
    # Selector de perfil de puesto para comparación
    st.markdown("### 🎯 Comparación con Perfil de Puesto")
    
    job_profile_name = st.selectbox(
        "Selecciona un perfil de puesto para comparar competencias:",
        options=["(Sin comparación)"] + list(TALENT_MAP_JOB_PROFILES.keys()),
        key="tm_job_profile_selector"
    )
    
    # Análisis de competencias con o sin match
    if job_profile_name and job_profile_name != "(Sin comparación)":
        analysis = analyze_talent_map_match(normalized, job_profile_name)
    else:
        analysis = analyze_talent_map_match(normalized, None)
    
    # === BANNER DE RESULTADO GENERAL ===
    avg_color = "#10B981" if analysis['average_score'] >= 75 else ("#F59E0B" if analysis['average_score'] >= 50 else "#EF4444")
    
    st.markdown(f"""
    <div style="background: {avg_color}22; border-left: 5px solid {avg_color};
                padding: 15px 20px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: {avg_color};">
            🎯 Perfil de Competencias — Promedio: {analysis['average_score']:.1f}/100
        </h3>
        <p style="margin: 5px 0 0 0; color: #374151;">
            <b>Competencia más fuerte:</b> {analysis['strongest_competency']} ({int(analysis['strongest_score'])}/100) | 
            <b>Área de mayor desarrollo:</b> {analysis['weakest_competency']} ({int(analysis['weakest_score'])}/100)
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # === ANÁLISIS DE MATCH (si aplica) ===
    if analysis.get('match_analysis'):
        match = analysis['match_analysis']
        match_color = match['match_color']
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                    padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;">
            <h4 style="margin: 0 0 5px 0;">📊 Match con {match['job_emoji']} {match['job_profile']}</h4>
            <h2 style="margin: 0; color: {match_color};">{match['match_label']}: {match['match_percentage']:.1f}%</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">{match['match_desc']}</p>
            <p style="margin: 8px 0 0 0; font-size: 0.9em; opacity: 0.85;">{match['job_description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # === MÉTRICAS POR COMPETENCIA ===
    st.markdown("### 📊 Puntajes por Competencia")
    
    # Crear columnas para las 8 competencias
    cols = st.columns(4)
    for idx, comp in enumerate(TALENT_MAP_COMPETENCIES):
        with cols[idx % 4]:
            score = normalized.get(comp, 0)
            if score >= 75:
                nivel = "🌟 Alto"
                delta_color = "normal"
            elif score >= 50:
                nivel = "👍 Medio"
                delta_color = "off"
            else:
                nivel = "📈 Desarrollo"
                delta_color = "inverse"
            
            st.metric(
                label=comp,
                value=f"{int(score)}/100",
                delta=nivel,
                delta_color=delta_color
            )
    
    st.markdown("---")
    
    # === GRÁFICOS ===
    # Si hay perfil de puesto seleccionado, crear gráficos con comparación
    if job_profile_name and job_profile_name != "(Sin comparación)":
        job_profile_scores = TALENT_MAP_JOB_PROFILES[job_profile_name]["competencias"]
        
        col_radar = st.container()
        with col_radar:
            st.markdown("#### 🎯 Perfil de Competencias (Candidato vs. Perfil Requerido)")
            radar_fig = create_talent_map_radar(normalized, job_profile_scores)
            st.pyplot(radar_fig)
        
        st.markdown("---")
        
        col_bars = st.container()
        with col_bars:
            st.markdown("#### 📊 Comparación de Competencias")
            bar_fig = create_talent_map_bars(normalized, job_profile_scores)
            st.pyplot(bar_fig)
        
        st.markdown("---")
        
        col_comparison = st.container()
        with col_comparison:
            st.markdown("#### 📈 Análisis de Brechas de Competencia")
            comparison_fig = create_talent_map_comparison(normalized, job_profile_name, job_profile_scores)
            st.pyplot(comparison_fig)
    else:
        col_radar, col_bars = st.columns(2)
        
        with col_radar:
            st.markdown("#### 🎯 Perfil de Competencias (Radar)")
            radar_fig = create_talent_map_radar(normalized)
            st.pyplot(radar_fig)
        
        with col_bars:
            st.markdown("#### 📊 Puntajes por Competencia")
            bar_fig = create_talent_map_bars(normalized)
            st.pyplot(bar_fig)
        
        comparison_fig = None
    
    st.markdown("---")
    
    # === ANÁLISIS POR COMPETENCIA ===
    st.markdown("### 📋 Análisis Detallado por Competencia")
    
    sorted_scores = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    
    for comp, score in sorted_scores:
        desc_info = TALENT_MAP_DESCRIPTIONS[comp]
        
        # Determinar nivel
        if score >= 75:
            level = "🌟 Alto"
            text = desc_info["high"]
            color = "#10B981"
        elif score >= 50:
            level = "👍 Medio"
            text = desc_info["medium"]
            color = "#F59E0B"
        else:
            level = "📈 En Desarrollo"
            text = desc_info["low"]
            color = "#EF4444"
        
        st.markdown(f"""
        <div style="background: {color}15; border-left: 3px solid {color}; 
                    padding: 12px; border-radius: 6px; margin-bottom: 10px;">
            <b style="color: {color};">{desc_info['title']}</b> — {level} ({int(score)}/100)
            <br><span style="color: #374151;">{text}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === FORTALEZAS ===
    if analysis.get('fortalezas'):
        st.markdown("### 💚 Fortalezas Clave")
        for f in analysis['fortalezas']:
            # Limpiar markdown
            f_clean = f.replace("**", "")
            st.markdown(f"- ✅ {f_clean}")
        st.markdown("")
    
    # === ÁREAS DE DESARROLLO ===
    if analysis.get('areas_desarrollo'):
        st.markdown("### 📈 Áreas de Desarrollo")
        for a in analysis['areas_desarrollo']:
            # Limpiar markdown
            a_clean = a.replace("**", "")
            st.markdown(f"- 🔵 {a_clean}")
        st.markdown("")
    
    # === GAPS Y STRENGTHS DE MATCH (si aplica) ===
    if analysis.get('match_analysis'):
        match = analysis['match_analysis']
        
        # Strengths del match
        if match.get('match_strengths'):
            st.markdown("### ✅ Competencias que Exceden el Perfil")
            for s in match['match_strengths']:
                s_clean = s.replace("**", "")
                st.markdown(f"- ✨ {s_clean}")
            st.markdown("")
        
        # Gaps del match
        if match.get('match_gaps'):
            st.markdown("### ⚠️ Brechas a Cerrar")
            for g in match['match_gaps']:
                g_clean = g.replace("**", "")
                st.markdown(f"- 📊 {g_clean}")
            st.markdown("")
    
    # === RECOMENDACIONES ===
    if analysis.get('recomendaciones'):
        with st.expander("💼 Ver Recomendaciones y Plan de Desarrollo"):
            for r in analysis['recomendaciones']:
                # Limpiar markdown (pero mantener bullets internos)
                r_clean = r.replace("**", "")
                st.markdown(f"{r_clean}")
    
    st.markdown("---")
    
    # === DESCARGA DE REPORTES ===
    st.markdown("### 📥 Descargar Reportes")
    
    session_id = session if isinstance(session, str) else session.get("id")
    completed_at = session.get("completed_at") if isinstance(session, dict) else None
    
    # Generar PDF (con o sin comparación de perfil)
    if job_profile_name and job_profile_name != "(Sin comparación)":
        pdf_buffer = generate_talent_map_pdf(
            candidate, raw, normalized, radar_fig, session_id, 
            completed_at, analysis, job_profile_name, comparison_fig
        )
    else:
        pdf_buffer = generate_talent_map_pdf(
            candidate, raw, normalized, radar_fig, session_id, 
            completed_at, analysis
        )
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📄 Descargar Reporte PDF Completo",
            data=pdf_buffer,
            file_name=f"talent_map_{candidate['cedula']}_{session_id}.pdf",
            mime="application/pdf",
            key=f"pdf_tm_{session_id}"
        )
    
    with col2:
        st.download_button(
            label="📊 Descargar Datos JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name=f"talent_map_{candidate['cedula']}_{session_id}.json",
            mime="application/json",
            key=f"json_tm_{session_id}"
        )



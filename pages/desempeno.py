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

def page_desempeno_eval():
    """Página de evaluación de desempeño (completada por el administra

dor)."""
    session_id = st.session_state.get("desempeno_session_id")
    
    if not session_id:
        st.error("No se encontró una sesión de evaluación activa.")
        if st.button("Volver al Dashboard"):
            nav("admin_dashboard")
            st.rerun()
        return
    
    session = db.get_session_by_id(session_id)
    if not session:
        st.error("Sesión no válida.")
        return
    
    candidate = db.get_candidate_by_cedula(
        db.get_connection().execute("SELECT cedula FROM candidates WHERE id = ?", (session["candidate_id"],)).fetchone()["cedula"]
    )
    
    admin = st.session_state.get("admin")
    evaluador = st.session_state.get("evaluador")
    if evaluador:
        evaluador_nombre = evaluador.get("name", "Evaluador")
    elif admin:
        evaluador_nombre = admin.get("name", "Administrador")
    else:
        evaluador_nombre = session.get("evaluador_nombre") or "Evaluador"
    
    st.markdown(f"## 📊 Evaluación de Desempeño")
    st.markdown(f"**Colaborador:** {candidate['name']} (Cédula: {candidate['cedula']})")
    st.markdown(f"**Cargo:** {candidate.get('position', 'N/A')}")
    st.markdown(f"**Evaluador:** {evaluador_nombre}")
    st.markdown("---")
    
    # Formulario de evaluación
    with st.form("evaluacion_desempeno_form"):
        st.markdown("### 📝 SECCIÓN 1: Evaluación de Rendimiento")
        st.markdown("Califique los siguientes 6 objetivos con una escala del 1 al 5:")
        st.markdown("**5** = Sobresaliente | **4** = Supera | **3** = Cumple | **2** = Debajo | **1** = Insatisfactorio")
        
        rendimiento_scores = {}
        
        for obj in DESEMPENO_OBJETIVOS:
            st.markdown(f"**{obj['titulo']}**")
            st.caption(obj['descripcion'])
            
            rendimiento_scores[obj['id']] = st.select_slider(
                f"Calificación Objetivo {obj['id']}",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: DESEMPENO_ESCALA_RENDIMIENTO[x]['label'],
                key=f"rend_{obj['id']}",
                label_visibility="collapsed"
            )
            st.markdown("---")
        
        st.markdown("### 🎯 SECCIÓN 2: Evaluación de Potencial")
        st.markdown("Seleccione el nivel que mejor describe al colaborador en cada dimensión (0-3):")
        
        potencial_scores = {}
        
        for dim in DESEMPENO_DIMENSIONES:
            st.markdown(f"**{dim['nombre']}**")
            st.caption(dim['descripcion'])
            
            opciones_texto = [f"Nivel {nivel}: {descripcion[:80]}..." for nivel, descripcion in dim['niveles'].items()]
            nivel_seleccionado = st.radio(
                f"Nivel para {dim['nombre']}",
                options=[3, 2, 1, 0],
                format_func=lambda x: f"Nivel {x}",
                key=f"pot_{dim['id']}",
                horizontal=True,
                label_visibility="collapsed"
            )
            
            potencial_scores[dim['id']] = nivel_seleccionado
            
            # Mostrar descripción del nivel seleccionado
            with st.expander("📄 Ver descripción completa del nivel seleccionado"):
                st.info(dim['niveles'][nivel_seleccionado])
            
            st.markdown("---")
        
        st.markdown("### 💡 SECCIÓN 3: Iniciativas de Mejora (Opcional)")
        st.markdown("Si el desempeño lo requiere, defina hasta 3 iniciativas de mejora:")
        
        iniciativa_1 = st.text_area("Iniciativa 1", placeholder="Descripción de la primera iniciativa...", key="init_1")
        iniciativa_2 = st.text_area("Iniciativa 2", placeholder="Descripción de la segunda iniciativa...", key="init_2")
        iniciativa_3 = st.text_area("Iniciativa 3", placeholder="Descripción de la tercera iniciativa...", key="init_3")
        
        iniciativas = [ini for ini in [iniciativa_1, iniciativa_2, iniciativa_3] if ini and ini.strip()]
        
        submitted = st.form_submit_button("✅ Completar Evaluación y Calcular Resultados", type="primary")
        
        if submitted:
            # Calcular resultados
            analysis = calculate_desempeno_results(rendimiento_scores, potencial_scores, iniciativas)
            
            # Guardar resultados en BD
            results_data = {
                "rendimiento_scores": rendimiento_scores,
                "potencial_scores": potencial_scores,
                "iniciativas": iniciativas,
                "analysis": analysis,
                "evaluador": evaluador_nombre
            }
            
            db.save_results(session_id, results_data)
            db.complete_test_session(session_id)
            
            st.success("✅ Evaluación completada y guardada exitosamente.")
            st.balloons()
            
            # Limpiar session_id y mostrar resultados
            del st.session_state["desempeno_session_id"]
            if evaluador:
                nav("evaluador_dashboard")
            else:
                nav("admin_dashboard")
            st.rerun()
    
    if st.button("❌ Cancelar Evaluación"):
        if "desempeno_session_id" in st.session_state:
            del st.session_state["desempeno_session_id"]
        if evaluador:
            nav("evaluador_dashboard")
        else:
            nav("admin_dashboard")
        st.rerun()


def show_desempeno_results_admin(results, candidate, session):
    """Muestra resultados de Evaluación de Desempeño en el panel de administración."""
    
    rendimiento_scores = results.get("rendimiento_scores", {})
    potencial_scores = results.get("potencial_scores", {})
    iniciativas = results.get("iniciativas", [])
    analysis = results.get("analysis", {})
    evaluador = results.get("evaluador", "N/A")
    
    # Convertir session a session_id si es necesario
    session_id = session["id"] if isinstance(session, dict) else session
    
    # Banner de clasificación
    if analysis.get("clasificacion"):
        clasif = analysis["clasificacion"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {clasif['color']}22 0%, {clasif['color']}44 100%);
                    border-left: 6px solid {clasif['color']}; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: {clasif['color']};">{clasif['label']}</h2>
            <p style="margin: 8px 0 0 0; font-size: 15px; color: #374151;">{clasif['descripcion']}</p>
            <p style="margin: 12px 0 0 0; font-size: 14px; color: #6B7280;">
                <b>Evaluador:</b> {evaluador} | <b>Puntaje Global:</b> {analysis.get('puntaje_global', 0):.2f}/5.00
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🎯 Promedio Rendimiento",
            f"{analysis.get('promedio_rendimiento', 0):.2f}/5.00",
            help="Promedio de los 6 objetivos de rendimiento"
        )
    
    with col2:
        st.metric(
            "⭐ Promedio Potencial",
            f"{analysis.get('promedio_potencial', 0):.2f}/3.00",
            help="Promedio de las 5 dimensiones de potencial"
        )
    
    with col3:
        st.metric(
            "📊 Puntaje Global",
            f"{analysis.get('puntaje_global', 0):.2f}/5.00",
            help="Puntaje ponderado: 60% Rendimiento + 40% Potencial"
        )
    
    st.markdown("---")
    
    # Gráficos
    st.markdown("### 📈 Visualización de Resultados")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### Evaluación de Rendimiento")
        bars_fig = create_desempeno_bars(rendimiento_scores)
        st.pyplot(bars_fig)
        plt.close(bars_fig)
    
    with col_right:
        st.markdown("#### Evaluación de Potencial")
        radar_fig = create_desempeno_radar(potencial_scores)
        st.pyplot(radar_fig)
        plt.close(radar_fig)
    
    st.markdown("---")
    
    # Detalles por secciones
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Rendimiento", "🎯 Potencial", "💡 Análisis", "🎯 Iniciativas"])
    
    with tab1:
        st.markdown("#### Desglose por Objetivo de Rendimiento")
        for obj_id, score in rendimiento_scores.items():
            objetivo = DESEMPENO_OBJETIVOS[int(obj_id) - 1]
            nivel = DESEMPENO_ESCALA_RENDIMIENTO.get(int(score), {"label": "Sin calificar", "color": "#6B7280"})
            
            col_obj1, col_obj2 = st.columns([3, 1])
            with col_obj1:
                st.markdown(f"**{objetivo['titulo']}**")
                st.caption(objetivo['descripcion'])
            with col_obj2:
                st.markdown(f"<div style='background:{nivel['color']}22; padding:12px; border-radius:8px; text-align:center;'>"
                           f"<b>{score:.1f}/5.0</b><br><span style='font-size:12px;'>{nivel['label']}</span></div>",
                           unsafe_allow_html=True)
            st.markdown("---")
    
    with tab2:
        st.markdown("#### Desglose por Dimensión de Potencial")
        for dim_id, score in potencial_scores.items():
            dimension = DESEMPENO_DIMENSIONES[int(dim_id) - 1]
            
            col_dim1, col_dim2 = st.columns([3, 1])
            with col_dim1:
                st.markdown(f"**{dimension['nombre']}**")
                st.caption(dimension['descripcion'])
                with st.expander("📄 Ver descripción del nivel asignado"):
                    st.info(dimension['niveles'][int(score)])
            with col_dim2:
                color = DESEMPENO_COLORES_DIMENSIONES.get(dimension['nombre'], "#6B7280")
                st.markdown(f"<div style='background:{color}22; padding:12px; border-radius:8px; text-align:center;'>"
                           f"<b>Nivel {score}/3</b></div>",
                           unsafe_allow_html=True)
            st.markdown("---")
    
    with tab3:
        col_for, col_mej = st.columns(2)
        
        with col_for:
            st.markdown("#### ✅ Fortalezas")
            
            if analysis.get("fortalezas_rendimiento"):
                st.markdown("**Rendimiento:**")
                for item in analysis["fortalezas_rendimiento"]:
                    st.success(f"**{item['titulo']}** - {item['score']:.1f}/5.0 ({item['label']})")
            
            if analysis.get("fortalezas_potencial"):
                st.markdown("**Potencial:**")
                for item in analysis["fortalezas_potencial"]:
                    st.success(f"**{item['nombre']}** - {item['nivel']}")
        
        with col_mej:
            st.markdown("#### ⚠️ Áreas de Mejora")
            
            if analysis.get("areas_mejora_rendimiento"):
                st.markdown("**Rendimiento:**")
                for item in analysis["areas_mejora_rendimiento"]:
                    st.warning(f"**{item['titulo']}** - {item['score']:.1f}/5.0 ({item['label']})")
            
            if analysis.get("areas_desarrollo_potencial"):
                st.markdown("**Potencial:**")
                for item in analysis["areas_desarrollo_potencial"]:
                    st.warning(f"**{item['nombre']}** - {item['nivel']}")
        
        st.markdown("---")
        st.markdown("#### 💡 Recomendaciones")
        if analysis.get("recomendaciones"):
            for recom in analysis["recomendaciones"]:
                st.info(f"• {recom}")
    
    with tab4:
        st.markdown("#### 🎯 Iniciativas de Mejora Definidas")
        
        if iniciativas and len(iniciativas) > 0:
            for i, iniciativa in enumerate(iniciativas, 1):
                st.markdown(f"**Iniciativa {i}:**")
                st.info(iniciativa)
        else:
            if analysis.get("requiere_iniciativas"):
                st.warning("⚠️ Esta evaluación requiere establecer iniciativas de mejora, pero no se definieron.")
            else:
                st.success("✅ El desempeño es satisfactorio. No se requieren iniciativas de mejora.")
    
    st.markdown("---")
    
    # Descargar PDF y JSON
    st.markdown("### 📥 Descargar Resultados")
    
    col1, col2 = st.columns(2)
    
    # Regenerar gráficos para PDF
    radar_fig_pdf = create_desempeno_radar(potencial_scores)
    bars_fig_pdf = create_desempeno_bars(rendimiento_scores)
    
    pdf_buffer = generate_desempeno_pdf(
        candidate=candidate,
        rendimiento_scores=rendimiento_scores,
        potencial_scores=potencial_scores,
        radar_fig=radar_fig_pdf,
        bars_fig=bars_fig_pdf,
        session_id=session_id,
        completed_at=session.get("completed_at") if isinstance(session, dict) else None,
        analysis=analysis,
        evaluador_nombre=evaluador,
        iniciativas=iniciativas
    )
    
    with col1:
        st.download_button(
            "📄 Descargar PDF",
            data=pdf_buffer,
            file_name=f"evaluacion_desempeno_{candidate['cedula']}_{session_id}.pdf",
            mime="application/pdf",
            key=f"pdf_desempeno_{session_id}"
        )
    
    with col2:
        st.download_button(
            "📄 Descargar JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name=f"evaluacion_desempeno_{candidate['cedula']}_{session_id}.json",
            mime="application/json",
            key=f"json_desempeno_{session_id}"
        )


# -------------------------------------------------------------------------
# ADMIN: EVALUACIÓN DE DESEMPEÑO — LÍDERES (FO-GH-41)
# -------------------------------------------------------------------------
def page_desempeno_lider_eval():
    """Página de evaluación de desempeño para líderes (completada por el administrador)."""
    session_id = st.session_state.get("desempeno_lider_session_id")
    if not session_id:
        st.error("No se encontró una sesión de evaluación activa.")
        if st.button("Volver al Dashboard"):
            nav("admin_dashboard")
            st.rerun()
        return

    session = db.get_session_by_id(session_id)
    if not session:
        st.error("Sesión no válida.")
        return

    candidate = db.get_candidate_by_cedula(
        db.get_connection().execute("SELECT cedula FROM candidates WHERE id = ?", (session["candidate_id"],)).fetchone()["cedula"]
    )
    admin = st.session_state.get("admin")
    evaluador_nombre = admin.get("name", "Administrador") if admin else "Administrador"
    nivel_cargo = candidate.get("nivel_cargo", "ANALISTA") or "ANALISTA"

    st.markdown("## 📊 Evaluación de Desempeño — Líderes")
    st.markdown(f"**Colaborador:** {candidate['name']} (Cédula: {candidate['cedula']})")
    st.markdown(f"**Cargo:** {candidate.get('position', 'N/A')} | **Nivel:** {nivel_cargo}")
    st.markdown(f"**Evaluador:** {evaluador_nombre}")
    st.markdown("---")

    with st.form("evaluacion_desempeno_lider_form"):
        # ---- SECCIÓN 1: COMPETENCIAS ----
        st.markdown("### 🏆 SECCIÓN 1: Evaluación de Competencias Organizacionales")
        st.markdown("Seleccione el nivel alcanzado por el colaborador en cada competencia (1-6):")

        nivel_req_info = COMPETENCIAS_NIVEL_REQUERIDO.get(nivel_cargo.upper(), None)
        competencias_scores = {}

        for comp in COMPETENCIAS_ORGANIZACIONALES:
            req = nivel_req_info["niveles"][comp["id"] - 1] if nivel_req_info else None
            req_text = f" _(Requerido: Nivel {req})_" if req else ""
            st.markdown(f"**{comp['nombre']}**{req_text}")
            st.caption(comp["descripcion"])
            opciones = {n: f"Nivel {n}: {desc[:90]}..." for n, desc in comp["niveles"].items()}
            nivel_sel = st.radio(
                f"Nivel {comp['nombre']}",
                options=[1, 2, 3, 4, 5, 6],
                format_func=lambda x, c=comp: f"Nivel {x} — {c['niveles'][x][:80]}...",
                horizontal=True,
                key=f"comp_{comp['id']}",
                label_visibility="collapsed",
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
                key=f"rend_lider_{obj['id']}",
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
                key=f"pot_lider_{dim['id']}",
                label_visibility="collapsed",
            )
            potencial_scores[dim["id"]] = nivel_sel
            st.markdown("---")

        # ---- INICIATIVAS ----
        st.markdown("### 🚀 Iniciativas de Mejora")
        n_iniciativas = st.selectbox("Número de iniciativas", [0, 1, 2, 3], index=1, key="n_init_lider")
        iniciativas = []
        for i in range(n_iniciativas):
            ini = st.text_area(f"Iniciativa {i+1}", key=f"ini_lider_{i}", height=80)
            if ini.strip():
                iniciativas.append(ini.strip())

        submitted = st.form_submit_button("✅ Guardar Evaluación", use_container_width=True, type="primary")

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
            }
            db.save_results(session_id, results_to_save)
            db.complete_test_session(session_id)
            st.success("✅ Evaluación de desempeño (líderes) guardada exitosamente.")
            st.session_state.pop("desempeno_lider_session_id", None)
            nav("admin_dashboard")
            st.rerun()

    if st.button("❌ Cancelar"):
        st.session_state.pop("desempeno_lider_session_id", None)
        nav("admin_dashboard")
        st.rerun()




def show_desempeno_lider_results_admin(results, candidate, session):
    """Muestra resultados de la evaluación de desempeño para líderes."""
    analysis = results.get("analysis", {})
    competencias_scores = {int(k): v for k, v in results.get("competencias_scores", {}).items()}
    rendimiento_scores = {int(k): v for k, v in results.get("rendimiento_scores", {}).items()}
    potencial_scores = {int(k): v for k, v in results.get("potencial_scores", {}).items()}
    iniciativas = results.get("iniciativas", [])
    evaluador = results.get("evaluador", "N/A")
    nivel_cargo = results.get("nivel_cargo", "N/A")
    session_id = session["id"] if isinstance(session, dict) else session

    clasif = analysis.get("clasificacion") or {}
    comp_clasif = analysis.get("clasificacion_comp") or {}

    if clasif:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {clasif.get('color','#6B7280')}22, {clasif.get('color','#6B7280')}44);
                    border-left: 6px solid {clasif.get('color','#6B7280')}; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h2 style="margin:0; color:{clasif.get('color','#111')};">{clasif.get('label','')}</h2>
            <p style="margin:8px 0 0 0; font-size:15px; color:#374151;">{clasif.get('descripcion','')}</p>
            <p style="margin:12px 0 0 0; font-size:14px; color:#6B7280;">
                <b>Evaluador:</b> {evaluador} | <b>Nivel Cargo:</b> {nivel_cargo} | <b>Puntaje Global:</b> {analysis.get('puntaje_global', 0):.2f}/5.00
            </p>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏆 Competencias", f"{analysis.get('promedio_competencias', 0):.2f}/6.00")
    col2.metric("🎯 Rendimiento", f"{analysis.get('promedio_rendimiento', 0):.2f}/5.00")
    col3.metric("⭐ Potencial", f"{analysis.get('promedio_potencial', 0):.2f}/3.00")
    col4.metric("📊 Global", f"{analysis.get('puntaje_global', 0):.2f}/5.00")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 Competencias", "📝 Rendimiento", "🎯 Potencial", "💡 Análisis", "🚀 Iniciativas"
    ])

    with tab1:
        st.markdown(f"#### Promedio de Competencias: **{analysis.get('promedio_competencias', 0):.2f}/6.00**")
        if comp_clasif:
            st.markdown(f"**Clasificación:** {comp_clasif.get('label','')}")
        nivel_req_info = COMPETENCIAS_NIVEL_REQUERIDO.get(nivel_cargo.upper(), None)
        for comp in COMPETENCIAS_ORGANIZACIONALES:
            cid = comp["id"]
            score = competencias_scores.get(cid, 0)
            req = nivel_req_info["niveles"][cid - 1] if nivel_req_info else None
            brecha = score - req if req is not None else None
            color = "#10B981" if (brecha is None or brecha >= 0) else "#EF4444"
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**{comp['nombre']}**")
                if req:
                    st.caption(f"Requerido: Nivel {req} | Asignado: Nivel {score}")
            with col_b:
                brecha_txt = f"(+{brecha})" if brecha and brecha > 0 else (f"({brecha})" if brecha else "")
                st.markdown(f"<div style='background:{color}22; padding:10px; border-radius:8px; text-align:center;'>"
                           f"<b>Nivel {score}</b><br><span style='color:{color}; font-size:12px;'>{brecha_txt}</span></div>",
                           unsafe_allow_html=True)
            with st.expander("Ver descripción del nivel asignado"):
                st.info(comp["niveles"].get(score, "N/A"))
            st.markdown("---")

    with tab2:
        for obj_id, score in rendimiento_scores.items():
            objetivo = DESEMPENO_OBJETIVOS[int(obj_id) - 1]
            nivel = DESEMPENO_ESCALA_RENDIMIENTO.get(int(score), {"label": "Sin calificar", "color": "#6B7280"})
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{objetivo['titulo']}**")
                st.caption(objetivo["descripcion"])
            with c2:
                st.markdown(f"<div style='background:{nivel['color']}22; padding:10px; border-radius:8px; text-align:center;'>"
                           f"<b>{score}/5</b><br><span style='font-size:12px;'>{nivel['label']}</span></div>",
                           unsafe_allow_html=True)
            st.markdown("---")

    with tab3:
        for dim_id, score in potencial_scores.items():
            dimension = DESEMPENO_DIMENSIONES[int(dim_id) - 1]
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{dimension['nombre']}**")
                st.caption(dimension["descripcion"])
                with st.expander("Ver descripción"):
                    st.info(dimension["niveles"][int(score)])
            with c2:
                color = DESEMPENO_COLORES_DIMENSIONES.get(dimension["nombre"], "#6B7280")
                st.markdown(f"<div style='background:{color}22; padding:10px; border-radius:8px; text-align:center;'>"
                           f"<b>Nivel {score}/3</b></div>", unsafe_allow_html=True)
            st.markdown("---")

    with tab4:
        col_for, col_mej = st.columns(2)
        with col_for:
            st.markdown("#### ✅ Fortalezas")
            for item in analysis.get("fortalezas_competencias", []):
                st.success(f"🏆 **{item['nombre']}** — Nivel {item['score']}")
            for item in analysis.get("fortalezas_rendimiento", []):
                st.success(f"🎯 **{item['titulo']}** — {item['score']}/5 ({item['label']})")
            for item in analysis.get("fortalezas_potencial", []):
                st.success(f"⭐ **{item['nombre']}** — {item['nivel']}")
        with col_mej:
            st.markdown("#### ⚠️ Áreas de Mejora")
            for item in analysis.get("brechas_competencias", []):
                st.warning(f"🏆 **{item['nombre']}** — Nivel {item['score']} (req. {item['requerido']}, brecha {item['brecha']})")
            for item in analysis.get("areas_mejora_rendimiento", []):
                st.warning(f"🎯 **{item['titulo']}** — {item['score']}/5 ({item['label']})")
            for item in analysis.get("areas_desarrollo_potencial", []):
                st.warning(f"⭐ **{item['nombre']}** — {item['nivel']}")
        st.markdown("---")
        st.markdown("#### 💡 Recomendaciones")
        for recom in analysis.get("recomendaciones", []):
            st.info(f"• {recom}")

    with tab5:
        if iniciativas:
            for i, ini in enumerate(iniciativas, 1):
                st.markdown(f"**Iniciativa {i}:** {ini}")
        else:
            st.info("No se definieron iniciativas.")

    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "📄 Descargar JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name=f"desempeno_lider_{candidate['cedula']}_{session_id}.json",
            mime="application/json",
            key=f"json_dl_{session_id}",
        )
    with col_dl2:
        try:
            _pdf_dl = generate_desempeno_lider_pdf(
                candidate=candidate,
                competencias_scores=competencias_scores,
                rendimiento_scores=rendimiento_scores,
                potencial_scores=potencial_scores,
                session_id=session_id,
                completed_at=session.get("completed_at") if isinstance(session, dict) else None,
                analysis=analysis,
                evaluador_nombre=evaluador,
                nivel_cargo=nivel_cargo,
                iniciativas=iniciativas,
            )
            st.download_button(
                "📑 Descargar PDF",
                data=_pdf_dl,
                file_name=f"desempeno_lider_{candidate['cedula']}_{session_id}.pdf",
                mime="application/pdf",
                key=f"pdf_dl_{session_id}",
            )
        except Exception as _pdf_err:
            st.warning(f"No se pudo generar el PDF: {_pdf_err}")


# -------------------------------------------------------------------------
# ADMIN: EVALUACIÓN PERÍODO DE PRUEBA (FO-GH-46)
# -------------------------------------------------------------------------
def page_periodo_prueba_eval():
    """Página de evaluación de período de prueba (completada por el administrador/evaluador)."""
    session_id = st.session_state.get("periodo_prueba_session_id")
    if not session_id:
        st.error("No se encontró una sesión de evaluación activa.")
        if st.button("Volver al Dashboard"):
            nav("admin_dashboard")
            st.rerun()
        return

    session = db.get_session_by_id(session_id)
    if not session:
        st.error("Sesión no válida.")
        return

    candidate = db.get_candidate_by_cedula(
        db.get_connection().execute("SELECT cedula FROM candidates WHERE id = ?", (session["candidate_id"],)).fetchone()["cedula"]
    )
    admin = st.session_state.get("admin")
    evaluador_nombre = admin.get("name", "Administrador") if admin else "Administrador"

    st.markdown("## 📋 Evaluación Período de Prueba")
    st.markdown(f"**Trabajador:** {candidate['name']} (Cédula: {candidate['cedula']})")
    st.markdown(f"**Cargo:** {candidate.get('position', 'N/A')} | **Área:** {candidate.get('regional', 'N/A')}")
    st.markdown(f"**Evaluador:** {evaluador_nombre}")
    st.info("Marque la frecuencia con la que observa cada comportamiento durante el desempeño laboral.")
    st.markdown("---")

    with st.form("evaluacion_periodo_prueba_form"):
        # ---- SECCIÓN 1: ACTUACIONES ----
        st.markdown("### 📝 Sección 1: Actuaciones y Comportamientos")
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
                    key=f"act_{idx}",
                    label_visibility="collapsed",
                )
            st.markdown("---")

        # ---- SECCIÓN 2: CALIFICACIONES ----
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
                    key=f"cal_{idx}",
                    label_visibility="collapsed",
                )
            st.markdown("---")

        # ---- SECCIÓN 3: PREGUNTAS ADICIONALES ----
        st.markdown("### 📌 Sección 3: Información Adicional")
        col_lam, col_con = st.columns(2)
        with col_lam:
            llamados = st.radio("¿Tuvo llamados de atención?", options=[False, True],
                                format_func=lambda x: "SÍ" if x else "NO",
                                key="llamados_atencion", horizontal=True)
        with col_con:
            conocimiento = st.radio("¿Su conocimiento se adecua al perfil del cargo?",
                                    options=[True, False],
                                    format_func=lambda x: "SÍ" if x else "NO",
                                    key="conocimiento_adecuado", horizontal=True)

        observaciones = st.text_area("Observaciones adicionales", height=120, key="obs_pp",
                                     placeholder="Comentarios generales sobre el desempeño durante el período...")

        aprobo = st.radio("¿El evaluado aprobó el período de prueba?",
                          options=[True, False],
                          format_func=lambda x: "✅ SÍ, APROBÓ" if x else "❌ NO APROBÓ",
                          key="aprobo_pp", horizontal=True)

        submitted = st.form_submit_button("✅ Guardar Evaluación", use_container_width=True, type="primary")

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
            }
            db.save_results(session_id, results_to_save)
            db.complete_test_session(session_id)
            st.success("✅ Evaluación de período de prueba guardada correctamente.")
            st.session_state.pop("periodo_prueba_session_id", None)
            nav("admin_dashboard")
            st.rerun()

    if st.button("❌ Cancelar"):
        st.session_state.pop("periodo_prueba_session_id", None)
        nav("admin_dashboard")
        st.rerun()


def show_periodo_prueba_results_admin(results, candidate, session):
    """Muestra resultados de la evaluación de período de prueba en el panel de administración."""
    analysis = results.get("analysis", {})
    evaluador = results.get("evaluador", "N/A")
    aprobo = results.get("aprobo", False)
    session_id = session["id"] if isinstance(session, dict) else session

    # Banner de resultado
    clasif = analysis.get("clasificacion") or {}
    aprobacion_color = "#10B981" if aprobo else "#EF4444"
    aprobacion_text = "✅ APROBÓ EL PERÍODO DE PRUEBA" if aprobo else "❌ NO APROBÓ EL PERÍODO DE PRUEBA"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {aprobacion_color}22, {aprobacion_color}44);
                border-left: 6px solid {aprobacion_color}; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="margin:0; color:{aprobacion_color};">{aprobacion_text}</h2>
        <p style="margin:8px 0 0 0; font-size:15px; color:#374151;">{clasif.get('descripcion','')}</p>
        <p style="margin:12px 0 0 0; font-size:14px; color:#6B7280;">
            <b>Evaluador:</b> {evaluador} | <b>Clasificación:</b> {clasif.get('label','')} |
            <b>Promedio General:</b> {analysis.get('promedio_general', 0):.2f}/4.00
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("📝 Actuaciones", f"{analysis.get('promedio_actuaciones', 0):.2f}/4.00")
    col2.metric("⭐ Calificaciones", f"{analysis.get('promedio_calificaciones', 0):.2f}/5.00")
    col3.metric("⚠️ Llamados de atención", "Sí" if results.get("llamados_atencion") else "No")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📝 Actuaciones", "⭐ Calificaciones", "💡 Análisis"])

    with tab1:
        st.markdown(f"**Promedio de actuaciones:** {analysis.get('promedio_actuaciones', 0):.2f}/4.00")
        actuaciones_scores = {int(k): v for k, v in results.get("actuaciones_scores", {}).items()}
        for idx, actuacion in enumerate(PERIODO_PRUEBA_ACTUACIONES):
            score = actuaciones_scores.get(idx, 0)
            if score == 0:
                continue
            escala = PERIODO_PRUEBA_ESCALA_ACTUACIONES.get(score, {})
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{idx+1}.** {actuacion}")
            with c2:
                color = escala.get("color", "#6B7280")
                st.markdown(f"<div style='background:{color}22; padding:8px; border-radius:6px; text-align:center;'>"
                           f"<span style='font-size:12px; color:{color};'><b>{escala.get('label','')}</b></span></div>",
                           unsafe_allow_html=True)

    with tab2:
        st.markdown(f"**Promedio de calificaciones:** {analysis.get('promedio_calificaciones', 0):.2f}/5.00")
        calificaciones_scores = {int(k): v for k, v in results.get("calificaciones_scores", {}).items()}
        for idx, cal in enumerate(PERIODO_PRUEBA_CALIFICACIONES):
            score = calificaciones_scores.get(idx, 0)
            if score == 0:
                continue
            escala = PERIODO_PRUEBA_ESCALA_CALIFICACIONES.get(score, {})
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{cal}**")
            with c2:
                color = escala.get("color", "#6B7280")
                st.markdown(f"<div style='background:{color}22; padding:8px; border-radius:6px; text-align:center;'>"
                           f"<span style='font-size:12px; color:{color};'><b>{escala.get('label','')}</b></span></div>",
                           unsafe_allow_html=True)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            kon = results.get("conocimiento_adecuado", False)
            st.markdown(f"**¿Conocimiento adecua al perfil?** {'✅ Sí' if kon else '❌ No'}")
        with col_b:
            lam = results.get("llamados_atencion", False)
            st.markdown(f"**¿Llamados de atención?** {'⚠️ Sí' if lam else '✅ No'}")

        if results.get("observaciones"):
            st.markdown("---")
            st.markdown("**Observaciones adicionales:**")
            st.info(results["observaciones"])

    with tab3:
        st.markdown("#### 💡 Recomendaciones")
        for recom in analysis.get("recomendaciones", []):
            if aprobo:
                st.success(f"• {recom}")
            else:
                st.warning(f"• {recom}")

        if analysis.get("actuaciones_destacadas"):
            st.markdown("#### ✅ Comportamientos Destacados")
            for item in analysis["actuaciones_destacadas"]:
                st.success(f"• {item['nombre']}")

        if analysis.get("actuaciones_observacion"):
            st.markdown("#### ⚠️ Comportamientos a Reforzar")
            for item in analysis["actuaciones_observacion"]:
                st.warning(f"• {item['nombre']}")

    st.markdown("---")
    _col_pp1, _col_pp2 = st.columns(2)
    with _col_pp1:
        st.download_button(
            "📄 Descargar JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name=f"periodo_prueba_{candidate['cedula']}_{session_id}.json",
            mime="application/json",
            key=f"json_pp_{session_id}",
        )
    with _col_pp2:
        try:
            _pdf_pp = generate_periodo_prueba_pdf(
                candidate=candidate,
                actuaciones_scores={int(k): v for k, v in results.get("actuaciones_scores", {}).items()},
                calificaciones_scores={int(k): v for k, v in results.get("calificaciones_scores", {}).items()},
                session_id=session_id,
                completed_at=session.get("completed_at") if isinstance(session, dict) else None,
                analysis=analysis,
                evaluador_nombre=evaluador,
                aprobo=aprobo,
                llamados_atencion=results.get("llamados_atencion", False),
                conocimiento_adecuado=results.get("conocimiento_adecuado", True),
                observaciones=results.get("observaciones"),
            )
            st.download_button(
                "📑 Descargar PDF",
                data=_pdf_pp,
                file_name=f"periodo_prueba_{candidate['cedula']}_{session_id}.pdf",
                mime="application/pdf",
                key=f"pdf_pp_{session_id}",
            )
        except Exception as _pdf_err:
            st.warning(f"No se pudo generar el PDF: {_pdf_err}")


# -------------------------------------------------------------------------
# EVALUADOR/JEFE: LOGIN
# -------------------------------------------------------------------------

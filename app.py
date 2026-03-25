import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import os
import math
from io import BytesIO
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import database as db

# =========================================================================
# IMPORTAR MÓDULOS REFACTORIZADOS
# =========================================================================
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
    calculate_desempeno_results
)
from analysis import (
    analyze_disc_aptitude,
    analyze_valanti_aptitude,
    analyze_wpi_aptitude,
    analyze_eri_aptitude,
    analyze_talent_map_match
)
from utils import load_disc_questions, load_disc_descriptions, load_wpi_questions, nav

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
    .stApp { max-width: 1200px; margin: 0 auto; }
    .stButton>button { font-weight: bold; }
    div[data-testid="stMetric"] { background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# NOTA: Constantes y funciones movidas a módulos separados
# =========================================================================
# - constants.py: Todas las constantes (VALANTI, WPI, ERI, TALENT MAP, DESEMPEÑO, DISC)
# - calculations.py: Todas las funciones de cálculo
# - analysis.py: Todas las funciones de análisis
# - utils.py: Funciones auxiliares
# =========================================================================

# =========================================================================
# FUNCIONES DE GRÁFICOS
# =========================================================================

def create_disc_plot(normalized_score):
    categories = ["D", "I", "S", "C"]
    labels = ["D\nDominancia", "I\nInfluencia", "S\nEstabilidad", "C\nCumplimiento"]
    disc_colors = {"D": "#EF4444", "I": "#F59E0B", "S": "#10B981", "C": "#3B82F6"}
    
    # Gráfico de barras horizontales + radar pequeño
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [3, 2]})
    
    # --- Barras horizontales ---
    vals = [normalized_score.get(s, 0) for s in categories]
    colors = [disc_colors[s] for s in categories]
    bars = ax1.barh(labels, vals, color=colors, height=0.6, edgecolor='white', linewidth=1.5)
    
    for bar, val, cat in zip(bars, vals, categories):
        ax1.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2, 
                f"{val:.1f}%", va='center', fontweight='bold', fontsize=12, color=disc_colors[cat])
    
    ax1.set_xlim(0, 110)
    ax1.axvline(x=50, color='#94A3B8', linestyle='--', alpha=0.6, label='Promedio')
    ax1.set_title("Puntajes por Estilo DISC", fontsize=14, fontweight='bold', pad=15)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_color('#CBD5E1')
    ax1.spines['left'].set_color('#CBD5E1')
    ax1.tick_params(axis='y', labelsize=11)
    ax1.set_facecolor('#FAFBFC')
    ax1.legend(fontsize=9)
    
    # --- Radar ---
    angles = [7 * np.pi / 4, np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4]
    scaled = {s: v / 100 for s, v in normalized_score.items()}
    
    # Dibujar áreas por estilo
    ax2 = fig.add_subplot(122, projection='polar')
    ax2.set_theta_offset(np.pi / 2)
    ax2.set_theta_direction(-1)
    ax2.set_ylim(0, 1.01)
    
    for i, s in enumerate(categories):
        ax2.bar(angles[i], scaled[s], width=np.pi/2.5, alpha=0.35, color=disc_colors[s], edgecolor=disc_colors[s], linewidth=2)
    
    # Punto central del perfil
    x = sum(scaled[s] * np.cos(angles[i]) for i, s in enumerate(categories))
    y = sum(scaled[s] * np.sin(angles[i]) for i, s in enumerate(categories))
    mag = np.sqrt(x**2 + y**2)
    ang = np.arctan2(y, x)
    ax2.plot(ang, mag, "o", markersize=16, color="#1E293B", zorder=5)
    ax2.plot(ang, mag, "o", markersize=10, color="#FBBF24", zorder=6)
    
    ax2.set_xticks(angles)
    ax2.set_xticklabels(categories, fontsize=13, fontweight="bold")
    tick_colors = ['#EF4444', '#F59E0B', '#10B981', '#3B82F6']
    for label, color in zip(ax2.get_xticklabels(), tick_colors):
        label.set_color(color)
    ax2.set_yticklabels([])
    ax2.grid(True, alpha=0.2)
    ax2.spines["polar"].set_visible(False)
    ax2.set_facecolor('#FAFBFC')
    ax2.set_title("Perfil DISC", fontsize=13, fontweight='bold', pad=20)
    
    fig.patch.set_facecolor('white')
    plt.tight_layout()
    return fig


def create_behavioral_styles_chart(behavioral_styles):
    """
    Crea un gráfico de barras horizontales para los 9 estilos conductuales
    derivados del perfil DISC, con sus 4 sub-dimensiones cada uno.
    Inspirado en el modelo de reporte THT.
    """
    style_names = list(behavioral_styles.keys())
    disc_colors = {"D": "#EF4444", "I": "#F59E0B", "S": "#10B981", "C": "#3B82F6"}
    sub_order = ["D", "I", "S", "C"]  # orden estándar de sub-dimensiones

    # Mapeo de sub-dimensión → estilo DISC para colorear
    sub_to_disc_idx = {0: "D", 1: "I", 2: "S", 3: "C"}

    n_styles = len(style_names)
    fig, axes = plt.subplots(n_styles, 1, figsize=(12, n_styles * 1.6 + 1))
    fig.patch.set_facecolor('white')
    fig.suptitle("Estilos Conductuales Derivados del Perfil DISC", fontsize=14,
                 fontweight='bold', color='#1E293B', y=1.01)

    for ax_idx, (style_name, style_data) in enumerate(behavioral_styles.items()):
        ax = axes[ax_idx]
        subs = style_data["subs"]
        sub_names = list(subs.keys())
        sub_values = list(subs.values())
        colors = [disc_colors[sub_to_disc_idx[i]] for i in range(len(sub_names))]

        bars = ax.barh(sub_names, sub_values, color=colors, height=0.55,
                       edgecolor='white', linewidth=1.2)

        for bar, val, color in zip(bars, sub_values, colors):
            ax.text(min(val + 2, 102), bar.get_y() + bar.get_height() / 2,
                    f"{val}", va='center', fontweight='bold', fontsize=9, color=color)

        ax.set_xlim(0, 110)
        ax.axvline(x=50, color='#CBD5E1', linestyle='--', alpha=0.6, linewidth=0.8)

        # Fondo de la fila con color alternado
        ax.set_facecolor('#F8FAFC' if ax_idx % 2 == 0 else '#FFFFFF')

        # Título del estilo a la izquierda como etiqueta del eje y
        ax.set_title(f"  {ax_idx + 1}. {style_name}", fontsize=10, fontweight='bold',
                     color='#1E293B', loc='left', pad=4)

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#E2E8F0')
        ax.spines['left'].set_color('#E2E8F0')
        ax.tick_params(axis='y', labelsize=8.5, colors='#475569')
        ax.tick_params(axis='x', labelsize=7, colors='#94A3B8')
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xticklabels(['0', '25', '50', '75', '100'])

    plt.tight_layout(pad=1.2)
    return fig


def create_valanti_radar(standard_scores):
    cats = list(standard_scores.keys())
    vals = list(standard_scores.values()) + [list(standard_scores.values())[0]]
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist() + [0]
    
    valanti_radar_colors = ["#3B82F6", "#10B981", "#8B5CF6", "#EF4444", "#F59E0B"]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Línea principal con gradiente
    ax.plot(angles, vals, "o-", linewidth=2.5, color="#6366F1", markersize=10, 
            markerfacecolor="#818CF8", markeredgecolor="white", markeredgewidth=2, zorder=5)
    ax.fill(angles, vals, alpha=0.15, color="#6366F1")
    
    # Colorear cada punto según su valor
    for i, (angle, val) in enumerate(zip(angles[:-1], vals[:-1])):
        color = valanti_radar_colors[i]
        ax.plot(angle, val, "o", markersize=14, color=color, zorder=6, markeredgecolor='white', markeredgewidth=2)
        ax.text(angle, val + 6, str(val), ha='center', va='center', fontsize=10, fontweight='bold', color=color)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=12, fontweight="bold",
                       color='#1E293B')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 50, 60, 80])
    ax.set_yticklabels(['20', '40', '50', '60', '80'], fontsize=8, color='#94A3B8')
    
    # Línea de referencia promedio
    ref = [50] * (len(cats) + 1)
    ax.plot(angles, ref, "--", linewidth=1.5, color="#F59E0B", alpha=0.6, label="Promedio (50)")
    
    # Zonas de color
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, 40, alpha=0.05, color='#EF4444')  # zona baja
    ax.fill_between(theta, 55, 100, alpha=0.05, color='#10B981')  # zona alta
    
    ax.grid(True, alpha=0.2, color='#CBD5E1')
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    plt.title("Perfil Valoral - VALANTI", fontsize=15, fontweight="bold", pad=25, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=10)
    return fig


def create_valanti_bars(direct_scores, standard_scores):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('white')
    cats = list(direct_scores.keys())
    bar_colors = [VALANTI_COLORS[c] for c in cats]
    
    # --- Puntajes Directos ---
    dv = list(direct_scores.values())
    bars1 = ax1.bar(cats, dv, color=bar_colors, alpha=0.85, edgecolor='white', linewidth=1.5, width=0.6)
    ax1.set_title("Puntajes Directos", fontsize=13, fontweight="bold", color='#1E293B', pad=15)
    for b, v, c in zip(bars1, dv, bar_colors):
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, str(v), 
                ha="center", fontweight="bold", fontsize=12, color=c)
    ax1.set_ylim(0, max(dv) * 1.3 if max(dv) > 0 else 15)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_color('#CBD5E1')
    ax1.spines['left'].set_color('#CBD5E1')
    ax1.set_facecolor('#FAFBFC')
    ax1.tick_params(axis='x', labelsize=10)
    ax1.tick_params(axis='y', colors='#94A3B8')
    
    # --- Puntajes Estándar ---
    sv = list(standard_scores.values())
    bars2 = ax2.bar(cats, sv, color=bar_colors, alpha=0.85, edgecolor='white', linewidth=1.5, width=0.6)
    ax2.axhline(y=50, color="#F59E0B", linestyle="--", alpha=0.7, linewidth=1.5, label="Promedio (50)")
    ax2.axhspan(0, 40, alpha=0.04, color='#EF4444')  # zona baja
    ax2.axhspan(55, max(sv)*1.3 if max(sv) > 0 else 100, alpha=0.04, color='#10B981')  # zona alta
    ax2.set_title("Puntajes Estándar (Escala T)", fontsize=13, fontweight="bold", color='#1E293B', pad=15)
    for b, v, c in zip(bars2, sv, bar_colors):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, str(v), 
                ha="center", fontweight="bold", fontsize=12, color=c)
    ax2.set_ylim(0, max(sv) * 1.3 if max(sv) > 0 else 100)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['bottom'].set_color('#CBD5E1')
    ax2.spines['left'].set_color('#CBD5E1')
    ax2.set_facecolor('#FAFBFC')
    ax2.tick_params(axis='x', labelsize=10)
    ax2.tick_params(axis='y', colors='#94A3B8')
    ax2.legend(fontsize=10, loc='upper right')
    plt.tight_layout()
    return fig


def create_wpi_radar(normalized_scores):
    """
    Crea un gráfico de radar para visualizar las 6 dimensiones del WPI.
    
    Args:
        normalized_scores: Dict con puntajes normalizados (0-100) por dimensión
        
    Returns:
        matplotlib.figure.Figure: Gráfico de radar
    """
    # Preparar datos para el radar
    dimensions = WPI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    values_closed = values + [values[0]]  # Cerrar el polígono
    
    # Calcular ángulos para cada dimensión
    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    
    # Colores para cada dimensión
    dim_colors = [WPI_COLORS[dim] for dim in dimensions]
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    
    # Línea principal del perfil
    ax.plot(angles_closed, values_closed, "o-", linewidth=2.5, color="#6366F1", 
            markersize=8, markerfacecolor="#818CF8", markeredgecolor="white", 
            markeredgewidth=2, zorder=5)
    
    # Rellenar área
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#6366F1")
    
    # Puntos coloreados por dimensión con valores
    for i, (angle, val, color) in enumerate(zip(angles, values, dim_colors)):
        # Punto
        ax.plot(angle, val, "o", markersize=16, color=color, zorder=6, 
                markeredgecolor='white', markeredgewidth=2.5)
        # Valor del punto
        ax.text(angle, val + 7, f"{int(val)}", ha='center', va='center', 
                fontsize=11, fontweight='bold', color=color)
    
    # Configurar etiquetas de dimensiones
    ax.set_xticks(angles)
    ax.set_xticklabels(dimensions, fontsize=11, fontweight="bold", color='#1E293B')
    
    # Configurar escala radial
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9, color='#94A3B8')
    
    # Líneas de referencia
    ref_50 = [50] * (len(dimensions) + 1)
    ref_70 = [70] * (len(dimensions) + 1)
    ax.plot(angles_closed, ref_50, "--", linewidth=1.5, color="#F59E0B", 
            alpha=0.6, label="Promedio (50)")
    ax.plot(angles_closed, ref_70, ":", linewidth=1.5, color="#10B981", 
            alpha=0.6, label="Alto (70)")
    
    # Zonas de color de fondo
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, 45, alpha=0.04, color='#EF4444')   # zona baja (rojo)
    ax.fill_between(theta, 70, 100, alpha=0.05, color='#10B981') # zona alta (verde)
    
    # Estilo del gráfico
    ax.grid(True, alpha=0.3, color='#CBD5E1', linestyle='-', linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    
    # Título y leyenda
    plt.title("Perfil de Personalidad Laboral - WPI", fontsize=16, fontweight="bold", 
              pad=30, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=10)
    
    plt.tight_layout()
    return fig


def create_wpi_bars(normalized_scores):
    """
    Crea un gráfico de barras horizontales para visualizar las dimensiones del WPI.
    
    Args:
        normalized_scores: Dict con puntajes normalize (0-100) por dimensión
        
    Returns:
        matplotlib.figure.Figure: Gráfico de barras horizontales
    """
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor('white')
    
    dimensions = WPI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    colors = [WPI_COLORS[dim] for dim in dimensions]
    
    # Crear barras horizontales (de abajo hacia arriba)
    y_positions = np.arange(len(dimensions))
    bars = ax.barh(y_positions, values, color=colors, alpha=0.85, 
                   edgecolor='white', linewidth=2, height=0.7)
    
    # Agregar valores al final de cada barra
    for i, (bar, val, color) in enumerate(zip(bars, values, colors)):
        ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}/100", 
                va='center', fontweight='bold', fontsize=12, color=color)
    
    # Líneas de referencia verticales
    ax.axvline(x=50, color="#F59E0B", linestyle="--", alpha=0.7, linewidth=2, 
               label="Promedio (50)")
    ax.axvline(x=70, color="#10B981", linestyle=":", alpha=0.7, linewidth=2, 
               label="Alto (70)")
    
    # Zonas de color de fondo
    ax.axvspan(0, 45, alpha=0.05, color='#EF4444')   # zona baja
    ax.axvspan(70, 100, alpha=0.05, color='#10B981') # zona alta
    
    # Configuración de ejes
    ax.set_yticks(y_positions)
    ax.set_yticklabels(dimensions, fontsize=12, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Puntaje (0-100)', fontsize=12, fontweight='bold', color='#475569')
    ax.set_xlim(0, 105)
    ax.set_ylim(-0.5, len(dimensions) - 0.5)
    
    # Título
    ax.set_title("Dimensiones de Personalidad Laboral", fontsize=14, 
                 fontweight="bold", pad=20, color='#1E293B')
    
    # Estilo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='x', colors='#94A3B8')
    ax.tick_params(axis='y', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    
    # Leyenda
    ax.legend(fontsize=10, loc='lower right', framealpha=0.95)
    
    plt.tight_layout()
    return fig


def create_eri_radar(normalized_scores):
    """
    Crea un gráfico de radar para visualizar las 6 dimensiones del ERI.
    IMPORTANTE: Valores altos = BAJO riesgo (verde), valores bajos = ALTO riesgo (rojo)
    
    Args:
        normalized_scores: Dict con puntajes normalizados (0-100) por dimensión (100 = bajo riesgo)
        
    Returns:
        matplotlib.figure.Figure: Gráfico de radar
    """
    # Preparar datos para el radar
    dimensions = ERI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    values_closed = values + [values[0]]  # Cerrar el polígono
    
    # Calcular ángulos para cada dimensión
    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    
    # Colores para cada dimensión
    dim_colors = [ERI_COLORS[dim] for dim in dimensions]
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Línea principal del perfil
    ax.plot(angles_closed, values_closed, "o-", linewidth=3, color="#6366F1", 
            markersize=10, markerfacecolor="#818CF8", markeredgecolor="white", 
            markeredgewidth=2.5, zorder=5)
    
    # Rellenar área
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#6366F1")
    
    # Puntos coloreados por dimensión con valores
    for i, (angle, val, color) in enumerate(zip(angles, values, dim_colors)):
        # Determinar riesgo por color del punto
        if val >= ERI_RISK_THRESHOLDS["low_risk"]:
            point_color = "#10B981"  # Verde - Bajo riesgo
        elif val >= ERI_RISK_THRESHOLDS["medium_risk"]:
            point_color = "#F59E0B"  # Amarillo - Riesgo moderado
        else:
            point_color = "#EF4444"  # Rojo - Alto riesgo
        
        # Punto
        ax.plot(angle, val, "o", markersize=18, color=point_color, zorder=6, 
                markeredgecolor='white', markeredgewidth=3)
        # Valor del punto
        ax.text(angle, val + 7, f"{int(val)}", ha='center', va='center', 
                fontsize=12, fontweight='bold', color=point_color)
    
    # Configurar etiquetas de dimensiones con ajuste de tamaño
    ax.set_xticks(angles)
    labels = []
    for dim in dimensions:
        # Dividir nombres largos en dos líneas
        if len(dim) > 15:
            words = dim.split()
            if len(words) >= 2:
                mid = len(words) // 2
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                labels.append(f"{line1}\n{line2}")
            else:
                labels.append(dim)
        else:
            labels.append(dim)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold", color='#1E293B')
    
    # Configurar escala radial
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 66, 80, 100])
    ax.set_yticklabels(['20', '40', '66\n(Umbral)', '80', '100'], fontsize=9, color='#94A3B8')
    
    # Líneas de referencia (umbrales de riesgo)
    ref_low_risk = [ERI_RISK_THRESHOLDS["low_risk"]] * (len(dimensions) + 1)
    ref_medium_risk = [ERI_RISK_THRESHOLDS["medium_risk"]] * (len(dimensions) + 1)
    
    ax.plot(angles_closed, ref_low_risk, "-", linewidth=2, color="#10B981", 
            alpha=0.7, label="Bajo Riesgo (≥66)")
    ax.plot(angles_closed, ref_medium_risk, "--", linewidth=2, color="#F59E0B", 
            alpha=0.7, label="Riesgo Moderado (≥41)")
    
    # Zonas de color de fondo (invertidas: alto score = bajo riesgo)
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, ERI_RISK_THRESHOLDS["medium_risk"], 
                     alpha=0.08, color='#EF4444')  # zona alto riesgo (rojo)
    ax.fill_between(theta, ERI_RISK_THRESHOLDS["medium_risk"], ERI_RISK_THRESHOLDS["low_risk"], 
                     alpha=0.06, color='#F59E0B')  # zona riesgo moderado (amarillo)
    ax.fill_between(theta, ERI_RISK_THRESHOLDS["low_risk"], 100, 
                     alpha=0.08, color='#10B981')  # zona bajo riesgo (verde)
    
    # Estilo del gráfico
    ax.grid(True, alpha=0.3, color='#CBD5E1', linestyle='-', linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    
    # Título y leyenda
    plt.title("Perfil de Riesgo e Integridad - ERI\n(Puntajes altos = BAJO riesgo)", 
              fontsize=16, fontweight="bold", pad=35, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
    
    plt.tight_layout()
    return fig


def create_eri_bars(normalized_scores):
    """
    Crea un gráfico de barras horizontales para visualizar las dimensiones del ERI con zonas de riesgo.
    IMPORTANTE: Valores altos = BAJO riesgo (verde), valores bajos = ALTO riesgo (rojo)
    
    Args:
        normalized_scores: Dict con puntajes normalizados (0-100) por dimensión (100 = bajo riesgo)
        
    Returns:
        matplotlib.figure.Figure: Gráfico de barras horizontales
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('white')
    
    dimensions = ERI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    
    # Colores de barras según nivel de riesgo
    colors = []
    for val in values:
        if val >= ERI_RISK_THRESHOLDS["low_risk"]:
            colors.append("#10B981")  # Verde - Bajo riesgo
        elif val >= ERI_RISK_THRESHOLDS["medium_risk"]:
            colors.append("#F59E0B")  # Amarillo - Riesgo moderado
        else:
            colors.append("#EF4444")  # Rojo - Alto riesgo
    
    # Crear barras horizontales (de abajo hacia arriba)
    y_positions = np.arange(len(dimensions))
    bars = ax.barh(y_positions, values, color=colors, alpha=0.85, 
                   edgecolor='white', linewidth=2.5, height=0.7)
    
    # Agregar valores al final de cada barra con etiqueta de riesgo
    for i, (bar, val, color) in enumerate(zip(bars, values, colors)):
        if val >= ERI_RISK_THRESHOLDS["low_risk"]:
            risk_label = "✅ Bajo Riesgo"
        elif val >= ERI_RISK_THRESHOLDS["medium_risk"]:
            risk_label = "⚠️ Moderado"
        else:
            risk_label = "🚨 Alto Riesgo"
        
        ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}  {risk_label}", 
                va='center', fontweight='bold', fontsize=11, color=color)
    
    # Líneas de referencia verticales (umbrales)
    ax.axvline(x=ERI_RISK_THRESHOLDS["low_risk"], color="#10B981", linestyle="-", 
               alpha=0.8, linewidth=2.5, label="Bajo Riesgo (≥66)")
    ax.axvline(x=ERI_RISK_THRESHOLDS["medium_risk"], color="#F59E0B", linestyle="--", 
               alpha=0.8, linewidth=2.5, label="Riesgo Moderado (≥41)")
    
    # Zonas de color de fondo
    ax.axvspan(0, ERI_RISK_THRESHOLDS["medium_risk"], alpha=0.08, color='#EF4444')  # Alto riesgo
    ax.axvspan(ERI_RISK_THRESHOLDS["medium_risk"], ERI_RISK_THRESHOLDS["low_risk"], 
               alpha=0.06, color='#F59E0B')  # Riesgo moderado
    ax.axvspan(ERI_RISK_THRESHOLDS["low_risk"], 100, alpha=0.08, color='#10B981')  # Bajo riesgo
    
    # Configuración de ejes
    ax.set_yticks(y_positions)
    ax.set_yticklabels(dimensions, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Puntaje (0-100) - Mayor puntaje = MENOR riesgo', fontsize=12, 
                  fontweight='bold', color='#475569')
    ax.set_xlim(0, 110)
    ax.set_ylim(-0.5, len(dimensions) - 0.5)
    
    # Título
    ax.set_title("Evaluación de Riesgo e Integridad por Dimensión", fontsize=15, 
                 fontweight="bold", pad=20, color='#1E293B')
    
    # Estilo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='x', colors='#94A3B8')
    ax.tick_params(axis='y', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    
    # Leyenda
    ax.legend(fontsize=11, loc='lower right', framealpha=0.95)
    
    plt.tight_layout()
    return fig


def create_talent_map_radar(normalized_scores, job_profile_scores=None):
    """
    Crea un gráfico de radar para visualizar las 8 competencias del Talent Map.
    Opcionalmente muestra overlay con perfil de puesto para comparación.
    
    Args:
        normalized_scores: Dict con puntajes del candidato (0-100) por competencia
        job_profile_scores: Dict opcional con puntajes del perfil de puesto para comparar
        
    Returns:
        matplotlib.figure.Figure: Gráfico de radar
    """
    # Preparar datos para el radar
    competencies = TALENT_MAP_COMPETENCIES
    values = [normalized_scores[comp] for comp in competencies]
    values_closed = values + [values[0]]  # Cerrar el polígono
    
    # Calcular ángulos para cada competencia
    angles = np.linspace(0, 2 * np.pi, len(competencies), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(polar=True))
    
    # Línea principal del perfil del candidato
    ax.plot(angles_closed, values_closed, "o-", linewidth=3.5, color="#6366F1", 
            markersize=12, markerfacecolor="#818CF8", markeredgecolor="white", 
            markeredgewidth=3, zorder=5, label="Candidato")
    
    # Rellenar área del candidato
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#6366F1")
    
    # Si hay perfil de puesto, agregarlo como comparación
    if job_profile_scores:
        profile_values = [job_profile_scores[comp] for comp in competencies]
        profile_values_closed = profile_values + [profile_values[0]]
        
        ax.plot(angles_closed, profile_values_closed, "s--", linewidth=2.5, color="#EF4444", 
                markersize=8, markerfacecolor="#FCA5A5", markeredgecolor="white", 
                markeredgewidth=2, zorder=4, label="Perfil Requerido", alpha=0.8)
        ax.fill(angles_closed, profile_values_closed, alpha=0.15, color="#EF4444")
    
    # Puntos coloreados por competencia con valores
    for i, (angle, val) in enumerate(zip(angles, values)):
        comp = competencies[i]
        point_color = TALENT_MAP_COLORS[comp]
        
        # Punto
        ax.plot(angle, val, "o", markersize=16, color=point_color, zorder=6, 
                markeredgecolor='white', markeredgewidth=2.5)
        # Valor del punto
        ax.text(angle, val + 6, f"{int(val)}", ha='center', va='center', 
                fontsize=11, fontweight='bold', color=point_color)
    
    # Configurar etiquetas de competencias con ajuste de tamaño
    ax.set_xticks(angles)
    labels = []
    for comp in competencies:
        # Dividir nombres largos en dos líneas
        if len(comp) > 15:
            words = comp.split()
            if len(words) >= 2:
                mid = len(words) // 2
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                labels.append(f"{line1}\n{line2}")
            else:
                labels.append(comp)
        else:
            labels.append(comp)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold", color='#1E293B')
    
    # Configurar escala radial
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25', '50\n(Promedio)', '75', '100'], fontsize=9, color='#94A3B8')
    
    # Líneas de referencia
    ref_levels = [[50] * (len(competencies) + 1), [75] * (len(competencies) + 1)]
    ax.plot(angles_closed, ref_levels[0], ":", linewidth=1.5, color="#94A3B8", 
            alpha=0.6, label="Nivel Promedio (50)")
    ax.plot(angles_closed, ref_levels[1], "--", linewidth=1.5, color="#10B981", 
            alpha=0.6, label="Nivel Alto (75)")
    
    # Zonas de color de fondo
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, 50, alpha=0.05, color='#EF4444')  # zona baja
    ax.fill_between(theta, 50, 75, alpha=0.05, color='#F59E0B')  # zona media
    ax.fill_between(theta, 75, 100, alpha=0.08, color='#10B981')  # zona alta
    
    # Estilo del gráfico
    ax.grid(True, alpha=0.3, color='#CBD5E1', linestyle='-', linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    
    # Título y leyenda
    title = "Mapeo de Competencias y Talentos"
    if job_profile_scores:
        title += "\n(Candidato vs. Perfil Requerido)"
    plt.title(title, fontsize=16, fontweight="bold", pad=40, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=11)
    
    plt.tight_layout()
    return fig


def create_talent_map_bars(normalized_scores, job_profile_scores=None):
    """
    Crea un gráfico de barras horizontales para visualizar las competencias del Talent Map.
    Opcionalmente incluye barras del perfil de puesto para comparación.
    
    Args:
        normalized_scores: Dict con puntajes del candidato (0-100) por competencia
        job_profile_scores: Dict opcional con puntajes del perfil de puesto
        
    Returns:
        matplotlib.figure.Figure: Gráfico de barras horizontales
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('white')
    
    competencies = TALENT_MAP_COMPETENCIES
    values = [normalized_scores[comp] for comp in competencies]
    
    # Si hay perfil de puesto, crear barras agrupadas
    y_positions = np.arange(len(competencies))
    bar_height = 0.35 if job_profile_scores else 0.7
    
    # Colores de barras según nivel
    colors = []
    for val in values:
        if val >= 75:
            colors.append("#10B981")  # Verde - Alto
        elif val >= 50:
            colors.append("#F59E0B")  # Amarillo - Medio
        else:
            colors.append("#EF4444")  # Rojo - Bajo
    
    # Crear barras del candidato
    if job_profile_scores:
        bars1 = ax.barh(y_positions - bar_height/2, values, bar_height, 
                       color=colors, alpha=0.85, edgecolor='white', 
                       linewidth=2, label="Candidato")
        
        # Barras del perfil requerido
        profile_values = [job_profile_scores[comp] for comp in competencies]
        bars2 = ax.barh(y_positions + bar_height/2, profile_values, bar_height, 
                       color="#94A3B8", alpha=0.7, edgecolor='white', 
                       linewidth=2, label="Perfil Requerido")
        
        # Agregar valores en las barras
        for bar, val in zip(bars1, values):
            ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}", 
                    va='center', fontweight='bold', fontsize=10, color='#1E293B')
        
        for bar, val in zip(bars2, profile_values):
            ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}", 
                    va='center', fontweight='bold', fontsize=10, color='#64748B')
    else:
        bars = ax.barh(y_positions, values, bar_height, color=colors, 
                      alpha=0.85, edgecolor='white', linewidth=2.5)
        
        # Agregar valores y nivel al final de cada barra
        for i, (bar, val, color) in enumerate(zip(bars, values, colors)):
            if val >= 75:
                level_label = "🌟 Alto"
            elif val >= 50:
                level_label = "👍 Medio"
            else:
                level_label = "📈 En Desarrollo"
            
            ax.text(val + 2, bar.get_y() + bar.get_height()/2, 
                    f"{int(val)}  {level_label}", 
                    va='center', fontweight='bold', fontsize=11, color=color)
    
    # Líneas de referencia verticales
    ax.axvline(x=50, color="#94A3B8", linestyle=":", alpha=0.6, linewidth=2, 
               label="Nivel Promedio (50)")
    ax.axvline(x=75, color="#10B981", linestyle="--", alpha=0.7, linewidth=2, 
               label="Nivel Alto (75)")
    
    # Zonas de color de fondo
    ax.axvspan(0, 50, alpha=0.05, color='#EF4444')  # Bajo
    ax.axvspan(50, 75, alpha=0.05, color='#F59E0B')  # Medio
    ax.axvspan(75, 100, alpha=0.08, color='#10B981')  # Alto
    
    # Configuración de ejes
    ax.set_yticks(y_positions)
    ax.set_yticklabels(competencies, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Puntuación (0-100)', fontsize=12, fontweight='bold', color='#475569')
    ax.set_xlim(0, 110)
    ax.set_ylim(-0.5, len(competencies) - 0.5)
    
    # Título
    title = "Evaluación de Competencias por Dimensión"
    if job_profile_scores:
        title += "\n(Candidato vs. Perfil Requerido)"
    ax.set_title(title, fontsize=15, fontweight="bold", pad=20, color='#1E293B')
    
    # Estilo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='x', colors='#94A3B8')
    ax.tick_params(axis='y', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    
    # Leyenda
    ax.legend(fontsize=11, loc='lower right', framealpha=0.95)
    
    plt.tight_layout()
    return fig


def create_talent_map_comparison(normalized_scores, job_profile_name, job_profile_scores):
    """
    Crea un gráfico de comparación detallada mostrando gaps y strengths vs perfil de puesto.
    
    Args:
        normalized_scores: Dict con puntajes del candidato
        job_profile_name: Nombre del perfil de puesto
        job_profile_scores: Dict con puntajes del perfil
        
    Returns:
        matplotlib.figure.Figure: Gráfico de comparación de gaps
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('white')
    
    competencies = TALENT_MAP_COMPETENCIES
    gaps = []
    gap_colors = []
    
    # Calcular gaps (positivo = excede, negativo = deficit)
    for comp in competencies:
        candidate = normalized_scores[comp]
        required = job_profile_scores[comp]
        gap = candidate - required
        gaps.append(gap)
        
        # Color según gap
        if gap >= 0:
            gap_colors.append("#10B981")  # Verde - Excede o cumple
        elif gap >= -15:
            gap_colors.append("#F59E0B")  # Amarillo - Gap moderado
        else:
            gap_colors.append("#EF4444")  # Rojo - Gap significativo
    
    # Crear barras de gap
    y_positions = np.arange(len(competencies))
    bars = ax.barh(y_positions, gaps, color=gap_colors, alpha=0.85, 
                   edgecolor='white', linewidth=2.5, height=0.7)
    
    # Agregar valores y etiquetas
    for i, (bar, gap) in enumerate(zip(bars, gaps)):
        comp = competencies[i]
        candidate_score = normalized_scores[comp]
        required_score = job_profile_scores[comp]
        
        # Texto del gap
        gap_text = f"{gap:+.0f}"
        if gap >= 0:
            label = f"{gap_text}  ✅ Excede"
            x_pos = gap + 2
        elif gap >= -15:
            label = f"{gap_text}  ⚠️ Gap moderado"
            x_pos = gap - 2
        else:
            label = f"{gap_text}  🚨 Gap crítico"
            x_pos = gap - 2
        
        ha = 'left' if gap >= 0 else 'right'
        ax.text(x_pos, bar.get_y() + bar.get_height()/2, label, 
                va='center', ha=ha, fontweight='bold', fontsize=10, 
                color=gap_colors[i])
        
        # Texto de puntajes (candidato vs requerido)
        score_text = f"Candidato: {candidate_score:.0f}  |  Requerido: {required_score:.0f}"
        ax.text(-42, bar.get_y() + bar.get_height()/2, score_text, 
                va='center', ha='left', fontsize=9, color='#64748B', style='italic')
    
    # Línea de referencia (gap = 0)
    ax.axvline(x=0, color='#1E293B', linestyle='-', linewidth=2.5, alpha=0.8)
    
    # Configuración de ejes
    ax.set_yticks(y_positions)
    ax.set_yticklabels(competencies, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Gap de Competencia (Candidato - Requerido)', fontsize=12, 
                  fontweight='bold', color='#475569')
    
    # Ajustar límites del eje X
    max_abs_gap = max(abs(min(gaps)), abs(max(gaps)))
    ax.set_xlim(-max_abs_gap - 20, max_abs_gap + 20)
    ax.set_ylim(-0.5, len(competencies) - 0.5)
    
    # Título
    profile_info = TALENT_MAP_JOB_PROFILES[job_profile_name]
    title = f"Análisis de Brechas vs. {profile_info['emoji']} {job_profile_name}\n{profile_info['descripcion']}"
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20, color='#1E293B')
    
    # Estilo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='both', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    
    plt.tight_layout()
    return fig


def create_desempeno_radar(potencial_scores):
    """Crea radar chart para las 5 dimensiones de potencial."""
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='polar')
    
    # Datos
    dimensiones = [dim["nombre"] for dim in DESEMPENO_DIMENSIONES]
    valores = [potencial_scores.get(i+1, 0) for i in range(5)]
    
    # Cerrar el polígono
    valores_plot = valores + [valores[0]]
    
    # Ángulos
    angulos = [n / 5 * 2 * np.pi for n in range(5)]
    angulos_plot = angulos + [angulos[0]]
    
    # Dibujar área
    ax.plot(angulos_plot, valores_plot, 'o-', linewidth=2.5, color='#3B82F6', markersize=8)
    ax.fill(angulos_plot, valores_plot, alpha=0.25, color='#3B82F6')
    
    # Zonas de fondo (0-1: rojo, 1-2: amarillo, 2-3: verde)
    for level, color, alpha in [(1, '#FEE2E2', 0.3), (2, '#FEF3C7', 0.3), (3, '#D1FAE5', 0.3)]:
        circle_angles = np.linspace(0, 2 * np.pi, 100)
        circle_values = [level] * 100
        ax.fill(circle_angles, circle_values, color=color, alpha=alpha)
    
    # Configuración
    ax.set_ylim(0, 3)
    ax.set_xticks(angulos)
    ax.set_xticklabels(dimensiones, size=11, fontweight='bold', color='#1E293B')
    ax.set_yticks([0.5, 1, 1.5, 2, 2.5, 3])
    ax.set_yticklabels(['', '1', '', '2', '', '3'], size=10, color='#64748B')
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.grid(True, color='#CBD5E1', linestyle='-', linewidth=0.5, alpha=0.7)
    ax.set_facecolor('#FFFFFF')
    
    # Título
    ax.set_title('Evaluación de Potencial\n5 Dimensiones', size=14, fontweight='bold', 
                 pad=30, color='#1E293B')
    
    plt.tight_layout()
    return fig


def create_desempeno_bars(rendimiento_scores):
    """Crea gráfico de barras para los 6 objetivos de rendimiento."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Datos
    objetivos = [obj["titulo"] for obj in DESEMPENO_OBJETIVOS]
    valores = [rendimiento_scores.get(i+1, 0) for i in range(6)]
    
    # Colores según nivel
    colores = []
    for valor in valores:
        if valor >= 4.5:
            colores.append('#10B981')  # Verde
        elif valor >= 3.5:
            colores.append('#3B82F6')  # Azul
        elif valor >= 2.5:
            colores.append('#F59E0B')  # Amarillo
        elif valor >= 1.5:
            colores.append('#EF4444')  # Rojo
        else:
            colores.append('#991B1B')  # Rojo oscuro
    
    # Crear barras horizontales
    y_positions = range(len(objetivos))
    bars = ax.barh(y_positions, valores, color=colores, alpha=0.8, height=0.6, 
                   edgecolor='#1E293B', linewidth=1.5)
    
    # Agregar valores en las barras
    for i, (bar, valor) in enumerate(zip(bars, valores)):
        label = DESEMPENO_ESCALA_RENDIMIENTO[int(valor)]["label"]
        ax.text(valor + 0.15, bar.get_y() + bar.get_height()/2, 
                f'{valor:.1f} - {label}', 
                va='center', ha='left', fontsize=10, fontweight='bold', color='#1E293B')
    
    # Zonas de fondo
    ax.axvspan(0, 1.5, alpha=0.1, color='#EF4444', label='Insatisfactorio')
    ax.axvspan(1.5, 2.5, alpha=0.1, color='#F59E0B', label='Debajo')
    ax.axvspan(2.5, 3.5, alpha=0.1, color='#3B82F6', label='Cumple')
    ax.axvspan(3.5, 5, alpha=0.1, color='#10B981', label='Supera/Sobresaliente')
    
    # Configuración
    ax.set_yticks(y_positions)
    ax.set_yticklabels(objetivos, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Calificación (1-5)', fontsize=12, fontweight='bold', color='#475569')
    ax.set_xlim(0, 5.5)
    ax.set_title('Evaluación de Rendimiento\n6 Objetivos de Desempeño', 
                 fontsize=14, fontweight='bold', pad=20, color='#1E293B')
    
    # Estilo
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='both', colors='#475569')
    ax.grid(axis='x', alpha=0.3, color='#CBD5E1', linestyle='--')
    ax.legend(loc='lower right', fontsize=9, framealpha=0.9)
    
    plt.tight_layout()
    return fig


# =========================================================================
# TIMER (JavaScript countdown)
# =========================================================================

def render_timer(deadline_ts, session_id):
    """Render a real-time JavaScript countdown timer."""
    html = f"""
    <div id="timer-box" style="
        display: flex; align-items: center; justify-content: center; gap: 12px;
        background: linear-gradient(135deg, #1e40af, #3b82f6); color: white;
        padding: 14px 24px; border-radius: 12px; font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 4px 12px rgba(30,64,175,0.3); margin-bottom: 8px;">
        <span style="font-size: 16px;">⏱️ Tiempo restante:</span>
        <span id="countdown" style="font-size: 28px; font-weight: bold; font-family: monospace; letter-spacing: 2px;">--:--</span>
        <span style="font-size: 12px; opacity: 0.8;">ID: {session_id}</span>
    </div>
    <script>
    var deadline = new Date({deadline_ts * 1000});
    function updateTimer() {{
        var now = new Date();
        var remaining = deadline - now;
        var box = document.getElementById("timer-box");
        var cd = document.getElementById("countdown");
        if (remaining <= 0) {{
            cd.textContent = "⏰ TIEMPO AGOTADO";
            box.style.background = "linear-gradient(135deg, #dc2626, #ef4444)";
        }} else {{
            var hrs = Math.floor(remaining / 3600000);
            var mins = Math.floor((remaining % 3600000) / 60000);
            var secs = Math.floor((remaining % 60000) / 1000);
            var display = "";
            if (hrs > 0) display = String(hrs).padStart(2,"0") + ":";
            display += String(mins).padStart(2,"0") + ":" + String(secs).padStart(2,"0");
            cd.textContent = display;
            if (remaining < 300000) {{
                box.style.background = "linear-gradient(135deg, #dc2626, #f59e0b)";
            }} else if (remaining < 600000) {{
                box.style.background = "linear-gradient(135deg, #f59e0b, #eab308)";
            }}
        }}
    }}
    updateTimer();
    setInterval(updateTimer, 1000);
    </script>
    """
    components.html(html, height=65)


# =========================================================================
# PDF GENERATION
# =========================================================================

def generate_disc_pdf(candidate, normalized, relative, fig, session_id, completed_at=None, analysis=None,
                      behavioral_styles=None, temperament=None, mega_summary=None, styles_fig=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    story = []
    story.append(Paragraph("Evaluación de Personalidad DISC - Reporte", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']} (Cédula: {candidate['cedula']})", styles["Normal"]))
    
    # Formatear la fecha de presentación
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            fecha_str = completed_at
    else:
        fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position','N/A')} | <b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    
    # Generar análisis si no se proporcionó
    if analysis is None:
        analysis = analyze_disc_aptitude(normalized, relative)
    
    # Sección de aptitud
    story.append(Spacer(1, 12))
    apt_color = analysis['aptitude_color']
    story.append(Paragraph(f"<b>RESULTADO DE APTITUD: {analysis['aptitude_level']} ({analysis['aptitude_score']}/100)</b>", styles["Heading2"]))
    story.append(Paragraph(f"{analysis['aptitude_desc']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Perfil:</b> {analysis['profile_name']} ({analysis['dominant_name']} + {analysis['secondary_name']})", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    # Tabla de puntajes
    data = [["Estilo", "Puntaje Normalizado", "Porcentaje Relativo"]]
    for s in "DISC":
        data.append([s, f"{normalized[s]:.1f}%", f"{relative[s]:.1f}%"])
    t = Table(data, colWidths=[100, 150, 150])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    if fig:
        img_buf = BytesIO()
        fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=280, height=280))
    
    # Página de recomendaciones
    story.append(PageBreak())
    story.append(Paragraph("Análisis y Recomendaciones", styles["Heading1"]))
    story.append(Spacer(1, 10))
    
    # Fortalezas
    story.append(Paragraph("FORTALEZAS DEL CANDIDATO", styles["Heading2"]))
    for f in analysis.get('fortalezas', []):
        story.append(Paragraph(f"• {f}", styles["Small"]))
    story.append(Spacer(1, 10))
    
    # Alertas
    story.append(Paragraph("ALERTAS Y ÁREAS DE ATENCIÓN", styles["Heading2"]))
    for a in analysis.get('alertas', []):
        story.append(Paragraph(f"• {a}", styles["Small"]))
    story.append(Spacer(1, 10))
    
    # Recomendaciones
    story.append(Paragraph("RECOMENDACIONES", styles["Heading2"]))
    for r in analysis.get('recomendaciones', []):
        story.append(Paragraph(f"• {r}", styles["Small"]))
    story.append(Spacer(1, 10))
    
    # Roles ideales
    if analysis.get('ideal_para'):
        story.append(Paragraph("ROLES IDEALES", styles["Heading2"]))
        for r in analysis['ideal_para']:
            story.append(Paragraph(f"• {r}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    if analysis.get('cuidado_en'):
        story.append(Paragraph("PRECAUCIÓN EN ROLES DE", styles["Heading2"]))
        for r in analysis['cuidado_en']:
            story.append(Paragraph(f"• {r}", styles["Small"]))

    # ── MEGA RESUMEN CONDUCTUAL ──────────────────────────────────────────
    if mega_summary:
        story.append(PageBreak())
        story.append(Paragraph("Resumen Conductual Detallado", styles["Heading1"]))
        story.append(Spacer(1, 8))
        if temperament:
            story.append(Paragraph(
                f"<b>Temperamento:</b> {temperament['label'].capitalize()} — {temperament['description']}",
                styles["Normal"]
            ))
            story.append(Spacer(1, 8))
        data_rows = [["Dimensión", "Descripción Conductual"]]
        for label, text in mega_summary.items():
            data_rows.append([label, text])
        t_sum = Table(data_rows, colWidths=[130, 360])
        t_sum.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 1), (0, -1), colors.HexColor("#1e40af")),
        ]))
        story.append(t_sum)

    # ── ESTILOS CONDUCTUALES ─────────────────────────────────────────────
    if behavioral_styles:
        story.append(PageBreak())
        story.append(Paragraph("9 Estilos Conductuales Derivados", styles["Heading1"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Puntajes derivados matemáticamente del perfil DISC. Cada estilo presenta 4 sub-dimensiones "
            "mapeadas a Dominancia (D), Influencia (I), Estabilidad (S) y Cumplimiento (C).",
            styles["Small"]
        ))
        story.append(Spacer(1, 10))

        if styles_fig:
            try:
                styles_buf = BytesIO()
                styles_fig.savefig(styles_buf, format="png", dpi=130, bbox_inches="tight")
                styles_buf.seek(0)
                story.append(Image(styles_buf, width=480, height=len(behavioral_styles) * 55 + 30))
            except Exception:
                pass
        
        story.append(Spacer(1, 12))
        for style_name, style_data in behavioral_styles.items():
            story.append(Paragraph(f"<b>{style_name}</b>", styles["Heading3"]))
            sub_data = [["Sub-dimensión", "Puntaje", "Descripción"]]
            for sub_name, sub_val in style_data["subs"].items():
                sub_data.append([sub_name, str(sub_val), style_data["desc"][sub_name]])
            t_sub = Table(sub_data, colWidths=[110, 45, 335])
            t_sub.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F9FAFB"), colors.white]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t_sub)
            story.append(Spacer(1, 8))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Este reporte es generado automáticamente como herramienta de apoyo para Recursos Humanos. Los resultados deben complementarse con entrevistas y otras evaluaciones.</i>", styles["Small"]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_valanti_pdf(candidate, direct, standard, radar_fig, session_id, completed_at=None, analysis=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    story = []
    story.append(Paragraph("Cuestionario VALANTI - Reporte de Resultados", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']} (Cédula: {candidate['cedula']})", styles["Normal"]))
    
    # Formatear la fecha de presentación
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            fecha_str = completed_at
    else:
        fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position','N/A')} | <b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    
    # Generar análisis si no se proporcionó
    if analysis is None:
        analysis = analyze_valanti_aptitude(standard)
    
    # Sección de aptitud
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>RESULTADO DE APTITUD: {analysis['aptitude_level']} ({analysis['aptitude_score']}/100)</b>", styles["Heading2"]))
    story.append(Paragraph(f"{analysis['aptitude_desc']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Valor más fuerte:</b> {analysis['strongest_value']} (T={analysis['strongest_score']}) | <b>Valor más bajo:</b> {analysis['weakest_value']} (T={analysis['weakest_score']})", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    # Tabla de puntajes
    data = [["Valor", "Puntaje Directo", "Puntaje Estándar (T)"]]
    for trait in VALANTI_TRAITS:
        data.append([trait, str(direct[trait]), str(standard[trait])])
    t = Table(data, colWidths=[120, 120, 150])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=300, height=300))
    
    # Página de recomendaciones
    story.append(PageBreak())
    story.append(Paragraph("Análisis y Recomendaciones", styles["Heading1"]))
    story.append(Spacer(1, 10))
    
    # Fortalezas
    if analysis.get('fortalezas'):
        story.append(Paragraph("FORTALEZAS VALORALES", styles["Heading2"]))
        for f in analysis['fortalezas']:
            story.append(Paragraph(f"• {f}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    # Alertas
    if analysis.get('alertas'):
        story.append(Paragraph("ALERTAS Y ÁREAS DE ATENCIÓN", styles["Heading2"]))
        for a in analysis['alertas']:
            story.append(Paragraph(f"• {a}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    # Recomendaciones
    if analysis.get('recomendaciones'):
        story.append(Paragraph("RECOMENDACIONES", styles["Heading2"]))
        for r in analysis['recomendaciones']:
            # Limpiar markdown para PDF
            r_clean = r.replace("**", "")
            story.append(Paragraph(f"• {r_clean}", styles["Small"]))
        story.append(Spacer(1, 10))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Este reporte es generado automáticamente como herramienta de apoyo para Recursos Humanos. Los resultados deben complementarse con entrevistas y otras evaluaciones.</i>", styles["Small"]))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_wpi_pdf(candidate, raw_scores, normalized, radar_fig, session_id, completed_at=None, analysis=None):
    """
    Genera un PDF con los resultados del WPI (Work Personality Index).
    
    Args:
        candidate: Dict con información del candidato
        raw_scores: Puntajes directos por dimensión
        normalized: Puntajes normalizados (0-100) por dimensión
        radar_fig: Figura matplotlib del radar
        session_id: ID de la sesión
        completed_at: Fecha de completación (opcional)
        analysis: Dict con análisis de aptitud (opcional, se genera si no se proporciona)
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], 
                             fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], 
                             fontSize=9, leading=12))
    
    story = []
    
    # === PÁGINA 1: PORTADA Y RESULTADOS ===
    story.append(Paragraph("WPI - Work Personality Index", styles["Title"]))
    story.append(Paragraph("Evaluación de Personalidad Laboral", styles["Heading2"]))
    story.append(Spacer(1, 12))
    
    # Información del candidato
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position', 'N/A')}", styles["Normal"]))
    
    # Formatear fecha
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            fecha_str = completed_at
    else:
        fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    # Generar análisis si no se proporcionó
    if analysis is None:
        analysis = analyze_wpi_aptitude(normalized)
    
    # === RESULTADO DE APTITUD ===
    story.append(Paragraph(
        f"<b>RESULTADO: {analysis['aptitude_level']} ({analysis['aptitude_score']}/100)</b>", 
        styles["Heading2"]
    ))
    story.append(Paragraph(f"{analysis['aptitude_desc']}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Dimensión más fuerte:</b> {analysis['strongest_dimension']} "
        f"({int(analysis['strongest_score'])}/100) | "
        f"<b>Dimensión a desarrollar:</b> {analysis['weakest_dimension']} "
        f"({int(analysis['weakest_score'])}/100)",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Promedio general:</b> {analysis['average_score']}/100",
        styles["Normal"]
    ))
    story.append(Spacer(1, 16))
    
    # === TABLA DE PUNTAJES ===
    story.append(Paragraph("Puntajes por Dimensión", styles["Heading2"]))
    story.append(Spacer(1, 8))
    
    data = [["Dimensión", "Puntaje Directo", "Puntaje Normalizado (0-100)", "Nivel"]]
    for dim in WPI_DIMENSIONS:
        nivel = "Alto" if normalized[dim] >= 70 else ("Medio" if normalized[dim] >= 45 else "Bajo")
        data.append([
            dim,
            str(int(raw_scores[dim])),
            f"{int(normalized[dim])}/100",
            nivel
        ])
    
    t = Table(data, colWidths=[140, 80, 130, 60])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    
    # === GRÁFICO RADAR ===
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=320, height=320))
    
    # === PÁGINA 2: ANÁLISIS DETALLADO ===
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado y Recomendaciones", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    # === FORTALEZAS ===
    if analysis.get('fortalezas'):
        story.append(Paragraph("✅ FORTALEZAS DESTACADAS", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for f in analysis['fortalezas']:
            # Limpiar markdown para PDF
            f_clean = f.replace("**", "")
            story.append(Paragraph(f"• {f_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === ALERTAS ===
    if analysis.get('alertas'):
        story.append(Paragraph("⚠️ ÁREAS DE ATENCIÓN", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for a in analysis['alertas']:
            # Limpiar markdown para PDF
            a_clean = a.replace("**", "").replace("⚠️ ", "")
            story.append(Paragraph(f"• {a_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === ROLES IDEALES ===
    if analysis.get('ideal_para'):
        story.append(Paragraph("🎯 ROLES IDEALES PARA EL CANDIDATO", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for role in analysis['ideal_para']:
            story.append(Paragraph(f"• {role}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === ROLES A EVITAR ===
    if analysis.get('avoid_roles'):
        story.append(Paragraph("⛔ ROLES NO RECOMENDADOS", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for role in analysis['avoid_roles']:
            story.append(Paragraph(f"• {role}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === RECOMENDACIONES ===
    if analysis.get('recomendaciones'):
        story.append(Paragraph("💡 RECOMENDACIONES ESPECÍFICAS", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for r in analysis['recomendaciones']:
            # Limpiar markdown para PDF
            r_clean = r.replace("**", "")
            story.append(Paragraph(f"• {r_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === DESCRIPCIÓN DE DIMENSIONES ===
    story.append(PageBreak())
    story.append(Paragraph("Descripción de las Dimensiones del WPI", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    for dim in WPI_DIMENSIONS:
        score = normalized[dim]
        desc_info = WPI_DESCRIPTIONS[dim]
        
        # Determinar nivel y descripción
        if score >= 70:
            level_text = "ALTO"
            desc_text = desc_info["high"]
        elif score >= 45:
            level_text = "MEDIO"
            desc_text = desc_info["medium"]
        else:
            level_text = "BAJO"
            desc_text = desc_info["low"]
        
        story.append(Paragraph(
            f"<b>{desc_info['title']}</b> - Nivel: {level_text} ({int(score)}/100)",
            styles["Heading3"]
        ))
        story.append(Paragraph(desc_text, styles["Small"]))
        story.append(Spacer(1, 8))
    
    # === FOOTER ===
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Este reporte es generado automáticamente como herramienta de apoyo para "
        "Recursos Humanos. Los resultados deben complementarse con entrevistas, "
        "referencias laborales y otras evaluaciones pertinentes.</i>",
        styles["Small"]
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_eri_pdf(candidate, raw_scores, normalized, radar_fig, session_id, completed_at=None, analysis=None, validity_score=None, validity_flags=None):
    """
    Genera un PDF con los resultados del ERI (Evaluación de Riesgo e Integridad).
    
    Args:
        candidate: Dict con información del candidato
        raw_scores: Puntajes directos por dimensión
        normalized: Puntajes normalizados (0-100) por dimensión (100 = bajo riesgo)
        radar_fig: Figura matplotlib del radar
        session_id: ID de la sesión
        completed_at: Fecha de completación (opcional)
        analysis: Dict con análisis de riesgo (opcional, se genera si no se proporciona)
        validity_score: Puntaje de validez del test (0-12)
        validity_flags: Lista de alertas de validez
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], 
                             fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], 
                             fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="AlertBold", parent=styles["Normal"],
                             fontSize=11, leading=14, fontName="Helvetica-Bold",
                             textColor=colors.HexColor("#DC2626")))
    
    story = []
    
    # === PÁGINA 1: PORTADA Y RESULTADOS ===
    story.append(Paragraph("ERI - Evaluación de Riesgo e Integridad", styles["Title"]))
    story.append(Paragraph("Screening de Confiabilidad y Comportamiento Laboral", styles["Heading2"]))
    story.append(Spacer(1, 12))
    
    # Información del candidato
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position', 'N/A')}", styles["Normal"]))
    
    # Formatear fecha
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            fecha_str = completed_at
    else:
        fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    # Generar análisis si no se proporcionó
    if analysis is None:
        if validity_score is None:
            validity_score = ERI_VALIDITY_QUESTIONS_COUNT
        if validity_flags is None:
            validity_flags = []
        analysis = analyze_eri_aptitude(normalized, validity_score, validity_flags)
    
    # === BANNER DE VALIDEZ (si aplica) ===
    if analysis.get('validity_warning'):
        story.append(Paragraph("⚠️ ALERTA DE VALIDEZ DEL TEST", styles["AlertBold"]))
        story.append(Paragraph(analysis['validity_warning'], styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === RESULTADO DE RIESGO ===
    risk_color_map = {
        "#10B981": "✅ BAJO RIESGO",
        "#F59E0B": "⚠️ RIESGO MODERADO",
        "#EF4444": "🚫 ALTO RIESGO"
    }
    risk_banner = risk_color_map.get(analysis['risk_color'], analysis['risk_level'])
    
    story.append(Paragraph(
        f"<b>RESULTADO: {risk_banner} ({analysis['risk_score']:.1f}/100)</b>", 
        styles["Heading2"]
    ))
    story.append(Paragraph(f"{analysis['risk_desc']}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Dimensión de menor riesgo:</b> {analysis['safest_dimension']} "
        f"({int(analysis['safest_score'])}/100) | "
        f"<b>Dimensión de mayor riesgo:</b> {analysis['riskiest_dimension']} "
        f"({int(analysis['riskiest_score'])}/100)",
        styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Promedio de riesgo:</b> {analysis['average_score']:.1f}/100 "
        f"(Puntajes altos = BAJO riesgo)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"<b>Decisión Recomendada:</b> {analysis['hiring_decision']}",
        styles["Heading3"]
    ))
    story.append(Spacer(1, 16))
    
    # === TABLA DE PUNTAJES ===
    story.append(Paragraph("Puntajes por Dimensión de Riesgo", styles["Heading2"]))
    story.append(Spacer(1, 8))
    
    data = [["Dimensión", "Puntaje", "Nivel de Riesgo", "Estado"]]
    for dim in ERI_DIMENSIONS:
        score = normalized[dim]
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            nivel = "Bajo Riesgo"
            estado = "✅"
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            nivel = "Riesgo Moderado"
            estado = "⚠️"
        else:
            nivel = "Alto Riesgo"
            estado = "🚨"
        
        data.append([
            dim,
            f"{int(score)}/100",
            nivel,
            estado
        ])
    
    t = Table(data, colWidths=[140, 70, 110, 50])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DC2626")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    
    # === GRÁFICO RADAR ===
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=350, height=350))
    
    # === PÁGINA 2: ANÁLISIS DETALLADO ===
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado y Recomendaciones de Contratación", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    # === FORTALEZAS ===
    if analysis.get('fortalezas'):
        story.append(Paragraph("✅ ASPECTOS POSITIVOS (Bajo Riesgo)", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for f in analysis['fortalezas']:
            # Limpiar markdown para PDF
            f_clean = f.replace("**", "")
            story.append(Paragraph(f"• {f_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === ALERTAS ===
    if analysis.get('alertas'):
        story.append(Paragraph("🚨 SEÑALES DE ALERTA Y FACTORES DE RIESGO", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for a in analysis['alertas']:
            # Limpiar markdown para PDF
            a_clean = a.replace("**", "").replace("⚠️ ", "").replace("🚨 ", "")
            story.append(Paragraph(f"• {a_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === RECOMENDACIONES ===
    if analysis.get('recomendaciones'):
        story.append(Paragraph("💼 RECOMENDACIONES DE CONTRATACIÓN", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for r in analysis['recomendaciones']:
            # Limpiar markdown para PDF
            r_clean = r.replace("**", "")
            story.append(Paragraph(f"{r_clean}", styles["Small"]))
        story.append(Spacer(1, 8))
    
    # === FLAGS DE VALIDEZ ===
    if validity_flags and len(validity_flags) > 0:
        story.append(PageBreak())
        story.append(Paragraph("⚠️ DETALLES DE VALIDEZ DEL TEST", styles["Heading2"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Se detectaron {len(validity_flags)} respuestas poco realistas en preguntas de validez. "
            "Esto puede indicar que el candidato está tratando de presentarse de forma irrealmente perfecta.",
            styles["Small"]
        ))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Ejemplos de respuestas sospechosas:", styles["SmallBold"]))
        story.append(Spacer(1, 4))
        for flag in validity_flags[:5]:  # Mostrar máximo 5 ejemplos
            story.append(Paragraph(f"• {flag}", styles["Small"]))
        if len(validity_flags) > 5:
            story.append(Paragraph(f"... y {len(validity_flags) - 5} más.", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === DESCRIPCIÓN DE DIMENSIONES ===
    story.append(PageBreak())
    story.append(Paragraph("Descripción de las Dimensiones del ERI", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    for dim in ERI_DIMENSIONS:
        score = normalized[dim]
        desc_info = ERI_DESCRIPTIONS[dim]
        
        # Determinar nivel y descripción (invertido: alto score = bajo riesgo)
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            level_text = "BAJO RIESGO ✅"
            desc_text = desc_info["low_risk"]
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            level_text = "RIESGO MODERADO ⚠️"
            desc_text = desc_info["medium_risk"]
        else:
            level_text = "ALTO RIESGO 🚨"
            desc_text = desc_info["high_risk"]
        
        story.append(Paragraph(
            f"<b>{desc_info['title']}</b> - {level_text} ({int(score)}/100)",
            styles["Heading3"]
        ))
        story.append(Paragraph(desc_text, styles["Small"]))
        story.append(Spacer(1, 8))
    
    # === INTERPRETACIÓN DE UMBRALES ===
    story.append(PageBreak())
    story.append(Paragraph("Interpretación de Umbrales de Riesgo", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("<b>✅ BAJO RIESGO (66-100 puntos):</b>", styles["Heading3"]))
    story.append(Paragraph(
        "Sin indicadores significativos de riesgo. El candidato muestra actitudes y comportamientos "
        "compatibles con un desempeño confiable y ético en el entorno laboral.",
        styles["Small"]
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>⚠️ RIESGO MODERADO (41-65 puntos):</b>", styles["Heading3"]))
    story.append(Paragraph(
        "Señales de alerta moderadas. Se recomienda profundizar con entrevistas enfocadas, "
        "referencias laborales exhaustivas y período de prueba con supervisión cercana.",
        styles["Small"]
    ))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>🚨 ALTO RIESGO (0-40 puntos):</b>", styles["Heading3"]))
    story.append(Paragraph(
        "Múltiples indicadores de riesgo significativo. La contratación representa riesgo elevado "
        "para la organización en términos de pérdidas, conflictos, accidentes o incumplimiento normativo. "
        "Se recomienda NO CONTRATAR o requerir evaluación psicológica profesional adicional.",
        styles["Small"]
    ))
    story.append(Spacer(1, 12))
    
    # === LIMITACIONES Y DISCLAIMERS ===
    story.append(Paragraph("Limitaciones y Consideraciones Importantes", styles["Heading2"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "• Este test es una herramienta de SCREENING, no un diagnóstico psicológico definitivo.",
        styles["Small"]
    ))
    story.append(Paragraph(
        "• Los resultados deben complementarse con: entrevistas conductuales (STAR), "
        "referencias laborales verificables, verificación de antecedentes penales y laborales.",
        styles["Small"]
    ))
    story.append(Paragraph(
        "• Ningún test psicométrico predice el comportamiento futuro con 100% de certeza.",
        styles["Small"]
    ))
    story.append(Paragraph(
        "• En casos de alto riesgo en dimensiones críticas (violencia, sustancias, deshonestidad), "
        "se recomienda evaluación por psicólogo organizacional certificado.",
        styles["Small"]
    ))
    story.append(Paragraph(
        "• Este reporte es CONFIDENCIAL y debe manejarse según políticas de protección de datos.",
        styles["Small"]
    ))
    story.append(Spacer(1, 20))
    
    # === FOOTER ===
    story.append(Paragraph(
        "<i>Este reporte es generado automáticamente como herramienta de apoyo para "
        "Recursos Humanos en procesos de selección. Los resultados deben ser interpretados "
        "por personal capacitado y complementados con otras fuentes de información.</i>",
        styles["Small"]
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_talent_map_pdf(candidate, raw_scores, normalized, radar_fig, session_id, completed_at=None, analysis=None, job_profile_name=None, comparison_fig=None):
    """
    Genera un PDF con los resultados del Talent Map (Mapeo de Competencias).
    
    Args:
        candidate: Dict con información del candidato
        raw_scores: Puntajes directos por competencia
        normalized: Puntajes normalizados (0-100) por competencia
        radar_fig: Figura matplotlib del radar
        session_id: ID de la sesión
        completed_at: Fecha de completación (opcional)
        analysis: Dict con análisis de competencias (opcional)
        job_profile_name: Nombre del perfil de puesto para match (opcional)
        comparison_fig: Figura matplotlib de comparación (opcional)
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=14))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Normal"], 
                             fontSize=9, leading=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], 
                             fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="MatchHighlight", parent=styles["Normal"],
                             fontSize=13, leading=16, fontName="Helvetica-Bold",
                             textColor=colors.HexColor("#1E40AF")))
    
    story = []
    
    # === PÁGINA 1: PORTADA Y RESULTADOS ===
    story.append(Paragraph("Talent Map - Mapeo de Competencias y Talentos", styles["Title"]))
    story.append(Paragraph("Evaluación de 8 Competencias Universales", styles["Heading2"]))
    story.append(Spacer(1, 12))
    
    # Información del candidato
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo Evaluado:</b> {candidate.get('position', 'N/A')}", styles["Normal"]))
    
    # Formatear fecha
    if completed_at:
        try:
            fecha_obj = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
            fecha_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
        except:
            fecha_str = completed_at
    else:
        fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    story.append(Paragraph(f"<b>Fecha de Presentación:</b> {fecha_str}", styles["Normal"]))
    story.append(Spacer(1, 16))
    
    # Generar análisis si no se proporcionó
    if analysis is None:
        profile_scores = TALENT_MAP_JOB_PROFILES[job_profile_name]["competencias"] if job_profile_name else None
        analysis = analyze_talent_map_match(normalized, job_profile_name)
    
    # === RESULTADO GENERAL ===
    story.append(Paragraph(
        f"<b>PERFIL DE COMPETENCIAS: Promedio {analysis['average_score']:.1f}/100</b>", 
        styles["Heading2"]
    ))
    story.append(Paragraph(
        f"<b>Competencia más fuerte:</b> {analysis['strongest_competency']} "
        f"({int(analysis['strongest_score'])}/100) | "
        f"<b>Área de mayor desarrollo:</b> {analysis['weakest_competency']} "
        f"({int(analysis['weakest_score'])}/100)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))
    
    # === ANÁLISIS DE MATCH (si aplica) ===
    if analysis.get('match_analysis'):
        match = analysis['match_analysis']
        story.append(Paragraph(
            f"{match['match_label']}: {match['match_percentage']:.1f}%",
            styles["MatchHighlight"]
        ))
        story.append(Paragraph(
            f"<b>Perfil de Puesto:</b> {match['job_emoji']} {match['job_profile']} - {match['job_description']}",
            styles["Normal"]
        ))
        story.append(Paragraph(
            f"<b>Evaluación:</b> {match['match_desc']}",
            styles["Normal"]
        ))
        story.append(Spacer(1, 16))
    else:
        story.append(Spacer(1, 12))
    
    # === TABLA DE COMPETENCIAS ===
    story.append(Paragraph("Puntajes por Competencia", styles["Heading2"]))
    story.append(Spacer(1, 8))
    
    data = [["Competencia", "Puntaje", "Nivel", "Estado"]]
    for comp in TALENT_MAP_COMPETENCIES:
        score = normalized[comp]
        if score >= 75:
            nivel = "Alto"
            estado = "🌟"
        elif score >= 50:
            nivel = "Medio"
            estado = "👍"
        else:
            nivel = "En Desarrollo"
            estado = "📈"
        
        data.append([
            comp,
            f"{int(score)}/100",
            nivel,
            estado
        ])
    
    t = Table(data, colWidths=[140, 70, 90, 50])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))
    
    # === GRÁFICO RADAR ===
    if radar_fig:
        img_buf = BytesIO()
        radar_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=350, height=350))
    
    # === PÁGINA 2: ANÁLISIS DETALLADO ===
    story.append(PageBreak())
    story.append(Paragraph("Análisis Detallado de Competencias", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    # === FORTALEZAS ===
    if analysis.get('fortalezas'):
        story.append(Paragraph("🌟 FORTALEZAS CLAVE", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for f in analysis['fortalezas']:
            # Limpiar markdown para PDF
            f_clean = f.replace("**", "")
            story.append(Paragraph(f"• {f_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === ÁREAS DE DESARROLLO ===
    if analysis.get('areas_desarrollo'):
        story.append(Paragraph("📈 ÁREAS DE DESARROLLO", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for a in analysis['areas_desarrollo']:
            # Limpiar markdown para PDF
            a_clean = a.replace("**", "")
            story.append(Paragraph(f"• {a_clean}", styles["Small"]))
        story.append(Spacer(1, 12))
    
    # === ANÁLISIS DE MATCH CON PERFIL (si aplica) ===
    if analysis.get('match_analysis'):
        match = analysis['match_analysis']
        
        story.append(Paragraph(f"🎯 ANÁLISIS DE MATCH CON {match['job_profile'].upper()}", styles["Heading2"]))
        story.append(Spacer(1, 8))
        
        # Fortalezas del match
        if match.get('match_strengths'):
            story.append(Paragraph("<b>✅ Competencias que EXCEDEN el perfil:</b>", styles["SmallBold"]))
            story.append(Spacer(1, 4))
            for s in match['match_strengths']:
                s_clean = s.replace("**", "")
                story.append(Paragraph(f"• {s_clean}", styles["Small"]))
            story.append(Spacer(1, 8))
        
        # Gaps del match
        if match.get('match_gaps'):
            story.append(Paragraph("<b>⚠️ Brechas a cerrar:</b>", styles["SmallBold"]))
            story.append(Spacer(1, 4))
            for g in match['match_gaps']:
                g_clean = g.replace("**", "")
                story.append(Paragraph(f"• {g_clean}", styles["Small"]))
            story.append(Spacer(1, 12))
    
    # === GRÁFICO DE COMPARACIÓN (si aplica) ===
    if comparison_fig:
        story.append(PageBreak())
        story.append(Paragraph("Análisis de Brechas de Competencia", styles["Heading1"]))
        story.append(Spacer(1, 12))
        img_buf = BytesIO()
        comparison_fig.savefig(img_buf, format="png", dpi=150, bbox_inches="tight")
        img_buf.seek(0)
        story.append(Image(img_buf, width=500, height=420))
    
    # === PÁGINA 3: RECOMENDACIONES ===
    story.append(PageBreak())
    story.append(Paragraph("💼 Recomendaciones y Plan de Desarrollo", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    if analysis.get('recomendaciones'):
        for r in analysis['recomendaciones']:
            # Limpiar markdown para PDF
            r_clean = r.replace("**", "")
            story.append(Paragraph(f"{r_clean}", styles["Small"]))
            story.append(Spacer(1, 6))
    
    # === DESCRIPCIÓN DE LAS 8 COMPETENCIAS ===
    story.append(PageBreak())
    story.append(Paragraph("Descripción de las 8 Competencias Evaluadas", styles["Heading1"]))
    story.append(Spacer(1, 12))
    
    for comp in TALENT_MAP_COMPETENCIES:
        score = normalized[comp]
        desc_info = TALENT_MAP_DESCRIPTIONS[comp]
        
        # Determinar nivel y descripción
        if score >= 75:
            level_text = "ALTO 🌟"
            desc_text = desc_info["high"]
        elif score >= 50:
            level_text = "MEDIO 👍"
            desc_text = desc_info["medium"]
        else:
            level_text = "EN DESARROLLO 📈"
            desc_text = desc_info["low"]
        
        story.append(Paragraph(
            f"<b>{desc_info['title']}</b> - {level_text} ({int(score)}/100)",
            styles["Heading3"]
        ))
        story.append(Paragraph(desc_text, styles["Small"]))
        story.append(Spacer(1, 8))
    
    # === PERFILES DE PUESTOS DISPONIBLES ===
    story.append(PageBreak())
    story.append(Paragraph("Perfiles de Puestos de Referencia", styles["Heading1"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "El sistema incluye perfiles de referencia (benchmarks) para los siguientes puestos:",
        styles["Normal"]
    ))
    story.append(Spacer(1, 8))
    
    for job_name, job_info in TALENT_MAP_JOB_PROFILES.items():
        story.append(Paragraph(
            f"<b>{job_info['emoji']} {job_name}:</b> {job_info['descripcion']}",
            styles["Small"]
        ))
        story.append(Spacer(1, 4))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Estos perfiles sirven como referencia para evaluar el ajuste (fit) entre "
        "las competencias del candidato y los requisitos del puesto.",
        styles["Small"]
    ))
    
    # === DISCLAIMER ===
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>Este reporte es generado automáticamente como herramienta de apoyo para "
        "Recursos Humanos en procesos de selección y desarrollo. Los resultados deben ser "
        "interpretados por personal capacitado y complementados con entrevistas, evaluaciones "
        "de desempeño y otras fuentes de información. Las competencias son desarrollables mediante "
        "capacitación, coaching y experiencia práctica.</i>",
        styles["Small"]
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_desempeno_pdf(candidate, rendimiento_scores, potencial_scores, radar_fig, bars_fig, 
                           session_id, completed_at=None, analysis=None, evaluador_nombre=None, iniciativas=None):
    """Genera PDF de Evaluación de Desempeño."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1E40AF"), alignment=1, spaceAfter=14))
    styles.add(ParagraphStyle(name='SubTitle', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor("#374151"), spaceAfter=10))
    styles.add(ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#6B7280")))
    styles.add(ParagraphStyle(name='ListItem', parent=styles['Normal'], fontSize=10, leftIndent=20, spaceAfter=6))
    
    story = []
    
    # Página 1: Portada
    story.append(Spacer(1, 72))
    story.append(Paragraph("📊 EVALUACIÓN DE DESEMPEÑO", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Colaborador Evaluado:</b> {candidate['name']}", styles['Normal']))
    story.append(Paragraph(f"<b>Cédula:</b> {candidate['cedula']}", styles['Normal']))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position', 'N/A')}", styles['Normal']))
    if evaluador_nombre:
        story.append(Paragraph(f"<b>Evaluador:</b> {evaluador_nombre}", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha de Evaluación:</b> {completed_at or 'N/A'}", styles['Normal']))
    story.append(Paragraph(f"<b>ID de Sesión:</b> {session_id}", styles['Small']))
    story.append(Spacer(1, 24))
    
    # Banner de clasificación
    if analysis and analysis.get("clasificacion"):
        clasif = analysis["clasificacion"]
        banner_color = colors.HexColor(clasif["color"])
        banner_table = Table([[clasif["label"]]], colWidths=[450])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), banner_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ]))
        story.append(banner_table)
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<i>{clasif['descripcion']}</i>", styles['Small']))
    
    story.append(Spacer(1, 24))
    
    # Tabla de puntajes
    if analysis:
        puntajes_data = [
            ["Componente", "Promedio", "Máximo"],
            ["Evaluación de Rendimiento (6 objetivos)", f"{analysis['promedio_rendimiento']:.2f}", "5.00"],
            ["Evaluación de Potencial (5 dimensiones)", f"{analysis['promedio_potencial']:.2f}", "3.00"],
            ["Puntaje Global Ponderado", f"<b>{analysis['puntaje_global']:.2f}</b>", "5.00"]
        ]
        
        puntajes_table = Table(puntajes_data, colWidths=[250, 100, 100])
        puntajes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor("#F3F4F6")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#DBEAFE")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(puntajes_table)
    
    story.append(PageBreak())
    
    # Página 2: Gráfico de Rendimiento
    story.append(Paragraph("EVALUACIÓN DE RENDIMIENTO", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if bars_fig:
        img_buffer = BytesIO()
        bars_fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img = Image(img_buffer, width=480, height=320)
        story.append(img)
        plt.close(bars_fig)
    
    story.append(Spacer(1, 12))
    
    # Detalles de cada objetivo
    story.append(Paragraph("<b>Detalle por Objetivo:</b>", styles['Normal']))
    story.append(Spacer(1, 6))
    
    for obj_id, score in rendimiento_scores.items():
        objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
        nivel = DESEMPENO_ESCALA_RENDIMIENTO[score]
        story.append(Paragraph(
            f"<b>{objetivo['titulo']}</b> - {score:.1f}/5.0 ({nivel['label']})",
            styles['ListItem']
        ))
    
    story.append(PageBreak())
    
    # Página 3: Gráfico de Potencial
    story.append(Paragraph("EVALUACIÓN DE POTENCIAL", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if radar_fig:
        img_buffer = BytesIO()
        radar_fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img = Image(img_buffer, width=400, height=400)
        story.append(img)
        plt.close(radar_fig)
    
    story.append(Spacer(1, 12))
    
    # Detalles de cada dimensión
    story.append(Paragraph("<b>Detalle por Dimensión:</b>", styles['Normal']))
    story.append(Spacer(1, 6))
    
    for dim_id, score in potencial_scores.items():
        dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
        story.append(Paragraph(
            f"<b>{dimension['nombre']}</b> - Nivel {score}/3",
            styles['ListItem']
        ))
        story.append(Paragraph(
            f"<i>{dimension['niveles'][score]}</i>",
            ParagraphStyle(name='DimDesc', parent=styles['Small'], leftIndent=30, spaceAfter=8)
        ))
    
    story.append(PageBreak())
    
    # Página 4: Fortalezas y Áreas de Mejora
    story.append(Paragraph("ANÁLISIS DE FORTALEZAS Y ÁREAS DE MEJORA", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if analysis:
        # Fortalezas de Rendimiento
        if analysis.get("fortalezas_rendimiento"):
            story.append(Paragraph("<b>✅ Fortalezas de Rendimiento:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["fortalezas_rendimiento"]:
                story.append(Paragraph(
                    f"• {item['titulo']} ({item['score']:.1f}/5.0 - {item['label']})",
                    styles['ListItem']
                ))
            story.append(Spacer(1, 12))
        
        # Fortalezas de Potencial
        if analysis.get("fortalezas_potencial"):
            story.append(Paragraph("<b>⭐ Fortalezas de Potencial:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["fortalezas_potencial"]:
                story.append(Paragraph(
                    f"• {item['nombre']} ({item['nivel']})",
                    styles['ListItem']
                ))
            story.append(Spacer(1, 12))
        
        # Áreas de Mejora de Rendimiento
        if analysis.get("areas_mejora_rendimiento"):
            story.append(Paragraph("<b>⚠️ Áreas de Mejora en Rendimiento:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["areas_mejora_rendimiento"]:
                story.append(Paragraph(
                    f"• {item['titulo']} ({item['score']:.1f}/5.0 - {item['label']})",
                    styles['ListItem']
                ))
            story.append(Spacer(1, 12))
        
        # Áreas de Desarrollo de Potencial
        if analysis.get("areas_desarrollo_potencial"):
            story.append(Paragraph("<b>📈 Áreas de Desarrollo en Potencial:</b>", styles['Normal']))
            story.append(Spacer(1, 6))
            for item in analysis["areas_desarrollo_potencial"]:
                story.append(Paragraph(
                    f"• {item['nombre']} ({item['nivel']})",
                    styles['ListItem']
                ))
            story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    
    # Página 5: Recomendaciones e Iniciativas
    story.append(Paragraph("RECOMENDACIONES Y PLAN DE ACCIÓN", styles['SubTitle']))
    story.append(Spacer(1, 12))
    
    if analysis and analysis.get("recomendaciones"):
        story.append(Paragraph("<b>💡 Recomendaciones Generales:</b>", styles['Normal']))
        story.append(Spacer(1, 6))
        for recom in analysis["recomendaciones"]:
            story.append(Paragraph(f"• {recom}", styles['ListItem']))
        story.append(Spacer(1, 18))
    
    # Iniciativas de Mejora
    if iniciativas and len(iniciativas) > 0:
        story.append(Paragraph("<b>🎯 Iniciativas de Mejora Definidas:</b>", styles['Normal']))
        story.append(Spacer(1, 6))
        for i, iniciativa in enumerate(iniciativas, 1):
            if iniciativa and iniciativa.strip():
                story.append(Paragraph(f"<b>Iniciativa {i}:</b>", styles['Normal']))
                story.append(Paragraph(iniciativa, styles['ListItem']))
                story.append(Spacer(1, 8))
    elif analysis and analysis.get("requiere_iniciativas"):
        story.append(Paragraph(
            "<b>⚠️ NOTA:</b> El promedio de evaluación requiere establecer iniciativas de mejora específicas.",
            ParagraphStyle(name='Alert', parent=styles['Normal'], textColor=colors.HexColor("#EF4444"))
        ))
    
    story.append(Spacer(1, 24))
    
    # Footer
    story.append(Paragraph(
        f"<i>Documento generado automáticamente el {completed_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles['Small']
    ))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# HELPER: Load DISC questions
# =========================================================================

def load_disc_questions():
    qfile = os.path.join(os.path.dirname(__file__), "questions_es.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def load_disc_descriptions():
    dfile = os.path.join(os.path.dirname(__file__), "disc_descriptions_es.json")
    with open(dfile, "r", encoding="utf-8") as f:
        return json.load(f)


def load_wpi_questions():
    """Carga las preguntas del WPI desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_wpi.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================================
# NAVIGATION HELPERS
# =========================================================================

def nav(page):
    st.session_state.page = page


# =========================================================================
# PÁGINAS
# =========================================================================

def page_home():
    st.markdown("<h1 style='text-align:center; color:#1e3a5f;'>🧠 Plataforma de Evaluaciones Psicométricas</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#555;'>Sistema de evaluación para Recursos Humanos</p>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("""
        ### 👤 Soy Candidato
        Ingresa con tu número de cédula para realizar la evaluación asignada por Recursos Humanos.
        """)
        if st.button("🔑 Ingresar como Candidato", use_container_width=True, key="btn_candidate"):
            nav("candidate_login")
            st.rerun()

    with col2:
        st.markdown("""
        ### 🔒 Soy Administrador RH
        Accede al panel de administración para gestionar evaluaciones y ver resultados.
        """)
        if st.button("🛡️ Ingresar como Administrador", use_container_width=True, key="btn_admin"):
            nav("admin_login")
            st.rerun()


# -------------------------------------------------------------------------
# ADMIN: LOGIN
# -------------------------------------------------------------------------
def page_admin_login():
    st.markdown("## 🔒 Acceso Administrador RH")
    if st.button("⬅️ Volver al inicio"):
        nav("home")
        st.rerun()

    with st.form("admin_login_form"):
        username = st.text_input("Usuario", key="admin_user")
        password = st.text_input("Contraseña", type="password", key="admin_pass")
        submitted = st.form_submit_button("Iniciar Sesión")
        
        if submitted:
            if not username or not password:
                st.error("❌ Por favor completa todos los campos.")
            else:
                username = username.strip()
                password = password.strip()
                
                admin = db.verify_admin(username, password)
                if admin:
                    st.session_state.admin = admin
                    nav("admin_dashboard")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Verifica usuario y contraseña.")


# -------------------------------------------------------------------------
# ADMIN: DASHBOARD
# -------------------------------------------------------------------------
def page_admin_dashboard():
    admin = st.session_state.get("admin")
    if not admin:
        nav("admin_login")
        st.rerun()
        return

    st.markdown(f"## 🛡️ Panel de Administración")
    st.caption(f"Bienvenido, {admin['name']}")

    if st.button("🚪 Cerrar Sesión"):
        st.session_state.pop("admin", None)
        nav("home")
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Crear Evaluación", "📊 Resultados", "👥 Candidatos", "⚙️ Configuración"])

    # ----- TAB 1: Crear Evaluación -----
    with tab1:
        st.markdown("### Asignar Nueva Evaluación")

        sub_tab = st.radio("Candidato:", ["Nuevo candidato", "Candidato existente"], horizontal=True, key="cand_type")

        if sub_tab == "Nuevo candidato":
            with st.form("new_candidate_form"):
                c1, c2 = st.columns(2)
                with c1:
                    cedula = st.text_input("Cédula *", placeholder="Número de identificación")
                    name = st.text_input("Nombre Completo *")
                    age = st.number_input("Edad", min_value=15, max_value=100, value=25)
                with c2:
                    sex = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
                    education = st.text_input("Nivel Educativo", placeholder="Ej: Universitario")
                    position = st.text_input("Cargo", placeholder="Cargo del candidato")

                st.markdown("---")
                c3, c4 = st.columns(2)
                with c3:
                    test_type = st.selectbox("Tipo de Evaluación", ["disc", "valanti", "wpi", "eri", "talent_map", "desempeno"], 
                                            format_func=lambda x: "🎯 DISC" if x == "disc" else ("🧭 VALANTI" if x == "valanti" else ("💼 WPI" if x == "wpi" else ("🔐 ERI" if x == "eri" else ("🌟 Talent Map" if x == "talent_map" else "📊 Evaluación Desempeño")))))
                with c4:
                    time_limit = st.selectbox("Tiempo Límite", [15, 20, 30, 45, 60, 90], index=3, format_func=lambda x: f"{x} minutos")

                create_btn = st.form_submit_button("✅ Crear Evaluación")
                if create_btn:
                    if not cedula.strip() or not name.strip():
                        st.error("Cédula y Nombre son obligatorios.")
                    else:
                        candidate = db.get_candidate_by_cedula(cedula.strip())
                        if not candidate:
                            candidate = db.create_candidate(cedula.strip(), name.strip(), age, sex, education, position)
                            if not candidate:
                                st.error("Error al crear candidato. Cédula duplicada.")
                                return
                        session_id, error = db.create_test_session(candidate["id"], test_type, time_limit, admin["id"])
                        if error:
                            st.warning(f"⚠️ {error}")
                        else:
                            st.success(f"✅ Evaluación creada exitosamente!\n\n**ID:** `{session_id}`\n\n**Cédula:** {cedula}\n\n**Tipo:** {test_type.upper()}\n\n**Tiempo:** {time_limit} min")

        else:  # Candidato existente
            candidates = db.get_all_candidates()
            if not candidates:
                st.info("No hay candidatos registrados.")
            else:
                options = {f"{c['cedula']} - {c['name']}": c for c in candidates}
                selected = st.selectbox("Seleccionar candidato:", list(options.keys()))
                candidate = options[selected]

                st.markdown(f"**Cédula:** {candidate['cedula']} | **Nombre:** {candidate['name']} | **Cargo:** {candidate.get('position', 'N/A')}")

                with st.form("existing_candidate_form"):
                    c3, c4 = st.columns(2)
                    with c3:
                        test_type = st.selectbox("Tipo de Evaluación", ["disc", "valanti", "wpi", "eri", "talent_map", "desempeno"], 
                                                format_func=lambda x: "🎯 DISC" if x == "disc" else ("🧭 VALANTI" if x == "valanti" else ("💼 WPI" if x == "wpi" else ("🔐 ERI" if x == "eri" else ("🌟 Talent Map" if x == "talent_map" else "📊 Evaluación Desempeño")))))
                    with c4:
                        time_limit = st.selectbox("Tiempo Límite", [15, 20, 30, 45, 60, 90], index=3, format_func=lambda x: f"{x} minutos")
                    create_btn2 = st.form_submit_button("✅ Asignar Evaluación")
                    if create_btn2:
                        session_id, error = db.create_test_session(candidate["id"], test_type, time_limit, admin["id"])
                        if error:
                            st.warning(f"⚠️ {error}")
                        else:
                            st.success(f"✅ Evaluación asignada!\n\n**ID:** `{session_id}` | **Cédula:** {candidate['cedula']} | **Tipo:** {test_type.upper()}")

    # ----- TAB 2: Resultados -----
    with tab2:
        st.markdown("### Resultados de Evaluaciones")
        
        # Obtener todas las sesiones primero para construir lista de candidatos
        all_sessions_raw = db.get_all_sessions()
        candidate_names = sorted(set(s["candidate_name"] for s in all_sessions_raw)) if all_sessions_raw else []
        
        # Fila de filtros
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "disc", "valanti", "wpi", "eri", "talent_map", "desempeno"], key="filter_type",
                                        format_func=lambda x: {"Todos": "📋 Todos", "disc": "🎯 DISC", "valanti": "🧭 VALANTI", "wpi": "💼 WPI", "eri": "🔐 ERI", "talent_map": "🌟 Talent Map", "desempeno": "📊 Evaluación Desempeño"}.get(x, x))
        with c2:
            filter_status = st.selectbox("Filtrar por estado:", ["Todos", "pending", "in_progress", "completed", "expired"], key="filter_status",
                                          format_func=lambda x: {"Todos": "📋 Todos", "pending": "⏳ Pendiente", "in_progress": "▶️ En Progreso", "completed": "✅ Completado", "expired": "⏰ Expirado"}.get(x, x))
        with c3:
            filter_candidate = st.selectbox("Filtrar por candidato:", ["Todos"] + candidate_names, key="filter_candidate")
        with c4:
            sort_option = st.selectbox("Ordenar por:", ["Fecha (reciente)", "Fecha (antigua)", "Candidato A-Z", "Candidato Z-A", "Tipo prueba"], key="sort_option")

        ft = filter_type if filter_type != "Todos" else None
        fs = filter_status if filter_status != "Todos" else None
        sessions = db.get_all_sessions(test_type=ft, status=fs)
        
        # Filtrar por candidato
        if filter_candidate != "Todos":
            sessions = [s for s in sessions if s["candidate_name"] == filter_candidate]
        
        # Ordenar según selección
        def get_sort_date(s):
            date_str = s.get("completed_at") or s.get("started_at") or s.get("created_at") or ""
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                return datetime.min
        
        if sort_option == "Fecha (reciente)":
            sessions.sort(key=get_sort_date, reverse=True)
        elif sort_option == "Fecha (antigua)":
            sessions.sort(key=get_sort_date, reverse=False)
        elif sort_option == "Candidato A-Z":
            sessions.sort(key=lambda s: s["candidate_name"].lower())
        elif sort_option == "Candidato Z-A":
            sessions.sort(key=lambda s: s["candidate_name"].lower(), reverse=True)
        elif sort_option == "Tipo prueba":
            sessions.sort(key=lambda s: s["test_type"])
        
        # Mostrar contador de resultados
        st.caption(f"📊 {len(sessions)} evaluación(es) encontrada(s)")

        if not sessions:
            st.info("No hay evaluaciones que coincidan con los filtros.")
        else:
            for sess in sessions:
                status_emoji = {"pending": "⏳", "in_progress": "▶️", "completed": "✅", "expired": "⏰"}.get(sess["status"], "❓")
                
                # Determinar emoji del test
                if sess["test_type"] == "disc":
                    test_emoji = "🎯"
                elif sess["test_type"] == "valanti":
                    test_emoji = "🧭"
                elif sess["test_type"] == "wpi":
                    test_emoji = "💼"
                elif sess["test_type"] == "eri":
                    test_emoji = "🔐"
                else:
                    test_emoji = "📝"
                
                # Agregar indicador de aptitud al título si está completada
                aptitud_tag = ""
                if sess["status"] == "completed":
                    res = db.get_results(sess["id"])
                    if res:
                        if sess["test_type"] == "disc":
                            norm = res.get("normalized", {})
                            rel = res.get("relative", {})
                            if norm:
                                a = analyze_disc_aptitude(norm, rel)
                                aptitud_tag = f" | {a['aptitude_emoji']} {a['aptitude_level']}"
                        elif sess["test_type"] == "valanti":
                            std = res.get("standard", {})
                            if std:
                                a = analyze_valanti_aptitude(std)
                                aptitud_tag = f" | {a['aptitude_emoji']} {a['aptitude_level']}"

                # Formatear fecha para el título del expander
                fecha_tag = ""
                completed_at_val = sess.get("completed_at")
                started_at_val = sess.get("started_at")
                if completed_at_val:
                    try:
                        fecha_obj = datetime.strptime(completed_at_val, "%Y-%m-%d %H:%M:%S")
                        fecha_tag = f" | 📅 {fecha_obj.strftime('%d/%m/%Y %H:%M')}"
                    except:
                        fecha_tag = f" | 📅 {completed_at_val}"
                elif started_at_val:
                    try:
                        fecha_obj = datetime.strptime(started_at_val, "%Y-%m-%d %H:%M:%S")
                        fecha_tag = f" | 📅 {fecha_obj.strftime('%d/%m/%Y %H:%M')}"
                    except:
                        fecha_tag = f" | 📅 {started_at_val}"

                with st.expander(f"{status_emoji} {test_emoji} {sess['test_type'].upper()} | {sess['candidate_name']} (CC: {sess['cedula']}) | ID: {sess['id']}{fecha_tag}{aptitud_tag}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Estado", sess["status"].upper())
                    c2.metric("Tiempo Límite", f"{sess['time_limit_minutes']} min")
                    
                    # Formatear fechas para mejor legibilidad
                    started_at = sess.get("started_at")
                    if started_at:
                        try:
                            fecha_inicio = datetime.strptime(started_at, "%Y-%m-%d %H:%M:%S")
                            started_str = fecha_inicio.strftime("%d/%m/%Y %H:%M")
                        except:
                            started_str = started_at
                    else:
                        started_str = "N/A"
                    
                    completed_at = sess.get("completed_at")
                    if completed_at:
                        try:
                            fecha_fin = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                            completed_str = fecha_fin.strftime("%d/%m/%Y %H:%M")
                        except:
                            completed_str = completed_at
                    else:
                        completed_str = "N/A"
                    
                    c3.metric("Iniciado", started_str)
                    c4.metric("Completado", completed_str)

                    if sess["status"] == "completed":
                        results = db.get_results(sess["id"])
                        candidate = db.get_candidate_by_cedula(sess["cedula"])
                        if results:
                            if sess["test_type"] == "disc":
                                show_disc_results_admin(results, candidate, sess)
                            elif sess["test_type"] == "valanti":
                                show_valanti_results_admin(results, candidate, sess)
                            elif sess["test_type"] == "wpi":
                                show_wpi_results_admin(results, candidate, sess)
                            elif sess["test_type"] == "eri":
                                show_eri_results_admin(results, candidate, sess)
                            elif sess["test_type"] == "talent_map":
                                show_talent_map_results_admin(results, candidate, sess)
                            elif sess["test_type"] == "desempeno":
                                show_desempeno_results_admin(results, candidate, sess)
                        else:
                            st.warning("Resultados no disponibles.")
                    
                    # Botón especial para evaluaciones de desempeño pendientes
                    elif sess["status"] == "pending" and sess["test_type"] == "desempeno":
                        st.info("⏳ Esta evaluación de desempeño está pendiente de ser completada por un evaluador.")
                        if st.button(f"✏️ Evaluar Ahora", key=f"eval_desemp_{sess['id']}"):
                            st.session_state["desempeno_session_id"] = sess["id"]
                            nav("desempeno_eval")
                            st.rerun()

                    # Solo superadmin puede eliminar pruebas
                    if admin.get("role") == "superadmin":
                        st.markdown("---")
                        col_del, col_spacer = st.columns([1, 3])
                        with col_del:
                            if st.button(f"🗑️ Eliminar prueba", key=f"del_{sess['id']}"):
                                st.session_state[f"confirm_del_{sess['id']}"] = True
                        
                        if st.session_state.get(f"confirm_del_{sess['id']}", False):
                            st.warning(f"⚠️ ¿Estás seguro de eliminar la prueba **{sess['id']}** de **{sess['candidate_name']}**? Esta acción es irreversible.")
                            col_yes, col_no, _ = st.columns([1, 1, 2])
                            with col_yes:
                                if st.button("✅ Sí, eliminar", key=f"confirm_yes_{sess['id']}"):
                                    db.delete_test_session(sess['id'])
                                    st.session_state.pop(f"confirm_del_{sess['id']}", None)
                                    st.success("Prueba eliminada.")
                                    st.rerun()
                            with col_no:
                                if st.button("❌ Cancelar", key=f"confirm_no_{sess['id']}"):
                                    st.session_state.pop(f"confirm_del_{sess['id']}", None)
                                    st.rerun()

    # ----- TAB 3: Candidatos -----
    with tab3:
        st.markdown("### Candidatos Registrados")
        candidates = db.get_all_candidates()
        if not candidates:
            st.info("No hay candidatos registrados.")
        else:
            for c in candidates:
                with st.expander(f"👤 {c['name']} | CC: {c['cedula']}"):
                    st.markdown(f"**Edad:** {c.get('age', 'N/A')} | **Sexo:** {c.get('sex', 'N/A')} | **Educación:** {c.get('education', 'N/A')} | **Cargo:** {c.get('position', 'N/A')}")
                    st.caption(f"Registrado: {c.get('created_at', 'N/A')}")
                    sess_list = db.get_all_sessions()
                    cand_sessions = [s for s in sess_list if s["cedula"] == c["cedula"]]
                    if cand_sessions:
                        for s in cand_sessions:
                            emoji = {"pending": "⏳", "in_progress": "▶️", "completed": "✅", "expired": "⏰"}.get(s["status"], "❓")
                            # Formatear fecha de presentación
                            fecha_presentacion = ""
                            if s.get("completed_at"):
                                try:
                                    fecha_obj = datetime.strptime(s["completed_at"], "%Y-%m-%d %H:%M:%S")
                                    fecha_presentacion = f" — Presentado: {fecha_obj.strftime('%d/%m/%Y %H:%M')}"
                                except:
                                    fecha_presentacion = f" — Presentado: {s['completed_at']}"
                            elif s.get("started_at"):
                                try:
                                    fecha_obj = datetime.strptime(s["started_at"], "%Y-%m-%d %H:%M:%S")
                                    fecha_presentacion = f" — Iniciado: {fecha_obj.strftime('%d/%m/%Y %H:%M')}"
                                except:
                                    fecha_presentacion = f" — Iniciado: {s['started_at']}"
                            
                            # Mostrar aptitud si la prueba está completada
                            aptitud_info = ""
                            if s["status"] == "completed":
                                res = db.get_results(s["id"])
                                if res:
                                    if s["test_type"] == "disc":
                                        norm = res.get("normalized", {})
                                        rel = res.get("relative", {})
                                        if norm:
                                            analysis = analyze_disc_aptitude(norm, rel)
                                            aptitud_info = f" | **{analysis['aptitude_emoji']} {analysis['aptitude_level']}** ({analysis['aptitude_score']}/100)"
                                    elif s["test_type"] == "valanti":
                                        std = res.get("standard", {})
                                        if std:
                                            analysis = analyze_valanti_aptitude(std)
                                            aptitud_info = f" | **{analysis['aptitude_emoji']} {analysis['aptitude_level']}** ({analysis['aptitude_score']}/100)"
                            
                            st.markdown(f"  - {emoji} {s['test_type'].upper()} (ID: {s['id']}) — Estado: {s['status']}{fecha_presentacion}{aptitud_info}")
                    
                    # Solo superadmin puede eliminar candidatos
                    if admin.get("role") == "superadmin":
                        st.markdown("---")
                        col_del_c, col_spacer_c = st.columns([1, 3])
                        with col_del_c:
                            if st.button(f"🗑️ Eliminar candidato", key=f"del_cand_{c['id']}"):
                                st.session_state[f"confirm_del_cand_{c['id']}"] = True
                        
                        if st.session_state.get(f"confirm_del_cand_{c['id']}", False):
                            n_sessions = len(cand_sessions) if cand_sessions else 0
                            st.warning(f"⚠️ ¿Estás seguro de eliminar al candidato **{c['name']}** (CC: {c['cedula']})? Se eliminarán también **{n_sessions} evaluación(es)** asociadas. Esta acción es **irreversible**.")
                            col_yes_c, col_no_c, _ = st.columns([1, 1, 2])
                            with col_yes_c:
                                if st.button("✅ Sí, eliminar", key=f"confirm_yes_cand_{c['id']}"):
                                    db.delete_candidate(c['id'])
                                    st.session_state.pop(f"confirm_del_cand_{c['id']}", None)
                                    st.success(f"Candidato **{c['name']}** eliminado correctamente.")
                                    st.rerun()
                            with col_no_c:
                                if st.button("❌ Cancelar", key=f"confirm_no_cand_{c['id']}"):
                                    st.session_state.pop(f"confirm_del_cand_{c['id']}", None)
                                    st.rerun()

    # ----- TAB 4: Configuración -----
    with tab4:
        st.markdown("### Cambiar Contraseña de Administrador")
        with st.form("change_pw"):
            new_pw = st.text_input("Nueva Contraseña", type="password")
            confirm_pw = st.text_input("Confirmar Contraseña", type="password")
            if st.form_submit_button("Cambiar Contraseña"):
                if new_pw and new_pw == confirm_pw:
                    db.change_admin_password(admin["id"], new_pw)
                    st.success("✅ Contraseña actualizada.")
                else:
                    st.error("Las contraseñas no coinciden o están vacías.")


def show_disc_results_admin(results, candidate, session):
    """Show DISC results in the admin panel."""
    normalized = results.get("normalized", {})
    relative = results.get("relative", {})

    # Análisis de aptitud
    analysis = analyze_disc_aptitude(normalized, relative)

    # Estilos conductuales, temperamento y mega resumen (nuevas funcionalidades THT-inspired)
    behavioral_styles = calculate_behavioral_styles(normalized)
    temperament = get_disc_temperament(normalized)
    mega_summary = generate_disc_mega_summary(normalized)

    # Banner de aptitud
    st.markdown(f"""
    <div style="background: {analysis['aptitude_color']}22; border-left: 5px solid {analysis['aptitude_color']};
                padding: 15px 20px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: {analysis['aptitude_color']};">{analysis['aptitude_emoji']} {analysis['aptitude_level']} — Puntaje: {analysis['aptitude_score']}/100</h3>
        <p style="margin: 5px 0 0 0; color: #374151;">{analysis['aptitude_desc']}</p>
        <p style="margin: 5px 0 0 0; color: #6B7280;"><b>Perfil:</b> {analysis['profile_name']} ({analysis['dominant_name']} + {analysis['secondary_name']})</p>
        <p style="margin: 5px 0 0 0; color: #6B7280;"><b>Temperamento:</b> {temperament['label']}</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    disc_colors = {"D": "#EF4444", "I": "#F59E0B", "S": "#10B981", "C": "#3B82F6"}
    disc_names = {"D": "Dominancia", "I": "Influencia", "S": "Estabilidad", "C": "Cumplimiento"}
    for idx, style in enumerate("DISC"):
        with cols[idx]:
            st.metric(f"{style} — {disc_names[style]}", f"{normalized.get(style, 0):.1f}%",
                      f"Rel: {relative.get(style, 0):.1f}%")

    fig = create_disc_plot(normalized)
    st.pyplot(fig)

    # ── MEGA RESUMEN ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Resumen Conductual")
    st.caption("Descripción detallada del perfil conductual en 16 dimensiones, derivada del resultado DISC.")

    cols_summary = st.columns(2)
    items = list(mega_summary.items())
    half = len(items) // 2
    for col, chunk in zip(cols_summary, [items[:half], items[half:]]):
        with col:
            for label, text in chunk:
                st.markdown(f"""
                <div style="background:#F8FAFC; border-left:3px solid #3B82F6; padding:10px 14px;
                            border-radius:6px; margin-bottom:8px;">
                    <b style="color:#1E40AF; font-size:0.85em;">{label}</b><br>
                    <span style="color:#374151; font-size:0.92em;">{text}</span>
                </div>""", unsafe_allow_html=True)

    # ── 9 ESTILOS CONDUCTUALES ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎯 Estilos Conductuales Derivados")
    st.caption("9 estilos con 4 sub-dimensiones cada uno, inferidos matemáticamente del perfil DISC (metodología THT).")

    styles_fig = create_behavioral_styles_chart(behavioral_styles)
    st.pyplot(styles_fig)

    # Detalle expandible de cada estilo
    with st.expander("🔍 Ver descripción detallada de cada sub-dimensión"):
        for style_name, style_data in behavioral_styles.items():
            st.markdown(f"**{style_name}**")
            for sub_name, sub_val in style_data["subs"].items():
                desc = style_data["desc"][sub_name]
                bar_w = int(sub_val)
                color = "#EF4444" if sub_name in ["Franqueza", "Control", "Insistencia", "Por Resultados",
                                                  "Resolución", "Confrontación", "Priorización",
                                                  "Pragmatismo"] else (
                        "#F59E0B" if sub_name in ["Expresividad", "Inspiración", "Optimismo", "Por Inspiración",
                                                  "Positivismo", "Apasionamiento", "Entusiasmo",
                                                  "Extroversión", "Persuasión"] else (
                        "#10B981" if sub_name in ["Autoregulación", "Moderación", "Focalización", "Democrático",
                                                  "Resistencia", "Inalterabilidad", "Pausa", "Autocontrol",
                                                  "Calma"] else "#3B82F6"))
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px; margin:4px 0;">
                    <span style="min-width:140px; font-size:0.85em; color:#374151;">{sub_name}</span>
                    <div style="flex:1; background:#E2E8F0; border-radius:4px; height:14px; position:relative;">
                        <div style="width:{bar_w}%; background:{color}; border-radius:4px; height:14px;"></div>
                    </div>
                    <span style="font-weight:bold; color:{color}; min-width:30px;">{bar_w}</span>
                    <span style="font-size:0.75em; color:#94A3B8; flex:1;">{desc}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("")

    # ── FORTALEZAS Y ALERTAS ──────────────────────────────────────────────
    st.markdown("---")
    col_f, col_a = st.columns(2)
    with col_f:
        st.markdown("#### 💪 Fortalezas")
        for f in analysis['fortalezas']:
            st.markdown(f"- ✅ {f}")
    with col_a:
        st.markdown("#### ⚠️ Alertas")
        for a in analysis['alertas']:
            st.markdown(f"- 🔸 {a}")

    st.markdown("#### 📋 Recomendaciones para el Candidato")
    for r in analysis['recomendaciones']:
        st.markdown(f"- 💡 {r}")

    if analysis['ideal_para']:
        st.markdown("#### 🎯 Ideal para roles de")
        st.markdown(", ".join([f"**{r}**" for r in analysis['ideal_para']]))

    if analysis['cuidado_en']:
        st.markdown("#### ⛔ Tener cuidado en")
        st.markdown(", ".join([f"*{r}*" for r in analysis['cuidado_en']]))

    session_id = session if isinstance(session, str) else session.get("id")
    completed_at = session.get("completed_at") if isinstance(session, dict) else None
    pdf = generate_disc_pdf(candidate, normalized, relative, fig, session_id, completed_at, analysis,
                            behavioral_styles=behavioral_styles, temperament=temperament,
                            mega_summary=mega_summary, styles_fig=styles_fig)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📑 Descargar PDF", data=pdf.getvalue(), file_name=f"disc_{candidate['cedula']}.pdf", mime="application/pdf", key=f"pdf_disc_{session_id}")
    with c2:
        st.download_button("📄 Descargar JSON", data=json.dumps(results, indent=2, ensure_ascii=False), file_name=f"disc_{candidate['cedula']}.json", mime="application/json", key=f"json_disc_{session_id}")


def show_valanti_results_admin(results, candidate, session):
    """Show VALANTI results in the admin panel."""
    direct = results.get("direct", {})
    standard = results.get("standard", {})
    
    # Análisis de aptitud
    analysis = analyze_valanti_aptitude(standard)
    
    # Banner de aptitud
    st.markdown(f"""
    <div style="background: {analysis['aptitude_color']}22; border-left: 5px solid {analysis['aptitude_color']};
                padding: 15px 20px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: {analysis['aptitude_color']};">{analysis['aptitude_emoji']} {analysis['aptitude_level']} — Puntaje: {analysis['aptitude_score']}/100</h3>
        <p style="margin: 5px 0 0 0; color: #374151;">{analysis['aptitude_desc']}</p>
        <p style="margin: 5px 0 0 0; color: #6B7280;"><b>Valor más fuerte:</b> {analysis['strongest_value']} (T={analysis['strongest_score']}) | <b>Valor más bajo:</b> {analysis['weakest_value']} (T={analysis['weakest_score']})</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    for idx, trait in enumerate(VALANTI_TRAITS):
        with cols[idx]:
            st.metric(trait, standard.get(trait, 0), f"Dir: {direct.get(trait, 0)}")

    radar_fig = create_valanti_radar(standard)
    st.pyplot(radar_fig)

    bar_fig = create_valanti_bars(direct, standard)
    st.pyplot(bar_fig)

    sorted_scores = sorted(standard.items(), key=lambda x: x[1], reverse=True)
    st.markdown(f"**Valor más prominente:** {sorted_scores[0][0]} ({sorted_scores[0][1]})")
    st.markdown(f"**Valor menos enfatizado:** {sorted_scores[-1][0]} ({sorted_scores[-1][1]})")
    for trait, score in sorted_scores:
        desc = VALANTI_DESCRIPTIONS[trait]
        level = "Alto" if score >= 55 else ("Bajo" if score <= 45 else "Promedio")
        text = desc["high"] if score >= 55 else (desc["low"] if score <= 45 else "Puntaje dentro del rango promedio.")
        st.markdown(f"**{desc['title']}** — {level} ({score}): {text}")
    
    # Fortalezas y alertas
    if analysis['fortalezas']:
        st.markdown("#### 💪 Fortalezas Valorales")
        for f in analysis['fortalezas']:
            st.markdown(f"- ✅ {f}")
    
    if analysis['alertas']:
        st.markdown("#### ⚠️ Alertas")
        for a in analysis['alertas']:
            st.markdown(f"- 🔸 {a}")
    
    if analysis['recomendaciones']:
        st.markdown("#### 📋 Recomendaciones")
        for r in analysis['recomendaciones']:
            st.markdown(f"- {r}")

    session_id = session if isinstance(session, str) else session.get("id")
    completed_at = session.get("completed_at") if isinstance(session, dict) else None
    pdf = generate_valanti_pdf(candidate, direct, standard, radar_fig, session_id, completed_at, analysis)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📑 Descargar PDF", data=pdf.getvalue(), file_name=f"valanti_{candidate['cedula']}.pdf", mime="application/pdf", key=f"pdf_val_{session_id}")
    with c2:
        st.download_button("📄 Descargar JSON", data=json.dumps(results, indent=2, ensure_ascii=False), file_name=f"valanti_{candidate['cedula']}.json", mime="application/json", key=f"json_val_{session_id}")


def show_wpi_results_admin(results, candidate, session):
    """
    Muestra los resultados del WPI en el panel de administración.
    
    Args:
        results: Dict con raw, normalized y percentages
        candidate: Dict con información del candidato
        session: Dict con información de la sesión o str con session_id
    """
    raw = results.get("raw", {})
    normalized = results.get("normalized", {})
    percentages = results.get("percentages", {})
    
    # Análisis de aptitud
    analysis = analyze_wpi_aptitude(normalized)
    
    # === BANNER DE APTITUD ===
    st.markdown(f"""
    <div style="background: {analysis['aptitude_color']}22; border-left: 5px solid {analysis['aptitude_color']};
                padding: 15px 20px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: {analysis['aptitude_color']};">
            {analysis['aptitude_emoji']} {analysis['aptitude_level']} — Puntaje: {analysis['aptitude_score']}/100
        </h3>
        <p style="margin: 5px 0 0 0; color: #374151;">{analysis['aptitude_desc']}</p>
        <p style="margin: 5px 0 0 0; color: #6B7280;">
            <b>Dimensión más fuerte:</b> {analysis['strongest_dimension']} ({int(analysis['strongest_score'])}/100) | 
            <b>Dimensión a desarrollar:</b> {analysis['weakest_dimension']} ({int(analysis['weakest_score'])}/100) |
            <b>Promedio:</b> {analysis['average_score']}/100
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # === MÉTRICAS POR DIMENSIÓN ===
    st.markdown("### 📊 Puntajes por Dimensión")
    
    # Crear 6 columnas para las 6 dimensiones
    cols = st.columns(3)
    for idx, dim in enumerate(WPI_DIMENSIONS):
        with cols[idx % 3]:
            score = normalized.get(dim, 0)
            nivel = "🟢 Alto" if score >= 70 else ("🟡 Medio" if score >= 45 else "🔴 Bajo")
            st.metric(
                label=dim,
                value=f"{int(score)}/100",
                delta=nivel,
                delta_color="off"
            )
    
    st.markdown("---")
    
    # === GRÁFICOS ===
    col_radar, col_bars = st.columns(2)
    
    with col_radar:
        st.markdown("#### 🎯 Perfil Radar")
        radar_fig = create_wpi_radar(normalized)
        st.pyplot(radar_fig)
    
    with col_bars:
        st.markdown("#### 📊 Puntajes por Dimensión")
        bar_fig = create_wpi_bars(normalized)
        st.pyplot(bar_fig)
    
    st.markdown("---")
    
    # === ANÁLISIS POR DIMENSIÓN ===
    st.markdown("### 📋 Análisis Detallado por Dimensión")
    
    sorted_scores = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    
    for dim, score in sorted_scores:
        desc_info = WPI_DESCRIPTIONS[dim]
        
        # Determinar nivel
        if score >= 70:
            level = "🟢 Alto"
            text = desc_info["high"]
            color = "#10B981"
        elif score >= 45:
            level = "🟡 Medio"
            text = desc_info["medium"]
            color = "#F59E0B"
        else:
            level = "🔴 Bajo"
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
        st.markdown("### 💪 Fortalezas Destacadas")
        for f in analysis['fortalezas']:
            # Limpiar markdown
            f_clean = f.replace("**", "")
            st.markdown(f"- ✅ {f_clean}")
        st.markdown("")
    
    # === ALERTAS ===
    if analysis.get('alertas'):
        st.markdown("### ⚠️ Áreas de Atención")
        for a in analysis['alertas']:
            # Limpiar markdown
            a_clean = a.replace("**", "").replace("⚠️ ", "")
            st.markdown(f"- 🔸 {a_clean}")
        st.markdown("")
    
    # === ROLES IDEALES ===
    if analysis.get('ideal_para'):
        st.markdown("### 🎯 Roles Ideales para el Candidato")
        for role in analysis['ideal_para']:
            st.markdown(f"- 🎯 {role}")
        st.markdown("")
    
    # === ROLES A EVITAR ===
    if analysis.get('avoid_roles'):
        st.markdown("### ⛔ Roles No Recomendados")
        for role in analysis['avoid_roles']:
            st.markdown(f"- ⛔ {role}")
        st.markdown("")
    
    # === RECOMENDACIONES ===
    if analysis.get('recomendaciones'):
        st.markdown("### 💡 Recomendaciones Específicas")
        for r in analysis['recomendaciones']:
            # Limpiar markdown
            r_clean = r.replace("**", "")
            st.markdown(f"- {r_clean}")
    
    st.markdown("---")
    
    # === DESCARGA DE REPORTES ===
    st.markdown("### 📥 Descargar Reportes")
    
    session_id = session if isinstance(session, str) else session.get("id")
    completed_at = session.get("completed_at") if isinstance(session, dict) else None
    
    # Generar PDF
    pdf_buffer = generate_wpi_pdf(candidate, raw, normalized, radar_fig, session_id, completed_at, analysis)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📑 Descargar PDF Completo",
            data=pdf_buffer.getvalue(),
            file_name=f"wpi_{candidate['cedula']}_{session_id}.pdf",
            mime="application/pdf",
            key=f"pdf_wpi_{session_id}"
        )
    with col2:
        st.download_button(
            "📄 Descargar JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name=f"wpi_{candidate['cedula']}_{session_id}.json",
            mime="application/json",
            key=f"json_wpi_{session_id}"
        )


def show_eri_results_admin(results, candidate, session):
    """
    Muestra los resultados del ERI en el panel de administración.
    
    Args:
        results: Dict con raw, normalized, percentages, validity_score, validity_flags
        candidate: Dict con información del candidato
        session: Dict con información de la sesión o str con session_id
    """
    raw = results.get("raw", {})
    normalized = results.get("normalized", {})
    percentages = results.get("percentages", {})
    validity_score = results.get("validity_score", ERI_VALIDITY_QUESTIONS_COUNT)
    validity_flags = results.get("validity_flags", [])
    
    # Análisis de riesgo
    analysis = analyze_eri_aptitude(normalized, validity_score, validity_flags)
    
    # === BANNER DE VALIDEZ (si aplica) ===
    if analysis.get('validity_warning'):
        st.markdown(f"""
        <div style="background: #FEF2F2; border-left: 5px solid #DC2626;
                    padding: 15px 20px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #FCA5A5;">
            <h4 style="margin: 0; color: #DC2626;">
                ⚠️ ALERTA DE VALIDEZ DEL TEST
            </h4>
            <p style="margin: 5px 0 0 0; color: #991B1B;">{analysis['validity_warning']}</p>
            <p style="margin: 5px 0 0 0; color: #7F1D1D; font-size: 0.9em;">
                El test detectó {len(validity_flags)} respuestas poco realistas. Considerar entrevista profunda adicional.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # === BANNER DE RIESGO ===
    st.markdown(f"""
    <div style="background: {analysis['risk_color']}22; border-left: 5px solid {analysis['risk_color']};
                padding: 15px 20px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: {analysis['risk_color']};">
            {analysis['risk_emoji']} {analysis['risk_level']} — Puntaje: {analysis['risk_score']:.1f}/100
        </h3>
        <p style="margin: 5px 0 0 0; color: #374151;">{analysis['risk_desc']}</p>
        <p style="margin: 5px 0 0 0; color: #6B7280;">
            <b>Dimensión de menor riesgo:</b> {analysis['safest_dimension']} ({int(analysis['safest_score'])}/100) | 
            <b>Dimensión de mayor riesgo:</b> {analysis['riskiest_dimension']} ({int(analysis['riskiest_score'])}/100) |
            <b>Promedio:</b> {analysis['average_score']:.1f}/100
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # === DECISIÓN DE CONTRATACIÓN ===
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;">
        <h4 style="margin: 0 0 10px 0;">📋 Decisión Recomendada de Contratación</h4>
        <h2 style="margin: 0; color: {analysis['risk_color']};">{analysis['hiring_decision']}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # === MÉTRICAS POR DIMENSIÓN ===
    st.markdown("### 📊 Puntajes por Dimensión de Riesgo")
    st.caption("⚠️ Recuerda: Puntajes más ALTOS = MENOR riesgo (Verde ✅), puntajes más BAJOS = MAYOR riesgo (Rojo 🚨)")
    
    # Crear 6 columnas para las 6 dimensiones
    cols = st.columns(3)
    for idx, dim in enumerate(ERI_DIMENSIONS):
        with cols[idx % 3]:
            score = normalized.get(dim, 0)
            if score >= ERI_RISK_THRESHOLDS["low_risk"]:
                nivel = "✅ Bajo Riesgo"
                delta_color = "normal"
            elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
                nivel = "⚠️ Moderado"
                delta_color = "off"
            else:
                nivel = "🚨 Alto Riesgo"
                delta_color = "inverse"
            
            st.metric(
                label=dim,
                value=f"{int(score)}/100",
                delta=nivel,
                delta_color=delta_color
            )
    
    st.markdown("---")
    
    # === GRÁFICOS ===
    col_radar, col_bars = st.columns(2)
    
    with col_radar:
        st.markdown("#### 🎯 Perfil de Riesgo (Radar)")
        radar_fig = create_eri_radar(normalized)
        st.pyplot(radar_fig)
    
    with col_bars:
        st.markdown("#### 📊 Puntajes por Dimensión")
        bar_fig = create_eri_bars(normalized)
        st.pyplot(bar_fig)
    
    st.markdown("---")
    
    # === ANÁLISIS POR DIMENSIÓN ===
    st.markdown("### 📋 Análisis Detallado por Dimensión")
    
    sorted_scores = sorted(normalized.items(), key=lambda x: x[1], reverse=False)  # Menor a mayor (más riesgo primero)
    
    for dim, score in sorted_scores:
        desc_info = ERI_DESCRIPTIONS[dim]
        
        # Determinar nivel de riesgo
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            level = "✅ Bajo Riesgo"
            text = desc_info["low_risk"]
            color = "#10B981"
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            level = "⚠️ Riesgo Moderado"
            text = desc_info["medium_risk"]
            color = "#F59E0B"
        else:
            level = "🚨 Alto Riesgo"
            text = desc_info["high_risk"]
            color = "#EF4444"
        
        st.markdown(f"""
        <div style="background: {color}15; border-left: 3px solid {color}; 
                    padding: 12px; border-radius: 6px; margin-bottom: 10px;">
            <b style="color: {color};">{desc_info['title']}</b> — {level} ({int(score)}/100)
            <br><span style="color: #374151;">{text}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === ASPECTOS POSITIVOS ===
    if analysis.get('fortalezas'):
        st.markdown("### 💚 Aspectos Positivos (Bajo Riesgo)")
        for f in analysis['fortalezas']:
            # Limpiar markdown
            f_clean = f.replace("**", "")
            st.markdown(f"- ✅ {f_clean}")
        st.markdown("")
    
    # === SEÑALES DE ALERTA ===
    if analysis.get('alertas'):
        st.markdown("### 🚨 Señales de Alerta y Factores de Riesgo")
        for a in analysis['alertas']:
            # Limpiar markdown
            a_clean = a.replace("**", "").replace("⚠️ ", "").replace("🚨 ", "")
            st.markdown(f"- 🔴 {a_clean}")
        st.markdown("")
    
    # === RECOMENDACIONES DE CONTRATACIÓN ===
    if analysis.get('recomendaciones'):
        st.markdown("### 💼 Recomendaciones de Contratación")
        for r in analysis['recomendaciones']:
            # Limpiar markdown (pero mantener bullets internos)
            r_clean = r.replace("**", "")
            st.markdown(f"{r_clean}")
        st.markdown("")
    
    # === DETALLES DE VALIDEZ ===
    if validity_flags and len(validity_flags) > 0:
        with st.expander(f"⚠️ Ver Detalles de Validez del Test ({len(validity_flags)} respuestas sospechosas)"):
            st.markdown(f"""
            Se detectaron **{len(validity_flags)}** respuestas poco realistas en preguntas de validez.
            
            Esto puede indicar:
            - El candidato está tratando de presentarse de forma irrealmente perfecta
            - Falta de sinceridad en las respuestas
            - No comprendió las instrucciones
            
            **Recomendación:** Explorar estos aspectos en entrevista personal.
            """)
            
            st.markdown("**Ejemplos de respuestas sospechosas:**")
            for flag in validity_flags[:10]:  # Mostrar máximo 10
                st.markdown(f"- {flag}")
            if len(validity_flags) > 10:
                st.caption(f"... y {len(validity_flags) - 10} respuestas más.")
    
    st.markdown("---")
    
    # === DESCARGA DE REPORTES ===
    st.markdown("### 📥 Descargar Reportes")
    
    session_id = session if isinstance(session, str) else session.get("id")
    completed_at = session.get("completed_at") if isinstance(session, dict) else None
    
    # Generar PDF
    pdf_buffer = generate_eri_pdf(candidate, raw, normalized, radar_fig, session_id, completed_at, analysis, validity_score, validity_flags)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📑 Descargar PDF Completo",
            data=pdf_buffer.getvalue(),
            file_name=f"eri_{candidate['cedula']}_{session_id}.pdf",
            mime="application/pdf",
            key=f"pdf_eri_{session_id}"
        )
    with col2:
        st.download_button(
            "📄 Descargar JSON",
            data=json.dumps(results, indent=2, ensure_ascii=False),
            file_name=f"eri_{candidate['cedula']}_{session_id}.json",
            mime="application/json",
            key=f"json_eri_{session_id}"
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
    evaluador_nombre = admin.get("name", "Administrador") if admin else "Administrador"
    
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
            
            # Actualizar session y recargar
            st.rerun()
    
    if st.button("❌ Cancelar Evaluación"):
        if "desempeno_session_id" in st.session_state:
            del st.session_state["desempeno_session_id"]
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
            objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
            nivel = DESEMPENO_ESCALA_RENDIMIENTO[score]
            
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
            dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
            
            col_dim1, col_dim2 = st.columns([3, 1])
            with col_dim1:
                st.markdown(f"**{dimension['nombre']}**")
                st.caption(dimension['descripcion'])
                with st.expander("📄 Ver descripción del nivel asignado"):
                    st.info(dimension['niveles'][score])
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
# CANDIDATE: LOGIN
# -------------------------------------------------------------------------
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
                candidate = db.get_candidate_by_cedula(cedula.strip())
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

    pending = db.get_pending_sessions_for_candidate(candidate["id"])
    # Filtrar evaluaciones de desempeño (las completa el admin, no el candidato)
    pending = [s for s in pending if s["test_type"] != "desempeno"]
    st.session_state.pending_sessions = pending

    st.markdown(f"## Bienvenido/a, {candidate['name']}")
    st.markdown("Tienes las siguientes evaluaciones asignadas:")

    if not pending:
        st.info("✅ No tienes evaluaciones pendientes. ¡Gracias!")
        if st.button("🔑 Cerrar Sesión"):
            for key in ["candidate", "pending_sessions", "test_session", "disc_questions", "disc_page", "disc_answers", "valanti_responses", "valanti_page"]:
                st.session_state.pop(key, None)
            nav("home")
            st.rerun()
        return

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
        else:
            test_emoji = "📝"
            test_name = "Evaluación"
        
        status_text = "En progreso ▶️" if sess["status"] == "in_progress" else "Pendiente ⏳"

        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"### {test_emoji} {test_name}")
                st.caption(f"ID: {sess['id']} | Tiempo: {sess['time_limit_minutes']} min | Estado: {status_text}")
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

                    st.session_state.test_session = sess
                    if sess["status"] == "pending":
                        db.start_test_session(sess["id"])
                        st.session_state.test_session["status"] = "in_progress"
                        st.session_state.test_session["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                    st.rerun()

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


# =========================================================================
# MAIN ROUTING
# =========================================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

page = st.session_state.page

PAGE_MAP = {
    "home": page_home,
    "admin_login": page_admin_login,
    "admin_dashboard": page_admin_dashboard,
    "candidate_login": page_candidate_login,
    "candidate_select_test": page_candidate_select_test,
    "disc_test": page_disc_test,
    "valanti_test": page_valanti_test,
    "wpi_test": page_wpi_test,
    "eri_test": page_eri_test,
    "talent_map_test": page_talent_map_test,
    "desempeno_eval": page_desempeno_eval,
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

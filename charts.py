"""
Funciones de generación de gráficos (matplotlib) para todas las pruebas.
"""
import numpy as np
import matplotlib.pyplot as plt
from constants import *


def create_disc_plot(normalized_score):
    categories = ["D", "I", "S", "C"]
    labels = ["D\nDominancia", "I\nInfluencia", "S\nEstabilidad", "C\nCumplimiento"]
    disc_colors = {"D": "#EF4444", "I": "#F59E0B", "S": "#10B981", "C": "#3B82F6"}
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5), gridspec_kw={'width_ratios': [3, 2]})
    
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
    
    ax2 = fig.add_subplot(122, projection='polar')
    ax2.set_theta_offset(np.pi / 2)
    ax2.set_theta_direction(-1)
    ax2.set_ylim(0, 1.01)
    
    for i, s in enumerate(categories):
        ax2.bar(angles[i], scaled[s], width=np.pi/2.5, alpha=0.35, color=disc_colors[s], edgecolor=disc_colors[s], linewidth=2)
    
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
    """
    disc_colors = {"D": "#EF4444", "I": "#F59E0B", "S": "#10B981", "C": "#3B82F6"}
    sub_to_disc_idx = {0: "D", 1: "I", 2: "S", 3: "C"}

    n_styles = len(behavioral_styles)
    fig, axes = plt.subplots(n_styles, 1, figsize=(10, n_styles * 1.3 + 1))
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
        ax.set_facecolor('#F8FAFC' if ax_idx % 2 == 0 else '#FFFFFF')
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
    
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    
    ax.plot(angles, vals, "o-", linewidth=2.5, color="#6366F1", markersize=10, 
            markerfacecolor="#818CF8", markeredgecolor="white", markeredgewidth=2, zorder=5)
    ax.fill(angles, vals, alpha=0.15, color="#6366F1")
    
    for i, (angle, val) in enumerate(zip(angles[:-1], vals[:-1])):
        color = valanti_radar_colors[i]
        ax.plot(angle, val, "o", markersize=14, color=color, zorder=6, markeredgecolor='white', markeredgewidth=2)
        ax.text(angle, val + 6, str(val), ha='center', va='center', fontsize=10, fontweight='bold', color=color)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=12, fontweight="bold", color='#1E293B')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 50, 60, 80])
    ax.set_yticklabels(['20', '40', '50', '60', '80'], fontsize=8, color='#94A3B8')
    
    ref = [50] * (len(cats) + 1)
    ax.plot(angles, ref, "--", linewidth=1.5, color="#F59E0B", alpha=0.6, label="Promedio (50)")
    
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, 40, alpha=0.05, color='#EF4444')
    ax.fill_between(theta, 55, 100, alpha=0.05, color='#10B981')
    
    ax.grid(True, alpha=0.2, color='#CBD5E1')
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    plt.title("Perfil Valoral - VALANTI", fontsize=15, fontweight="bold", pad=25, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=10)
    return fig


def create_valanti_bars(direct_scores, standard_scores):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))
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
    ax2.axhspan(0, 40, alpha=0.04, color='#EF4444')
    ax2.axhspan(55, max(sv)*1.3 if max(sv) > 0 else 100, alpha=0.04, color='#10B981')
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
    dimensions = WPI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    values_closed = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    dim_colors = [WPI_COLORS[dim] for dim in dimensions]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.plot(angles_closed, values_closed, "o-", linewidth=2.5, color="#6366F1", 
            markersize=8, markerfacecolor="#818CF8", markeredgecolor="white", 
            markeredgewidth=2, zorder=5)
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#6366F1")
    
    for i, (angle, val, color) in enumerate(zip(angles, values, dim_colors)):
        ax.plot(angle, val, "o", markersize=16, color=color, zorder=6, 
                markeredgecolor='white', markeredgewidth=2.5)
        ax.text(angle, val + 7, f"{int(val)}", ha='center', va='center', 
                fontsize=11, fontweight='bold', color=color)
    
    ax.set_xticks(angles)
    ax.set_xticklabels(dimensions, fontsize=11, fontweight="bold", color='#1E293B')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9, color='#94A3B8')
    
    ref_50 = [50] * (len(dimensions) + 1)
    ref_70 = [70] * (len(dimensions) + 1)
    ax.plot(angles_closed, ref_50, "--", linewidth=1.5, color="#F59E0B", 
            alpha=0.6, label="Promedio (50)")
    ax.plot(angles_closed, ref_70, ":", linewidth=1.5, color="#10B981", 
            alpha=0.6, label="Alto (70)")
    
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, 45, alpha=0.04, color='#EF4444')
    ax.fill_between(theta, 70, 100, alpha=0.05, color='#10B981')
    
    ax.grid(True, alpha=0.3, color='#CBD5E1', linestyle='-', linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    plt.title("Perfil de Personalidad Laboral - WPI", fontsize=16, fontweight="bold", 
              pad=30, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=10)
    plt.tight_layout()
    return fig


def create_wpi_bars(normalized_scores):
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('white')
    
    dimensions = WPI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    colors = [WPI_COLORS[dim] for dim in dimensions]
    
    y_positions = np.arange(len(dimensions))
    bars = ax.barh(y_positions, values, color=colors, alpha=0.85, 
                   edgecolor='white', linewidth=2, height=0.7)
    
    for i, (bar, val, color) in enumerate(zip(bars, values, colors)):
        ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}/100", 
                va='center', fontweight='bold', fontsize=12, color=color)
    
    ax.axvline(x=50, color="#F59E0B", linestyle="--", alpha=0.7, linewidth=2, label="Promedio (50)")
    ax.axvline(x=70, color="#10B981", linestyle=":", alpha=0.7, linewidth=2, label="Alto (70)")
    ax.axvspan(0, 45, alpha=0.05, color='#EF4444')
    ax.axvspan(70, 100, alpha=0.05, color='#10B981')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(dimensions, fontsize=12, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Puntaje (0-100)', fontsize=12, fontweight='bold', color='#475569')
    ax.set_xlim(0, 105)
    ax.set_ylim(-0.5, len(dimensions) - 0.5)
    ax.set_title("Dimensiones de Personalidad Laboral", fontsize=14, 
                 fontweight="bold", pad=20, color='#1E293B')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='x', colors='#94A3B8')
    ax.tick_params(axis='y', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    ax.legend(fontsize=10, loc='lower right', framealpha=0.95)
    plt.tight_layout()
    return fig


def create_eri_radar(normalized_scores):
    """
    Crea radar para el ERI. Valores altos = BAJO riesgo (verde).
    """
    dimensions = ERI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    values_closed = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    dim_colors = [ERI_COLORS[dim] for dim in dimensions]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.plot(angles_closed, values_closed, "o-", linewidth=3, color="#6366F1", 
            markersize=10, markerfacecolor="#818CF8", markeredgecolor="white", 
            markeredgewidth=2.5, zorder=5)
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#6366F1")
    
    for i, (angle, val, color) in enumerate(zip(angles, values, dim_colors)):
        if val >= ERI_RISK_THRESHOLDS["low_risk"]:
            point_color = "#10B981"
        elif val >= ERI_RISK_THRESHOLDS["medium_risk"]:
            point_color = "#F59E0B"
        else:
            point_color = "#EF4444"
        
        ax.plot(angle, val, "o", markersize=18, color=point_color, zorder=6, 
                markeredgecolor='white', markeredgewidth=3)
        ax.text(angle, val + 7, f"{int(val)}", ha='center', va='center', 
                fontsize=12, fontweight='bold', color=point_color)
    
    ax.set_xticks(angles)
    labels = []
    for dim in dimensions:
        if len(dim) > 15:
            words = dim.split()
            if len(words) >= 2:
                mid = len(words) // 2
                labels.append(f"{' '.join(words[:mid])}\n{' '.join(words[mid:])}")
            else:
                labels.append(dim)
        else:
            labels.append(dim)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold", color='#1E293B')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 66, 80, 100])
    ax.set_yticklabels(['20', '40', '66\n(Umbral)', '80', '100'], fontsize=9, color='#94A3B8')
    
    ref_low_risk = [ERI_RISK_THRESHOLDS["low_risk"]] * (len(dimensions) + 1)
    ref_medium_risk = [ERI_RISK_THRESHOLDS["medium_risk"]] * (len(dimensions) + 1)
    ax.plot(angles_closed, ref_low_risk, "-", linewidth=2, color="#10B981", 
            alpha=0.7, label="Bajo Riesgo (≥66)")
    ax.plot(angles_closed, ref_medium_risk, "--", linewidth=2, color="#F59E0B", 
            alpha=0.7, label="Riesgo Moderado (≥41)")
    
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, ERI_RISK_THRESHOLDS["medium_risk"], alpha=0.08, color='#EF4444')
    ax.fill_between(theta, ERI_RISK_THRESHOLDS["medium_risk"], ERI_RISK_THRESHOLDS["low_risk"], 
                     alpha=0.06, color='#F59E0B')
    ax.fill_between(theta, ERI_RISK_THRESHOLDS["low_risk"], 100, alpha=0.08, color='#10B981')
    
    ax.grid(True, alpha=0.3, color='#CBD5E1', linestyle='-', linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    plt.title("Perfil de Riesgo e Integridad - ERI\n(Puntajes altos = BAJO riesgo)", 
              fontsize=16, fontweight="bold", pad=35, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.tight_layout()
    return fig


def create_eri_bars(normalized_scores):
    """
    Barras horizontales para el ERI. Valores altos = BAJO riesgo.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('white')
    
    dimensions = ERI_DIMENSIONS
    values = [normalized_scores[dim] for dim in dimensions]
    
    colors = []
    for val in values:
        if val >= ERI_RISK_THRESHOLDS["low_risk"]:
            colors.append("#10B981")
        elif val >= ERI_RISK_THRESHOLDS["medium_risk"]:
            colors.append("#F59E0B")
        else:
            colors.append("#EF4444")
    
    y_positions = np.arange(len(dimensions))
    bars = ax.barh(y_positions, values, color=colors, alpha=0.85, 
                   edgecolor='white', linewidth=2.5, height=0.7)
    
    for i, (bar, val, color) in enumerate(zip(bars, values, colors)):
        if val >= ERI_RISK_THRESHOLDS["low_risk"]:
            risk_label = "✅ Bajo Riesgo"
        elif val >= ERI_RISK_THRESHOLDS["medium_risk"]:
            risk_label = "⚠️ Moderado"
        else:
            risk_label = "🚨 Alto Riesgo"
        
        ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}  {risk_label}", 
                va='center', fontweight='bold', fontsize=11, color=color)
    
    ax.axvline(x=ERI_RISK_THRESHOLDS["low_risk"], color="#10B981", linestyle="-", 
               alpha=0.8, linewidth=2.5, label="Bajo Riesgo (≥66)")
    ax.axvline(x=ERI_RISK_THRESHOLDS["medium_risk"], color="#F59E0B", linestyle="--", 
               alpha=0.8, linewidth=2.5, label="Riesgo Moderado (≥41)")
    ax.axvspan(0, ERI_RISK_THRESHOLDS["medium_risk"], alpha=0.08, color='#EF4444')
    ax.axvspan(ERI_RISK_THRESHOLDS["medium_risk"], ERI_RISK_THRESHOLDS["low_risk"], 
               alpha=0.06, color='#F59E0B')
    ax.axvspan(ERI_RISK_THRESHOLDS["low_risk"], 100, alpha=0.08, color='#10B981')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(dimensions, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Puntaje (0-100) - Mayor puntaje = MENOR riesgo', fontsize=12, 
                  fontweight='bold', color='#475569')
    ax.set_xlim(0, 110)
    ax.set_ylim(-0.5, len(dimensions) - 0.5)
    ax.set_title("Evaluación de Riesgo e Integridad por Dimensión", fontsize=15, 
                 fontweight="bold", pad=20, color='#1E293B')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='x', colors='#94A3B8')
    ax.tick_params(axis='y', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    ax.legend(fontsize=11, loc='lower right', framealpha=0.95)
    plt.tight_layout()
    return fig


def create_talent_map_radar(normalized_scores, job_profile_scores=None):
    competencies = TALENT_MAP_COMPETENCIES
    values = [normalized_scores[comp] for comp in competencies]
    values_closed = values + [values[0]]
    angles = np.linspace(0, 2 * np.pi, len(competencies), endpoint=False).tolist()
    angles_closed = angles + [angles[0]]
    
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    
    ax.plot(angles_closed, values_closed, "o-", linewidth=3.5, color="#6366F1", 
            markersize=12, markerfacecolor="#818CF8", markeredgecolor="white", 
            markeredgewidth=3, zorder=5, label="Candidato")
    ax.fill(angles_closed, values_closed, alpha=0.2, color="#6366F1")
    
    if job_profile_scores:
        profile_values = [job_profile_scores[comp] for comp in competencies]
        profile_values_closed = profile_values + [profile_values[0]]
        ax.plot(angles_closed, profile_values_closed, "s--", linewidth=2.5, color="#EF4444", 
                markersize=8, markerfacecolor="#FCA5A5", markeredgecolor="white", 
                markeredgewidth=2, zorder=4, label="Perfil Requerido", alpha=0.8)
        ax.fill(angles_closed, profile_values_closed, alpha=0.15, color="#EF4444")
    
    for i, (angle, val) in enumerate(zip(angles, values)):
        comp = competencies[i]
        point_color = TALENT_MAP_COLORS[comp]
        ax.plot(angle, val, "o", markersize=16, color=point_color, zorder=6, 
                markeredgecolor='white', markeredgewidth=2.5)
        ax.text(angle, val + 6, f"{int(val)}", ha='center', va='center', 
                fontsize=11, fontweight='bold', color=point_color)
    
    ax.set_xticks(angles)
    labels = []
    for comp in competencies:
        if len(comp) > 15:
            words = comp.split()
            if len(words) >= 2:
                mid = len(words) // 2
                labels.append(f"{' '.join(words[:mid])}\n{' '.join(words[mid:])}")
            else:
                labels.append(comp)
        else:
            labels.append(comp)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold", color='#1E293B')
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25', '50\n(Promedio)', '75', '100'], fontsize=9, color='#94A3B8')
    
    ref_levels = [[50] * (len(competencies) + 1), [75] * (len(competencies) + 1)]
    ax.plot(angles_closed, ref_levels[0], ":", linewidth=1.5, color="#94A3B8", 
            alpha=0.6, label="Nivel Promedio (50)")
    ax.plot(angles_closed, ref_levels[1], "--", linewidth=1.5, color="#10B981", 
            alpha=0.6, label="Nivel Alto (75)")
    
    theta = np.linspace(0, 2*np.pi, 100)
    ax.fill_between(theta, 0, 50, alpha=0.05, color='#EF4444')
    ax.fill_between(theta, 50, 75, alpha=0.05, color='#F59E0B')
    ax.fill_between(theta, 75, 100, alpha=0.08, color='#10B981')
    
    ax.grid(True, alpha=0.3, color='#CBD5E1', linestyle='-', linewidth=0.8)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor('#FAFBFC')
    fig.patch.set_facecolor('white')
    
    title = "Mapeo de Competencias y Talentos"
    if job_profile_scores:
        title += "\n(Candidato vs. Perfil Requerido)"
    plt.title(title, fontsize=16, fontweight="bold", pad=40, color='#1E293B')
    plt.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=11)
    plt.tight_layout()
    return fig


def create_talent_map_bars(normalized_scores, job_profile_scores=None):
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor('white')
    
    competencies = TALENT_MAP_COMPETENCIES
    values = [normalized_scores[comp] for comp in competencies]
    y_positions = np.arange(len(competencies))
    bar_height = 0.35 if job_profile_scores else 0.7
    
    colors = []
    for val in values:
        if val >= 75:
            colors.append("#10B981")
        elif val >= 50:
            colors.append("#F59E0B")
        else:
            colors.append("#EF4444")
    
    if job_profile_scores:
        bars1 = ax.barh(y_positions - bar_height/2, values, bar_height, 
                       color=colors, alpha=0.85, edgecolor='white', 
                       linewidth=2, label="Candidato")
        profile_values = [job_profile_scores[comp] for comp in competencies]
        bars2 = ax.barh(y_positions + bar_height/2, profile_values, bar_height, 
                       color="#94A3B8", alpha=0.7, edgecolor='white', 
                       linewidth=2, label="Perfil Requerido")
        for bar, val in zip(bars1, values):
            ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}", 
                    va='center', fontweight='bold', fontsize=10, color='#1E293B')
        for bar, val in zip(bars2, profile_values):
            ax.text(val + 2, bar.get_y() + bar.get_height()/2, f"{int(val)}", 
                    va='center', fontweight='bold', fontsize=10, color='#64748B')
    else:
        bars = ax.barh(y_positions, values, bar_height, color=colors, 
                      alpha=0.85, edgecolor='white', linewidth=2.5)
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
    
    ax.axvline(x=50, color="#94A3B8", linestyle=":", alpha=0.6, linewidth=2, label="Nivel Promedio (50)")
    ax.axvline(x=75, color="#10B981", linestyle="--", alpha=0.7, linewidth=2, label="Nivel Alto (75)")
    ax.axvspan(0, 50, alpha=0.05, color='#EF4444')
    ax.axvspan(50, 75, alpha=0.05, color='#F59E0B')
    ax.axvspan(75, 100, alpha=0.08, color='#10B981')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(competencies, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Puntuación (0-100)', fontsize=12, fontweight='bold', color='#475569')
    ax.set_xlim(0, 110)
    ax.set_ylim(-0.5, len(competencies) - 0.5)
    
    title = "Evaluación de Competencias por Dimensión"
    if job_profile_scores:
        title += "\n(Candidato vs. Perfil Requerido)"
    ax.set_title(title, fontsize=15, fontweight="bold", pad=20, color='#1E293B')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='x', colors='#94A3B8')
    ax.tick_params(axis='y', colors='#475569')
    ax.grid(axis='x', alpha=0.2, color='#CBD5E1', linestyle='-')
    ax.legend(fontsize=11, loc='lower right', framealpha=0.95)
    plt.tight_layout()
    return fig


def create_talent_map_comparison(normalized_scores, job_profile_name, job_profile_scores):
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor('white')
    
    competencies = TALENT_MAP_COMPETENCIES
    gaps = []
    gap_colors = []
    
    for comp in competencies:
        candidate = normalized_scores[comp]
        required = job_profile_scores[comp]
        gap = candidate - required
        gaps.append(gap)
        if gap >= 0:
            gap_colors.append("#10B981")
        elif gap >= -15:
            gap_colors.append("#F59E0B")
        else:
            gap_colors.append("#EF4444")
    
    y_positions = np.arange(len(competencies))
    bars = ax.barh(y_positions, gaps, color=gap_colors, alpha=0.85, 
                   edgecolor='white', linewidth=2.5, height=0.7)
    
    for i, (bar, gap) in enumerate(zip(bars, gaps)):
        comp = competencies[i]
        candidate_score = normalized_scores[comp]
        required_score = job_profile_scores[comp]
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
                va='center', ha=ha, fontweight='bold', fontsize=10, color=gap_colors[i])
        score_text = f"Candidato: {candidate_score:.0f}  |  Requerido: {required_score:.0f}"
        ax.text(-42, bar.get_y() + bar.get_height()/2, score_text, 
                va='center', ha='left', fontsize=9, color='#64748B', style='italic')
    
    ax.axvline(x=0, color='#1E293B', linestyle='-', linewidth=2.5, alpha=0.8)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(competencies, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Gap de Competencia (Candidato - Requerido)', fontsize=12, 
                  fontweight='bold', color='#475569')
    max_abs_gap = max(abs(min(gaps)), abs(max(gaps)))
    ax.set_xlim(-max_abs_gap - 20, max_abs_gap + 20)
    ax.set_ylim(-0.5, len(competencies) - 0.5)
    
    profile_info = TALENT_MAP_JOB_PROFILES[job_profile_name]
    title = f"Análisis de Brechas vs. {profile_info['emoji']} {job_profile_name}\n{profile_info['descripcion']}"
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20, color='#1E293B')
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
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='polar')
    
    dimensiones = [dim["nombre"] for dim in DESEMPENO_DIMENSIONES]
    valores = [float(potencial_scores.get(i+1, potencial_scores.get(str(i+1), 0))) for i in range(5)]
    valores_plot = valores + [valores[0]]
    angulos = [n / 5 * 2 * np.pi for n in range(5)]
    angulos_plot = angulos + [angulos[0]]
    
    ax.plot(angulos_plot, valores_plot, 'o-', linewidth=2.5, color='#3B82F6', markersize=8)
    ax.fill(angulos_plot, valores_plot, alpha=0.25, color='#3B82F6')
    
    for level, color, alpha in [(1, '#FEE2E2', 0.3), (2, '#FEF3C7', 0.3), (3, '#D1FAE5', 0.3)]:
        circle_angles = np.linspace(0, 2 * np.pi, 100)
        circle_values = [level] * 100
        ax.fill(circle_angles, circle_values, color=color, alpha=alpha)
    
    ax.set_ylim(0, 3)
    ax.set_xticks(angulos)
    ax.set_xticklabels(dimensiones, size=11, fontweight='bold', color='#1E293B')
    ax.set_yticks([0.5, 1, 1.5, 2, 2.5, 3])
    ax.set_yticklabels(['', '1', '', '2', '', '3'], size=10, color='#64748B')
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.grid(True, color='#CBD5E1', linestyle='-', linewidth=0.5, alpha=0.7)
    ax.set_facecolor('#FFFFFF')
    ax.set_title('Evaluación de Potencial\n5 Dimensiones', size=14, fontweight='bold', 
                 pad=30, color='#1E293B')
    plt.tight_layout()
    return fig


def create_desempeno_bars(rendimiento_scores):
    """Crea gráfico de barras para los 6 objetivos de rendimiento."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    objetivos = [obj["titulo"] for obj in DESEMPENO_OBJETIVOS]
    # Las claves pueden venir como str o int desde la BD
    valores = [float(rendimiento_scores.get(i+1, rendimiento_scores.get(str(i+1), 0))) for i in range(6)]
    
    colores = []
    for valor in valores:
        if valor >= 4.5:
            colores.append('#10B981')
        elif valor >= 3.5:
            colores.append('#3B82F6')
        elif valor >= 2.5:
            colores.append('#F59E0B')
        elif valor >= 1.5:
            colores.append('#EF4444')
        else:
            colores.append('#991B1B')
    
    y_positions = range(len(objetivos))
    bars = ax.barh(y_positions, valores, color=colores, alpha=0.8, height=0.6, 
                   edgecolor='#1E293B', linewidth=1.5)
    
    for i, (bar, valor) in enumerate(zip(bars, valores)):
        escala = DESEMPENO_ESCALA_RENDIMIENTO.get(int(valor), {})
        label = escala.get("label", "Sin calificar")
        ax.text(valor + 0.15, bar.get_y() + bar.get_height()/2, 
                f'{valor:.1f} - {label}', 
                va='center', ha='left', fontsize=10, fontweight='bold', color='#1E293B')
    
    ax.axvspan(0, 1.5, alpha=0.1, color='#EF4444', label='Insatisfactorio')
    ax.axvspan(1.5, 2.5, alpha=0.1, color='#F59E0B', label='Debajo')
    ax.axvspan(2.5, 3.5, alpha=0.1, color='#3B82F6', label='Cumple')
    ax.axvspan(3.5, 5, alpha=0.1, color='#10B981', label='Supera/Sobresaliente')
    
    ax.set_yticks(y_positions)
    ax.set_yticklabels(objetivos, fontsize=11, fontweight='bold', color='#1E293B')
    ax.set_xlabel('Calificación (1-5)', fontsize=12, fontweight='bold', color='#475569')
    ax.set_xlim(0, 7.5)
    ax.set_title('Evaluación de Rendimiento\n6 Objetivos de Desempeño', 
                 fontsize=14, fontweight='bold', pad=20, color='#1E293B')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CBD5E1')
    ax.spines['left'].set_color('#CBD5E1')
    ax.set_facecolor('#FAFBFC')
    ax.tick_params(axis='both', colors='#475569')
    ax.grid(axis='x', alpha=0.3, color='#CBD5E1', linestyle='--')
    ax.legend(loc='upper right', bbox_to_anchor=(1, -0.08), ncol=4, fontsize=9, framealpha=0.9)
    plt.tight_layout()
    return fig

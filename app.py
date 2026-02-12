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
# CONSTANTES VALANTI
# =========================================================================
VALANTI_PREGUNTAS = [
    ["Muestro dedicación a las personas que amo", "Actúo con perseverancia"],
    ["Soy tolerante", "Prefiero actuar con ética"],
    ["Al pensar, utilizo mi intuición o 'sexto sentido'", "Me siento una persona digna"],
    ["Logro buena concentración mental", "Perdono todas las ofensas de cualquier persona"],
    ["Normalmente razono mucho", "Me destaco por el liderazgo en mis acciones"],
    ["Pienso con integridad", "Me coloco objetivos y metas en mi vida personal"],
    ["Soy una persona de iniciativa", "En mi trabajo normalmente soy curioso"],
    ["Doy amor", "Para pensar hago síntesis de las distintas ideas"],
    ["Me siento en calma", "Pienso con veracidad"],
    ["Irrespetar la propiedad", "Sentir inquietud"],
    ["Ser irrespetable", "Ser desconsiderado hacia cualquier persona"],
    ["Caer en contradicción al pensar", "Sentir intolerancia"],
    ["Ser violento", "Actuar con cobardía"],
    ["Sentirse presumido", "Generar divisiones y discordia entre los seres humanos"],
    ["Ser cruel", "Sentir ira"],
    ["Pensar con confusión", "Tener odio en el corazón"],
    ["Decir blasfemias", "Ser escandaloso"],
    ["Crear desigualdades entre los seres humanos", "Apasionarse por una idea"],
    ["Sentirse inconstante", "Crear rivalidad hacia otros"],
    ["Pensamientos irracionales", "Traicionar a un desconocido"],
    ["Ostentar riquezas materiales", "Sentirse infeliz"],
    ["Entorpecer la comunicación entre seres humanos", "La maldad"],
    ["Odiar a cualquier ser de la naturaleza", "Hacer distinciones entre las personas"],
    ["Sentirse intranquilo", "Ser infiel"],
    ["Tener la mente dispersa", "Mostrar apatía al pensar"],
    ["La injusticia", "Sentirse angustiado"],
    ["Ventajarse de los que odian a todo el mundo", "Vengarse del que hace daño a un familiar"],
    ["Usar abusivamente el poder", "Distraerse"],
    ["Ser desagradecido con los que ayudan", "Ser egoísta con todos"],
    ["Cualquier forma de irrespeto", "Odiar"],
]

VALANTI_TRAITS = {
    "Verdad": [1, 7, 13, 19, 25],
    "Rectitud": [2, 8, 14, 20, 26],
    "Paz": [3, 9, 15, 21, 27],
    "Amor": [4, 10, 16, 22, 28],
    "No Violencia": [5, 11, 17, 23, 29],
}

VALANTI_AVGS = {"Verdad": 15.65, "Rectitud": 21.05, "Paz": 17.35, "Amor": 16.68, "No Violencia": 21.22}
VALANTI_SDS = {"Verdad": 4.7, "Rectitud": 4.44, "Paz": 6.61, "Amor": 5.41, "No Violencia": 7.19}

VALANTI_COLORS = {"Verdad": "#3B82F6", "Rectitud": "#10B981", "Paz": "#8B5CF6", "Amor": "#EF4444", "No Violencia": "#F59E0B"}

VALANTI_DESCRIPTIONS = {
    "Verdad": {
        "title": "🔍 Verdad", "high": "Fuerte inclinación hacia la búsqueda del conocimiento, honestidad intelectual y razonamiento lógico.",
        "low": "Podría beneficiarse de desarrollar más pensamiento analítico y curiosidad intelectual."
    },
    "Rectitud": {
        "title": "⚖️ Rectitud", "high": "Fuerte compromiso con la ética, integridad, perseverancia y disciplina.",
        "low": "Podría fortalecer su sentido de disciplina y compromiso ético."
    },
    "Paz": {
        "title": "☮️ Paz", "high": "Notable capacidad para mantener la calma, serenidad interior, tolerancia y armonía.",
        "low": "Podría trabajar en desarrollar más paciencia y tolerancia."
    },
    "Amor": {
        "title": "❤️ Amor", "high": "Gran capacidad de amar, empatía, compasión y facilidad para perdonar.",
        "low": "Podría beneficiarse de abrir más su corazón y practicar la empatía."
    },
    "No Violencia": {
        "title": "🕊️ No Violencia", "high": "Profundo respeto por la vida y dignidad, promueve cooperación y justicia social.",
        "low": "Podría desarrollar mayor sensibilidad hacia el impacto de sus acciones."
    },
}


# =========================================================================
# ANÁLISIS DE APTITUD Y RECOMENDACIONES
# =========================================================================

# --- Nombres legibles de cada estilo DISC ---
DISC_STYLE_NAMES = {
    "D": "Dominancia",
    "I": "Influencia",
    "S": "Estabilidad",
    "C": "Cumplimiento/Minuciosidad"
}

# --- Recomendaciones por estilo DISC según nivel ---
DISC_RECOMMENDATIONS = {
    "D": {
        "high": {
            "fortalezas": ["Liderazgo natural y toma de decisiones rápida", "Orientación a resultados y metas", "Capacidad para asumir retos y resolver problemas", "Iniciativa y autonomía"],
            "alertas": ["Puede ser percibido como autoritario o impaciente", "Riesgo de conflictos interpersonales por estilo directo", "Puede descuidar el bienestar emocional del equipo"],
            "recomendaciones": ["Desarrollar la escucha activa y empatía con el equipo", "Practicar la delegación efectiva", "Equilibrar la exigencia con el reconocimiento positivo", "Trabajar la paciencia en procesos que requieren consenso"]
        },
        "low": {
            "fortalezas": ["Colaborativo y receptivo a las ideas de otros", "Evita conflictos innecesarios", "Flexible y adaptable"],
            "alertas": ["Puede tener dificultad para tomar decisiones bajo presión", "Riesgo de ser percibido como indeciso o pasivo", "Puede evitar confrontaciones necesarias"],
            "recomendaciones": ["Fortalecer la asertividad y confianza en la toma de decisiones", "Practicar la comunicación directa en situaciones importantes", "Asumir gradualmente roles de mayor responsabilidad"]
        }
    },
    "I": {
        "high": {
            "fortalezas": ["Excelente comunicador y motivador", "Crea ambientes positivos y entusiastas", "Habilidad natural para networking y relaciones", "Persuasivo e inspirador"],
            "alertas": ["Puede perder el enfoque en los detalles", "Riesgo de comprometerse en exceso sin cumplir", "Puede priorizar popularidad sobre efectividad"],
            "recomendaciones": ["Desarrollar disciplina en seguimiento de tareas", "Establecer sistemas de organización personal", "Practicar la gestión del tiempo y priorización", "Equilibrar sociabilidad con productividad"]
        },
        "low": {
            "fortalezas": ["Enfocado y centrado en la tarea", "Trabaja bien de forma independiente", "Analítico y reservado"],
            "alertas": ["Puede tener dificultad para trabajar en equipo", "Riesgo de aislamiento social en el entorno laboral", "Comunicación limitada puede generar malentendidos"],
            "recomendaciones": ["Participar activamente en dinámicas de equipo", "Desarrollar habilidades de presentación y comunicación", "Practicar la colaboración y trabajo grupal"]
        }
    },
    "S": {
        "high": {
            "fortalezas": ["Confiable, leal y consistente", "Excelente trabajo en equipo y colaboración", "Paciente y buen oyente", "Estabilizador del grupo"],
            "alertas": ["Resistencia al cambio y nuevas situaciones", "Puede evitar conflictos necesarios", "Dificultad para expresar desacuerdos"],
            "recomendaciones": ["Desarrollar flexibilidad ante cambios organizacionales", "Practicar la expresión asertiva de opiniones", "Asumir riesgos calculados gradualmente", "Trabajar la adaptabilidad en entornos cambiantes"]
        },
        "low": {
            "fortalezas": ["Adaptable y flexible ante cambios", "Cómodo con la variedad y lo impredecible", "Dinámico y de ritmo rápido"],
            "alertas": ["Puede ser percibido como impaciente o inquieto", "Riesgo de falta de constancia en proyectos largos", "Puede generar inestabilidad en equipos que necesitan estructura"],
            "recomendaciones": ["Cultivar la paciencia en procesos a largo plazo", "Practicar la constancia y seguimiento de rutinas", "Desarrollar mayor empatía con compañeros de ritmo diferente"]
        }
    },
    "C": {
        "high": {
            "fortalezas": ["Analítico y detallista", "Altos estándares de calidad", "Organizado y metódico", "Excelente para análisis de datos y procesos"],
            "alertas": ["Perfeccionismo que puede retrasar entregas", "Puede ser excesivamente crítico consigo mismo y con otros", "Dificultad para tomar decisiones sin información completa"],
            "recomendaciones": ["Aprender a aceptar 'suficientemente bueno' en ciertos contextos", "Practicar la toma de decisiones con información incompleta", "Desarrollar tolerancia a la ambigüedad", "Equilibrar calidad con agilidad"]
        },
        "low": {
            "fortalezas": ["Flexible con las reglas y procedimientos", "Cómodo con la ambigüedad", "Rápido para actuar sin parálisis por análisis"],
            "alertas": ["Puede descuidar detalles importantes", "Riesgo de errores por falta de verificación", "Puede resistir normas y procesos establecidos"],
            "recomendaciones": ["Implementar listas de verificación para tareas críticas", "Desarrollar atención al detalle en áreas clave", "Respetar procedimientos y estándares de calidad"]
        }
    }
}

# --- Recomendaciones combinadas para perfiles DISC dominantes ---
DISC_PROFILE_RECOMMENDATIONS = {
    "DI": {
        "perfil": "Líder Inspirador",
        "ideal_para": ["Ventas y desarrollo de negocios", "Liderazgo de equipos comerciales", "Emprendimiento", "Roles que requieran persuasión y acción rápida"],
        "cuidado_en": ["Roles muy analíticos o rutinarios", "Posiciones que requieran paciencia extrema", "Tareas con muchos detalles técnicos"]
    },
    "DS": {
        "perfil": "Líder Estable",
        "ideal_para": ["Gerencia intermedia", "Coordinación de proyectos", "Roles que combinen liderazgo con estabilidad"],
        "cuidado_en": ["Ambientes muy dinámicos y cambiantes", "Roles que requieran sociabilidad constante"]
    },
    "DC": {
        "perfil": "Estratega Analítico",
        "ideal_para": ["Dirección de proyectos complejos", "Consultoría estratégica", "Ingeniería y tecnología", "Roles de auditoría y control"],
        "cuidado_en": ["Roles con alta interacción social", "Posiciones que requieran alta flexibilidad"]
    },
    "ID": {
        "perfil": "Comunicador Dinámico",
        "ideal_para": ["Relaciones públicas", "Marketing y publicidad", "Capacitación y formación", "Roles creativos con liderazgo"],
        "cuidado_en": ["Roles muy estructurados", "Posiciones con poco contacto humano"]
    },
    "IS": {
        "perfil": "Facilitador Empático",
        "ideal_para": ["Recursos Humanos", "Servicio al cliente premium", "Coaching y mentoría", "Roles de bienestar organizacional"],
        "cuidado_en": ["Roles de alta presión competitiva", "Posiciones que requieran confrontación frecuente"]
    },
    "IC": {
        "perfil": "Comunicador Preciso",
        "ideal_para": ["Investigación de mercados", "Capacitación técnica", "Consultoría", "Roles analíticos con presentación"],
        "cuidado_en": ["Roles puramente operativos", "Ambientes de alta tensión"]
    },
    "SD": {
        "perfil": "Ejecutor Confiable",
        "ideal_para": ["Operaciones y logística", "Supervisión de equipos operativos", "Administración", "Roles de implementación"],
        "cuidado_en": ["Roles de venta agresiva", "Posiciones de cambio constante"]
    },
    "SI": {
        "perfil": "Colaborador Armonioso",
        "ideal_para": ["Trabajo social", "Atención al cliente", "Educación", "Roles de soporte y asistencia"],
        "cuidado_en": ["Roles competitivos individuales", "Posiciones de toma de decisiones rápidas"]
    },
    "SC": {
        "perfil": "Especialista Metódico",
        "ideal_para": ["Contabilidad y finanzas", "Control de calidad", "Archivo y documentación", "Roles técnicos especializados"],
        "cuidado_en": ["Roles de liderazgo de alta presión", "Posiciones con mucha improvisación"]
    },
    "CD": {
        "perfil": "Analista Determinado",
        "ideal_para": ["Ingeniería", "Análisis financiero", "Desarrollo de software", "Roles de investigación con impacto"],
        "cuidado_en": ["Roles de ventas directas", "Posiciones muy sociales"]
    },
    "CI": {
        "perfil": "Analista Comunicativo",
        "ideal_para": ["Investigación y desarrollo", "Docencia universitaria", "Consultoría especializada", "Roles analíticos con interacción"],
        "cuidado_en": ["Roles operativos repetitivos", "Posiciones de alta agresividad comercial"]
    },
    "CS": {
        "perfil": "Ejecutor Preciso",
        "ideal_para": ["Calidad y procesos", "Administración", "Soporte técnico", "Roles de cumplimiento normativo"],
        "cuidado_en": ["Roles de innovación disruptiva", "Posiciones de alta presión social"]
    }
}


def analyze_disc_aptitude(normalized, relative):
    """Analiza los resultados DISC y genera recomendaciones, fortalezas, alertas y nivel de aptitud."""
    
    # Determinar estilos dominante y secundario
    sorted_styles = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_styles[0]
    secondary = sorted_styles[1]
    weakest = sorted_styles[-1]
    
    dominant_style = dominant[0]
    secondary_style = secondary[0]
    dominant_score = dominant[1]
    secondary_score = secondary[1]
    weakest_score = weakest[1]
    
    # Determinar perfil combinado
    profile_key = dominant_style + secondary_style
    profile_info = DISC_PROFILE_RECOMMENDATIONS.get(profile_key, {})
    
    # Calcular nivel de aptitud general (0-100)
    # Basado en: claridad del perfil (diferenciación entre estilos) y balance general
    score_range = dominant_score - weakest_score
    balance_score = 100 - abs(50 - (sum(normalized.values()) / 4))  # Qué tan centrado está
    differentiation = min(score_range * 1.5, 100)  # Qué tan claro es el perfil
    
    # Un perfil claro (buena diferenciación) con al menos un estilo bien definido es positivo
    aptitude_score = round((differentiation * 0.6 + balance_score * 0.4))
    aptitude_score = max(0, min(100, aptitude_score))
    
    # Determinar nivel de aptitud
    if aptitude_score >= 70:
        aptitude_level = "APTO"
        aptitude_color = "#10B981"  # verde
        aptitude_emoji = "✅"
        aptitude_desc = "Perfil DISC claramente definido. El candidato muestra un patrón conductual coherente y diferenciado."
    elif aptitude_score >= 45:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"  # amarillo
        aptitude_emoji = "⚠️"
        aptitude_desc = "Perfil DISC con áreas que requieren atención. Se recomienda considerar las observaciones para el cargo."
    else:
        aptitude_level = "REQUIERE EVALUACIÓN ADICIONAL"
        aptitude_color = "#EF4444"  # rojo
        aptitude_emoji = "🔴"
        aptitude_desc = "Perfil DISC poco diferenciado. Se sugiere complementar con entrevista por competencias u otra evaluación."
    
    # Obtener fortalezas y alertas del estilo dominante
    dom_level = "high" if dominant_score >= 55 else "low"
    sec_level = "high" if secondary_score >= 55 else "low"
    
    fortalezas = DISC_RECOMMENDATIONS[dominant_style][dom_level]["fortalezas"]
    alertas = DISC_RECOMMENDATIONS[dominant_style][dom_level]["alertas"]
    recomendaciones = DISC_RECOMMENDATIONS[dominant_style][dom_level]["recomendaciones"]
    
    # Agregar info del estilo secundario
    sec_fortalezas = DISC_RECOMMENDATIONS[secondary_style][sec_level]["fortalezas"][:2]
    sec_alertas = DISC_RECOMMENDATIONS[secondary_style][sec_level]["alertas"][:1]
    
    return {
        "aptitude_score": aptitude_score,
        "aptitude_level": aptitude_level,
        "aptitude_color": aptitude_color,
        "aptitude_emoji": aptitude_emoji,
        "aptitude_desc": aptitude_desc,
        "dominant_style": dominant_style,
        "dominant_name": DISC_STYLE_NAMES[dominant_style],
        "dominant_score": dominant_score,
        "secondary_style": secondary_style,
        "secondary_name": DISC_STYLE_NAMES[secondary_style],
        "secondary_score": secondary_score,
        "profile_key": profile_key,
        "profile_name": profile_info.get("perfil", f"{DISC_STYLE_NAMES[dominant_style]}-{DISC_STYLE_NAMES[secondary_style]}"),
        "ideal_para": profile_info.get("ideal_para", []),
        "cuidado_en": profile_info.get("cuidado_en", []),
        "fortalezas": fortalezas + sec_fortalezas,
        "alertas": alertas + sec_alertas,
        "recomendaciones": recomendaciones,
    }


def analyze_valanti_aptitude(standard):
    """Analiza los resultados VALANTI y genera recomendaciones, fortalezas, alertas y nivel de aptitud."""
    
    sorted_values = sorted(standard.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_values[0]
    second = sorted_values[1]
    weakest = sorted_values[-1]
    second_weakest = sorted_values[-2]
    
    # Evaluar aptitud basada en valores
    # Un candidato "apto" tiene al menos 2 valores en rango alto (>=55) y ninguno críticamente bajo (<35)
    high_values = [v for v, s in standard.items() if s >= 55]
    low_values = [v for v, s in standard.items() if s < 40]
    critical_values = [v for v, s in standard.items() if s < 30]
    avg_score = sum(standard.values()) / len(standard)
    
    # Calcular puntaje de aptitud
    aptitude_score = round(avg_score + len(high_values) * 5 - len(low_values) * 8 - len(critical_values) * 15)
    aptitude_score = max(0, min(100, aptitude_score))
    
    if len(critical_values) > 0:
        aptitude_level = "REQUIERE EVALUACIÓN ADICIONAL"
        aptitude_color = "#EF4444"
        aptitude_emoji = "🔴"
        aptitude_desc = f"Valores críticamente bajos detectados en: {', '.join(critical_values)}. Se recomienda entrevista profunda sobre ética y valores."
    elif len(low_values) >= 2:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = f"Valores por debajo del promedio en: {', '.join(low_values)}. Considerar programas de desarrollo en estas áreas."
    elif avg_score >= 50 and len(high_values) >= 2:
        aptitude_level = "APTO"
        aptitude_color = "#10B981"
        aptitude_emoji = "✅"
        aptitude_desc = "Perfil de valores sólido y equilibrado. El candidato demuestra una base ética consistente."
    else:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = "Perfil de valores en rango promedio. Se sugiere profundizar en entrevista sobre valores organizacionales."
    
    # Generar fortalezas
    fortalezas = []
    for value, score in sorted_values:
        if score >= 55:
            desc = VALANTI_DESCRIPTIONS[value]
            fortalezas.append(f"{value} (T={score}): {desc['high']}")
    
    # Generar alertas
    alertas = []
    for value, score in sorted_values:
        if score < 40:
            desc = VALANTI_DESCRIPTIONS[value]
            alertas.append(f"{value} (T={score}): {desc['low']}")
    
    # Generar recomendaciones según perfil
    recomendaciones = []
    
    VALANTI_RECS = {
        "Verdad": {
            "high": "Aprovechar su capacidad analítica e intelectual asignando tareas de investigación y resolución de problemas complejos.",
            "low": "Fomentar la curiosidad intelectual mediante capacitaciones, lecturas y exposición a nuevos conceptos.",
        },
        "Rectitud": {
            "high": "Ideal para roles que requieran integridad, cumplimiento de normas y ética profesional.",
            "low": "Reforzar el compromiso con normas y procesos. Incluir en programas de ética organizacional.",
        },
        "Paz": {
            "high": "Eficaz en mediación de conflictos y roles que requieran calma bajo presión.",
            "low": "Brindar herramientas de manejo de estrés y técnicas de relajación. Considerar carga laboral.",
        },
        "Amor": {
            "high": "Excelente para trabajo en equipo, mentoría y roles de servicio al cliente.",
            "low": "Desarrollar la empatía mediante dinámicas de grupo y ejercicios de inteligencia emocional.",
        },
        "No Violencia": {
            "high": "Promotor natural de ambientes de trabajo respetuosos e inclusivos.",
            "low": "Sensibilizar sobre el impacto de las acciones en otros. Incluir en programas de convivencia laboral.",
        }
    }
    
    for value, score in sorted_values:
        level = "high" if score >= 55 else "low"
        if score >= 55 or score < 45:
            recomendaciones.append(f"**{value}:** {VALANTI_RECS[value][level]}")
    
    return {
        "aptitude_score": aptitude_score,
        "aptitude_level": aptitude_level,
        "aptitude_color": aptitude_color,
        "aptitude_emoji": aptitude_emoji,
        "aptitude_desc": aptitude_desc,
        "strongest_value": strongest[0],
        "strongest_score": strongest[1],
        "weakest_value": weakest[0],
        "weakest_score": weakest[1],
        "high_values": high_values,
        "low_values": low_values,
        "critical_values": critical_values,
        "fortalezas": fortalezas,
        "alertas": alertas,
        "recomendaciones": recomendaciones,
    }


# =========================================================================
# FUNCIONES DE SCORING
# =========================================================================

def normalize_disc_scores(scores, questions):
    max_possible = {s: 0.0 for s in "DISC"}
    min_possible = {s: 0.0 for s in "DISC"}
    for q in questions:
        for style in "DISC":
            m = q["mapping"][style]
            if m >= 0:
                max_possible[style] += m * 2
                min_possible[style] += m * (-2)
            else:
                max_possible[style] += m * (-2)
                min_possible[style] += m * 2
    normalized = {}
    for style in "DISC":
        score = max(min(scores[style], max_possible[style]), min_possible[style])
        r = max_possible[style] - min_possible[style]
        normalized[style] = ((score - min_possible[style]) / r) * 100 if r != 0 else 50.0
        normalized[style] = max(0, min(normalized[style], 100))
    return normalized


def calculate_disc_results(answers_list, questions):
    raw = {"D": 0, "I": 0, "S": 0, "C": 0}
    for i, q in enumerate(questions):
        answer = answers_list[i]
        for style in "DISC":
            raw[style] += q["mapping"][style] * (answer - 3)
    normalized = normalize_disc_scores(raw, questions)
    total = sum(normalized.values())
    relative = {s: (v / total * 100 if total > 0 else 25) for s, v in normalized.items()}
    return raw, normalized, relative


def calculate_valanti_results(responses):
    direct = {t: 0 for t in VALANTI_TRAITS}
    for trait, indices in VALANTI_TRAITS.items():
        for idx in indices:
            if idx - 1 < len(responses) and responses[idx - 1] is not None:
                direct[trait] += responses[idx - 1]
    standard = {}
    for trait in VALANTI_TRAITS:
        z = (direct[trait] - VALANTI_AVGS[trait]) / VALANTI_SDS[trait]
        standard[trait] = round(z * 10 + 50)
    return direct, standard


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

def generate_disc_pdf(candidate, normalized, relative, fig, session_id, completed_at=None, analysis=None):
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
                    test_type = st.selectbox("Tipo de Evaluación", ["disc", "valanti"], format_func=lambda x: "🎯 DISC" if x == "disc" else "🧭 VALANTI")
                with c4:
                    time_limit = st.selectbox("Tiempo Límite", [15, 20, 30, 45, 60], index=2, format_func=lambda x: f"{x} minutos")

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
                        test_type = st.selectbox("Tipo de Evaluación", ["disc", "valanti"], format_func=lambda x: "🎯 DISC" if x == "disc" else "🧭 VALANTI")
                    with c4:
                        time_limit = st.selectbox("Tiempo Límite", [15, 20, 30, 45, 60], index=2, format_func=lambda x: f"{x} minutos")
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
            filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "disc", "valanti"], key="filter_type",
                                        format_func=lambda x: {"Todos": "📋 Todos", "disc": "🎯 DISC", "valanti": "🧭 VALANTI"}.get(x, x))
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
                test_emoji = "🎯" if sess["test_type"] == "disc" else "🧭"
                
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
                            else:
                                show_valanti_results_admin(results, candidate, sess)
                        else:
                            st.warning("Resultados no disponibles.")

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
    
    # Banner de aptitud
    st.markdown(f"""
    <div style="background: {analysis['aptitude_color']}22; border-left: 5px solid {analysis['aptitude_color']};
                padding: 15px 20px; border-radius: 8px; margin-bottom: 15px;">
        <h3 style="margin: 0; color: {analysis['aptitude_color']};">{analysis['aptitude_emoji']} {analysis['aptitude_level']} — Puntaje: {analysis['aptitude_score']}/100</h3>
        <p style="margin: 5px 0 0 0; color: #374151;">{analysis['aptitude_desc']}</p>
        <p style="margin: 5px 0 0 0; color: #6B7280;"><b>Perfil:</b> {analysis['profile_name']} ({analysis['dominant_name']} + {analysis['secondary_name']})</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for idx, style in enumerate("DISC"):
        with cols[idx]:
            st.metric(style, f"{normalized.get(style, 0):.1f}%", f"Rel: {relative.get(style, 0):.1f}%")

    fig = create_disc_plot(normalized)
    st.pyplot(fig)
    
    # Fortalezas, alertas y recomendaciones
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
    pdf = generate_disc_pdf(candidate, normalized, relative, fig, session_id, completed_at, analysis)
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
        test_emoji = "🎯" if sess["test_type"] == "disc" else "🧭"
        test_name = "Evaluación DISC" if sess["test_type"] == "disc" else "Cuestionario VALANTI"
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
                    else:
                        nav("valanti_test")
                    st.rerun()

    st.markdown("---")
    if st.button("🔑 Cerrar Sesión"):
        for key in ["candidate", "pending_sessions", "test_session", "disc_questions", "disc_page", "disc_answers", "valanti_responses", "valanti_page"]:
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
            for key in ["candidate", "pending_sessions", "test_session", "disc_questions", "disc_page", "disc_answers", "valanti_responses", "valanti_page"]:
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

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
# CONSTANTES WPI (Work Personality Index)
# =========================================================================

# Dimensiones del WPI - Índice de Personalidad Laboral
WPI_DIMENSIONS = [
    "Responsabilidad",
    "Trabajo en Equipo", 
    "Adaptabilidad",
    "Autodisciplina",
    "Estabilidad Emocional",
    "Orientación al Logro"
]

# Colores para cada dimensión WPI
WPI_COLORS = {
    "Responsabilidad": "#3B82F6",        # Azul
    "Trabajo en Equipo": "#10B981",      # Verde
    "Adaptabilidad": "#F59E0B",          # Naranja
    "Autodisciplina": "#8B5CF6",         # Púrpura
    "Estabilidad Emocional": "#06B6D4",  # Cian
    "Orientación al Logro": "#EF4444"    # Rojo
}

# Descripciones de cada dimensión según nivel
WPI_DESCRIPTIONS = {
    "Responsabilidad": {
        "title": "📋 Responsabilidad",
        "high": "Alta confiabilidad, cumple compromisos, asume la rendición de cuentas y es puntual.",
        "medium": "Cumple con responsabilidades básicas, ocasionalmente requiere seguimiento.",
        "low": "Puede tener dificultad para cumplir compromisos, requiere supervisión frecuente."
    },
    "Trabajo en Equipo": {
        "title": "🤝 Trabajo en Equipo",
        "high": "Excelente colaborador, comparte información, apoya a compañeros y resuelve conflictos constructivamente.",
        "medium": "Trabaja bien con otros en la mayoría de situaciones, colabora cuando se le solicita.",
        "low": "Prefiere trabajo independiente, puede tener dificultad colaborando o compartiendo."
    },
    "Adaptabilidad": {
        "title": "🔄 Adaptabilidad",
        "high": "Muy flexible ante cambios, aprende rápido, maneja bien la incertidumbre y nuevas situaciones.",
        "medium": "Se adapta a cambios graduales, puede requerir tiempo para ajustarse a nuevos contextos.",
        "low": "Prefiere rutinas establecidas, los cambios rápidos pueden generar resistencia o estrés."
    },
    "Autodisciplina": {
        "title": "🎯 Autodisciplina",
        "high": "Excelente organización, gestión del tiempo, sigue procedimientos y mantiene altos estándares.",
        "medium": "Mantiene organización básica, cumple con procedimientos principales con recordatorios.",
        "low": "Puede tener dificultad con organización, gestión del tiempo o seguimiento de procedimientos."
    },
    "Estabilidad Emocional": {
        "title": "😌 Estabilidad Emocional",
        "high": "Maneja muy bien el estrés, mantiene calma bajo presión, se recupera rápido de contratiempos.",
        "medium": "Maneja estrés moderado adecuadamente, puede afectarse en situaciones de alta presión.",
        "low": "Vulnerable al estrés, puede tener reacciones emocionales intensas ante dificultades."
    },
    "Orientación al Logro": {
        "title": "🏆 Orientación al Logro",
        "high": "Alta motivación por excelencia, busca superar metas, toma iniciativa y mejora continua.",
        "medium": "Cumple con objetivos establecidos, motivación estándar por buenos resultados.",
        "low": "Motivación limitada por superación, prefiere tareas básicas sin desafíos adicionales."
    }
}

# Recomendaciones por nivel de cada dimensión WPI
WPI_RECOMMENDATIONS = {
    "Responsabilidad": {
        "high": ["Excelente para roles que requieren autonomía", "Puede supervisar o mentorear a otros", "Ideal para posiciones de confianza"],
        "medium": ["Buen desempeño con supervisión regular", "Puede mejorar con sistemas de recordatorios", "Adecuado para roles estructurados"],
        "low": ["Requiere supervisión cercana", "Beneficiaría de capacitación en gestión del tiempo", "Better en roles muy estructurados con checklists"]
    },
    "Trabajo en Equipo": {
        "high": ["Excelente para proyectos colaborativos", "Puede facilitar trabajo en equipo", "Ideal para mejorar clima laboral"],
        "medium": ["Funciona bien en equipos establecidos", "Puede colaborar con instrucciones claras", "Adecuado para trabajo semi-independiente"],
        "low": ["Mejor en roles independientes", "Puede requerir capacitación en habilidades interpersonales", "Considerar tareas individuales"]
    },
    "Adaptabilidad": {
        "high": ["Excelente para entornos dinámicos", "Ideal para proyectos de cambio", "Puede manejar múltiples prioridades"],
        "medium": ["Funciona bien con cambios planificados", "Necesita tiempo para ajustarse", "Adecuado para entornos moderadamente estables"],
        "low": ["Mejor en roles con rutinas establecidas", "Comunicar cambios con anticipación", "Proporcionar capacitación ante nuevas tareas"]
    },
    "Autodisciplina": {
        "high": ["Excelente para trabajo remoto/autónomo", "Puede manejar múltiples tareas", "Ideal para roles que requieren precisión"],
        "medium": ["Funciona bien con estructura externa", "Puede mejorar con herramientas de organización", "Supervisión periódica recomendada"],
        "low": ["Requiere estructura clara y supervisión", "Beneficiaría de capacitación en organización", "Mejor con tareas simples y bien definidas"]
    },
    "Estabilidad Emocional": {
        "high": ["Excelente para roles de alta presión", "Puede manejar crisis efectivamente", "Ideal para atención al cliente difícil"],
        "medium": ["Funciona bien en condiciones normales", "Puede requerir apoyo en crisis", "Adecuado para la mayoría de roles estándar"],
        "low": ["Mejor en entornos de bajo estrés", "Requiere apoyo emocional y capacitación", "Evitar roles con alta presión constante"]
    },
    "Orientación al Logro": {
        "high": ["Excelente para roles desafiantes", "Auto-motivado y proactivo", "Ideal para innovación y mejora continua"],
        "medium": ["Cumple objetivos con motivación externa", "Funciona bien con metas claras", "Adecuado para roles estándar"],
        "low": ["Requiere motivación y reconocimiento frecuente", "Mejor en roles sin metas ambiciosas", "Necesita supervisión para mantener resultados"]
    }
}


# =========================================================================
# CONSTANTES ERI (Evaluación de Riesgo e Integridad)
# =========================================================================

# Dimensiones del ERI - Evaluación de Riesgo e Integridad
ERI_DIMENSIONS = [
    "Honestidad",
    "Confiabilidad",
    "Consumo de Sustancias",
    "Control de Impulsos",
    "Actitud hacia Normas",
    "Hostilidad Laboral"
]

# Colores para cada dimensión ERI (Verde = bajo riesgo, Amarillo = medio, Rojo = alto)
ERI_COLORS = {
    "Honestidad": "#10B981",           # Verde
    "Confiabilidad": "#3B82F6",        # Azul
    "Consumo de Sustancias": "#F59E0B", # Naranja
    "Control de Impulsos": "#EF4444",  # Rojo
    "Actitud hacia Normas": "#8B5CF6", # Púrpura
    "Hostilidad Laboral": "#EC4899"    # Rosa
}

# Descripciones de cada dimensión según nivel de riesgo
ERI_DESCRIPTIONS = {
    "Honestidad": {
        "title": "🔐 Honestidad",
        "low_risk": "Alta integridad, transparente en sus acciones, reporta irregularidades.",
        "medium_risk": "Generalmente honesto, puede tener comportamientos cuestionables ocasionales.",
        "high_risk": "⚠️ ALERTA: Indicadores de deshonestidad, riesgo de robo o fraude."
    },
    "Confiabilidad": {
        "title": "✅ Confiabilidad",
        "low_risk": "Alta consistencia, cumple compromisos, asistencia puntual y constante.",
        "medium_risk": "Confiable en general, ocasionalmente puede faltar a compromisos.",
        "high_risk": "⚠️ ALERTA: Patrón de incumplimiento, ausentismo, falta de constancia."
    },
    "Consumo de Sustancias": {
        "title": "🚫 Consumo de Sustancias",
        "low_risk": "Sin indicadores de consumo problemático, actitud preventiva.",
        "medium_risk": "Consumo ocasional reportado, puede afectar desempeño ocasionalmente.",
        "high_risk": "⚠️ ALERTA: Indicadores de consumo problemático, riesgo para seguridad laboral."
    },
    "Control de Impulsos": {
        "title": "🧘 Control de Impulsos",
        "low_risk": "Excelente autocontrol, maneja frustración adecuadamente, pensante antes de actuar.",
        "medium_risk": "Control moderado, puede tener reacciones impulsivas ocasionales bajo presión.",
        "high_risk": "⚠️ ALERTA: Indicadores de comportamiento agresivo, riesgo de violencia laboral."
    },
    "Actitud hacia Normas": {
        "title": "📋 Actitud hacia Normas",
        "low_risk": "Respeta reglas y procedimientos, valora la autoridad y estructura.",
        "medium_risk": "Cumple normas básicas, puede cuestionar o saltarse reglas menores.",
        "high_risk": "⚠️ ALERTA: Desafío a la autoridad, desprecio por normas, riesgo de incumplimiento."
    },
    "Hostilidad Laboral": {
        "title": "🤝 Relaciones Laborales",
        "low_risk": "Relaciones positivas, respeta a compañeros, sin indicadores de hostilidad.",
        "medium_risk": "Ocasionalmente conflictivo, puede tener problemas interpersonales menores.",
        "high_risk": "⚠️ ALERTA: Indicadores de acoso, intimidación, riesgo de ambiente tóxico."
    }
}

# Umbrales de riesgo para cada dimensión (puntuaciones invertidas: más bajo = más riesgo)
# Los scores se normalizan a 0-100, donde:
# 0-40 = ALTO RIESGO (Rojo)
# 41-65 = RIESGO MODERADO (Amarillo)
# 66-100 = BAJO RIESGO (Verde)
ERI_RISK_THRESHOLDS = {
    "low_risk": 66,     # >= 66 = Bajo riesgo (Verde)
    "medium_risk": 41,  # 41-65 = Riesgo moderado (Amarillo)
    "high_risk": 0      # 0-40 = Alto riesgo (Rojo)
}

# Número de preguntas de validez en el test (aproximadamente el 20-25% de las preguntas)
ERI_VALIDITY_QUESTIONS_COUNT = 12

# Umbral de inconsistencias para invalidar el test
# Si el candidato responde 5 o más con falta extrema de honestidad en preguntas de validez (ej: "Nunca he mentido")
ERI_VALIDITY_THRESHOLD = 5

# Recomendaciones por nivel de riesgo en cada dimensión
ERI_RECOMMENDATIONS = {
    "Honestidad": {
        "low_risk": ["Excelente para roles de manejo de efectivo o activos", "Apto para posiciones de confianza", "Bajo riesgo de robo o fraude"],
        "medium_risk": ["Supervisión estándar recomendada", "Entrevista profunda sobre valores éticos", "Monitoreo en período de prueba"],
        "high_risk": ["⚠️ NO RECOMENDADO para roles con acceso a dinero o activos", "Riesgo elevado de pérdidas por deshonestidad", "Considerar descarte del candidato"]
    },
    "Confiabilidad": {
        "low_risk": ["Excelente para roles que requieren autonomía", "Bajo riesgo de ausentismo", "Ideal para trabajos sin supervisión directa"],
        "medium_risk": ["Sistemas de seguimiento recomendados", "Puede requerir recordatorios de compromisos", "Adecuado con supervisión regular"],
        "high_risk": ["⚠️ Alto riesgo de ausentismo y rotación", "Requiere supervisión constante", "Considerar para roles de bajo impacto solamente"]
    },
    "Consumo de Sustancias": {
        "low_risk": ["Apto para roles de seguridad crítica", "Sin riesgos relacionados con sustancias", "Excelente para operación de maquinaria"],
        "medium_risk": ["Evaluar con pruebas adicionales si el rol es crítico", "Considerar política de pruebas aleatorias", "Entrevista sobre hábitos"],
        "high_risk": ["⚠️ NO RECOMENDADO para roles de seguridad o conducción", "Riesgo grave de accidentes", "Requiere evaluación de adicciones profesional"]
    },
    "Control de Impulsos": {
        "low_risk": ["Apto para roles de alta presión", "Bajo riesgo de conflictos violentos", "Excelente para atención al cliente difícil"],
        "medium_risk": ["Capacitación en manejo de emociones recomendada", "Evitar roles de muy alta tensión", "Monitoreo de comportamiento"],
        "high_risk": ["⚠️ Riesgo de violencia laboral", "NO RECOMENDADO para roles de atención al público", "Requiere evaluación psicológica profesional"]
    },
    "Actitud hacia Normas": {
        "low_risk": ["Excelente para roles regulados o compliance", "Respeta procedimientos de seguridad", "Ideal para ambientes estructurados"],
        "medium_risk": ["Comunicar claramente expectativas y consecuencias", "Supervisión de cumplimiento de normas", "Puede funcionar con autonomía limitada"],
        "high_risk": ["⚠️ Riesgo de incumplimiento de seguridad y normativas", "NO RECOMENDADO para roles regulados", "Puede generar sanciones legales a la empresa"]
    },
    "Hostilidad Laboral": {
        "low_risk": ["Excelente para trabajo en equipo", "Contribuye a clima laboral positivo", "Bajo riesgo de demandas por acoso"],
        "medium_risk": ["Capacitación en relaciones interpersonales", "Monitoreo de interacciones con equipo", "Puede requerir mediación ocasional"],
        "high_risk": ["⚠️ Alto riesgo de acoso laboral y demandas", "Puede crear ambiente tóxico", "Considerar descarte para proteger al equipo"]
    }
}

# Recomendaciones de contratación según perfil de riesgo general
ERI_HIRING_RECOMMENDATIONS = {
    "low_risk": {
        "decision": "✅ RECOMENDADO PARA CONTRATACIÓN",
        "resumen": "Perfil de bajo riesgo en integridad y comportamiento laboral. Candidato confiable.",
        "acciones": [
            "Proceso de contratación estándar",
            "Supervisión normal según el puesto",
            "Buen prospecto para desarrollo a largo plazo"
        ]
    },
    "medium_risk": {
        "decision": "⚠️ CONTRATAR CON PRECAUCIONES",
        "resumen": "Perfil con señales de alerta moderadas. Requiere medidas preventivas.",
        "acciones": [
            "Entrevista profunda sobre dimensiones de riesgo identificadas",
            "Referencias laborales exhaustivas",
            "Período de prueba extendido con supervisión cercana",
            "Evaluaciones de desempeño frecuentes (30-60-90 días)",
            "Capacitación específica en áreas de riesgo"
        ]
    },
    "high_risk": {
        "decision": "🚫 NO RECOMENDADO PARA CONTRATACIÓN",
        "resumen": "Perfil de alto riesgo. Contratación representa riesgo significativo para la organización.",
        "acciones": [
            "⚠️ Considerar seriamente descartar al candidato",
            "Si se decide contratar: rol de muy bajo impacto y alta supervisión",
            "Evaluación psicológica profesional obligatoria",
            "Políticas estrictas de monitoreo y consecuencias claras",
            "Documentación exhaustiva de comportamiento"
        ]
    }
}


# =========================================================================
# CONSTANTES TALENT MAP (Mapeo de Competencias y Talentos)
# =========================================================================

# Dimensiones del Talent Map - 8 competencias universales
TALENT_MAP_COMPETENCIES = [
    "Liderazgo",
    "Comunicación",
    "Pensamiento Analítico",
    "Innovación y Creatividad",
    "Orientación al Cliente",
    "Trabajo en Equipo",
    "Gestión del Cambio",
    "Resolución de Problemas"
]

# Colores para cada competencia
TALENT_MAP_COLORS = {
    "Liderazgo": "#EF4444",              # Rojo
    "Comunicación": "#3B82F6",           # Azul
    "Pensamiento Analítico": "#8B5CF6",  # Púrpura
    "Innovación y Creatividad": "#F59E0B", # Naranja
    "Orientación al Cliente": "#10B981", # Verde
    "Trabajo en Equipo": "#06B6D4",      # Cian
    "Gestión del Cambio": "#EC4899",     # Rosa
    "Resolución de Problemas": "#14B8A6" # Teal
}

# Descripciones de cada competencia según nivel
TALENT_MAP_DESCRIPTIONS = {
    "Liderazgo": {
        "title": "👑 Liderazgo",
        "high": "Capacidad sobresaliente para dirigir equipos, inspirar y tomar decisiones estratégicas. Asume responsabilidad y desarrolla talento.",
        "medium": "Muestra iniciativa de liderazgo ocasional, puede dirigir con apoyo. En desarrollo.",
        "low": "Prefiere roles sin responsabilidad de dirección. Requiere desarrollo significativo en habilidades de liderazgo."
    },
    "Comunicación": {
        "title": "💬 Comunicación",
        "high": "Comunicador excepcional, expresa ideas claramente, escucha activamente y adapta mensaje a audiencias diversas.",
        "medium": "Comunicación efectiva en situaciones estándar, puede mejorar en contextos complejos o audiencias difíciles.",
        "low": "Desafíos en expresión clara o escucha activa. Requiere capacitación en comunicación efectiva."
    },
    "Pensamiento Analítico": {
        "title": "🔍 Pensamiento Analítico",
        "high": "Analiza problemas complejos desde múltiples perspectivas, identifica patrones, usa datos para decisiones fundamentadas.",
        "medium": "Capacidad analítica básica, maneja problemas de complejidad moderada con orientación.",
        "low": "Prefiere intuición sobre análisis estructurado. Requiere desarrollo en pensamiento crítico y análisis de datos."
    },
    "Innovación y Creatividad": {
        "title": "💡 Innovación y Creatividad",
        "high": "Genera constantemente ideas originales, propone soluciones innovadoras, cómodo con experimentación y riesgo calculado.",
        "medium": "Muestra creatividad ocasional, puede aportar ideas con estímulo. Balancea innovación con métodos probados.",
        "low": "Prefiere métodos establecidos, resistencia al cambio. Requiere estímulo para pensar creativamente."
    },
    "Orientación al Cliente": {
        "title": "🎯 Orientación al Cliente",
        "high": "Comprende profundamente necesidades del cliente, anticipa expectativas, construye relaciones de largo plazo, va más allá.",
        "medium": "Atiende necesidades básicas del cliente adecuadamente, puede mejorar en anticipación y personalización.",
        "low": "Enfoque limitado en cliente, prioriza procesos internos. Requiere desarrollo en mentalidad centrada en cliente."
    },
    "Trabajo en Equipo": {
        "title": "🤝 Trabajo en Equipo",
        "high": "Colaborador excepcional, comparte conocimiento abiertamente, construye consenso, valora diversidad, contribuye al éxito colectivo.",
        "medium": "Trabaja bien en equipo cuando se requiere, colaboración estándar. Ocasionalmente prefiere trabajo individual.",
        "low": "Preferencia marcada por trabajo independiente, desafíos en colaboración. Requiere desarrollo en habilidades interpersonales."
    },
    "Gestión del Cambio": {
        "title": "🔄 Gestión del Cambio",
        "high": "Altamente adaptable, ve cambios como oportunidades, ayuda a otros en transiciones, aprende rápido, positivo ante incertidumbre.",
        "medium": "Se adapta a cambios graduales, puede requerir tiempo de ajuste. Maneja cambios planificados adecuadamente.",
        "low": "Resistencia al cambio, prefiere rutinas establecidas. Requiere apoyo significativo en períodos de transformación."
    },
    "Resolución de Problemas": {
        "title": "🎯 Resolución de Problemas",
        "high": "Identifica soluciones efectivas bajo presión, evalúa alternativas, implementa decisiones, aprende de errores, decisivo.",
        "medium": "Resuelve problemas estándar efectivamente, puede requerir apoyo en situaciones complejas o de alta presión.",
        "low": "Desafíos para tomar decisiones, se paraliza con problemas complejos. Requiere capacitación estructurada en solución de problemas."
    }
}

# Perfiles de referencia por puesto (benchmarks de competencias en escala 0-100)
TALENT_MAP_JOB_PROFILES = {
    "Gerente General": {
        "emoji": "👔",
        "descripcion": "Lidera organización, toma decisiones estratégicas, gestiona recursos",
        "competencias": {
            "Liderazgo": 90,
            "Comunicación": 85,
            "Pensamiento Analítico": 85,
            "Innovación y Creatividad": 75,
            "Orientación al Cliente": 80,
            "Trabajo en Equipo": 75,
            "Gestión del Cambio": 85,
            "Resolución de Problemas": 90
        }
    },
    "Gerente de Ventas": {
        "emoji": "📊",
        "descripcion": "Dirige equipo comercial, desarrolla estrategias de venta, alcanza metas",
        "competencias": {
            "Liderazgo": 85,
            "Comunicación": 90,
            "Pensamiento Analítico": 70,
            "Innovación y Creatividad": 75,
            "Orientación al Cliente": 95,
            "Trabajo en Equipo": 80,
            "Gestión del Cambio": 75,
            "Resolución de Problemas": 80
        }
    },
    "Gerente de Recursos Humanos": {
        "emoji": "👥",
        "descripcion": "Gestiona talento humano, cultura organizacional, desarrollo de personal",
        "competencias": {
            "Liderazgo": 80,
            "Comunicación": 90,
            "Pensamiento Analítico": 75,
            "Innovación y Creatividad": 70,
            "Orientación al Cliente": 75,
            "Trabajo en Equipo": 90,
            "Gestión del Cambio": 85,
            "Resolución de Problemas": 80
        }
    },
    "Gerente de Operaciones": {
        "emoji": "⚙️",
        "descripcion": "Optimiza procesos, gestiona producción, controla calidad y eficiencia",
        "competencias": {
            "Liderazgo": 85,
            "Comunicación": 75,
            "Pensamiento Analítico": 90,
            "Innovación y Creatividad": 70,
            "Orientación al Cliente": 70,
            "Trabajo en Equipo": 80,
            "Gestión del Cambio": 80,
            "Resolución de Problemas": 90
        }
    },
    "Gerente de TI": {
        "emoji": "💻",
        "descripcion": "Lidera tecnología, infraestructura, seguridad y proyectos digitales",
        "competencias": {
            "Liderazgo": 80,
            "Comunicación": 75,
            "Pensamiento Analítico": 95,
            "Innovación y Creatividad": 85,
            "Orientación al Cliente": 70,
            "Trabajo en Equipo": 75,
            "Gestión del Cambio": 90,
            "Resolución de Problemas": 95
        }
    },
    "Vendedor Senior": {
        "emoji": "🎯",
        "descripcion": "Desarrolla clientes, negocia contratos, alcanza cuotas de venta",
        "competencias": {
            "Liderazgo": 60,
            "Comunicación": 90,
            "Pensamiento Analítico": 70,
            "Innovación y Creatividad": 75,
            "Orientación al Cliente": 95,
            "Trabajo en Equipo": 70,
            "Gestión del Cambio": 75,
            "Resolución de Problemas": 75
        }
    },
    "Analista de Datos": {
        "emoji": "📈",
        "descripcion": "Analiza información, genera insights, reporta métricas de negocio",
        "competencias": {
            "Liderazgo": 50,
            "Comunicación": 70,
            "Pensamiento Analítico": 95,
            "Innovación y Creatividad": 70,
            "Orientación al Cliente": 65,
            "Trabajo en Equipo": 70,
            "Gestión del Cambio": 70,
            "Resolución de Problemas": 85
        }
    },
    "Especialista en Marketing": {
        "emoji": "📱",
        "descripcion": "Desarrolla campañas, gestiona marca, analiza mercados y tendencias",
        "competencias": {
            "Liderazgo": 60,
            "Comunicación": 85,
            "Pensamiento Analítico": 75,
            "Innovación y Creatividad": 90,
            "Orientación al Cliente": 85,
            "Trabajo en Equipo": 80,
            "Gestión del Cambio": 80,
            "Resolución de Problemas": 75
        }
    },
    "Ingeniero de Software": {
        "emoji": "⌨️",
        "descripcion": "Desarrolla aplicaciones, mantiene sistemas, resuelve problemas técnicos",
        "competencias": {
            "Liderazgo": 50,
            "Comunicación": 65,
            "Pensamiento Analítico": 90,
            "Innovación y Creatividad": 85,
            "Orientación al Cliente": 60,
            "Trabajo en Equipo": 75,
            "Gestión del Cambio": 80,
            "Resolución de Problemas": 95
        }
    },
    "Coordinador de Proyectos": {
        "emoji": "📋",
        "descripcion": "Planifica, organiza y supervisa proyectos, coordina equipos multifuncionales",
        "competencias": {
            "Liderazgo": 75,
            "Comunicación": 85,
            "Pensamiento Analítico": 80,
            "Innovación y Creatividad": 65,
            "Orientación al Cliente": 75,
            "Trabajo en Equipo": 90,
            "Gestión del Cambio": 80,
            "Resolución de Problemas": 85
        }
    },
    "Especialista en Servicio al Cliente": {
        "emoji": "☎️",
        "descripcion": "Atiende consultas, resuelve problemas, mantiene satisfacción del cliente",
        "competencias": {
            "Liderazgo": 45,
            "Comunicación": 90,
            "Pensamiento Analítico": 65,
            "Innovación y Creatividad": 60,
            "Orientación al Cliente": 95,
            "Trabajo en Equipo": 80,
            "Gestión del Cambio": 70,
            "Resolución de Problemas": 80
        }
    },
    "Contador/Analista Financiero": {
        "emoji": "💰",
        "descripcion": "Gestiona finanzas, reportes contables, análisis financiero y presupuestos",
        "competencias": {
            "Liderazgo": 55,
            "Comunicación": 70,
            "Pensamiento Analítico": 95,
            "Innovación y Creatividad": 60,
            "Orientación al Cliente": 60,
            "Trabajo en Equipo": 70,
            "Gestión del Cambio": 65,
            "Resolución de Problemas": 85
        }
    }
}

# Niveles de coincidencia (match) con perfil de puesto
TALENT_MAP_MATCH_LEVELS = {
    "excelente": {"min": 85, "label": "🌟 Excelente Match", "color": "#10B981", "descripcion": "Competencias altamente alineadas con el perfil del puesto"},
    "muy_bueno": {"min": 75, "label": "✅ Muy Buen Match", "color": "#3B82F6", "descripcion": "Competencias bien alineadas, candidato muy apto para el rol"},
    "bueno": {"min": 65, "label": "👍 Buen Match", "color": "#F59E0B", "descripcion": "Competencias aceptables, puede requerir desarrollo en algunas áreas"},
    "aceptable": {"min": 50, "label": "⚠️ Match Aceptable", "color": "#EF4444", "descripcion": "Competencias limitadas, requiere capacitación significativa"},
    "bajo": {"min": 0, "label": "❌ Match Bajo", "color": "#991B1B", "descripcion": "Competencias insuficientes para el rol, no recomendado"}
}

# Recomendaciones por nivel de competencia
TALENT_MAP_COMPETENCY_RECOMMENDATIONS = {
    "high": [
        "Fortaleza clave: aprovechar en el rol",
        "Puede mentorear a otros en esta competencia",
        "Considerar para proyectos que requieran esta habilidad"
    ],
    "medium": [
        "Nivel adecuado para el rol",
        "Puede beneficiarse de capacitación para alcanzar excelencia",
        "Monitorear desarrollo continuo"
    ],
    "low": [
        "Área de desarrollo prioritaria",
        "Requiere plan de capacitación específico",
        "Considerar apoyo o mentoría en esta competencia"
    ]
}


# =========================================================================
# EVALUACIÓN DE DESEMPEÑO
# =========================================================================

# 6 Objetivos de Rendimiento (Escala 1-5)
DESEMPENO_OBJETIVOS = [
    {
        "id": 1,
        "titulo": "Conocimiento y Proactividad",
        "descripcion": "Conoce sus deberes y es proactivo al momento de realizar su trabajo. Conoce a cabalidad los procedimientos de la operación y los aplica en el trabajo diario, realizando las tareas de manera proactiva y autónoma dentro de sus responsabilidades."
    },
    {
        "id": 2,
        "titulo": "Puntualidad",
        "descripcion": "Es puntual con el cumplimiento de Horarios y Jornada Laboral asignados."
    },
    {
        "id": 3,
        "titulo": "Cumplimiento de Responsabilidades",
        "descripcion": "Cumple con las solicitudes, requerimientos, obligaciones, funciones y responsabilidades respondiendo de manera inmediata en el tiempo estimado."
    },
    {
        "id": 4,
        "titulo": "Trabajo en Equipo",
        "descripcion": "Es cordial y respetuoso con sus compañeros, demostrando empatía, colaboración y actitud positiva dentro del equipo. Ayuda a los demás y demuestra buenas relaciones interpersonales."
    },
    {
        "id": 5,
        "titulo": "Orientación al Cliente",
        "descripcion": "Demuestra buena actitud, disponibilidad y preocupación para responder a las necesidades e inquietudes de los usuarios. Tiene una buena postura, actitud, simpatía y proactividad en el contacto establecido con el usuario en su trabajo diario."
    },
    {
        "id": 6,
        "titulo": "Calificación Global",
        "descripcion": "Teniendo en cuenta el resultado de la evaluación y los comportamientos evidenciados durante el periodo. Otorgue una calificación global al colaborador dentro de este periodo de acuerdo a lo observado."
    }
]

# Escala de Rendimiento (1-5)
DESEMPENO_ESCALA_RENDIMIENTO = {
    5: {"label": "Sobresaliente", "descripcion": "Resultado claramente sobre lo esperado", "color": "#10B981"},
    4: {"label": "Supera las expectativas", "descripcion": "Resultado que satisface plenamente las expectativas", "color": "#3B82F6"},
    3: {"label": "Cumple las expectativas", "descripcion": "Nivel de resultado aceptable, pero podría mejorar", "color": "#F59E0B"},
    2: {"label": "Debajo de las expectativas", "descripcion": "Resultado elemental, poco satisfactorio", "color": "#EF4444"},
    1: {"label": "Insatisfactorio", "descripcion": "Resultado deficiente. No alcanzó los requerimientos mínimos", "color": "#991B1B"}
}

# 5 Dimensiones de Potencial (Escala 0-3)
DESEMPENO_DIMENSIONES = [
    {
        "id": 1,
        "nombre": "Motivaciones Personales",
        "descripcion": "Capacidad para asumir nuevas responsabilidades y retos",
        "niveles": {
            3: "Es capaz de asumir con entereza y entusiasmo nuevas responsabilidades, así como nuevos retos y desafíos. Demuestra tener gran potencial de desarrollo en la Organización.",
            2: "Demuestra el potencial para asumir en un mediano plazo nuevos retos y mayores responsabilidades. Es capaz de consolidarse en su posición actual.",
            1: "No se encuentra consolidado en su posición actual y requiere de mayor tiempo y fortalecimiento para poder asumir mayores responsabilidades a futuro.",
            0: "No se evidencia motivación en el colaborador para asumir nuevos retos o asumir responsabilidades adicionales."
        }
    },
    {
        "id": 2,
        "nombre": "Visión",
        "descripcion": "Habilidad para analizar situaciones y configurar perspectivas",
        "niveles": {
            3: "Cuenta con facilidad y destreza para analizar situaciones complejas desde una perspectiva general y amplia, con el fin de configurar cada circunstancia o decisión dentro de un contexto más amplio.",
            2: "Es capaz de analizar diversas situaciones y contextos con la intención de establecer criterios de decisión o acción acertados.",
            1: "Requiere que se le brinde la información completa sobre alguna situación, problema o circunstancia para poder actuar o tomar decisiones al respecto.",
            0: "No se evidencia habilidad para integrar temas ni información diversa para analizar desde múltiples perspectivas y tomar decisiones."
        }
    },
    {
        "id": 3,
        "nombre": "Disposición para Sobresalir",
        "descripcion": "Compromiso con objetivos y metas organizacionales",
        "niveles": {
            3: "Se compromete a lograr los objetivos y metas que se le asignen, incluso cuando no tiene definidas o claras las condiciones o parámetros para hacerlo. Busca activamente la forma de hacerlo.",
            2: "Tiene claro cuáles son sus objetivos y qué se espera de él, y se esfuerza por cumplirlos. Cuando se le asigna una tarea adicional, responde positivamente y hace lo que corresponde.",
            1: "Requiere de motivación externa y constante para lograr sus objetivos, así como de supervisión cercana de su jefe directo.",
            0: "No se evidencia disposición para lograr sus objetivos ni para entregar resultados. No se compromete con el cumplimiento de sus responsabilidades."
        }
    },
    {
        "id": 4,
        "nombre": "Compromiso",
        "descripcion": "Capacidad para mantener relaciones positivas con clientes",
        "niveles": {
            3: "Se preocupa por lograr y mantener relaciones positivas con sus clientes internos y externos, de tal manera que realiza esfuerzos adicionales para lograrlo.",
            2: "Establece relaciones adecuadas con sus clientes internos y externos, considerando que logra comprender sus necesidades y actuar en consecuencia.",
            1: "Se relaciona con sus clientes internos y externos solo con la finalidad de atender sus necesidades y requerimientos más básicos.",
            0: "No se evidencia en el colaborador voluntad ni capacidad para relacionarse adecuadamente con sus clientes internos o externos."
        }
    },
    {
        "id": 5,
        "nombre": "Capacidad de Aprendizaje",
        "descripcion": "Interés por adquirir nuevos conocimientos y habilidades",
        "niveles": {
            3: "Le motiva y demuestra gran interés por buscar y adquirir nuevos conocimientos y habilidades. Invierte tiempo y esfuerzo con tal de seguir  aprendiendo y capacitándose.",
            2: "Muestra disposición para recibir e interiorizar nuevos conocimientos e información, con el fin de continuar su proceso de aprendizaje.",
            1: "No evidencia conductas de interés por continuar aprendiendo y/o capacitándose para mejorar en su desempeño.",
            0: "No se evidencia en el colaborador actitud o voluntad de aprender y capacitarse."
        }
    }
]

# Clasificación de desempeño
DESEMPENO_CLASIFICACION = {
    "sobresaliente": {"min": 4.5, "label": "🌟 Sobresaliente", "color": "#10B981", "descripcion": "Desempeño excepcional que supera ampliamente las expectativas"},
    "supera": {"min": 3.5, "label": "⭐ Supera las Expectativas", "color": "#3B82F6", "descripcion": "Desempeño destacado que supera lo esperado"},
    "cumple": {"min": 2.5, "label": "✅ Cumple las Expectativas", "color": "#F59E0B", "descripcion": "Desempeño satisfactorio que cumple lo esperado"},
    "debajo": {"min": 1.5, "label": "⚠️ Debajo de las Expectativas", "color": "#EF4444", "descripcion": "Desempeño insuficiente que requiere mejora"},
    "insatisfactorio": {"min": 0, "label": "❌ Insatisfactorio", "color": "#991B1B", "descripcion": "Desempeño deficiente que requiere plan de acción inmediato"}
}

# Colores para dimensiones de potencial
DESEMPENO_COLORES_DIMENSIONES = {
    "Motivaciones Personales": "#8B5CF6",
    "Visión": "#3B82F6",
    "Disposición para Sobresalir": "#10B981",
    "Compromiso": "#F59E0B",
    "Capacidad de Aprendizaje": "#EF4444"
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


def analyze_wpi_aptitude(normalized):
    """
    Analiza los resultados WPI y genera recomendaciones, fortalezas, alertas y nivel de aptitud laboral.
    
    Args:
        normalized: Dict con puntajes normalizados (0-100) por dimensión
        
    Returns:
        Dict con análisis completo: aptitud, fortalezas, alertas, recomendaciones
    """
    # Ordenar dimensiones por puntaje
    sorted_dims = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_dims[0]
    second_strongest = sorted_dims[1]
    weakest = sorted_dims[-1]
    second_weakest = sorted_dims[-2]
    
    # Clasificar dimensiones por nivel de puntaje
    # Alto: >= 70, Medio: 45-69, Bajo: < 45
    high_dims = [d for d, s in normalized.items() if s >= 70]
    medium_dims = [d for d, s in normalized.items() if 45 <= s < 70]
    low_dims = [d for d, s in normalized.items() if s < 45]
    critical_dims = [d for d, s in normalized.items() if s < 30]
    
    # Calcular puntaje promedio
    avg_score = sum(normalized.values()) / len(normalized)
    
    # Calcular puntaje de aptitud general (0-100)
    # Basado en: promedio + bonificación por fortalezas - penalización por debilidades
    aptitude_score = round(
        avg_score + 
        len(high_dims) * 5 -      # Bonificación por dimensiones altas
        len(low_dims) * 10 -       # Penalización por dimensiones bajas
        len(critical_dims) * 20    # Penalización fuerte por dimensiones críticas
    )
    aptitude_score = max(0, min(100, aptitude_score))
    
    # Determinar nivel de aptitud laboral
    if len(critical_dims) > 0:
        aptitude_level = "NO RECOMENDADO"
        aptitude_color = "#EF4444"
        aptitude_emoji = "🔴"
        aptitude_desc = f"Deficiencias críticas en: {', '.join(critical_dims)}. Alto riesgo de bajo desempeño laboral. Se requiere desarrollo sustancial."
    elif len(low_dims) >= 3:
        aptitude_level = "CONTRATACIÓN CON RESERVAS"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = f"Múltiples áreas de mejora ({', '.join(low_dims)}). Requiere supervisión cercana y plan de desarrollo."
    elif len(low_dims) >= 1 and len(high_dims) >= 2:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = f"Buen potencial con fortalezas en {strongest[0]} y {second_strongest[0]}, pero requiere desarrollo en: {', '.join(low_dims)}."
    elif avg_score >= 60 and len(high_dims) >= 3:
        aptitude_level = "ALTAMENTE RECOMENDADO"
        aptitude_color = "#10B981"
        aptitude_emoji = "✅"
        aptitude_desc = f"Perfil laboral sobresaliente. Fortalezas destacadas en {', '.join(high_dims)}. Candidato ideal para el puesto."
    elif avg_score >= 50:
        aptitude_level = "APTO"
        aptitude_color = "#10B981"
        aptitude_emoji = "✓"
        aptitude_desc = "Perfil laboral adecuado. Competencias en nivel esperado para desempeño satisfactorio."
    else:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = "Perfil laboral en nivel básico. Se recomienda evaluar ajuste específico al puesto."
    
    # Generar fortalezas (dimensiones altas)
    fortalezas = []
    for dim, score in sorted_dims:
        if score >= 70:
            desc = WPI_DESCRIPTIONS[dim]
            fortalezas.append(f"**{dim}** ({int(score)}/100): {desc['high']}")
        elif score >= 60 and len(fortalezas) < 3:  # Incluir algunas medias-altas si no hay muchas altas
            desc = WPI_DESCRIPTIONS[dim]
            fortalezas.append(f"**{dim}** ({int(score)}/100): {desc['medium']}")
    
    # Generar alertas (dimensiones bajas)
    alertas = []
    for dim, score in sorted_dims:
        if score < 45:
            desc = WPI_DESCRIPTIONS[dim]
            alertas.append(f"⚠️ **{dim}** ({int(score)}/100): {desc['low']}")
    
    # Generar recomendaciones específicas por dimensión
    recomendaciones = []
    for dim, score in sorted_dims:
        if score >= 70:
            level = "high"
        elif score >= 45:
            level = "medium"
        else:
            level = "low"
        
        # Solo incluir recomendaciones para extremos (muy alto o muy bajo)
        if score >= 70 or score < 50:
            recs = WPI_RECOMMENDATIONS[dim][level]
            recomendaciones.append(f"**{dim}:** {' | '.join(recs)}")
    
    # Determinar roles ideales según perfil
    ideal_para = []
    avoid_roles = []
    
    # Lógica de roles según combinación de dimensiones
    if normalized.get("Responsabilidad", 0) >= 70 and normalized.get("Autodisciplina", 0) >= 70:
        ideal_para.append("Trabajo remoto o autónomo")
    if normalized.get("Trabajo en Equipo", 0) >= 70:
        ideal_para.append("Proyectos colaborativos")
    if normalized.get("Adaptabilidad", 0) >= 70:
        ideal_para.append("Entornos dinámicos o de cambio")
    if normalized.get("Estabilidad Emocional", 0) >= 70:
        ideal_para.append("Roles de alta presión")
    if normalized.get("Orientación al Logro", 0) >= 70:
        ideal_para.append("Posiciones de desarrollo y crecimiento")
    
    # Roles a evitar
    if normalized.get("Trabajo en Equipo", 0) < 40:
        avoid_roles.append("Proyectos colaborativos intensivos")
    if normalized.get("Adaptabilidad", 0) < 40:
        avoid_roles.append("Entornos de cambio constante")
    if normalized.get("Estabilidad Emocional", 0) < 40:
        avoid_roles.append("Roles de alta presión o crisis")
    if normalized.get("Orientación al Logro", 0) < 40:
        avoid_roles.append("Posiciones que requieren auto-motivación")
    
    return {
        "aptitude_score": aptitude_score,
        "aptitude_level": aptitude_level,
        "aptitude_color": aptitude_color,
        "aptitude_emoji": aptitude_emoji,
        "aptitude_desc": aptitude_desc,
        "strongest_dimension": strongest[0],
        "strongest_score": strongest[1],
        "weakest_dimension": weakest[0],
        "weakest_score": weakest[1],
        "high_dimensions": high_dims,
        "medium_dimensions": medium_dims,
        "low_dimensions": low_dims,
        "critical_dimensions": critical_dims,
        "average_score": round(avg_score, 1),
        "fortalezas": fortalezas,
        "alertas": alertas,
        "recomendaciones": recomendaciones,
        "ideal_para": ideal_para,
        "avoid_roles": avoid_roles,
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


def calculate_wpi_results(responses, questions):
    """
    Calcula los resultados del WPI (Work Personality Index).
    
    Args:
        responses: Lista de respuestas (1-5) del candidato
        questions: Lista de preguntas con dimension y reverse flag
        
    Returns:
        tuple: (raw_scores, normalized_scores, percentages)
            - raw_scores: Puntajes directos por dimensión
            - normalized_scores: Puntajes normalizados 0-100
            - percentages: Porcentajes relativos entre dimensiones
    """
    # Contar preguntas por dimensión
    questions_per_dim = {}
    for q in questions:
        dim = q["dimension"]
        questions_per_dim[dim] = questions_per_dim.get(dim, 0) + 1
    
    # Calcular puntajes directos por dimensión
    raw_scores = {dim: 0 for dim in WPI_DIMENSIONS}
    
    for i, q in enumerate(questions):
        if i < len(responses) and responses[i] is not None:
            dim = q["dimension"]
            answer = responses[i]
            
            # Si es pregunta reversa, invertir escala (1->5, 2->4, 3->3, 4->2, 5->1)
            if q.get("reverse", False):
                answer = 6 - answer
            
            raw_scores[dim] += answer
    
    # Normalizar a escala 0-100
    # Cada dimensión tiene ~8 preguntas, escala 1-5
    # Mínimo posible: 8 * 1 = 8
    # Máximo posible: 8 * 5 = 40
    normalized_scores = {}
    for dim in WPI_DIMENSIONS:
        num_questions = questions_per_dim.get(dim, 8)
        min_possible = num_questions * 1
        max_possible = num_questions * 5
        raw = raw_scores[dim]
        
        # Normalizar a 0-100
        if max_possible > min_possible:
            normalized = ((raw - min_possible) / (max_possible - min_possible)) * 100
        else:
            normalized = 50.0
        
        normalized_scores[dim] = round(max(0, min(normalized, 100)), 1)
    
    # Calcular porcentajes relativos (suma = 100%)
    total = sum(normalized_scores.values())
    percentages = {}
    if total > 0:
        for dim in WPI_DIMENSIONS:
            percentages[dim] = round((normalized_scores[dim] / total) * 100, 1)
    else:
        for dim in WPI_DIMENSIONS:
            percentages[dim] = 16.67  # 100% / 6 dimensiones
    
    return raw_scores, normalized_scores, percentages


def load_eri_questions():
    """Carga las preguntas del ERI desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_eri.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_eri_results(responses, questions):
    """
    Calcula los resultados del ERI (Evaluación de Riesgo e Integridad).
    
    IMPORTANTE: En ERI, las puntuaciones altas indican BAJO riesgo, puntuaciones bajas indican ALTO riesgo.
    - Escala Likert: 1 = Totalmente de acuerdo, 5 = Totalmente en desacuerdo
    - Preguntas normales (riesgo): respuesta 1 = riesgo, respuesta 5 = seguro
    - Preguntas reversas (positivas): respuesta 5 = riesgo, respuesta 1 = seguro
    - Preguntas de validez: detectan respuestas poco sinceras (ej: "Nunca he mentido" = sospechoso si responde 1)
    
    Args:
        responses: Lista de respuestas (1-5) del candidato
        questions: Lista de preguntas con dimension, reverse, y validity_check flags
        
    Returns:
        tuple: (raw_scores, normalized_scores, percentages, validity_score, validity_flags)
            - raw_scores: Puntajes directos por dimensión
            - normalized_scores: Puntajes normalizados 0-100 (100 = bajo riesgo, 0 = alto riesgo)
            - percentages: Porcentajes relativos entre dimensiones
            - validity_score: Número de respuestas válidas/sospechosas en preguntas de validez
            - validity_flags: Lista de alertas de validez
    """
    # Contar preguntas por dimensión
    questions_per_dim = {}
    for q in questions:
        dim = q["dimension"]
        questions_per_dim[dim] = questions_per_dim.get(dim, 0) + 1
    
    # Calcular puntajes directos por dimensión
    raw_scores = {dim: 0 for dim in ERI_DIMENSIONS}
    
    # Validez: contar respuestas sospechosas en preguntas de validez
    validity_suspicious = 0
    validity_flags = []
    
    for i, q in enumerate(questions):
        if i < len(responses) and responses[i] is not None:
            dim = q["dimension"]
            answer = responses[i]
            
            # Detectar respuestas de validez (perfeccionismo poco realista)
            if q.get("validity_check", False):
                # Preguntas de validez son afirmaciones perfectas poco realistas:
                # "Nunca he mentido", "Siempre llego puntual", "Nunca he sentido enojo"
                # Si responde 1 o 2 (de acuerdo), es sospechoso
                if answer <= 2:
                    validity_suspicious += 1
                    validity_flags.append(f"Respuesta poco realista en pregunta {i+1}: '{q['question'][:60]}...'")
            
            # Normalizar respuesta a escala de riesgo:
            # Para preguntas normales (reverse=False, comportamiento de riesgo):
            #   respuesta 1 (de acuerdo) = alto riesgo = puntaje bajo
            #   respuesta 5 (en desacuerdo) = bajo riesgo = puntaje alto
            # Para preguntas reversas (reverse=True, comportamiento positivo):
            #   respuesta 5 (en desacuerdo con lo positivo) = alto riesgo = puntaje bajo
            #   respuesta 1 (de acuerdo con lo positivo) = bajo riesgo = puntaje alto
            
            if q.get("reverse", False):
                # Pregunta positiva: mantener directo (1=bueno=5pts, 5=malo=1pt)
                risk_score = answer
            else:
                # Pregunta de riesgo: invertir (1=riesgo=1pt, 5=seguro=5pts)
                risk_score = 6 - answer
            
            raw_scores[dim] += risk_score
    
    # Normalizar a escala 0-100 (100 = bajo riesgo, 0 = alto riesgo)
    normalized_scores = {}
    for dim in ERI_DIMENSIONS:
        num_questions = questions_per_dim.get(dim, 10)
        min_possible = num_questions * 1  # Peor caso: todas respuestas de alto riesgo
        max_possible = num_questions * 5  # Mejor caso: todas respuestas de bajo riesgo
        raw = raw_scores[dim]
        
        # Normalizar a 0-100
        if max_possible > min_possible:
            normalized = ((raw - min_possible) / (max_possible - min_possible)) * 100
        else:
            normalized = 50.0
        
        normalized_scores[dim] = round(max(0, min(normalized, 100)), 1)
    
    # Calcular porcentajes relativos (suma = 100%)
    total = sum(normalized_scores.values())
    percentages = {}
    if total > 0:
        for dim in ERI_DIMENSIONS:
            percentages[dim] = round((normalized_scores[dim] / total) * 100, 1)
    else:
        for dim in ERI_DIMENSIONS:
            percentages[dim] = 16.67  # 100% / 6 dimensiones
    
    # Validez del test: si hay 5 o más respuestas sospechosas, test no confiable
    validity_score = ERI_VALIDITY_QUESTIONS_COUNT - validity_suspicious
    
    return raw_scores, normalized_scores, percentages, validity_score, validity_flags


def analyze_eri_aptitude(normalized, validity_score, validity_flags):
    """
    Analiza los resultados ERI y genera recomendaciones de contratación según nivel de riesgo.
    
    Args:
        normalized: Dict con puntajes normalizados (0-100) por dimensión (100 = bajo riesgo)
        validity_score: Puntaje de validez del test (0-12)
        validity_flags: Lista de alertas de validez
        
    Returns:
        Dict con análisis completo: nivel de riesgo, decisión, fortalezas, alertas, recomendaciones
    """
    # VALIDEZ: Verificar si el test es confiable
    test_valid = validity_score >= (ERI_VALIDITY_QUESTIONS_COUNT - ERI_VALIDITY_THRESHOLD)
    validity_warning = None
    
    if not test_valid:
        validity_warning = f"⚠️ TEST POCO CONFIABLE: {ERI_VALIDITY_QUESTIONS_COUNT - validity_score} respuestas sospechosas detectadas. El candidato puede estar respondiendo de manera poco sincera o tratando de presentarse de forma irrealmente perfecta."
    
    # Ordenar dimensiones por puntaje (mayor = menos riesgo)
    sorted_dims = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    safest = sorted_dims[0]
    riskiest = sorted_dims[-1]
    
    # Clasificar dimensiones por nivel de riesgo
    # Bajo riesgo: >= 66 (Verde)
    # Riesgo moderado: 41-65 (Amarillo)
    # Alto riesgo: 0-40 (Rojo)
    low_risk_dims = [d for d, s in normalized.items() if s >= ERI_RISK_THRESHOLDS["low_risk"]]
    medium_risk_dims = [d for d, s in normalized.items() if ERI_RISK_THRESHOLDS["medium_risk"] <= s < ERI_RISK_THRESHOLDS["low_risk"]]
    high_risk_dims = [d for d, s in normalized.items() if s < ERI_RISK_THRESHOLDS["medium_risk"]]
    critical_risk_dims = [d for d, s in normalized.items() if s < 25]  # Riesgo crítico muy alto
    
    # Calcular puntaje promedio general
    avg_score = sum(normalized.values()) / len(normalized)
    
    # Determinar perfil de riesgo general
    if not test_valid:
        risk_profile = "high_risk"
        risk_level = "🚫 ALTO RIESGO - TEST NO CONFIABLE"
        risk_color = "#EF4444"
        risk_emoji = "🚫"
        risk_desc = validity_warning
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["high_risk"]["decision"]
    elif len(critical_risk_dims) > 0 or len(high_risk_dims) >= 3:
        risk_profile = "high_risk"
        risk_level = "🚫 ALTO RIESGO"
        risk_color = "#EF4444"
        risk_emoji = "🚫"
        risk_desc = f"Múltiples indicadores de riesgo significativo en: {', '.join(high_risk_dims + critical_risk_dims)}. Contratación NO recomendada."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["high_risk"]["decision"]
    elif len(high_risk_dims) >= 1 or len(medium_risk_dims) >= 3:
        risk_profile = "medium_risk"
        risk_level = "⚠️ RIESGO MODERADO"
        risk_color = "#F59E0B"
        risk_emoji = "⚠️"
        all_risk_dims = high_risk_dims + medium_risk_dims
        risk_desc = f"Señales de alerta en: {', '.join(all_risk_dims)}. Requiere evaluación adicional y medidas preventivas."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["medium_risk"]["decision"]
    elif avg_score >= 70:
        risk_profile = "low_risk"
        risk_level = "✅ BAJO RIESGO"
        risk_color = "#10B981"
        risk_emoji = "✅"
        risk_desc = f"Perfil de integridad sobresaliente. Sin indicadores significativos de riesgo. Candidato confiable."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["low_risk"]["decision"]
    else:
        risk_profile = "medium_risk"
        risk_level = "⚠️ RIESGO MODERADO"
        risk_color = "#F59E0B"
        risk_emoji = "⚠️"
        risk_desc = "Perfil dentro de parámetros aceptables con algunas áreas de atención."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["medium_risk"]["decision"]
    
    # Generar fortalezas (dimensiones de bajo riesgo)
    fortalezas = []
    for dim, score in sorted_dims:
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            desc = ERI_DESCRIPTIONS[dim]
            fortalezas.append(f"**{dim}** ({int(score)}/100 - Bajo Riesgo): {desc['low_risk']}")
    
    # Generar alertas (dimensiones de riesgo)
    alertas = []
    if validity_warning:
        alertas.append(validity_warning)
    
    for dim, score in sorted_dims:
        desc = ERI_DESCRIPTIONS[dim]
        if score < ERI_RISK_THRESHOLDS["medium_risk"]:
            alertas.append(f"🚨 **{dim}** ({int(score)}/100 - ALTO RIESGO): {desc['high_risk']}")
        elif score < ERI_RISK_THRESHOLDS["low_risk"]:
            alertas.append(f"⚠️ **{dim}** ({int(score)}/100 - Riesgo Moderado): {desc['medium_risk']}")
    
    # Generar recomendaciones específicas por dimensión
    recomendaciones = []
    hiring_recommendations = ERI_HIRING_RECOMMENDATIONS[risk_profile]
    
    # Agregar recomendaciones de contratación general
    recomendaciones.append(f"**Decisión Recomendada:** {hiring_recommendations['decision']}")
    recomendaciones.append(f"**Resumen:** {hiring_recommendations['resumen']}")
    recomendaciones.append("**Acciones:**")
    for action in hiring_recommendations['acciones']:
        recomendaciones.append(f"  • {action}")
    
    # Agregar recomendaciones específicas por dimensión de riesgo
    recomendaciones.append("\n**Recomendaciones por Dimensión:**")
    for dim, score in sorted_dims:
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            level = "low_risk"
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            level = "medium_risk"
        else:
            level = "high_risk"
        
        # Solo incluir recomendaciones para dimensiones con algún riesgo
        if score < ERI_RISK_THRESHOLDS["low_risk"]:
            recs = ERI_RECOMMENDATIONS[dim][level]
            recomendaciones.append(f"**{dim}:** {' | '.join(recs)}")
    
    return {
        "risk_score": round(avg_score, 1),
        "risk_profile": risk_profile,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_emoji": risk_emoji,
        "risk_desc": risk_desc,
        "hiring_decision": hiring_decision,
        "safest_dimension": safest[0],
        "safest_score": safest[1],
        "riskiest_dimension": riskiest[0],
        "riskiest_score": riskiest[1],
        "low_risk_dimensions": low_risk_dims,
        "medium_risk_dimensions": medium_risk_dims,
        "high_risk_dimensions": high_risk_dims,
        "critical_risk_dimensions": critical_risk_dims,
        "average_score": round(avg_score, 1),
        "fortalezas": fortalezas,
        "alertas": alertas,
        "recomendaciones": recomendaciones,
        "test_valid": test_valid,
        "validity_score": validity_score,
        "validity_warning": validity_warning,
        "validity_flags": validity_flags,
    }


def load_talent_map_questions():
    """Carga las preguntas del Talent Map desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_talent_map.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_talent_map_results(responses, questions):
    """
    Calcula los resultados del Talent Map (Mapeo de Competencias).
    
    Args:
        responses: Lista de respuestas (1-5) del candidato
            1 = Totalmente en desacuerdo
            5 = Totalmente de acuerdo
        questions: Lista de preguntas con competency y reverse flags
        
    Returns:
        tuple: (raw_scores, normalized_scores, percentages)
            - raw_scores: Puntajes directos por competencia
            - normalized_scores: Puntajes normalizados 0-100
            - percentages: Porcentajes relativos entre competencias
    """
    # Contar preguntas por competencia
    questions_per_comp = {}
    for q in questions:
        comp = q["competency"]
        questions_per_comp[comp] = questions_per_comp.get(comp, 0) + 1
    
    # Calcular puntajes directos por competencia
    raw_scores = {comp: 0 for comp in TALENT_MAP_COMPETENCIES}
    
    for i, q in enumerate(questions):
        if i < len(responses) and responses[i] is not None:
            comp = q["competency"]
            answer = responses[i]
            
            # Procesar respuesta según si es reversa o no
            if q.get("reverse", False):
                # Pregunta reversa: invertir escala (5->1, 4->2, etc.)
                score = 6 - answer
            else:
                # Pregunta normal: mantener escala (5 = totalmente de acuerdo = alto)
                score = answer
            
            raw_scores[comp] += score
    
    # Normalizar a escala 0-100
    normalized_scores = {}
    for comp in TALENT_MAP_COMPETENCIES:
        num_questions = questions_per_comp.get(comp, 10)
        min_possible = num_questions * 1  # Peor caso
        max_possible = num_questions * 5  # Mejor caso
        raw = raw_scores[comp]
        
        # Normalizar a 0-100
        if max_possible > min_possible:
            normalized = ((raw - min_possible) / (max_possible - min_possible)) * 100
        else:
            normalized = 50.0
        
        normalized_scores[comp] = round(max(0, min(normalized, 100)), 1)
    
    # Calcular porcentajes relativos (suma = 100%)
    total = sum(normalized_scores.values())
    percentages = {}
    if total > 0:
        for comp in TALENT_MAP_COMPETENCIES:
            percentages[comp] = round((normalized_scores[comp] / total) * 100, 1)
    else:
        for comp in TALENT_MAP_COMPETENCIES:
            percentages[comp] = 12.5  # 100% / 8 competencias
    
    return raw_scores, normalized_scores, percentages


def analyze_talent_map_match(normalized_scores, selected_job_profile=None):
    """
    Analiza los resultados de Talent Map y calcula match con perfil de puesto.
    
    Args:
        normalized_scores: Dict con puntajes normalizados (0-100) por competencia
        selected_job_profile: Nombre del perfil de puesto para comparar (opcional)
        
    Returns:
        Dict con análisis completo: fortalezas, áreas de desarrollo, recomendaciones, match
    """
    # Ordenar competencias por puntaje
    sorted_comps = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_comps[0]
    weakest = sorted_comps[-1]
    
    # Clasificar competencias por nivel
    # Alto: >= 75
    # Medio: 50-74
    # Bajo: < 50
    high_comps = [(c, s) for c, s in normalized_scores.items() if s >= 75]
    medium_comps = [(c, s) for c, s in normalized_scores.items() if 50 <= s < 75]
    low_comps = [(c, s) for c, s in normalized_scores.items() if s < 50]
    
    # Calcular puntaje promedio general
    avg_score = sum(normalized_scores.values()) / len(normalized_scores)
    
    # Generar fortalezas (competencias altas)
    fortalezas = []
    for comp, score in high_comps:
        desc = TALENT_MAP_DESCRIPTIONS[comp]
        fortalezas.append(f"**{comp}** ({int(score)}/100): {desc['high']}")
    
    # Generar áreas de desarrollo (competencias bajas)
    areas_desarrollo = []
    for comp, score in low_comps:
        desc = TALENT_MAP_DESCRIPTIONS[comp]
        areas_desarrollo.append(f"**{comp}** ({int(score)}/100): {desc['low']}")
    
    # Generar recomendaciones generales
    recomendaciones = []
    for comp, score in sorted_comps:
        if score >= 75:
            level = "high"
        elif score >= 50:
            level = "medium"
        else:
            level = "low"
        
        recs = TALENT_MAP_COMPETENCY_RECOMMENDATIONS[level]
        recomendaciones.append(f"**{comp}:** {' | '.join(recs)}")
    
    # Análisis de match con perfil de puesto (si se especificó)
    match_analysis = None
    match_percentage = None
    match_level = None
    match_color = None
    match_label = None
    match_gaps = []
    match_strengths = []
    
    if selected_job_profile and selected_job_profile in TALENT_MAP_JOB_PROFILES:
        profile = TALENT_MAP_JOB_PROFILES[selected_job_profile]
        profile_comps = profile["competencias"]
        
        # Calcular diferencias por competencia
        total_gap = 0
        max_possible_gap = 0
        
        for comp in TALENT_MAP_COMPETENCIES:
            required = profile_comps.get(comp, 50)
            actual = normalized_scores.get(comp, 0)
            gap = required - actual
            
            max_possible_gap += required
            
            if gap > 15:  # Gap significativo
                match_gaps.append(f"**{comp}**: Requiere {int(required)}, tiene {int(actual)} (brecha de {int(gap)} puntos)")
            elif gap < -10:  # Excede significativamente
                match_strengths.append(f"**{comp}**: Excede requisito ({int(actual)} vs {int(required)} requerido)")
            
            # Calcular distancia absoluta para el match
            total_gap += abs(gap)
        
        # Calcular match percentage (inverso de la brecha promedio)
        # 100% = sin brecha, 0% = brecha máxima
        avg_gap = total_gap / len(TALENT_MAP_COMPETENCIES)
        match_percentage = max(0, min(100, 100 - avg_gap))
        
        # Determinar nivel de match
        for level_name, level_info in TALENT_MAP_MATCH_LEVELS.items():
            if match_percentage >= level_info["min"]:
                match_level = level_name
                match_label = level_info["label"]
                match_color = level_info["color"]
                match_desc = level_info["descripcion"]
                break
        
        match_analysis = {
            "job_profile": selected_job_profile,
            "job_emoji": profile["emoji"],
            "job_description": profile["descripcion"],
            "match_percentage": round(match_percentage, 1),
            "match_level": match_level,
            "match_label": match_label,
            "match_color": match_color,
            "match_desc": match_desc,
            "match_gaps": match_gaps,
            "match_strengths": match_strengths,
            "profile_scores": profile_comps
        }
    
    return {
        "average_score": round(avg_score, 1),
        "strongest_competency": strongest[0],
        "strongest_score": strongest[1],
        "weakest_competency": weakest[0],
        "weakest_score": weakest[1],
        "high_competencies": [c for c, s in high_comps],
        "medium_competencies": [c for c, s in medium_comps],
        "low_competencies": [c for c, s in low_comps],
        "fortalezas": fortalezas,
        "areas_desarrollo": areas_desarrollo,
        "recomendaciones": recomendaciones,
        "match_analysis": match_analysis
    }


def calculate_desempeno_results(rendimiento_scores, potencial_scores, iniciativas=None):
    """
    Calcula resultados de evaluación de desempeño.
    
    rendimiento_scores: dict con calificaciones 1-5 de los 6 objetivos {1: 5, 2: 4, ...}
    potencial_scores: dict con calificaciones 0-3 de las 5 dimensiones {1: 3, 2: 2, ...}
    iniciativas: list de 3 textos con iniciativas de mejora (opcional)
    
    Returns: dict con análisis completo
    """
    # Calcular promedios
    promedio_rendimiento = sum(rendimiento_scores.values()) / len(rendimiento_scores)
    promedio_potencial = sum(potencial_scores.values()) / len(potencial_scores)
    
    # Puntaje global ponderado (60% rendimiento + 40% potencial normalizado)
    # Normalizar potencial de escala 0-3 a escala 0-5
    potencial_normalizado = (promedio_potencial / 3) * 5
    puntaje_global = (promedio_rendimiento * 0.6) + (potencial_normalizado * 0.4)
    
    # Determinar clasificación
    clasificacion = None
    for nivel, info in sorted(DESEMPENO_CLASIFICACION.items(), key=lambda x: x[1]["min"], reverse=True):
        if puntaje_global >= info["min"]:
            clasificacion = {
                "nivel": nivel,
                "label": info["label"],
                "color": info["color"],
                "descripcion": info["descripcion"]
            }
            break
    
    # Identificar fortalezas (objetivos con 4 o 5)
    fortalezas_rendimiento = []
    for obj_id, score in rendimiento_scores.items():
        if score >= 4:
            objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
            fortalezas_rendimiento.append({
                "titulo": objetivo["titulo"],
                "score": score,
                "label": DESEMPENO_ESCALA_RENDIMIENTO[score]["label"]
            })
    
    # Identificar áreas de mejora (objetivos con 1, 2 o 3)
    areas_mejora_rendimiento = []
    for obj_id, score in rendimiento_scores.items():
        if score <= 3:
            objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
            areas_mejora_rendimiento.append({
                "titulo": objetivo["titulo"],
                "score": score,
                "label": DESEMPENO_ESCALA_RENDIMIENTO[score]["label"]
            })
    
    # Identificar fortalezas de potencial (nivel 3 o 2)
    fortalezas_potencial = []
    for dim_id, score in potencial_scores.items():
        if score >= 2:
            dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
            fortalezas_potencial.append({
                "nombre": dimension["nombre"],
                "score": score,
                "nivel": f"Nivel {score}"
            })
    
    # Identificar áreas de desarrollo de potencial (nivel 0 o 1)
    areas_desarrollo_potencial = []
    for dim_id, score in potencial_scores.items():
        if score <= 1:
            dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
            areas_desarrollo_potencial.append({
                "nombre": dimension["nombre"],
                "score": score,
                "nivel": f"Nivel {score}"
            })
    
    # Generar recomendaciones generales
    recomendaciones = []
    if puntaje_global >= 4.5:
        recomendaciones.append("Empleado con desempeño excepcional. Considerar para promociones o proyectos de alto impacto.")
        recomendaciones.append("Puede servir como mentor para otros colaboradores.")
        recomendaciones.append("Mantener motivación con retos profesionales y reconocimiento.")
    elif puntaje_global >= 3.5:
        recomendaciones.append("Empleado con desempeño destacado. Continuar fortaleciendo sus competencias.")
        recomendaciones.append("Identificar oportunidades de desarrollo para alcanzar siguiente nivel.")
        recomendaciones.append("Reconocer logros y mantener nivel de compromiso.")
    elif puntaje_global >= 2.5:
        recomendaciones.append("Empleado con desempeño satisfactorio pero con áreas de mejora identificadas.")
        recomendaciones.append("Implementar plan de capacitación en áreas específicas.")
        recomendaciones.append("Establecer seguimiento trimestral para monitorear progreso.")
    else:
        recomendaciones.append("Desempeño insuficiente. Requiere plan de acción inmediato.")
        recomendaciones.append("Implementar plan de mejoramiento con metas claras y medibles.")
        recomendaciones.append("Seguimiento mensual obligatorio con evaluación en 3 meses.")
        recomendaciones.append("Considerar reubicación o capacitación intensiva.")
    
    # Recomendaciones específicas por áreas de mejora
    if len(areas_mejora_rendimiento) > 0:
        recomendaciones.append(f"Áreas prioritarias de rendimiento: {', '.join([a['titulo'] for a in areas_mejora_rendimiento[:3]])}")
    
    if len(areas_desarrollo_potencial) > 0:
        recomendaciones.append(f"Dimensiones de potencial a desarrollar: {', '.join([a['nombre'] for a in areas_desarrollo_potencial])}")
    
    # Determinar si requiere iniciativas
    requiere_iniciativas = promedio_rendimiento < 3 or promedio_potencial < 2
    
    return {
        "promedio_rendimiento": round(promedio_rendimiento, 2),
        "promedio_potencial": round(promedio_potencial, 2),
        "puntaje_global": round(puntaje_global, 2),
        "clasificacion": clasificacion,
        "fortalezas_rendimiento": fortalezas_rendimiento,
        "areas_mejora_rendimiento": areas_mejora_rendimiento,
        "fortalezas_potencial": fortalezas_potencial,
        "areas_desarrollo_potencial": areas_desarrollo_potencial,
        "recomendaciones": recomendaciones,
        "requiere_iniciativas": requiere_iniciativas,
        "iniciativas": iniciativas if iniciativas else []
    }


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

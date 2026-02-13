"""
Constantes y configuraciones para las evaluaciones psicométricas.
Incluye definiciones de VALANTI, WPI, ERI, TALENT MAP y DESEMPEÑO.
"""

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

WPI_DIMENSIONS = [
    "Responsabilidad",
    "Trabajo en Equipo", 
    "Adaptabilidad",
    "Autodisciplina",
    "Estabilidad Emocional",
    "Orientación al Logro"
]

WPI_COLORS = {
    "Responsabilidad": "#3B82F6",
    "Trabajo en Equipo": "#10B981",
    "Adaptabilidad": "#F59E0B",
    "Autodisciplina": "#8B5CF6",
    "Estabilidad Emocional": "#06B6D4",
    "Orientación al Logro": "#EF4444"
}

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

ERI_DIMENSIONS = [
    "Honestidad",
    "Confiabilidad",
    "Consumo de Sustancias",
    "Control de Impulsos",
    "Actitud hacia Normas",
    "Hostilidad Laboral"
]

ERI_COLORS = {
    "Honestidad": "#10B981",
    "Confiabilidad": "#3B82F6",
    "Consumo de Sustancias": "#F59E0B",
    "Control de Impulsos": "#EF4444",
    "Actitud hacia Normas": "#8B5CF6",
    "Hostilidad Laboral": "#EC4899"
}

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

ERI_RISK_THRESHOLDS = {
    "low_risk": 66,
    "medium_risk": 41,
    "high_risk": 0
}

ERI_VALIDITY_QUESTIONS_COUNT = 12
ERI_VALIDITY_THRESHOLD = 5

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

TALENT_MAP_COLORS = {
    "Liderazgo": "#EF4444",
    "Comunicación": "#3B82F6",
    "Pensamiento Analítico": "#8B5CF6",
    "Innovación y Creatividad": "#F59E0B",
    "Orientación al Cliente": "#10B981",
    "Trabajo en Equipo": "#06B6D4",
    "Gestión del Cambio": "#EC4899",
    "Resolución de Problemas": "#14B8A6"
}

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

TALENT_MAP_MATCH_LEVELS = {
    "excelente": {"min": 85, "label": "🌟 Excelente Match", "color": "#10B981", "descripcion": "Competencias altamente alineadas con el perfil del puesto"},
    "muy_bueno": {"min": 75, "label": "✅ Muy Buen Match", "color": "#3B82F6", "descripcion": "Competencias bien alineadas, candidato muy apto para el rol"},
    "bueno": {"min": 65, "label": "👍 Buen Match", "color": "#F59E0B", "descripcion": "Competencias aceptables, puede requerir desarrollo en algunas áreas"},
    "aceptable": {"min": 50, "label": "⚠️ Match Aceptable", "color": "#EF4444", "descripcion": "Competencias limitadas, requiere capacitación significativa"},
    "bajo": {"min": 0, "label": "❌ Match Bajo", "color": "#991B1B", "descripcion": "Competencias insuficientes para el rol, no recomendado"}
}

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

DESEMPENO_ESCALA_RENDIMIENTO = {
    5: {"label": "Sobresaliente", "descripcion": "Resultado claramente sobre lo esperado", "color": "#10B981"},
    4: {"label": "Supera las expectativas", "descripcion": "Resultado que satisface plenamente las expectativas", "color": "#3B82F6"},
    3: {"label": "Cumple las expectativas", "descripcion": "Nivel de resultado aceptable, pero podría mejorar", "color": "#F59E0B"},
    2: {"label": "Debajo de las expectativas", "descripcion": "Resultado elemental, poco satisfactorio", "color": "#EF4444"},
    1: {"label": "Insatisfactorio", "descripcion": "Resultado deficiente. No alcanzó los requerimientos mínimos", "color": "#991B1B"}
}

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

DESEMPENO_CLASIFICACION = {
    "sobresaliente": {"min": 4.5, "label": "🌟 Sobresaliente", "color": "#10B981", "descripcion": "Desempeño excepcional que supera ampliamente las expectativas"},
    "supera": {"min": 3.5, "label": "⭐ Supera las Expectativas", "color": "#3B82F6", "descripcion": "Desempeño destacado que supera lo esperado"},
    "cumple": {"min": 2.5, "label": "✅ Cumple las Expectativas", "color": "#F59E0B", "descripcion": "Desempeño satisfactorio que cumple lo esperado"},
    "debajo": {"min": 1.5, "label": "⚠️ Debajo de las Expectativas", "color": "#EF4444", "descripcion": "Desempeño insuficiente que requiere mejora"},
    "insatisfactorio": {"min": 0, "label": "❌ Insatisfactorio", "color": "#991B1B", "descripcion": "Desempeño deficiente que requiere plan de acción inmediato"}
}

DESEMPENO_COLORES_DIMENSIONES = {
    "Motivaciones Personales": "#8B5CF6",
    "Visión": "#3B82F6",
    "Disposición para Sobresalir": "#10B981",
    "Compromiso": "#F59E0B",
    "Capacidad de Aprendizaje": "#EF4444"
}

# =========================================================================
# RECOMENDACIONES DISC
# =========================================================================

DISC_STYLE_NAMES = {
    "D": "Dominancia",
    "I": "Influencia",
    "S": "Estabilidad",
    "C": "Cumplimiento/Minuciosidad"
}

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

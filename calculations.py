"""
Funciones de cálculo para todas las evaluaciones psicométricas.
"""
import os
import json
from constants import *


# =========================================================================
# CÁLCULOS DISC
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


def calculate_behavioral_styles(normalized):
    """
    Deriva 9 estilos conductuales a partir de los puntajes DISC normalizados.
    Cada estilo tiene 4 sub-dimensiones mapeadas a D, I, S, C respectivamente.
    Inspirado en la metodología THT de perfilamiento conductual.
    """
    D = normalized.get('D', 50)
    I = normalized.get('I', 50)
    S = normalized.get('S', 50)
    C = normalized.get('C', 50)

    # El complemento (100 - S) representa el grado de aceleración / baja resistencia
    # El complemento (100 - I) representa introversión relativa
    styles = {
        "Comunicación": {
            "subs": {
                "Franqueza": round(D),           # Decir las cosas sin rodeos
                "Expresividad": round(I),         # Compartir ideas con entusiasmo
                "Autoregulación": round(S),       # Controlar lo que se dice
                "Formalidad": round(C),           # Prudencia y moderación al hablar
            },
            "desc": {
                "Franqueza": "Sinceridad y dirección al comunicarse",
                "Expresividad": "Facilidad para dar a conocer ideas con optimismo",
                "Autoregulación": "Capacidad de controlar lo que se dice",
                "Formalidad": "Comportamiento prudente y moderado al expresarse",
            }
        },
        "Delegación": {
            "subs": {
                "Control": round(D),              # Comprobar e inspeccionar todo
                "Inspiración": round(I),          # Motivar a otros para trabajar
                "Moderación": round(S),           # Dar instrucciones y esperar sin presionar
                "Exigencia": round(C),            # Demandar altos estándares de calidad
            },
            "desc": {
                "Control": "Tendencia a comprobar e inspeccionar a su alrededor",
                "Inspiración": "Capacidad para motivar a otros en sus tareas",
                "Moderación": "Tendencia a dar instrucciones y esperar sin presionar",
                "Exigencia": "Tendencia a demandar altos estándares de calidad",
            }
        },
        "Emprendimiento": {
            "subs": {
                "Insistencia": round(D),          # Actuar por encima de obstáculos
                "Optimismo": round(I),            # Ver el aspecto más favorable
                "Focalización": round(S),         # Centrarse en pocas tareas sistemáticamente
                "Planificación": round(C),        # Acometer proyectos con control del riesgo
            },
            "desc": {
                "Insistencia": "Capacidad para actuar por encima de los obstáculos",
                "Optimismo": "Tendencia a ver el aspecto más favorable de las cosas",
                "Focalización": "Tendencia a centrarse en pocas tareas de forma sistemática",
                "Planificación": "Facilidad para iniciar proyectos con control del riesgo",
            }
        },
        "Liderazgo": {
            "subs": {
                "Por Resultados": round(D),       # Movilizar por logros
                "Por Inspiración": round(I),      # Movilizar por ideas inspiradoras
                "Democrático": round(S),          # Movilizar por confianza y participación
                "Conservador": round(C),          # Movilizar por acciones seguras
            },
            "desc": {
                "Por Resultados": "Tendencia a movilizar al grupo en función de logros",
                "Por Inspiración": "Tendencia a movilizar por ideas inspiradoras",
                "Democrático": "Tendencia a movilizar por confianza y participación",
                "Conservador": "Tendencia a movilizar por acciones seguras y demostradas",
            }
        },
        "Adaptación al Cambio": {
            "subs": {
                "Resolución": round(D),           # Actuar con determinación ante el cambio
                "Positivismo": round(I),          # Pensar que lo mejor puede suceder
                "Resistencia": round(100 - S),    # Permanecer igual, evitando cambiar (invertido)
                "Consistencia": round(C),         # Pensar y actuar siempre de la misma manera
            },
            "desc": {
                "Resolución": "Tendencia a actuar con determinación al aceptar el cambio",
                "Positivismo": "Tendencia a pensar que lo mejor puede suceder en el nuevo entorno",
                "Resistencia": "Tendencia a resistir el cambio hasta que sea inevitable",
                "Consistencia": "Tendencia a pensar y actuar siempre de la misma manera",
            }
        },
        "Manejo del Conflicto": {
            "subs": {
                "Confrontación": round(D),        # Debatir y argumentar su punto de vista
                "Apasionamiento": round(I),       # Expresarse elocuentemente
                "Inalterabilidad": round(S),      # Retener reacciones cuando se le presiona
                "Severidad": round(C),            # Exigencia y rigor para que las cosas se hagan
            },
            "desc": {
                "Confrontación": "Tendencia a debatir y argumentar su punto de vista",
                "Apasionamiento": "Tendencia a expresarse de forma elocuente sobre lo que importa",
                "Inalterabilidad": "Tendencia a retener reacciones cuando se le presiona",
                "Severidad": "Tendencia a actuar con exigencia y rigor para que las cosas se hagan bien",
            }
        },
        "Manejo del Tiempo": {
            "subs": {
                "Priorización": round(D),         # Dirigir atención hacia mejores resultados
                "Entusiasmo": round(I),           # Trabajar con motivación en tareas de interés
                "Pausa": round(S),                # Actuar de forma recatada y moderada
                "Precisión": round(C),            # Cumplir tiempos establecidos con precisión
            },
            "desc": {
                "Priorización": "Tendencia a dirigir la atención hacia los asuntos de mayor impacto",
                "Entusiasmo": "Tendencia a trabajar con motivación en tareas de interés",
                "Pausa": "Tendencia a actuar de forma tranquila y moderada",
                "Precisión": "Tendencia a cumplir los tiempos establecidos de forma precisa",
            }
        },
        "Manejo Emocional": {
            "subs": {
                "Franqueza": round(D),            # Decir las cosas por su nombre
                "Extroversión": round(I),         # Manifestar sentimientos con entusiasmo
                "Autocontrol": round(S),          # Controlar o regular su propia conducta
                "Reflexibilidad": round(C),       # Pensar detenidamente las cosas
            },
            "desc": {
                "Franqueza": "Capacidad para decir las cosas por su nombre",
                "Extroversión": "Facilidad para manifestar sentimientos o pensamientos con entusiasmo",
                "Autocontrol": "Capacidad para controlar o regular su propia conducta",
                "Reflexibilidad": "Tendencia a pensar detenidamente las cosas antes de actuar",
            }
        },
        "Negociación": {
            "subs": {
                "Pragmatismo": round(D),          # Valorar utilidad y valor práctico
                "Persuasión": round(I),           # Convencer a través de argumentos positivos
                "Calma": round(S),                # Autocontrolar reacciones y esperar el momento
                "Rigidez": round(C),              # Actuar de manera rigurosa e inflexible
            },
            "desc": {
                "Pragmatismo": "Tendencia a valorar la utilidad y el valor práctico de las cosas",
                "Persuasión": "Facilidad para convencer o disuadir con argumentos positivos",
                "Calma": "Tendencia a autocontrolar reacciones y esperar el momento oportuno",
                "Rigidez": "Propensión a actuar de manera rigurosa, severa e inflexible",
            }
        },
    }
    return styles


def get_disc_temperament(normalized):
    """
    Determina el temperamento dominante basado en los puntajes DISC.
    Mapeo clásico: D=Colérico, I=Sanguíneo, S=Flemático, C=Melancólico.
    """
    D = normalized.get('D', 50)
    I = normalized.get('I', 50)
    S = normalized.get('S', 50)
    C = normalized.get('C', 50)

    temperament_map = {
        'Colérico': {'score': D, 'style': 'D', 'adj': 'colérico',
                     'desc': 'activo, decidido, orientado a resultados y con fuerte impulso de liderazgo'},
        'Sanguíneo': {'score': I, 'style': 'I', 'adj': 'sanguíneo',
                      'desc': 'optimista, sociable, entusiasta y con facilidad para relacionarse'},
        'Flemático': {'score': S, 'style': 'S', 'adj': 'flemático',
                      'desc': 'tranquilo, estable, constante y orientado al equipo'},
        'Melancólico': {'score': C, 'style': 'C', 'adj': 'melancólico',
                        'desc': 'perfeccionista, analítico, organizado y orientado a la calidad'},
    }

    sorted_temps = sorted(temperament_map.items(), key=lambda x: x[1]['score'], reverse=True)
    primary_name, primary_data = sorted_temps[0]
    secondary_name, secondary_data = sorted_temps[1]

    return {
        'primary': primary_name,
        'secondary': secondary_name,
        'primary_score': primary_data['score'],
        'secondary_score': secondary_data['score'],
        'label': f"predominantemente {primary_data['adj']} y {secondary_data['adj']}",
        'description': f"{primary_data['desc']}; con rasgos {secondary_data['adj']}s de {secondary_data['desc']}",
    }


def generate_disc_mega_summary(normalized):
    """
    Genera un resumen conductual de 16 puntos basado en el perfil DISC.
    Inspirado en la metodología de reporte de 32 frases de THT.
    """
    D = normalized.get('D', 50)
    I = normalized.get('I', 50)
    S = normalized.get('S', 50)
    C = normalized.get('C', 50)

    def level(score):
        if score >= 70: return 'high'
        if score >= 40: return 'mid'
        return 'low'

    lD, lI, lS, lC = level(D), level(I), level(S), level(C)

    phrases = {
        'como_es': {
            ('high','high','low','low'): "Persona decidida, entusiasta, carismática y orientada a la acción.",
            ('high','low','low','high'): "Persona confrontante, rigurosa, realista e inquieta.",
            ('high','low','low','low'): "Persona confrontante, dominante, directa y orientada a resultados.",
            ('low','high','high','low'): "Persona cálida, sociable, paciente y empática.",
            ('low','low','high','high'): "Persona metódica, paciente, detallista y estable.",
            ('low','high','low','high'): "Persona persuasiva, organizada, analítica y relacional.",
        },
        'que_busca': {
            'high_D': "Tener el control, la excelencia y actuar de forma expedita.",
            'high_I': "Conectar con las personas, inspirar y ser reconocido.",
            'high_S': "Mantener la armonía, estabilidad y un entorno predecible.",
            'high_C': "La precisión, la calidad y cumplir con los estándares establecidos.",
        },
        'ambiente_ideal': {
            'high_D': "Entorno libre de control excesivo, con privacidad, autonomía y dinamismo.",
            'high_I': "Entorno social, colaborativo y con reconocimiento constante.",
            'high_S': "Entorno estable, predecible y con relaciones duraderas.",
            'high_C': "Entorno estructurado, con procesos claros y altos estándares.",
        },
        'gran_limitante': {
            'high_D': "Podría ser poco diplomático, parca, incrédulo y fácilmente irritable.",
            'high_I': "Puede distraerse, desorganizarse y prometer más de lo que cumple.",
            'high_S': "Puede resistirse al cambio y evitar confrontaciones necesarias.",
            'high_C': "Puede ser demasiado crítico, perfeccionista e inflexible.",
        },
    }

    # Determinar el estilo dominante para las frases
    dominant = max({'D': D, 'I': I, 'S': S, 'C': C}.items(), key=lambda x: x[1])
    secondary = sorted({'D': D, 'I': I, 'S': S, 'C': C}.items(), key=lambda x: x[1], reverse=True)[1]

    dom_key = f"high_{dominant[0]}"
    sec_key = f"high_{secondary[0]}"

    # Construir mega resumen
    summary = {
        "Cómo es": _pick_como_es(lD, lI, lS, lC),
        "Qué busca": phrases['que_busca'].get(dom_key, phrases['que_busca']['high_D']),
        "Ambiente ideal": phrases['ambiente_ideal'].get(dom_key, phrases['ambiente_ideal']['high_D']),
        "Gran limitante": phrases['gran_limitante'].get(dom_key, phrases['gran_limitante']['high_D']),
        "Cómo lidera": _describe_leadership(D, I, S, C),
        "Cómo decide": _describe_decision(D, I, S, C),
        "Cómo negocia": _describe_negotiation(D, I, S, C),
        "Cómo maneja el conflicto": _describe_conflict(D, I, S, C),
        "Cómo se relaciona": _describe_relations(D, I, S, C),
        "Qué le motiva": _describe_motivation(D, I, S, C),
        "Qué le desmotiva": _describe_demotivation(D, I, S, C),
        "Valor para el equipo": _describe_team_value(D, I, S, C),
        "Cómo bajo presión": _describe_under_pressure(D, I, S, C),
        "Cómo entrenarle": _describe_training(D, I, S, C),
        "Cómo darle feedback": _describe_feedback(D, I, S, C),
        "Recomendación clave": _describe_recommendation(D, I, S, C),
    }
    return summary


def _pick_como_es(lD, lI, lS, lC):
    key = (lD, lI, lS, lC)
    options = {
        ('high','high','low','low'): "Persona decidida, entusiasta, carismática y orientada a la acción.",
        ('high','high','low','mid'): "Persona dinámica, decidida, entusiasta y con capacidad de análisis.",
        ('high','low','low','high'): "Persona confrontante, rigurosa, realista e inquieta.",
        ('high','mid','low','high'): "Persona confrontante, rigurosa, realista e inquieta, con capacidad de influencia.",
        ('high','low','low','mid'): "Persona directa, analítica, orientada a resultados y exigente.",
        ('high','low','mid','high'): "Persona exigente, rigurosa, metódica y orientada a la calidad con alto dinamismo.",
        ('high','low','low','low'): "Persona confrontante, dominante, directa y orientada a resultados.",
        ('low','high','high','low'): "Persona cálida, sociable, paciente y empática con su entorno.",
        ('low','low','high','high'): "Persona metódica, paciente, detallista y orientada a la estabilidad.",
        ('low','high','low','high'): "Persona persuasiva, organizada, analítica con habilidad relacional.",
        ('low','mid','high','high'): "Persona estable, analítica, consistente y orientada a la calidad.",
        ('mid','mid','mid','mid'): "Persona versátil con un perfil conductual equilibrado y adaptable.",
        ('high','mid','low','mid'): "Persona activa, decidida, directa y con habilidad de influencia moderada.",
        ('mid','high','mid','low'): "Persona entusiasta, sociable, dinámica y orientada a las relaciones.",
        ('low','low','mid','high'): "Persona analítica, tranquila, rigurosa y orientada al detalle.",
    }
    # Primero busca match exacto
    if key in options:
        return options[key]
    # Si no, describe según el estilo dominante
    dominant = max({'D': lD, 'I': lI, 'S': lS, 'C': lC}.items(), key=lambda x: ['low','mid','high'].index(x[1]))
    fallbacks = {
        'D': "Persona decidida, dominante, orientada a resultados y directa en su comunicación.",
        'I': "Persona optimista, sociable, entusiasta y orientada a las relaciones interpersonales.",
        'S': "Persona tranquila, estable, paciente y orientada al apoyo del equipo.",
        'C': "Persona analítica, detallista, rigurosa y orientada a la calidad y los estándares.",
    }
    return fallbacks.get(dominant[0], "Persona con perfil conductual equilibrado y versátil.")


def _describe_leadership(D, I, S, C):
    if D >= 70 and C >= 70: return "Moviliza a los demás con pragmatismo, exigiendo, validando cada paso y ejecutando con celeridad."
    if D >= 70 and I >= 70: return "Lidera con carisma y determinación, inspirando con energía y tomando decisiones ágiles."
    if I >= 70 and S >= 70: return "Lidera por inspiración y confianza, creando ambientes de colaboración y motivación."
    if S >= 70 and C >= 70: return "Lidera de forma conservadora y metódica, asegurando procesos sólidos y confiables."
    if D >= 70: return "Lidera por resultados, movilizando al equipo hacia logros concretos y de alto impacto."
    if I >= 70: return "Lidera con entusiasmo e inspiración, motivando a otros con ideas y visión positiva."
    if S >= 70: return "Lidera de forma democrática, construyendo confianza y fomentando la participación."
    return "Lidera de manera conservadora, con acciones demostradas y planificación cuidadosa."


def _describe_decision(D, I, S, C):
    if D >= 70 and C >= 70: return "Resuelve con determinación, analizando hasta el último detalle y actuando con cautela sin demoras."
    if D >= 70: return "Decide rápidamente y con firmeza, priorizando la acción sobre el análisis exhaustivo."
    if C >= 70: return "Analiza minuciosamente antes de decidir, asegurándose de contar con toda la información."
    if I >= 70: return "Decide con intuición y entusiasmo, buscando el apoyo de otros antes de actuar."
    return "Decide de forma equilibrada, considerando los hechos y el impacto en el equipo."


def _describe_negotiation(D, I, S, C):
    if D >= 70 and C >= 70: return "Llega a acuerdos defendiendo con fuerza sus intereses, gestionando la información y explicando rápidamente."
    if D >= 70: return "Negocia con firmeza y orientación a resultados, cediendo poco y cerrando rápido."
    if I >= 70: return "Negocia con persuasión y entusiasmo, buscando acuerdos que beneficien a todas las partes."
    if S >= 70: return "Negocia con calma y paciencia, prefiriendo consensos y evitando confrontaciones."
    return "Negocia de forma rigurosa y planificada, basándose en datos y estándares claros."


def _describe_conflict(D, I, S, C):
    if D >= 70: return "Reacciona debatiendo directamente, buscando justicia y actuando de inmediato."
    if I >= 70: return "Busca resolver el conflicto con entusiasmo y persuasión, apelando a las relaciones."
    if S >= 70: return "Tiende a evitar el conflicto, buscando armonía y conciliación entre las partes."
    return "Analiza el conflicto con detalle antes de reaccionar, buscando una solución lógica."


def _describe_relations(D, I, S, C):
    if D >= 70 and C >= 70: return "Interactúa de forma contundente, fría, avisada y diligente."
    if I >= 70 and S >= 70: return "Se relaciona de forma cálida, abierta y con genuino interés por los demás."
    if D >= 70: return "Se relaciona de forma directa y asertiva, valorando la eficiencia sobre lo social."
    if I >= 70: return "Se relaciona de forma entusiasta y sociable, construyendo redes con facilidad."
    if S >= 70: return "Se relaciona de forma leal y estable, manteniendo vínculos duraderos."
    return "Se relaciona de forma correcta y estructurada, respetando límites y roles."


def _describe_motivation(D, I, S, C):
    if D >= 70: return "Le estimulan los grandes retos, la información clara, la discreción y la interactividad."
    if I >= 70: return "Le motiva el reconocimiento, la sociabilidad, los ambientes creativos y la libertad de expresión."
    if S >= 70: return "Le motiva la estabilidad, el trabajo en equipo, la lealtad y un entorno predecible."
    return "Le motiva la precisión, los sistemas, la calidad del trabajo y el cumplimiento de estándares."


def _describe_demotivation(D, I, S, C):
    if D >= 70: return "Le desaniman la falta de resultados, el desorden, las promesas incumplidas y la inactividad."
    if I >= 70: return "Le desmotiva la repetición, la rigidez, la falta de reconocimiento y el trabajo en solitario."
    if S >= 70: return "Le desmotiva la inestabilidad, los cambios abruptos y los ambientes de alta presión."
    return "Le desmotiva el trabajo impreciso, los errores tolerados y la falta de estructura."


def _describe_team_value(D, I, S, C):
    if D >= 70: return "Aporta metas ambiciosas, control del riesgo, planes de contingencia y vitalidad."
    if I >= 70: return "Aporta entusiasmo, ideas innovadoras, conexión interpersonal y motivación al grupo."
    if S >= 70: return "Aporta estabilidad, lealtad, escucha activa y soporte constante al equipo."
    return "Aporta rigor, calidad, análisis profundo y sistemas de trabajo eficientes."


def _describe_under_pressure(D, I, S, C):
    if D >= 70: return "Tiende a reaccionar de manera impositiva, salvando responsabilidades y de forma reactiva."
    if I >= 70: return "Puede volverse impulsivo, disperso o buscar validación externa ante la presión."
    if S >= 70: return "Puede bloquearse, evitar decisiones y necesitar más tiempo del usual para actuar."
    return "Puede volverse hipercrítico, perfeccionista en exceso y paralizado por el análisis."


def _describe_training(D, I, S, C):
    if D >= 70: return "Aprende mejor con actividades competitivas, instrucciones detalladas, casos prácticos y tareas dinámicas."
    if I >= 70: return "Aprende mejor con dinámicas grupales, role-playing, feedforward y ambientes creativos."
    if S >= 70: return "Aprende mejor con procesos paso a paso, mentorías estables y ambientes seguros de práctica."
    return "Aprende mejor con documentación detallada, análisis de casos y tiempo para reflexionar."


def _describe_feedback(D, I, S, C):
    if D >= 70 and C >= 70: return "Argumentar con franqueza total rigurosidad, validar todo lo que va a decir y centrarse rápidamente en lo que se debe mejorar."
    if D >= 70: return "Ser directo y concreto con hechos y datos, evitar rodeos y ofrecer soluciones inmediatas."
    if I >= 70: return "Iniciar con lo positivo, usar un tono motivador y reconocer sus esfuerzos antes de señalar mejoras."
    if S >= 70: return "Hacerlo en privado, con calma, con tiempo suficiente y reforzando la relación de confianza."
    return "Presentar datos concretos, dar tiempo para procesar y enfocarse en el proceso más que en la persona."


def _describe_recommendation(D, I, S, C):
    if D >= 70 and C >= 70: return "Es clave que potencie su capacidad natural para hacer que las cosas sucedan, ser exigente con la calidad, aterrizar las ideas y moverse con prontitud."
    if D >= 70 and I >= 70: return "Es clave canalizar su energía y entusiasmo hacia objetivos concretos, aprendiendo a delegar y escuchar más."
    if I >= 70 and S >= 70: return "Es clave aprovechar su calidez y sociabilidad para construir equipos sólidos, desarrollando asertividad cuando sea necesario."
    if S >= 70 and C >= 70: return "Es clave aprovechar su rigor y estabilidad para ser un referente de calidad, trabajando en mayor flexibilidad y toma de decisiones ágiles."
    if D >= 70: return "Es clave aprender a escuchar más, tolerar el ritmo de otros y construir relaciones de confianza."
    if I >= 70: return "Es clave desarrollar disciplina de seguimiento, organización y cumplimiento de compromisos."
    if S >= 70: return "Es clave desarrollar mayor asertividad y comodidad con el cambio y la toma de decisiones rápidas."
    return "Es clave aprender a tomar decisiones con información incompleta y a aceptar los errores como parte del proceso."


# =========================================================================
# CÁLCULOS VALANTI
# =========================================================================

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
# CÁLCULOS WPI
# =========================================================================

def calculate_wpi_results(responses, questions):
    """
    Calcula los resultados del WPI (Work Personality Index).
    
    Args:
        responses: Lista de respuestas (1-5) del candidato
        questions: Lista de preguntas con dimension y reverse flag
        
    Returns:
        tuple: (raw_scores, normalized_scores, percentages)
    """
    questions_per_dim = {}
    for q in questions:
        dim = q["dimension"]
        questions_per_dim[dim] = questions_per_dim.get(dim, 0) + 1
    
    raw_scores = {dim: 0 for dim in WPI_DIMENSIONS}
    
    for i, q in enumerate(questions):
        if i < len(responses) and responses[i] is not None:
            dim = q["dimension"]
            answer = responses[i]
            
            if q.get("reverse", False):
                answer = 6 - answer
            
            raw_scores[dim] += answer
    
    normalized_scores = {}
    for dim in WPI_DIMENSIONS:
        num_questions = questions_per_dim.get(dim, 8)
        min_possible = num_questions * 1
        max_possible = num_questions * 5
        raw = raw_scores[dim]
        
        if max_possible > min_possible:
            normalized = ((raw - min_possible) / (max_possible - min_possible)) * 100
        else:
            normalized = 50.0
        
        normalized_scores[dim] = round(max(0, min(normalized, 100)), 1)
    
    total = sum(normalized_scores.values())
    percentages = {}
    if total > 0:
        for dim in WPI_DIMENSIONS:
            percentages[dim] = round((normalized_scores[dim] / total) * 100, 1)
    else:
        for dim in WPI_DIMENSIONS:
            percentages[dim] = 16.67
    
    return raw_scores, normalized_scores, percentages


# =========================================================================
# CÁLCULOS ERI
# =========================================================================

def load_eri_questions():
    """Carga las preguntas del ERI desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_eri.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_eri_results(responses, questions):
    """
    Calcula los resultados del ERI (Evaluación de Riesgo e Integridad).
    Puntuaciones altas = BAJO riesgo, puntuaciones bajas = ALTO riesgo.
    """
    questions_per_dim = {}
    for q in questions:
        dim = q["dimension"]
        questions_per_dim[dim] = questions_per_dim.get(dim, 0) + 1
    
    raw_scores = {dim: 0 for dim in ERI_DIMENSIONS}
    validity_suspicious = 0
    validity_flags = []
    
    for i, q in enumerate(questions):
        if i < len(responses) and responses[i] is not None:
            dim = q["dimension"]
            answer = responses[i]
            
            if q.get("validity_check", False):
                if answer <= 2:
                    validity_suspicious += 1
                    validity_flags.append(f"Respuesta poco realista en pregunta {i+1}: '{q['question'][:60]}...'")
            
            if q.get("reverse", False):
                risk_score = answer
            else:
                risk_score = 6 - answer
            
            raw_scores[dim] += risk_score
    
    normalized_scores = {}
    for dim in ERI_DIMENSIONS:
        num_questions = questions_per_dim.get(dim, 10)
        min_possible = num_questions * 1
        max_possible = num_questions * 5
        raw = raw_scores[dim]
        
        if max_possible > min_possible:
            normalized = ((raw - min_possible) / (max_possible - min_possible)) * 100
        else:
            normalized = 50.0
        
        normalized_scores[dim] = round(max(0, min(normalized, 100)), 1)
    
    total = sum(normalized_scores.values())
    percentages = {}
    if total > 0:
        for dim in ERI_DIMENSIONS:
            percentages[dim] = round((normalized_scores[dim] / total) * 100, 1)
    else:
        for dim in ERI_DIMENSIONS:
            percentages[dim] = 16.67
    
    validity_score = ERI_VALIDITY_QUESTIONS_COUNT - validity_suspicious
    
    return raw_scores, normalized_scores, percentages, validity_score, validity_flags


# =========================================================================
# CÁLCULOS TALENT MAP
# =========================================================================

def load_talent_map_questions():
    """Carga las preguntas del Talent Map desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_talent_map.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_talent_map_results(responses, questions):
    """
    Calcula los resultados del Talent Map (Mapeo de Competencias).
    """
    questions_per_comp = {}
    for q in questions:
        comp = q["competency"]
        questions_per_comp[comp] = questions_per_comp.get(comp, 0) + 1
    
    raw_scores = {comp: 0 for comp in TALENT_MAP_COMPETENCIES}
    
    for i, q in enumerate(questions):
        if i < len(responses) and responses[i] is not None:
            comp = q["competency"]
            answer = responses[i]
            
            if q.get("reverse", False):
                score = 6 - answer
            else:
                score = answer
            
            raw_scores[comp] += score
    
    normalized_scores = {}
    for comp in TALENT_MAP_COMPETENCIES:
        num_questions = questions_per_comp.get(comp, 10)
        min_possible = num_questions * 1
        max_possible = num_questions * 5
        raw = raw_scores[comp]
        
        if max_possible > min_possible:
            normalized = ((raw - min_possible) / (max_possible - min_possible)) * 100
        else:
            normalized = 50.0
        
        normalized_scores[comp] = round(max(0, min(normalized, 100)), 1)
    
    total = sum(normalized_scores.values())
    percentages = {}
    if total > 0:
        for comp in TALENT_MAP_COMPETENCIES:
            percentages[comp] = round((normalized_scores[comp] / total) * 100, 1)
    else:
        for comp in TALENT_MAP_COMPETENCIES:
            percentages[comp] = 12.5
    
    return raw_scores, normalized_scores, percentages


# =========================================================================
# CÁLCULOS DESEMPEÑO
# =========================================================================

def calculate_desempeno_results(rendimiento_scores, potencial_scores, iniciativas=None):
    """
    Calcula resultados de evaluación de desempeño.
    """
    promedio_rendimiento = sum(rendimiento_scores.values()) / len(rendimiento_scores)
    promedio_potencial = sum(potencial_scores.values()) / len(potencial_scores)
    
    potencial_normalizado = (promedio_potencial / 3) * 5
    puntaje_global = (promedio_rendimiento * 0.6) + (potencial_normalizado * 0.4)
    
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
    
    fortalezas_rendimiento = []
    for obj_id, score in rendimiento_scores.items():
        if score >= 4:
            objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
            fortalezas_rendimiento.append({
                "titulo": objetivo["titulo"],
                "score": score,
                "label": DESEMPENO_ESCALA_RENDIMIENTO[score]["label"]
            })
    
    areas_mejora_rendimiento = []
    for obj_id, score in rendimiento_scores.items():
        if score <= 3:
            objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
            areas_mejora_rendimiento.append({
                "titulo": objetivo["titulo"],
                "score": score,
                "label": DESEMPENO_ESCALA_RENDIMIENTO[score]["label"]
            })
    
    fortalezas_potencial = []
    for dim_id, score in potencial_scores.items():
        if score >= 2:
            dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
            fortalezas_potencial.append({
                "nombre": dimension["nombre"],
                "score": score,
                "nivel": f"Nivel {score}"
            })
    
    areas_desarrollo_potencial = []
    for dim_id, score in potencial_scores.items():
        if score <= 1:
            dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
            areas_desarrollo_potencial.append({
                "nombre": dimension["nombre"],
                "score": score,
                "nivel": f"Nivel {score}"
            })
    
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
    
    if len(areas_mejora_rendimiento) > 0:
        recomendaciones.append(f"Áreas prioritarias de rendimiento: {', '.join([a['titulo'] for a in areas_mejora_rendimiento[:3]])}")
    
    if len(areas_desarrollo_potencial) > 0:
        recomendaciones.append(f"Dimensiones de potencial a desarrollar: {', '.join([a['nombre'] for a in areas_desarrollo_potencial])}")
    
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
# CÁLCULOS DESEMPEÑO LÍDERES (FO-GH-41)
# =========================================================================

def calculate_desempeno_lider_results(competencias_scores, rendimiento_scores, potencial_scores,
                                      nivel_cargo=None, iniciativas=None, competencias_catalog=None):
    """
    Calcula resultados de evaluación de desempeño para líderes.
    competencias_scores: {comp_id (1-7): nivel (1-6)}
    rendimiento_scores:  {obj_id (1-6): puntaje (1-5)}
    potencial_scores:    {dim_id (1-5): nivel (0-3)}
    nivel_cargo:         str (ej. "LIDER", "GERENTE") para comparar contra niveles requeridos
    """
    from constants import (
        COMPETENCIAS_ORGANIZACIONALES, COMPETENCIAS_NIVEL_REQUERIDO,
        DESEMPENO_LIDER_CLASIFICACION_COMP,
        DESEMPENO_OBJETIVOS, DESEMPENO_ESCALA_RENDIMIENTO,
        DESEMPENO_DIMENSIONES, DESEMPENO_CLASIFICACION,
    )
    competencias_catalog = competencias_catalog or COMPETENCIAS_ORGANIZACIONALES

    # --- Competencias ---
    promedio_competencias = sum(competencias_scores.values()) / len(competencias_scores) if competencias_scores else 0

    nivel_requerido_info = COMPETENCIAS_NIVEL_REQUERIDO.get(nivel_cargo.upper() if nivel_cargo else "", None)
    brechas_competencias = []
    fortalezas_competencias = []
    for comp in competencias_catalog:
        cid = comp["id"]
        score = competencias_scores.get(cid, 0)
        req = nivel_requerido_info["niveles"][cid - 1] if nivel_requerido_info else None
        brecha = score - req if req is not None else None
        item = {"nombre": comp["nombre"], "score": score, "requerido": req, "brecha": brecha}
        if brecha is not None and brecha < 0:
            brechas_competencias.append(item)
        elif score >= 4:
            fortalezas_competencias.append(item)

    # Clasificación de competencias
    clasificacion_comp = None
    for nivel, info in sorted(DESEMPENO_LIDER_CLASIFICACION_COMP.items(), key=lambda x: x[1]["min"], reverse=True):
        if promedio_competencias >= info["min"]:
            clasificacion_comp = {"nivel": nivel, **info}
            break

    # --- Rendimiento (igual que operativo) ---
    promedio_rendimiento = sum(rendimiento_scores.values()) / len(rendimiento_scores) if rendimiento_scores else 0
    fortalezas_rendimiento = []
    areas_mejora_rendimiento = []
    for obj_id, score in rendimiento_scores.items():
        objetivo = DESEMPENO_OBJETIVOS[obj_id - 1]
        item = {"titulo": objetivo["titulo"], "score": score, "label": DESEMPENO_ESCALA_RENDIMIENTO[score]["label"]}
        if score >= 4:
            fortalezas_rendimiento.append(item)
        elif score <= 2:
            areas_mejora_rendimiento.append(item)

    # --- Potencial (igual que operativo) ---
    promedio_potencial = sum(potencial_scores.values()) / len(potencial_scores) if potencial_scores else 0
    fortalezas_potencial = []
    areas_desarrollo_potencial = []
    for dim_id, score in potencial_scores.items():
        dimension = DESEMPENO_DIMENSIONES[dim_id - 1]
        item = {"nombre": dimension["nombre"], "score": score, "nivel": f"Nivel {score}"}
        if score >= 2:
            fortalezas_potencial.append(item)
        else:
            areas_desarrollo_potencial.append(item)

    # --- Puntaje Global (ponderado) ---
    potencial_normalizado = (promedio_potencial / 3) * 5
    comp_normalizado = (promedio_competencias / 6) * 5
    puntaje_global = (comp_normalizado * 0.35) + (promedio_rendimiento * 0.40) + (potencial_normalizado * 0.25)

    clasificacion = None
    for nivel, info in sorted(DESEMPENO_CLASIFICACION.items(), key=lambda x: x[1]["min"], reverse=True):
        if puntaje_global >= info["min"]:
            clasificacion = {"nivel": nivel, "label": info["label"], "color": info["color"],
                             "descripcion": info["descripcion"]}
            break

    recomendaciones = []
    if puntaje_global >= 4.5:
        recomendaciones.append("Líder con desempeño excepcional. Candidato para promociones o proyectos estratégicos.")
        recomendaciones.append("Puede actuar como mentor y multiplicador de cultura.")
    elif puntaje_global >= 3.5:
        recomendaciones.append("Líder con desempeño destacado. Fortalecer competencias estratégicas de mayor nivel.")
        recomendaciones.append("Identificar oportunidades de stretch assignments para maximizar su potencial.")
    elif puntaje_global >= 2.5:
        recomendaciones.append("Líder con desempeño satisfactorio. Definir plan de desarrollo en competencias con brecha.")
        recomendaciones.append("Establecer mentoring o coaching para las competencias con mayor gap.")
    else:
        recomendaciones.append("Requiere plan de mejoramiento inmediato con metas claras.")
        recomendaciones.append("Seguimiento mensual y evaluación de competencias en 90 días.")

    if brechas_competencias:
        nombres = ", ".join([b["nombre"] for b in brechas_competencias[:3]])
        recomendaciones.append(f"Competencias con brecha vs. nivel requerido: {nombres}.")

    requiere_iniciativas = promedio_rendimiento < 3 or promedio_potencial < 2

    return {
        "promedio_competencias": round(promedio_competencias, 2),
        "clasificacion_comp": clasificacion_comp,
        "fortalezas_competencias": fortalezas_competencias,
        "brechas_competencias": brechas_competencias,
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
        "iniciativas": iniciativas if iniciativas else [],
        "nivel_cargo": nivel_cargo,
    }


def calculate_desempeno_medios_results(competencias_scores, rendimiento_scores, potencial_scores,
                                       nivel_cargo=None, iniciativas=None):
    """Calcula resultados de Evaluación de Desempeño Medios (FO-GH-17)."""
    return calculate_desempeno_lider_results(
        competencias_scores=competencias_scores,
        rendimiento_scores=rendimiento_scores,
        potencial_scores=potencial_scores,
        nivel_cargo=nivel_cargo,
        iniciativas=iniciativas,
        competencias_catalog=DESEMPENO_MEDIOS_COMPETENCIAS,
    )


# =========================================================================
# CÁLCULOS PERÍODO DE PRUEBA (FO-GH-46)
# =========================================================================

def calculate_periodo_prueba_results(actuaciones_scores, calificaciones_scores,
                                     aprobo, llamados_atencion, conocimiento_adecuado,
                                     observaciones=""):
    """
    Calcula resultados de la Evaluación de Período de Prueba.
    actuaciones_scores:    {idx (0-17): valor (1-4)}  → Nunca=1, AlgunasVeces=2, CasiSiempre=3, Siempre=4
    calificaciones_scores: {idx (0-4):  valor (1-5)}  → Insuficiente=1 … Excelente=5
    aprobo:                bool
    llamados_atencion:     bool
    conocimiento_adecuado: bool
    """
    from constants import (
        PERIODO_PRUEBA_ACTUACIONES, PERIODO_PRUEBA_CALIFICACIONES,
        PERIODO_PRUEBA_ESCALA_ACTUACIONES, PERIODO_PRUEBA_ESCALA_CALIFICACIONES,
        PERIODO_PRUEBA_CLASIFICACION,
    )

    promedio_actuaciones = sum(actuaciones_scores.values()) / len(actuaciones_scores) if actuaciones_scores else 0
    promedio_calificaciones = sum(calificaciones_scores.values()) / len(calificaciones_scores) if calificaciones_scores else 0

    # Normalizar a escala 1-4 para combinar (calificaciones max=5 → proporcional a 4)
    cal_normalizado = (promedio_calificaciones / 5) * 4
    promedio_general = (promedio_actuaciones * 0.6) + (cal_normalizado * 0.4)

    # Clasificación
    clasificacion = None
    for nivel, info in sorted(PERIODO_PRUEBA_CLASIFICACION.items(), key=lambda x: x[1]["min"], reverse=True):
        if promedio_general >= info["min"]:
            clasificacion = {"nivel": nivel, "label": info["label"], "color": info["color"],
                             "descripcion": info["descripcion"]}
            break

    # Ítems destacados y con observación
    actuaciones_destacadas = [
        {"nombre": PERIODO_PRUEBA_ACTUACIONES[idx], "valor": v,
         "label": PERIODO_PRUEBA_ESCALA_ACTUACIONES[v]["label"]}
        for idx, v in actuaciones_scores.items() if v >= 3
    ]
    actuaciones_observacion = [
        {"nombre": PERIODO_PRUEBA_ACTUACIONES[idx], "valor": v,
         "label": PERIODO_PRUEBA_ESCALA_ACTUACIONES[v]["label"]}
        for idx, v in actuaciones_scores.items() if v <= 2
    ]
    calificaciones_detalle = [
        {"nombre": PERIODO_PRUEBA_CALIFICACIONES[idx], "valor": v,
         "label": PERIODO_PRUEBA_ESCALA_CALIFICACIONES[v]["label"],
         "color": PERIODO_PRUEBA_ESCALA_CALIFICACIONES[v]["color"]}
        for idx, v in calificaciones_scores.items()
    ]

    # Recomendaciones
    recomendaciones = []
    if aprobo:
        recomendaciones.append("El colaborador aprobó el período de prueba satisfactoriamente.")
        if promedio_general >= 3.5:
            recomendaciones.append("Desempeño sobresaliente. Integrar formalmente con plan de desarrollo.")
        elif promedio_general >= 2.8:
            recomendaciones.append("Buen inicio. Continuar con onboarding y acompañamiento durante los primeros meses.")
        else:
            recomendaciones.append("Aprobó con observaciones. Implementar plan de seguimiento en los próximos 60 días.")
    else:
        recomendaciones.append("El colaborador NO aprobó el período de prueba.")
        recomendaciones.append("Evaluar si aplica extensión del período o desvinculación.")
        recomendaciones.append("Documentar las razones específicas del no cumplimiento.")

    if llamados_atencion:
        recomendaciones.append("Se presentaron llamados de atención durante el período. Registrar en hoja de vida.")
    if not conocimiento_adecuado:
        recomendaciones.append("El conocimiento/capacidad no se adecua completamente al perfil del cargo. Considerar capacitación adicional.")
    if actuaciones_observacion:
        nombres = ", ".join([a["nombre"] for a in actuaciones_observacion[:3]])
        recomendaciones.append(f"Comportamientos a reforzar: {nombres}.")

    return {
        "promedio_actuaciones": round(promedio_actuaciones, 2),
        "promedio_calificaciones": round(promedio_calificaciones, 2),
        "promedio_general": round(promedio_general, 2),
        "clasificacion": clasificacion,
        "aprobo": aprobo,
        "llamados_atencion": llamados_atencion,
        "conocimiento_adecuado": conocimiento_adecuado,
        "observaciones": observaciones,
        "actuaciones_destacadas": actuaciones_destacadas,
        "actuaciones_observacion": actuaciones_observacion,
        "calificaciones_detalle": calificaciones_detalle,
        "recomendaciones": recomendaciones,
    }

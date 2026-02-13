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

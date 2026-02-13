"""
Funciones de análisis y gener ación de recomendaciones para todas las evaluaciones.
"""
from constants import *


# =========================================================================
# ANÁLISIS DISC
# =========================================================================

def analyze_disc_aptitude(normalized, relative):
    """Analiza los resultados DISC y genera recomendaciones, fortalezas, alertas."""
    
    sorted_styles = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_styles[0]
    secondary = sorted_styles[1]
    weakest = sorted_styles[-1]
    
    dominant_style = dominant[0]
    secondary_style = secondary[0]
    dominant_score = dominant[1]
    secondary_score = secondary[1]
    weakest_score = weakest[1]
    
    profile_key = dominant_style + secondary_style
    profile_info = DISC_PROFILE_RECOMMENDATIONS.get(profile_key, {})
    
    score_range = dominant_score - weakest_score
    balance_score = 100 - abs(50 - (sum(normalized.values()) / 4))
    differentiation = min(score_range * 1.5, 100)
    
    aptitude_score = round((differentiation * 0.6 + balance_score * 0.4))
    aptitude_score = max(0, min(100, aptitude_score))
    
    if aptitude_score >= 70:
        aptitude_level = "APTO"
        aptitude_color = "#10B981"
        aptitude_emoji = "✅"
        aptitude_desc = "Perfil DISC claramente definido. El candidato muestra un patrón conductual coherente y diferenciado."
    elif aptitude_score >= 45:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = "Perfil DISC con áreas que requieren atención. Se recomienda considerar las observaciones para el cargo."
    else:
        aptitude_level = "REQUIERE EVALUACIÓN ADICIONAL"
        aptitude_color = "#EF4444"
        aptitude_emoji = "🔴"
        aptitude_desc = "Perfil DISC poco diferenciado. Se sugiere complementar con entrevista por competencias u otra evaluación."
    
    dom_level = "high" if dominant_score >= 55 else "low"
    sec_level = "high" if secondary_score >= 55 else "low"
    
    fortalezas = DISC_RECOMMENDATIONS[dominant_style][dom_level]["fortalezas"]
    alertas = DISC_RECOMMENDATIONS[dominant_style][dom_level]["alertas"]
    recomendaciones = DISC_RECOMMENDATIONS[dominant_style][dom_level]["recomendaciones"]
    
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


# =========================================================================
# ANÁLISIS VALANTI
# =========================================================================

def analyze_valanti_aptitude(standard):
    """Analiza los resultados VALANTI y genera recomendaciones."""
    
    sorted_values = sorted(standard.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_values[0]
    weakest = sorted_values[-1]
    
    high_values = [v for v, s in standard.items() if s >= 55]
    low_values = [v for v, s in standard.items() if s < 40]
    critical_values = [v for v, s in standard.items() if s < 30]
    avg_score = sum(standard.values()) / len(standard)
    
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
    
    fortalezas = []
    for value, score in sorted_values:
        if score >= 55:
            desc = VALANTI_DESCRIPTIONS[value]
            fortalezas.append(f"{value} (T={score}): {desc['high']}")
    
    alertas = []
    for value, score in sorted_values:
        if score < 40:
            desc = VALANTI_DESCRIPTIONS[value]
            alertas.append(f"{value} (T={score}): {desc['low']}")
    
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
    
    recomendaciones = []
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
# ANÁLISIS WPI
# =========================================================================

def analyze_wpi_aptitude(normalized):
    """Analiza los resultados WPI y genera recomendaciones."""
    
    sorted_dims = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_dims[0]
    second_strongest = sorted_dims[1]
    weakest = sorted_dims[-1]
    
    high_dims = [d for d, s in normalized.items() if s >= 70]
    medium_dims = [d for d, s in normalized.items() if 45 <= s < 70]
    low_dims = [d for d, s in normalized.items() if s < 45]
    critical_dims = [d for d, s in normalized.items() if s < 30]
    
    avg_score = sum(normalized.values()) / len(normalized)
    
    aptitude_score = round(
        avg_score + 
        len(high_dims) * 5 -
        len(low_dims) * 10 -
        len(critical_dims) * 20
    )
    aptitude_score = max(0, min(100, aptitude_score))
    
    if len(critical_dims) > 0:
        aptitude_level = "NO RECOMENDADO"
        aptitude_color = "#EF4444"
        aptitude_emoji = "🔴"
        aptitude_desc = f"Deficiencias críticas en: {', '.join(critical_dims)}. Alto riesgo de bajo desempeño laboral."
    elif len(low_dims) >= 3:
        aptitude_level = "CONTRATACIÓN CON RESERVAS"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = f"Múltiples áreas de mejora ({', '.join(low_dims)}). Requiere supervisión cercana."
    elif len(low_dims) >= 1 and len(high_dims) >= 2:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = f"Buen potencial con fortalezas en {strongest[0]} y {second_strongest[0]}, pero requiere desarrollo."
    elif avg_score >= 60 and len(high_dims) >= 3:
        aptitude_level = "ALTAMENTE RECOMENDADO"
        aptitude_color = "#10B981"
        aptitude_emoji = "✅"
        aptitude_desc = f"Perfil laboral sobresaliente. Fortalezas destacadas en {', '.join(high_dims)}."
    elif avg_score >= 50:
        aptitude_level = "APTO"
        aptitude_color = "#10B981"
        aptitude_emoji = "✓"
        aptitude_desc = "Perfil laboral adecuado. Competencias en nivel esperado."
    else:
        aptitude_level = "APTO CON OBSERVACIONES"
        aptitude_color = "#F59E0B"
        aptitude_emoji = "⚠️"
        aptitude_desc = "Perfil laboral en nivel básico."
    
    fortalezas = []
    for dim, score in sorted_dims:
        if score >= 70:
            desc = WPI_DESCRIPTIONS[dim]
            fortalezas.append(f"**{dim}** ({int(score)}/100): {desc['high']}")
        elif score >= 60 and len(fortalezas) < 3:
            desc = WPI_DESCRIPTIONS[dim]
            fortalezas.append(f"**{dim}** ({int(score)}/100): {desc['medium']}")
    
    alertas = []
    for dim, score in sorted_dims:
        if score < 45:
            desc = WPI_DESCRIPTIONS[dim]
            alertas.append(f"⚠️ **{dim}** ({int(score)}/100): {desc['low']}")
    
    recomendaciones = []
    for dim, score in sorted_dims:
        if score >= 70:
            level = "high"
        elif score >= 45:
            level = "medium"
        else:
            level = "low"
        
        if score >= 70 or score < 50:
            recs = WPI_RECOMMENDATIONS[dim][level]
            recomendaciones.append(f"**{dim}:** {' | '.join(recs)}")
    
    ideal_para = []
    avoid_roles = []
    
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
# ANÁLISIS ERI
# =========================================================================

def analyze_eri_aptitude(normalized, validity_score, validity_flags):
    """Analiza los resultados ERI y genera recomendaciones de contratación."""
    
    test_valid = validity_score >= (ERI_VALIDITY_QUESTIONS_COUNT - ERI_VALIDITY_THRESHOLD)
    validity_warning = None
    
    if not test_valid:
        validity_warning = f"⚠️ TEST POCO CONFIABLE: {ERI_VALIDITY_QUESTIONS_COUNT - validity_score} respuestas sospechosas detectadas."
    
    sorted_dims = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
    safest = sorted_dims[0]
    riskiest = sorted_dims[-1]
    
    low_risk_dims = [d for d, s in normalized.items() if s >= ERI_RISK_THRESHOLDS["low_risk"]]
    medium_risk_dims = [d for d, s in normalized.items() if ERI_RISK_THRESHOLDS["medium_risk"] <= s < ERI_RISK_THRESHOLDS["low_risk"]]
    high_risk_dims = [d for d, s in normalized.items() if s < ERI_RISK_THRESHOLDS["medium_risk"]]
    critical_risk_dims = [d for d, s in normalized.items() if s < 25]
    
    avg_score = sum(normalized.values()) / len(normalized)
    
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
        risk_desc = f"Múltiples indicadores de riesgo significativo. Contratación NO recomendada."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["high_risk"]["decision"]
    elif len(high_risk_dims) >= 1 or len(medium_risk_dims) >= 3:
        risk_profile = "medium_risk"
        risk_level = "⚠️ RIESGO MODERADO"
        risk_color = "#F59E0B"
        risk_emoji = "⚠️"
        all_risk_dims = high_risk_dims + medium_risk_dims
        risk_desc = f"Señales de alerta en: {', '.join(all_risk_dims)}. Requiere evaluación adicional."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["medium_risk"]["decision"]
    elif avg_score >= 70:
        risk_profile = "low_risk"
        risk_level = "✅ BAJO RIESGO"
        risk_color = "#10B981"
        risk_emoji = "✅"
        risk_desc = f"Perfil de integridad sobresaliente. Sin indicadores significativos de riesgo."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["low_risk"]["decision"]
    else:
        risk_profile = "medium_risk"
        risk_level = "⚠️ RIESGO MODERADO"
        risk_color = "#F59E0B"
        risk_emoji = "⚠️"
        risk_desc = "Perfil dentro de parámetros aceptables con algunas áreas de atención."
        hiring_decision = ERI_HIRING_RECOMMENDATIONS["medium_risk"]["decision"]
    
    fortalezas = []
    for dim, score in sorted_dims:
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            desc = ERI_DESCRIPTIONS[dim]
            fortalezas.append(f"**{dim}** ({int(score)}/100 - Bajo Riesgo): {desc['low_risk']}")
    
    alertas = []
    if validity_warning:
        alertas.append(validity_warning)
    
    for dim, score in sorted_dims:
        desc = ERI_DESCRIPTIONS[dim]
        if score < ERI_RISK_THRESHOLDS["medium_risk"]:
            alertas.append(f"🚨 **{dim}** ({int(score)}/100 - ALTO RIESGO): {desc['high_risk']}")
        elif score < ERI_RISK_THRESHOLDS["low_risk"]:
            alertas.append(f"⚠️ **{dim}** ({int(score)}/100 - Riesgo Moderado): {desc['medium_risk']}")
    
    recomendaciones = []
    hiring_recommendations = ERI_HIRING_RECOMMENDATIONS[risk_profile]
    
    recomendaciones.append(f"**Decisión Recomendada:** {hiring_recommendations['decision']}")
    recomendaciones.append(f"**Resumen:** {hiring_recommendations['resumen']}")
    recomendaciones.append("**Acciones:**")
    for action in hiring_recommendations['acciones']:
        recomendaciones.append(f"  • {action}")
    
    recomendaciones.append("\n**Recomendaciones por Dimensión:**")
    for dim, score in sorted_dims:
        if score >= ERI_RISK_THRESHOLDS["low_risk"]:
            level = "low_risk"
        elif score >= ERI_RISK_THRESHOLDS["medium_risk"]:
            level = "medium_risk"
        else:
            level = "high_risk"
        
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


# =========================================================================
# ANÁLISIS TALENT MAP
# =========================================================================

def analyze_talent_map_match(normalized_scores, selected_job_profile=None):
    """Analiza los resultados de Talent Map y calcula match con perfil de puesto."""
    
    sorted_comps = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
    strongest = sorted_comps[0]
    weakest = sorted_comps[-1]
    
    high_comps = [(c, s) for c, s in normalized_scores.items() if s >= 75]
    medium_comps = [(c, s) for c, s in normalized_scores.items() if 50 <= s < 75]
    low_comps = [(c, s) for c, s in normalized_scores.items() if s < 50]
    
    avg_score = sum(normalized_scores.values()) / len(normalized_scores)
    
    fortalezas = []
    for comp, score in high_comps:
        desc = TALENT_MAP_DESCRIPTIONS[comp]
        fortalezas.append(f"**{comp}** ({int(score)}/100): {desc['high']}")
    
    areas_desarrollo = []
    for comp, score in low_comps:
        desc = TALENT_MAP_DESCRIPTIONS[comp]
        areas_desarrollo.append(f"**{comp}** ({int(score)}/100): {desc['low']}")
    
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
        
        total_gap = 0
        max_possible_gap = 0
        
        for comp in TALENT_MAP_COMPETENCIES:
            required = profile_comps.get(comp, 50)
            actual = normalized_scores.get(comp, 0)
            gap = required - actual
            
            max_possible_gap += required
            
            if gap > 15:
                match_gaps.append(f"**{comp}**: Requiere {int(required)}, tiene {int(actual)} (brecha de {int(gap)} puntos)")
            elif gap < -10:
                match_strengths.append(f"**{comp}**: Excede requisito ({int(actual)} vs {int(required)} requerido)")
            
            total_gap += abs(gap)
        
        avg_gap = total_gap / len(TALENT_MAP_COMPETENCIES)
        match_percentage = max(0, min(100, 100 - avg_gap))
        
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

"""
Script de demostración de los módulos refactorizados.
Muestra cómo usar las funciones de cálculo y análisis de forma independiente.
"""

# Importar módulos refactorizados
from constants import (
    WPI_DIMENSIONS, 
    ERI_DIMENSIONS, 
    TALENT_MAP_COMPETENCIES,
    TALENT_MAP_JOB_PROFILES
)
from calculations import (
    calculate_wpi_results,
    calculate_eri_results,
    load_eri_questions,
    calculate_talent_map_results,
    load_talent_map_questions,
    calculate_valanti_results,
    calculate_disc_results
)
from analysis import (
    analyze_wpi_aptitude,
    analyze_eri_aptitude,
    analyze_talent_map_match,
    analyze_valanti_aptitude,
    analyze_disc_aptitude
)
from utils import load_disc_questions, load_wpi_questions


def demo_wpi():
    """Demostración de evaluación WPI."""
    print("\n" + "="*60)
    print("📋 DEMO: Work Personality Index (WPI)")
    print("="*60)
    
    # Cargar preguntas
    questions = load_wpi_questions()
    print(f"✓ Cargadas {len(questions)} preguntas WPI")
    
    # Simular respuestas de un candidato (escala 1-5)
    # Este candidato responde en general positivamente (4-5)
    responses = [5, 4, 5, 4, 5, 4, 5, 4] * 6  # 48 respuestas
    print(f"✓ Candidato respondió {len(responses)} preguntas")
    
    # Calcular resultados
    raw, normalized, percentages = calculate_wpi_results(responses, questions)
    
    print("\n📊 Puntajes Normalizados (0-100):")
    for dim in WPI_DIMENSIONS:
        score = normalized[dim]
        bar = "█" * int(score / 5)
        print(f"  {dim:25s} [{score:5.1f}] {bar}")
    
    # Analizar aptitud
    analysis = analyze_wpi_aptitude(normalized)
    
    print(f"\n{analysis['aptitude_emoji']} RESULTADO: {analysis['aptitude_level']}")
    print(f"📈 Score de Aptitud: {analysis['aptitude_score']}/100")
    print(f"🎯 {analysis['aptitude_desc']}")
    
    print(f"\n💪 Fortalezas:")
    for fortaleza in analysis['fortalezas'][:3]:
        print(f"  ✓ {fortaleza}")
    
   if analysis['alertas']:
        print(f"\n⚠️  Alertas:")
        for alerta in analysis['alertas'][:2]:
            print(f"  ! {alerta}")
    
    if analysis['ideal_para']:
        print(f"\n✨ Ideal para:")
        for rol in analysis['ideal_para']:
            print(f"  • {rol}")


def demo_eri():
    """Demostración de evaluación ERI."""
    print("\n" + "="*60)
    print("🔒 DEMO: Evaluación de Riesgo e Integridad (ERI)")
    print("="*60)
    
    # Cargar preguntas
    questions = load_eri_questions()
    print(f"✓ Cargadas {len(questions)} preguntas ERI")
    
    # Simular respuestas de un candidato confiable (4-5 en la mayoría)
    # En ERI: 5 = bajo riesgo (positivo)
    responses = [4, 5, 4, 5, 4, 5] * 8  # 48 respuestas
    print(f"✓ Candidato respondió {len(responses)} preguntas")
    
    # Calcular resultados
    raw, normalized, percentages, validity_score, validity_flags = calculate_eri_results(responses, questions)
    
    print("\n📊 Puntajes de Riesgo (0-100, mayor = menor riesgo):")
    for dim in ERI_DIMENSIONS:
        score = normalized[dim]
        if score >= 66:
            emoji = "🟢"
            level = "BAJO RIESGO"
        elif score >= 41:
            emoji = "🟡"
            level = "MODERADO"
        else:
            emoji = "🔴"
            level = "ALTO RIESGO"
        bar = "█" * int(score / 5)
        print(f"  {emoji} {dim:25s} [{score:5.1f}] {level}")
    
    # Analizar aptitud
    analysis = analyze_eri_aptitude(normalized, validity_score, validity_flags)
    
    print(f"\n{analysis['risk_emoji']} {analysis['risk_level']}")
    print(f"📊 Score Promedio de Riesgo: {analysis['risk_score']:.1f}/100")
    print(f"✅ Test Válido: {'Sí' if analysis['test_valid'] else 'No'}")
    print(f"📋 {analysis['risk_desc']}")
    
    print(f"\n💼 Decisión de Contratación:")
    print(f"  {analysis['hiring_decision']}")
    
    if analysis['fortalezas']:
        print(f"\n💪 Fortalezas (Bajo Riesgo):")
        for fortaleza in analysis['fortalezas'][:3]:
            print(f"  ✓ {fortaleza}")
    
    if analysis['alertas']:
        print(f"\n⚠️  Alertas de Riesgo:")
        for alerta in analysis['alertas'][:2]:
            print(f"  ! {alerta}")


def demo_talent_map():
    """Demostración de evaluación Talent Map con match."""
    print("\n" + "="*60)
    print("🎯 DEMO: Talent Map - Mapeo de Competencias")
    print("="*60)
    
    # Cargar preguntas
    questions = load_talent_map_questions()
    print(f"✓ Cargadas {len(questions)} preguntas Talent Map")
    
    # Simular respuestas competentes (3-5)
    responses = [4, 5, 4, 3, 5, 4, 5, 4] * 8  # 64 respuestas
    print(f"✓ Candidato respondió {len(responses)} preguntas")
    
    # Calcular resultados
    raw, normalized, percentages = calculate_talent_map_results(responses, questions)
    
    print("\n📊 Competencias (0-100):")
    for comp in TALENT_MAP_COMPETENCIES:
        score = normalized[comp]
        bar = "█" * int(score / 5)
        print(f"  {comp:28s} [{score:5.1f}] {bar}")
    
    # Comparar con perfil de "Gerente de Ventas"
    job_profile = "Gerente de Ventas"
    analysis = analyze_talent_map_match(normalized, selected_job_profile=job_profile)
    
    print(f"\n🎯 Match con Perfil: {job_profile}")
    
    if analysis['match_analysis']:
        match = analysis['match_analysis']
        print(f"  {match['match_label']}")
        print(f"  Porcentaje de Match: {match['match_percentage']:.1f}%")
        print(f"  {match['match_desc']}")
        
        if match['match_strengths']:
            print(f"\n💪 Fortalezas vs Perfil:")
            for strength in match['match_strengths'][:3]:
                print(f"  ✓ {strength}")
        
        if match['match_gaps']:
            print(f"\n📚 Brechas de Desarrollo:")
            for gap in match['match_gaps'][:3]:
                print(f"  → {gap}")
    
    print(f"\n📈 Score Promedio General: {analysis['average_score']:.1f}/100")
    print(f"🌟 Competencia más fuerte: {analysis['strongest_competency']}")


def demo_valanti():
    """Demostración rápida de VALANTI."""
    print("\n" + "="*60)
    print("💎 DEMO: VALANTI - Valores Humanos")
    print("="*60)
    
    # Simular 30 respuestas (escala aproximada)
    responses = [25, 28, 22, 24, 27] * 6  # 30 respuestas
    print(f"✓ Candidato respondió {len(responses)} preguntas")
    
    # Calcular
    direct, standard = calculate_valanti_results(responses)
    
    print("\n📊 Puntajes Estandarizados (T-Score, media=50):")
    for valor, score in standard.items():
        bar = "█" * int(score / 3)
        color = "🟢" if score >= 55 else ("🟡" if score >= 45 else "🔴")
        print(f"  {color} {valor:15s} [T={score:3d}] {bar}")
    
    # Analizar
    analysis = analyze_valanti_aptitude(standard)
    
    print(f"\n{analysis['aptitude_emoji']} {analysis['aptitude_level']}")
    print(f"💡 {analysis['aptitude_desc']}")


def demo_disc():
    """Demostración rápida de DISC."""
    print("\n" + "="*60)
    print("🎭 DEMO: DISC - Perfil de Comportamiento")
    print("="*60)
    
    # Cargar preguntas
    questions = load_disc_questions()
    print(f"✓ Cargadas {len(questions)} preguntas DISC")
    
    # Simular respuestas (escala 1-5)
    # Este candidato es alto en D (dominancia) e I (influencia)
    answers = [4, 3, 5, 4, 3, 5, 4, 3] * 3  # 24 respuestas
    print(f"✓ Candidato respondió {len(answers)} preguntas")
    
    # Calcular
    raw, normalized, relative = calculate_disc_results(answers, questions)
    
    print("\n📊 Puntajes DISC Normalizados (0-100):")
    styles = ["D", "I", "S", "C"]
    for style in styles:
        score = normalized[style]
        bar = "█" * int(score / 5)
        print(f"  {style} - {score:5.1f} {bar}")
    
    # Analizar
    analysis = analyze_disc_aptitude(normalized, relative)
    
    print(f"\n{analysis['aptitude_emoji']} {analysis['aptitude_level']}")
    print(f"📈 Perfil: {analysis['profile_name']}")
    print(f"🎯 Estilo Dominante: {analysis['dominant_name']} ({analysis['dominant_score']:.1f})")
    print(f"🎯 Estilo Secundario: {analysis['secondary_name']} ({analysis['secondary_score']:.1f})")


def main():
    """Ejecuta todas las demostraciones."""
    print("\n" + "="*60)
    print("🚀 DEMOSTRACIÓN DE MÓDULOS REFACTORIZADOS")
    print("   Evaluaciones Psicométricas - Código Modular")
    print("="*60)
    
    # Ejecutar demos
    demo_wpi()
    demo_eri()
    demo_talent_map()
    demo_valanti()
    demo_disc()
    
    print("\n" + "="*60)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("="*60)
    print("\nLos módulos funcionan correctamente de forma independiente.")
    print("Puedes importarlos en tu código para crear APIs, scripts, o apps.")
    print("\nPara más información, consulta REFACTORIZACION.md")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import json
import base64
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


st.set_page_config(
    page_title="Cuestionario VALANTI 🧭",
    layout="wide",
    page_icon="🧭",
)

# Custom CSS
st.markdown(
    """
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        background-color: #1e40af;
        color: white;
        font-weight: bold;
    }
    .stProgress > div > div > div {
        background-color: #d3d3d3d3;
    }
    .valanti-header {
        text-align: center;
        color: #1e40af;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================================
# DATOS DEL CUESTIONARIO VALANTI
# =========================================================================

# Preguntas del cuestionario (30 pares de frases)
preguntas = [
    # Primera Parte - Preguntas 1-9 (Valores positivos)
    ["Muestro dedicación a las personas que amo", "Actúo con perseverancia"],
    ["Soy tolerante", "Prefiero actuar con ética"],
    ["Al pensar, utilizo mi intuición o 'sexto sentido'", "Me siento una persona digna"],
    ["Logro buena concentración mental", "Perdono todas las ofensas de cualquier persona"],
    ["Normalmente razono mucho", "Me destaco por el liderazgo en mis acciones"],
    ["Pienso con integridad", "Me coloco objetivos y metas en mi vida personal"],
    ["Soy una persona de iniciativa", "En mi trabajo normalmente soy curioso"],
    ["Doy amor", "Para pensar hago síntesis de las distintas ideas"],
    ["Me siento en calma", "Pienso con veracidad"],
    # Segunda Parte - Preguntas 10-30 (Antivalores)
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

# Mapeo de rasgos a preguntas (índices 1-based)
TRAITS = {
    "Verdad": [1, 7, 13, 19, 25],
    "Rectitud": [2, 8, 14, 20, 26],
    "Paz": [3, 9, 15, 21, 27],
    "Amor": [4, 10, 16, 22, 28],
    "No Violencia": [5, 11, 17, 23, 29],
}

# Promedios nacionales y desviaciones estándar para normalización
NATIONAL_AVERAGES = {
    "Verdad": 15.65,
    "Rectitud": 21.05,
    "Paz": 17.35,
    "Amor": 16.68,
    "No Violencia": 21.22,
}

STANDARD_DEVS = {
    "Verdad": 4.7,
    "Rectitud": 4.44,
    "Paz": 6.61,
    "Amor": 5.41,
    "No Violencia": 7.19,
}

# Colores para cada valor
VALUE_COLORS = {
    "Verdad": "#3B82F6",      # Azul
    "Rectitud": "#10B981",    # Verde
    "Paz": "#8B5CF6",         # Morado
    "Amor": "#EF4444",        # Rojo
    "No Violencia": "#F59E0B", # Amarillo/Oro
}

# Descripciones de los valores
VALUE_DESCRIPTIONS = {
    "Verdad": {
        "title": "🔍 Verdad",
        "description": "Representa la búsqueda del conocimiento, la curiosidad intelectual, la intuición y el pensamiento analítico. Las personas con alto puntaje en Verdad valoran la honestidad intelectual, la investigación y el aprendizaje continuo.",
        "high": "Tienes una fuerte inclinación hacia la búsqueda del conocimiento y la verdad. Valoras la honestidad intelectual, el razonamiento lógico y la curiosidad. Tiendes a analizar las situaciones con profundidad antes de actuar.",
        "low": "Podrías beneficiarte de desarrollar más tu pensamiento analítico y curiosidad intelectual. Considerar diferentes perspectivas antes de tomar decisiones te ayudará a crecer."
    },
    "Rectitud": {
        "title": "⚖️ Rectitud",
        "description": "Refleja la ética, la perseverancia, la disciplina y el sentido del deber. Las personas con alto puntaje en Rectitud actúan con integridad, establecen metas claras y se esfuerzan por cumplirlas.",
        "high": "Demuestras un fuerte compromiso con la ética y la integridad. Eres perseverante, te fijas metas ambiciosas y trabajas con disciplina para alcanzarlas. Los demás confían en tu rectitud moral.",
        "low": "Podrías fortalecer tu sentido de disciplina y compromiso ético. Establecer metas claras y trabajar consistentemente hacia ellas te ayudará a desarrollar esta dimensión."
    },
    "Paz": {
        "title": "☮️ Paz",
        "description": "Representa la calma interior, la tolerancia, la paciencia y la armonía. Las personas con alto puntaje en Paz buscan la tranquilidad, evitan el conflicto innecesario y promueven ambientes serenos.",
        "high": "Posees una notable capacidad para mantener la calma y la serenidad interior. Valoras la tolerancia y buscas la armonía en tus relaciones. Tu presencia tiene un efecto tranquilizador en los demás.",
        "low": "Podrías trabajar en desarrollar más paciencia y tolerancia. Practicar técnicas de mindfulness o meditación puede ayudarte a encontrar mayor paz interior."
    },
    "Amor": {
        "title": "❤️ Amor",
        "description": "Refleja la dedicación, el cariño, el perdón y la compasión hacia los demás. Las personas con alto puntaje en Amor demuestran empatía, generosidad y capacidad de perdonar.",
        "high": "Tienes una gran capacidad de amar y demostrar afecto. Eres empático, compasivo y tienes facilidad para perdonar. Tu generosidad emocional fortalece tus relaciones personales y profesionales.",
        "low": "Podrías beneficiarte de abrir más tu corazón hacia los demás. Practicar la empatía y el perdón te ayudará a construir relaciones más profundas y significativas."
    },
    "No Violencia": {
        "title": "🕊️ No Violencia",
        "description": "Representa el respeto por toda forma de vida, la no agresión, la cooperación y la consideración hacia los demás. Las personas con alto puntaje valoran la justicia social y rechazan cualquier forma de violencia.",
        "high": "Demuestras un profundo respeto por la vida y la dignidad de todos los seres. Rechazas la violencia en todas sus formas y promueves activamente la cooperación y la justicia social.",
        "low": "Podrías desarrollar mayor sensibilidad hacia el impacto de tus acciones en los demás. Practicar la consideración y el respeto por las diferencias enriquecerá tu perspectiva."
    }
}


# =========================================================================
# FUNCIONES
# =========================================================================

def calculate_scores(responses):
    """Calcula puntajes directos y estándar basados en las respuestas"""
    direct_scores = {trait: 0 for trait in TRAITS}
    
    for trait, question_indices in TRAITS.items():
        for q_idx in question_indices:
            if q_idx - 1 < len(responses):
                a_value = responses[q_idx - 1]
                if a_value is not None:
                    direct_scores[trait] += a_value
    
    # Calcular puntajes estándar (escala T: media 50, desviación 10)
    standard_scores = {}
    for trait in TRAITS:
        z = (direct_scores[trait] - NATIONAL_AVERAGES[trait]) / STANDARD_DEVS[trait]
        standard_scores[trait] = round(z * 10 + 50)
    
    return direct_scores, standard_scores


def get_interpretation(standard_scores):
    """Genera interpretación basada en puntajes estándar"""
    sorted_scores = sorted(standard_scores.items(), key=lambda x: x[1], reverse=True)
    highest = sorted_scores[0]
    lowest = sorted_scores[-1]
    
    interpretation = f"### Perfil de Valores\n\n"
    interpretation += f"Tu valor más prominente es **{highest[0]}** (puntaje estándar: {highest[1]}). "
    interpretation += f"Tu valor menos enfatizado es **{lowest[0]}** (puntaje estándar: {lowest[1]}).\n\n"
    
    for trait, score in sorted_scores:
        desc = VALUE_DESCRIPTIONS[trait]
        if score >= 55:
            interpretation += f"**{desc['title']}** (Puntaje: {score} - Alto)\n\n{desc['high']}\n\n"
        elif score <= 45:
            interpretation += f"**{desc['title']}** (Puntaje: {score} - Bajo)\n\n{desc['low']}\n\n"
        else:
            interpretation += f"**{desc['title']}** (Puntaje: {score} - Promedio)\n\n{desc['description']}\n\n"
    
    return interpretation


def create_radar_chart(standard_scores):
    """Crea gráfico radar de los puntajes estándar"""
    categories = list(standard_scores.keys())
    values = list(standard_scores.values())
    
    # Cerrar el polígono
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Dibujar el polígono
    ax.plot(angles, values, 'o-', linewidth=2, color='#1e40af', markersize=8)
    ax.fill(angles, values, alpha=0.25, color='#1e40af')
    
    # Configurar etiquetas
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold')
    
    # Configurar ejes
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 50, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '50', '60', '80', '100'], fontsize=8)
    
    # Línea de referencia en 50 (promedio)
    ref_values = [50] * (len(categories) + 1)
    ax.plot(angles, ref_values, '--', linewidth=1, color='gray', alpha=0.5, label='Promedio (50)')
    
    ax.grid(True, alpha=0.3)
    ax.spines['polar'].set_visible(False)
    ax.set_facecolor('#f0f2f6')
    
    plt.title("Perfil Valoral - Cuestionario VALANTI", fontsize=14, fontweight='bold', pad=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    return fig


def create_bar_chart(direct_scores, standard_scores):
    """Crea gráfico de barras comparando puntajes directos y estándar"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    categories = list(direct_scores.keys())
    bar_colors = [VALUE_COLORS[cat] for cat in categories]
    
    # Puntajes directos
    direct_vals = list(direct_scores.values())
    bars1 = ax1.bar(categories, direct_vals, color=bar_colors, alpha=0.8, edgecolor='white')
    ax1.set_title("Puntajes Directos", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Puntaje")
    for bar, val in zip(bars1, direct_vals):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                str(val), ha='center', va='bottom', fontweight='bold')
    ax1.set_ylim(0, max(direct_vals) * 1.2 if max(direct_vals) > 0 else 15)
    
    # Puntajes estándar
    standard_vals = list(standard_scores.values())
    bars2 = ax2.bar(categories, standard_vals, color=bar_colors, alpha=0.8, edgecolor='white')
    ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Promedio (50)')
    ax2.set_title("Puntajes Estándar (Escala T)", fontsize=14, fontweight='bold')
    ax2.set_ylabel("Puntaje T")
    for bar, val in zip(bars2, standard_vals):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.3,
                str(val), ha='center', va='bottom', fontweight='bold')
    ax2.set_ylim(0, max(standard_vals) * 1.2 if max(standard_vals) > 0 else 100)
    ax2.legend()
    
    plt.tight_layout()
    return fig


def create_pdf_report(form_data, responses, direct_scores, standard_scores, interpretation, radar_fig):
    """Genera reporte PDF con los resultados"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Estilo personalizado
    styles.add(ParagraphStyle(
        name='Justify',
        parent=styles['Normal'],
        alignment=4,
        spaceAfter=6,
    ))
    
    story = []
    
    # Título
    story.append(Paragraph("Cuestionario VALANTI - Hoja de Resultados", styles["Title"]))
    story.append(Spacer(1, 20))
    
    # Información personal
    personal_data = [
        ["Nombre:", form_data.get("name", ""), "Edad:", str(form_data.get("age", ""))],
        ["Sexo:", form_data.get("sex", ""), "Educación:", form_data.get("education", "")],
        ["Cargo:", form_data.get("position", ""), "", ""],
    ]
    
    table = Table(personal_data, colWidths=[80, 180, 80, 180])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Puntajes
    story.append(Paragraph("Puntajes por Valor", styles["Heading2"]))
    score_data = [["Valor", "Puntaje Directo", "Puntaje Estándar (T)"]]
    for trait in TRAITS:
        score_data.append([trait, str(direct_scores[trait]), str(standard_scores[trait])])
    
    score_table = Table(score_data, colWidths=[120, 120, 150])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))
    
    # Gráfico radar
    if radar_fig:
        img_buffer = BytesIO()
        radar_fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        img = Image(img_buffer, width=350, height=350)
        story.append(img)
        story.append(Spacer(1, 20))
    
    story.append(PageBreak())
    
    # Interpretación
    story.append(Paragraph("Interpretación de Resultados", styles["Heading2"]))
    story.append(Spacer(1, 10))
    
    # Limpiar markdown para el PDF
    clean_interpretation = interpretation.replace("###", "").replace("**", "").replace("🔍", "").replace("⚖️", "").replace("☮️", "").replace("❤️", "").replace("🕊️", "")
    for line in clean_interpretation.split("\n"):
        if line.strip():
            story.append(Paragraph(line.strip(), styles['Justify']))
            story.append(Spacer(1, 4))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================================
# INTERFAZ DE USUARIO
# =========================================================================

# Título
st.markdown(
    "<h1 style='text-align: center; color: #1e40af;'>Cuestionario VALANTI 🧭</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-style: italic;'>Evaluación de Valores y Antivalores - Descubre tu perfil valoral</p>",
    unsafe_allow_html=True,
)

# Inicializar estado
if "valanti_started" not in st.session_state:
    st.session_state.valanti_started = False

if "valanti_submitted" not in st.session_state:
    st.session_state.valanti_submitted = False

if "valanti_responses" not in st.session_state:
    st.session_state.valanti_responses = [None] * len(preguntas)

if "valanti_page" not in st.session_state:
    st.session_state.valanti_page = 0

if "valanti_form_data" not in st.session_state:
    st.session_state.valanti_form_data = {
        "name": "",
        "age": "",
        "sex": "",
        "education": "",
        "position": "",
    }


# ---- PANTALLA DE INICIO ----
if not st.session_state.valanti_started:
    # Forzar reinicio de estado
    st.session_state.valanti_submitted = False
    st.session_state.valanti_responses = [None] * len(preguntas)
    st.session_state.valanti_page = 1
    st.session_state.valanti_form_data = {
        "name": "",
        "age": "",
        "sex": "",
        "education": "",
        "position": "",
    }
    st.markdown("""
    ### Bienvenido al Cuestionario VALANTI
    
    El VALANTI es un instrumento psicométrico diseñado para evaluar la importancia que otorgas a cinco valores humanos fundamentales:
    
    - 🔍 **Verdad**: Búsqueda del conocimiento, honestidad intelectual
    - ⚖️ **Rectitud**: Ética, perseverancia, sentido del deber
    - ☮️ **Paz**: Calma interior, tolerancia, armonía
    - ❤️ **Amor**: Dedicación, compasión, perdón
    - 🕊️ **No Violencia**: Respeto por la vida, cooperación, justicia
    
    #### Instrucciones:
    
    **Primera Parte (Preguntas 1-9):**
    Para cada par de frases, distribuye **3 puntos** entre las dos opciones según la importancia que le das a cada una en tu vida personal.
    
    **Segunda Parte (Preguntas 10-30):**
    Para cada par de frases, distribuye **3 puntos** entre las dos opciones. El puntaje más alto será para la frase que indique lo **peor** según tu juicio.
    
    Las únicas combinaciones válidas son: **3-0, 0-3, 2-1, 1-2** (siempre deben sumar 3).
    
    ¡Haz clic en "Comenzar" para iniciar la evaluación!
    """)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("🚀 Comenzar"):
        st.session_state.valanti_started = True
        st.rerun()

# ---- FORMULARIO DE INFORMACIÓN PERSONAL ----
elif st.session_state.valanti_started and st.session_state.valanti_page == 0 and not st.session_state.valanti_submitted:
    st.markdown("### 📋 Información Personal")
    
    with st.form("personal_info"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nombre Completo", value=st.session_state.valanti_form_data.get("name", ""))
            age = st.number_input("Edad", min_value=15, max_value=100, value=25)
            sex = st.selectbox("Sexo", ["Masculino", "Femenino", "Otro"])
        with col2:
            education = st.text_input("Nivel Educativo", value=st.session_state.valanti_form_data.get("education", ""), placeholder="Ej: Secundaria, Universitario, etc.")
            position = st.text_input("Cargo Actual", value=st.session_state.valanti_form_data.get("position", ""), placeholder="Tu cargo")
        
        submit_personal = st.form_submit_button("Continuar al Cuestionario")
        
        if submit_personal:
            if not name.strip():
                st.warning("Por favor ingresa tu nombre.")
            else:
                st.session_state.valanti_form_data = {
                    "name": name,
                    "age": age,
                    "sex": sex,
                    "education": education,
                    "position": position,
                }
                st.session_state.valanti_page = 1
                st.rerun()

# ---- CUESTIONARIO ----
elif st.session_state.valanti_page >= 1 and not st.session_state.valanti_submitted:

    # Configuración de preguntas por página
    questions_per_page = 5
    total_questions = len(preguntas)
    current_q_start = (st.session_state.valanti_page - 1) * questions_per_page
    current_q_end = min(current_q_start + questions_per_page, total_questions)
    total_pages = math.ceil(total_questions / questions_per_page)

    # Progreso
    progress = current_q_end / total_questions
    st.progress(progress)
    st.markdown(f"**Preguntas {current_q_start + 1} - {current_q_end} de {total_questions}**")

    # Instrucciones según la parte
    if current_q_start < 9:
        st.info("**Primera Parte:** Distribuye 3 puntos entre las dos frases según la importancia que le das a cada una en tu vida personal.")
    else:
        st.warning("**Segunda Parte:** Distribuye 3 puntos entre las dos frases. El puntaje más alto será para la frase que indique **lo peor** según tu juicio.")

    # Callbacks de auto-completado: al cambiar A se calcula B y viceversa
    def make_callback_a(idx):
        def _cb():
            val = st.session_state.get(f"sel_a_{idx}", "--")
            if val != "--":
                st.session_state[f"sel_b_{idx}"] = 3 - int(val)
        return _cb

    def make_callback_b(idx):
        def _cb():
            val = st.session_state.get(f"sel_b_{idx}", "--")
            if val != "--":
                st.session_state[f"sel_a_{idx}"] = 3 - int(val)
        return _cb

    all_valid = True

    for i in range(current_q_start, current_q_end):
        par = preguntas[i]
        a_key = f"sel_a_{i}"
        b_key = f"sel_b_{i}"

        # Inicializar desde respuestas guardadas si la clave no existe todavía
        if a_key not in st.session_state:
            if st.session_state.valanti_responses[i] is not None:
                st.session_state[a_key] = st.session_state.valanti_responses[i]
                st.session_state[b_key] = 3 - st.session_state.valanti_responses[i]

        st.markdown("---")
        st.markdown(f"#### Pregunta {i + 1}")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**A)** {par[0]}")
        with col_b:
            st.markdown(f"**B)** {par[1]}")

        st.markdown("**Distribuye 3 puntos entre las dos opciones (la suma debe ser 3):**")

        col_sa, col_sb, col_icon = st.columns([3, 3, 1])
        with col_sa:
            st.selectbox(
                f"Puntos para A (P{i+1})",
                options=["--", 0, 1, 2, 3],
                key=a_key,
                on_change=make_callback_a(i),
            )
        with col_sb:
            st.selectbox(
                f"Puntos para B (P{i+1})",
                options=["--", 0, 1, 2, 3],
                key=b_key,
                on_change=make_callback_b(i),
            )

        a_val = st.session_state.get(a_key, "--")
        b_val = st.session_state.get(b_key, "--")

        with col_icon:
            st.markdown("<br>", unsafe_allow_html=True)
            if a_val != "--" and b_val != "--" and int(a_val) + int(b_val) == 3:
                st.success("✅")
            else:
                st.warning("⚠️")
                all_valid = False

    # Navegación
    st.markdown("---")
    col_prev, col_space, col_next = st.columns([1, 4, 1])

    with col_prev:
        if st.session_state.valanti_page > 1:
            if st.button("⬅️ Anterior"):
                for j in range(current_q_start, current_q_end):
                    a = st.session_state.get(f"sel_a_{j}", "--")
                    if a != "--":
                        st.session_state.valanti_responses[j] = int(a)
                st.session_state.valanti_page -= 1
                st.rerun()

    with col_next:
        btn_label = "✅ Calcular Resultados" if current_q_end >= total_questions else "Siguiente ➡️"
        if st.button(btn_label, disabled=not all_valid):
            # Guardar respuestas de la página actual
            for j in range(current_q_start, current_q_end):
                a = st.session_state.get(f"sel_a_{j}", "--")
                if a != "--":
                    st.session_state.valanti_responses[j] = int(a)

            if current_q_end >= total_questions:
                if None in st.session_state.valanti_responses:
                    st.warning("⚠️ Hay preguntas sin responder. Revisa las páginas anteriores.")
                else:
                    st.session_state.valanti_submitted = True
                    st.rerun()
            else:
                st.session_state.valanti_page += 1
                st.rerun()

# ---- RESULTADOS ----
elif st.session_state.valanti_submitted:
    
    # Calcular puntajes
    direct_scores, standard_scores = calculate_scores(st.session_state.valanti_responses)
    interpretation = get_interpretation(standard_scores)
    
    st.markdown("---")
    st.markdown("## 📊 Resultados del Cuestionario VALANTI")
    st.markdown(f"**Participante:** {st.session_state.valanti_form_data.get('name', 'N/A')}")
    
    # Puntajes en columnas
    st.markdown("### Puntajes por Valor")
    cols = st.columns(5)
    for idx, (trait, score) in enumerate(standard_scores.items()):
        with cols[idx]:
            st.metric(
                label=trait,
                value=f"{score}",
                delta=f"{'↑ Alto' if score >= 55 else '↓ Bajo' if score <= 45 else '= Promedio'}",
                delta_color="normal" if score >= 55 else ("inverse" if score <= 45 else "off")
            )
            st.caption(f"Directo: {direct_scores[trait]}")
    
    # Gráficos
    st.markdown("### Gráfico de Perfil Valoral")
    col_radar, col_bars = st.columns([1, 1])
    
    with col_radar:
        radar_fig = create_radar_chart(standard_scores)
        st.pyplot(radar_fig)
    
    with col_bars:
        bar_fig = create_bar_chart(direct_scores, standard_scores)
        st.pyplot(bar_fig)
    
    # Interpretación
    st.markdown("---")
    st.markdown(interpretation)
    
    # Tabla de referencia
    st.markdown("### 📋 Tabla de Referencia de Puntajes")
    st.markdown("""
    | Rango de Puntaje T | Clasificación |
    |:---:|:---:|
    | 70+ | Muy Alto |
    | 55 - 69 | Alto |
    | 45 - 54 | Promedio |
    | 30 - 44 | Bajo |
    | < 30 | Muy Bajo |
    """)
    
    # Descargas
    st.markdown("### 📥 Descargar Resultados")
    col_json, col_pdf = st.columns(2)
    
    with col_json:
        results_json = {
            "participante": st.session_state.valanti_form_data,
            "puntajes_directos": direct_scores,
            "puntajes_estandar": standard_scores,
        }
        json_str = json.dumps(results_json, indent=2, ensure_ascii=False)
        st.download_button(
            label="📄 Descargar JSON",
            data=json_str,
            file_name=f"valanti_{st.session_state.valanti_form_data.get('name', 'resultados').replace(' ', '_')}.json",
            mime="application/json",
        )
    
    with col_pdf:
        pdf_buffer = create_pdf_report(
            st.session_state.valanti_form_data,
            st.session_state.valanti_responses,
            direct_scores,
            standard_scores,
            interpretation,
            radar_fig
        )
        st.download_button(
            label="📑 Descargar PDF",
            data=pdf_buffer.getvalue(),
            file_name=f"valanti_{st.session_state.valanti_form_data.get('name', 'resultados').replace(' ', '_')}.pdf",
            mime="application/pdf",
        )
    
    # Reiniciar
    if st.button("🔄 Reiniciar Evaluación"):
        for key in list(st.session_state.keys()):
            if key.startswith("valanti"):
                del st.session_state[key]
        st.rerun()


# Footer
st.markdown(
    """
    ---
    <div style="text-align: center;">
        <strong>Cuestionario VALANTI</strong> | Evaluación de Valores y Antivalores
        <br><small>Basado en los cinco valores humanos: Verdad, Rectitud, Paz, Amor y No Violencia</small>
    </div>
    """,
    unsafe_allow_html=True,
)

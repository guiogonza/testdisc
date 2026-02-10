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
    angles = [7 * np.pi / 4, np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4]
    scaled = {s: v / 100 for s, v in normalized_score.items()}
    x = sum(scaled[s] * np.cos(angles[i]) for i, s in enumerate(categories))
    y = sum(scaled[s] * np.sin(angles[i]) for i, s in enumerate(categories))
    mag = np.sqrt(x**2 + y**2)
    ang = np.arctan2(y, x)

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 1.01)
    ax.plot(ang, mag, "o", markersize=24, color="#4CAF50", label="Estilo DISC")
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=14, fontweight="bold")
    for a in [0, np.pi / 2, np.pi, 3 * np.pi / 2]:
        ax.axvline(x=a, color="gray", linestyle="--", alpha=0.7)
    ax.set_yticklabels([])
    ax.grid(True, alpha=0.3)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor("#f0f2f6")
    plt.title("Perfil de Estilo DISC", fontsize=14, fontweight="bold", pad=20)
    return fig


def create_valanti_radar(standard_scores):
    cats = list(standard_scores.keys())
    vals = list(standard_scores.values()) + [list(standard_scores.values())[0]]
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False).tolist() + [0]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.plot(angles, vals, "o-", linewidth=2, color="#1e40af", markersize=8)
    ax.fill(angles, vals, alpha=0.25, color="#1e40af")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(cats, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 50, 60, 80])
    ref = [50] * (len(cats) + 1)
    ax.plot(angles, ref, "--", linewidth=1, color="gray", alpha=0.5, label="Promedio (50)")
    ax.grid(True, alpha=0.3)
    ax.spines["polar"].set_visible(False)
    ax.set_facecolor("#f0f2f6")
    plt.title("Perfil Valoral - VALANTI", fontsize=14, fontweight="bold", pad=20)
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    return fig


def create_valanti_bars(direct_scores, standard_scores):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    cats = list(direct_scores.keys())
    bar_colors = [VALANTI_COLORS[c] for c in cats]
    dv = list(direct_scores.values())
    bars1 = ax1.bar(cats, dv, color=bar_colors, alpha=0.8)
    ax1.set_title("Puntajes Directos", fontsize=13, fontweight="bold")
    for b, v in zip(bars1, dv):
        ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3, str(v), ha="center", fontweight="bold")
    ax1.set_ylim(0, max(dv) * 1.2 if max(dv) > 0 else 15)
    sv = list(standard_scores.values())
    bars2 = ax2.bar(cats, sv, color=bar_colors, alpha=0.8)
    ax2.axhline(y=50, color="gray", linestyle="--", alpha=0.5, label="Promedio (50)")
    ax2.set_title("Puntajes Estándar (Escala T)", fontsize=13, fontweight="bold")
    for b, v in zip(bars2, sv):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.3, str(v), ha="center", fontweight="bold")
    ax2.set_ylim(0, max(sv) * 1.2 if max(sv) > 0 else 100)
    ax2.legend()
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

def generate_disc_pdf(candidate, normalized, relative, fig, session_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=12))
    story = []
    story.append(Paragraph("Evaluación de Personalidad DISC - Reporte", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']} (Cédula: {candidate['cedula']})", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position','N/A')} | <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 16))
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
        story.append(Image(img_buf, width=300, height=300))
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_valanti_pdf(candidate, direct, standard, radar_fig, session_id):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Justify", alignment=4, leading=12))
    story = []
    story.append(Paragraph("Cuestionario VALANTI - Reporte de Resultados", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>ID Evaluación:</b> {session_id}", styles["Normal"]))
    story.append(Paragraph(f"<b>Candidato:</b> {candidate['name']} (Cédula: {candidate['cedula']})", styles["Normal"]))
    story.append(Paragraph(f"<b>Cargo:</b> {candidate.get('position','N/A')} | <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 16))
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
        story.append(Image(img_buf, width=320, height=320))
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
        c1, c2 = st.columns(2)
        with c1:
            filter_type = st.selectbox("Filtrar por tipo:", ["Todos", "disc", "valanti"], key="filter_type")
        with c2:
            filter_status = st.selectbox("Filtrar por estado:", ["Todos", "pending", "in_progress", "completed", "expired"], key="filter_status",
                                          format_func=lambda x: {"Todos": "Todos", "pending": "⏳ Pendiente", "in_progress": "▶️ En Progreso", "completed": "✅ Completado", "expired": "⏰ Expirado"}.get(x, x))

        ft = filter_type if filter_type != "Todos" else None
        fs = filter_status if filter_status != "Todos" else None
        sessions = db.get_all_sessions(test_type=ft, status=fs)

        if not sessions:
            st.info("No hay evaluaciones que coincidan con los filtros.")
        else:
            for sess in sessions:
                status_emoji = {"pending": "⏳", "in_progress": "▶️", "completed": "✅", "expired": "⏰"}.get(sess["status"], "❓")
                test_emoji = "🎯" if sess["test_type"] == "disc" else "🧭"

                with st.expander(f"{status_emoji} {test_emoji} {sess['test_type'].upper()} | {sess['candidate_name']} (CC: {sess['cedula']}) | ID: {sess['id']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Estado", sess["status"].upper())
                    c2.metric("Tiempo Límite", f"{sess['time_limit_minutes']} min")
                    c3.metric("Iniciado", sess.get("started_at", "N/A") or "N/A")
                    c4.metric("Completado", sess.get("completed_at", "N/A") or "N/A")

                    if sess["status"] == "completed":
                        results = db.get_results(sess["id"])
                        candidate = db.get_candidate_by_cedula(sess["cedula"])
                        if results:
                            if sess["test_type"] == "disc":
                                show_disc_results_admin(results, candidate, sess["id"])
                            else:
                                show_valanti_results_admin(results, candidate, sess["id"])
                        else:
                            st.warning("Resultados no disponibles.")

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
                            st.markdown(f"  - {emoji} {s['test_type'].upper()} (ID: {s['id']}) — Estado: {s['status']}")

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


def show_disc_results_admin(results, candidate, session_id):
    """Show DISC results in the admin panel."""
    normalized = results.get("normalized", {})
    relative = results.get("relative", {})

    cols = st.columns(4)
    for idx, style in enumerate("DISC"):
        with cols[idx]:
            st.metric(style, f"{normalized.get(style, 0):.1f}%", f"Rel: {relative.get(style, 0):.1f}%")

    fig = create_disc_plot(normalized)
    st.pyplot(fig)

    pdf = generate_disc_pdf(candidate, normalized, relative, fig, session_id)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📑 Descargar PDF", data=pdf.getvalue(), file_name=f"disc_{candidate['cedula']}.pdf", mime="application/pdf", key=f"pdf_disc_{session_id}")
    with c2:
        st.download_button("📄 Descargar JSON", data=json.dumps(results, indent=2, ensure_ascii=False), file_name=f"disc_{candidate['cedula']}.json", mime="application/json", key=f"json_disc_{session_id}")


def show_valanti_results_admin(results, candidate, session_id):
    """Show VALANTI results in the admin panel."""
    direct = results.get("direct", {})
    standard = results.get("standard", {})

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

    pdf = generate_valanti_pdf(candidate, direct, standard, radar_fig, session_id)
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

            if page < total - 1:
                btn = st.form_submit_button("Siguiente ➡️")
            else:
                btn = st.form_submit_button("✅ Finalizar Evaluación")

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

    if page > 0:
        if st.button("⬅️ Anterior"):
            st.session_state.disc_page -= 1
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
    questions_per_page = 3
    page = st.session_state.valanti_page
    q_start = page * questions_per_page
    q_end = min(q_start + questions_per_page, total)

    progress = q_start / total
    st.progress(progress)
    st.markdown(f"**Preguntas {q_start + 1} - {q_end} de {total}**")

    if q_start < 9:
        st.info("**Primera Parte:** Distribuye 3 puntos entre las dos frases. El puntaje más alto para la frase más importante para ti.")
    else:
        st.warning("**Segunda Parte:** Distribuye 3 puntos entre las dos frases. El puntaje más alto para lo que consideres **peor**.")

    with st.form(key=f"valanti_form_{page}"):
        page_responses = []
        for i in range(q_start, q_end):
            par = VALANTI_PREGUNTAS[i]
            st.markdown(f"---")
            st.markdown(f"#### Pregunta {i + 1}")
            ca, ci, cb = st.columns([4, 2, 4])
            with ca:
                st.markdown(f"**A)** {par[0]}")
            with ci:
                default_val = st.session_state.valanti_responses[i]
                a_val = st.selectbox(
                    f"Puntos A (P{i+1})",
                    options=["--", 0, 1, 2, 3],
                    index=0 if default_val is None else [0, 1, 2, 3, 4][[None, 0, 1, 2, 3].index(default_val)],
                    key=f"vq_{i}_a",
                )
            with cb:
                st.markdown(f"**B)** {par[1]}")
                if a_val != "--":
                    st.markdown(f"**Puntos B: {3 - int(a_val)}**")
            page_responses.append((i, a_val))

        is_last = q_end >= total
        btn_text = "✅ Finalizar Evaluación" if is_last else "Siguiente ➡️"
        submitted = st.form_submit_button(btn_text)

    if submitted:
        remaining = db.check_session_time(db.get_session_by_id(session["id"]))
        if remaining == -1:
            st.error("⏰ El tiempo ha expirado.")
            return

        all_valid = True
        for idx, (q_idx, a_val) in enumerate(page_responses):
            if a_val == "--":
                all_valid = False
                break
            st.session_state.valanti_responses[q_idx] = int(a_val)

        if not all_valid:
            st.warning("⚠️ Por favor responde todas las preguntas.")
        else:
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

    if page > 0:
        if st.button("⬅️ Anterior"):
            st.session_state.valanti_page -= 1
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

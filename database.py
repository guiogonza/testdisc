import sqlite3
import hashlib
import uuid
import os
import json
from datetime import datetime, timedelta

# Ruta de la base de datos - usa /app/data en Docker, directorio local en desarrollo
if os.path.exists('/app/data'):
    DB_PATH = "/app/data/evaluaciones_rh.db"
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluaciones_rh.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        );

        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            activa INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            sex TEXT,
            education TEXT,
            position TEXT,
            empresa_id INTEGER,
            regional TEXT,
            correo TEXT,
            jefe_inmediato TEXT,
            nivel_cargo TEXT,
            invitar TEXT DEFAULT 'SI',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        );

        CREATE TABLE IF NOT EXISTS test_sessions (
            id TEXT PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            test_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            time_limit_minutes INTEGER DEFAULT 30,
            questions_data TEXT,
            started_at TEXT,
            completed_at TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (created_by) REFERENCES admins(id)
        );

        CREATE TABLE IF NOT EXISTS test_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_index INTEGER NOT NULL,
            question_text TEXT,
            answer_value INTEGER,
            answer_b_value INTEGER,
            FOREIGN KEY (session_id) REFERENCES test_sessions(id)
        );

        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            results_json TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES test_sessions(id)
        );
    """)

    # Migrar: agregar columna role si no existe
    try:
        c.execute("ALTER TABLE admins ADD COLUMN role TEXT DEFAULT 'admin'")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

    # Migrar: agregar columnas de empresa a candidates
    for column_def in [
        "empresa_id INTEGER",
        "regional TEXT",
        "correo TEXT",
        "jefe_inmediato TEXT",
        "nivel_cargo TEXT",
        "invitar TEXT DEFAULT 'SI'"
    ]:
        try:
            c.execute(f"ALTER TABLE candidates ADD COLUMN {column_def}")
        except sqlite3.OperationalError:
            pass  # La columna ya existe

    # Default admin
    existing = c.execute("SELECT id FROM admins WHERE username = 'admin'").fetchone()
    if not existing:
        c.execute(
            "INSERT INTO admins (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "Administrador RH", "admin"),
        )

    # Superadmin
    existing_super = c.execute("SELECT id FROM admins WHERE username = 'superadmin'").fetchone()
    if not existing_super:
        c.execute(
            "INSERT INTO admins (username, password_hash, name, role) VALUES (?, ?, ?, ?)",
            ("superadmin", hash_password("admin123"), "Super Administrador", "superadmin"),
        )
    else:
        # Si ya existe, actualizar contraseña a admin123 por seguridad
        c.execute(
            "UPDATE admins SET password_hash = ? WHERE username = 'superadmin'",
            (hash_password("admin123"),)
        )

    conn.commit()
    conn.close()


# =========================================================================
# ADMIN OPERATIONS
# =========================================================================

def verify_admin(username, password):
    conn = get_connection()
    admin = conn.execute(
        "SELECT * FROM admins WHERE username = ? AND password_hash = ?",
        (username, hash_password(password)),
    ).fetchone()
    conn.close()
    return dict(admin) if admin else None


def change_admin_password(admin_id, new_password):
    conn = get_connection()
    conn.execute(
        "UPDATE admins SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), admin_id),
    )
    conn.commit()
    conn.close()


# =========================================================================
# CANDIDATE OPERATIONS
# =========================================================================

def create_candidate(cedula, name, age, sex, education, position):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO candidates (cedula, name, age, sex, education, position) VALUES (?, ?, ?, ?, ?, ?)",
            (cedula, name, age, sex, education, position),
        )
        conn.commit()
        candidate = conn.execute("SELECT * FROM candidates WHERE cedula = ?", (cedula,)).fetchone()
        conn.close()
        return dict(candidate)
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Duplicate cédula


def get_candidate_by_cedula(cedula):
    conn = get_connection()
    candidate = conn.execute("SELECT * FROM candidates WHERE cedula = ?", (cedula,)).fetchone()
    conn.close()
    return dict(candidate) if candidate else None


def get_all_candidates():
    conn = get_connection()
    candidates = conn.execute("SELECT * FROM candidates ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(c) for c in candidates]


def update_candidate(candidate_id, name, age, sex, education, position):
    conn = get_connection()
    conn.execute(
        "UPDATE candidates SET name=?, age=?, sex=?, education=?, position=? WHERE id=?",
        (name, age, sex, education, position, candidate_id),
    )
    conn.commit()
    conn.close()


# =========================================================================
# TEST SESSION OPERATIONS
# =========================================================================

def create_test_session(candidate_id, test_type, time_limit_minutes, created_by, questions_data=None):
    conn = get_connection()

    # Check if candidate already has an ACTIVE session for this test type (pending or in progress)
    # Allow new sessions if previous ones are completed
    existing = conn.execute(
        "SELECT id, status FROM test_sessions WHERE candidate_id = ? AND test_type = ? AND status IN ('pending', 'in_progress')",
        (candidate_id, test_type),
    ).fetchone()

    if existing:
        conn.close()
        return None, f"El candidato ya tiene una evaluación {test_type.upper()} activa con estado '{existing['status']}'. Complete o cancele la evaluación activa antes de crear una nueva."

    session_id = str(uuid.uuid4())[:8].upper()
    questions_json = json.dumps(questions_data, ensure_ascii=False) if questions_data else None

    conn.execute(
        "INSERT INTO test_sessions (id, candidate_id, test_type, status, time_limit_minutes, questions_data, created_by) VALUES (?, ?, ?, 'pending', ?, ?, ?)",
        (session_id, candidate_id, test_type, time_limit_minutes, questions_json, created_by),
    )
    conn.commit()
    conn.close()
    return session_id, None


def get_pending_sessions_for_candidate(candidate_id):
    conn = get_connection()
    sessions = conn.execute(
        "SELECT * FROM test_sessions WHERE candidate_id = ? AND status IN ('pending', 'in_progress') ORDER BY created_at",
        (candidate_id,),
    ).fetchall()
    conn.close()
    return [dict(s) for s in sessions]


def get_session_by_id(session_id):
    conn = get_connection()
    session = conn.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(session) if session else None


def start_test_session(session_id):
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE test_sessions SET status = 'in_progress', started_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def complete_test_session(session_id):
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE test_sessions SET status = 'completed', completed_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def expire_test_session(session_id):
    conn = get_connection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE test_sessions SET status = 'expired', completed_at = ? WHERE id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def update_session_questions(session_id, questions_data):
    conn = get_connection()
    conn.execute(
        "UPDATE test_sessions SET questions_data = ? WHERE id = ?",
        (json.dumps(questions_data, ensure_ascii=False), session_id),
    )
    conn.commit()
    conn.close()


def get_all_sessions(test_type=None, status=None):
    conn = get_connection()
    query = """
        SELECT ts.*, c.cedula, c.name as candidate_name 
        FROM test_sessions ts 
        JOIN candidates c ON ts.candidate_id = c.id
    """
    conditions = []
    params = []
    if test_type:
        conditions.append("ts.test_type = ?")
        params.append(test_type)
    if status:
        conditions.append("ts.status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY ts.created_at DESC"

    sessions = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(s) for s in sessions]


def check_session_time(session):
    """Check if a session has expired based on time limit. Returns remaining seconds or -1 if expired."""
    if session["status"] != "in_progress" or not session["started_at"]:
        return None

    started = datetime.strptime(session["started_at"], "%Y-%m-%d %H:%M:%S")
    deadline = started + timedelta(minutes=session["time_limit_minutes"])
    remaining = (deadline - datetime.now()).total_seconds()

    if remaining <= 0:
        expire_test_session(session["id"])
        return -1
    return remaining


def get_session_deadline_timestamp(session):
    """Return deadline as Unix timestamp for JS timer."""
    if not session["started_at"]:
        return None
    started = datetime.strptime(session["started_at"], "%Y-%m-%d %H:%M:%S")
    deadline = started + timedelta(minutes=session["time_limit_minutes"])
    return deadline.timestamp()


# =========================================================================
# ANSWERS & RESULTS
# =========================================================================

def save_answers(session_id, answers):
    """
    Save test answers.
    answers: list of dicts with keys: question_index, question_text, answer_value, answer_b_value (optional)
    """
    conn = get_connection()
    for a in answers:
        conn.execute(
            "INSERT INTO test_answers (session_id, question_index, question_text, answer_value, answer_b_value) VALUES (?, ?, ?, ?, ?)",
            (session_id, a["question_index"], a.get("question_text", ""), a["answer_value"], a.get("answer_b_value")),
        )
    conn.commit()
    conn.close()


def get_answers(session_id):
    conn = get_connection()
    answers = conn.execute(
        "SELECT * FROM test_answers WHERE session_id = ? ORDER BY question_index",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(a) for a in answers]


def save_results(session_id, results_dict):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO test_results (session_id, results_json) VALUES (?, ?)",
            (session_id, json.dumps(results_dict, ensure_ascii=False)),
        )
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE test_results SET results_json = ? WHERE session_id = ?",
            (json.dumps(results_dict, ensure_ascii=False), session_id),
        )
    conn.commit()
    conn.close()


def get_results(session_id):
    conn = get_connection()
    result = conn.execute(
        "SELECT results_json FROM test_results WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    conn.close()
    if result:
        return json.loads(result["results_json"])
    return None


def delete_test_session(session_id):
    """Delete a test session and all its related answers and results."""
    conn = get_connection()
    conn.execute("DELETE FROM test_answers WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM test_results WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM test_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def delete_candidate(candidate_id):
    """Delete a candidate and ALL related test sessions, answers, and results."""
    conn = get_connection()
    # Get all sessions for this candidate
    sessions = conn.execute(
        "SELECT id FROM test_sessions WHERE candidate_id = ?", (candidate_id,)
    ).fetchall()
    # Delete answers and results for each session
    for s in sessions:
        conn.execute("DELETE FROM test_answers WHERE session_id = ?", (s["id"],))
        conn.execute("DELETE FROM test_results WHERE session_id = ?", (s["id"],))
    # Delete all sessions for this candidate
    conn.execute("DELETE FROM test_sessions WHERE candidate_id = ?", (candidate_id,))
    # Delete the candidate
    conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()


# =========================================================================
# EMPRESA OPERATIONS
# =========================================================================

def create_empresa(codigo, nombre, activa=1):
    """Crear o actualizar una empresa."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO empresas (codigo, nombre, activa) VALUES (?, ?, ?)",
            (codigo, nombre, activa),
        )
        conn.commit()
        empresa = conn.execute("SELECT * FROM empresas WHERE codigo = ?", (codigo,)).fetchone()
        conn.close()
        return dict(empresa)
    except sqlite3.IntegrityError:
        # Ya existe, actualizar
        conn.execute(
            "UPDATE empresas SET nombre = ?, activa = ? WHERE codigo = ?",
            (nombre, activa, codigo),
        )
        conn.commit()
        empresa = conn.execute("SELECT * FROM empresas WHERE codigo = ?", (codigo,)).fetchone()
        conn.close()
        return dict(empresa)


def get_all_empresas():
    """Obtener todas las empresas."""
    conn = get_connection()
    empresas = conn.execute("SELECT * FROM empresas ORDER BY nombre").fetchall()
    conn.close()
    return [dict(e) for e in empresas]


def get_empresa_by_codigo(codigo):
    """Obtener empresa por código."""
    conn = get_connection()
    empresa = conn.execute("SELECT * FROM empresas WHERE codigo = ?", (codigo,)).fetchone()
    conn.close()
    return dict(empresa) if empresa else None


def get_empresa_by_id(empresa_id):
    """Obtener empresa por ID."""
    conn = get_connection()
    empresa = conn.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,)).fetchone()
    conn.close()
    return dict(empresa) if empresa else None


def create_empleado(cedula, name, empresa_codigo, regional, correo, position, 
                   jefe_inmediato, nivel_cargo, invitar="SI", age=None, sex=None, education=None):
    """Crear un empleado con todos los datos del Excel."""
    conn = get_connection()
    
    # Obtener empresa_id
    empresa = conn.execute("SELECT id FROM empresas WHERE codigo = ?", (empresa_codigo,)).fetchone()
    empresa_id = empresa["id"] if empresa else None
    
    try:
        conn.execute(
            """INSERT INTO candidates (cedula, name, age, sex, education, position, 
               empresa_id, regional, correo, jefe_inmediato, nivel_cargo, invitar) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cedula, name, age, sex, education, position, 
             empresa_id, regional, correo, jefe_inmediato, nivel_cargo, invitar),
        )
        conn.commit()
        empleado = conn.execute("SELECT * FROM candidates WHERE cedula = ?", (cedula,)).fetchone()
        conn.close()
        return dict(empleado)
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Duplicate cédula


def get_empleados_by_empresa(empresa_id=None):
    """Obtener empleados filtrados por empresa."""
    conn = get_connection()
    if empresa_id:
        empleados = conn.execute(
            """SELECT c.*, e.codigo as empresa_codigo, e.nombre as empresa_nombre 
               FROM candidates c 
               LEFT JOIN empresas e ON c.empresa_id = e.id 
               WHERE c.empresa_id = ? 
               ORDER BY c.name""",
            (empresa_id,)
        ).fetchall()
    else:
        empleados = conn.execute(
            """SELECT c.*, e.codigo as empresa_codigo, e.nombre as empresa_nombre 
               FROM candidates c 
               LEFT JOIN empresas e ON c.empresa_id = e.id 
               ORDER BY c.name"""
        ).fetchall()
    conn.close()
    return [dict(emp) for emp in empleados]


# Initialize DB on import
init_db()

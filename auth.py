"""
Autenticación y gestión de sesiones de administrador.
"""
import base64
import hmac
import hashlib
import os
from datetime import datetime, timedelta

import streamlit as st
import database as db

ADMIN_IDLE_TIMEOUT_MINUTES = 60
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "rh-evaluaciones-secret-key")


def _get_admin_token_from_query():
    """Lee el token admin desde query params (permite restaurar sesión tras refresh)."""
    try:
        return st.query_params.get("admin_token", None)
    except Exception:
        return None


def _set_admin_token_in_query(token):
    """Escribe o elimina el token admin en query params preservando los demás parámetros."""
    try:
        if token:
            st.query_params["admin_token"] = token
        else:
            st.query_params.pop("admin_token", None)
    except Exception:
        pass


def _create_admin_session_token(admin_id, expires_at=None):
    """Crea token firmado con expiración para restaurar sesión tras refresh."""
    if expires_at is None:
        expires_at = datetime.utcnow() + timedelta(minutes=ADMIN_IDLE_TIMEOUT_MINUTES)
    exp_ts = int(expires_at.timestamp())
    payload = f"{admin_id}:{exp_ts}"
    signature = hmac.new(ADMIN_SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    raw = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _parse_admin_session_token(token):
    """Valida token firmado y devuelve admin_id si está vigente; si no, None."""
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        admin_id_str, exp_ts_str, signature = raw.split(":", 2)
        payload = f"{admin_id_str}:{exp_ts_str}"
        expected_sig = hmac.new(
            ADMIN_SESSION_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        if datetime.utcnow().timestamp() > int(exp_ts_str):
            return None
        return int(admin_id_str)
    except Exception:
        return None


def _get_admin_by_id(admin_id):
    """Obtiene admin por ID para restaurar sesión desde token."""
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM admins WHERE id = ?", (admin_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _start_admin_session(admin):
    """Inicia sesión admin con token de 60 minutos renovable por actividad."""
    token = _create_admin_session_token(admin["id"])
    st.session_state["admin"] = admin
    st.session_state["admin_session_token"] = token
    st.session_state["admin_last_seen_at"] = datetime.utcnow().isoformat()
    _set_admin_token_in_query(token)


def _touch_admin_session():
    """Renueva ventana de inactividad cuando hay uso de la app."""
    admin = st.session_state.get("admin")
    if not admin:
        return

    token = _create_admin_session_token(admin["id"])
    st.session_state["admin_session_token"] = token
    st.session_state["admin_last_seen_at"] = datetime.utcnow().isoformat()
    _set_admin_token_in_query(token)


def _restore_admin_session():
    """Restaura admin desde token en URL si la sesión aún no expiró."""
    if st.session_state.get("admin"):
        if not st.session_state.get("admin_session_token"):
            _start_admin_session(st.session_state["admin"])
        else:
            _touch_admin_session()
        return

    token = _get_admin_token_from_query()
    if not token:
        return

    admin_id = _parse_admin_session_token(token)
    if not admin_id:
        _set_admin_token_in_query(None)
        return

    admin = _get_admin_by_id(admin_id)
    if not admin:
        _set_admin_token_in_query(None)
        return

    st.session_state["admin"] = admin
    st.session_state["admin_session_token"] = token
    _touch_admin_session()


def _logout_admin():
    """Cierra sesión admin local y elimina token persistido."""
    st.session_state.pop("admin", None)
    st.session_state.pop("admin_session_token", None)
    st.session_state.pop("admin_last_seen_at", None)
    _set_admin_token_in_query(None)

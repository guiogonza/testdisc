"""
Autenticación y gestión de sesiones de administrador.
"""
import base64
import hmac
import hashlib
import os
import json
import secrets
from datetime import datetime, timedelta

import streamlit as st
import database as db

ADMIN_IDLE_TIMEOUT_MINUTES = 60
ADMIN_SESSION_SECRET = os.getenv("ADMIN_SESSION_SECRET", "rh-evaluaciones-secret-key")
RESULT_LINK_SECRET = os.getenv("RESULT_LINK_SECRET", ADMIN_SESSION_SECRET)


def _get_admin_token_from_query():
    """Lee el token admin desde query params (permite restaurar sesión tras refresh)."""
    try:
        return st.query_params.get("admin_token", None)
    except Exception:
        return None


def _set_admin_token_in_query(token):
    """Elimina el token admin de la URL; la sesión admin vive en session_state."""
    try:
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
    """Inicia sesión admin con token interno de 60 minutos renovable por actividad."""
    token = _create_admin_session_token(admin["id"])
    st.session_state["admin"] = admin
    st.session_state["admin_session_token"] = token
    st.session_state["admin_last_seen_at"] = datetime.utcnow().isoformat()
    _set_admin_token_in_query(token)


def _touch_admin_session():
    """Renueva ventana de inactividad cuando hay uso de la app sin exponer token en URL."""
    admin = st.session_state.get("admin")
    if not admin:
        return

    token = _create_admin_session_token(admin["id"])
    st.session_state["admin_session_token"] = token
    st.session_state["admin_last_seen_at"] = datetime.utcnow().isoformat()
    _set_admin_token_in_query(token)


def _restore_admin_session():
    """Restaura admin desde session_state; acepta tokens antiguos en URL y los limpia."""
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


def _derive_keystream(secret, nonce, length):
    """Deriva flujo de bytes pseudoaleatorio para cifrado reversible liviano."""
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hashlib.sha256(f"{secret}:{nonce}:{counter}".encode("utf-8")).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def _xor_bytes(data, key_stream):
    return bytes(a ^ b for a, b in zip(data, key_stream))


def _create_result_view_token(session_id, test_type, expires_minutes=1440):
    """Crea token firmado y cifrado para visualizar resultados por URL."""
    exp_ts = int((datetime.utcnow() + timedelta(minutes=expires_minutes)).timestamp())
    payload = {
        "sid": str(session_id),
        "tt": str(test_type),
        "exp": exp_ts,
        "jti": secrets.token_hex(8),
    }
    payload_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    nonce = secrets.token_hex(8)
    key_stream = _derive_keystream(RESULT_LINK_SECRET, nonce, len(payload_raw))
    cipher_raw = _xor_bytes(payload_raw, key_stream)

    nonce_b64 = base64.urlsafe_b64encode(nonce.encode("utf-8")).decode("utf-8")
    cipher_b64 = base64.urlsafe_b64encode(cipher_raw).decode("utf-8")
    body = f"{nonce_b64}.{cipher_b64}"
    sig = hmac.new(
        RESULT_LINK_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{sig}"


def _parse_result_view_token(token):
    """Valida y descifra token de visualización. Retorna dict o None."""
    try:
        nonce_b64, cipher_b64, sig = token.split(".", 2)
        body = f"{nonce_b64}.{cipher_b64}"
        expected_sig = hmac.new(
            RESULT_LINK_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        nonce = base64.urlsafe_b64decode(nonce_b64.encode("utf-8")).decode("utf-8")
        cipher_raw = base64.urlsafe_b64decode(cipher_b64.encode("utf-8"))
        key_stream = _derive_keystream(RESULT_LINK_SECRET, nonce, len(cipher_raw))
        payload_raw = _xor_bytes(cipher_raw, key_stream)
        payload = json.loads(payload_raw.decode("utf-8"))

        if datetime.utcnow().timestamp() > int(payload.get("exp", 0)):
            return None
        if not payload.get("sid") or not payload.get("tt"):
            return None
        return {
            "session_id": payload["sid"],
            "test_type": payload["tt"],
            "expires_at": int(payload["exp"]),
        }
    except Exception:
        return None

"""
Funciones auxiliares y utilidades compartidas.
"""
import os
import json


def load_disc_questions():
    """Carga las preguntas DISC desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_es.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def load_disc_descriptions():
    """Carga las descripciones DISC desde el archivo JSON."""
    dfile = os.path.join(os.path.dirname(__file__), "disc_descriptions_es.json")
    with open(dfile, "r", encoding="utf-8") as f:
        return json.load(f)


def load_wpi_questions():
    """Carga las preguntas del WPI desde el archivo JSON."""
    qfile = os.path.join(os.path.dirname(__file__), "questions_wpi.json")
    with open(qfile, "r", encoding="utf-8") as f:
        return json.load(f)


def nav(page):
    """Navega a una página específica."""
    import streamlit as st
    st.session_state["page"] = page
    st.rerun()

"""Récords personales."""
import streamlit as st

from modules import repo
from modules.config import fmt_fecha
from modules.ui import tabla


def render():
    st.title("🏆 Récords personales")
    rec = repo.prs_recientes()
    if not rec.empty:
        st.subheader("🎉 Récords rotos en los últimos 60 días")
        tabla(rec[["fecha", "ejercicio", "peso_kg", "reps", "e1rm_kg"]].rename(columns={
            "fecha": "Fecha", "ejercicio": "Ejercicio", "peso_kg": "Peso (kg)", "reps": "Reps", "e1rm_kg": "1RM est."}))
    df = repo.prs()
    if df.empty:
        st.info("Aún no hay récords.")
        return
    c = st.columns(2)
    cat = c[0].selectbox("Grupo", ["Todos"] + sorted(df.categoria.unique()))
    q = c[1].text_input("Buscar", placeholder="press, curl…")
    if cat != "Todos":
        df = df[df.categoria == cat]
    if q:
        df = df[df.ejercicio.str.contains(q, case=False, na=False)]
    st.subheader("Mejor marca por ejercicio")
    tabla(df[["ejercicio", "categoria", "peso_kg", "reps", "e1rm_kg", "fecha"]].rename(columns={
        "ejercicio": "Ejercicio", "categoria": "Grupo", "peso_kg": "Peso (kg)", "reps": "Reps",
        "e1rm_kg": "1RM est. (kg)", "fecha": "Fecha"}))

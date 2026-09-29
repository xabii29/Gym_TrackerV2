"""Panel general: semana actual vs anterior, volumen por grupo muscular, últimas sesiones."""
from datetime import timedelta

import altair as alt
import pandas as pd
import streamlit as st

from modules import repo
from modules.config import fmt_fecha, hoy
from modules.temas import get_tema
from modules.ui import tabla


def _delta(a, b):
    return None if not b else f"{(a - b) / b:+.0%}"


def render():
    st.title("📈 Resumen")
    activa = repo.sesion_activa()
    if activa is not None:
        st.info(f"🟢 Hay una sesión en curso ({fmt_fecha(activa.fecha)}). Ve a **Entrenar** para continuarla.")
    h = hoy()
    lunes = h - timedelta(days=h.weekday())
    ses = repo.sesiones_resumen(lunes - timedelta(days=7), h)
    ses["fecha"] = pd.to_datetime(ses["fecha"]).dt.date
    esta, previa = ses[ses.fecha >= lunes], ses[ses.fecha < lunes]

    c = st.columns(3)
    c[0].metric("Sesiones esta semana", len(esta), None if previa.empty else len(esta) - len(previa))
    c[1].metric("Series", int(esta.n_series.sum()), _delta(esta.n_series.sum(), previa.n_series.sum()))
    c[2].metric("Volumen (kg)", f"{esta.volumen_kg.sum():,.0f}", _delta(esta.volumen_kg.sum(), previa.volumen_kg.sum()))
    st.caption("Comparado contra la semana anterior completa.")

    vol = repo.volumen_semanal(h - timedelta(weeks=8))
    st.subheader("Volumen semanal por grupo")
    if vol.empty:
        st.caption("Aún no hay datos suficientes.")
    else:
        vol["semana"] = pd.to_datetime(vol["semana"])
        st.altair_chart(alt.Chart(vol).mark_bar().encode(
            x=alt.X("yearmonthdate(semana):T", title="Semana"), y=alt.Y("volumen:Q", title="Volumen (kg)"),
            color=alt.Color("categoria:N", title="Grupo"),
            tooltip=["semana:T", "categoria", "volumen", "series"]).properties(height=280),
            width="stretch")
        ult4 = vol[vol.semana >= pd.Timestamp(h - timedelta(weeks=4))]
        frec = ult4.groupby("categoria").agg(series=("series", "sum"), dias=("dias", "sum")).reset_index()
        st.subheader("Frecuencia (últimas 4 semanas)")
        tabla(frec.rename(columns={"categoria": "Grupo", "series": "Series", "dias": "Días entrenados"})
              .sort_values("Series", ascending=False))

    st.subheader("Últimas sesiones")
    ult = repo.sesiones_resumen().head(5)
    if ult.empty:
        st.caption("Todavía no hay sesiones terminadas.")
    else:
        tabla(ult[["fecha", "plantilla", "n_ejercicios", "n_series", "volumen_kg", "notas"]].rename(columns={
            "fecha": "Fecha", "plantilla": "Plantilla", "n_ejercicios": "Ejercicios", "n_series": "Series",
            "volumen_kg": "Volumen (kg)", "notas": "Notas"}))

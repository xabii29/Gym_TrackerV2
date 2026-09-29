"""Progreso por ejercicio: peso máx, 1RM estimado, volumen, reps."""
from datetime import timedelta

import altair as alt
import pandas as pd
import streamlit as st

from modules import repo
from modules.config import hoy
from modules.temas import get_tema
from modules.ui import tabla

METRICAS = {"Peso máximo (kg)": "peso_max", "1RM estimado (kg)": "e1rm",
            "Volumen (kg)": "volumen", "Reps máximas": "reps_max"}
RANGOS = {"30 días": 30, "90 días": 90, "6 meses": 182, "1 año": 365, "Todo": None}


def render():
    st.title("📊 Progreso")
    lista = repo.ejercicios_con_datos()
    if lista.empty:
        st.info("Aún no hay entrenamientos terminados.")
        return
    eid = st.selectbox("Ejercicio", list(lista.id), format_func=dict(zip(lista.id, lista.nombre)).get)
    c = st.columns(2)
    metrica = c[0].selectbox("Métrica", list(METRICAS))
    rango = c[1].selectbox("Periodo", list(RANGOS), index=1)
    df = repo.progreso_ejercicio(eid)
    df["fecha"] = pd.to_datetime(df["fecha"])
    if METRICAS[metrica] in ("peso_max", "e1rm") and df.peso_max.max() == 0:
        st.caption("Este ejercicio no usa peso (peso corporal): se muestran las repeticiones.")
        metrica = "Reps máximas"
    dias = RANGOS[rango]
    corte = pd.Timestamp(hoy() - timedelta(days=dias)) if dias else df.fecha.min()
    actual = df[df.fecha >= corte]
    col = METRICAS[metrica]
    if actual.empty:
        st.warning("No hay sesiones en ese periodo.")
        return

    if dias:  # comparativo contra el periodo anterior de la misma duración
        previo = df[(df.fecha < corte) & (df.fecha >= corte - timedelta(days=dias))]
        m = st.columns(3)
        mejor = actual[col].max()
        m[0].metric("Mejor del periodo", f"{mejor:g}", None if previo.empty else f"{mejor - previo[col].max():+g} vs anterior")
        m[1].metric("Sesiones", len(actual), None if previo.empty else len(actual) - len(previo))
        m[2].metric("Volumen total (kg)", f"{actual.volumen.sum():,.0f}")

    graf = alt.Chart(actual).mark_line(point=True, color=get_tema()["primario"]).encode(
        x=alt.X("fecha:T", title="Fecha"), y=alt.Y(f"{col}:Q", title=metrica, scale=alt.Scale(zero=False)),
        tooltip=["fecha:T", alt.Tooltip(f"{col}:Q", title=metrica), "series", "notas"])
    st.altair_chart(graf.properties(height=320), width="stretch")

    st.subheader("Historial de récords de este ejercicio")
    prs = repo.pr_historial(eid)
    tabla(prs.rename(columns={"fecha": "Fecha", "peso_kg": "Peso (kg)", "reps": "Reps", "e1rm_kg": "1RM est. (kg)"}))
    st.subheader("Sesiones")
    tabla(actual.sort_values("fecha", ascending=False)[["fecha", "peso_max", "reps_max", "series", "volumen", "notas"]]
          .assign(fecha=lambda d: d.fecha.dt.date)
          .rename(columns={"fecha": "Fecha", "peso_max": "Peso máx", "reps_max": "Reps máx", "series": "Series",
                           "volumen": "Volumen", "notas": "Notas de la sesión"}))

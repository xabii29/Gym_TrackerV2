"""Calculadora de calorías y macros (Mifflin-St Jeor) con peso corporal guardado."""
import altair as alt
import pandas as pd
import streamlit as st

from modules import repo
from modules.auth import es_editor
from modules.config import hoy
from modules.temas import get_tema

ACTIVIDAD = {"Sedentario (oficina / poco ejercicio)": 1.2, "Ligero (1-3 días/sem)": 1.375,
             "Moderado (3-5 días/sem)": 1.55, "Fuerte (6-7 días/sem)": 1.725,
             "Atleta (2 turnos diarios)": 1.9}


def render():
    st.title("🔥 Calorías y peso corporal")
    pesos = repo.pesos_corporales()
    ultimo = float(pesos.peso_kg.iloc[-1]) if not pesos.empty else 75.0

    st.subheader("⚖️ Peso corporal")
    if es_editor():
        c = st.columns([2, 2, 1])
        fecha = c[0].date_input("Fecha", hoy(), max_value=hoy(), key="pc_fecha")
        kg = c[1].number_input("Peso (kg)", 30.0, 250.0, ultimo, 0.1, key="pc_kg")
        if c[2].button("Guardar", type="primary"):
            repo.guardar_peso(fecha, kg)
            st.rerun()
    if len(pesos) >= 2:
        pesos["fecha"] = pd.to_datetime(pesos["fecha"])
        st.altair_chart(alt.Chart(pesos).mark_line(point=True, color=get_tema()["primario"]).encode(
            x="fecha:T", y=alt.Y("peso_kg:Q", scale=alt.Scale(zero=False), title="kg")).properties(height=220),
            width="stretch")
    elif pesos.empty:
        st.caption("Aún no hay pesos registrados.")

    st.divider()
    st.subheader("Calculadora")
    c1, c2 = st.columns(2)
    sexo = c1.radio("Sexo", ["Hombre", "Mujer"], horizontal=True)
    edad = c1.number_input("Edad (años)", 15, 80, 25)
    peso = c1.number_input("Peso (kg)", 40.0, 180.0, min(max(ultimo, 40.0), 180.0), 0.5, key="calc_peso")
    estatura = c2.number_input("Estatura (cm)", 120, 220, 175)
    actividad = c2.selectbox("Nivel de actividad", list(ACTIVIDAD), index=2)
    objetivo = c2.selectbox("Objetivo", ["Déficit (-20%)", "Mantenimiento", "Volumen (+15%)"], index=1)

    bmr = 10 * peso + 6.25 * estatura - 5 * edad + (5 if sexo == "Hombre" else -161)
    tdee = bmr * ACTIVIDAD[actividad]
    meta = tdee * (0.80 if "Déficit" in objetivo else 1.15 if "Volumen" in objetivo else 1.0)
    g_prot, g_gras = peso * 2.0, peso * 0.9
    resto = meta - g_prot * 4 - g_gras * 9
    g_carb = max(0.0, resto / 4)

    m = st.columns(3)
    m[0].metric("Meta diaria", f"{int(meta)} kcal")
    m[1].metric("Gasto total (TDEE)", f"{int(tdee)} kcal")
    m[2].metric("Metabolismo basal (BMR)", f"{int(bmr)} kcal")
    mc = st.columns(3)
    mc[0].metric("Proteínas", f"{int(g_prot)} g", "2.0 g/kg")
    mc[1].metric("Carbohidratos", f"{int(g_carb)} g", "el resto")
    mc[2].metric("Grasas", f"{int(g_gras)} g", "0.9 g/kg")
    if resto < 0:
        st.warning(f"Con esta meta, proteínas y grasas ya suman {int(g_prot * 4 + g_gras * 9)} kcal, "
                   f"más que la meta ({int(meta)} kcal). Baja las grasas o sube la meta.")

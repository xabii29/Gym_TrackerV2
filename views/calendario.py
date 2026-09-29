"""Calendario mensual: toca un día entrenado para ver su sesión."""
import calendar
from datetime import date

import streamlit as st

from modules import repo
from modules.config import DIAS, MESES, fmt_fecha, hoy
from modules.ui import inyectar_css, texto
from views.historial import detalle


def _cabecera_sesion(r):
    partes = [texto(r.plantilla) or "Sesión libre", f"{int(r.n_ejercicios)} ejercicios",
              f"{int(r.n_series)} series", f"{r.volumen_kg:,.0f} kg"]
    if r.duracion_min == r.duracion_min and r.duracion_min:   # NaN-safe
        partes.append(f"{int(r.duracion_min)} min")
    return " · ".join(partes)


def render():
    inyectar_css()
    st.title("📅 Calendario")
    h = hoy()
    c = st.columns(2)
    anio = int(c[0].number_input("Año", 2020, h.year + 1, h.year, 1))
    mes = c[1].selectbox("Mes", range(1, 13), index=h.month - 1, format_func=lambda m: MESES[m - 1].capitalize())

    ini, fin = date(anio, mes, 1), date(anio, mes, calendar.monthrange(anio, mes)[1])
    ses = repo.sesiones_resumen(ini, fin)
    por_dia = {f: g for f, g in ses.groupby("fecha")} if not ses.empty else {}
    por_dia = {(k.date() if hasattr(k, "date") else k): v for k, v in por_dia.items()}

    # el día elegido se olvida al cambiar de mes
    if st.session_state.get("cal_mes") != (anio, mes):
        st.session_state.update(cal_mes=(anio, mes), cal_dia=None)
    elegido = st.session_state.get("cal_dia")

    with st.container(key="cal_box"):
        cols = st.columns(7)
        for col, d in zip(cols, DIAS):
            col.markdown(f"<div style='text-align:center;opacity:.6;font-size:.8rem'>{d}</div>", unsafe_allow_html=True)
        for semana in calendar.Calendar(0).monthdayscalendar(anio, mes):
            cols = st.columns(7)
            for col, d in zip(cols, semana):
                if d == 0:
                    continue
                f = date(anio, mes, d)
                entreno = f in por_dia
                etiqueta = f"**{d}**" if f == h else str(d)
                if f == elegido:
                    etiqueta = f":orange[**{d}**]"
                if col.button(etiqueta, key=f"cal_{f.isoformat()}", type="primary" if entreno else "secondary",
                              disabled=not entreno, width="stretch"):
                    st.session_state["cal_dia"] = f
                    st.rerun()

    st.caption(f"{len(por_dia)} día(s) entrenados en {MESES[mes - 1]}. Toca un día en verde para ver su sesión.")
    if elegido and elegido in por_dia:
        st.subheader(fmt_fecha(elegido))
        for r in por_dia[elegido].itertuples():
            st.markdown(f"**{_cabecera_sesion(r)}**")
            if texto(r.notas):
                st.info("📝 " + texto(r.notas))
            detalle(int(r.id), editable=False)

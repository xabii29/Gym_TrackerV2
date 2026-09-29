"""Historial de sesiones, edición y respaldo en CSV."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from modules import repo
from modules.auth import es_editor
from modules.config import fmt_fecha, fmt_kg, hoy
from modules.ui import tabla, texto


def detalle(sid: int, editable: bool):
    """Series de una sesión; con editable=True permite corregir o borrar (solo en modo edición)."""
    df = repo.detalle_sesion(sid)
    if df.empty:
        st.caption("Sesión sin series.")
        return
    editable = editable and es_editor()
    for (eid, nom), g in df.groupby(["ejercicio_id", "ejercicio"], sort=False):
        st.markdown(f"**{nom}**")
        if not editable:
            st.caption(" · ".join(f"{fmt_kg(r.peso_kg)}×{r.reps}" + (" 🔥" if r.es_calentamiento else "")
                                  for r in g.itertuples()))
            continue
        base = g[["peso_kg", "reps", "es_calentamiento"]].rename(
            columns={"peso_kg": "Peso (kg)", "reps": "Reps", "es_calentamiento": "Calentamiento"})
        ed = st.data_editor(base, num_rows="dynamic", hide_index=True, key=f"ed_{sid}_{eid}", width="stretch")
        c = st.columns(2)
        if c[0].button("💾 Guardar cambios", key=f"gs_{sid}_{eid}"):
            filas = [dict(peso=float(r["Peso (kg)"] or 0), reps=int(r["Reps"] or 0), cal=bool(r["Calentamiento"]))
                     for _, r in ed.iterrows() if int(r["Reps"] or 0) > 0]
            rpe = g.rpe.dropna().iloc[0] if g.rpe.notna().any() else None
            nota = g.nota.dropna().iloc[0] if g.nota.notna().any() else None
            repo.guardar_ejercicio(sid, eid, filas, float(rpe) if rpe is not None else None, nota, historico=True)
            st.rerun()
        if c[1].button("🗑 Quitar ejercicio", key=f"qe_{sid}_{eid}"):
            repo.eliminar_ejercicio_de_sesion(sid, eid, historico=True)
            st.rerun()
        if g.nota.notna().any():
            st.caption("📝 " + str(g.nota.dropna().iloc[0]))


def render():
    st.title("📚 Historial")
    c = st.columns(2)
    desde = c[0].date_input("Desde", hoy() - timedelta(days=90))
    hasta = c[1].date_input("Hasta", hoy())
    ses = repo.sesiones_resumen(desde, hasta)
    if ses.empty:
        st.info("No hay sesiones en ese rango.")
    for r in ses.head(40).itertuples():
        titulo = f"{fmt_fecha(r.fecha)} · {texto(r.plantilla) or 'Sesión libre'} · {int(r.n_series)} series · {r.volumen_kg:,.0f} kg"
        with st.expander(titulo):
            if texto(r.notas):
                st.info("📝 " + texto(r.notas))
            detalle(int(r.id), editable=True)
            if es_editor():
                with st.popover("✏️ Editar sesión"):
                    f = st.date_input("Fecha", r.fecha, key=f"f_{r.id}", max_value=hoy())
                    n = st.text_area("Notas", texto(r.notas) or "", key=f"n_{r.id}")
                    if st.button("Guardar", key=f"g_{r.id}"):
                        repo.actualizar_sesion(int(r.id), f, n)
                        st.rerun()
                    if st.button("🗑 Borrar sesión completa", key=f"b_{r.id}"):
                        repo.descartar_sesion(int(r.id))
                        st.rerun()
    if len(ses) > 40:
        st.caption(f"Se muestran 40 de {len(ses)} sesiones; acota el rango para ver otras.")

    st.divider()
    st.subheader("💾 Respaldo")
    todo = repo.series_export()
    st.download_button("Descargar todas las series (CSV)", todo.to_csv(index=False).encode("utf-8-sig"),
                       "gym_tracker_series.csv", "text/csv", disabled=todo.empty)

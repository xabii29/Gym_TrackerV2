"""Catálogo: crear ejercicios propios y corregir nombres dudosos."""
import streamlit as st

from modules import repo
from modules.auth import requerir_editor
from modules.config import EQUIPOS_ES
from modules.db import leer


def _tab_personalizado(cat):
    st.caption("Para ejercicios que no están en el catálogo.")
    with st.form("nuevo_ej", clear_on_submit=True):
        nombre = st.text_input("Nombre del ejercicio")
        c = st.columns(3)
        categoria = c[0].selectbox("Grupo", sorted(cat.categoria.unique()))
        musculo = c[1].selectbox("Músculo principal", sorted(cat.musculo_objetivo.unique()))
        equipo = c[2].selectbox("Equipo", ["(ninguno)"] + sorted(cat.equipo.dropna().unique()),
                                format_func=lambda e: EQUIPOS_ES.get(e, e))
        if st.form_submit_button("Crear ejercicio", type="primary"):
            if not nombre.strip():
                st.error("Escribe un nombre.")
            else:
                try:
                    repo.crear_ejercicio(nombre, categoria, musculo, None if equipo == "(ninguno)" else equipo)
                    st.success("Ejercicio creado.")
                except Exception as e:  # noqa: BLE001
                    st.error(f"No se pudo crear (¿ya existe ese nombre?): {e}")


def _tab_revisar():
    st.caption("Nombres que el traductor automático marcó como dudosos. Corrige la columna **nombre** y guarda; "
               "al guardar dejan de aparecer aquí. Referencia: columna *nombre_en*.")
    q = st.text_input("Filtrar", placeholder="texto del nombre en inglés o español")
    df = leer("SELECT id, nombre, nombre_en, equipo FROM ejercicios WHERE revisar AND activo ORDER BY nombre", cache="catalogo")
    if q:
        df = df[df.nombre.str.contains(q, case=False) | df.nombre_en.str.contains(q, case=False, na=False)]
    st.write(f"{len(df)} pendientes")
    if df.empty:
        return
    ed = st.data_editor(df.head(100), hide_index=True, disabled=["id", "nombre_en", "equipo"], key="rev_ed",
                        width="stretch")
    if st.button("💾 Guardar nombres corregidos", type="primary"):
        orig = df.head(100).set_index("id").nombre
        cambios = [(r.id, r.nombre) for r in ed.itertuples() if r.nombre.strip() and r.nombre != orig[r.id]]
        if not cambios:
            st.info("No hay cambios.")
        else:
            try:
                repo.renombrar_ejercicios(cambios)
                st.success(f"{len(cambios)} nombre(s) actualizados.")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"No se pudo guardar (¿nombre duplicado?): {e}")


def render():
    st.title("📖 Catálogo")
    requerir_editor()
    cat = repo.catalogo()
    st.caption(f"{len(cat)} ejercicios activos.")
    t1, t2 = st.tabs(["Corregir nombres", "Ejercicio nuevo"])
    with t1:
        _tab_revisar()
    with t2:
        _tab_personalizado(cat)

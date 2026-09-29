"""Plantillas de entrenamiento: lista ordenable con ↑ ↓ ✕ y buscador para agregar ejercicios."""
import streamlit as st

from modules import repo
from modules.auth import requerir_editor
from modules.config import EQUIPOS_ES
from modules.ui import inyectar_css

NUEVA = "➕ Nueva plantilla"


def _cargar(elegida, pl):
    """Copia la plantilla elegida al estado de edición (solo cuando cambia la selección)."""
    if st.session_state.get("pl_cargada") == elegida:
        return
    if elegida == NUEVA:
        ids, nombre, pid = [], "", None
    else:
        sel = pl[pl.plantilla == elegida].dropna(subset=["ejercicio_id"])
        ids, nombre, pid = list(sel.ejercicio_id), elegida, int(pl[pl.plantilla == elegida].plantilla_id.iloc[0])
    st.session_state.update(pl_cargada=elegida, pl_ids=ids, pl_orig=list(ids), pl_nombre=nombre,
                            pl_nombre_orig=nombre, pl_pid=pid, pl_ver=st.session_state.get("pl_ver", 0) + 1)


def _lista(nombres):
    ids = st.session_state["pl_ids"]
    if not ids:
        st.caption("Aún no hay ejercicios. Agrega el primero abajo.")
    with st.container(key="series_box"):   # reutiliza el CSS que evita apilar columnas en el celular
        for i, eid in enumerate(ids):
            c = st.columns([7, 1, 1, 1])
            c[0].markdown(f"**{i + 1}.** {nombres.get(eid, eid)}")
            if c[1].button("↑", key=f"up_{i}", disabled=i == 0):
                ids[i - 1], ids[i] = ids[i], ids[i - 1]
                st.rerun()
            if c[2].button("↓", key=f"dn_{i}", disabled=i == len(ids) - 1):
                ids[i + 1], ids[i] = ids[i], ids[i + 1]
                st.rerun()
            if c[3].button("✕", key=f"rm_{i}"):
                ids.pop(i)
                st.rerun()


def _agregar(cat, nombres):
    ids = st.session_state["pl_ids"]
    with st.expander("➕ Agregar ejercicio", expanded=not ids):
        c = st.columns(2)
        grupo = c[0].selectbox("Grupo", ["Todos"] + sorted(cat.categoria.unique()), key="pl_grupo")
        equipo = c[1].selectbox("Equipo", ["Todos"] + sorted(cat.equipo.dropna().unique()), key="pl_equipo",
                                format_func=lambda e: EQUIPOS_ES.get(e, e))
        vista = cat
        if grupo != "Todos":
            vista = vista[vista.categoria == grupo]
        if equipo != "Todos":
            vista = vista[vista.equipo == equipo]
        ver = st.session_state["pl_ver"]
        elegido = st.selectbox(f"Buscar ({len(vista)} ejercicios)", list(vista.id), index=None,
                               format_func=lambda i: nombres.get(i, i), placeholder="Escribe para buscar…",
                               key=f"pl_add_{ver}")
        if st.button("Agregar a la plantilla", disabled=elegido is None, type="primary"):
            if elegido in ids:
                st.warning("Ese ejercicio ya está en la plantilla.")
            else:
                ids.append(elegido)
                st.session_state["pl_ver"] = ver + 1   # limpia el buscador
                st.rerun()


def render():
    inyectar_css()
    st.title("📋 Plantillas")
    requerir_editor()
    cat = repo.catalogo()
    nombres = dict(zip(cat.id, cat.nombre))
    pl = repo.plantillas()
    existentes = sorted(pl.plantilla.unique()) if not pl.empty else []

    if "pl_sel_pendiente" in st.session_state:          # tras guardar, apuntar a la plantilla guardada
        st.session_state["pl_sel"] = st.session_state.pop("pl_sel_pendiente")
    elegida = st.selectbox("Plantilla", [NUEVA] + existentes, key="pl_sel")
    _cargar(elegida, pl)

    nombre = st.text_input("Nombre de la plantilla", key="pl_nombre", placeholder="Ej: Día de empuje")
    ids = st.session_state["pl_ids"]
    st.markdown(f"##### Ejercicios ({len(ids)})")
    _lista(nombres)
    _agregar(cat, nombres)

    sin_guardar = ids != st.session_state["pl_orig"] or nombre.strip() != st.session_state["pl_nombre_orig"]
    if sin_guardar:
        st.warning("Hay cambios sin guardar.")
    pid = st.session_state["pl_pid"]
    c = st.columns(3)
    if c[0].button("💾 Guardar", type="primary", disabled=not (nombre.strip() and ids and sin_guardar),
                   width="stretch"):
        try:
            repo.guardar_plantilla(nombre, ids, pid)
        except Exception as e:  # noqa: BLE001
            st.error(f"No se pudo guardar (¿ya existe una plantilla con ese nombre?): {e}")
        else:
            st.session_state["pl_cargada"] = None
            st.session_state["pl_sel_pendiente"] = nombre.strip()
            st.toast("✅ Plantilla guardada")
            st.rerun()
    if pid and c[1].button("📄 Duplicar", width="stretch"):
        try:
            repo.guardar_plantilla(f"{nombre.strip()} (copia)", ids, None)
        except Exception as e:  # noqa: BLE001
            st.error(f"No se pudo duplicar: {e}")
        else:
            st.session_state["pl_cargada"] = None
            st.session_state["pl_sel_pendiente"] = f"{nombre.strip()} (copia)"
            st.rerun()
    if pid:
        with c[2].popover("🗑 Eliminar", width="stretch"):
            st.write(f"Se eliminará **{elegida}** (las sesiones ya registradas no se tocan).")
            if st.button("Sí, eliminar", key="pl_del"):
                repo.eliminar_plantilla(pid)
                st.session_state["pl_cargada"] = None
                st.session_state["pl_sel_pendiente"] = NUEVA
                st.rerun()

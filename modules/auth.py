"""Modo lectura para todos / modo edición con contraseña (st.secrets)."""
import hashlib
import hmac
import time

import streamlit as st

MAX_INTENTOS = 5
BLOQUEO_SEG = 60


def es_editor() -> bool:
    return bool(st.session_state.get("es_editor"))


def _contrasena_valida(intento: str) -> bool:
    conf = st.secrets.get("auth", {})
    if "password_sha256" in conf:
        h = hashlib.sha256(intento.encode()).hexdigest()
        return hmac.compare_digest(h, str(conf["password_sha256"]).lower())
    if "password" in conf:
        return hmac.compare_digest(intento.encode(), str(conf["password"]).encode())
    return False


def _configurada() -> bool:
    conf = st.secrets.get("auth", {})
    return "password" in conf or "password_sha256" in conf


def formulario_login(clave: str = "login"):
    """Dibuja el formulario. Devuelve True si se acaba de iniciar sesión."""
    if not _configurada():
        st.warning("No hay contraseña configurada: agrega `[auth] password = \"...\"` en los secrets. "
                   "Mientras tanto la app funciona solo en modo lectura.")
        return False
    bloqueado_hasta = st.session_state.get("bloqueado_hasta", 0)
    if time.time() < bloqueado_hasta:
        st.error(f"Demasiados intentos. Espera {int(bloqueado_hasta - time.time())} s.")
        return False
    with st.form(clave):
        pwd = st.text_input("Contraseña de edición", type="password")
        if st.form_submit_button("🔓 Entrar", type="primary"):
            if _contrasena_valida(pwd):
                st.session_state["es_editor"] = True
                st.session_state["intentos"] = 0
                st.rerun()
            st.session_state["intentos"] = st.session_state.get("intentos", 0) + 1
            if st.session_state["intentos"] >= MAX_INTENTOS:
                st.session_state["bloqueado_hasta"] = time.time() + BLOQUEO_SEG
                st.session_state["intentos"] = 0
            st.error("Contraseña incorrecta.")
    return False


def requerir_editor():
    """Al inicio de una pantalla que modifica datos."""
    if es_editor():
        return
    st.info("🔒 Estás en **modo lectura**. Para registrar o editar, ingresa la contraseña.")
    formulario_login("login_pagina")
    st.stop()


def sidebar_estado():
    with st.sidebar:
        if es_editor():
            st.success("✏️ Modo edición")
            if st.button("Salir del modo edición", width="stretch"):
                st.session_state["es_editor"] = False
                st.rerun()
        else:
            st.caption("👀 Modo lectura")

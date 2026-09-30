"""Gym Tracker V2 - punto de entrada."""
import streamlit as st

from modules.auth import formulario_login, es_editor, sidebar_estado
from modules.config import APP_NOMBRE
from modules.db import limpiar_todo, panel_debug
from modules.temas import render_selector_tema

st.set_page_config(page_title=APP_NOMBRE, page_icon="🏋️", layout="centered",
                   initial_sidebar_state="collapsed")

from views import calendario, catalogo, entrenar, historial, nutricion, plantillas, progreso, records, resumen  # noqa: E402

paginas = [
    st.Page(entrenar.render, title="Entrenar", icon="🏋️", url_path="entrenar", default=True),
    st.Page(resumen.render, title="Resumen", icon="📈", url_path="resumen"),
    st.Page(progreso.render, title="Progreso", icon="📊", url_path="progreso"),
    st.Page(records.render, title="Récords", icon="🏆", url_path="records"),
    st.Page(calendario.render, title="Calendario", icon="📅", url_path="calendario"),
    st.Page(historial.render, title="Historial", icon="📚", url_path="historial"),
    st.Page(plantillas.render, title="Plantillas", icon="📋", url_path="plantillas"),
    st.Page(catalogo.render, title="Catálogo", icon="📖", url_path="catalogo"),
    st.Page(nutricion.render, title="Nutrición", icon="🍽️", url_path="nutricion"),
]
nav = st.navigation(paginas)
st.sidebar.title(APP_NOMBRE)
sidebar_estado()
if not es_editor():
    with st.sidebar.expander("🔒 Modo edición"):
        formulario_login("login_sidebar")
render_selector_tema()
if st.sidebar.button("🔄 Refrescar datos", width="stretch"):
    limpiar_todo()
nav.run()
panel_debug()

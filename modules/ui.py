"""Utilidades de interfaz compartidas."""
import streamlit as st

CSS_MOVIL = """
<style>
/* Botones y campos cómodos para el pulgar */
.stApp button, .stApp input { min-height: 2.6rem; }
/* Las filas de series NO se apilan en pantallas angostas */
.st-key-series_box [data-testid="stHorizontalBlock"],
.st-key-cal_box [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .3rem; }
.st-key-series_box [data-testid="stColumn"], .st-key-series_box [data-testid="column"],
.st-key-cal_box [data-testid="stColumn"], .st-key-cal_box [data-testid="column"] { min-width: 0 !important; }
.st-key-cal_box button { padding: 0 !important; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; }
</style>
"""


def inyectar_css():
    st.markdown(CSS_MOVIL, unsafe_allow_html=True)


def tabla(df, **kw):
    kw.setdefault("hide_index", True)
    st.dataframe(df, width="stretch", **kw)


def html_con_js(html: str, altura: int = 70):
    """Incrusta HTML+JS (temporizador). st.components.v1.html fue retirado: se usa st.iframe."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=altura)
    else:  # Streamlit antiguo
        import streamlit.components.v1 as components
        components.html(html, height=altura)


def texto(v) -> str | None:
    """Texto o None: pandas devuelve NaN (que es 'verdadero') para NULL; esto lo normaliza."""
    import pandas as pd
    return None if v is None or (not isinstance(v, str) and pd.isna(v)) or str(v).strip() == "" else str(v)

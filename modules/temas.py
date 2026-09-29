"""Selector de temas de color para Gym Tracker.

Streamlit no permite cambiar su tema nativo en caliente, así que se inyecta CSS
sobre los componentes principales. La elección se guarda en la URL
(?tema=...) para que sobreviva a recargas y se pueda dejar como favorito
en el celular y en la computadora por separado.
"""

import streamlit as st

TEMA_DEFECTO = "Oscuro clásico"

# bg: fondo | bg2: tarjetas/sidebar/inputs | texto | primario: botones y acentos
# primario_txt: texto sobre el color primario | suave: texto secundario | borde
TEMAS = {
    "Oscuro clásico": {
        "bg": "#0e1117", "bg2": "#1e1e1e", "texto": "#fafafa",
        "primario": "#28a745", "primario_txt": "#ffffff",
        "suave": "#888888", "borde": "#333333",
    },
    "Claro": {
        "bg": "#ffffff", "bg2": "#f0f2f6", "texto": "#1a1a1a",
        "primario": "#1f77b4", "primario_txt": "#ffffff",
        "suave": "#6b7280", "borde": "#d1d5db",
    },
    "Medianoche": {
        "bg": "#0b132b", "bg2": "#1c2541", "texto": "#e0e6f5",
        "primario": "#5bc0be", "primario_txt": "#0b132b",
        "suave": "#8d99ae", "borde": "#3a506b",
    },
    "Bosque": {
        "bg": "#10231a", "bg2": "#1b3a2b", "texto": "#e8f5e9",
        "primario": "#8bc34a", "primario_txt": "#10231a",
        "suave": "#9bb5a4", "borde": "#2f5d46",
    },
    "Fuego": {
        "bg": "#1a0f0a", "bg2": "#2b1a12", "texto": "#fff3e8",
        "primario": "#ff6b35", "primario_txt": "#1a0f0a",
        "suave": "#b89a88", "borde": "#4a2c1d",
    },
    "Púrpura": {
        "bg": "#14101f", "bg2": "#241c3a", "texto": "#f1ecff",
        "primario": "#a78bfa", "primario_txt": "#14101f",
        "suave": "#a59cc4", "borde": "#3d3160",
    },
    "Alto contraste": {
        "bg": "#000000", "bg2": "#111111", "texto": "#ffffff",
        "primario": "#ffd60a", "primario_txt": "#000000",
        "suave": "#cccccc", "borde": "#ffffff",
    },
}


def get_tema() -> dict:
    """Devuelve la paleta del tema activo (para usar en gráficas, calendario, etc.)."""
    nombre = st.session_state.get("tema", TEMA_DEFECTO)
    return TEMAS.get(nombre, TEMAS[TEMA_DEFECTO])


def _al_cambiar_tema():
    st.query_params["tema"] = st.session_state["tema"]


def _css(t: dict) -> str:
    return f"""
    <style>
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: {t['bg']}; color: {t['texto']};
    }}
    [data-testid="stHeader"] {{ background-color: {t['bg']}; }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {{
        background-color: {t['bg2']};
    }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp label, .stApp li,
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] *,
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] * {{
        color: {t['texto']};
    }}
    .stApp [data-testid="stCaptionContainer"], .stApp small {{
        color: {t['suave']};
    }}
    .stApp hr {{ border-color: {t['borde']}; }}

    /* Inputs y selectores */
    .stApp input, .stApp textarea,
    .stApp [data-baseweb="select"] > div,
    .stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"] {{
        background-color: {t['bg2']}; color: {t['texto']};
        border-color: {t['borde']};
    }}
    .stApp [data-baseweb="select"] span {{ color: {t['texto']}; }}
    [data-baseweb="popover"] li, [data-baseweb="popover"] ul {{
        background-color: {t['bg2']}; color: {t['texto']};
    }}

    /* Botones */
    .stApp button[kind="primary"] {{
        background-color: {t['primario']}; color: {t['primario_txt']};
        border: 1px solid {t['primario']};
    }}
    .stApp button[kind="primary"] p {{ color: {t['primario_txt']}; }}
    .stApp button[kind="secondary"] {{
        background-color: {t['bg2']}; color: {t['texto']};
        border: 1px solid {t['borde']};
    }}
    .stApp button[kind="secondary"]:hover {{
        border-color: {t['primario']}; color: {t['primario']};
    }}

    /* Pestañas, expanders, radio */
    .stApp button[data-baseweb="tab"] {{ color: {t['suave']}; }}
    .stApp button[data-baseweb="tab"][aria-selected="true"] {{
        color: {t['primario']};
    }}
    .stApp [data-baseweb="tab-highlight"] {{ background-color: {t['primario']}; }}
    .stApp [data-testid="stExpander"] {{
        background-color: {t['bg2']}; border-color: {t['borde']};
    }}
    .stApp [data-testid="stExpander"] summary * {{ color: {t['texto']}; }}
    </style>
    """


def render_selector_tema():
    """Dibuja el selector en la barra lateral y aplica el tema elegido.

    Llamar una sola vez, cerca del inicio de app.py (después de set_page_config).
    """
    if "tema" not in st.session_state:
        desde_url = st.query_params.get("tema")
        st.session_state["tema"] = (
            desde_url if desde_url in TEMAS else TEMA_DEFECTO
        )

    with st.sidebar:
        st.selectbox(
            "🎨 Tema de color",
            options=list(TEMAS.keys()),
            key="tema",
            on_change=_al_cambiar_tema,
        )
        t = get_tema()
        muestra = "".join(
            f"<span style='display:inline-block;width:22px;height:22px;"
            f"border-radius:50%;margin-right:6px;background:{t[k]};"
            f"border:1px solid {t['borde']};'></span>"
            for k in ("bg", "bg2", "primario", "texto")
        )
        st.markdown(muestra, unsafe_allow_html=True)

    st.markdown(_css(get_tema()), unsafe_allow_html=True)

"""Acceso a PostgreSQL. Único punto de contacto con st.connection.

Rendimiento: cada consulta es un viaje de red a la base. Por eso hay 5 cachés independientes
y cada escritura solo invalida las que realmente cambian (no todo):

  catalogo  ejercicios, plantillas, instrucciones      (1 h)   cambia al editar catálogo/plantillas
  sesion    sesión en curso                            (10 min) cambia al iniciar/terminar/descartar
  vivo      series de la sesión en curso               (10 min) cambia al guardar un ejercicio
  historia  última vez, recientes                      (10 min) cambia al terminar una sesión
  general   gráficas, récords, calendario, historial   (60 s)   cambia al terminar/editar sesiones
"""
import time

import pandas as pd
import streamlit as st

CACHES = ("catalogo", "sesion", "vivo", "historia", "general")
LOG: list[tuple[str, float, str]] = []   # (tipo, ms, sql) de las últimas llamadas reales a la BD


def conexion():
    # pool_recycle: descarta conexiones inactivas antes de que el servidor las cierre
    return st.connection("postgresql", type="sql", pool_recycle=280)


def _registrar(tipo: str, t0: float, sql: str):
    LOG.append((tipo, (time.perf_counter() - t0) * 1000, " ".join(sql.split())[:70]))
    del LOG[:-40]


def _consultar(sql: str, params: dict) -> pd.DataFrame:
    t0 = time.perf_counter()
    df = conexion().query(sql, params=params, ttl=0)
    _registrar("LEER", t0, sql)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def _q_catalogo(sql, params):
    return _consultar(sql, params)


@st.cache_data(ttl=600, show_spinner=False)
def _q_sesion(sql, params):
    return _consultar(sql, params)


@st.cache_data(ttl=600, show_spinner=False)
def _q_vivo(sql, params):
    return _consultar(sql, params)


@st.cache_data(ttl=600, show_spinner=False)
def _q_historia(sql, params):
    return _consultar(sql, params)


@st.cache_data(ttl=60, show_spinner=False)
def _q_general(sql, params):
    return _consultar(sql, params)


_FUNCIONES = {"catalogo": _q_catalogo, "sesion": _q_sesion, "vivo": _q_vivo,
              "historia": _q_historia, "general": _q_general}


def _error_amigable(e: Exception) -> str:
    txt = str(e)
    if "does not exist" in txt and ("relation" in txt or "table" in txt or "function" in txt):
        return ("La base de datos aún no tiene el esquema v2. Ejecuta "
                "`python scripts/instalar_bd.py` (o los archivos de la carpeta `sql/` en orden).")
    return f"No se pudo consultar la base de datos: {e}"


def leer(sql: str, params: dict | None = None, cache: str = "general") -> pd.DataFrame:
    """Consulta con caché por categoría. Si falla muestra el error y detiene la pantalla
    (nunca datos vacíos falsos)."""
    try:
        return _FUNCIONES[cache](sql, params or {})
    except Exception as e:  # noqa: BLE001
        st.error(_error_amigable(e))
        st.button("🔄 Reintentar")
        st.stop()


def escribir(fn, limpiar: tuple[str, ...] = CACHES):
    """Ejecuta fn(session) en UNA transacción e invalida solo las cachés indicadas."""
    t0 = time.perf_counter()
    with conexion().session as s:
        try:
            resultado = fn(s)
            s.commit()
        except Exception:
            s.rollback()
            raise
    _registrar("ESCRIBIR", t0, "transacción")
    for nombre in limpiar:
        _FUNCIONES[nombre].clear()
    return resultado


def limpiar_todo():
    for f in _FUNCIONES.values():
        f.clear()


def panel_debug():
    """Con ?debug=1 muestra cuánto tarda cada llamada real a la base (las de caché no aparecen)."""
    if st.query_params.get("debug") != "1":
        return
    with st.sidebar.expander("🛠 Diagnóstico de rendimiento", expanded=True):
        if st.button("🔄 Vaciar cachés"):
            limpiar_todo()
        if not LOG:
            st.caption("Sin llamadas reales a la base (todo salió de caché).")
        for tipo, ms, sql in reversed(LOG[-12:]):
            st.caption(f"{tipo} {ms:.0f} ms · {sql}")

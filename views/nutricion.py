"""Nutrición: tus calorías y macros por fase (tú decides los números), recordatorio de semanas e historial."""
import altair as alt
import pandas as pd
import streamlit as st

from modules import repo
from modules.auth import es_editor
from modules.config import fmt_fecha, hoy
from modules.nutricion import COLORES, TIPOS, kcal_de_macros, progreso_fase, semanas_por_tipo
from modules.temas import get_tema
from modules.ui import inyectar_css, tabla, texto

ESCALA = alt.Scale(domain=list(COLORES), range=list(COLORES.values()))


def _limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """Fechas como date; fin NULL como None."""
    df = df.copy()
    df["inicio"] = pd.to_datetime(df["inicio"]).dt.date
    df["fin"] = pd.Series([None if pd.isna(x) else pd.Timestamp(x).date() for x in df["fin"]],
                          index=df.index, dtype=object)
    df["semanas_planeadas"] = pd.Series([None if pd.isna(x) else int(x) for x in df["semanas_planeadas"]],
                                        index=df.index, dtype=object)
    return df


def _error_fase(e: Exception) -> str:
    t = str(e).lower()
    if "exclusion" in t or "overlap" in t or "conflicting key" in t:
        return ("Las fechas se cruzan con otra fase (o ya hay un plan que empezó ese día). "
                "Si solo te equivocaste en un número, usa **✏️ Corregir plan actual**.")
    return f"No se pudo guardar: {e}"


def _plan_actual(actual):
    st.subheader(f"Plan actual · {TIPOS[actual.tipo]}")
    c = st.columns(4)
    c[0].metric("Calorías", f"{int(actual.kcal)} kcal")
    c[1].metric("Proteína", f"{int(actual.proteina_g)} g")
    c[2].metric("Carbohidratos", f"{int(actual.carbos_g)} g")
    c[3].metric("Grasas", f"{int(actual.grasas_g)} g")
    suma = kcal_de_macros(int(actual.proteina_g), int(actual.carbos_g), int(actual.grasas_g))
    dif = suma - int(actual.kcal)
    if abs(dif) > 50:
        st.caption(f"Los macros suman {suma} kcal ({dif:+d} vs. tu meta de {int(actual.kcal)}).")
    if texto(actual.nota):
        st.caption("📝 " + texto(actual.nota))

    p = progreso_fase(actual.inicio, actual.semanas_planeadas, hoy())
    if p["futuro"]:
        st.info(f"Este plan empieza el {fmt_fecha(actual.inicio)}.")
        return
    if "estado" not in p:
        st.write(f"📅 Semana **{p['semana_actual']}** (sin plazo definido) · desde el {fmt_fecha(actual.inicio)}.")
        return
    st.progress(p["fraccion"], text=f"Semana {min(p['semana_actual'], p['planeadas'])} de {p['planeadas']}")
    fin = fmt_fecha(p["fin_estimado"])
    if p["estado"] == "vencido":
        st.warning(f"⏰ Tu plan de {p['planeadas']} semanas terminó el {fin} (hace {-p['dias_restantes']} días). "
                   "¿Lo extiendes, o cambias de fase?")
    elif p["estado"] == "termina_hoy":
        st.warning(f"⏰ Hoy se cumplen las {p['planeadas']} semanas de este plan.")
    elif p["estado"] == "por_terminar":
        st.warning(f"⏳ Te queda menos de una semana ({p['dias_restantes']} días). Termina el {fin}.")
    else:
        st.write(f"⏳ Faltan **{p['semanas_restantes']} semana(s)** · termina el {fin}.")


def _campos(prefijo: str, prev=None, tipo_def="recomp"):
    """Campos comunes a 'nuevo plan' y 'corregir plan' (claves únicas por prefijo)."""
    tipos = list(TIPOS)
    c = st.columns(2)
    tipo = c[0].selectbox("Fase", tipos, index=tipos.index(prev.tipo if prev is not None else tipo_def),
                          format_func=TIPOS.get, key=f"{prefijo}_tipo")
    inicio = c[1].date_input("Empieza", prev.inicio if prev is not None else hoy(), key=f"{prefijo}_inicio")
    c = st.columns(2)
    kcal = c[0].number_input("Calorías (kcal)", 800, 8000, int(prev.kcal) if prev is not None else 2500, 50,
                             key=f"{prefijo}_kcal")
    sem = c[1].number_input("Semanas planeadas (0 = sin plazo)", 0, 104,
                            int(prev.semanas_planeadas) if prev is not None and prev.semanas_planeadas else 0, 1, key=f"{prefijo}_semanas")
    c = st.columns(3)
    p = c[0].number_input("Proteína (g)", 0, 600, int(prev.proteina_g) if prev is not None else 150, 5, key=f"{prefijo}_p")
    ch = c[1].number_input("Carbos (g)", 0, 1000, int(prev.carbos_g) if prev is not None else 250, 5, key=f"{prefijo}_c")
    g = c[2].number_input("Grasas (g)", 0, 300, int(prev.grasas_g) if prev is not None else 70, 5, key=f"{prefijo}_g")
    nota = st.text_input("Nota (opcional)", (texto(prev.nota) or "") if prev is not None else "", key=f"{prefijo}_nota")
    return tipo, inicio, int(sem) or None, int(kcal), int(p), int(ch), int(g), nota


def _formularios(actual):
    with st.expander("➕ Nuevo plan / cambiar de fase", expanded=actual is None):
        with st.form("nuevo_plan"):
            st.caption("Al guardar, el plan vigente se cierra el día en que empieza el nuevo. "
                       "Los números están prellenados con el plan actual para que solo ajustes lo que cambió.")
            tipo, inicio, sem, kcal, p, c, g, nota = _campos("nf", actual)
            pasada = st.checkbox("Es una fase pasada (ya terminó)", key="nf_pasada")
            fin = st.date_input("Terminó el (solo si es una fase pasada)", hoy(), key="nf_fin")
            if st.form_submit_button("💾 Guardar plan", type="primary"):
                if pasada and fin <= inicio:
                    st.error("La fecha de fin debe ser posterior al inicio.")
                else:
                    try:
                        repo.nueva_fase(tipo, inicio, sem, kcal, p, c, g, nota, fin if pasada else None)
                    except Exception as e:  # noqa: BLE001
                        st.error(_error_fase(e))
                    else:
                        st.toast("✅ Plan guardado")
                        st.rerun()
    if actual is not None:
        with st.expander("✏️ Corregir plan actual"):
            with st.form(f"corregir_{actual.id}"):
                tipo, inicio, sem, kcal, p, c, g, nota = _campos(f"ed{actual.id}", actual)
                if st.form_submit_button("💾 Guardar corrección"):
                    try:
                        repo.corregir_fase(int(actual.id), tipo, inicio, sem, kcal, p, c, g, nota)
                    except Exception as e:  # noqa: BLE001
                        st.error(_error_fase(e))
                    else:
                        st.toast("✅ Corregido")
                        st.rerun()
            if st.button("🏁 Cerrar este plan hoy (sin plan nuevo)", key="cerrar_hoy"):
                try:
                    repo.cerrar_fase(int(actual.id), hoy())
                except Exception as e:  # noqa: BLE001
                    st.error(_error_fase(e))
                else:
                    st.rerun()


def _historial(df):
    st.subheader("🗓️ Historial de fases")
    fin_plot = [f or hoy() for f in df["fin"]]
    graf = df.assign(inicio=pd.to_datetime(df["inicio"]), fin_plot=pd.to_datetime(fin_plot),
                     fase=[TIPOS[t] for t in df["tipo"]])
    st.altair_chart(alt.Chart(graf).mark_bar(height=34).encode(
        x=alt.X("inicio:T", title=None), x2="fin_plot:T",
        color=alt.Color("tipo:N", scale=ESCALA, legend=alt.Legend(title="Fase")),
        tooltip=["fase", "inicio:T", "fin_plot:T", "kcal", "proteina_g", "carbos_g", "grasas_g"]).properties(height=90),
        width="stretch")

    lista = df.to_dict("records")
    c = st.columns(2)
    for col, titulo, dias in ((c[0], "Últimos 12 meses", 365), (c[1], "Desde el primer registro", None)):
        desde = hoy().replace(year=hoy().year - 1) if dias else min(f["inicio"] for f in lista)
        res = semanas_por_tipo(lista, desde, hoy())
        col.markdown(f"**{titulo}**")
        for t in TIPOS:
            if t in res:
                col.write(f"{TIPOS[t]}: **{res[t]:.0f}** semanas")
        if not res:
            col.caption("Sin datos.")

    vista = df.assign(
        Fase=[TIPOS[t] for t in df["tipo"]], Inicio=[fmt_fecha(i) for i in df["inicio"]],
        Fin=[fmt_fecha(f) if f else "vigente" for f in df["fin"]],
        Semanas=[round(((f or hoy()) - i).days / 7, 1) for i, f in zip(df["inicio"], df["fin"])],
        Plan=[str(s) if s else "—" for s in df["semanas_planeadas"]],
    )[["Fase", "Inicio", "Fin", "Semanas", "Plan", "kcal", "proteina_g", "carbos_g", "grasas_g", "nota"]]
    tabla(vista.rename(columns={"proteina_g": "P (g)", "carbos_g": "C (g)", "grasas_g": "G (g)",
                                "nota": "Nota", "Plan": "Sem. planeadas"}))
    if es_editor():
        with st.expander("🗑 Eliminar una fase (error de captura)"):
            elegido = st.selectbox("Fase", list(df["id"]), key="del_fase",
                                   format_func=lambda i: (lambda r: f"{TIPOS[r.tipo]} · {fmt_fecha(r.inicio)} · {int(r.kcal)} kcal")(
                                       df[df["id"] == i].iloc[0]))
            if st.button("Eliminar", key="btn_del_fase"):
                repo.eliminar_fase(int(elegido))
                st.rerun()


def _peso(fases_df):
    st.subheader("⚖️ Peso corporal")
    pesos = repo.pesos_corporales()
    ultimo = float(pesos.peso_kg.iloc[-1]) if not pesos.empty else 70.0
    if es_editor():
        c = st.columns([2, 2, 1])
        fecha = c[0].date_input("Fecha", hoy(), max_value=hoy(), key="pc_fecha")
        kg = c[1].number_input("Peso (kg)", 30.0, 250.0, ultimo, 0.1, key="pc_kg")
        if c[2].button("Guardar", type="primary", key="pc_guardar"):
            repo.guardar_peso(fecha, kg)
            st.rerun()
    if pesos.empty:
        st.caption("Aún no hay pesos registrados.")
        return
    pesos = pesos.assign(fecha=pd.to_datetime(pesos["fecha"]))
    linea = alt.Chart(pesos).mark_line(point=True, color=get_tema()["primario"]).encode(
        x=alt.X("fecha:T", title=None), y=alt.Y("peso_kg:Q", scale=alt.Scale(zero=False), title="kg"),
        tooltip=["fecha:T", "peso_kg"])
    graf = linea
    if fases_df is not None and not fases_df.empty:
        bandas = fases_df.assign(inicio=pd.to_datetime(fases_df["inicio"]),
                                 fin_plot=pd.to_datetime([f or hoy() for f in fases_df["fin"]]))
        graf = alt.Chart(bandas).mark_rect(opacity=0.16).encode(
            x="inicio:T", x2="fin_plot:T", color=alt.Color("tipo:N", scale=ESCALA, legend=alt.Legend(title="Fase"))) + linea
    st.altair_chart(graf.properties(height=260), width="stretch")


def render():
    inyectar_css()
    st.title("🍽️ Nutrición")
    st.caption("Tú decides las calorías y macros; aquí se guardan por fase para no perder el hilo.")
    crudo = repo.fases()
    df = _limpiar(crudo) if not crudo.empty else None
    abiertas = df[df["fin"].isna()] if df is not None else None
    actual = abiertas.iloc[0] if abiertas is not None and not abiertas.empty else None

    if actual is not None:
        _plan_actual(actual)
    elif df is None:
        st.info("Aún no hay ningún plan. Registra tu fase actual" + (" abajo." if es_editor() else " (requiere modo edición)."))
    else:
        st.info("No hay un plan vigente: todas las fases registradas ya terminaron.")
    if es_editor():
        _formularios(actual)
    if df is not None:
        st.divider()
        _historial(df)
    st.divider()
    _peso(df)

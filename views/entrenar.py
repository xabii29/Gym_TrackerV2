"""Registro de entrenamiento (pensado para el celular)."""
import streamlit as st

from modules import repo
from modules.auth import requerir_editor
from modules.config import fmt_fecha, fmt_kg, hoy
from modules.ui import html_con_js, inyectar_css, texto

TEMPORIZADOR = """
<div style="font-family:sans-serif;display:flex;gap:6px;align-items:center;flex-wrap:wrap">
  <b id="t" style="font-size:26px;min-width:64px">0:00</b>
  <button onclick="ini(60)">1:00</button><button onclick="ini(90)">1:30</button>
  <button onclick="ini(120)">2:00</button><button onclick="ini(180)">3:00</button>
  <button onclick="ini(0)">■</button>
</div>
<script>
let id=null;
function fmt(s){return Math.floor(s/60)+":"+String(s%60).padStart(2,"0");}
function pita(){try{const c=new (window.AudioContext||window.webkitAudioContext)();const o=c.createOscillator();
 o.connect(c.destination);o.frequency.value=880;o.start();setTimeout(()=>o.stop(),400);}catch(e){}
 if(navigator.vibrate)navigator.vibrate([300,100,300]);}
function ini(n){clearInterval(id);const t=document.getElementById("t");if(!n){t.textContent="0:00";return;}
 let r=n;t.textContent=fmt(r);id=setInterval(()=>{r--;t.textContent=fmt(r);if(r<=0){clearInterval(id);pita();}},1000);}
</script>"""


def _filas_iniciales(sid, eid, hechas, previa):
    """Series guardadas hoy > lo de la última vez > 3 series vacías."""
    if not hechas.empty:
        return [dict(peso=float(r.peso_kg), reps=int(r.reps), cal=bool(r.es_calentamiento))
                for r in hechas.itertuples()]
    if not previa.empty:
        return [dict(peso=float(r.peso_kg), reps=int(r.reps), cal=bool(r.es_calentamiento))
                for r in previa.itertuples()]
    return [dict(peso=0.0, reps=10, cal=False) for _ in range(3)]


def _sugerencia(previa):
    trab = previa[~previa.es_calentamiento]
    if trab.empty:
        return None
    mejor = trab.sort_values(["peso_kg", "reps"], ascending=False).iloc[0]
    peso, reps = float(mejor.peso_kg), int(mejor.reps)
    if peso == 0:
        return f"Prueba {reps + 1} reps"
    if reps >= 12:
        return f"Prueba {fmt_kg(peso + 2.5)} kg × {max(reps - 4, 6)}"
    return f"Prueba {fmt_kg(peso)} kg × {reps + 1}"


def _panel_ejercicio(sid, eid, nombre, series_sesion):
    hechas = series_sesion[series_sesion.ejercicio_id == eid]
    previa = repo.ultima_vez(eid, sid)
    st.subheader(nombre)
    if not previa.empty:
        resumen = " · ".join(f"{fmt_kg(r.peso_kg)}×{r.reps}" for r in previa.itertuples())
        st.caption(f"Última vez ({fmt_fecha(previa.fecha.iloc[0])}): {resumen}")
        sug = _sugerencia(previa)
        if sug:
            st.caption(f"💡 {sug}")
    key_ej = f"{sid}_{eid}"
    est = st.session_state.setdefault(
        f"filas_{key_ej}", {"ver": 0, "filas": _filas_iniciales(sid, eid, hechas, previa)})
    ver, filas = est["ver"], est["filas"]

    with st.form(f"form_{key_ej}_{ver}"):
        h = st.columns([0.7, 2, 2, 1.2])
        h[1].caption("kg"); h[2].caption("reps"); h[3].caption("🔥 cal.")
        valores = []
        with st.container(key="series_box"):
            for i, f in enumerate(filas):
                c = st.columns([0.7, 2, 2, 1.2])
                c[0].markdown(f"**{i + 1}**")
                peso = c[1].number_input("kg", 0.0, 1000.0, float(f["peso"]), 2.5,
                                         key=f"p_{key_ej}_{ver}_{i}", label_visibility="collapsed")
                reps = c[2].number_input("reps", 0, 200, int(f["reps"]), 1,
                                         key=f"r_{key_ej}_{ver}_{i}", label_visibility="collapsed")
                cal = c[3].checkbox("cal", bool(f["cal"]), key=f"c_{key_ej}_{ver}_{i}",
                                    label_visibility="collapsed")
                valores.append(dict(peso=peso, reps=reps, cal=cal))
        with st.expander("Detalles opcionales"):
            rpe = st.number_input("RPE (0 = sin dato)", 0.0, 10.0, 0.0, 0.5, key=f"rpe_{key_ej}_{ver}")
            nota = st.text_input("Nota del ejercicio", key=f"nota_{key_ej}_{ver}")
        b = st.columns(3)
        mas = b[0].form_submit_button("➕ Serie", width="stretch")
        menos = b[1].form_submit_button("➖", width="stretch")
        guardar = b[2].form_submit_button("💾 Guardar", type="primary", width="stretch")

    if mas:
        est.update(filas=valores + [dict(valores[-1])], ver=ver + 1)
        st.rerun()
    if menos and len(valores) > 1:
        est.update(filas=valores[:-1], ver=ver + 1)
        st.rerun()
    if guardar:
        validas = [v for v in valores if v["reps"] > 0]
        try:
            repo.guardar_ejercicio(sid, eid, validas, rpe or None, nota)
        except Exception as e:  # noqa: BLE001
            st.error(f"No se pudo guardar: {e}")
        else:
            est["filas"] = validas or valores
            st.toast(f"✅ {nombre}: {len(validas)} series guardadas")
            st.rerun()
    html_con_js(TEMPORIZADOR, 70)
    instr = repo.instrucciones(eid)
    if instr:
        with st.expander("📖 Cómo se hace"):
            st.write(instr)


def _selector_ejercicio(sesion, catalogo, hechas):
    plantillas = repo.plantillas()
    ids_plantilla = []
    if texto(sesion.plantilla):
        p = plantillas[plantillas.plantilla == sesion.plantilla].dropna(subset=["ejercicio_id"])
        ids_plantilla = list(p.ejercicio_id)
    n_hechas = hechas.groupby("ejercicio_id").size().to_dict() if not hechas.empty else {}
    nombres = dict(zip(catalogo.id, catalogo.nombre))
    modo = st.radio("Ejercicio", ["Plantilla", "Buscar"] if ids_plantilla else ["Buscar"],
                    horizontal=True, label_visibility="collapsed")
    if modo == "Plantilla":
        def etiqueta(i):
            return f"{'✅' if i in n_hechas else '⬜'} {nombres.get(i, i)}" + (f"  ({n_hechas[i]})" if i in n_hechas else "")
        return st.selectbox("Ejercicio de la plantilla", ids_plantilla, format_func=etiqueta,
                            key="sel_plantilla")
    with st.expander("Filtros (opcional)"):
        cat = st.selectbox("Categoría", ["Todas"] + sorted(catalogo.categoria.unique()))
        eq = st.selectbox("Equipo", ["Todos"] + sorted(catalogo.equipo.dropna().unique()))
    cat_f = catalogo
    if cat != "Todas":
        cat_f = cat_f[cat_f.categoria == cat]
    if eq != "Todos":
        cat_f = cat_f[cat_f.equipo == eq]
    rec = repo.recientes()
    orden = [i for i in rec.id if i in set(cat_f.id)] + [i for i in cat_f.id if i not in set(rec.id)]
    return st.selectbox("Buscar ejercicio (escribe para filtrar)", orden, index=None,
                        format_func=lambda i: ("⭐ " if i in set(rec.id) else "") + nombres.get(i, i),
                        placeholder="Ej: press banca", key="sel_buscar")


def render():
    inyectar_css()
    st.title("🏋️ Entrenar")
    requerir_editor()
    sesion = repo.sesion_activa()
    if sesion is None:
        pl = repo.plantillas()
        nombres = sorted(pl.plantilla.unique()) if not pl.empty else []
        elegida = st.selectbox("Plantilla", ["Sesión libre"] + nombres)
        fecha = st.date_input("Fecha de la sesión", hoy(), max_value=hoy())
        if st.button("▶ Empezar sesión", type="primary", width="stretch"):
            repo.iniciar_sesion(fecha, None if elegida == "Sesión libre" else elegida)
            st.rerun()
        return

    sid = int(sesion.id)
    st.caption(f"Sesión del {fmt_fecha(sesion.fecha)}" + (f" · {sesion.plantilla}" if texto(sesion.plantilla) else "")
               + " · se guarda ejercicio por ejercicio: puedes cerrar el navegador y retomarla")
    catalogo = repo.catalogo()
    hechas = repo.series_sesion(sid)
    eid = _selector_ejercicio(sesion, catalogo, hechas)
    if eid:
        _panel_ejercicio(sid, eid, dict(zip(catalogo.id, catalogo.nombre)).get(eid, eid), hechas)

    st.divider()
    if not hechas.empty:
        with st.expander(f"📋 Resumen de la sesión ({hechas.ejercicio_id.nunique()} ejercicios)", expanded=False):
            for (ej_id, nom), g in hechas.groupby(["ejercicio_id", "ejercicio"], sort=False):
                c = st.columns([5, 1])
                c[0].markdown(f"**{nom}** — " + " · ".join(f"{fmt_kg(r.peso_kg)}×{r.reps}" for r in g.itertuples()))
                if c[1].button("🗑", key=f"del_{ej_id}"):
                    repo.eliminar_ejercicio_de_sesion(sid, ej_id)
                    st.session_state.pop(f"filas_{sid}_{ej_id}", None)
                    st.rerun()
    notas = st.text_area("📝 Notas de la sesión (opcional)", placeholder="Ej: dormí poco, molestia en hombro…",
                         height=90, key=f"notas_{sid}")
    c = st.columns(2)
    if c[0].button("🏁 Terminar sesión", type="primary", width="stretch", disabled=hechas.empty):
        repo.finalizar_sesion(sid, notas)
        st.success("¡Sesión guardada!")
        st.rerun()
    with c[1].popover("🗑 Descartar", width="stretch"):
        st.write("Se borrará toda la sesión en curso.")
        if st.button("Sí, descartar", key="descartar"):
            repo.descartar_sesion(sid)
            st.rerun()

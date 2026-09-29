"""Prueba de integración: app real + PostgreSQL temporal. Ejecutar:  python tests/test_app.py"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "tests")]

from streamlit.testing.v1 import AppTest  # noqa: E402

import bd_temporal  # noqa: E402

srv, URI, CON = bd_temporal.iniciar()
CUR = CON.cursor()
SECRETS = {"connections": {"postgresql": {"dialect": "postgresql", "url": URI.replace("postgresql://", "postgresql+psycopg2://")}},
           "auth": {"password": "clave-de-prueba"}}
resultados = []

# AppTest no propaga secretos anidados: se escriben en el secrets.toml del usuario (solo entorno de pruebas)
_dir = Path.home() / ".streamlit"
_dir.mkdir(exist_ok=True)
_sec = _dir / "secrets.toml"
_backup = _sec.read_text() if _sec.exists() else None
_sec.write_text(f'[connections.postgresql]\ndialect = "postgresql"\nurl = "{SECRETS["connections"]["postgresql"]["url"]}"\n'
                f'[auth]\npassword = "clave-de-prueba"\n')
import atexit  # noqa: E402
atexit.register(lambda: _sec.write_text(_backup) if _backup is not None else _sec.unlink(missing_ok=True))


def check(nombre, cond, extra=""):
    resultados.append(cond)
    print(("PASS " if cond else "FAIL ") + nombre + (f"  [{extra}]" if extra else ""))


def app(codigo=None, editor=False):
    at = AppTest.from_string(codigo, default_timeout=60) if codigo else AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60)
    if editor:
        at.session_state["es_editor"] = True
    return at


def limpio(a):
    """Sin excepciones Y sin avisos rojos (los errores de BD se muestran con st.error)."""
    return not a.exception and not a.error


def vista(mod, editor=False):
    return app(f"import sys; sys.path.insert(0, r'{RAIZ}')\nfrom views.{mod} import render\nrender()", editor)


# ---------------------------------------------------------------- 1. acceso
at = app().run()
check("app arranca sin excepciones", limpio(at), str((at.exception, [e.value[:160] for e in at.error]))[:300])
check("modo lectura por defecto pide contraseña", any("modo lectura" in i.value for i in at.info))

at = app().run()
formu = at.text_input[0] if at.text_input else None
check("hay formulario de contraseña", formu is not None)
formu.set_value("mala").run()
[b for b in at.button if "Entrar" in b.label][0].click().run()
check("contraseña incorrecta se rechaza", not at.session_state["es_editor"] if "es_editor" in at.session_state else True)
at.text_input[0].set_value("clave-de-prueba").run()
[b for b in at.button if "Entrar" in b.label][0].click().run()
check("contraseña correcta activa modo edición", at.session_state["es_editor"] is True)

# --------------------------------------------------- 2. flujo de una sesión
at = vista("entrenar", editor=True).run()
check("entrenar (editor) sin excepciones", limpio(at), str((at.exception, [e.value[:160] for e in at.error]))[:300])
at.selectbox[0].select("Push (Pecho, Hombro, Tríceps)" if "Push (Pecho, Hombro, Tríceps)" in at.selectbox[0].options else at.selectbox[0].options[1]).run()
[b for b in at.button if "Empezar" in b.label][0].click().run()
CUR.execute("select count(*), max(plantilla) from sesiones where estado='en_curso'")
check("iniciar crea una sesión en_curso", CUR.fetchone()[0] == 1)

# retomar tras "cerrar el navegador": app nueva, misma BD
at = vista("entrenar", editor=True).run()
check("la sesión en curso se retoma en una sesión nueva del navegador", any("se guarda ejercicio" in c.value for c in at.caption))

sid = None
CUR.execute("select id from sesiones where estado='en_curso'"); sid = CUR.fetchone()[0]
at.radio[0].set_value("Plantilla" if "Plantilla" in at.radio[0].options else "Buscar").run()
check("selector de ejercicio de la plantilla aparece", len(at.selectbox) >= 1)
eid = at.selectbox[0].options[0] if at.selectbox[0].options else None
CUR.execute("""select pe.ejercicio_id from plantilla_ejercicios pe join plantillas p on p.id=pe.plantilla_id
               where p.nombre=(select plantilla from sesiones where id=%s) order by pe.orden limit 1""", (sid,))
EID = CUR.fetchone()[0]
at.selectbox(key="sel_plantilla").set_value(EID).run()
check("panel de ejercicio sin excepciones", limpio(at), str((at.exception, [e.value[:160] for e in at.error]))[:300])
# capturar 3 series: 60x8, 62.5x6 y calentamiento 40x10
nums = [n for n in at.number_input if n.label in ("kg", "reps")]
check("hay 3 filas de series por defecto", len(nums) == 6, f"{len(nums)} campos")
vals = [(60.0, 8), (62.5, 6), (40.0, 10)]
for i, (p, r) in enumerate(vals):
    nums[2 * i].set_value(p); nums[2 * i + 1].set_value(r)
at.checkbox[2].set_value(True)
[b for b in at.button if "Guardar" in b.label][0].click().run()
CUR.execute("select serie, reps, peso_kg, es_calentamiento from series where sesion_id=%s order by serie", (sid,))
filas = CUR.fetchall()
check("las series se guardan con su peso (bug v1 corregido)", [(f[1], float(f[2])) for f in filas] == [(8, 60.0), (6, 62.5), (10, 40.0)], str(filas))
check("calentamiento marcado", [f[3] for f in filas] == [False, False, True])
CUR.execute("select count(distinct ejercicio_id) from series where sesion_id=%s", (sid,))
check("solo 1 ejercicio en la sesión", CUR.fetchone()[0] == 1)

# re-guardar el mismo ejercicio reemplaza, no duplica
at = vista("entrenar", editor=True).run()
at.selectbox(key="sel_plantilla").set_value(EID).run()
[b for b in at.button if "Guardar" in b.label][0].click().run()
CUR.execute("select count(*) from series where sesion_id=%s", (sid,))
check("re-guardar no duplica series", CUR.fetchone()[0] == 3)

# notas vacías = NULL, terminar
at = vista("entrenar", editor=True).run()
at.text_area[0].set_value("   ").run()
[b for b in at.button if "Terminar" in b.label][0].click().run()
CUR.execute("select estado, notas, fin is not null from sesiones where id=%s", (sid,))
check("terminar con notas vacías guarda NULL", CUR.fetchone() == ("terminada", None, True))

# segunda sesión con nota real
at = vista("entrenar", editor=True).run()
[b for b in at.button if "Empezar" in b.label][0].click().run()
at = vista("entrenar", editor=True).run()
CUR.execute("select id from sesiones where estado='en_curso'"); sid2 = CUR.fetchone()[0]
at.radio[0].set_value("Buscar").run()
CUR.execute("select id from ejercicios where nombre ilike 'Press de banca inclinado (barra)%' limit 1")
EID2 = (CUR.fetchone() or [EID])[0]
at.selectbox(key="sel_buscar").set_value(EID2).run()
check("buscar ejercicio en catálogo funciona", not at.exception, str(at.exception)[:200])
[b for b in at.button if "Guardar" in b.label][0].click().run()
at = vista("entrenar", editor=True).run()
at.text_area[0].set_value("Dormí poco, hombro molesto").run()
if any("Terminar" in b.label and not b.disabled for b in at.button):
    [b for b in at.button if "Terminar" in b.label][0].click().run()
CUR.execute("select notas from sesiones where id=%s", (sid2,))
check("nota de sesión con texto se guarda", (CUR.fetchone() or [None])[0] == "Dormí poco, hombro molesto")

# ------------------------------------------------- 3. todas las pantallas
for mod in ["resumen", "progreso", "records", "calendario", "historial", "calorias"]:
    a = vista(mod, editor=False).run()
    check(f"pantalla {mod} (lectura) sin excepciones", limpio(a), str((a.exception, [e.value[:160] for e in a.error]))[:300])
for mod in ["historial", "plantillas", "catalogo", "calorias"]:
    a = vista(mod, editor=True).run()
    check(f"pantalla {mod} (editor) sin excepciones", limpio(a), str((a.exception, [e.value[:160] for e in a.error]))[:300])
a = vista("plantillas", editor=False).run()
check("plantillas exige contraseña", any("modo lectura" in i.value for i in a.info))

# ---- calendario: tocar un día entrenado muestra la sesión
from modules.config import hoy  # noqa: E402
a = vista("calendario").run()
clave = f"cal_{hoy().isoformat()}"
check("el día entrenado (hoy) es un botón habilitado", any(b.key == clave and not b.disabled for b in a.button))
check("un día sin entreno está deshabilitado", any(b.key and b.key.startswith("cal_") and b.disabled for b in a.button))
a.button(key=clave).click().run()
check("tocar el día despliega la sesión sin errores", limpio(a) and any("series" in m.value for m in a.markdown), str(a.exception))
check("aparece el detalle de ejercicios", len(a.subheader) >= 1)

# ------------------------------------------- 4. análisis con datos reales
CUR.execute("select ejercicio, peso_kg, reps from v_prs"); prs = CUR.fetchall()
check("PR correcto (62.5×6) y sin contar el calentamiento", any(float(p[1]) == 62.5 and p[2] == 6 for p in prs), str(prs))
a = vista("progreso").run()
check("progreso dibuja gráfica y tabla", any(type(x).__name__ == "UnknownElement" for x in a.main) and len(a.dataframe) >= 1)

# ------------------------------------------- 5. plantillas y catálogo
a = vista("plantillas", editor=True).run()
check("plantillas del usuario migradas visibles", "Dia de empujes" in a.selectbox(key="pl_sel").options)
a.selectbox(key="pl_sel").set_value("Dia de empujes").run()
CUR.execute("select ejercicio_id from plantilla_ejercicios pe join plantillas p on p.id=pe.plantilla_id where p.nombre='Dia de empujes' order by orden")
antes = [r[0] for r in CUR.fetchall()]
check("la lista muestra los ejercicios de la plantilla", len([b for b in a.button if b.key and b.key.startswith("up_")]) == len(antes), f"{len(antes)} ejercicios")
a.button(key="dn_0").click().run()                       # baja el primero
check("aparece aviso de cambios sin guardar", any("sin guardar" in w.value for w in a.warning))
a.button(key="rm_2").click().run()                       # quita el tercero
[b for b in a.button if "Guardar" in b.label][0].click().run()
CUR.execute("select ejercicio_id from plantilla_ejercicios pe join plantillas p on p.id=pe.plantilla_id where p.nombre='Dia de empujes' order by orden")
despues = [r[0] for r in CUR.fetchall()]
esperado = [antes[1], antes[0]] + antes[3:]
check("reordenar y quitar se guarda en la BD", despues == esperado, f"{len(antes)}->{len(despues)}")
a = vista("catalogo", editor=True).run()
check("pantalla catálogo sin excepciones", limpio(a), str((a.exception, [e.value[:160] for e in a.error]))[:300])

print(f"\n{sum(resultados)}/{len(resultados)} comprobaciones correctas")
sys.exit(0 if all(resultados) else 1)

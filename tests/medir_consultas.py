"""Cuenta las consultas a la BD por interacción en la pantalla Entrenar (cada una = 1 viaje de red)."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "tests")]
src = open(RAIZ / "tests" / "test_app.py", encoding="utf-8").read().split("# ---------------------------------------------------------------- 1. acceso")[0]
exec(src)  # levanta BD temporal y define app()/vista()

import modules.db as db  # noqa: E402

LEC, ESC = [], []
_orig_q, _orig_e = db._consultar, db.escribir


def _q(sql, params):
    LEC.append(sql)
    return _orig_q(sql, params)


def _e(fn, limpiar=db.CACHES):
    ESC.append(1)
    return _orig_e(fn, limpiar)


db._consultar = _q
import modules.repo as repo  # noqa: E402
repo.escribir = _e


def paso(nombre, fn):
    LEC.clear(); ESC.clear()
    fn()
    print(f"{nombre:<34} {len(LEC):>2} lecturas a la BD | {len(ESC)} escritura(s)")
    return len(LEC) + len(ESC)


CUR.execute("select id from plantillas order by nombre limit 1"); PID = CUR.fetchone()
at = vista("entrenar", editor=True)
total = {}
total["abrir (sin sesión)"] = paso("abrir pantalla (sin sesión)", lambda: at.run())
at.selectbox[0].set_value("Dia de empujes").run()
total["empezar"] = paso("pulsar 'Empezar sesión'", lambda: ([b for b in at.button if "Empezar" in b.label][0].click().run()))
at = vista("entrenar", editor=True)
total["abrir con sesión"] = paso("abrir con sesión en curso", lambda: at.run())
CUR.execute("select pe.ejercicio_id from plantilla_ejercicios pe join plantillas p on p.id=pe.plantilla_id join sesiones s on s.plantilla=p.nombre where s.estado='en_curso' order by pe.orden limit 1")
EID = CUR.fetchone()[0]
total["elegir ejercicio"] = paso("elegir un ejercicio", lambda: at.selectbox(key="sel_plantilla").set_value(EID).run())
total["mas serie"] = paso("pulsar ➕ Serie", lambda: [b for b in at.button if "Serie" in b.label][0].click().run())
total["guardar"] = paso("pulsar 💾 Guardar", lambda: [b for b in at.button if "Guardar" in b.label][0].click().run())
print("\nTOTAL viajes a la BD en el flujo:", sum(total.values()))

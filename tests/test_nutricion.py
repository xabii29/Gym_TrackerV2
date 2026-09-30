"""Pruebas unitarias de la lógica de fases (fechas exactas)."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.nutricion import kcal_de_macros, progreso_fase, semanas_por_tipo  # noqa: E402

ok = True


def check(nombre, cond):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + nombre)


ini = date(2026, 9, 1)
p = progreso_fase(ini, 12, date(2026, 9, 29))          # 28 días = 4 semanas completas
check("semana actual = 5 y 4 completadas", (p["semana_actual"], p["completadas"]) == (5, 4))
check("faltan 8 semanas y fin estimado 24/11", (p["semanas_restantes"], p["fin_estimado"]) == (8, date(2026, 11, 24)))
check("estado en_curso", p["estado"] == "en_curso")
check("día 0: semana 1, 0 completadas", progreso_fase(ini, 12, ini)["semana_actual"] == 1)
check("día 7 ya es la semana 2", progreso_fase(ini, 12, date(2026, 9, 8))["semana_actual"] == 2)
check("a 5 días del fin: por_terminar", progreso_fase(ini, 4, date(2026, 9, 24))["estado"] == "por_terminar")
check("justo en la fecha de fin: termina_hoy", progreso_fase(ini, 4, date(2026, 9, 29))["estado"] == "termina_hoy")
v = progreso_fase(ini, 4, date(2026, 10, 9))
check("pasado del plazo: vencido, 10 días", v["estado"] == "vencido" and v["dias_restantes"] == -10)
check("sin semanas planeadas no hay recordatorio", "estado" not in progreso_fase(ini, None, date(2026, 9, 29)))
check("fecha de inicio futura", progreso_fase(date(2026, 10, 1), 8, date(2026, 9, 29))["futuro"])
check("la fracción no pasa de 100 %", progreso_fase(ini, 2, date(2027, 1, 1))["fraccion"] == 1.0)

fases = [dict(tipo="bulk", inicio=date(2026, 1, 1), fin=date(2026, 3, 1)),
         dict(tipo="recomp", inicio=date(2026, 3, 1), fin=None)]
s = semanas_por_tipo(fases, date(2026, 1, 1), date(2026, 4, 12))
check("bulk = 59 días (8.4 sem) y recomp = 42 días (6 sem)", abs(s["bulk"] - 59 / 7) < 1e-9 and abs(s["recomp"] - 6) < 1e-9)
s2 = semanas_por_tipo(fases, date(2026, 2, 1), date(2026, 3, 15))       # ventana que recorta ambas fases
check("la ventana recorta las fases", abs(s2["bulk"] - 28 / 7) < 1e-9 and abs(s2["recomp"] - 14 / 7) < 1e-9)
check("fase fuera de la ventana no cuenta", "bulk" not in semanas_por_tipo(fases, date(2026, 5, 1), date(2026, 6, 1)))
check("kcal de macros: 180P/250C/70G = 2350", kcal_de_macros(180, 250, 70) == 2350)
import numpy as np  # noqa: E402
check("acepta numpy.int64 (lo que devuelve pandas)", progreso_fase(ini, np.int64(12), date(2026, 9, 29))["semanas_restantes"] == 8)
check("NaN de pandas = sin plazo", "estado" not in progreso_fase(ini, float("nan"), date(2026, 9, 29)))
check("0 semanas = sin plazo", "estado" not in progreso_fase(ini, 0, date(2026, 9, 29)))
sys.exit(0 if ok else 1)

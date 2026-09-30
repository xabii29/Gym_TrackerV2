"""Consultas y escrituras de Gym Tracker V2 (todo el SQL de la app vive aquí)."""
import uuid
from datetime import date

import pandas as pd
from sqlalchemy import text

from modules.config import TZ
from modules.db import escribir, leer


# ---------------------------------------------------------------- catálogo
def catalogo() -> pd.DataFrame:
    return leer("""SELECT id, nombre, categoria, musculo_objetivo, equipo, revisar
                   FROM ejercicios WHERE activo ORDER BY nombre""", cache="catalogo")


def instrucciones(ejercicio_id: str) -> str | None:
    df = leer("SELECT instrucciones_es FROM ejercicios WHERE id = :i", {"i": ejercicio_id}, cache="catalogo")
    return None if df.empty or df.iloc[0, 0] is None or df.iloc[0, 0] != df.iloc[0, 0] else df.iloc[0, 0]


def recientes(n: int = 15) -> pd.DataFrame:
    return leer("""SELECT e.id, e.nombre, MAX(se.fecha) AS ultima
                   FROM series sr JOIN sesiones se ON se.id = sr.sesion_id
                   JOIN ejercicios e ON e.id = sr.ejercicio_id
                   GROUP BY e.id, e.nombre ORDER BY ultima DESC LIMIT :n""", {"n": n}, cache="historia")


def crear_ejercicio(nombre: str, categoria: str, musculo: str, equipo: str | None) -> str:
    id_ = "custom-" + uuid.uuid4().hex[:10]

    def _f(s):
        s.execute(text("""INSERT INTO ejercicios (id, nombre, categoria, musculo_objetivo, equipo, personalizado)
                          VALUES (:id, :n, :c, :m, :e, TRUE)"""),
                  {"id": id_, "n": nombre.strip(), "c": categoria, "m": musculo, "e": equipo})
    escribir(_f, limpiar=("catalogo", "general"))
    return id_


def renombrar_ejercicios(cambios: list[tuple[str, str]]):
    def _f(s):
        for id_, nombre in cambios:
            s.execute(text("UPDATE ejercicios SET nombre = :n, revisar = FALSE WHERE id = :i"),
                      {"n": nombre.strip(), "i": id_})
    escribir(_f, limpiar=("catalogo", "historia", "vivo", "general"))


# -------------------------------------------------------------- plantillas
def plantillas() -> pd.DataFrame:
    return leer("""SELECT p.id AS plantilla_id, p.nombre AS plantilla, pe.orden, e.id AS ejercicio_id,
                          e.nombre AS ejercicio
                   FROM plantillas p LEFT JOIN plantilla_ejercicios pe ON pe.plantilla_id = p.id
                   LEFT JOIN ejercicios e ON e.id = pe.ejercicio_id
                   ORDER BY p.nombre, pe.orden""", cache="catalogo")


def guardar_plantilla(nombre: str, ids: list[str], plantilla_id: int | None = None) -> int:
    def _f(s):
        pid = plantilla_id
        if pid is None:
            pid = s.execute(text("INSERT INTO plantillas (nombre) VALUES (:n) RETURNING id"),
                            {"n": nombre.strip()}).scalar()
        else:
            s.execute(text("UPDATE plantillas SET nombre = :n WHERE id = :i"), {"n": nombre.strip(), "i": pid})
            s.execute(text("DELETE FROM plantilla_ejercicios WHERE plantilla_id = :i"), {"i": pid})
        for orden, eid in enumerate(ids, start=1):
            s.execute(text("""INSERT INTO plantilla_ejercicios (plantilla_id, orden, ejercicio_id)
                              VALUES (:p, :o, :e)"""), {"p": pid, "o": orden, "e": eid})
        return pid
    return escribir(_f, limpiar=("catalogo",))


def eliminar_plantilla(plantilla_id: int):
    escribir(lambda s: s.execute(text("DELETE FROM plantillas WHERE id = :i"), {"i": plantilla_id}), limpiar=("catalogo",))


# ---------------------------------------------------------------- sesiones
def sesion_activa() -> pd.Series | None:
    df = leer("SELECT id, fecha, inicio, plantilla, notas FROM sesiones WHERE estado = 'en_curso' LIMIT 1", cache="sesion")
    return None if df.empty else df.iloc[0]


def iniciar_sesion(fecha: date, plantilla: str | None) -> int:
    def _f(s):
        return s.execute(text("""INSERT INTO sesiones (fecha, plantilla) VALUES (:f, :p)
                                 ON CONFLICT (estado) WHERE estado = 'en_curso' DO NOTHING RETURNING id"""),
                         {"f": fecha, "p": plantilla}).scalar()
    return escribir(_f, limpiar=("sesion", "vivo"))


def series_sesion(sesion_id: int) -> pd.DataFrame:
    return leer("""SELECT sr.ejercicio_id, e.nombre AS ejercicio, sr.orden, sr.serie, sr.reps, sr.peso_kg,
                          sr.rpe, sr.es_calentamiento, sr.nota
                   FROM series sr JOIN ejercicios e ON e.id = sr.ejercicio_id
                   WHERE sr.sesion_id = :s ORDER BY sr.orden, sr.serie""", {"s": sesion_id}, cache="vivo")


def ultima_vez(ejercicio_id: str, excluir_sesion: int) -> pd.DataFrame:
    return leer("""SELECT sr.serie, sr.peso_kg, sr.reps, sr.es_calentamiento, se.fecha
                   FROM series sr JOIN sesiones se ON se.id = sr.sesion_id
                   WHERE sr.ejercicio_id = :e
                     AND sr.sesion_id = (SELECT sr2.sesion_id FROM series sr2
                                         JOIN sesiones s2 ON s2.id = sr2.sesion_id
                                         WHERE sr2.ejercicio_id = :e AND sr2.sesion_id <> :x
                                         ORDER BY s2.fecha DESC, s2.id DESC LIMIT 1)
                   ORDER BY sr.serie""", {"e": ejercicio_id, "x": excluir_sesion}, cache="historia")


def guardar_ejercicio(sesion_id: int, ejercicio_id: str, filas: list[dict],
                      rpe: float | None = None, nota: str | None = None, historico: bool = False):
    """Reemplaza las series de un ejercicio en la sesión. UN solo viaje: la lógica vive en
    la función SQL guardar_ejercicio_sesion (sql/00_esquema.sql)."""
    nota = (nota or "").strip() or None

    def _f(s):
        s.execute(text("""SELECT guardar_ejercicio_sesion(CAST(:s AS int[]), 
                                                            CAST(:e AS text),
                                                            CAST(:reps AS int[]), 
                                                            CAST(:pesos AS numeric[]),
                                                            CAST(:cals AS boolean[]), 
                                                            CAST(:rpe AS numeric),
                                                            CAST(:nota AS text))"""),
                  {"s": sesion_id, "e": ejercicio_id, "rpe": rpe, "nota": nota,
                   "reps": [int(f["reps"]) for f in filas],
                   "pesos": [float(f["peso"]) for f in filas],
                   "cals": [bool(f["cal"]) for f in filas]})
    escribir(_f, limpiar=("vivo", "historia", "general") if historico else ("vivo",))


def eliminar_ejercicio_de_sesion(sesion_id: int, ejercicio_id: str, historico: bool = False):
    escribir(lambda s: s.execute(text("DELETE FROM series WHERE sesion_id = :s AND ejercicio_id = :e"),
                                 {"s": sesion_id, "e": ejercicio_id}),
             limpiar=("vivo", "historia", "general") if historico else ("vivo",))


def finalizar_sesion(sesion_id: int, notas: str | None):
    escribir(lambda s: s.execute(text("""UPDATE sesiones SET estado = 'terminada', fin = now(),
                                         notas = NULLIF(trim(:n), '') WHERE id = :i"""),
                                 {"n": notas or "", "i": sesion_id}), limpiar=("sesion", "vivo", "historia", "general"))


def descartar_sesion(sesion_id: int):
    escribir(lambda s: s.execute(text("DELETE FROM sesiones WHERE id = :i"), {"i": sesion_id}),
             limpiar=("sesion", "vivo", "historia", "general"))


def actualizar_sesion(sesion_id: int, fecha: date, notas: str | None):
    escribir(lambda s: s.execute(text("""UPDATE sesiones SET fecha = :f, notas = NULLIF(trim(:n), '')
                                         WHERE id = :i"""), {"f": fecha, "n": notas or "", "i": sesion_id}), limpiar=("vivo", "historia", "general"))


def sesiones_resumen(desde: date | None = None, hasta: date | None = None) -> pd.DataFrame:
    return leer("""SELECT * FROM v_sesiones_resumen
                   WHERE estado = 'terminada' AND fecha >= COALESCE(CAST(:d AS date), DATE '0001-01-01')
                     AND fecha <= COALESCE(CAST(:h AS date), DATE '9999-12-31')
                   ORDER BY fecha DESC, id DESC""", {"d": desde, "h": hasta})


def detalle_sesion(sesion_id: int) -> pd.DataFrame:
    return series_sesion(sesion_id)


# ---------------------------------------------------------------- análisis
def ejercicios_con_datos() -> pd.DataFrame:
    return leer("""SELECT ejercicio_id AS id, ejercicio AS nombre, COUNT(DISTINCT sesion_id) AS sesiones
                   FROM v_series_detalle GROUP BY ejercicio_id, ejercicio ORDER BY ejercicio""")


def progreso_ejercicio(ejercicio_id: str) -> pd.DataFrame:
    return leer("""SELECT d.fecha, d.sesion_id, MAX(d.peso_kg) AS peso_max, MAX(d.e1rm_kg) AS e1rm,
                          SUM(d.volumen_kg) AS volumen, MAX(d.reps) AS reps_max, COUNT(*) AS series,
                          MAX(se.notas) AS notas
                   FROM v_series_detalle d JOIN sesiones se ON se.id = d.sesion_id
                   WHERE d.ejercicio_id = :e GROUP BY d.fecha, d.sesion_id ORDER BY d.fecha, d.sesion_id""",
                {"e": ejercicio_id})


def prs() -> pd.DataFrame:
    return leer("SELECT * FROM v_prs ORDER BY categoria, ejercicio")


def prs_recientes(dias: int = 60) -> pd.DataFrame:
    return leer("""SELECT h.* FROM v_pr_historial h
                   WHERE h.fecha >= (now() AT TIME ZONE :tz)::date - CAST(:d AS int)
                     AND EXISTS (SELECT 1 FROM v_pr_historial x WHERE x.ejercicio_id = h.ejercicio_id AND x.fecha < h.fecha)
                   ORDER BY h.fecha DESC""", {"tz": TZ, "d": dias})


def pr_historial(ejercicio_id: str) -> pd.DataFrame:
    return leer("SELECT fecha, peso_kg, reps, e1rm_kg FROM v_pr_historial WHERE ejercicio_id = :e ORDER BY fecha DESC",
                {"e": ejercicio_id})


def volumen_semanal(desde: date) -> pd.DataFrame:
    return leer("""SELECT date_trunc('week', fecha)::date AS semana, categoria,
                          SUM(volumen_kg) AS volumen, COUNT(*) AS series, COUNT(DISTINCT fecha) AS dias
                   FROM v_series_detalle WHERE fecha >= :d GROUP BY 1, 2 ORDER BY 1, 2""", {"d": desde})


def fechas_entreno(desde: date, hasta: date) -> pd.DataFrame:
    return leer("""SELECT id, fecha FROM sesiones WHERE estado = 'terminada' AND fecha BETWEEN :d AND :h
                   ORDER BY fecha""", {"d": desde, "h": hasta})


def series_export() -> pd.DataFrame:
    return leer("""SELECT se.fecha, se.id AS sesion_id, se.plantilla, se.notas AS notas_sesion, sr.orden,
                          e.nombre AS ejercicio, e.categoria, sr.serie, sr.peso_kg, sr.reps, sr.rpe,
                          sr.es_calentamiento, sr.nota
                   FROM series sr JOIN sesiones se ON se.id = sr.sesion_id
                   JOIN ejercicios e ON e.id = sr.ejercicio_id
                   WHERE se.estado = 'terminada' ORDER BY se.fecha, se.id, sr.orden, sr.serie""", cache="general")


# ------------------------------------------------------------ peso corporal
def pesos_corporales() -> pd.DataFrame:
    return leer("SELECT fecha, peso_kg FROM peso_corporal ORDER BY fecha")


def guardar_peso(fecha: date, kg: float):
    escribir(lambda s: s.execute(text("""INSERT INTO peso_corporal (fecha, peso_kg) VALUES (:f, :k)
                                         ON CONFLICT (fecha) DO UPDATE SET peso_kg = EXCLUDED.peso_kg"""),
                                 {"f": fecha, "k": kg}), limpiar=("general",))

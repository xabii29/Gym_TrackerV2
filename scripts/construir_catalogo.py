"""Genera el catálogo v2 (CSV para revisión + SQL para PostgreSQL).

Uso:  python scripts/construir_catalogo.py
Entradas:  data/origen/*.json      Salidas: data/catalogo_es_v2.csv  y  sql/01..03_*.sql
"""
import csv
import json
import unicodedata
from pathlib import Path

from glosario import MUSCULOS_ES
from traductor import traducir

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "data" / "origen"
CHUNK_INSTR = 450


def norm(s: str) -> str:
    return " ".join(str(s).lower().split())


def q(v) -> str:
    """Literal SQL de texto (o NULL)."""
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def arr(vals) -> str:
    return "NULL" if not vals else "ARRAY[" + ",".join(q(v) for v in vals) + "]::text[]"


def cargar(nombre):
    with open(ORIGEN / nombre, encoding="utf-8") as f:
        return json.load(f)


def main():
    ex = cargar("exercises.json")
    aud = cargar("ejercicios_es_latam_auditada.json")
    old = cargar("simple_db_es.json")
    plant = cargar("plantillas.json")

    def col(d, campo):  # los json de pandas vienen como {campo: {"0": v}}
        return [d[campo][k] for k in sorted(d[campo], key=int)] if isinstance(d, dict) else [x[campo] for x in d]

    cat, tgt, sec, nom_aud = (col(aud, c) for c in ("category", "target", "secondary_muscles", "name"))
    nom_old = col(old, "name")
    assert len(ex) == len(cat) == len(nom_old), "los catálogos no están alineados"

    filas, vistos_en, usados = [], {}, {}
    for i, e in enumerate(ex):
        id_ = str(e.get("id", f"{i:04d}"))
        n_en = e["name"]
        es, ok, var = traducir(n_en, e["equipment"])
        if var:
            es += f" (variante {var})"
        activo, revisar = True, not ok
        if norm(n_en) in vistos_en:            # duplicado exacto del origen
            activo, es = False, f"{es} [duplicado {id_}]"
        else:
            vistos_en[norm(n_en)] = id_
        base = norm(es)
        if base in usados:                     # dos ejercicios distintos, mismo nombre
            usados[base] += 1
            es, revisar = f"{es} (variante {usados[base]})", True
        else:
            usados[base] = 1
        usados.setdefault(norm(es), 1)
        secs = []
        for m in (sec[i] or []):
            m = MUSCULOS_ES.get(m, m)
            if m not in secs and m != tgt[i]:
                secs.append(m)
        instr = (e.get("instructions") or {}).get("es")
        filas.append(dict(id=id_, nombre=es, nombre_en=n_en, categoria=cat[i], musculo=tgt[i],
                          secundarios=secs, equipo=e["equipment"], instr=instr,
                          activo=activo, revisar=revisar, antes=nom_old[i]))

    # ---- CSV de revisión
    with open(RAIZ / "data" / "catalogo_es_v2.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "nombre_anterior", "nombre_nuevo", "nombre_en", "equipo", "categoria",
                    "musculo", "revisar", "activo"])
        for r in filas:
            w.writerow([r["id"], r["antes"], r["nombre"], r["nombre_en"], r["equipo"], r["categoria"],
                        r["musculo"], "SI" if r["revisar"] else "", "" if r["activo"] else "NO"])

    # ---- 01 catálogo
    sql = ["-- 01: catálogo de ejercicios (generado por scripts/construir_catalogo.py)",
           "-- Idempotente: solo inserta ejercicios que no existan; NO pisa nombres corregidos a mano.", "BEGIN;"]
    for k in range(0, len(filas), 200):
        vals = ",\n".join(
            f"({q(r['id'])},{q(r['nombre'])},{q(r['nombre_en'])},{q(r['categoria'])},{q(r['musculo'])},"
            f"{arr(r['secundarios'])},{q(r['equipo'])},{'TRUE' if r['activo'] else 'FALSE'},"
            f"{'TRUE' if r['revisar'] else 'FALSE'})" for r in filas[k:k + 200])
        sql.append("INSERT INTO ejercicios (id,nombre,nombre_en,categoria,musculo_objetivo,"
                   "musculos_secundarios,equipo,activo,revisar) VALUES\n" + vals +
                   "\nON CONFLICT (id) DO NOTHING;")   # no pisa nombres que corrijas desde la app
    sql.append("COMMIT;")
    (RAIZ / "sql" / "01_catalogo_ejercicios.sql").write_text("\n".join(sql) + "\n", encoding="utf-8")

    # ---- 02 instrucciones (en trozos para poder pegarlas en el SQL Editor)
    con_instr = [r for r in filas if r["instr"]]
    for n, k in enumerate(range(0, len(con_instr), CHUNK_INSTR), start=1):
        vals = ",\n".join(f"({q(r['id'])},{q(r['instr'])})" for r in con_instr[k:k + CHUNK_INSTR])
        (RAIZ / "sql" / f"02_instrucciones_{n}.sql").write_text(
            f"-- 02.{n}: instrucciones en español (generado)\nUPDATE ejercicios e SET instrucciones_es = v.t\n"
            f"FROM (VALUES\n{vals}\n) AS v(id, t) WHERE e.id = v.id;\n", encoding="utf-8")

    # ---- 03 alias (nombres antiguos -> id) y plantillas iniciales
    alias = {}
    prim = {r["id"]: r for r in filas}
    for r, n_aud in zip(filas, nom_aud):
        if not r["activo"]:
            continue
        for a in {norm(r["antes"]), norm(n_aud)}:
            alias.setdefault(a, r["id"])       # ante colisión gana el primero
    por_nombre_en = {norm(r["nombre_en"]): r["id"] for r in filas if r["activo"]}
    s3 = ["-- 03: alias de nombres antiguos y plantillas iniciales (generado)", "BEGIN;"]
    items = sorted(alias.items())
    for k in range(0, len(items), 300):
        vals = ",".join(f"({q(a)},{q(i)})" for a, i in items[k:k + 300])
        s3.append(f"INSERT INTO ejercicios_alias (alias, ejercicio_id) VALUES {vals} ON CONFLICT (alias) DO NOTHING;")
    faltan = []
    for nombre_p, lista in plant.items():
        ids = []
        for n in lista:
            i = alias.get(norm(n))
            (ids.append(i) if i else faltan.append((nombre_p, n)))
        s3.append(f"INSERT INTO plantillas (nombre) VALUES ({q(nombre_p)}) ON CONFLICT (nombre) DO NOTHING;")
        for orden, i in enumerate(ids, start=1):
            s3.append(f"INSERT INTO plantilla_ejercicios (plantilla_id, orden, ejercicio_id) "
                      f"SELECT id, {orden}, {q(i)} FROM plantillas WHERE nombre = {q(nombre_p)} "
                      f"ON CONFLICT DO NOTHING;")
    s3.append("COMMIT;")
    (RAIZ / "sql" / "03_alias_y_plantillas.sql").write_text("\n".join(s3) + "\n", encoding="utf-8")

    rev = sum(r["revisar"] for r in filas)
    print(f"ejercicios: {len(filas)} | activos: {sum(r['activo'] for r in filas)} | a revisar: {rev} | "
          f"con instrucciones: {len(con_instr)} | alias: {len(alias)} | plantillas sin resolver: {faltan}")


if __name__ == "__main__":
    main()

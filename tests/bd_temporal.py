"""Levanta un PostgreSQL temporal (pgserver) con el esquema y catálogo v2 para pruebas."""
import pathlib
import tempfile

import psycopg2
import pgserver

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def iniciar(migrar_v1_demo: bool = False):
    srv = pgserver.get_server(tempfile.mkdtemp())
    uri = srv.get_uri()
    c = psycopg2.connect(uri)
    c.autocommit = True
    cur = c.cursor()
    for f in sorted((RAIZ / "sql").glob("*.sql")):
        if f.name.startswith("04_"):
            continue
        cur.execute(f.read_text(encoding="utf-8"))
    return srv, uri, c

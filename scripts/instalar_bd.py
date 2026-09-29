"""Aplica los archivos sql/*.sql en orden sobre tu PostgreSQL. Seguro de re-ejecutar.

Uso:
    python scripts/instalar_bd.py                 # 00..03 (instalación)
    python scripts/instalar_bd.py --migrar-v1     # además 04 (migra la tabla `registros`)
    python scripts/instalar_bd.py --url postgresql://...   # o usa .streamlit/secrets.toml
"""
import argparse
import re
import sys
import tomllib
from pathlib import Path

import psycopg2

RAIZ = Path(__file__).resolve().parent.parent


def url_desde_secrets() -> str:
    ruta = RAIZ / ".streamlit" / "secrets.toml"
    if not ruta.exists():
        sys.exit("No hay .streamlit/secrets.toml; usa --url.")
    conf = tomllib.loads(ruta.read_text(encoding="utf-8"))
    return conf["connections"]["postgresql"]["url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--migrar-v1", action="store_true")
    args = ap.parse_args()
    url = re.sub(r"^postgresql\+\w+://", "postgresql://", args.url or url_desde_secrets())

    archivos = sorted((RAIZ / "sql").glob("*.sql"))
    if not args.migrar_v1:
        archivos = [a for a in archivos if not a.name.startswith("04_")]
    conn = psycopg2.connect(url)
    conn.autocommit = True
    with conn.cursor() as cur:
        for a in archivos:
            print(f"-> {a.name} ...", end=" ", flush=True)
            cur.execute(a.read_text(encoding="utf-8"))   # sin parámetros: los % del texto son seguros
            print("ok")
    conn.close()
    print("Base de datos lista.")


if __name__ == "__main__":
    main()

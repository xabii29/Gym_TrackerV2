"""La app debe funcionar sea cual sea el prefijo de la URL (postgres://, postgresql://, +psycopg, +psycopg2)."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(RAIZ), str(RAIZ / "tests")]
import bd_temporal  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

srv, URI, CON = bd_temporal.iniciar()
prefijo = sys.argv[1]                       # p. ej. postgresql+psycopg://
url = URI.replace("postgresql://", prefijo, 1)
d = Path.home() / ".streamlit"; d.mkdir(exist_ok=True)
(d / "secrets.toml").write_text(f'[connections.postgresql]\nurl = "{url}"\n[auth]\npassword = "x"\n')
at = AppTest.from_string(f"import sys; sys.path.insert(0, r'{RAIZ}')\nfrom views.resumen import render\nrender()", default_timeout=60).run()
errores = [e.value[:120] for e in at.error] + [str(e.message)[:120] for e in at.exception]
print(f"{prefijo:<28}", "OK" if not errores else f"FALLA -> {errores}")
sys.exit(1 if errores else 0)

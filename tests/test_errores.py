"""Los errores de conexión más comunes deben explicar qué hacer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.db import _error_amigable  # noqa: E402

casos = {
    "(psycopg2.OperationalError) could not translate host name \"db.x.supabase.co\" to address: No address associated with hostname": "pooler",
    "connection failed: Network is unreachable": "pooler",
    "FATAL: Tenant or user not found": "postgres.<ID",
    "FATAL: password authentication failed for user": "Contraseña",
    'relation "sesiones" does not exist': "instalar_bd",
    "algo inesperado": "No se pudo consultar",
}
ok = True
for err, esperado in casos.items():
    msg = _error_amigable(Exception(err))
    bien = esperado in msg
    ok &= bien
    print(("PASS " if bien else "FAIL ") + err[:60])
sys.exit(0 if ok else 1)

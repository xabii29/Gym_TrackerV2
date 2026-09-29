"""Configuración global de Gym Tracker V2."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

APP_NOMBRE = "Gym Tracker V2"
TZ = "America/Mexico_City"   # el servidor de Streamlit Cloud corre en UTC: SIEMPRE usar hoy()
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
EQUIPOS_ES = {
    "barbell": "Barra", "dumbbell": "Mancuernas", "cable": "Polea", "leverage machine": "Máquina",
    "smith machine": "Máquina Smith", "body weight": "Peso corporal", "band": "Banda elástica",
    "kettlebell": "Pesa rusa", "weighted": "Con lastre", "assisted": "Asistido", "ez barbell": "Barra Z",
    "stability ball": "Pelota de estabilidad", "medicine ball": "Balón medicinal", "roller": "Rodillo",
    "rope": "Cuerda", "sled machine": "Trineo", "olympic barbell": "Barra olímpica",
    "trap bar": "Barra hexagonal", "resistance band": "Banda elástica", "bosu ball": "Bosu",
    "hammer": "Máquina Hammer", "tire": "Llanta", "wheel roller": "Rueda abdominal",
}


def ahora() -> datetime:
    return datetime.now(ZoneInfo(TZ))


def hoy() -> date:
    return ahora().date()


def fmt_fecha(d) -> str:
    d = d if isinstance(d, date) else d.date()
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def fmt_kg(v) -> str:
    v = float(v)
    return f"{v:g}"

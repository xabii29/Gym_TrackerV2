"""Lógica pura de las fases de nutrición (sin Streamlit ni base de datos: fácil de probar)."""
from datetime import date, timedelta

TIPOS = {"recomp": "Recomposición", "bulk": "Bulk (volumen)", "cut": "Cut (definición)",
         "mantenimiento": "Mantenimiento"}
COLORES = {"recomp": "#28a745", "bulk": "#f59e0b", "cut": "#3b82f6", "mantenimiento": "#9ca3af"}


def progreso_fase(inicio: date, semanas: int | None, hoy: date) -> dict:
    """Dónde va un plan: semana actual, semanas completas, cuánto falta y si ya se pasó del plazo."""
    semanas = None if semanas is None or semanas != semanas else (int(semanas) or None)   # NaN/0 => sin plazo
    dias = (hoy - inicio).days
    res = {"dias": dias, "semana_actual": max(dias, 0) // 7 + 1, "completadas": max(dias, 0) // 7,
           "futuro": dias < 0, "planeadas": semanas}
    if semanas:
        fin = inicio + timedelta(weeks=semanas)
        restantes_dias = (fin - hoy).days
        res.update(fin_estimado=fin, dias_restantes=restantes_dias,
                   semanas_restantes=max(0, -(-restantes_dias // 7)),   # redondea hacia arriba
                   fraccion=min(1.0, max(0.0, dias / (semanas * 7))),
                   estado="vencido" if restantes_dias < 0 else "termina_hoy" if restantes_dias == 0
                   else "por_terminar" if restantes_dias <= 7 else "en_curso")
    return res


def semanas_por_tipo(fases: list[dict], desde: date, hasta: date) -> dict[str, float]:
    """Semanas pasadas en cada tipo de fase dentro de [desde, hasta]. fin=None => vigente hasta `hasta`."""
    total: dict[str, float] = {}
    for f in fases:
        ini = max(f["inicio"], desde)
        fin = min(f["fin"] or hasta, hasta)
        dias = max(0, (fin - ini).days)
        if dias:
            total[f["tipo"]] = total.get(f["tipo"], 0.0) + dias / 7
    return total


def kcal_de_macros(p: int, c: int, g: int) -> int:
    return 4 * p + 4 * c + 9 * g

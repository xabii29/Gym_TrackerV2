"""Reconstruye el nombre en español de un ejercicio a partir del nombre en inglés.

Regla de salida:  Movimiento [de objeto] [posición / agarre / variante] (equipo)
Ejemplo:          "dumbbell incline one arm fly"  ->  "Aperturas inclinadas a un brazo (mancuernas)"

Devuelve (nombre, ok). ok=False significa que quedó alguna palabra sin traducir o
que la estructura es ambigua: esos nombres se marcan `revisar` en la base de datos.
"""

import re
from dataclasses import dataclass

from glosario import (
    ADJETIVOS, CABEZAS, CABEZAS_OBJ, CONECTORES, EQUIPO_ES, FRASES, IGNORAR,
    NOMBRES, OBJETOS, OVERRIDES, PREFIJOS_EQUIPO,
)

# movimientos "genéricos" que admiten "de <músculo>" aunque estén en CABEZAS
GENERICAS = {"press", "row", "curl", "curls", "crunch", "crunches", "twist", "twists",
             "bridge", "swing", "hop", "hops", "jump", "jumps", "walk", "run", "bend",
             "bends", "snatch", "clean", "shrug", "pullover"}

# palabra de equipo que se descarta del cuerpo del nombre (ya va en el sufijo)
RAIZ_EQUIPO = {
    "barbell": {"barbell"}, "dumbbell": {"dumbbell", "dumbbells"}, "cable": {"cable"},
    "leverage machine": {"lever"}, "smith machine": {"smith"}, "kettlebell": {"kettlebell"},
    "ez barbell": {"ez"}, "olympic barbell": {"olympic"}, "hammer": {"hammer"},
}


@dataclass
class Item:
    tipo: str   # H h O N A V C U
    es: str
    genero: str = "m"
    obj: bool = False  # la cabeza admite "de <objeto>"


def _plural(adj: str) -> str:
    if adj.endswith(("a", "e", "o")):
        return adj + "s"
    return adj + "es"


def _concordar(adj: str, genero: str) -> str:
    """Concuerda un adjetivo con el género/número de la cabeza."""
    if " " in adj:
        return adj
    plural = genero.endswith("p")
    fem = genero.startswith("f")
    if adj.endswith("o"):
        base = adj[:-1] + ("a" if fem else "o")
        return base + ("s" if plural else "")
    return _plural(adj) if plural else adj


def _tokenizar(nombre: str) -> tuple[list[str], int | None]:
    s = nombre.lower().replace("°", " ")
    variante = None
    m = re.search(r"\bv\. ?(\d+)\b", s)
    if m:
        variante = int(m.group(1))
        s = s.replace(m.group(0), " ")
    s = re.sub(r"[(),/]", " ", s).replace("-", " ").replace("’", "'")
    return re.findall(r"[a-z0-9']+", s), variante


def _quitar_prefijo_equipo(tokens: list[str]) -> list[str]:
    cambio = True
    while cambio and tokens:
        cambio = False
        for patron in sorted(PREFIJOS_EQUIPO, key=len, reverse=True):
            n = len(patron)
            if tuple(tokens[:n]) == patron:
                tokens = tokens[n:]
                cambio = True
                break
    return tokens


def _clasificar(tokens: list[str], equipo: str) -> list[Item]:
    raiz = RAIZ_EQUIPO.get(equipo, set())
    items: list[Item] = []
    i = 0
    while i < len(tokens):
        hallado = None
        for largo in range(min(6, len(tokens) - i), 0, -1):
            clave = " ".join(tokens[i:i + largo])
            if clave in CABEZAS:
                es, g = CABEZAS[clave]
                hallado = Item("H", es, g, obj=clave in GENERICAS)
            elif clave in FRASES:
                hallado = Item("V", FRASES[clave])
            elif clave in CABEZAS_OBJ:
                es, g = CABEZAS_OBJ[clave]
                hallado = Item("H", es, g, obj=True)
            elif clave in ADJETIVOS and largo == 1:
                hallado = Item("A", ADJETIVOS[clave])
            elif clave in OBJETOS:
                hallado = Item("O", OBJETOS[clave])
            elif clave in NOMBRES:
                hallado = Item("N", NOMBRES[clave])
            elif clave in CONECTORES and largo == 1:
                hallado = Item("C", CONECTORES[clave])
            elif clave in IGNORAR and largo == 1:
                hallado = Item("X", "")
            if hallado:
                i += largo
                break
        if not hallado:
            tok = tokens[i]
            if tok in raiz:
                hallado = Item("X", "")
            elif tok.isdigit():
                hallado = Item("V", tok)
            else:
                hallado = Item("U", tok)
            i += 1
        if hallado.tipo != "X":
            items.append(hallado)
    return items


def _unir_objetos(objs: list[str]) -> str:
    return " y ".join(objs) if len(objs) <= 2 else ", ".join(objs[:-1]) + " y " + objs[-1]


def traducir(nombre_en: str, equipo: str) -> tuple[str, bool, int | None]:
    """Devuelve (nombre_es, ok, variante)."""
    clave = nombre_en.lower().strip()
    tokens, variante = _tokenizar(clave)
    sufijo = EQUIPO_ES.get(equipo)

    if clave in OVERRIDES:
        base = OVERRIDES[clave]
        return _armar(base, sufijo), True, variante

    tokens = _quitar_prefijo_equipo(tokens)
    items = _clasificar(tokens, equipo)
    if equipo == "weighted":
        items = [it for it in items if not (it.tipo == "A" and it.es == "con lastre")]

    idx_cabezas = [k for k, it in enumerate(items) if it.tipo == "H"]
    ok = not any(it.tipo == "U" for it in items)

    if not idx_cabezas:
        # sin movimiento reconocido: se deja en el orden original, para revisión
        texto = " ".join(it.es for it in items if it.es)
        return _armar(_cap(texto), sufijo), False, variante

    if len(idx_cabezas) > 1:
        ok = False
    hi = idx_cabezas[-1]
    cabeza = items[hi]

    # objetos inmediatamente antes de la cabeza ("triceps" + "extension")
    objs: list[str] = []
    usados = set()
    j = hi - 1
    if cabeza.obj:
        while j >= 0:
            if items[j].tipo == "O":
                objs.insert(0, items[j].es)
                usados.add(j)
                j -= 1
            elif (items[j].tipo == "C" and items[j].es == "y" and j - 1 >= 0
                  and items[j - 1].tipo == "O"):
                usados.add(j)
                j -= 1
            else:
                break

    partes = [cabeza.es]
    if objs:
        partes.append("de " + _unir_objetos(objs))

    antes, despues = [], []
    for k, it in enumerate(items):
        if k == hi or k in usados:
            continue
        (antes if k < hi else despues).append(it)

    def frase(it: Item, tras_conector: bool) -> str:
        if it.tipo == "A":
            return _concordar(it.es, cabeza.genero)
        if it.tipo == "O":
            return it.es if tras_conector else "de " + it.es
        if it.tipo == "N":
            return it.es if tras_conector else "con " + it.es
        if it.tipo == "H":
            return it.es.lower()
        return it.es

    for grupo in (antes, despues):
        tras = False
        for it in grupo:
            if it.tipo == "C":
                if it.es:
                    partes.append(it.es)
                tras = True
                continue
            if it.tipo in ("O", "N") and not tras and grupo is antes:
                partes.append(frase(it, False))
            else:
                partes.append(frase(it, tras))
            tras = False
    texto = " ".join(p for p in partes if p)
    return _armar(_cap(texto), sufijo), ok, variante


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _armar(base: str, sufijo: str | None) -> str:
    base = re.sub(r"\s+", " ", base).strip()
    return f"{base} ({sufijo})" if sufijo else base

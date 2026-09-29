"""Glosario inglés -> español para reconstruir los nombres del catálogo.

Tipos de entrada (los usa traductor.py):
  CABEZAS       movimiento ya armado:                ("Press de banca", "m")
  CABEZAS_OBJ   movimiento que admite objeto "de X": ("Extensión", "f")
  OBJETOS       músculo/objeto, va como "de <obj>":  "tríceps"
  NOMBRES       implemento de apoyo, va como "con":  "toalla"
  ADJETIVOS     concuerdan en género/número:         "sentado"
  FRASES        frases invariables:                  "de pie"
  CONECTORES    palabras de enlace
Género: m, f, mp (masc. plural), fp (fem. plural).
"""

# ------------------------------------------------------------------ cabezas
CABEZAS = {
    "bench press": ("Press de banca", "m"),
    "leg press": ("Prensa de piernas", "f"),
    "hack squat": ("Sentadilla hack", "f"),
    "pull up": ("Dominada", "f"), "chin up": ("Dominada supina", "f"),
    "push up": ("Flexión de brazos", "f"), "sit up": ("Abdominal", "m"),
    "v up": ("Abdominal en V", "m"), "step up": ("Subida al escalón", "f"),
    "butt ups": ("Elevación de glúteos", "f"),
    "dip": ("Fondos", "mp"), "dips": ("Fondos", "mp"),
    "deadlift": ("Peso muerto", "m"), "good morning": ("Buenos días", "mp"),
    "lat pulldown": ("Jalón dorsal", "m"), "pulldown": ("Jalón", "m"),
    "pushdown": ("Jalón de tríceps", "m"), "pullover": ("Pullover", "m"),
    "shrug": ("Encogimiento de hombros", "m"),
    "upright row": ("Remo al mentón", "m"), "face pull": ("Jalón a la cara", "m"),
    "hip thrust": ("Empuje de cadera", "m"), "glute bridge": ("Puente de glúteos", "m"),
    "glute kickback": ("Patada de glúteo", "f"),
    "triceps kickback": ("Patada de tríceps", "f"), "tricep kickback": ("Patada de tríceps", "f"),
    "kickback": ("Patada hacia atrás", "f"), "kickbacks": ("Patadas hacia atrás", "fp"),
    "skullcrusher": ("Rompecráneos", "mp"), "skull crusher": ("Rompecráneos", "mp"),
    "russian twist": ("Giro ruso", "m"), "side plank": ("Plancha lateral", "f"),
    "side bend": ("Flexión lateral", "f"), "wood chop": ("Leñador", "m"),
    "mountain climber": ("Escaladores", "mp"), "jumping jack": ("Saltos de tijera", "mp"),
    "jumping jacks": ("Saltos de tijera", "mp"), "jack knife": ("Navaja", "f"),
    "jackknife": ("Navaja", "f"), "burpee": ("Burpee", "m"), "burpees": ("Burpees", "mp"),
    "farmers walk": ("Caminata del granjero", "f"), "farmers carry": ("Caminata del granjero", "f"),
    "cossack squat": ("Sentadilla cosaca", "f"), "cossack squats": ("Sentadilla cosaca", "f"),
    "romanian deadlift": ("Peso muerto rumano", "m"),
    "stiff leg deadlift": ("Peso muerto con piernas rígidas", "m"),
    "stiff legged deadlift": ("Peso muerto con piernas rígidas", "m"),
    "sumo deadlift": ("Peso muerto sumo", "m"),
    "hyperextension": ("Hiperextensión", "f"), "back extension": ("Extensión de espalda", "f"),
    "hammer curl": ("Curl martillo", "m"), "preacher curl": ("Curl predicador", "m"),
    "concentration curl": ("Curl concentrado", "m"), "zottman curl": ("Curl Zottman", "m"),
    "spider curl": ("Curl araña", "m"), "drag curl": ("Curl arrastrado", "m"),
    "reverse curl": ("Curl inverso", "m"), "wrist curl": ("Curl de muñeca", "m"),
    "leg curl": ("Curl femoral", "m"), "leg extension": ("Extensión de piernas", "f"),
    "leg raise": ("Elevación de piernas", "f"), "knee raise": ("Elevación de rodillas", "f"),
    "calf raise": ("Elevación de pantorrillas", "f"), "calf raises": ("Elevación de pantorrillas", "f"),
    "lateral raise": ("Elevación lateral", "f"), "front raise": ("Elevación frontal", "f"),
    "rear delt raise": ("Elevación de deltoides posterior", "f"),
    "rear lateral raise": ("Elevación lateral posterior", "f"),
    "hip abduction": ("Abducción de cadera", "f"), "hip adduction": ("Aducción de cadera", "f"),
    "abduction": ("Abducción", "f"), "adduction": ("Aducción", "f"),
    "military press": ("Press militar", "m"), "overhead press": ("Press sobre la cabeza", "m"),
    "push press": ("Push press", "m"), "arnold press": ("Press Arnold", "m"),
    "jm press": ("Press JM", "m"), "floor press": ("Press en el suelo", "m"),
    "guillotine press": ("Press guillotina", "m"), "pallof press": ("Press Pallof", "m"),
    "landmine press": ("Press landmine", "m"), "reverse fly": ("Aperturas inversas", "fp"),
    "pec deck": ("Peck deck", "m"), "pec deck fly": ("Aperturas en peck deck", "fp"),
    "wheel rollerout": ("Rueda abdominal", "f"), "wheel roller out": ("Rueda abdominal", "f"),
    "ab wheel": ("Rueda abdominal", "f"), "rollerout": ("Rueda abdominal", "f"),
    "toe touch": ("Toque de puntas", "m"), "toe touches": ("Toque de puntas", "m"),
    "bicycle crunch": ("Crunch bicicleta", "m"), "air bike": ("Bicicleta en el aire", "f"),
    "dead bug": ("Bicho muerto", "m"), "bird dog": ("Perro de caza", "m"),
    "superman": ("Superman", "m"), "glute ham raise": ("Elevación glúteo-isquio", "f"),
    "reverse hyperextension": ("Hiperextensión inversa", "f"),
    "power clean": ("Cargada de potencia", "f"), "hang clean": ("Cargada colgante", "f"),
    "clean and jerk": ("Cargada y envión", "f"), "clean and press": ("Cargada y press", "f"),
    "high pull": ("Tirón alto", "m"), "turkish get up": ("Levantamiento turco", "m"),
    "bear crawl": ("Gateo de oso", "m"), "inchworm": ("Gusano", "m"),
    "wall sit": ("Sentadilla en pared", "f"),
    "lunge": ("Zancada", "f"), "lunges": ("Zancadas", "fp"),
    "split squat": ("Sentadilla dividida", "f"), "step lunge": ("Zancada con paso", "f"),
    "squat": ("Sentadilla", "f"), "squats": ("Sentadillas", "fp"),
    "goblet squat": ("Sentadilla goblet", "f"), "front squat": ("Sentadilla frontal", "f"),
    "overhead squat": ("Sentadilla sobre la cabeza", "f"), "pistol squat": ("Sentadilla pistola", "f"),
    "jump squat": ("Sentadilla con salto", "f"), "sissy squat": ("Sentadilla sissy", "f"),
    "zercher squat": ("Sentadilla Zercher", "f"), "thruster": ("Thruster", "m"),
    "plank": ("Plancha", "f"), "twist": ("Giro", "m"), "twists": ("Giros", "mp"),
    "crunch": ("Crunch", "m"), "crunches": ("Crunches", "mp"),
    "press": ("Press", "m"), "presses": ("Press", "mp"), "row": ("Remo", "m"),
    "curl": ("Curl", "m"), "curls": ("Curls", "mp"),
    "hop": ("Salto", "m"), "hops": ("Saltos", "mp"), "windmill": ("Molino", "m"),
    "butterfly": ("Mariposa", "f"), "cobra": ("Cobra", "f"), "bridge": ("Puente", "m"),
    "walk": ("Caminata", "f"), "walking": ("Caminata", "f"), "run": ("Carrera", "f"),
    "sprint": ("Sprint", "m"), "sprints": ("Sprints", "mp"), "skater": ("Patinador", "m"),
    "cycle": ("Ciclismo", "m"), "swing": ("Swing", "m"), "snatch": ("Arranque", "m"),
    "clean": ("Cargada", "f"), "jerk": ("Envión", "m"), "slam": ("Golpe al suelo", "m"),
    "throw": ("Lanzamiento", "m"), "carry": ("Caminata con carga", "f"),
    "pose": ("Postura", "f"), "saw": ("Sierra", "f"), "bend": ("Flexión", "f"),
    "bends": ("Flexiones", "fp"), "jump": ("Salto", "m"), "jumps": ("Saltos", "mp"),
    "row up": ("Remo", "m"),
}
# movimientos que aceptan objeto:  "triceps extension" -> "Extensión de tríceps"
CABEZAS_OBJ = {
    "extension": ("Extensión", "f"), "flexion": ("Flexión", "f"),
    "raise": ("Elevación", "f"), "raises": ("Elevación", "f"),
    "fly": ("Aperturas", "fp"), "flye": ("Aperturas", "fp"), "flyes": ("Aperturas", "fp"),
    "crossover": ("Cruce de poleas", "m"), "crossovers": ("Cruce de poleas", "m"),
    "stretch": ("Estiramiento", "m"), "kick": ("Patada", "f"), "kicks": ("Patadas", "fp"),
    "circles": ("Círculos", "mp"), "rotation": ("Rotación", "f"), "lift": ("Levantamiento", "m"),
    "thrust": ("Empuje", "m"), "thrusts": ("Empujes", "mp"), "tilt": ("Inclinación", "f"),
    "pass": ("Pase", "m"), "squeeze": ("Contracción", "f"), "roll": ("Rodamiento", "m"),
}

# ----------------------------------------------------------------- objetos
OBJETOS = {
    "triceps": "tríceps", "tricep": "tríceps", "biceps": "bíceps", "bicep": "bíceps",
    "leg": "piernas", "legs": "piernas", "arm": "brazos", "arms": "brazos",
    "calf": "pantorrillas", "calves": "pantorrillas", "knee": "rodillas", "knees": "rodillas",
    "hip": "cadera", "hips": "cadera", "shoulder": "hombros", "shoulders": "hombros",
    "wrist": "muñeca", "wrists": "muñecas", "ankle": "tobillo", "ankles": "tobillos",
    "back": "espalda", "chest": "pecho", "neck": "cuello", "head": "cabeza",
    "glute": "glúteos", "glutes": "glúteos", "gluteus": "glúteos",
    "hamstring": "isquiotibiales", "hamstrings": "isquiotibiales",
    "quad": "cuádriceps", "quads": "cuádriceps", "quadriceps": "cuádriceps",
    "lat": "dorsales", "lats": "dorsales", "delt": "deltoides", "delts": "deltoides",
    "deltoid": "deltoides", "trap": "trapecio", "traps": "trapecios",
    "abs": "abdomen", "abdominal": "abdomen", "ab": "abdomen", "oblique": "oblicuos",
    "forearm": "antebrazo", "finger": "dedos", "fingers": "dedos", "spine": "columna",
    "scapula": "escápula", "pec": "pecho", "pectoralis major": "pectoral mayor",
    "adductor": "aductores", "abductor": "abductores", "groin": "ingle",
    "piriformis": "piriforme", "rectus femoris": "recto femoral",
    "hip flexor": "flexores de cadera", "hip flexors": "flexores de cadera",
    "inner thigh": "muslo interno", "inner thighs": "muslo interno",
    "rear delt": "deltoides posterior", "rear delts": "deltoides posterior",
    "tibialis": "tibial", "peroneals": "peroneos", "feet": "pies", "foot": "pie",
    "hand": "manos", "hands": "manos", "body": "cuerpo", "elbow": "codo", "elbows": "codos",
    "toe": "punta del pie", "toes": "puntas de los pies", "shin": "espinilla",
    "femoral": "femoral", "flexor": "flexores", "muscle": "músculo", "pelvic": "pélvica",
}

# --------------------------------------------- sustantivos de apoyo ("con")
NOMBRES = {
    "towel": "toalla", "strap": "correa", "straps": "correas", "chair": "silla",
    "wall": "pared", "rope": "cuerda", "ropes": "cuerdas", "bench": "banco",
    "box": "cajón", "floor": "suelo", "bar": "barra", "step": "escalón",
    "handle": "agarre", "pad": "almohadilla", "support": "apoyo", "stirrups": "estribos",
    "platform": "plataforma", "ring": "anilla", "rings": "anillas", "band": "banda",
    "bands": "bandas", "rack": "rack", "pin": "pin", "cage": "jaula",
    "barbell": "barra", "dumbbell": "mancuerna", "dumbbells": "mancuernas",
    "kettlebell": "pesa rusa", "gripper": "pinza de agarre", "staircase": "escalera",
    "attachment": "accesorio", "bars": "barras", "treadmill": "caminadora",
    "arm blaster": "arm blaster", "v bar": "barra en V", "sz bar": "barra Z",
    "ez bar": "barra Z", "pro lat bar": "barra dorsal", "tennis ball": "pelota de tenis",
    "medicine ball": "balón medicinal", "stability ball": "pelota de estabilidad",
    "exercise ball": "pelota de estabilidad", "bosu ball": "Bosu", "ball": "pelota",
    "swiss ball": "pelota de estabilidad", "roller": "rodillo", "wheel": "rueda",
    "bike": "bicicleta", "machine": "máquina", "equipment": "equipo", "tire": "llanta",
    "sled": "trineo", "pulley": "polea", "cable": "polea", "battling ropes": "cuerdas de batalla",
    "landmine": "landmine",
}

# ----------------------------------------------------------- modificadores
ADJETIVOS = {  # concuerdan con el género de la cabeza
    "seated": "sentado", "sitted": "sentado", "lying": "acostado", "incline": "inclinado",
    "decline": "declinado", "flat": "plano", "alternate": "alterno", "alternating": "alterno",
    "reverse": "inverso", "reversed": "inverso", "revers": "inverso",
    "front": "frontal", "lateral": "lateral", "rear": "posterior", "wide": "amplio",
    "close": "cerrado", "narrow": "estrecho", "closer": "más cerrado", "high": "alto",
    "low": "bajo", "hanging": "colgado", "hang": "colgado", "assisted": "asistido",
    "double": "doble", "full": "completo", "half": "medio", "isometric": "isométrico",
    "straight": "recto", "elevated": "elevado", "raised": "elevado", "extended": "extendido",
    "twisted": "con giro", "supported": "con apoyo", "suspended": "suspendido",
    "inverted": "invertido", "vertical": "vertical", "horizontal": "horizontal",
    "diagonal": "diagonal", "dynamic": "dinámico", "negative": "negativo",
    "explosive": "explosivo", "unilateral": "unilateral", "modified": "modificado",
    "basic": "básico", "advanced": "avanzado", "intermediate": "intermedio", "deep": "profundo",
    "short": "corto", "quarter": "de un cuarto", "pronated": "prono", "supinated": "supino",
    "circular": "circular", "rotary": "rotatorio", "rotational": "rotacional",
    "romanian": "rumano", "sumo": "sumo", "fixed": "fijo", "outstretched": "con brazos extendidos",
    "cambered": "curvo", "angled": "angulado", "kneeling": "de rodillas", "standing": "de pie",
    "prone": "boca abajo", "supine": "boca arriba", "bent": "flexionado", "left": "izquierdo",
    "forward": "hacia adelante", "backward": "hacia atrás", "upward": "hacia arriba",
    "single": "a una mano", "multiple": "múltiple", "mixed": "mixto", "big": "grande",
    "plyo": "pliométrico", "outside": "exterior", "inside": "interior", "outer": "exterior",
    "inner": "interno", "upper": "superior", "lower": "inferior", "middle": "medio",
    "posterior": "posterior", "external": "externo", "internal": "interno",
    "lean": "inclinado", "twisting": "con giro", "weighted": "con lastre",
    "wall": "en pared", "pyramid": "piramidal", "figure": "", "sprint": "de sprint",
}
FRASES = {  # invariables
    "one arm": "a un brazo", "single arm": "a un brazo", "one hand": "a una mano",
    "one leg": "a una pierna", "single leg": "a una pierna", "two arm": "a dos brazos",
    "two legs": "a dos piernas", "one legged": "a una pierna", "single legged": "a una pierna",
    "bent over": "inclinado hacia adelante", "bent knee": "con rodillas flexionadas",
    "bent knees": "con rodillas flexionadas", "knees bent": "con rodillas flexionadas",
    "bent arm": "con brazos flexionados", "straight arm": "con brazos rectos",
    "arms straight": "con brazos rectos", "leg straight": "con piernas rectas",
    "legs up": "con piernas arriba", "side lying": "acostado de lado",
    "side pov": "vista lateral", "back pov": "vista posterior",
    "reverse grip": "con agarre inverso", "close grip": "con agarre cerrado",
    "wide grip": "con agarre amplio", "narrow grip": "con agarre estrecho",
    "neutral grip": "con agarre neutro", "parallel grip": "con agarre paralelo",
    "narrow parallel grip": "con agarre paralelo estrecho", "clean grip": "con agarre de cargada",
    "underhand": "con agarre supino", "overhand": "con agarre prono", "mixed grip": "con agarre mixto",
    "palms up": "con palmas arriba", "palms down": "con palmas abajo", "palm up": "con palma arriba",
    "palms": "con palmas", "palm": "con palma",
    "gripless": "sin agarre", "hands overhead": "con manos sobre la cabeza",
    "overhead": "sobre la cabeza", "behind head": "detrás de la cabeza",
    "behind the head": "detrás de la cabeza", "behind back": "detrás de la espalda",
    "full range hands behind head": "con rango completo y manos detrás de la cabeza",
    "on knees": "de rodillas", "on knee": "sobre una rodilla", "on hip": "sobre la cadera",
    "on floor": "en el suelo", "on bench": "en banco", "on box": "en cajón", "on bar": "en barra",
    "on vertical bar": "en barra vertical", "on parallel bars": "en barras paralelas",
    "on a staircase": "en escalera", "on stability ball": "sobre pelota de estabilidad",
    "on exercise ball": "sobre pelota de estabilidad", "on a dumbbell": "sobre una mancuerna",
    "over incline bench": "sobre banco inclinado", "between benches": "entre bancos",
    "bench support": "con apoyo en banco", "support head": "con apoyo de cabeza",
    "with support": "con apoyo", "with towel": "con toalla", "with rope": "con cuerda",
    "with rope attachment": "con cuerda", "rope attachment": "con cuerda",
    "with arm blaster": "con arm blaster", "with band": "con banda", "with strap": "con correa",
    "with barbell": "con barra", "with medicine ball": "con balón medicinal",
    "v bar": "con barra en V", "sz bar": "con barra Z", "pro lat bar": "con barra dorsal",
    "on pull up cable machine": "en máquina de polea",
    "on dip pull up cage": "en jaula de fondos y dominadas",
    "tennis ball between ankles": "con pelota de tenis entre los tobillos",
    "tennis ball between knees": "con pelota de tenis entre las rodillas",
    "band under both legs": "con banda bajo ambas piernas", "cross body": "cruzado",
    "across face": "cruzando la cara", "chest pad": "con apoyo de pecho",
    "bench leg": "con pierna en banco", "squat style": "estilo sentadilla",
    "up down": "arriba y abajo", "stork stance": "con postura de cigüeña",
    "wide stance": "con postura amplia", "sumo stance": "con postura sumo",
    "45": "a 45°", "180": "de 180°", "360": "de 360°",
}
CONECTORES = {
    "with": "con", "on": "en", "over": "sobre", "to": "a", "behind": "detrás de",
    "from": "desde", "in": "en", "against": "contra", "between": "entre", "and": "y",
    "of": "de", "through": "a través de", "into": "hacia", "above": "sobre",
    "across": "a través de", "around": "alrededor de", "off": "fuera de", "under": "bajo",
    "out": "hacia afuera", "the": "", "a": "", "at": "en", "up": "arriba", "down": "abajo",
    "both": "ambos",
}
IGNORAR = {"male", "female", "exercise", "v", "pov", "variation", "style", "position",
           "sequence", "range", "reps", "get", "equipment"}

# ----------------------------------------------------- equipo (sufijo del nombre)
EQUIPO_ES = {
    "barbell": "barra", "dumbbell": "mancuernas", "cable": "polea",
    "leverage machine": "máquina", "smith machine": "máquina Smith",
    "ez barbell": "barra Z", "olympic barbell": "barra olímpica",
    "trap bar": "barra hexagonal", "band": "banda elástica",
    "resistance band": "banda elástica", "kettlebell": "pesa rusa",
    "medicine ball": "balón medicinal", "stability ball": "pelota de estabilidad",
    "bosu ball": "Bosu", "roller": "rodillo", "rope": "cuerda",
    "sled machine": "trineo", "tire": "llanta", "wheel roller": "rueda abdominal",
    "stationary bike": "bicicleta estática", "elliptical machine": "elíptica",
    "skierg machine": "SkiErg", "stepmill machine": "escaladora",
    "upper body ergometer": "ergómetro de brazos", "hammer": "máquina Hammer",
    "weighted": "con lastre", "assisted": None, "body weight": None,
}
# palabras al inicio del nombre inglés que ya quedan representadas en el sufijo de equipo
PREFIJOS_EQUIPO = [
    ("olympic", "barbell"), ("ez", "barbell"), ("ez", "bar"), ("sz", "bar"),
    ("smith", "machine"), ("stability", "ball"), ("exercise", "ball"), ("medicine", "ball"),
    ("bosu", "ball"), ("resistance", "band"), ("trap", "bar"), ("hammer", "strength"),
    ("dumbbell",), ("dumbbells",), ("barbell",), ("cable",), ("lever",), ("band",),
    ("smith",), ("kettlebell",), ("sled",), ("bodyweight",), ("weighted",), ("roller",),
    ("rope",), ("tire",), ("hammer",),
]

# ------------------------------------------------- músculos secundarios
MUSCULOS_ES = {
    "back": "espalda", "core": "core", "brachialis": "braquial", "feet": "pies",
    "grip muscles": "músculos del agarre", "groin": "ingle", "inner thighs": "muslo interno",
    "lower abs": "abdomen inferior", "rear deltoids": "deltoides posterior",
    "shins": "espinillas", "sternocleidomastoid": "esternocleidomastoideo",
    "upper chest": "pecho superior", "trapecios": "trapecio", "dorsal ancho": "dorsales",
    "parte superior de la espalda": "espalda alta",
}

# ---------------------------------------- traducciones manuales (nombre EN -> ES)
OVERRIDES = {
    "barbell lying back of the head tricep extension": "Extensión de tríceps tras nuca acostado",
    "cable pulldown": "Jalón al pecho",
    "cable pushdown": "Jalón de tríceps",
    "assisted pull-up": "Dominada asistida",
}

# ---- ampliaciones tras medir cobertura
ADJETIVOS.update({
    "side": "lateral", "inverse": "inverso", "neutral": "neutro", "parallel": "paralelo",
    "cross": "cruzado", "stationary": "estacionario", "archer": "arquero", "pike": "en pica",
    "frog": "rana", "donkey": "de burro", "cuban": "cubano", "rocking": "con balanceo",
    "tuck": "agrupado", "self": "autoasistido", "pronation": "con pronación",
    "supination": "con supinación", "clasped": "con manos entrelazadas",
})
CABEZAS.update({
    "bench dip": ("Fondos en banco", "mp"), "chest dip": ("Fondos de pecho", "mp"),
    "tricep dip": ("Fondos de tríceps", "mp"), "triceps dip": ("Fondos de tríceps", "mp"),
    "french press": ("Press francés", "m"),
})
CABEZAS_OBJ.update({
    "push": ("Empuje", "m"), "pull": ("Jalón", "m"), "tap": ("Toque", "m"),
    "reach": ("Alcance", "m"), "march": ("Marcha", "f"), "hug": ("Abrazo", "m"),
})
FRASES.update({
    "high bar": "con barra alta", "low bar": "con barra baja", "inverse grip": "con agarre inverso",
    "grip": "de agarre", "wall": "en la pared",
})
IGNORAR.update({"hammer", "lever", "machine", "trainer"})

import time
import random
import logging

# from .admin_report_functions import *
from otree.api import *
from otree import settings
import math
from statistics import mean, stdev
from decimal import Decimal

# ================== Tratamientos + IAT randomization helpers ==================

# 3 tratamientos idénticos (por ahora)
TREATMENTS = ['T1', 'T2', 'T3']

# === Catálogo de IATs disponibles (usa tus clases reales) =====================
# kind: 'st' = single-target; '2cat' = dos categorías
# === Catálogo de IATs por clave, sin referenciar clases. ===
IAT_LIBRARY = {
    'MinnoIAT2Cats':   {'kind': '2cat'},
    'MinnoIAT2CatsA':  {'kind': '2cat'},
    'MinnoIAT2CatsB':  {'kind': '2cat'},
    'StiatSexuality':  {'kind': 'st'},
    'StiatDisability': {'kind': 'st'},
    'StiatMinno':      {'kind': 'st'},
}

# comentarios.
doc = """
Implicit Association Test, draft
"""
from statistics import mean, stdev

from typing import Optional, List, Dict, Tuple, Any
from statistics import mean, stdev

# ========= Minno IAT (2 categorías) – Parser + D-score =========
import csv, io
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Tuple

MINNO_IAT_MIN_RT = 0.300
MINNO_IAT_MAX_RT = 10.000
MINNO_IAT_FAST_PROP = 0.10
MINNO_IAT_ERR_PENALTY = 0.600  # 600 ms

def _min2_to_bool(x):
    if isinstance(x, bool): return x
    if x is None: return None
    s = str(x).strip().lower()
    if s in {"1","true","t","yes","y","si","sí"}: return True
    if s in {"0","false","f","no","n"}: return False
    return None

def parse_minno_iat_csv(csv_text: str) -> List[Dict[str, Any]]:
    """
    Devuelve dicts con: block(int), rt(segundos), correct(bool)
    Soporta encabezados comunes de Minno/Qualtrics.
    """
    rows: List[Dict[str, Any]] = []
    if not csv_text:
        return rows
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    for r in reader:
        blk_raw = r.get('block') or r.get('Block') or r.get('blockNum') or r.get('phase')
        try:
            block = int(str(blk_raw).strip())
        except:
            continue

        lat_raw = r.get('latency') or r.get('rt') or r.get('latency_ms') or r.get('responseLatency')
        if lat_raw is None:
            continue
        try:
            rt = float(lat_raw)
        except:
            continue
        # Heurística ms→s
        if rt > 50:
            rt = rt / 1000.0

        correct = _min2_to_bool(r.get('correct'))
        if correct is None:
            err = r.get('error') or r.get('Error')
            if err is not None:
                correct = not _min2_to_bool(err)
        if correct is None:
            correct = False

        rows.append(dict(block=block, rt=rt, correct=bool(correct)))
    return rows

def _minno_iat_reason_from_meta(d: Optional[float], meta: Dict[str, Any]) -> str:
    if d is not None:
        return ''
    if meta.get('excluded_fast_prop'):
        return 'Excluido: >10% de RT <300 ms'
    if meta.get('sd36') == 0 or meta.get('sd47') == 0 or meta.get('sd_pooled') == 0:
        return 'Excluido: SD=0'
    if meta.get('n3',0) < 2 or meta.get('n6',0) < 2 or meta.get('n4',0) < 2 or meta.get('n7',0) < 2:
        return f"Excluido: pocos ensayos (b3={meta.get('n3',0)}, b4={meta.get('n4',0)}, b6={meta.get('n6',0)}, b7={meta.get('n7',0)})"
    return 'Excluido: sin datos válidos'

def compute_minno_iat_d(
    trials: List[Dict[str, Any]],
    compat_blocks: Tuple[int,int] = (3,4),
    incompat_blocks: Tuple[int,int] = (6,7),
    *,
    error_penalty_s: float = MINNO_IAT_ERR_PENALTY,
    min_rt_s: float = MINNO_IAT_MIN_RT,
    max_rt_s: float = MINNO_IAT_MAX_RT,
    max_fast_prop: float = MINNO_IAT_FAST_PROP,
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Implementación estilo Greenwald (2003) para IAT de 7 bloques:
      - chequeo de rápidos <300ms (>10% ⇒ exclusión)
      - filtra RT fuera de [0.3, 10] s
      - penaliza errores sumando 600 ms
      - D = promedio( (mean6-mean3)/sd(3∪6), (mean7-mean4)/sd(4∪7) )
    Devuelve (D, meta)
    """
    meta: Dict[str, Any] = {
        "n_total": len(trials),
        "n_fast_300ms": 0,
        "excluded_fast_prop": False,
        "n3": 0, "n4": 0, "n6": 0, "n7": 0,
        "sd36": None, "sd47": None, "sd_pooled": None,
        "d36": None, "d47": None,
    }
    if not trials:
        return None, meta

    # 1) proporción <300ms en crudo (antes de filtrar max 10s)
    fast = [t for t in trials if t["rt"] < min_rt_s]
    meta["n_fast_300ms"] = len(fast)
    if meta["n_total"] > 0 and (len(fast) / meta["n_total"]) > max_fast_prop:
        meta["excluded_fast_prop"] = True
        return None, meta

    # 2) recolectar por bloque con penalización de error, dentro de [min,max]
    b3, b4, b6, b7 = [], [], [], []
    for t in trials:
        rt = t["rt"]
        if rt < min_rt_s or rt > max_rt_s:
            continue
        if not t["correct"]:
            rt += error_penalty_s
        if t["block"] == compat_blocks[0]:
            b3.append(rt)
        elif t["block"] == compat_blocks[1]:
            b4.append(rt)
        elif t["block"] == incompat_blocks[0]:
            b6.append(rt)
        elif t["block"] == incompat_blocks[1]:
            b7.append(rt)

    meta["n3"], meta["n4"], meta["n6"], meta["n7"] = len(b3), len(b4), len(b6), len(b7)

    # 3) D por pares disponibles
    dvals = []

    if len(b3) >= 2 and len(b6) >= 2:
        sd36 = stdev(b3 + b6)
        meta["sd36"] = sd36
        if sd36 > 0:
            meta["d36"] = (mean(b6) - mean(b3)) / sd36
            dvals.append(meta["d36"])

    if len(b4) >= 2 and len(b7) >= 2:
        sd47 = stdev(b4 + b7)
        meta["sd47"] = sd47
        if sd47 > 0:
            meta["d47"] = (mean(b7) - mean(b4)) / sd47
            dvals.append(meta["d47"])

    if not dvals:
        return None, meta

    d = float(round(sum(dvals) / len(dvals), 4))
    # sd_pooled informativa (no estrictamente necesaria)
    pooled = b3 + b4 + b6 + b7
    meta["sd_pooled"] = stdev(pooled) if len(pooled) >= 2 else 0.0
    return d, meta
# ========= Fin Minno IAT (2 categorías) =========


# === ST-IAT: parseo y D-score (MinnoJS) ======================================
import csv, io
from typing import Dict, Any, List, Tuple, Optional

# Por defecto, en el script de Project Implicit (qstiat6.js) los dos bloques críticos
# suelen ser: 3 = Target+Pleasant  (compatible) y 5 = Target+Unpleasant (incompatible).
# Si en el futuro cambias el orden, cambia estos IDs vía session.config['stiat_block_map']
DEFAULT_STIAT_BLOCK_MAP = {
    "compatible":   [3],
    "incompatible": [5],
}

def _to_bool(x):
    # Acepta 1/0, "true"/"false", "True"/"False", etc.
    if isinstance(x, bool):
        return x
    if x is None:
        return None
    s = str(x).strip().lower()
    if s in ("1","true","t","yes","y","si","sí"):
        return True
    if s in ("0","false","f","no","n"):
        return False
    return None

#funcion para el dscore de black. (o del primer st-iat).
def parse_minno_stiat_csv(csv_text: str) -> List[Dict[str, Any]]:
    """
    Devuelve una lista de dicts con los campos que necesitamos:
    block (int), rt (segundos), correct (bool).
    Soporta columnas comunes de Minno: 'block','latency','rt','correct','error'
    """
    rows = []
    if not csv_text:
        return rows
    f = io.StringIO(csv_text)
    reader = csv.DictReader(f)
    for r in reader:
        # --- block ---
        blk = r.get('block') or r.get('Block') or r.get('blockNum') or r.get('phase')
        try:
            block = int(str(blk).strip())
        except:
            # si no hay número, salta fila
            continue

        # --- latencia (ms o s) ---
        lat = r.get('latency') or r.get('rt') or r.get('latency_ms') or r.get('responseLatency')
        if lat is None:
            continue
        try:
            rt = float(lat)
        except:
            continue
        # Si parece estar en milisegundos, pásalo a segundos
        if rt > 50:  # heurística: >50 es casi seguro milisegundos
            rt = rt / 1000.0

        # --- correct / error ---
        correct = _to_bool(r.get('correct'))
        if correct is None:
            # Algunas hojas traen 'error' (1 = error)
            err = r.get('error') or r.get('Error')
            if err is not None:
                correct = not _to_bool(err)
        # Si sigue None, asumimos "desconocido"; los tratamos como incorrectos para ser conservadores
        if correct is None:
            correct = False

        rows.append(dict(block=block, rt=rt, correct=bool(correct)))
    return rows

def compute_stiat_d(
    trials: List[Dict[str, Any]],
    compat_blocks: List[int],
    incompat_blocks: List[int],
    *,
    error_penalty_s: float = 0.600,  # 600 ms
    min_rt_s: float = 0.300,
    max_rt_s: float = 10.000,
    max_fast_prop: float = 0.10,
) -> Tuple[Optional[float], Dict[str, Any]]:
    """
    Implementación estilo Greenwald et al. (2003) adaptada a ST-IAT:
      • descarta RT < 300 ms y > 10 s
      • exclusión si >10% de todos los trials (antes de descartar por >10s) < 300 ms
      • penaliza errores sumando 600 ms al RT del ensayo
      • D = (mean_incompat - mean_compat) / sd_pooled(trials de ambos bloques críticos)
    Devuelve (D, meta) donde meta trae contadores/flags útiles para depurar.
    """
    meta = {
        "n_total": len(trials),
        "n_fast_300ms": 0,
        "excluded_fast_prop": False,
        "n_compat_used": 0,
        "n_incompat_used": 0,
        "sd_pooled": None,
    }
    if not trials:
        return None, meta

    # Proporción <300 ms (con el conjunto completo que vino)
    fast = [t for t in trials if t["rt"] < min_rt_s]
    meta["n_fast_300ms"] = len(fast)
    if meta["n_total"] > 0 and (len(fast) / meta["n_total"]) > max_fast_prop:
        meta["excluded_fast_prop"] = True
        return None, meta  # recomendación habitual: excluir participante

    # Mantén solo bloque crítico y RT dentro de [300ms,10s]; aplica penalización a errores
    compat_rts = []
    incompat_rts = []
    for t in trials:
        if t["rt"] < min_rt_s or t["rt"] > max_rt_s:
            continue
        rt = t["rt"] + (error_penalty_s if not t["correct"] else 0.0)
        if t["block"] in compat_blocks:
            compat_rts.append(rt)
        elif t["block"] in incompat_blocks:
            incompat_rts.append(rt)

    meta["n_compat_used"] = len(compat_rts)
    meta["n_incompat_used"] = len(incompat_rts)

    if len(compat_rts) < 2 or len(incompat_rts) < 2:
        return None, meta

    pooled = compat_rts + incompat_rts
    sd = stdev(pooled) if len(pooled) >= 2 else 0.0
    meta["sd_pooled"] = sd

    if sd == 0:
        return None, meta

    d = (mean(incompat_rts) - mean(compat_rts)) / sd
    return float(round(d, 4)), meta

def classify_stiat_black(d: Optional[float]) -> str:
    """
    Umbrales habituales: |D| < .15 = Neutral; .15–.35 = Leve; .35–.65 = Moderada; >.65 = Fuerte.
    Para ST-IAT de 'Black people':
      D > 0 → Black+Pleasant más rápido (evaluación implícita positiva hacia Black)
      D < 0 → Black+Unpleasant más rápido (evaluación implícita negativa hacia Black)
    """
    if d is None:
        return "Sin clasificación"
    x = abs(d)
    if x < 0.15:
        return "Neutral"
    level = "Leve" if x <= 0.35 else ("Moderada" if x <= 0.65 else "Fuerte")
    return f"{level}: {'Black+positivo' if d>0 else 'Black+negativo'}"

def classify_stiat_sexuality(d: Optional[float]) -> str:
    """
    Umbrales habituales: |D| < .15 = Neutral; .15–.35 = Leve; .35–.65 = Moderada; >.65 = Fuerte.
    Para ST-IAT de 'Gay people':
      D > 0 → Gay+Pleasant más rápido (evaluación implícita positiva hacia Gay people)
      D < 0 → Gay+Unpleasant más rápido (evaluación implícita negativa hacia Gay people)
    """
    if d is None:
        return "Sin clasificación"
    x = abs(d)
    if x < 0.15:
        return "Neutral"
    level = "Leve" if x <= 0.35 else ("Moderada" if x <= 0.65 else "Fuerte")
    return f"{level}: {'Gay+positivo' if d > 0 else 'Gay+negativo'}"


def classify_stiat_disability(d: Optional[float]) -> str:
    """
    Umbrales habituales: |D| < .15 = Neutral; .15–.35 = Leve; .35–.65 = Moderada; >.65 = Fuerte.
    Para ST-IAT de 'People with disabilities':
      D > 0 → Disability+Pleasant más rápido (evaluación implícita positiva hacia People with disabilities)
      D < 0 → Disability+Unpleasant más rápido (evaluación implícita negativa hacia People with disabilities)
    """
    if d is None:
        return "Sin clasificación"
    x = abs(d)
    if x < 0.15:
        return "Neutral"
    level = "Leve" if x <= 0.35 else ("Moderada" if x <= 0.65 else "Fuerte")
    return f"{level}: {'Disability+positivo' if d > 0 else 'Disability+negativo'}"


# === Fin de tus funciones ===

def _block_map(session):
    # permite override desde SESSION_CONFIGS; si no, usa (3 compat, 5 incompat)
    return session.config.get('stiat_block_map', DEFAULT_STIAT_BLOCK_MAP)

def _save_stiat_csv(player: 'Player', raw_csv: str, target: str):
    rows = parse_minno_stiat_csv(raw_csv)
    bm = _block_map(player.session)
    d, meta = compute_stiat_d(rows, bm["compatible"], bm["incompatible"])
    if target == 'sex':
        player.stiat_sex_d = d
        player.stiat_sex_reason = _reason_from_meta(d, meta)
    elif target == 'dis':
        player.stiat_dis_d = d
        player.stiat_dis_reason = _reason_from_meta(d, meta)

def _reason_from_meta(d, meta) -> str:
    if d is not None: return ''
    if meta.get("excluded_fast_prop"): return 'Excluido: >10% RT <300ms'
    if meta.get("sd_pooled") == 0:     return 'Excluido: SD=0'
    if meta.get("n_compat_used",0) < 2 or meta.get("n_incompat_used",0) < 2:
        return f'Excluido: pocos ensayos (compat={meta.get("n_compat_used")}, incompat={meta.get("n_incompat_used")})'
    return 'Excluido: sin datos válidos'

# clase de Constants para definir las variables globales del experimento. 

class Constants(BaseConstants):
    name_in_url = 'iat'
    players_per_group = None
    num_rounds = 3  # <-- exactamente 6 rondas
    
    endowment = Decimal('100')  # Añadido para un posible juego del dictador


    ### variables para el cuestionario de comprensión

    # 1 ·  lista canónica para no repetir
    STAGES_CORRECT = [
        "Sociodemográfica",
        "Pruebas de asociación implícita",
        "Adivinas tus puntajes en las pruebas de la Etapa 2",
        "Rango aceptable de puntajes en las pruebas de la Etapa 2",
        "Qué información revelar en las decisiones de la Etapa 6",
        "Decisiones monetarias que pueden afectar a grupos de la Etapa 2",
    ]

    CORRECT_ANSWERS = dict(
        comp_q1='e',
        comp_q2='b',
        stage_order="\n".join(STAGES_CORRECT),  # tu BooleanField usa True/False
        comp_q4='c',
        comp_q5='d',
        comp_q6='c',
    )

    QUESTION_TEXT = dict(
        comp_q1=(
            '1. Supón que haces una prueba de asociación implícita que involucra a grupos A y B, en donde el grupo B es el grupo “base”. ¿Qué puntaje indicaría que tu sesgo implícito es igual al promedio de cientos de miles de participantes? ¿Qué puntaje indicaría que tu sesgo implícito favorece al grupo A más que el promedio de cientos de miles de participantes?'),
        comp_q2=(
            '2. ¿Cuáles son las dos características que hace que la Prueba de Asociación Implícita sea una manera robusta de medir sesgos que tal vez ni siquiera sabías que tenías?'),
        stage_order=(
            "3. Arrastra las etapas para ponerlas en el orden correcto:"
        ),
        comp_q4=('4. En la Etapa 5 (qué información revelar en la Etapa 6), ¿cómo tomas la decisión de qué se te revela en la Etapa 6?'),
        comp_q5=('5. Supón que nos indicas que quieres que en la Etapa 6 te revelemos la identidad de los grupos A y B, y que no te revelemos la identidad de los grupos C y D. ¿Qué haríamos en la práctica?'),
        comp_q6=('6. ¿Qué es lo que cada participantes debe adivinar sobre los miembros de su grupo en este experimento?'),
    )

    QUESTION_OPTIONS = dict(
        comp_q1=[
            ('a',
             'a) Un puntaje positivo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'),
            ('b',
             'b) Un puntaje positivo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje negativo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'),
            ('c',
             'c) Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje positivo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'),
            ('d',
             'd) Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje negativo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '),
            ('e',
             'e) Un puntaje negativo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'
             ),
            ('f',
             'f) Un puntaje negativo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje positivo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '
             ),
        ],

        comp_q2=[
            ('a',
             'a) Primero, hay una base de datos con cientos de miles de participantes que ya tomaron la prueba. Segundo, fue desarrollado por académicos.'),
            ('b',
             'b) Primero, está ligado a comportamientos relevantes en el mundo real. Segundo, es difícil de manipular ya que mide tu respuesta automática, sin que hayas tenido tiempo de pensar. '),
            ('c', 'c) Primero, no existen otras pruebas para medir sesgos. Segundo, es fácil de implementar.'),
        ],

        stage_order=[],

        comp_q4=[
            ('a',
             'a) Tomas una sola decisión sobre todos los grupos a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de todos los grupos cuando estés en la Etapa 6.'),
            ('b',
             'b) Tomas una decisión para cada grupo a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de cada grupo cuando estés en la Etapa 6.'),
            ('c',
             'c) Nos vas a decir si quieres que te revelemos la identidad de los grupos correspondientes a una decisión dependiendo de si tu puntaje en la prueba de asociación implícita cayó debajo, dentro o arriba del rango que consideras aceptable. '),
        ],

        comp_q5=[
            ('a', 'a) Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D.'),
            ('b', 'b) Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la dentidad de los grupos C y D.'),
            ('c', 'c) Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D. '),
            ('d',
             'd) Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D.'),
        ],
        comp_q6=[
            ('a',
             'a) Ninguna decisión involucra a los grupos de personas sobre las que te preguntamos en las pruebas de la Etapa 2, y sólo vamos a incluir decisiones que no afecten a las personas sobre las que te preguntamos en la Etapa 2. '),
            ('b',
             'b) No todas las decisiones involucran a los grupos de personas sobre las que te preguntamos en las pruebas de la Etapa 2, y es posible que incluyamos decisiones que no afecten a algunas de las personas sobre las que te preguntamos en la Etapa 2. '),
            ('c',
             'c) Todas las decisiones involucran a los grupos de personas sobre las que te preguntamos en las pruebas de la Etapa 2, y ninguna decisión van a incluir a grupos de personas sobre las que no te preguntamos en la Etapa 2. '),
        ],
    )

    CORRECT_EXPLANATIONS = dict(
        comp_q1='Tu puntaje se compara con los datos de Project Implicit, una base con cientos de miles de participantes. Una puntuación de cero representa el promedio de dicha base. La interpretación del puntaje depende de cuál de los dos grupos es el grupo "base" para fines de la comparación. En la pregunta, el grupo B es el grupo "base". Un puntaje positivo indicaría que, comparado a la base de datos de Project Implicit, el/la participante asocia con mayor facilidad a los del grupo B con los atributos positivos en comparación la asociación que hace con los del grupo A. Un puntaje negativo indica una asociación relativamente más fuerte de los del grupo A con atributos positivos en comparación con la asociación con los del grupo B. ',
        comp_q2='Como mostramos con los estudios que mencionamos, hay mucha evidencia que la Prueba de Asociación Implícita está ligada a comportamientos relevantes en el mundo real. A diferencia de otras pruebas, la Prueba de Asociación Implícita es difícil de manipular ya que mide tu respuesta automática---tu primera reacción, sin haber tenido tiempo para pensar. Sí existen otras pruebas para medir sesgos que tienen muchos participantes que ya tomaron la prueba, que fueron desarrollados por académicos, pero la Prueba de Asociación Implícita destaca por las dos razones que mencionamos. ',
        stage_order=(
                "El orden correcto es:\n• " + "\n• ".join(STAGES_CORRECT)
        ),
        comp_q4='No es directa la decisión sobre la información que se te revela—no te vamos a preguntar simplemente si quieres que se te revele la información sobre cada grupo. En vez de eso, la decisión va a depender de tus puntajes en las pruebas de asociación implícita y en el rango de puntajes aceptables que nos diste en la cuarta etapa. Para los dos grupos de personas que aparecieron en una de las pruebas, vamos a tomar en cuenta tres rangos en donde pudo haber caído tu puntaje: abajo del rango que consideras aceptable, dentro del rango que consideras aceptable, y arriba del rango que consideras aceptable. Para cada rango, nos vas a decir si quieres que te revelemos la identidad de los grupos correspondientes a la decisión en caso de que tu puntaje de la prueba de asociación que incluía a ese grupo haya caído dentro de ese rango.',
        comp_q5='Recuerda que con 20% de probabilidad vamos a hacer lo contrario a lo que nos pediste que hiciéramos en esta quinta etapa. Si tu puntaje cayó en un rango en el que querías que no te reportáramos la identidad de los grupos, con 20% de probabilidad te la vamos a reportar. Si tu puntaje cayó en un rango en el que sí querías que te reportáramos la identidad de los grupos, con 20% de probabilidad no te la vamos a reportar. Nota que con 80% de probabilidad sí vamos a hacer lo que nos pediste, por lo que sigue siendo mejor para ti reportarnos lo que realmente quieres que hagamos en cada rango. También nota que de esta manera no vas a poder saber con certeza en qué rango cayó tu puntaje de la Prueba de Asociación Implícita basado en la información que recibes en la Etapa 6.',
        comp_q6='Los participantes deben adivinar si la opinión que los demás miembros te expresaron es la misma que expresaron en privado y el porcentaje de gente que le expresaron a su grupo una opinión que no es su opinón privada.',
    )


def url_for_image(filename):
    return f"/static/images/{filename}"


# clase Subsession para definir las variables de sesión
class Subsession(BaseSubsession):
    practice = models.BooleanField()
    primary_left = models.StringField()
    primary_right = models.StringField()
    secondary_left = models.StringField()
    secondary_right = models.StringField()


def _select_iats_for_participant(cfg) -> list[str]:
    import random
    # lee reglas de settings
    n_st   = cfg.get('iat_n_st')
    n_2cat = cfg.get('iat_n_2cat')
    total  = cfg.get('iat_total', None)
    rnd_types = cfg.get('iat_randomize_types', False)

    if (n_st is None and n_2cat is None and total is None):
        total = Constants.num_rounds  # por defecto: tantas rondas como Constants

    st_pool   = [k for k,v in IAT_LIBRARY.items() if v['kind'] == 'st']
    cat2_pool = [k for k,v in IAT_LIBRARY.items() if v['kind'] == '2cat']

    selected = []
    if (n_st is not None) or (n_2cat is not None):
        if n_st:
            selected += random.sample(st_pool, min(n_st, len(st_pool)))
        if n_2cat:
            selected += random.sample(cat2_pool, min(n_2cat, len(cat2_pool)))
    else:
        total = int(total or Constants.num_rounds)
        pools = {'st': st_pool.copy(), '2cat': cat2_pool.copy()}
        for _ in range(total):
            tipos_disponibles = [t for t,p in pools.items() if p]
            if not tipos_disponibles:
                break
            tipo = random.choice(tipos_disponibles) if rnd_types else (
                'st' if (len(pools['st']) >= len(pools['2cat'])) else '2cat'
            )
            key = random.choice(pools[tipo])
            selected.append(key)
            pools[tipo].remove(key)

    random.shuffle(selected)
    if len(selected) > Constants.num_rounds:
        selected = selected[:Constants.num_rounds]
    return selected

def _show_in_round(player: 'Player', key: str) -> bool:
    mapping = player.participant.vars.get('iat_task_rounds', {})
    return mapping.get(key) == player.round_number

# ================== FIN helpers ==================

def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        cfg = subsession.session.config

        # ¿forzar tratamiento desde settings?, ¿balancear?, ¿o random?
        forced_treatment   = cfg.get('treatment')         # e.g. 'T1'|'T2'|'T3'
        balanced_treatments = cfg.get('balanced_treatments', False)

        # si se pide balanceo por sesión
        cycler = None
        if forced_treatment not in TREATMENTS and balanced_treatments:
            import itertools
            cycler = itertools.cycle(TREATMENTS)

        for p in subsession.get_players():
            # 1) asignar tratamiento
            if forced_treatment in TREATMENTS:
                tr = forced_treatment
            elif cycler:
                tr = next(cycler)
            else:
                import random
                tr = random.choice(TREATMENTS)

            p.participant.vars['treatment'] = tr

            # 2) seleccionar y ordenar IATs para este participante
            order = _select_iats_for_participant(cfg)
            rounds_map = {key: idx+1 for idx, key in enumerate(order)}
            p.participant.vars['iat_task_order']  = order
            p.participant.vars['iat_task_rounds'] = rounds_map

            # 3) DEBUG a consola
            print(f"[DEBUG] P{p.id_in_subsession} code={p.participant.code} "
                  f"treatment={tr} order={order} task→round={rounds_map}")

def vars_for_admin_report(subsession: Subsession):
    rows = []
    for p in subsession.get_players():
        rows.append(dict(
            pid=p.id_in_subsession,
            code=p.participant.code,
            treatment=p.participant.vars.get('treatment'),
            order=p.participant.vars.get('iat_task_order', []),
            mapping=p.participant.vars.get('iat_task_rounds', {}),
        ))
    return dict(rows=rows)

class Player(BasePlayer):

    # este es el espacio dedicado a las variables del iat de dos categorías. 
    # CSV crudo del IAT Minno (ya lo tenías en 1), lo dejo por claridad: 
    iat_minno2_csv = models.LongStringField(blank=True)

    # NUEVOS: resultado y motivo/exclusión
    iat_minno2_d      = models.FloatField(blank=True)
    iat_minno2_reason = models.LongStringField(blank=True)

    # IAT adicional A (palabras)
    iat_minno2a_csv    = models.LongStringField(blank=True)
    iat_minno2a_d      = models.FloatField(blank=True)
    iat_minno2a_reason = models.LongStringField(blank=True)

    # IAT adicional B (palabras)
    iat_minno2b_csv    = models.LongStringField(blank=True)
    iat_minno2b_d      = models.FloatField(blank=True)
    iat_minno2b_reason = models.LongStringField(blank=True)

    # variables para el st-iat de minno:

    # NUEVOS: black
    stiat_raw     = models.LongStringField(blank=True)
    stiat_d       = models.FloatField(blank=True)
    stiat_reason  = models.LongStringField(blank=True)

    # NUEVOS: Sexuality
    stiat_sex_raw     = models.LongStringField(blank=True)
    stiat_sex_d       = models.FloatField(blank=True)
    stiat_sex_reason  = models.LongStringField(blank=True)

    # NUEVOS: Disability
    stiat_dis_raw     = models.LongStringField(blank=True)
    stiat_dis_d       = models.FloatField(blank=True)
    stiat_dis_reason  = models.LongStringField(blank=True)

    # ─── Cuestionario de comprensión 1────────────────────────────────────
    comp_q1 = models.StringField(
        label=(
            '1. ¿Supón que haces una prueba de asociación implícita que involucra a grupos A y B, en donde el grupo B es el grupo “base”. ¿Qué puntaje indicaría que tu sesgo implícito es igual al promedio de cientos de miles de participantes? ¿Qué puntaje indicaría que tu sesgo implícito favorece al grupo A más que el promedio de cientos de miles de participantes?'
        ),
        choices=[
            ('a',
             'a) Un puntaje positivo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'),
            ('b',
             'b) Un puntaje positivo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje negativo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'),
            ('c',
             'c) Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje positivo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'),
            ('d',
             'd) Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje negativo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '),
            ('e',
             'e) Un puntaje negativo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'
             ),
            ('f',
             'f) Un puntaje negativo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje positivo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '
             ),
        ],
        blank=False,
    )

    comp_q2 = models.StringField(
        label=(
            '2. ¿Cuáles son las dos características que hace que la Prueba de Asociación Implícita sea una manera robusta de medir sesgos que tal vez ni siquiera sabías que tenías?'
        ),
        choices=[
            ('a', 'a) Primero, hay una base de datos con cientos de miles de participantes que ya tomaron la prueba. Segundo, fue desarrollado por académicos.'),
            ('b', 'b) Primero, está ligado a comportamientos relevantes en el mundo real. Segundo, es difícil de manipular ya que mide tu respuesta automática, sin que hayas tenido tiempo de pensar. '),
            ('c', 'c) Primero, no existen otras pruebas para medir sesgos. Segundo, es fácil de implementar.'),
        ],
        blank=False,
    )

    #esta pregunta es para arrastrar las etapas en el orden correcto. Es como si fuera comp_q3
    stage_order = models.LongStringField(
        blank=True,
        label="Arrastra las etapas para ponerlas en el orden correcto:"
    )

    comp_q4 = models.StringField(
        label=(
            '4. ¿En la Etapa 5 (qué información revelar en la Etapa 6), ¿cómo tomas la decisión de qué se te revela en la Etapa 6?'
        ),
        choices=[
            ('a', 'a) Tomas una sola decisión sobre todos los grupos a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de todos los grupos cuando estés en la Etapa 6.'),
            ('b', 'b) Tomas una decisión para cada grupo a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de cada grupo cuando estés en la Etapa 6.'),
            ('c', 'c) Nos vas a decir si quieres que te revelemos la identidad de los grupos correspondientes a una decisión dependiendo de si tu puntaje en la prueba de asociación implícita cayó debajo, dentro o arriba del rango que consideras aceptable. '),
            ],
        blank=False,
    )

    comp_q5 = models.StringField(
        label=(
            '5. Supón que nos indicas que quieres que en la Etapa 6 te revelemos la identidad de los grupos A y B, y que no te revelemos la identidad de los grupos C y D. ¿Qué haríamos en la práctica?'
        ),
        choices=[
            ('a', 'a) Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D.'),
            ('b', 'b) Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la dentidad de los grupos C y D.'),
            ('c', 'c) Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D. '),
            ('d', 'd) Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D.'),
        ],
        blank=False,
    )

    comp_q6 = models.StringField(
        label=(
            '6. Escoge la opción correcta sobre tus decisiones en la Etapa 6.'
        ),
        choices=[
            ('a', 'a) Ninguna decisión involucra a los grupos de personas sobre las que te preguntamos en las pruebas de la Etapa 2, y sólo vamos a incluir decisiones que no afecten a las personas sobre las que te preguntamos en la Etapa 2. '),
            ('b',
             'b) No todas las decisiones involucran a los grupos de personas sobre las que te preguntamos en las pruebas de la Etapa 2, y es posible que incluyamos decisiones que no afecten a algunas de las personas sobre las que te preguntamos en la Etapa 2. '),
            ('c',
             'c) Todas las decisiones involucran a los grupos de personas sobre las que te preguntamos en las pruebas de la Etapa 2, y ninguna decisión van a incluir a grupos de personas sobre las que no te preguntamos en la Etapa 2. '),
        ],

        blank=False,
    )


class Group(BaseGroup):
    pass


def custom_export(players):
    yield [
        "session",
        "participant_code",
        "round",
        "primary_left",
        "primary_right",
        "secondary_left",
        "secondary_right",
        "iteration",
        "timestamp",
        "stimulus_class",
        "stimulus_category",
        "stimulus",
        "expected",
        "response",
        "is_correct",
        "reaction_time",
        "dictator_category",
        "dictator_offer",
        "assigned",
        "kept",
        "payoff"

    ]
    for p in players:
        if p.round_number not in (3, 4, 6, 7, 10, 11, 13, 14, 15, 16):
            continue
        sess = p.session
        part = p.participant
        for t in Trial.filter(player=p):
            rnd = p.round_number
            pv = part.vars
            yield [
                sess.code,
                part.code,
                rnd,
                t.iteration,
                t.timestamp,
                t.stimulus_cls,
                t.stimulus_cat,
                t.stimulus,
                t.correct,
                t.response,
                t.is_correct,
                t.reaction_time,
                # Leemos de participant.vars:
                pv.get(f'cat_r{rnd}'),
                pv.get(f'dictator_offer_r{rnd}'),
                pv.get(f'kept_r{rnd}'),
                pv.get(f'assigned_r{rnd}'),
                pv.get(f'payoff_r{rnd}'),
                # ... (más campos IAT si los deseas) ...
            ]

#nueva página para el stiat de minno: la herramienta de minno es la herramienta que hay que implementar para ambos iat. 

# --- NUEVA PÁGINA: ejecuta Minno y recibe el CSV
class MinnoIAT2Cats(Page):
    form_model = 'player'
    form_fields = ['iat_minno2_csv']

    @staticmethod
    def is_displayed(player: Player):
        m = player.participant.vars.get('iat_task_rounds', {})
        return m.get('MinnoIAT2Cats') == player.round_number

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        trials = parse_minno_iat_csv(player.iat_minno2_csv or "")
        d, meta = compute_minno_iat_d(trials)
        player.iat_minno2_d = d
        player.iat_minno2_reason = _minno_iat_reason_from_meta(d, meta)

        # (opcional) guardar meta para debugging / export
        pv = player.participant.vars
        pv['minno_iat2_meta'] = meta

class MinnoIAT2Result(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        d = player.iat_minno2_d  # Float o None
        d_display = f"{d:.3f}" if d is not None else "(N/A)"
        reason_display = player.iat_minno2_reason or ""
        return dict(
            d_display=d_display,
            reason_display=reason_display,
        )


#iats con dos categorías de minno:

# En tu clase StiatMinno, sustituye el before_next_page por éste:

class StiatMinno(Page):
    form_model  = 'player'
    form_fields = ['stiat_raw']

    @staticmethod
    def is_displayed(player: Player):
        m = player.participant.vars.get('iat_task_rounds', {})
        return m.get('StiatMinno') == player.round_number

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # 1) parsear CSV de Minno
        trials = parse_minno_stiat_csv(player.stiat_raw or "")

        # 2) mapa de bloques: toma de session.config si existe; si no, usa defaults (3=compat, 5=incompat)
        bm = player.session.config.get('stiat_block_map', DEFAULT_STIAT_BLOCK_MAP)
        compat = bm.get("compatible", [3])
        incompat = bm.get("incompatible", [5])

        # 3) calcular D
        d, meta = compute_stiat_d(trials, compat, incompat)

        # 4) guardar
        player.stiat_d = d
        pv = player.participant.vars
        pv['stiat_meta'] = meta
        pv['stiat_block_map'] = dict(compatible=compat, incompatible=incompat)
        pv['minno_stiat_done'] = True
        pv['stiat_class'] = classify_stiat_black(d)

# === IAT adicional A (igual estructura) ===
class MinnoIAT2CatsA(Page):
    form_model  = 'player'
    form_fields = ['iat_minno2a_csv']

    @staticmethod
    def is_displayed(player: Player):
        m = player.participant.vars.get('iat_task_rounds', {})
        return m.get('MinnoIAT2CatsA') == player.round_number


    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        trials = parse_minno_iat_csv(player.iat_minno2a_csv or "")
        d, meta = compute_minno_iat_d(trials)
        player.iat_minno2a_d = d
        player.iat_minno2a_reason = '' if d is not None else _minno_iat_reason_from_meta(d, meta)
        player.participant.vars['minno_iat2a_meta'] = meta


# === IAT adicional B (igual estructura) ===
class MinnoIAT2CatsB(Page):
    form_model  = 'player'
    form_fields = ['iat_minno2b_csv']

    @staticmethod
    def is_displayed(player: Player):
        m = player.participant.vars.get('iat_task_rounds', {})
        return m.get('MinnoIAT2CatsB') == player.round_number

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        trials = parse_minno_iat_csv(player.iat_minno2b_csv or "")
        d, meta = compute_minno_iat_d(trials)
        player.iat_minno2b_d = d
        player.iat_minno2b_reason = '' if d is not None else _minno_iat_reason_from_meta(d, meta)
        player.participant.vars['minno_iat2b_meta'] = meta

class MinnoIAT2CatsAResult(Page):
    @staticmethod
    def is_displayed(player): return player.round_number == 1
    @staticmethod
    def vars_for_template(player):
        d = player.iat_minno2a_d
        return dict(d_display=f"{d:.3f}" if d is not None else "(N/A)",
                    reason_display=player.iat_minno2a_reason or "")

class MinnoIAT2CatsBResult(Page):
    @staticmethod
    def is_displayed(player): return player.round_number == 1
    @staticmethod
    def vars_for_template(player):
        d = player.iat_minno2b_d
        return dict(d_display=f"{d:.3f}" if d is not None else "(N/A)",
                    reason_display=player.iat_minno2b_reason or "")


class StiatSexuality(Page):
    form_model  = 'player'
    form_fields = ['stiat_sex_raw']

    @staticmethod
    def is_displayed(player: Player):
        m = player.participant.vars.get('iat_task_rounds', {})
        return m.get('StiatSexuality') == player.round_number
    
    @staticmethod
    def before_next_page(player: 'Player', timeout_happened):
        trials = parse_minno_stiat_csv(player.stiat_sex_raw or "")
        bm = player.session.config.get('stiat_block_map', DEFAULT_STIAT_BLOCK_MAP)
        compat = bm.get("compatible", [3]); incompat = bm.get("incompatible", [5])
        d, meta = compute_stiat_d(trials, compat, incompat)
        player.stiat_sex_d = d
        player.stiat_sex_reason = _reason_from_meta(d, meta)
        pv = player.participant.vars
        pv['stiat_sex_meta'] = meta
        pv['stiat_sex_block_map'] = dict(compatible=compat, incompatible=incompat)
        pv['minno_stiat_sex_done'] = True
        pv['stiat_sex_class'] = classify_stiat_sexuality(d)


class StiatDisability(Page):
    form_model  = 'player'
    form_fields = ['stiat_dis_raw']

    @staticmethod
    def is_displayed(player: Player):
        m = player.participant.vars.get('iat_task_rounds', {})
        return m.get('StiatDisability') == player.round_number

    @staticmethod
    def before_next_page(player: 'Player', timeout_happened):
        trials = parse_minno_stiat_csv(player.stiat_dis_raw or "")
        bm = player.session.config.get('stiat_block_map', DEFAULT_STIAT_BLOCK_MAP)
        compat = bm.get("compatible", [3]); incompat = bm.get("incompatible", [5])
        d, meta = compute_stiat_d(trials, compat, incompat)
        player.stiat_dis_d = d
        player.stiat_dis_reason = _reason_from_meta(d, meta)
        pv = player.participant.vars
        pv['stiat_dis_meta'] = meta
        pv['stiat_dis_block_map'] = dict(compatible=compat, incompatible=incompat)
        pv['minno_stiat_dis_done'] = True
        pv['stiat_dis_class'] = classify_stiat_disability(d)


#### espacio para la página del cuestionario :

from collections import OrderedDict

from otree.api import *
from otree import settings
import random
from collections import OrderedDict  # ya lo usas en before_next_page

class Comprehension(Page):
    form_model = 'player'
    form_fields = [
        'comp_q1', 'comp_q2', 'stage_order',
        'comp_q4', 'comp_q5', 'comp_q6',
    ]

    @staticmethod
    def before_next_page(player, timeout_happened):
        res, score = {}, 0
        for f in Comprehension.form_fields:
            given = getattr(player, f)
            correct = Constants.CORRECT_ANSWERS[f]

            if f == 'stage_order':
                given_list = [s.strip() for s in (given or '').splitlines() if s.strip()]
                correct_list = [s.strip() for s in correct.splitlines()]
                ok = (given_list == correct_list)
                given_label = " → ".join(given_list) if given else "(vacío)"
            else:
                ok = (given == correct)
                opts_dict = OrderedDict(Constants.QUESTION_OPTIONS[f])
                given_label = opts_dict.get(given, "(sin marcar)")

            res[f] = dict(
                text=Constants.QUESTION_TEXT[f],
                given=given,
                given_label=given_label,
                correct=correct,
                ok=ok,
                options=Constants.QUESTION_OPTIONS.get(f, []),
                explanation=Constants.CORRECT_EXPLANATIONS[f],
            )
            score += ok

        player.participant.vars.update(comp_results=res, comp_score=score)
        player.participant.vars['compr1_shown'] = True

    @staticmethod
    def is_displayed(player):
        return (
            player.participant.vars.get('iat_round_order') == list(range(1, 15))
            and not player.participant.vars.get('compr1_shown', False)
        )

    @staticmethod
    def vars_for_template(player):
        etapas = [
            "Sociodemográfica",
            "Pruebas de asociación implícita",
            "Adivinas tus puntajes en las pruebas de la Etapa 2",
            "Rango aceptable de puntajes en las pruebas de la Etapa 2",
            "Qué información revelar en las decisiones de la Etapa 6",
            "Decisiones monetarias que pueden afectar a grupos de la Etapa 2",
        ]
        random.shuffle(etapas)

        # Construimos una lista de IATs activos con un flag booleano 'has'
        iat_scores = []

        if getattr(settings, 'use_minno_stiat', True):
            val = player.field_maybe_none('stiat_d')
            iat_scores.append({
                'nombre': 'ST-IAT (personas negras)',
                'valor': val,
                'has': (val is not None),
                'razon': player.field_maybe_none('stiat_reason') or '',
            })

        if getattr(settings, 'use_minno_stiat_sex', True):
            val = player.field_maybe_none('stiat_sex_d')
            iat_scores.append({
                'nombre': 'ST-IAT (sexualidad)',
                'valor': val,
                'has': (val is not None),
                'razon': player.field_maybe_none('stiat_sex_reason') or '',
            })

        if getattr(settings, 'use_minno_stiat_dis', True):
            val = player.field_maybe_none('stiat_dis_d')
            iat_scores.append({
                'nombre': 'ST-IAT (discapacidad)',
                'valor': val,
                'has': (val is not None),
                'razon': player.field_maybe_none('stiat_dis_reason') or '',
            })

        return dict(
            etapas_aleatorias=etapas,
            iat_scores=iat_scores,
        )

    
class ComprehensionFeedback(Page):
    @staticmethod
    def vars_for_template(player):
        # 1) Sacamos los resultados y al mismo tiempo los 'poppeamos'
        #    para que no queden en player.participant.vars
        results = player.participant.vars.pop('comp_results', {})

        # 2) Recuperamos el score (no habrá sido 'popped')
        score = player.participant.vars.get('comp_score', 0)

        return dict(
            results=results,
            score=score,
            total=len(Constants.CORRECT_ANSWERS),
        )

    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order', []) == list(range(1, 15))
            and not player.participant.vars.get('feedback1_shown', False)
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        # Aquí marcamos que ya mostramos feedback, para que is_displayed pase a False
        player.participant.vars['feedback1_shown'] = True

page_sequence = [
    # IATs (todas; se mostrarán sólo las asignadas en cada ronda)
    MinnoIAT2Cats,
    MinnoIAT2CatsA,
    MinnoIAT2CatsB,
    StiatSexuality,
    StiatDisability,
    StiatMinno,
]




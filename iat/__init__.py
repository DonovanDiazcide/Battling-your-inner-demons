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
    num_rounds = 5  # ← ahora son 5 rondas (1-3 IATs, 4 prefs, 5 decisiones)
    endowment = Decimal('100')


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


# === NUEVO: cantidad fija de rondas de IAT ===
IAT_ROUNDS = 3  # rondas 1..3 son IATs; 4=preferencias; 5=decisiones

def _select_iats_for_participant(cfg) -> list[str]:
    import random
    # lee reglas de settings
    n_st   = cfg.get('iat_n_st')
    n_2cat = cfg.get('iat_n_2cat')
    total  = cfg.get('iat_total', None)
    rnd_types = cfg.get('iat_randomize_types', False)

    # Fallback: 3 IATs, no 5
    if (n_st is None and n_2cat is None and total is None):
        total = IAT_ROUNDS

    st_pool   = [k for k,v in IAT_LIBRARY.items() if v['kind'] == 'st']
    cat2_pool = [k for k,v in IAT_LIBRARY.items() if v['kind'] == '2cat']

    selected = []
    if (n_st is not None) or (n_2cat is not None):
        if n_st:
            selected += random.sample(st_pool, min(n_st, len(st_pool)))
        if n_2cat:
            selected += random.sample(cat2_pool, min(n_2cat, len(cat2_pool)))
    else:
        total = int(total or IAT_ROUNDS)
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
    if len(selected) > IAT_ROUNDS:
        selected = selected[:IAT_ROUNDS]
    return selected


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

            # 3) DEBUG: asignar D por default si se pidió
            if _debug_use_fake_d(subsession.session):
                # usa participant.vars (persisten entre rondas)
                dmap = {}
                for key in order:
                    dmap[key] = _debug_fake_d_for_key(subsession.session, key)
                # opcional: resto del catálogo
                for key in IAT_LIBRARY.keys():
                    dmap.setdefault(key, _debug_fake_d_for_key(subsession.session, key))
                p.participant.vars['debug_fake_d'] = dmap

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
    # --- RONDA 4: tres preguntas (booleanas) en orden aleatorizado por tratamiento ---
    r4_q1 = models.BooleanField(
        choices=[(True, 'Sí'), (False, 'No')],
        widget=widgets.RadioSelect,
        label='(Se definirá dinámicamente en la plantilla)'
    )
    r4_q2 = models.BooleanField(
        choices=[(True, 'Sí'), (False, 'No')],
        widget=widgets.RadioSelect,
        label='(Se definirá dinámicamente en la plantilla)'
    )
    r4_q3 = models.BooleanField(
        choices=[(True, 'Sí'), (False, 'No')],
        widget=widgets.RadioSelect,
        label='(Se definirá dinámicamente en la plantilla)'
    )

    # --- RONDA 5: campo de captura (un solo input reutilizable) ---
    r5_offer = models.IntegerField(min=0, max=100, blank=True)

    # este es el espacio dedicado a las variables del iat de dos categorías. 
    # CSV crudo del IAT Minno (ya lo tenías en 1), lo dejo por claridad: 
    iat_minno2_csv = models.LongStringField(blank=True)

    # IAT black-white: resultado y motivo/exclusión
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
#funciones decisiones monetarias: 

# ===== Helpers de mapeo IAT→tipo y d-score, y orden por tratamiento =====

# Mapea clave de IAT → nombre del campo d-score en Player
IAT_DFIELD = {
    'MinnoIAT2Cats':  'iat_minno2_d',
    'MinnoIAT2CatsA': 'iat_minno2a_d',
    'MinnoIAT2CatsB': 'iat_minno2b_d',
    'StiatMinno':     'stiat_d',
    'StiatSexuality': 'stiat_sex_d',
    'StiatDisability':'stiat_dis_d',
}

def get_treatment(player: 'Player') -> str:
    return player.participant.vars.get('treatment', 'T1')

def iat_key_for_round(player: 'Player', rnd_idx: int) -> str:
    """rnd_idx ∈ {1,2,3} → clave de IAT jugado en esa ronda (según aleatorización previa)."""
    order = player.participant.vars.get('iat_task_order', [])
    if 1 <= rnd_idx <= len(order):
        return order[rnd_idx-1]
    return ''

def key_kind(key: str) -> str:
    """'st' | '2cat' según IAT_LIBRARY."""
    info = IAT_LIBRARY.get(key, {})
    return info.get('kind', 'st')

def dscore_for_key(player: 'Player', key: str):
    field = IAT_DFIELD.get(key)
    return getattr(player, field, None) if field else None

def d_in_range(d, lo=-0.5, hi=0.5) -> bool:
    return (d is not None) and (lo <= d <= hi)

# ---- Orden de preguntas (Ronda 4) decidido a nivel tratamiento (fijo y reproducible) ----
# Cada lista indica en qué orden se referencian los IAT de las rondas 1,2,3.
# Ej.: ['3','1','2'] => Pregunta 1 habla del IAT jugado en la ronda 3, pregunta 2 del de la 1, etc.
TREATMENT_R4_ORDER = {
    'T1': [3, 1, 2],  # (similar a tu ejemplo)
    'T2': [1, 3, 2],
    'T3': [2, 1, 3],
}

def build_round4_question_plan(player: 'Player'):
    """Devuelve lista de 3 dicts con metadata por pregunta (orden a nivel tratamiento)."""
    tr = get_treatment(player)
    perm = TREATMENT_R4_ORDER.get(tr, [1,2,3])
    plan = []
    for i, rnd_idx in enumerate(perm, start=1):
        key = iat_key_for_round(player, rnd_idx)
        kind = key_kind(key)
        d = dscore_for_key(player, key)
        plan.append(dict(
            qslot=i, rnd_idx=rnd_idx, key=key, kind=kind, d=d,
            d_in_band=d_in_range(d)
        ))
    # Guarda el plan y un map qslot→rnd en participant.vars para trazabilidad
    player.participant.vars['r4_plan'] = plan
    player.participant.vars['r4_qmap'] = {p['qslot']: p['rnd_idx'] for p in plan}
    return plan

# ---- Construcción de las 9 decisiones de la Ronda 5 (3 por IAT), orden a nivel tratamiento ----

# Para cada IAT generamos 3 "páginas" (p1,p2,p3) con modos de revelación:
#   ST:
#     p1: self vs target; revelación depende de R4 (80/20).
#     p2: self vs target; revelación SIEMPRE (independiente de R4).
#     p3: self vs target; revelación NUNCA  (independiente de R4).
#   2cat:
#     p1: cat1 vs cat2; revelación depende de R4 (80/20) sobre ambas categorías.
#     p2: cat1 vs cat2; revelación SIEMPRE.
#     p3: cat1 vs cat2; revelación NUNCA.
#
# Esto asegura "3 páginas por IAT" también cuando el IAT es ST (simetría y claridad).

def _seed_for_r5(session_code: str, treatment: str) -> int:
    # Un seed reproducible por sesión y tratamiento
    return abs(hash(f'R5-{session_code}-{treatment}')) % (2**31)

def _r5_label_categories(key: str, kind: str):
    # Etiquetas genéricas (si tienes nombres reales de categorías por IAT, cámbialas aquí)
    if kind == 'st':
        return ('Tú', f'Categoría del IAT ({key})')
    else:
        return ('Categoría 1', 'Categoría 2')

def init_round5_decisions(player: 'Player'):
    """
    Construye y guarda en participant.vars['r5_decision_queue'] una lista de 9 decisiones:
    cada item: dict con {pos, rnd_idx, key, kind, page_type, reveal_mode}
    - page_type: 'p1','p2','p3'
    - reveal_mode: 'depends_r4' | 'always' | 'never'
    Orden aleatorio a nivel tratamiento (mismo para participantes del mismo tratamiento).
    """
    if player.participant.vars.get('r5_decision_queue'):
        return  # ya inicializado

    # 3 IATs según rondas 1..3
    items = []
    for rnd_idx in [1,2,3]:
        key = iat_key_for_round(player, rnd_idx)
        kind = key_kind(key)
        # Tres páginas por IAT:
        items.append(dict(rnd_idx=rnd_idx, key=key, kind=kind, page_type='p1', reveal_mode='depends_r4'))
        items.append(dict(rnd_idx=rnd_idx, key=key, kind=kind, page_type='p2', reveal_mode='always'))
        items.append(dict(rnd_idx=rnd_idx, key=key, kind=kind, page_type='p3', reveal_mode='never'))

    # Barajar con semilla por tratamiento
    tr = get_treatment(player)
    seed = _seed_for_r5(player.session.code, tr)
    rng = random.Random(seed)
    rng.shuffle(items)

    # Numerar posiciones 1..9 y guardar
    for i, it in enumerate(items, start=1):
        it['pos'] = i
        # Precalcula etiquetas de las "partes"
        it['left_label'], it['right_label'] = _r5_label_categories(it['key'], it['kind'])

    player.participant.vars['r5_decision_queue'] = items
    player.participant.vars['r5_log'] = []      # log secuencial de las 9 decisiones
    player.participant.vars['r5_agg'] = {}      # agregados por IAT/page_type/categoría


#nueva página para el stiat de minno: la herramienta de minno es la herramienta que hay que implementar para ambos iat. 

#probando:iat falso: 

# ======= DEBUG helpers: saltar IAT y D fake =======

def _debug_skip_iats(session) -> bool:
    return bool(session.config.get('debug_skip_iats', False))

def _debug_use_fake_d(session) -> bool:
    return bool(session.config.get('debug_fake_dscores', False))

def _debug_fake_d_for_key(session, key: str) -> float:
    cfg = session.config
    if 'debug_fake_d_value' in cfg:
        return float(cfg['debug_fake_d_value'])
    lo, hi = cfg.get('debug_fake_d_range', (-0.4, 0.4))
    seed = abs(hash(f"{session.code}-{key}")) % (2**31)
    rng = random.Random(seed)
    return round(rng.uniform(lo, hi), 3)

def ensure_fake_dscores_for_selected_iats(player: 'Player'):
    """Construye y guarda en participant.vars['debug_fake_d'] D-scores
    para los 3 IAT seleccionados (y opcionalmente para todo el catálogo)."""
    if not _debug_use_fake_d(player.session):
        return
    dmap = player.participant.vars.get('debug_fake_d', {})
    order = player.participant.vars.get('iat_task_order', [])
    for key in order:
        if key and key not in dmap:
            dmap[key] = _debug_fake_d_for_key(player.session, key)
    # (Opcional) si quieres que TODO el catálogo tenga valor:
    for key in IAT_LIBRARY.keys():
        dmap.setdefault(key, _debug_fake_d_for_key(player.session, key))
    player.participant.vars['debug_fake_d'] = dmap

# === Reemplaza tu dscore_for_key por este fallback (usa Player.field; si no, fake) ===
def dscore_for_key(player: 'Player', key: str):
    """Devuelve el D-score del IAT 'key'.
    - Primero intenta leer el campo del Player de forma segura (field_maybe_none).
    - Si es None, busca en participant.vars['debug_fake_d'].
    """
    field = IAT_DFIELD.get(key)
    if not field:
        return None

    # Acceso seguro para evitar TypeError de oTree cuando el campo es None
    try:
        val = player.field_maybe_none(field)
    except Exception:
        # fallback ultra-conservador si el método no existiera (o en tests)
        val = getattr(player, field, None)

    if val is None:
        dmap = player.participant.vars.get('debug_fake_d', {})
        val = dmap.get(key, None)
    return val


# --- NUEVA PÁGINA: ejecuta Minno y recibe el CSV
class MinnoIAT2Cats(Page):
    form_model = 'player'
    form_fields = ['iat_minno2_csv']

    @staticmethod
    def is_displayed(player: Player):
        if _debug_skip_iats(player.session):
            return False
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
        if _debug_skip_iats(player.session):
            return False
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
        if _debug_skip_iats(player.session):
            return False
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
        if _debug_skip_iats(player.session):
            return False
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
        if _debug_skip_iats(player.session):
            return False
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
        if _debug_skip_iats(player.session):
            return False
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

# modificar el is_displayed luego, aún tiene la línea del orden de los iats.
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

#páginas decisiones monetarias:
class Round4Reveal(Page):
    form_model = 'player'
    form_fields = ['r4_q1', 'r4_q2', 'r4_q3']

    @staticmethod
    def is_displayed(player: 'Player'):
        return player.round_number == 4

    @staticmethod
    def vars_for_template(player: 'Player'):
        ensure_fake_dscores_for_selected_iats(player)
        plan = player.participant.vars.get('r4_plan') or build_round4_question_plan(player)
        # Construye textos de pregunta (puedes usarlos en la plantilla)
        questions = []
        for p in plan:
            dtxt = f"{p['d']:.3f}" if p['d'] is not None else "(N/A)"
            if p['kind'] == 'st':
                text = (
                    f"Tu IAT de la ronda {p['rnd_idx']} (una categoría) tiene D={dtxt}. "
                    f"Si D ∈ [-0.5,0.5]: ¿Quieres que, cuando repartas dinero con una persona de esa categoría, "
                    f"con 80% de probabilidad te revelemos la categoría y 20% no?"
                )
            else:
                text = (
                    f"Tu IAT de la ronda {p['rnd_idx']} (dos categorías) tiene D={dtxt}. "
                    f"Si D ∈ [-0.5,0.5]: ¿Quieres que, cuando repartas dinero entre personas de ambas categorías, "
                    f"con 80% de probabilidad te revelemos la identidad de ambas categorías y 20% no?"
                )
            questions.append(dict(qslot=p['qslot'], text=text, d=p['d'], kind=p['kind'], rnd_idx=p['rnd_idx']))
        return dict(questions=questions)

    @staticmethod
    def before_next_page(player: 'Player', timeout_happened):
        plan = player.participant.vars.get('r4_plan') or build_round4_question_plan(player)
        answers = {
            1: player.r4_q1,
            2: player.r4_q2,
            3: player.r4_q3,
        }
        # Guardar por ronda original (rnd_idx) para usar en R5
        prefs = {}
        for p in plan:
            rnd = p['rnd_idx']
            ans = answers[p['qslot']]
            # Sólo cuenta si D ∈ [-0.5,0.5]; si no, lo marcamos None
            prefs[rnd] = ans if d_in_range(p['d']) else None
        player.participant.vars['r4_prefs_by_rnd'] = prefs

class _MonetaryDecisionBase(Page):
    form_model  = 'player'
    form_fields = ['r5_offer']
    timeout_seconds = 5  # 5 segundos para decidir

    @staticmethod
    def is_displayed(player: 'Player'):
        return player.round_number == 5

    @staticmethod
    def _current_item(player: 'Player', pos: int) -> dict:
        init_round5_decisions(player)
        queue = player.participant.vars['r5_decision_queue']
        return next(x for x in queue if x['pos'] == pos)

    # ===== Helper para vars_for_template(pos) =====
    @staticmethod
    def _vars_for_template(player: 'Player', pos: int):
        ensure_fake_dscores_for_selected_iats(player)
        item = _MonetaryDecisionBase._current_item(player, pos)

        # Determinar si habrá revelación de categorías en ESTA página
        reveal = False
        if item['reveal_mode'] == 'always':
            reveal = True
        elif item['reveal_mode'] == 'never':
            reveal = False
        else:
            # depends_r4 → usa preferencia de R4 SÓLO si D ∈ [-0.5,0.5]; si no, tratamos como "no pref" (20% reveal)
            prefs = player.participant.vars.get('r4_prefs_by_rnd', {})
            pref = prefs.get(item['rnd_idx'], None)
            d = dscore_for_key(player, item['key'])
            base_prob = 0.8 if (pref is True and d_in_range(d)) else 0.2
            # RNG reproducible por participante+pos para que no cambie en refresh
            seed = abs(hash(f"{player.participant.code}-{player.round_number}-pos{pos}")) % (2**31)
            rng = random.Random(seed)
            reveal = (rng.random() < base_prob)

        # Texto para la interfaz
        L, R = item['left_label'], item['right_label']
        if item['kind'] == 'st':
            if reveal:
                context = f"Estás repartiendo entre {L} y {R}."
            else:
                context = "Estás repartiendo entre Tú y una persona del grupo A."
        else:
            if reveal:
                context = f"Estás repartiendo entre {L} y {R}."
            else:
                context = "Estás repartiendo entre la Categoría A y la Categoría B."

        return dict(
            pos=pos,
            endowment=int(Constants.endowment),
            context=context,
            left_label=L if reveal else ('Tú' if item['kind']=='st' else 'Categoría A'),
            right_label=R if reveal else ('Grupo A' if item['kind']=='st' else 'Categoría B'),
            page_type=item['page_type'],
            reveal=reveal,
            iat_key=item['key'],
            iat_kind=item['kind'],
            rnd_idx=item['rnd_idx'],
        )

    # ===== Helper para before_next_page(pos) =====
    @staticmethod
    def _before_next_page(player: 'Player', timeout_happened, pos: int):
        item = _MonetaryDecisionBase._current_item(player, pos)

        # Leer la entrada del usuario de forma segura (puede ser None)
        raw_offer = player.field_maybe_none('r5_offer')

        # ¿Fue default?
        defaulted = False
        default_reason = None
        if timeout_happened:
            defaulted = True
            default_reason = 'timeout'
            offer = 50
        elif raw_offer is None:
            defaulted = True
            default_reason = 'blank'
            offer = 50
        else:
            offer = int(raw_offer)

        # Clamp
        offer = max(0, min(100, offer))

        # Determinar revelación (misma lógica que en _vars_for_template)
        reveal = False
        if item['reveal_mode'] == 'always':
            reveal = True
        elif item['reveal_mode'] == 'never':
            reveal = False
        else:
            prefs = player.participant.vars.get('r4_prefs_by_rnd', {})
            pref = prefs.get(item['rnd_idx'], None)
            d = dscore_for_key(player, item['key'])
            base_prob = 0.8 if (pref is True and d_in_range(d)) else 0.2
            seed = abs(hash(f"{player.participant.code}-{player.round_number}-pos{pos}")) % (2**31)
            rng = random.Random(seed)
            reveal = (rng.random() < base_prob)

        # Montos (100 total)
        left_amt = offer
        right_amt = 100 - offer

        # Log secuencial
        log = player.participant.vars.get('r5_log', [])
        entry = dict(
            pos=pos,
            rnd_idx=item['rnd_idx'],
            key=item['key'],
            kind=item['kind'],
            page_type=item['page_type'],
            reveal_mode=item['reveal_mode'],
            reveal=reveal,
            offer_left=left_amt,
            offer_right=right_amt,
            submitted_offer=raw_offer,     # <- NUEVO (para auditar)
            defaulted=defaulted,           # <- NUEVO
            default_reason=default_reason, # <- NUEVO
            timestamp=time.time(),
        )
        log.append(entry)
        player.participant.vars['r5_log'] = log

        # Agregados por IAT / page_type / categoría (igual que antes)
        agg = player.participant.vars.get('r5_agg', {})
        k = (item['key'], item['page_type'])
        if item['kind'] == 'st':
            a = agg.get(k, dict(self_total=0, cat_total=0, count=0))
            a['self_total'] += left_amt
            a['cat_total']  += right_amt
            a['count'] += 1
            agg[k] = a
        else:
            a = agg.get(k, dict(cat1_total=0, cat2_total=0, count=0))
            a['cat1_total'] += left_amt
            a['cat2_total'] += right_amt
            a['count'] += 1
            agg[k] = a
        player.participant.vars['r5_agg'] = agg

        # limpiar input para la siguiente página
        player.r5_offer = None

# ===== Subclases 1..9: llaman a los helpers con su posición =====
class MonetaryDecision1(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 1)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 1)

class MonetaryDecision2(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 2)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 2)

class MonetaryDecision3(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 3)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 3)

class MonetaryDecision4(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 4)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 4)

class MonetaryDecision5(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 5)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 5)

class MonetaryDecision6(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 6)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 6)

class MonetaryDecision7(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 7)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 7)

class MonetaryDecision8(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 8)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 8)

class MonetaryDecision9(_MonetaryDecisionBase):
    @staticmethod
    def vars_for_template(player): return _MonetaryDecisionBase._vars_for_template(player, 9)
    @staticmethod
    def before_next_page(player, timeout_happened): return _MonetaryDecisionBase._before_next_page(player, timeout_happened, 9)

# ======= Página de resumen de resultados de la Ronda 5 =======

def _labels_for_entry(entry: dict):
    """Reconstruye las etiquetas (izq/der) que vio el participante según kind y si hubo revelación."""
    kind = entry.get('kind')
    key = entry.get('key')
    reveal = entry.get('reveal', False)
    if kind == 'st':
        # IAT de una categoría
        if reveal:
            return ('Tú', f'Categoría del IAT ({key})')
        else:
            return ('Tú', 'Grupo A')
    else:
        # IAT de dos categorías
        if reveal:
            return ('Categoría 1', 'Categoría 2')
        else:
            return ('Categoría A', 'Categoría B')

def _label_page_type(pt: str) -> str:
    return {'p1': 'Página 1', 'p2': 'Página 2', 'p3': 'Página 3'}.get(pt, pt)

def _label_reveal_mode(rm: str) -> str:
    return {
        'depends_r4': 'Depende de R4 (80/20)',
        'always':     'Siempre revelado',
        'never':      'Nunca revelado',
    }.get(rm, rm)

class ResultsR5(Page):
    @staticmethod
    def is_displayed(player: 'Player'):
        return player.round_number == 5

    @staticmethod
    def vars_for_template(player: 'Player'):
        log = player.participant.vars.get('r5_log', []) or []
        log = sorted(log, key=lambda x: x.get('pos', 0))
        prefs = player.participant.vars.get('r4_prefs_by_rnd', {}) or {}

        iat_order, grouped = [], {}
        for e in log:
            k = e['key']
            if k not in grouped:
                grouped[k] = []
                iat_order.append(k)
            grouped[k].append(e)

        iats = []
        for key in iat_order:
            entries = grouped[key]
            kind = entries[0].get('kind')
            rnd_idx = entries[0].get('rnd_idx')

            pref = prefs.get(rnd_idx, None)
            base_censor_text = 'No' if pref is True else ('Sí' if pref is False else 'N/A')

            titulo = f"{key} — {'una categoría' if kind=='st' else 'dos categorías'} (ronda {rnd_idx})"

            filas = []
            for e in entries:
                left_label, right_label = _labels_for_entry(e)
                censurar = base_censor_text if e.get('reveal_mode') == 'depends_r4' else '-'

                # NUEVO: texto "Por default"
                if 'defaulted' in e:
                    por_default = 'Sí' if e['defaulted'] else 'No'
                else:
                    por_default = 'N/D'  # para logs viejos sin este campo

                filas.append(dict(
                    pos=e['pos'],
                    page=_label_page_type(e['page_type']),
                    modo=_label_reveal_mode(e['reveal_mode']),
                    revelado='Sí' if e['reveal'] else 'No',
                    censurar=censurar,
                    por_default=por_default,          # ← NUEVO
                    left_label=left_label,
                    left_amt=e['offer_left'],
                    right_label=right_label,
                    right_amt=e['offer_right'],
                ))

            iats.append(dict(
                key=key, kind=kind, rnd_idx=rnd_idx,
                titulo=titulo, filas=filas,
            ))

        total_dotacion = int(Constants.endowment) if hasattr(Constants, 'endowment') else 100
        return dict(iats=iats, total_dotacion=total_dotacion)    




page_sequence = [
    # IATs (todas; se mostrarán sólo las asignadas en cada ronda)
    MinnoIAT2Cats,
    MinnoIAT2CatsA,
    MinnoIAT2CatsB,
    StiatSexuality,
    StiatDisability,
    StiatMinno,

    # --- NUEVAS RONDAS ---
    Round4Reveal,            # ronda 4
    MonetaryDecision1,       # las 9 decisiones de la ronda 5
    MonetaryDecision2,
    MonetaryDecision3,
    MonetaryDecision4,
    MonetaryDecision5,
    MonetaryDecision6,
    MonetaryDecision7,
    MonetaryDecision8,
    MonetaryDecision9,

    ResultsR5,               # resumen de la ronda 5
]
import time
import random
import logging

# from .admin_report_functions import *
from otree.api import *
from otree import settings
from . import stimuli
from . import stats
from . import blocks
import math
from statistics import mean, stdev
from decimal import Decimal

# comentarios.
doc = """
Implicit Association Test, draft
"""
from statistics import mean, stdev



def dscore1(data3: list, data4: list, data6: list, data7: list):
    # Filtrar valores demasiado largos.
    def not_long(value):
        return value < 10.0

    data3 = list(filter(not_long, data3))
    data4 = list(filter(not_long, data4))
    data6 = list(filter(not_long, data6))
    data7 = list(filter(not_long, data7))

    # Filtrar valores demasiado cortos
    def too_short(value):
        return value < 0.300

    total_data = data3 + data4 + data6 + data7
    short_data = list(filter(too_short, total_data))

    if len(total_data) == 0 or (len(short_data) / len(total_data) > 0.1):
        return None

    # Calcular el d-score
    combined_3_6 = data3 + data6
    combined_4_7 = data4 + data7

    if len(combined_3_6) < 2 or len(combined_4_7) < 2:
        # stdev requiere al menos dos datos
        return None

    std_3_6 = stdev(combined_3_6)
    std_4_7 = stdev(combined_4_7)

    mean_3_6 = mean(data6) - mean(data3) if len(data6) > 0 and len(data3) > 0 else 0
    mean_4_7 = mean(data7) - mean(data4) if len(data7) > 0 and len(data4) > 0 else 0

    dscore_3_6 = mean_3_6 / std_3_6 if std_3_6 > 0 else 0
    dscore_4_7 = mean_4_7 / std_4_7 if std_4_7 > 0 else 0

    dscore_mean1 = (dscore_3_6 + dscore_4_7) * 0.5
    return dscore_mean1


def dscore2(data10: list, data13: list, data11: list, data14: list):
    # Filtrar valores demasiado largos
    def not_long(value):
        return value < 10.0

    data10 = list(filter(not_long, data10))
    data13 = list(filter(not_long, data13))
    data11 = list(filter(not_long, data11))
    data14 = list(filter(not_long, data14))

    # Filtrar valores demasiado cortos
    def too_short(value):
        return value < 0.300

    total_data = data10 + data13 + data11 + data14
    short_data = list(filter(too_short, total_data))

    if len(total_data) == 0 or (len(short_data) / len(total_data) > 0.1):
        return None

    # Calcular el d-score
    combined_10_11 = data10 + data11
    combined_13_14 = data13 + data14

    if len(combined_10_11) < 2 or len(combined_13_14) < 2:
        # stdev requiere al menos dos datos
        return None

    std_10_11 = stdev(combined_10_11)
    std_13_14 = stdev(combined_13_14)

    mean_10_11 = mean(data11) - mean(data10) if len(data11) > 0 and len(data10) > 0 else 0
    mean_13_14 = mean(data14) - mean(data13) if len(data14) > 0 and len(data13) > 0 else 0

    dscore_10_11 = mean_10_11 / std_10_11 if std_10_11 > 0 else 0
    dscore_13_14 = mean_13_14 / std_13_14 if std_13_14 > 0 else 0

    dscore_mean2 = (dscore_10_11 + dscore_13_14) * 0.5
    return dscore_mean2



class Constants(BaseConstants):
    name_in_url = 'iat'
    players_per_group = None
    num_rounds = 16  # 14 para iat + 4 para dictador

    keys = {"e": 'left', "i": 'right'}
    trial_delay = 0.250
    endowment = Decimal('100')  # Añadido para dictador
    categories = ['personas delgadas y personas obesas', 'personas homosexuales y personas heterosexuales']  # Categorías para el Dictador
    PersonasDelgadas = "personas delgadas"
    PersonasObesas = "personas obesas"
    PersonasHeterosexuales = "personas heterosexuales"
    PersonasHomosexuales = "personas homosexuales"


def url_for_image(filename):
    return f"/static/images/{filename}"


class Subsession(BaseSubsession):
    practice = models.BooleanField()
    primary_left = models.StringField()
    primary_right = models.StringField()
    secondary_left = models.StringField()
    secondary_right = models.StringField()


def creating_session(self):
    session = self.session
    defaults = dict(
        retry_delay=0.5,
        trial_delay=0.5,
        primary=[None, None],
        primary_images=False,
        secondary=[None, None],
        secondary_images=False,
        num_iterations={
            # Rondas existentes para iat.
            1: 5, 2: 5, 3: 10, 4: 20, 5: 5, 6: 10, 7: 20,
            8: 5, 9: 5, 10: 10, 11: 20, 12: 5, 13: 10, 14: 20,
            # Rondas adicionales para Dictador.
            15: 1, 16: 1
        },
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])

    if self.round_number == 1:
        players = list(self.get_players())
        random.shuffle(players)
        mitad = len(players) // 2

        orden_directo = list(range(1, 15))
        orden_invertido = list(range(8, 15)) + list(range(1, 8))

        # 50% → directos
        for p in players[:mitad]:
            p.participant.vars['iat_round_order'] = orden_directo

        # 50% → invertidos
        for p in players[mitad:]:
            p.participant.vars['iat_round_order'] = orden_invertido

        # --- Nuevo bloque: imprime resumen ordenado ---
        print("[IAT ORDER SUMMARY]")
        for p in sorted(players, key=lambda p: p.id_in_subsession):
            order = p.participant.vars['iat_round_order']
            # aquí decides cómo formatear el texto
            print(f"Jugador {p.id_in_subsession}: {order}")

        # tu código de categorías del Dictador sigue igual
        shuffled_categories = Constants.categories.copy()
        random.shuffle(shuffled_categories)
        session.vars['shuffled_dictator_categories'] = shuffled_categories
        # Fijamos orden: 15→delgadas/obesas, 16→homo/hetero
        session.vars['shuffled_dictator_categories'] = Constants.categories.copy()

    block = get_block_for_round(self.round_number, session.params)

    self.practice = block.get('practice', False)
    self.primary_left = block.get('left', {}).get('primary', "")
    self.primary_right = block.get('right', {}).get('primary', "")
    self.secondary_left = block.get('left', {}).get('secondary', "")
    self.secondary_right = block.get('right', {}).get('secondary', "")

        #print("shuffled categories:", shuffled_categories)

    # Asignar categorías al Dictador basadas en la lista aleatoria para las rondas 15-18
    if self.round_number in [15, 16]:
        shuffled_categories = session.vars.get('shuffled_dictator_categories')
        if shuffled_categories:
            # Asignar una categoría por ronda 15-18 al grupo
            assigned_category = shuffled_categories[self.round_number - 15]
            for group in self.get_groups():
                group.dictator_category = assigned_category


def get_block_for_round(rnd, params):
    """Get a round setup from BLOCKS with actual categories' names substituted from session config"""
    if rnd in blocks.BLOCKS:
        block = blocks.BLOCKS[rnd]
        result = blocks.configure(block, params)
        return result
    else:
        # Retorna un bloque vacío o predeterminado para rondas que no lo necesitan
        return {}

def thumbnails_for_block(block, params):
    """Return image urls for each category in block.
    Taking first image in the category as a thumbnail.
    """
    thumbnails = {'left': {}, 'right': {}}
    for side in ['left', 'right']:
        for cls in ['primary', 'secondary']:
            if cls in block[side] and params[f"{cls}_images"]:
                # use first image in categopry as a corner thumbnail
                images = stimuli.DICT[block[side][cls]]
                thumbnails[side][cls] = url_for_image(images[0])
    return thumbnails


def labels_for_block(block):
    """Return category labels for each category in block
    Just stripping prefix "something:"
    """
    labels = {'left': {}, 'right': {}}
    for side in ['left', 'right']:
        for cls in ['primary', 'secondary']:
            if cls in block[side]:
                cat = block[side][cls]
                if ':' in cat:
                    labels[side][cls] = cat.split(':')[1]
                else:
                    labels[side][cls] = cat
    return labels


def get_num_iterations_for_round(rnd):
    """Get configured number of iterations
    The rnd: Player or Subsession
    """
    idx = rnd.round_number
    num = rnd.session.params['num_iterations'][idx]
    return num


class Player(BasePlayer):
    iteration = models.IntegerField(initial=0)  # Contador para iteraciones del jugador
    num_trials = models.IntegerField(initial=0)  # Número total de intentos del jugador
    num_correct = models.IntegerField(initial=0)  # Número de respuestas correctas
    edad = models.IntegerField(label="Edad", min=18, max=120, )
    num_failed = models.IntegerField(initial=0)  # Número de respuestas incorrectas
    sexo = models.StringField(
        label="¿Cuál es tu sexo?",
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('NB', 'No binario'),
            ('ND', 'Prefiero no decirlo')
        ]
    )

    random_number = models.IntegerField(label="Número aleatorio entre 1 y 20", min=1, max=20)
    ha_participado = models.StringField(
        label="¿Has participado en experimentos previamente?",
        choices=['Sí', 'No'],
        blank = True,  # <--- permitimos valor nulo al inicio

    )

    num_experimentos = models.IntegerField(
        label="¿En cuántos?",
        min=0,
        blank=True
    )

    dscore1 = models.FloatField()  # D-score del primer iat
    dscore2 = models.FloatField()  # D-score del segundo iat

    # Nuevo campo para la pregunta moral
    moral_question = models.StringField(label="Aquí va una pregunta moral", blank=True)

    # nuevo campo de preguntas morales, con algunas de relleno:
    # 1. Pregunta central — moralidad vs intuición (alta carga reflexiva)
    preguntaM1 = models.LongStringField(
        label="Describe una situación en la que sabías cuál era la acción moralmente correcta según tus principios, pero intuitivamente sentías que debías actuar de otra manera. ¿Qué hiciste y por qué?"
    )

    # 2. Principios personales — moralidad autónoma
    preguntaM2 = models.LongStringField(
        label="¿Qué significa para ti actuar de forma moralmente correcta, incluso cuando nadie te está observando?"
    )

    # 3. Aplicación práctica de valores — contexto cotidiano
    preguntaM3 = models.LongStringField(
        label="Piensa en una decisión difícil que hayas tomado recientemente. ¿Qué valores o principios influyeron en lo que decidiste?"
    )

    # 4. Dilema cotidiano — tensión entre normas y práctica
    preguntaM4 = models.LongStringField(
        label="¿Hay alguna regla o norma moral que consideres importante, pero que a veces te resulte difícil seguir? ¿Por qué?"
    )

    # 5. Pregunta proyectiva — diseño ideal (relleno con carga valorativa)
    preguntaM5 = models.LongStringField(
        label="Si fueras responsable de diseñar una escuela ideal, ¿qué valores te gustaría que se enseñaran desde temprana edad?"
    )

    # (opcional) 6. Pregunta de relleno informal — preferencias personales
    preguntaM6 = models.LongStringField(
        label="¿Cuál es una cualidad que más valoras en otras Personas (por ejemplo: creatividad, lealtad, inteligencia, honestidad)? ¿Por qué?"
    )

    iat1_self_assessment = models.StringField(
        label="¿Cómo crees que te fue en el IAT de Personas obesas y Personas delgadas?",
        choices=[
        "Neutral",
        "Leve: Personas delgadas+bueno, Personas obesas+malo",
        "Moderada: Personas delgadas+bueno, Personas obesas+malo",
        "Fuerte: Personas delgadas+bueno, Personas obesas+malo",
        "Leve: Personas obesas+bueno, Personas delgadas+malo",
        "Moderada: Personas obesas+bueno, Personas delgadas+malo",
        "Fuerte: Personas obesas+bueno, Personas delgadas+malo",
    ],
        widget=widgets.RadioSelect
    )

    iat2_self_assessment = models.StringField(
        label="¿Cómo crees que te fue en el IAT de Personas homosexuales y Personas heterosexuales?",
        choices=[
            "Neutral",
            "Leve: Personas heterosexuales+bueno, Personas homosexuales+malo",
            "Moderada: Personas heterosexuales+bueno, Personas homosexuales+malo",
            "Fuerte: Personas heterosexuales+bueno, Personas homosexuales+malo",
            "Leve: Personas homosexuales+bueno, Personas heterosexuales+malo",
            "Moderada: Personas homosexuales+bueno, Personas heterosexuales+malo",
            "Fuerte: Personas homosexuales+bueno, Personas heterosexuales+malo",
        ],
        widget=widgets.RadioSelect
    )

    # Variables para el rango moralmente aceptable del iat 1. nota: hay que cambiar esto para que vayan de -2 a 2.
    iat2_lower_limit = models.FloatField(
        label="¿Cuál es el límite inferior del rango aceptable para el IAT Personas homosexuales y Personas heterosexuales?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat2_upper_limit = models.FloatField(
        label="¿Cuál es el límite superior del rango aceptable para el IAT Personas homosexuales y Personas heterosexuales?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    # Variables para el rango moralmente aceptable del iat 2
    iat1_lower_limit = models.FloatField(
        label="¿Cuál es el límite inferior del rango aceptable para el IAT Personas obesas y Personas delgadas?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat1_upper_limit = models.FloatField(
        label="¿Cuál es el límite superior del rango aceptable para el IAT Personas obesas y Personas delgadas?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat2_probability_right = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "homosexuales y el otro grupo es una o más personas heterosexuales. Además supón "
            "que tu puntaje en la prueba de asociación implícita con gente homosexual y heterosexual "
            "cae por arriba del rango que consideras aceptable. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los homosexuales y el grupo B son los heterosexuales, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat1_probability_left = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "obesas y el otro grupo es una o más personas delgadas. Además supón "
            "que tu puntaje en la prueba de asociación implícita con gente gorda y delgada "
            "cae por debajo del rango que consideras aceptable. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat2_probability_left = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "homosexuales y el otro grupo es una o más personas heterosexuales. Además supón "
            "que tu puntaje en la prueba de asociación implícita con gente homosexual y heterosexual "
            "cae por debajo del rango que consideras aceptable. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los homosexuales y el grupo B son los heterosexuales, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat1_probability_right = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "obesas y el otro grupo es una o más personas delgadas. Además supón "
            "que tu puntaje en la prueba de asociación implícita con gente gorda y delgada "
            "cae por arriba del rango que consideras aceptable. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat2_probability = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "homosexuales y el otro grupo es una o más personas heterosexuales. Además supón "
            "que tu puntaje en la prueba de asociación implícita con gente homosexual y heterosexual "
            "cae en el rango que consideras aceptable. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los homosexuales y el grupo B son los heterosexuales, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat1_probability = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "obesas y el otro grupo es una o más personas delgadas. Además supón "
            "que tu puntaje en la prueba de asociación implícita con gente gorda y delgada "
            "cae en el rango que consideras aceptable. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat2_probability_right2 = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "gordas y el otro grupo es una o más personas delgadas. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat1_probability_left2 = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "gordas y el otro grupo es una o más personas delgadas. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat2_probability_left2 = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "gordas y el otro grupo es una o más personas delgadas. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat1_probability_right2 = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "gordas y el otro grupo es una o más personas delgadas. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat2_probability2 = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "gordas y el otro grupo es una o más personas delgadas. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    iat1_probability2 = models.BooleanField(
        label=(
            "Supón que en la Etapa 6 tomas una decisión con consecuencias monetarias "
            "para el Grupo A y el Grupo B, donde uno de los grupos es una o más personas "
            "gordas y el otro grupo es una o más personas delgadas. ¿Qué prefieres?"
        ),
        widget=widgets.RadioSelect,
        choices=[
            (True,
             "Saber quiénes son del grupo A y quiénes son del grupo B (esto es, sabes si el grupo A son los gordos y el grupo B son los delgados, o al revés)."),
            (False, "No saber quiénes son del grupo A y quiénes son del grupo B."),
        ],
        blank=True,
    )

    # Variables para capturar la asociación calculada (se asignan en DictatorIntroduction)
    iat1_association = models.StringField(blank=True)
    iat2_association = models.StringField(blank=True)

    # Nuevas variables para capturar si el jugador adivinó su resultado
    iat1_guess_correct = models.BooleanField(blank=True)
    iat2_guess_correct = models.BooleanField(blank=True)

    # Nuevas variables para capturar si el iat del jugador está en su rango moralmente aceptable
    iat1_moral_range = models.BooleanField(blank=True)
    iat2_moral_range = models.BooleanField(blank=True)

    # Nuevas variables para capturar si el iat del jugador está en su rango moralmente aceptable
    iat1_moral_range_left = models.BooleanField(blank=True)
    iat2_moral_range_left = models.BooleanField(blank=True)

    # Nuevas variables para capturar si el iat del jugador está en su rango moralmente aceptable
    iat1_moral_range_right = models.BooleanField(blank=True)
    iat2_moral_range_right = models.BooleanField(blank=True)



    # campos para el juego del dictador.
    dictator_offer = models.CurrencyField(
        min=0,
        max=Constants.endowment,
        label="¿Cuánto te gustaría ofrecer?"
    )

    # ——— Cuestionario grupo 1 —————

    compr1_q1 = models.StringField(
        choices=[
            ['A', 'Un puntaje bueno indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['B', 'Un puntaje bueno indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje malo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['C', 'Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje bueno indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['D', 'Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje malo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['E', 'Un puntaje malo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['F', 'Un puntaje malo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje bueno indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="Supón que haces una Prueba de asociación implícita que involucra a grupos A y B, en donde el grupo B es el grupo “base”. ¿Qué puntaje indicaría que tu sesgo implícito es igual al promedio de cientos de miles de participantes? ¿Qué puntaje indicaría que tu sesgo implícito favorece al grupo A más que el promedio de cientos de miles de participantes?"
    )

    # Pregunta 2 para grupo 1 (ahora radio, no múltiple)
    compr1_q2 = models.StringField(
        choices=[
            ['A',
             'Primero, hay una base de datos con cientos de miles de participantes que ya tomaron la prueba. Segundo, fue desarrollado por académicos.'],
            ['B',
             'Primero, está ligado a comportamientos relevantes en el mundo real. Segundo, es difícil de manipular ya que mide tu respuesta automática, sin que hayas tenido tiempo de pensar.'],
            ['C', 'Primero, no existen otras pruebas para medir sesgos. Segundo, es fácil de implementar.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="¿Cuáles son las dos características que hacen que la iat sea una manera robusta de medir sesgos que tal vez ni siquiera sabías que tenías?"
    )

    compr1_order = models.LongStringField(
        blank=True,
        label="Arrastra las etapas para ponerlas en el orden correcto:"
    )

    compr1_q4 = models.StringField(
        choices=[
            ['A', 'Tomas una sola decisión sobre todos los grupos a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de todos los grupos cuando estés en la Etapa 6.'],
            ['B', 'Tomas una decisión para cada grupo a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de cada grupo cuando estés en la Etapa 6.'],
            ['C', 'Nos vas a decir si quieres que te revelemos la identidad de los grupos correspondientes a una decisión dependiendo de si tu puntaje en la iat cayó debajo, dentro o arriba del rango que consideras aceptable. '],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="En la Etapa 5 (qué información revelar en la Etapa 6), ¿cómo tomas la decisión de qué se te revela en la Etapa 6?"
    )

    compr1_q5 = models.StringField(
        choices=[
            ['A', 'Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D.'],
            ['B', 'Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D.'],
            ['C', 'Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D. '],
            ['D', 'Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="Supón que nos indicas que quieres que en la Etapa 6 te revelemos la identidad de los grupos A y B, y que no te revelemos la identidad de los grupos C y D. ¿Qué haríamos en la práctica?"
    )

    compr1_q6 = models.StringField(
        choices=[
            ['A', 'Ninguna decisión involucra a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y sólo vamos a incluir decisiones que no afecten a las Personas sobre las que te preguntamos en la Etapa 2. '],
            ['B', 'No todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y es posible que incluyamos decisiones que no afecten a algunas de las Personas sobre las que te preguntamos en la Etapa 2. '],
            ['C', 'Todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y ninguna decisión van a incluir a grupos de Personas sobre las que no te preguntamos en la Etapa 2.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="Escoge la opción correcta sobre tus decisiones en la Etapa 6."
    )

    # ——— Cuestionario grupo 2 —————

    compr2_q1 = models.StringField(
        choices=[
            ['A', 'Un puntaje bueno indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['B', 'Un puntaje bueno indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje malo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'],
            ['C', 'Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje bueno indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['D', 'Un puntaje de cero indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje malo indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['E', 'Un puntaje malo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. '],
            ['F', 'Un puntaje malo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje bueno indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="Supón que haces una Prueba de asociación implícita que involucra a grupos A y B, en donde el grupo B es el grupo “base”. ¿Qué puntaje indicaría que tu sesgo implícito es igual al promedio de cientos de miles de participantes? ¿Qué puntaje indicaría que tu sesgo implícito favorece al grupo A más que el promedio de cientos de miles de participantes?"
    )

    # Pregunta 2 para grupo 2 (igual)
    compr2_q2 = models.StringField(
        choices=[
            ['A',
             'Primero, hay una base de datos con cientos de miles de participantes que ya tomaron la prueba. Segundo, fue desarrollado por académicos.'],
            ['B',
             'Primero, está ligado a comportamientos relevantes en el mundo real. Segundo, es difícil de manipular ya que mide tu respuesta automática, sin que hayas tenido tiempo de pensar.'],
            ['C', 'Primero, no existen otras pruebas para medir sesgos. Segundo, es fácil de implementar.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="¿Cuáles son las dos características que hacen que la iat sea una manera robusta de medir sesgos que tal vez ni siquiera sabías que tenías?"
    )

    compr2_order = models.LongStringField(
        blank=True,
        label="Arrastra las etapas para ponerlas en el orden correcto:"
    )

    compr2_q4 = models.StringField(
        choices=[
            ['A', 'Tomas una sola decisión sobre todos los grupos a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de todos los grupos cuando estés en la Etapa 6.'],
            ['B', 'Tomas una decisión para cada grupo a los cuales puedes afectar monetariamente en la Etapa 6: decides directamente si se te informa o no sobre la identidad de cada grupo cuando estés en la Etapa 6.'],
            ['C', 'Nos vas a decir si quieres que te revelemos la identidad de los grupos correspondientes a una decisión dependiendo de si tu puntaje en la iat cayó debajo, dentro o arriba del rango que consideras aceptable.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="En la Etapa 5 (qué información revelar en la Etapa 6), ¿cómo tomas la decisión de qué se te revela en la Etapa 6?"
    )

    compr2_q5 = models.StringField(
        choices=[
            ['A', 'Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D.'],
            ['B', 'Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la dentidad de los grupos C y D.'],
            ['C', 'Te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D.'],
            ['D', 'Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="Supón que nos indicas que quieres que en la Etapa 6 te revelemos la identidad de los grupos A y B, y que no te revelemos la identidad de los grupos C y D. ¿Qué haríamos en la práctica?"
    )

    compr2_q6 = models.StringField(
        choices=[
            ['A', 'Ninguna decisión involucra a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y sólo vamos a incluir decisiones que no afecten a las Personas sobre las que te preguntamos en la Etapa 2.'],
            ['B', 'No todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y es posible que incluyamos decisiones que no afecten a algunas de las Personas sobre las que te preguntamos en la Etapa 2.'],
            ['C', 'Todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y ninguna decisión van a incluir a grupos de Personas sobre las que no te preguntamos en la Etapa 2.'],
        ],
        blank=True,
        widget=widgets.RadioSelect,
        label="Escoge la opción correcta sobre tus decisiones en la Etapa 6."
    )


class Group(BaseGroup):
    dictator_category = models.StringField(
        label="Categoría Asignada",
        doc="""Categoría a la que se asignará dinero en esta ronda."""
    )
    kept = models.CurrencyField(
        label="¿Cuánto deseas mantener para ti mismo?",
        min=0,
        max=Constants.endowment,
        doc="""Cantidad que el jugador decide mantener."""
    )
    assigned = models.CurrencyField(
        label="Asignación a la Categoría",
        min=0,
        max=Constants.endowment,
        doc="""Cantidad asignada a la categoría."""
    )


def get_actual_iat_round(player: Player):
    order = player.participant.vars.get('iat_round_order')
    if order and player.round_number <= 14:
        return order[player.round_number - 1]
    return player.round_number


def set_payoffs(group: Group):
    """
    Asigna los payoffs basados en la decisión del jugador.
    El jugador mantiene 'kept' y asigna el resto a la categoría.
    """
    kept = group.kept
    assigned = Constants.endowment - kept

    # Validar que la asignación sea correcta
    if assigned < 0 or kept < 0 or kept > Constants.endowment:
        # Manejar errores: asignar valores predeterminados o lanzar excepciones
        group.assigned = 0
        group.kept = Constants.endowment
    else:
        group.assigned = assigned

    # Asignar el payoff al jugador (manteniendo 'kept')
    for player in group.get_players():
        player.payoff = kept


class Trial(ExtraModel):
    """A record of single iteration
    Keeps corner categories from round setup to simplify furher analysis.
    The stimulus class is for appropriate styling on page.
    """

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    stimulus_cls = models.StringField(choices=('primary', 'secondary'))
    stimulus_cat = models.StringField()
    stimulus = models.StringField()
    correct = models.StringField(choices=('left', 'right'))

    response = models.StringField(choices=('left', 'right'))
    response_timestamp = models.FloatField()
    reaction_time = models.FloatField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


def generate_trial(player: Player) -> Trial:
    """Create new question for a player"""
    actual_round = get_actual_iat_round(player)
    block = get_block_for_round(actual_round, player.session.params)
    chosen_side = random.choice(['left', 'right'])
    chosen_cls = random.choice(list(block[chosen_side].keys()))
    chosen_cat = block[chosen_side][chosen_cls]
    stimulus = random.choice(stimuli.DICT[chosen_cat])

# 27 de febrero del 2025. esto era lo que faltaba para que las imágnes se mostraran correctamente.
    player.iteration += 1
    return Trial.create(
        player=player,
        iteration=player.iteration,
        timestamp=time.time(),
        stimulus_cls=chosen_cls,
        stimulus_cat=chosen_cat,
        stimulus=stimulus,
        correct=chosen_side,
    )

def get_current_trial(player: Player):
    """Get last (current) question for a player"""
    trials = Trial.filter(player=player, iteration=player.iteration)
    if trials:
        [trial] = trials
        return trial


def encode_trial(trial: Trial):
    return dict(
        cls=trial.stimulus_cls,
        cat=trial.stimulus_cat,
        stimulus=url_for_image(trial.stimulus) if trial.stimulus.endswith((".png", ".jpg")) else str(trial.stimulus),
    )


def get_progress(player: Player):
    """Return current player progress"""
    return dict(
        num_trials=player.num_trials,
        num_correct=player.num_correct,
        num_incorrect=player.num_failed,
        iteration=player.iteration,
        total=get_num_iterations_for_round(player),
    )


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

def play_game(player: Player, message: dict):
    try:
        session = player.session
        my_id = player.id_in_group
        ret_params = session.params
        max_iters = get_num_iterations_for_round(player)
        now = time.time()
        current = get_current_trial(player)
        message_type = message.get('type')

        # Caso "load": la página se ha cargado
        if message_type == 'load':
            p = get_progress(player)
            if current:
                return {my_id: dict(type='status', progress=p, trial=encode_trial(current))}
            else:
                return {my_id: dict(type='status', progress=p)}

        # Caso "next": solicitud de un nuevo trial
        elif message_type == 'next':
            if current is not None:
                if current.response is None:
                    return {my_id: dict(type='error', message="Debes resolver el trial actual antes de continuar.")}
                if now < current.timestamp + ret_params["trial_delay"]:
                    return {my_id: dict(type='error', message="Estás intentando avanzar demasiado rápido.")}
                if current.iteration == max_iters:
                    return {my_id: dict(type='status', progress=get_progress(player), iterations_left=0)}
            # Generar y retornar un nuevo trial
            new_trial = generate_trial(player)
            p = get_progress(player)
            return {my_id: dict(type='trial', trial=encode_trial(new_trial), progress=p)}

        # Caso "answer": el jugador envía una respuesta
        elif message_type == "answer":
            if current is None:
                return {my_id: dict(type='error', message="No hay trial activo para responder.")}
            # Si ya se respondió previamente, se trata de un reintento
            if current.response is not None:
                if now < current.response_timestamp + ret_params["retry_delay"]:
                    return {my_id: dict(type='error', message="Estás respondiendo demasiado rápido.")}
                # Revertir la actualización previa del progreso
                player.num_trials -= 1
                if current.is_correct:
                    player.num_correct -= 1
                else:
                    player.num_failed -= 1

            answer = message.get("answer")
            if not answer:
                return {my_id: dict(type='error', message="Respuesta inválida.")}
            current.response = answer
            current.reaction_time = message.get("reaction_time", 0)
            current.is_correct = (current.correct == answer)
            current.response_timestamp = now

            if current.is_correct:
                player.num_correct += 1
            else:
                player.num_failed += 1
            player.num_trials += 1

            p = get_progress(player)
            return {my_id: dict(type='feedback', is_correct=current.is_correct, progress=p)}

        # Caso "cheat": modo de depuración en DEBUG para generar datos automáticamente
        elif message_type == "cheat" and settings.DEBUG:
            m = float(message.get('reaction', 0))
            if current:
                current.delete()
            for i in range(player.iteration, max_iters):
                t = generate_trial(player)
                t.iteration = i
                t.timestamp = now + i
                t.response = t.correct
                t.is_correct = True
                t.response_timestamp = now + i
                t.reaction_time = random.gauss(m, 0.3)
            return {my_id: dict(type='status', progress=get_progress(player), iterations_left=0)}

        # Mensaje no reconocido
        else:
            return {my_id: dict(type='error', message="Mensaje no reconocido del cliente.")}

    except Exception as e:
        # Captura cualquier error inesperado y lo devuelve en el mensaje de error
        return {player.id_in_group: dict(type='error', message=str(e))}


# PAGES
# sobre los cambios del 25 de mayo del 2025: pre-correr el experimento: pensé que tenía que agregar muchas rondas para las instrucciones nuevas, pero simplemente
# puedo agregar páginas para que se muestren en un orden que tenga sentido. Qué tranquilidad.





class Intro(Page):
    # comentario en caso de ser necesario: cambié está página para que se
    # pudiera mostrar los labels correctos de inicios del iat, pero causó un
    # problema con el primer intento, si esto vuelve a suceder, regresar al
    # sigueiente código:
    #     @staticmethod
    #     def is_displayed(player):
    #         # Display the page in rounds 1 and 8
    #         return player.round_number in [1, 8]
    #
    #     @staticmethod
    #     def vars_for_template(player: Player):
    #         # Determine the block based on the round number
    #         params = player.session.params
    #         if player.round_number == 1:
    #             block = get_block_for_round(3, params)  # Use block for round 3 in round 1
    #         elif player.round_number == 8:
    #             block = get_block_for_round(10, params)  # Use block for round 10 in round 8
    #         else:
    #             block = None  # Fallback in case of unexpected behavior
    #
    #         return dict(
    #             params=params,
    #             labels=labels_for_block(block) if block else {},
    #         )

    @staticmethod
    def is_displayed(player):
        return player.round_number in [1, 8]

    @staticmethod
    def vars_for_template(player: Player):
        params = player.session.params
        iat_round_order = player.participant.vars.get('iat_round_order', [])

        if iat_round_order == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
            block_number = {1: 3, 8: 10}
        elif iat_round_order == [8, 9, 10, 11, 12, 13, 14, 1, 2, 3, 4, 5, 6, 7]:
            block_number = {1: 10, 8: 3}
        else:
            block_number = {}

        block_id = block_number.get(player.round_number, None)
        # Asegurar que block sea un diccionario válido
        block = get_block_for_round(block_id, params) if block_id else None

        return dict(
            params=params,
            labels=labels_for_block(block) if isinstance(block, dict) else {},
        )


class RoundN(Page):
    template_name = "iat/Main.html"

    @staticmethod
    def is_displayed(player: Player):
        # Mostrar solo en rondas de iat
        return player.round_number <= 14

    @staticmethod
    def js_vars(player: Player):
        actual_round = get_actual_iat_round(player)
        return dict(
            params=player.session.params,
            keys=Constants.keys,
            actual_round=actual_round
        )

    @staticmethod
    def vars_for_template(player: Player):
        actual_round = get_actual_iat_round(player)
        params = player.session.params
        block = get_block_for_round(actual_round, params)
        return dict(
            params=params,
            block=block,
            thumbnails=thumbnails_for_block(block, params),
            labels=labels_for_block(block),
            num_iterations=get_num_iterations_for_round(player),
            DEBUG=settings.DEBUG,
            keys=Constants.keys,
            lkeys="/".join(
                [k for k in Constants.keys.keys() if Constants.keys[k] == 'left']
            ),
            rkeys="/".join(
                [k for k in Constants.keys.keys() if Constants.keys[k] == 'right']
            ),
        )

    live_method = play_game


class UserInfo(Page):
    form_model = 'player'
    form_fields = ['edad', 'sexo', 'ha_participado', 'num_experimentos']

    @staticmethod
    def is_displayed(player):
        return not player.participant.vars.get('user_info_completed', False)

    @staticmethod
    def error_message(player, values):
        if values['ha_participado'] == 'Sí' and values['num_experimentos'] is None:
            return "Por favor indica en cuántos experimentos has participado."


    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        participant = player.participant
        if player.ha_participado != 'Sí':
            player.num_experimentos = 0
        participant.vars['user_info_completed'] = True


class PreguntaM(Page):
    form_model = 'player'
    form_fields = ['preguntaM1', 'preguntaM2', 'preguntaM3', 'preguntaM4', 'preguntaM5', 'preguntaM6']

    @staticmethod
    def is_displayed(player):
        # Mostrar esta página solo una vez por participante
        return player.participant.vars.get('pregunta_moral_completada', False) == False

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Marcar que la página ya fue completada
        player.participant.vars['pregunta_moral_completada'] = True

    @staticmethod
    def error_message(player, values):
        # Validar que ninguno de los campos esté vacío
        preguntas = ['preguntaM1', 'preguntaM2', 'preguntaM3', 'preguntaM4', 'preguntaM5', 'preguntaM6']
        for p in preguntas:
            if not values.get(p):
                return "Por favor, responde todas las preguntas antes de continuar."
#pie
# acá el detalle es que las validaciones de los campos están mal, aunque fáciles de cambiar, no lo haré ahora. 4 de febrero del 2025.
class Comprension1(Page):
    form_model = 'player'
    form_fields = [
        'compr1_q1',
        'compr1_q2',
        'compr1_order',
        'compr1_q4',
        'compr1_q5',
        'compr1_q6',
    ]
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order') == list(range(1, 15))
            and not player.participant.vars.get('compr1_shown', False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['compr1_shown'] = True

    @staticmethod
    def vars_for_template(player):
        stages = [
            "Sociodemográfica",
            "Pruebas de asociación implícita",
            "Adivinas tus puntajes en las pruebas de la Etapa 2",
            "Rango aceptable de puntajes en las pruebas de la Etapa 2",
            "Qué información revelar en las decisiones de la Etapa 6",
            "Decisiones monetarias que pueden afectar a grupos de la Etapa 2",
        ]
        return {'stages': stages}

    @staticmethod
    def error_message(player: Player, values):
        # Requiere que TODOS los campos tengan valor
        for field in Comprension1.form_fields:
            if not values.get(field):
                return "Por favor, responde todas las preguntas antes de continuar."



class Comprension2(Page):
    form_model = 'player'
    form_fields = [
        'compr2_q1',
        'compr2_q2',
        'compr2_order',
        'compr2_q4',
        'compr2_q5',
        'compr2_q6',
    ]

    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order')
                == (list(range(8, 15)) + list(range(1, 8)))
            and not player.participant.vars.get('compr2_shown', False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['compr2_shown'] = True

    @staticmethod
    def vars_for_template(player):
        stages = [
            "Sociodemográfica",
            "Pruebas de asociación implícita",
            "Adivinas tus puntajes en las pruebas de la Etapa 2",
            "Rango aceptable de puntajes en las pruebas de la Etapa 2",
            "Qué información revelar en las decisiones de la Etapa 6",
            "Decisiones monetarias que pueden afectar a grupos de la Etapa 2",
        ]
        return {'stages': stages}

    @staticmethod
    def error_message(player: Player, values):
        # Requiere que TODOS los campos tengan valor
        for field in Comprension2.form_fields:
            if not values.get(field):
                return "Por favor, responde todas las preguntas antes de continuar."

# Feedback para el grupo 1
class Feedback1(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order', []) == list(range(1, 15))
            and not player.participant.vars.get('feedback1_shown', False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['feedback1_shown'] = True

    @staticmethod
    def vars_for_template(player: Player):
        # Respuestas correctas
        correct = {
            'compr1_q1': 'Un puntaje malo indica que mi sesgo implícito es igual al promedio de cientos de miles de participantes. Un puntaje de cero indica que mi sesgo implícito favorece al grupo A más que cientos de miles de participantes. ',
            'compr1_q2': 'Primero, está ligado a comportamientos relevantes en el mundo real. Segundo, es difícil de manipular ya que mide tu respuesta automática, sin que hayas tenido tiempo de pensar.',
            'compr1_order': "Sociodemográfica, Pruebas de asociación implícita, Adivinas tus puntajes en las pruebas de la Etapa 2, "
                            "Rango aceptable de puntajes en las pruebas de la Etapa 2, Qué información revelar en las decisiones de la Etapa 6, "
                            "Decisiones monetarias que pueden afectar a grupos de la Etapa 2",
            'compr1_q4': 'Nos vas a decir si quieres que te revelemos la identidad de los grupos correspondientes a una decisión dependiendo de si tu puntaje en la iat cayó debajo, dentro o arriba del rango que consideras aceptable. ',
            'compr1_q5': 'Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% de probabilidad sí te revelamos la identidad de los grupos C y D.',
            'compr1_q6': 'No todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en las pruebas de la Etapa 2, y es posible que incluyamos decisiones que no afecten a algunas de las Personas sobre las que te preguntamos en la Etapa 2. ',
        }
        # Explicaciones
        explanation = {
            'compr1_q1': (
                "Tu puntaje se compara con los datos de Project Implicit, una base con cientos de miles de participantes. "
                "Una puntuación de cero representa el promedio de dicha base. La interpretación del puntaje depende "
                "de cuál de los dos grupos es el grupo “base” para fines de la comparación. En la pregunta, el grupo B "
                "es el grupo “base”. Un puntaje bueno indicaría que, comparado a la base de datos de Project Implicit, "
                "el/la participante asocia con mayor facilidad a los del grupo B con los atributos buenos en comparación "
                "con la asociación que hace con los del grupo A. Un puntaje malo indica una asociación relativamente "
                "más fuerte de los del grupo A con atributos buenos en comparación con la asociación con los del grupo B."
            ),
            'compr1_q2': (
                "Como mostramos con los estudios que mencionamos, hay mucha evidencia que la iat "
                "está ligada a comportamientos relevantes en el mundo real. A diferencia de otras pruebas, la Prueba de Asociación "
                "Implícita es difícil de manipular ya que mide tu respuesta automática—tu primera reacción, sin haber tenido tiempo "
                "para pensar."
            ),
            'compr1_order': (""),
            'compr1_q4': (
                "No es directa la decisión sobre la información que se te revela—no te vamos a preguntar simplemente si quieres "
                "que se te revele la información sobre cada grupo. En vez de eso, la decisión va a depender de tus puntajes en "
                "las pruebas de asociación implícita y en el rango de puntajes aceptables que nos diste en la cuarta etapa."
            ),
            'compr1_q5': (
                "Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos "
                "la identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con "
                "20% de probabilidad sí te revelamos la identidad de los grupos C y D."
            ),
            'compr1_q6': (
                "No todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en la Etapa 2, y es posible "
                "que incluyamos decisiones que afecten a grupos de Personas sobre las que no te preguntamos en la Etapa 2."
            ),
        }
        # Labels manuales
        labels = {
            'compr1_q1': "Supón que haces una Prueba de asociación implícita que involucra a grupos A y B, en donde el grupo B es el grupo “base”. ¿Qué puntaje indicaría que tu sesgo implícito es igual al promedio de cientos de miles de participantes? ¿Qué puntaje indicaría que tu sesgo implícito favorece al grupo A más que el promedio de cientos de miles de participantes?",
            'compr1_q2': "¿Cuáles son las dos características que hace que la iat sea una manera robusta de medir sesgos que tal vez ni siquiera sabías que tenías?",
            'compr1_order': "Arrastra las etapas para ponerlas en el orden correcto:" ,
            'compr1_q4': "En la Etapa 5 (qué información revelar en la Etapa 6), ¿cómo tomas la decisión de qué se te revela en la Etapa 6?",
            'compr1_q5': "Supón que nos indicas que quieres que en la Etapa 6 te revelemos la identidad de los grupos A y B, y que no te revelemos la identidad de los grupos C y D. ¿Qué haríamos en la práctica?",
            'compr1_q6': "Escoge la opción correcta sobre tus decisiones en la Etapa 6.",
        }

        feedback = []
        for field in ['compr1_q1', 'compr1_q2', 'compr1_order', 'compr1_q4', 'compr1_q5', 'compr1_q6']:
            your = getattr(player, field)
            corr = correct[field]
            is_corr = (your == corr) if not isinstance(corr, list) else (set(your or []) == set(corr))
            feedback.append({
                'label': labels[field],
                'your_answer': your,
                'correct_answer': corr,
                'is_correct': is_corr,
                'explanation': explanation[field],
            })
        return {'feedback': feedback}

# Feedback para el grupo 2
class Feedback2(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order', [])
                == (list(range(8, 15)) + list(range(1, 8)))
            and not player.participant.vars.get('feedback2_shown', False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['feedback2_shown'] = True

    @staticmethod
    def vars_for_template(player: Player):
        # Respuestas correctas
        correct = {
            'compr2_q1': 'E',
            'compr2_q2': ['B'],
            'compr2_order': "Sociodemográfica, Pruebas de asociación implícita, Adivinas tus puntajes en las pruebas de la Etapa 2, "
                            "Rango aceptable de puntajes en las pruebas de la Etapa 2, Qué información revelar en las decisiones "
                            "de la Etapa 6, Decisiones monetarias que pueden afectar a grupos de la Etapa 2",
            'compr2_q4': 'C',
            'compr2_q5': 'D',
            'compr2_q6': 'B',
        }
        # Explicaciones (idénticas a las de Feedback1, copiadas manualmente)
        explanation = {
            'compr2_q1': (
                "Tu puntaje se compara con los datos de Project Implicit, una base con cientos de miles de participantes. "
                "Una puntuación de cero representa el promedio de dicha base. La interpretación del puntaje depende "
                "de cuál de los dos grupos es el grupo “base” para fines de la comparación. En la pregunta, el grupo B "
                "es el grupo “base”. Un puntaje bueno indicaría que, comparado a la base de datos de Project Implicit, "
                "el/la participante asocia con mayor facilidad a los del grupo B con los atributos buenos en comparación "
                "con la asociación que hace con los del grupo A. Un puntaje malo indica una asociación relativamente "
                "más fuerte de los del grupo A con atributos buenos en comparación con la asociación con los del grupo B."
            ),
            'compr2_q2': (
                "Como mostramos con los estudios que mencionamos, hay mucha evidencia que la iat "
                "está ligada a comportamientos relevantes en el mundo real. A diferencia de otras pruebas, la Prueba de Asociación "
                "Implícita es difícil de manipular ya que mide tu respuesta automática—tu primera reacción, sin haber tenido tiempo "
                "para pensar."
            ),
            'compr2_order': (
                "El orden correcto de las etapas es: Sociodemográfica; Pruebas de asociación implícita; Adivinas tus puntajes "
                "en las pruebas de la Etapa 2; Rango aceptable de puntajes en las pruebas de la Etapa 2; Qué información revelar "
                "en las decisiones de la Etapa 6; Decisiones monetarias que pueden afectar a grupos de la Etapa 2."
            ),
            'compr2_q4': (
                "Es directa la decisión—siguiendo el ejemplo, te preguntaríamos simplemente si quieres que se te revele la información "
                "sobre indígenas y mestizo. Si en la Etapa 6 tomas una decisión que afecta a mestizos e indígenas, te vamos a reportar "
                "que esa decisión va a afectar a indígenas sólo si así nos lo indicaste."
            ),
            'compr2_q5': (
                "Te revelamos la identidad de los grupos A y B con 80% de probabilidad, y con 20% de probabilidad no te revelamos la "
                "identidad de los grupos A y B. No te revelamos la identidad de los grupos C y D con 80% de probabilidad, y con 20% "
                "de probabilidad sí te revelamos la identidad de los grupos C y D."
            ),
            'compr2_q6': (
                "No todas las decisiones involucran a los grupos de Personas sobre las que te preguntamos en la Etapa 2, y es posible "
                "que incluyamos decisiones que afecten a grupos de Personas sobre las que no te preguntamos en la Etapa 2."
            ),
        }
        # Labels manuales (igual a los que pusiste en tu modelo)
        labels = {
            'compr2_q1': "Supón que haces una Prueba de asociación implícita que involucra a grupos A y B, en donde el grupo B es el grupo “base”. ¿Qué puntaje indicaría que tu sesgo implícito es igual al promedio de cientos de miles de participantes? ¿Qué puntaje indicaría que tu sesgo implícito favorece al grupo A más que el promedio de cientos de miles de participantes?",
            'compr2_q2': "¿Cuáles son las dos características que hace que la iat sea una manera robusta de medir sesgos que tal vez ni siquiera sabías que tenías?",
            'compr2_order': "Arrastra las etapas para ponerlas en el orden correcto:",
            'compr2_q4': "En la Etapa 5 (qué información revelar en la Etapa 6), ¿cómo tomas la decisión de qué se te revela en la Etapa 6?",
            'compr2_q5': "Supón que nos indicas que quieres que en la Etapa 6 te revelemos la identidad de los grupos A y B, y que no te revelemos la identidad de los grupos C y D. ¿Qué haríamos en la práctica?",
            'compr2_q6': "Escoge la opción correcta sobre tus decisiones en la Etapa 6.",
        }

        feedback = []
        for field in ['compr2_q1', 'compr2_q2', 'compr2_order', 'compr2_q4', 'compr2_q5', 'compr2_q6']:
            your = getattr(player, field)
            corr = correct[field]
            is_corr = (your == corr) if not isinstance(corr, list) else (set(your or []) == set(corr))
            feedback.append({
                'label': labels[field],
                'your_answer': your,
                'correct_answer': corr,
                'is_correct': is_corr,
                'explanation': explanation[field],
            })
        return {'feedback': feedback}

class InstruccionesGenerales1(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order') == list(range(1, 15))
            and not player.participant.vars.get('user_generales1_completed', False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['user_generales1_completed'] = True


class InstruccionesGenerales2(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get('iat_round_order')
                == (list(range(8, 15)) + list(range(1, 8)))
            and not player.participant.vars.get('user_generales2_completed', False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['user_generales2_completed'] = True

class InstruccionesGenerales3(Page):
    @staticmethod
    def is_displayed(player):
        return (
            player.participant.vars.get('user_generales2_completed', False)
            and not player.participant.vars.get('user_generales3_completed', False)
        )

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.vars['user_generales3_completed'] = True



# creo que hay el grave problema (no tan grave) que cambié algo de la sinxtaxis y ahora solamente permite guess neutral
class IATAssessmentPage(Page):
    form_model = 'player'
    form_fields = [
        'iat1_self_assessment',
        'iat2_self_assessment',
        'iat2_lower_limit',  # Límite inferior para el iat negro blanco
        'iat2_upper_limit',  # Límite superior para el iat negro blanco
        'iat1_lower_limit',  # Límite inferior para el iat blanco negro
        'iat1_upper_limit'  # Límite superior para el iat blanco negro
    ]

    @staticmethod
    def is_displayed(player: Player):
        # Mostrar esta página solo en la ronda 15
        return player.round_number == 15

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        # Se obtiene la categoría asignada (usada en otros contextos, por ejemplo en el Dictator Game)
        if group.dictator_category:
            category = group.dictator_category.capitalize()
        else:
            category = "Sin categoría asignada"

        # Función para extraer los tiempos de reacción de las rondas especificadas
        def extract(rnd):
            trials = [
                t
                for t in Trial.filter(player=player.in_round(rnd))
                if t.reaction_time is not None
            ]
            return [t.reaction_time for t in trials]

        # Extraer datos para el primer iat (rondas 3, 4, 6, 7)
        data3 = extract(3)
        data4 = extract(4)
        data6 = extract(6)
        data7 = extract(7)
        dscore1_result = dscore1(data3, data4, data6, data7)

        # Extraer datos para el segundo iat (rondas 10, 13, 11, 14)
        data10 = extract(10)
        data13 = extract(13)
        data11 = extract(11)
        data14 = extract(14)
        dscore2_result = dscore2(data10, data13, data11, data14)

        # Recuperar el orden de las rondas y asignar dscores según ello
        iat_round_order = player.participant.vars.get('iat_round_order', [])
        if iat_round_order == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
            player.dscore1 = dscore1_result
            player.dscore2 = dscore2_result
        elif iat_round_order == [8, 9, 10, 11, 12, 13, 14, 1, 2, 3, 4, 5, 6, 7]:
            player.dscore1 = dscore2_result
            player.dscore2 = dscore1_result
        else:
            # En caso de otro orden, se asigna directamente
            player.dscore1 = dscore1_result
            player.dscore2 = dscore2_result

        # Función para clasificar la asociación según el dscore y la categoría
        def clasificar(dscore, category):
            if abs(dscore) < 0.15:
                return "Neutral"
            if dscore < 0:
                if -0.35 <= dscore <= -0.15:
                    if category == "Personas obesas/Personas delgadas":
                        return "Leve: Personas delgadas+bueno, Personas obesas+malo"
                    else:  # Personas homosexuales/Personas heterosexuales
                        return "Leve: Personas heterosexuales+bueno, Personas homosexuales+malo"
                elif -0.65 <= dscore < -0.35:
                    if category == "Personas obesas/Personas delgadas":
                        return "Moderada: Personas delgadas+bueno, Personas obesas+malo"
                    else:
                        return "Moderada: Personas heterosexuales+bueno, Personas homosexuales+malo"
                elif -2 <= dscore < -0.65:
                    if category == "Personas obesas/Personas delgadas":
                        return "Fuerte: Personas delgadas+bueno, Personas obesas+malo"
                    else:
                        return "Fuerte: Personas heterosexuales+bueno, Personas homosexuales+malo"
            else:  # dscore > 0
                if 0.15 <= dscore <= 0.35:
                    if category == "Personas obesas/Personas delgadas":
                        return "Leve: Personas obesas+bueno, Personas delgadas+malo"
                    else:
                        return "Leve: Personas homosexuales+bueno, Personas heterosexuales+malo"
                elif 0.35 < dscore <= 0.65:
                    if category == "Personas obesas/Personas delgadas":
                        return "Moderada: Personas obesas+bueno, Personas delgadas+malo"
                    else:
                        return "Moderada: Personas homosexuales+bueno, Personas heterosexuales+malo"
                elif 0.65 < dscore <= 2:
                    if category == "Personas obesas/Personas delgadas":
                        return "Fuerte: Personas obesas+bueno, Personas delgadas+malo"
                    else:
                        return "Fuerte: Personas homosexuales+bueno, Personas heterosexuales+malo"
            return "Sin clasificación"

        # Se asigna la asociación de forma fija:
        # - iat1 corresponde siempre a "Personas obesas/Personas delgadas"
        # - iat2 corresponde siempre a "Personas homosexuales/Personas heterosexuales"
        player.iat1_association = clasificar(player.dscore1, "Personas obesas/Personas delgadas")
        player.iat2_association = clasificar(player.dscore2, "Personas homosexuales/Personas heterosexuales")

        return dict(
            category=category,
            endowment=Constants.endowment,
            dscore1=player.dscore1,
            dscore2=player.dscore2,
            iat1_association=player.iat1_association,
            iat2_association=player.iat2_association,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        participant = player.participant

        # Si no se completó la autoevaluación se asigna un valor por defecto
        if not player.iat1_self_assessment:
            player.iat1_self_assessment = "No especificado"
        if not player.iat2_self_assessment:
            player.iat2_self_assessment = "No especificado"

        # Marcar que la evaluación del iat ya fue completada
        participant.vars['iat_assessment_completed'] = True

        # Se convierte la asociación calculada al formato de las opciones
        # Fijamos:
        # • iat1 (gato y perro) se compara con player.iat1_association
        # • iat2 (blanco y negro) se compara con player.iat2_association
        expected_iat1 = player.iat1_association
        expected_iat2 = player.iat2_association

        player.iat1_guess_correct = (player.iat1_self_assessment == expected_iat1)
        player.iat2_guess_correct = (player.iat2_self_assessment == expected_iat2)

        # Validación de los rangos morales para iat 1 y iat 2
        iat1_moral_range = (
                player.dscore1 >= player.iat1_lower_limit and
                player.dscore1 <= player.iat1_upper_limit
        )

        iat2_moral_range = (
                player.dscore2 >= player.iat2_lower_limit and
                player.dscore2 <= player.iat2_upper_limit
        )

        # Validación de los rangos para iat 1 y iat 2 en el rango izquierdo
        iat1_moral_range_left = (
                player.dscore1 < player.iat1_lower_limit
        )

        iat2_moral_range_left = (
                player.dscore2 < player.iat2_lower_limit
        )

        # Validación de los rangos para iat 1 y iat 2 en el rango derecho
        iat1_moral_range_right = (
                player.dscore1 > player.iat1_upper_limit
        )

        iat2_moral_range_right = (
                player.dscore2 > player.iat2_upper_limit
        )

        # Asignación de las variables al jugador
        player.iat1_moral_range = iat1_moral_range
        player.iat2_moral_range = iat2_moral_range
        player.iat1_moral_range_left = iat1_moral_range_left
        player.iat2_moral_range_left = iat2_moral_range_left
        player.iat1_moral_range_right = iat1_moral_range_right
        player.iat2_moral_range_right = iat2_moral_range_right

        # iatAssessmentPage.before_next_page
        participant.vars['iat1_moral_range'] = player.iat1_moral_range
        participant.vars['iat2_moral_range'] = player.iat2_moral_range
        participant.vars['iat1_moral_range_left'] = player.iat1_moral_range_left
        participant.vars['iat1_moral_range_right'] = player.iat1_moral_range_right
        participant.vars['iat2_moral_range_left'] = player.iat2_moral_range_left
        participant.vars['iat2_moral_range_right'] = player.iat2_moral_range_right

        # Configuración del logger
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Registrar las asociaciones correctas y las respuestas del usuario
        logging.info("Asociación iat1 (Personas obesas/Personas delgadas) esperada: %s", expected_iat1)
        logging.info("Asociación iat1 (Personas obesas/Personas delgadas) ingresada por el usuario: %s",
                     player.iat1_self_assessment)
        logging.info("Asociación iat2 (Personas homosexuales/Personas heterosexuales) esperada: %s", expected_iat2)
        logging.info("Asociación iat2 (Personas homosexuales/Personas heterosexuales) ingresada por el usuario: %s",
                     player.iat2_self_assessment)

        logging.info("Resultado de la adivinanza iat1 (Personas obesas/Personas delgadas): %s",
                     player.iat1_guess_correct)
        logging.info("Resultado de la adivinanza iat2 (Personas homosexuales/Personas heterosexuales): %s",
                     player.iat2_guess_correct)

        logging.info("¿El iat Personas obesas/Personas delgadas está dentro del rango moral del jugador? %s",
                     player.iat1_moral_range)
        logging.info(
            "¿El iat Personas homosexuales/Personas heterosexuales está dentro del rango moral del jugador? %s",
            player.iat2_moral_range)

        # Logs adicionales para especificar si el iat está a la izquierda, derecha o en el rango
        if iat1_moral_range:
            logging.info("El iat1 (Personas obesas/Personas delgadas) está dentro del rango moral.")
        elif iat1_moral_range_left:
            logging.info("El iat1 (Personas obesas/Personas delgadas) está a la izquierda del rango moral.")
        else:
            logging.info("El iat1 (Personas obesas/Personas delgadas) está a la derecha del rango moral.")

        if iat2_moral_range:
            logging.info("El iat2 (Personas homosexuales/Personas heterosexuales) está dentro del rango moral.")
        elif iat2_moral_range_left:
            logging.info("El iat2 (Personas homosexuales/Personas heterosexuales) está a la izquierda del rango moral.")
        else:
            logging.info("El iat2 (Personas homosexuales/Personas heterosexuales) está a la derecha del rango moral.")


    @staticmethod
    def error_message(player, values):
        if not values.get('iat1_self_assessment'):
            return "Por favor, selecciona una opción para el iat de Personas obesas y Personas delgadas."
        if not values.get('iat2_self_assessment'):
            return "Por favor, selecciona una opción para el iat de Personas homosexuales y Personas heterosexuales."
        if values.get('iat2_lower_limit') is None:
            return "Por favor, ingresa un límite inferior para el rango moralmente aceptable del iat de Personas homosexuales y Personas heterosexuales."
        if values.get('iat2_upper_limit') is None:
            return "Por favor, ingresa un límite superior para el rango moralmente aceptable del iat de Personas homosexuales y Personas heterosexuales."
        if values['iat2_lower_limit'] >= values['iat2_upper_limit']:
            return "El límite inferior para el iat de Personas homosexuales y Personas heterosexuales debe ser menor que el límite superior."
        if values.get('iat1_lower_limit') is None:
            return "Por favor, ingresa un límite inferior para el rango moralmente aceptable del iat de Personas obesas y Personas delgadas."
        if values.get('iat1_upper_limit') is None:
            return "Por favor, ingresa un límite superior para el rango moralmente aceptable del iat de Personas obesas y Personas delgadas."
        if values['iat1_lower_limit'] >= values['iat1_upper_limit']:
            return "El límite inferior para el iat de Personas obesas y Personas delgadas debe ser menor que el límite superior."


# si Mauricio dice que quiere que el recordatorio se haga entre cada pregunta, tengo que dejar de usar formfields y crer
# y editar la página MoralDecision de forma manual.
class MoralDecisionPageCerteza(Page):
    form_model = 'player'
    form_fields = [
        'iat1_probability',
        'iat2_probability',
    ]
    # aquí puedo considerar agregar validaciones al formulario para que el usuario no pueda agregar puntuaciones muy pequeñas al programa, con muchos números.

    @staticmethod
    def error_message(player, values):
        errors = {}
        for field in MoralDecisionPageCerteza.form_fields:
            # Checa None o cadena vacía
            if values.get(field) in (None, ''):
                errors[field] = 'Por favor completa este campo antes de continuar.'
        return errors or None

    @staticmethod
    def is_displayed(player: Player):
        # Only show to participants with iat order 1-14 and not shown yet
        return (
                player.round_number == 15 and
                player.participant.vars.get('iat_round_order') == list(range(1, 15))
                and not player.participant.vars.get('certeza_shown', False)
        )

    @staticmethod
    def vars_for_template(player):
        iat1_moral_range = player.dscore1 >= player.iat1_lower_limit and player.dscore1 <= player.iat1_upper_limit
        iat2_moral_range = player.dscore2 >= player.iat2_lower_limit and player.dscore2 <= player.iat2_upper_limit

        return {
            'iat1_moral_range': iat1_moral_range,
            'iat2_moral_range': iat2_moral_range,
            'iat1_lower_limit': player.iat1_lower_limit,
            'iat1_upper_limit': player.iat1_upper_limit,
            'iat2_lower_limit': player.iat2_lower_limit,
            'iat2_upper_limit': player.iat2_upper_limit,
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        part = player.participant
        part.vars['iat1_probability']        = player.iat1_probability
        part.vars['iat2_probability']        = player.iat2_probability

class MoralDecisionPageCerteza2(Page):
    form_model = 'player'
    form_fields = [
        'iat1_probability2',
        'iat2_probability2',
        'iat1_probability_left2',
        'iat2_probability_left2',
        'iat1_probability_right2',
        'iat2_probability_right2',
    ]
    # aquí puedo considerar agregar validaciones al formulario para que el usuario no pueda agregar puntuaciones muy pequeñas al programa, con muchos números.
    @staticmethod
    def error_message(player, values):
        errors = {}
        for field in MoralDecisionPageCerteza2.form_fields:
            # Checa None o cadena vacía
            if values.get(field) in (None, ''):
                errors[field] = 'Por favor completa este campo antes de continuar.'
        return errors or None

    @staticmethod
    def is_displayed(player: Player):
        # Show to participants with the alternate iat order and not shown yet
        alternate_order = list(range(8, 15)) + list(range(1, 8))
        return (
            player.round_number == 15 and
            player.participant.vars.get('iat_round_order') == alternate_order
            and not player.participant.vars.get('certeza2_shown', False)
        )

    @staticmethod
    def vars_for_template(player):
        iat1_moral_range = player.dscore1 >= player.iat1_lower_limit and player.dscore1 <= player.iat1_upper_limit
        iat2_moral_range = player.dscore2 >= player.iat2_lower_limit and player.dscore2 <= player.iat2_upper_limit

        return {
            'iat1_moral_range': iat1_moral_range,
            'iat2_moral_range': iat2_moral_range,
            'iat1_lower_limit': player.iat1_lower_limit,
            'iat1_upper_limit': player.iat1_upper_limit,
            'iat2_lower_limit': player.iat2_lower_limit,
            'iat2_upper_limit': player.iat2_upper_limit,
        }

    @staticmethod
    def before_next_page(player, timeout_happened):
        part = player.participant
        part.vars['iat1_probability2']        = player.iat1_probability2
        part.vars['iat2_probability2']        = player.iat2_probability2
        part.vars['iat1_probability_left2']   = player.iat1_probability_left2
        part.vars['iat2_probability_left2']   = player.iat2_probability_left2
        part.vars['iat1_probability_right2']  = player.iat1_probability_right2
        part.vars['iat2_probability_right2']  = player.iat2_probability_right2

# queda por introducir la función que propuse para esta clase, está en esta página: https://chatgpt.com/g/g-p-6770700264fc81918f62555c338c6f02-literature-review-iat/c/67a0f18e-087c-800c-966d-f4186e249d2e?model=o3-mini-high
class DictatorIntroduction(Page):
    """
    Página de introducción al Juego del Dictador para la categoría asignada.
    """
    template_name = 'iat/DictatorIntroduction.html'

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in [15]

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            endowment=Constants.endowment,
        )

def _active_flags(moral_left, moral_right,
                  p_in, p_left, p_right):
    """
    Devuelve los flags (p_in, p_left, p_right) que
    corresponden al lado correcto.
    """
    if moral_left or moral_right:
        # está fuera del rango: solo vale uno de los dos lados
        p_left  = p_left  if moral_left  else False
        p_right = p_right if moral_right else False
    # dentro del rango (moral_range=True) dejamos p_in tal cual
    return p_in, p_left, p_right



from typing import Optional

def _calc_threshold(
    moral_range: Optional[bool],
    p_in:         Optional[bool],
    p_left:       Optional[bool],
    p_right:      Optional[bool],
) -> float:
    """
    Devuelve la probabilidad (0–1) de revelar la etiqueta explícita
    según la preferencia declarada por el/la participante.

    • moral_range  == None  → 0.80  (no contestó su rango ⇒ asumimos “Sí”)
    • moral_range  == True  → 0.80 si p_in   ∈ {None, True}; 0.20 si p_in is False
    • moral_range  == False
        – si existe p_right (caso “a la derecha”):
              0.80 si p_right ∈ {None, True}; 0.20 si p_right is False
        – si existe p_left  (caso “a la izquierda”):
              0.80 si p_left  ∈ {None, True}; 0.20 si p_left  is False
        – si ambos están None (no respondió ninguno) → 0.80
    """
    # Caso 1 : no respondió sus límites
    if moral_range is None:
        return 0.80

    # Caso 2 : su d-score cayó *dentro* del rango aceptable
    if moral_range:
        return 0.80 if (p_in is None or p_in) else 0.20

    # Caso 3 : su d-score cayó *fuera* del rango
    # ——— a la derecha del rango
    if p_right is not None:
        return 0.80 if p_right else 0.20
    # ——— a la izquierda del rango
    if p_left is not None:
        return 0.80 if p_left else 0.20
    # Si no contestó ningún flag específico, asumimos “Sí”
    return 0.80

def split_groups(cat_string: str):
    """
    Devuelve los nombres de los grupos A y B a partir del string completo
    de categoría (por ejemplo 'personas delgadas y personas obesas').

    Si la categoría no coincide con los dos pares que manejamos,
    regresa los nombres genéricos 'Grupo A' y 'Grupo B'.
    """
    cat_lower = (cat_string or "").lower()

    if "personas delgadas" in cat_lower and "personas obesas" in cat_lower:
        return Constants.PersonasDelgadas, Constants.PersonasObesas

    if "personas heterosexuales" in cat_lower and "personas homosexuales" in cat_lower:
        return Constants.PersonasHeterosexuales, Constants.PersonasHomosexuales

    # Fallback genérico
    return "Grupo A", "Grupo B"


class DictatorOffer(Page):
    form_model = 'player'
    form_fields = ['dictator_offer']


    @staticmethod
    def is_displayed(player: Player):
        rotated = list(range(1, 8)) + list(range(8, 15))
        return (
            player.round_number in (15, 16)
            and player.participant.vars.get("iat_round_order") == rotated
        )

    @staticmethod
    def vars_for_template(player: Player):
        import random

        # Datos de la categoría y etiqueta explícita
        original_category = player.group.dictator_category or ""
        explicit_label = original_category.capitalize() if original_category else "Sin categoría asignada"

        part_vars = player.participant.vars

        # Selección del usuario
        user_pref = part_vars.get('iat1_probability') if "delgadas" in original_category.lower() else part_vars.get('iat2_probability')

        # Umbral según preferencia
        threshold = 0.8 if user_pref else 0.2

        # Generación de la probabilidad
        rand_val = random.random()

        # Decisión final
        display_label = explicit_label if rand_val < threshold else "Miembro del grupo"

        # DEBUG reducido
        print(f"[DEBUG] user_pref={user_pref}, threshold={threshold}, rand_val={rand_val}, label={display_label}")

        # Guardar para resultados
        player.participant.vars[f"visible_category_round_{player.round_number}"] = display_label

        # Nombres de grupos
        group_a, group_b = split_groups(original_category)

        return dict(
            category=display_label,
            endowment=Constants.endowment,
            group_a=group_a,
            group_b=group_b,
        )

    @staticmethod
    def error_message(player: Player, values):
        offer = values.get('dictator_offer')
        if offer is None:
            return "Por favor indica cuánto deseas ofrecer."
        if offer < 0 or offer > Constants.endowment:
            return f"Por favor, ofrece una cantidad entre 0 y {Constants.endowment}."

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # 1) Asignar al grupo y calcular payoff
        player.group.kept = player.dictator_offer
        set_payoffs(player.group)

        # 2) Volcar TODO a participant.vars
        rnd = player.round_number
        pv = player.participant.vars
        pv[f'dictator_offer_r{rnd}'] = player.dictator_offer
        pv[f'kept_r{rnd}'] = player.group.kept
        pv[f'assigned_r{rnd}'] = player.group.assigned
        pv[f'payoff_r{rnd}'] = player.payoff
        pv[f'cat_r{rnd}'] = player.group.dictator_category



class DictatorOffer2(Page):
    """
    Página donde el jugador decide cuánto mantener y cuánto asignar a la categoría,
    para quienes tienen el ordering invertido.
    """
    form_model = 'player'
    form_fields = ['dictator_offer']

    @staticmethod
    def is_displayed(player: Player):
        alternate = list(range(8, 15)) + list(range(1, 8))
        return (
            player.round_number in (15, 16)
            and player.participant.vars.get('iat_round_order') == alternate
        )

    @staticmethod
    def vars_for_template(player: Player):
        import random

        original = player.group.dictator_category or ""
        explicit = original.capitalize() if original else "Sin categoría asignada"
        pv = player.participant.vars
        cat = original.lower()

        # flags y rango según categoría
        if "delgadas" in cat:
            raw_in = pv.get("iat1_probability2")
            raw_left = pv.get("iat1_probability_left2")
            raw_right = pv.get("iat1_probability_right2")
            mor_l = pv.get("iat1_moral_range_left")
            mor_r = pv.get("iat1_moral_range_right")
            mor = pv.get("iat1_moral_range")
        else:
            raw_in = pv.get("iat2_probability2")
            raw_left = pv.get("iat2_probability_left2")
            raw_right = pv.get("iat2_probability_right2")
            mor_l = pv.get("iat2_moral_range_left")
            mor_r = pv.get("iat2_moral_range_right")
            mor = pv.get("iat2_moral_range")

        # 1) posición del d-score
        if mor is True:
            position = "dentro del rango"
        elif mor_l:
            position = "a la izquierda del rango"
        elif mor_r:
            position = "a la derecha del rango"
        else:
            position = "sin rango definido"

        # 2) aplicamos active_flags y 3) calculamos umbral
        p_in, p_left, p_right = _active_flags(mor_l, mor_r, raw_in, raw_left, raw_right)
        threshold = _calc_threshold(mor, p_in, p_left, p_right)

        # 4) aleatorio y decisión
        rv = random.random()
        label = explicit if rv < threshold else "Miembro del grupo"

        # DEBUG ampliado
        print(
            f"[DEBUG Offer2 ▶ rnd={player.round_number}] "
            f"dscore {position}; "
            f"raw_flags(in/left/right)={raw_in}/{raw_left}/{raw_right}; "
            f"active_flags(in/left/right)={p_in}/{p_left}/{p_right}; "
            f"threshold={threshold:.2f}; rand={rv:.2f} → '{label}'"
        )

        # guardamos y retornamos
        pv[f"visible_category_round_{player.round_number}"] = {
            "label": label,
            "full_category": original
        }
        group_a, group_b = split_groups(original)
        return dict(
            category=label,
            endowment=Constants.endowment,
            group_a=group_a,
            group_b=group_b,
        )

    @staticmethod
    def error_message(player: Player, values):
        offer = values.get('dictator_offer')
        if offer is None:
            return "Por favor indica cuánto deseas ofrecer."
        if offer < 0 or offer > Constants.endowment:
            return f"Por favor, ofrece una cantidad entre 0 y {Constants.endowment}."

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.group.kept = player.dictator_offer
        set_payoffs(player.group)

        rnd = player.round_number
        pv = player.participant.vars
        pv[f'dictator_offer_r{rnd}'] = player.dictator_offer
        pv[f'kept_r{rnd}'] = player.group.kept
        pv[f'assigned_r{rnd}'] = player.group.assigned
        pv[f'payoff_r{rnd}'] = player.payoff
        pv[f'cat_r{rnd}'] = player.group.dictator_category


class ResultsDictador(Page):
    @staticmethod
    def is_displayed(player: Player):
        rotated = list(range(1, 8)) + list(range(8, 15))
        return (
            player.round_number == 16
            and player.participant.vars.get("iat_round_order") == rotated
        )

    @staticmethod
    def vars_for_template(player: Player):
        dictator_offers = []
        pv = player.participant.vars
        for rnd in [15, 16]:
            # Recuperamos de participant.vars en lugar de group
            visible_cat = pv.get(f'visible_category_round_{rnd}')
            kept       = pv.get(f'kept_r{rnd}')
            assigned   = pv.get(f'assigned_r{rnd}', 0)
            full_cat   = pv.get(f'cat_r{rnd}')
            dictator_offers.append({
                'round':         rnd,
                'category':      visible_cat,
                'full_category': full_cat,
                'kept':          kept,
                'assigned':      assigned,
            })
        return dict(dictator_offers=dictator_offers)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Sobrescribimos el payoff con el valor guardado por participante
        payoff16 = player.participant.vars.get('payoff_r16')
        if payoff16 is not None:
            player.payoff = payoff16


class ResultsDictator2(Page):
    """Resultados para participantes con ordering invertido (DictatorOffer2)."""
    @staticmethod
    def is_displayed(player: Player):
        alternate = list(range(8, 15)) + list(range(1, 8))
        return (
            player.round_number == 16
            and player.participant.vars.get("iat_round_order") == alternate
        )

    @staticmethod
    def vars_for_template(player: Player):
        dictator_offers = []
        pv = player.participant.vars
        for rnd in [15, 16]:
            # Para el caso invertido, label y full_category pueden venir empaquetados
            vis       = pv.get(f'visible_category_round_{rnd}', {})
            label     = vis.get("label", pv.get(f'cat_r{rnd}'))
            full_cat  = vis.get("full_category", pv.get(f'cat_r{rnd}'))
            kept      = pv.get(f'kept_r{rnd}')
            assigned  = pv.get(f'assigned_r{rnd}', 0)
            dictator_offers.append({
                'round':         rnd,
                'category':      label,
                'full_category': full_cat,
                'kept':          kept,
                'assigned':      assigned,
            })
        return dict(dictator_offers=dictator_offers)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Sobrescribimos el payoff con el valor guardado por participante
        payoff16 = player.participant.vars.get('payoff_r16')
        if payoff16 is not None:
            player.payoff = payoff16


page_sequence = [
    #InstruccionesGenerales1,
    #InstruccionesGenerales2,
    #Comprension1,
    #Comprension2,
    #Feedback1,
    #Feedback2,
    UserInfo,
    #PreguntaM,
    Intro,
    RoundN,  # Rondas 1-14: iat.
    IATAssessmentPage,  # Ronda 15: Evaluación del iat
    MoralDecisionPageCerteza,
    MoralDecisionPageCerteza2,
    # Ronda 15: Decisión
    # Results,                   # Por ahora, no queremos mostrar los resultados del iat. En caso de querer hacer esto e
    # en caso de querer hacerlo, falta manejar los assement de acuerdo con la aleatorización del iat.
    DictatorIntroduction,  # Rondas 16-18: Introducción al Dictador
    DictatorOffer,
    DictatorOffer2, # Rondas 16-18: Oferta del Dictador,    # Rondas 16-18: Espera de Resultados del Dictador
    ResultsDictador,  # Rondas 16-18: Resultados del Dictador,            # Ronda 18: Resultados Finales del Dictador
    ResultsDictator2,
]




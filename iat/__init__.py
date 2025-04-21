import time
import random
# from .admin_report_functions import *
from otree.api import *
from otree import settings
from . import stimuli
from . import stats
from . import blocks
import math
from statistics import mean, stdev
from decimal import Decimal

# comentarios


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
    num_rounds = 18  # 14 para IAT + 4 para dictador

    keys = {"f": 'left', "j": 'right'}
    trial_delay = 0.250
    endowment = Decimal('100')  # Añadido para dictador
    categories = ['perro', 'gato', 'blanco', 'negro']  # Categorías para el Dictador


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
            # Rondas existentes para IAT.
            1: 5, 2: 5, 3: 10, 4: 20, 5: 5, 6: 10, 7: 20,
            8: 5, 9: 5, 10: 10, 11: 20, 12: 5, 13: 10, 14: 20,
            # Rondas adicionales para Dictador.
            15: 1, 16: 1, 17: 1, 18: 1
        },
    )
    session.params = {}
    for param in defaults:
        session.params[param] = session.config.get(param, defaults[param])


    # Asignar orden de rondas del IAT solo en la primera ronda
    if self.round_number == 1:
        for player in self.get_players():
            blocks.iat_ordering = random.choice([
                list(range(1, 15)),  # Orden directo: 1-14
                list(range(8, 15)) + list(range(1, 8))  # Orden invertido: 8-14,1-7
            ])
            player.participant.vars['iat_round_order'] = blocks.iat_ordering
            print(blocks.iat_ordering)

        # Aleatorizar las categorías del Dictador para las rondas 15-18
        shuffled_categories = Constants.categories.copy()
        random.shuffle(shuffled_categories)
        session.vars['shuffled_dictator_categories'] = shuffled_categories

    block = get_block_for_round(self.round_number, session.params)

    self.practice = block.get('practice', False)
    self.primary_left = block.get('left', {}).get('primary', "")
    self.primary_right = block.get('right', {}).get('primary', "")
    self.secondary_left = block.get('left', {}).get('secondary', "")
    self.secondary_right = block.get('right', {}).get('secondary', "")

        #print("shuffled categories:", shuffled_categories)

    # Asignar categorías al Dictador basadas en la lista aleatoria para las rondas 15-18
    if self.round_number in [15, 16, 17, 18]:
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
    num_failed = models.IntegerField(initial=0)  # Número de respuestas incorrectas
    name = models.StringField(label="Nombre")
    age = models.IntegerField(label="Edad", min=0, max=99)
    sports = models.StringField(
        widget=widgets.RadioSelect,
        choices=[
            ('Futból', 'Futból'),
            ('Basketball', 'Basketball'),
            ('Tenis', 'Tenis'),
            ('Natación', 'Natación'),
            ('Otro', 'Otro'),
        ],
        label="¿Qué deporte prefieres?"
    )
    random_number = models.IntegerField(label="Número aleatorio entre 1 y 20", min=1, max=20)
    dscore1 = models.FloatField()  # D-score del primer IAT
    dscore2 = models.FloatField()  # D-score del segundo IAT

    # Nuevo campo para la pregunta moral
    moral_question = models.StringField(label="Aquí va una pregunta moral", blank=True)

    iat2_self_assessment = models.StringField(
        label="¿Cómo crees que te fue en el IAT de blanco y negro?",
        choices=[
            "Neutral",
            "Asociación leve a blanco+feliz, negro+triste",
            "Asociación leve a blanco+triste, negro+feliz",
            "Asociación moderada a blanco+feliz, negro+triste",
            "Asociación moderada a blanco+triste, negro+feliz",
            "Asociación fuerte a blanco+feliz, negro+triste",
            "Asociación fuerte a blanco+triste, negro+feliz",
        ],
        widget=widgets.RadioSelect
    )

    iat1_self_assessment = models.StringField(
        label="¿Cómo crees que te fue en el IAT de gato y perro?",
        choices=[
            "Neutral",
            "Asociación leve a gato+feliz, perro+triste",
            "Asociación leve a gato+triste, perro+feliz",
            "Asociación moderada a gato+feliz, perro+triste",
            "Asociación moderada a gato+triste, perro+feliz",
            "Asociación fuerte a gato+feliz, perro+triste",
            "Asociación fuerte a gato+triste, perro+feliz",
        ],
        widget=widgets.RadioSelect
    )

    # Variables para el rango moralmente aceptable del IAT 1. nota: hay que cambiar esto para que vayan de -2 a 2.
    iat2_lower_limit = models.FloatField(
        label="¿Cuál es el límite inferior del rango moralmente aceptable para el IAT negro blanco?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat2_upper_limit = models.FloatField(
        label="¿Cuál es el límite superior del rango moralmente aceptable para el IAT negro blanco?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    # Variables para el rango moralmente aceptable del IAT 2
    iat1_lower_limit = models.FloatField(
        label="¿Cuál es el límite inferior del rango moralmente aceptable para el IAT gato perro?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat1_upper_limit = models.FloatField(
        label="¿Cuál es el límite superior del rango moralmente aceptable para el IAT gato perro?",
        help_text="Debe estar entre -2 y 2.",
        min=-2,
        max=2
    )

    iat1_probability = models.IntegerField(
        label="Indica la probabilidad con la que se te revelará información de tu IAT gato perro si tu puntuación está dentro del rango moralmente aceptable:",
        choices=[[80, "80"], [20, "20"]],
        widget=widgets.RadioSelect,
        blank=True
    )

    iat1_probability_out_of_range = models.IntegerField(
        label="Indica la probabilidad con la que se te revelará información de tu IAT gato perro si tu puntuación está fuera del rango moralmente aceptable:",
        choices=[[80, "80"], [20, "20"]],
        widget=widgets.RadioSelect,
        blank=True
    )

    iat2_probability = models.IntegerField(
        label="Indica la probabilidad con la que se te revelará información de tu IAT negro blanco si tu puntuación está dentro del rango moralmente aceptable:",
        choices=[[80, "80"], [20, "20"]],
        widget=widgets.RadioSelect,
        blank=True
    )

    iat2_probability_out_of_range = models.IntegerField(
        label="Indica la probabilidad con la que se te revelará información de tu IAT negro blanco si tu puntuación está fuera del rango moralmente aceptable:",
        choices=[[80, "80"], [20, "20"]],
        widget=widgets.RadioSelect,
        blank=True
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

    # campos para el juego del dictador.
    dictator_offer = models.CurrencyField(
        min=0,
        max=Constants.endowment,
        label="¿Cuánto te gustaría ofrecer?"
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
        if p.round_number not in (3, 4, 6, 7, 10, 11, 13, 14, 15, 16, 17, 18):
            continue
        participant = p.participant
        session = p.session
        subsession = p.subsession
        group = p.group
        for z in Trial.filter(player=p):
            yield [
                session.code,
                participant.code,
                subsession.round_number,
                subsession.primary_left,
                subsession.primary_right,
                subsession.secondary_left,
                subsession.secondary_right,
                z.iteration,
                z.timestamp,
                z.stimulus_cls,
                z.stimulus_cat,
                z.stimulus,
                z.correct,
                z.response,
                z.is_correct,
                z.reaction_time,
                p.dictator_category,
                p.dictator_offer,
                group.kept,
                group.dictator_category,
                group.assigned,
                p.payoff,
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
class Intro(Page):
    # comentario en caso de ser necesario: cambié está página para que se
    # pudiera mostrar los labels correctos de inicios del IAT, pero causó un
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
        # Mostrar solo en rondas de IAT
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
    form_fields = ['name', 'age', 'sports', 'random_number']

    @staticmethod
    def is_displayed(player):
        # Mostrar esta página solo una vez por participante
        return player.participant.vars.get('user_info_completed', False) == False

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Guardar valores en participant.vars si deseas usarlos globalmente
        participant = player.participant
        if not player.name:
            player.name = "Anónimo"
        if not player.age:
            player.age = 18
        if not player.sports:
            player.sports = "Sin especificar"
        if not player.random_number:
            player.random_number = 0

        # Marcar que la información ya fue recopilada
        participant.vars['user_info_completed'] = True


class PreguntaM(Page):
    form_model = 'player'
    form_fields = ['moral_question']

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
        # Validar que el campo moral_question no esté vacío
        if not values.get('moral_question'):
            return "Por favor, responde la pregunta antes de continuar."
#pie
# acá el detalle es que las validaciones de los campos están mal, aunque fáciles de cambiar, no lo haré ahora. 4 de febrero del 2025.
class IATAssessmentPage(Page):
    form_model = 'player'
    form_fields = [
        'iat1_self_assessment',
        'iat2_self_assessment',
        'iat2_lower_limit',  # Límite inferior para el IAT negro blanco
        'iat2_upper_limit',  # Límite superior para el IAT negro blanco
        'iat1_lower_limit',  # Límite inferior para el IAT blanco negro
        'iat1_upper_limit'  # Límite superior para el IAT blanco negro
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

        # Extraer datos para el primer IAT (rondas 3, 4, 6, 7)
        data3 = extract(3)
        data4 = extract(4)
        data6 = extract(6)
        data7 = extract(7)
        dscore1_result = dscore1(data3, data4, data6, data7)

        # Extraer datos para el segundo IAT (rondas 10, 13, 11, 14)
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
                    if category == "gato/perro":
                        return "Leve: perro positivo, gato negativo"
                    else:  # white/black
                        return "Leve: black positivo, white negativo"
                elif -0.65 <= dscore < -0.35:
                    if category == "gato/perro":
                        return "Moderada: perro positivo, gato negativo"
                    else:
                        return "Moderada: black positivo, white negativo"
                elif -2 <= dscore < -0.65:
                    if category == "gato/perro":
                        return "Fuerte: perro positivo, gato negativo"
                    else:
                        return "Fuerte: black positivo, white negativo"
            else:  # dscore > 0
                if 0.15 <= dscore <= 0.35:
                    if category == "gato/perro":
                        return "Leve: gato positivo, perro negativo"
                    else:
                        return "Leve: white positivo, black negativo"
                elif 0.35 < dscore <= 0.65:
                    if category == "gato/perro":
                        return "Moderada: gato positivo, perro negativo"
                    else:
                        return "Moderada: white positivo, black negativo"
                elif 0.65 < dscore <= 2:
                    if category == "gato/perro":
                        return "Fuerte: gato positivo, perro negativo"
                    else:
                        return "Fuerte: white positivo, black negativo"
            return "Sin clasificación"

        # Se asigna la asociación de forma fija:
        # - IAT1 corresponde siempre a "gato/perro"
        # - IAT2 corresponde siempre a "white/black"
        player.iat1_association = clasificar(player.dscore1, "gato/perro")
        player.iat2_association = clasificar(player.dscore2, "white/black")

        return dict(
            category=category,
            endowment=Constants.endowment,
            dscore1=player.dscore1,
            dscore2=player.dscore2,
            iat1_association=player.iat1_association,
            iat2_association=player.iat2_association,
        )

    @staticmethod
    def convert_computed(association: str, category: str) -> str:
        """
        Convierte el string de asociación calculado al formato de las opciones de la autoevaluación.

        Para "white/black":
            - "white positivo" se convierte en "blanco+feliz"
            - "black negativo" se convierte en "negro+triste"
            - "black positivo" se convierte en "negro+feliz"
            - "white negativo" se convierte en "blanco+triste"

        Para "gato/perro":
            - "gato positivo" se convierte en "gato+feliz"
            - "perro negativo" se convierte en "perro+triste"
            - "perro positivo" se convierte en "perro+feliz"
            - "gato negativo" se convierte en "gato+triste"

        Además, transforma el prefijo:
            - "Leve: "    → "Asociación leve a "
            - "Moderada: " → "Asociación moderada a "
            - "Fuerte: "   → "Asociación fuerte a "
        """
        if association == "Neutral":
            return "Neutral"
        if association.startswith("Leve: "):
            prefix, rest = "Asociación leve a ", association[len("Leve: "):]
        elif association.startswith("Moderada: "):
            prefix, rest = "Asociación moderada a ", association[len("Moderada: "):]
        elif association.startswith("Fuerte: "):
            prefix, rest = "Asociación fuerte a ", association[len("Fuerte: "):]
        else:
            prefix, rest = "", association

        if category == "white/black":
            rest = rest.replace("white positivo", "blanco+feliz") \
                .replace("black negativo", "negro+triste") \
                .replace("black positivo", "negro+feliz") \
                .replace("white negativo", "blanco+triste")
        elif category == "gato/perro":
            rest = rest.replace("gato positivo", "gato+feliz") \
                .replace("perro negativo", "perro+triste") \
                .replace("perro positivo", "perro+feliz") \
                .replace("gato negativo", "gato+triste")
        return prefix + rest

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        participant = player.participant

        # Si no se completó la autoevaluación se asigna un valor por defecto
        if not player.iat1_self_assessment:
            player.iat1_self_assessment = "No especificado"
        if not player.iat2_self_assessment:
            player.iat2_self_assessment = "No especificado"

        # Marcar que la evaluación del IAT ya fue completada
        participant.vars['iat_assessment_completed'] = True

        # Se convierte la asociación calculada al formato de las opciones
        # Fijamos:
        # • IAT1 (gato y perro) se compara con player.iat1_association
        # • IAT2 (blanco y negro) se compara con player.iat2_association
        expected_iat1 = IATAssessmentPage.convert_computed(player.iat1_association, "gato/perro")
        expected_iat2 = IATAssessmentPage.convert_computed(player.iat2_association, "white/black")

        player.iat1_guess_correct = (player.iat1_self_assessment == expected_iat1)
        player.iat2_guess_correct = (player.iat2_self_assessment == expected_iat2)

        iat1_moral_range = (
                player.dscore1 >= player.iat1_lower_limit and
                player.dscore1 <= player.iat1_upper_limit
        )
        iat2_moral_range = (
                player.dscore2 >= player.iat2_lower_limit and
                player.dscore2 <= player.iat2_upper_limit
        )

        # asignaciones de las variables.
        player.iat1_moral_range = iat1_moral_range
        player.iat2_moral_range = iat2_moral_range

        # Imprimir en consola las asociaciones correctas y las respuestas del usuario
        # print("ahora, test del programa:")
        # print("Asociación IAT1 (gato/perro) esperada:", expected_iat1)
        # print("Asociación IAT1 (gato/perro) ingresada por el usuario:", player.iat1_self_assessment)
        # print("Asociación IAT2 (blanco/negro) esperada:", expected_iat2)
        # print("Asociación IAT2 (blanco/negro) ingresada por el usuario:", player.iat2_self_assessment)
        #
        # print("Resultado de la adivinanza IAT1 (gato/perro):", player.iat1_guess_correct)
        # print("Resultado de la adivinanza IAT2 (blanco/negro):", player.iat2_guess_correct)
        #
        # print("¿el IAT negro blanco está dentro del rango moral del jugador?", player.iat2_moral_range)
        # print("¿el IAT gato perro está dentro del rango moral del jugador?", player.iat1_moral_range)

    @staticmethod
    def error_message(player, values):
        if not values.get('iat1_self_assessment'):
            return "Por favor, selecciona una opción para el IAT de gato y perro."
        if not values.get('iat2_self_assessment'):
            return "Por favor, selecciona una opción para el IAT de blanco y negro."
        if values.get('iat2_lower_limit') is None:
            return "Por favor, ingresa un límite inferior para el rango moralmente aceptable del IAT negro blanco."
        if values.get('iat2_upper_limit') is None:
            return "Por favor, ingresa un límite superior para el rango moralmente aceptable del IAT negro blanco."
        if values['iat2_lower_limit'] >= values['iat2_upper_limit']:
            return "El límite inferior para el IAT negro blanco debe ser menor que el límite superior."
        if values.get('iat1_lower_limit') is None:
            return "Por favor, ingresa un límite inferior para el rango moralmente aceptable del IAT blanco negro."
        if values.get('iat1_upper_limit') is None:
            return "Por favor, ingresa un límite superior para el rango moralmente aceptable del IAT blanco negro."
        if values['iat1_lower_limit'] >= values['iat1_upper_limit']:
            return "El límite inferior para el IAT blanco negro debe ser menor que el límite superior."


# si Mauricio dice que quiere que el recordatorio se haga entre cada pregunta, tengo que dejar de usar formfields y crer
# y editar la página MoralDecision de forma manual.
class MoralDecisionPageCerteza(Page):
    form_model = 'player'
    form_fields = [
        'iat1_probability',
        'iat1_probability_out_of_range',
        'iat2_probability',
        'iat2_probability_out_of_range'
    ]

    # aquí puedo considerar agregar validaciones al formulario para que el usuario no pueda agregar puntuaciones muy pequeñas al programa, con muchos números.

    @staticmethod
    def is_displayed(player):
        return player.round_number == 15

    @staticmethod
    def vars_for_template(player):
        return {
            'iat1_lower_limit': player.iat1_lower_limit,
            'iat1_upper_limit': player.iat1_upper_limit,
            'iat2_lower_limit': player.iat2_lower_limit,
            'iat2_upper_limit': player.iat2_upper_limit,
        }


# queda por introducir la función que propuse para esta clase, está en esta página: https://chatgpt.com/g/g-p-6770700264fc81918f62555c338c6f02-literature-review-iat/c/67a0f18e-087c-800c-966d-f4186e249d2e?model=o3-mini-high
class DictatorIntroduction(Page):
    """
    Página de introducción al Juego del Dictador para la categoría asignada.
    """

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in [15]

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            endowment=Constants.endowment,
        )


# entonces, en la pagina anterior estoy calculando los dscores de los jugadores, hacerlos
# en esta sección me permite que pueda acceder a estos valores dentro de las rondas.

# una propuesta para que aparezca con 80% de probabilidad está en el siguiente chat: https://chatgpt.com/g/g-p-6770700264fc81918f62555c338c6f02-literature-review-iat/c/67a3c2bd-eff0-800c-a2c7-2c3614ae93a7

# hace falta probar este caso, donde hago pruebas con la página que propuse para esta clase, el link es: https://chatgpt.com/g/g-p-6770700264fc81918f62555c338c6f02-literature-review-iat/c/67a64686-ecc0-800c-ac14-13e5f56b038e?model=o3-mini
class DictatorOffer(Page):
    """
    Página donde el jugador decide cuánto mantener y cuánto asignar a la categoría.
    """
    form_model = 'group'
    form_fields = ['kept']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number in [15, 16, 17, 18]

    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        if group.dictator_category:
            original_category = group.dictator_category.lower()
            explicit_label = group.dictator_category.capitalize()
        else:
            original_category = ""
            explicit_label = "Sin categoría asignada"

        import random
        display_label = explicit_label

        # Usar participant.vars para almacenar los valores de forma persistente entre rondas.
        part_vars = player.participant.vars

        # Para IAT1: moral_range y probabilidades
        if 'iat1_moral_range' not in part_vars:
            part_vars['iat1_moral_range'] = player.field_maybe_none("iat1_moral_range")
        iat1_moral_range = part_vars['iat1_moral_range']

        if 'iat1_probability' not in part_vars:
            part_vars['iat1_probability'] = player.field_maybe_none("iat1_probability")
        iat1_probability = part_vars['iat1_probability']

        if 'iat1_probability_out_of_range' not in part_vars:
            part_vars['iat1_probability_out_of_range'] = player.field_maybe_none("iat1_probability_out_of_range")
        iat1_probability_out_of_range = part_vars['iat1_probability_out_of_range']

        # Para IAT2: moral_range y probabilidades
        if 'iat2_moral_range' not in part_vars:
            part_vars['iat2_moral_range'] = player.field_maybe_none("iat2_moral_range")
        iat2_moral_range = part_vars['iat2_moral_range']

        if 'iat2_probability' not in part_vars:
            part_vars['iat2_probability'] = player.field_maybe_none("iat2_probability")
        iat2_probability = part_vars['iat2_probability']

        if 'iat2_probability_out_of_range' not in part_vars:
            part_vars['iat2_probability_out_of_range'] = player.field_maybe_none("iat2_probability_out_of_range")
        iat2_probability_out_of_range = part_vars['iat2_probability_out_of_range']

        # Lógica para categorías 'perro' o 'gato'
        if original_category in ['perro', 'gato']:
            substitute_label = "animal"
            if iat1_moral_range is None:
                threshold = 0.8
                debug_msg = ("DEBUG: iat1_moral_range es None. Probabilidad ingresada: None. "
                             "Usando probabilidad por defecto del 80%.")
            elif iat1_moral_range is True:
                if iat1_probability is None:
                    threshold = 0.8
                    debug_msg = (
                        "DEBUG: iat1_moral_range True, pero iat1_probability en blanco. Probabilidad ingresada: None. "
                        "Usando probabilidad por defecto del 80%.")
                else:
                    threshold = iat1_probability / 100.0
                    debug_msg = f"DEBUG: iat1_moral_range True. Probabilidad ingresada: {iat1_probability}%. Usando iat1_probability."
            else:  # iat1_moral_range es False
                if iat1_probability_out_of_range is None:
                    threshold = 0.2
                    debug_msg = (
                        "DEBUG: iat1_moral_range False, pero iat1_probability_out_of_range en blanco. Probabilidad ingresada: None. "
                        "Usando probabilidad por defecto del 20%.")
                else:
                    threshold = iat1_probability_out_of_range / 100.0
                    debug_msg = f"DEBUG: iat1_moral_range False. Probabilidad ingresada: {iat1_probability_out_of_range}%. Usando iat1_probability_out_of_range."
            rand_val = random.random()
            if rand_val < threshold:
                display_label = explicit_label
            else:
                display_label = substitute_label
            # print(f"{debug_msg} Recordatorio: Se define el threshold como {threshold:.2f} "
            #       f"(valor mínimo para elegir la etiqueta explícita). Valor aleatorio generado: {rand_val:.2f}. "
            #       f"Resultado: {display_label}")

        # Lógica para categorías 'blanco' o 'negro'
        elif original_category in ['blanco', 'negro']:
            substitute_label = "persona"
            if iat2_moral_range is None:
                threshold = 0.8
                debug_msg = ("DEBUG: iat2_moral_range es None. Probabilidad ingresada: None. "
                             "Usando probabilidad por defecto del 80%.")
            elif iat2_moral_range is True:
                if iat2_probability is None:
                    threshold = 0.8
                    debug_msg = (
                        "DEBUG: iat2_moral_range True, pero iat2_probability en blanco. Probabilidad ingresada: None. "
                        "Usando probabilidad por defecto del 80%.")
                else:
                    threshold = iat2_probability / 100.0
                    debug_msg = f"DEBUG: iat2_moral_range True. Probabilidad ingresada: {iat2_probability}%. Usando iat2_probability."
            else:  # iat2_moral_range es False
                if iat2_probability_out_of_range is None:
                    threshold = 0.2
                    debug_msg = (
                        "DEBUG: iat2_moral_range False, pero iat2_probability_out_of_range en blanco. Probabilidad ingresada: None. "
                        "Usando probabilidad por defecto del 20%.")
                else:
                    threshold = iat2_probability_out_of_range / 100.0
                    debug_msg = f"DEBUG: iat2_moral_range False. Probabilidad ingresada: {iat2_probability_out_of_range}%. Usando iat2_probability_out_of_range."
            rand_val = random.random()
            if rand_val < threshold:
                display_label = explicit_label
            else:
                display_label = substitute_label
            # print(f"{debug_msg} Recordatorio: Se define el threshold como {threshold:.2f} "
            #       f"(valor mínimo para elegir la etiqueta explícita). Valor aleatorio generado: {rand_val:.2f}. "
            #       f"Resultado: {display_label}")

        player.participant.vars[f'visible_category_round_{player.round_number}'] = display_label
        return dict(
            category=display_label,
            endowment=Constants.endowment,
        )

    @staticmethod
    def error_message(player, values):
        kept = values['kept']
        if kept < 0 or kept > Constants.endowment:
            return f"Por favor, ofrece una cantidad entre 0 y {Constants.endowment}."

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        group = player.group
        set_payoffs(group)


## cometario random.

class ResultsDictador(Page):
    @staticmethod
    def is_displayed(player):
        # Mostrar la página de resultados final solo en la última ronda (18)
        return player.round_number == 18

    @staticmethod
    def vars_for_template(player: Player):
        dictator_offers = []
        dictator_round_numbers = [15, 16, 17, 18]
        for rnd in dictator_round_numbers:
            p = player.in_round(rnd)
            visible_cat = player.participant.vars.get(f'visible_category_round_{rnd}', None)
            dictator_offers.append({
                'round': rnd,
                'category': visible_cat.capitalize() if visible_cat else "Sin categoría asignada",
                'kept': p.group.kept,
                'assigned': p.group.assigned or 0,
            })

        return dict(
            dictator_offers=dictator_offers
        )


page_sequence = [
    UserInfo,
    PreguntaM,
    Intro,
    RoundN,  # Rondas 1-14: IAT
    IATAssessmentPage,  # Ronda 15: Evaluación del IAT
    MoralDecisionPageCerteza,  # Ronda 15: Decisión
    # Results,                   # Por ahora, no queremos mostrar los resultados del IAT. En caso de querer hacer esto e
    # en caso de querer hacerlo, falta manejar los assement de acuerdo con la aleatorización del IAT.
    DictatorIntroduction,  # Rondas 16-18: Introducción al Dictador
    DictatorOffer,  # Rondas 16-18: Oferta del Dictador,    # Rondas 16-18: Espera de Resultados del Dictador
    ResultsDictador,  # Rondas 16-18: Resultados del Dictador,            # Ronda 18: Resultados Finales del Dictador
]


# página que podría ser útil, probablemente no.
class Results(Page):
    @staticmethod
    def is_displayed(player):
        # Mostrar la página de resultados en la ronda 14
        return player.round_number == 15

    @staticmethod
    def vars_for_template(player: Player):
        def extract(rnd):
            # Extraer tiempos de reacción de las rondas especificadas
            trials = [
                t
                for t in Trial.filter(player=player.in_round(rnd))
                if t.reaction_time is not None
            ]
            values = [t.reaction_time for t in trials]
            return values

        # Extraer datos para el primer IAT (rondas 3, 4, 6, 7)
        data3 = extract(3)
        data4 = extract(4)
        data6 = extract(6)
        data7 = extract(7)
        dscore1_result = dscore1(data3, data4, data6, data7)

        # Extraer datos para el segundo IAT (rondas 10, 13, 11, 14)
        data10 = extract(10)
        data13 = extract(13)
        data11 = extract(11)
        data14 = extract(14)
        dscore2_result = dscore2(data10, data13, data11, data14)

        # Recuperar el orden de las rondas del IAT
        iat_round_order = player.participant.vars.get('iat_round_order', [])

        # Asignar dscore1 y dscore2 según el orden de las rondas
        if iat_round_order == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
            player.dscore1 = dscore1_result
            player.dscore2 = dscore2_result
        elif iat_round_order == [8, 9, 10, 11, 12, 13, 14, 1, 2, 3, 4, 5, 6, 7]:
            player.dscore1 = dscore2_result
            player.dscore2 = dscore1_result
        else:
            # Manejo de otros posibles órdenes, si los hay
            player.dscore1 = dscore1_result
            player.dscore2 = dscore2_result

        # Obtener combinaciones de pares positivos y negativos para el primer IAT
        pos_pairs_iat1 = labels_for_block(get_block_for_round(3, player.session.params))
        neg_pairs_iat1 = labels_for_block(get_block_for_round(6, player.session.params))

        # Obtener combinaciones de pares positivos y negativos para el segundo IAT
        pos_pairs_iat2 = labels_for_block(get_block_for_round(10, player.session.params))
        neg_pairs_iat2 = labels_for_block(get_block_for_round(13, player.session.params))

        # Validar si los resultados están dentro o fuera de los rangos definidos
        dscore1_in_range = (
                player.dscore1 >= player.iat1_lower_limit and
                player.dscore1 <= player.iat1_upper_limit
        )
        dscore2_in_range = (
                player.dscore2 >= player.iat2_lower_limit and
                player.dscore2 <= player.iat2_upper_limit
        )

        # Decidir si mostrar u ocultar resultados en base a las preferencias del usuario
        show_dscore1 = (
                (dscore1_in_range and not player.hide_iat1_info_in_range) or
                (not dscore1_in_range and not player.hide_iat1_info_out_of_range)
        )
        show_dscore2 = (
                (dscore2_in_range and not player.hide_iat2_info_in_range) or
                (not dscore2_in_range and not player.hide_iat2_info_out_of_range)
        )

        # Manejar valores del jugador
        player_name = player.field_maybe_none('name') or "Anónimo"
        player_age = player.field_maybe_none('age') or 18
        player_sports = player.field_maybe_none('sports') or "Sin especificar"
        player_random_number = player.field_maybe_none('random_number') or 0
        moral_question = player.field_maybe_none('moral_question') or "Sin respuesta"
        iat1_self_assessment = player.field_maybe_none('iat1_self_assessment') or "No especificado"
        iat1_assessment_probability = player.field_maybe_none('iat1_assessment_probability') or 0
        iat2_self_assessment = player.field_maybe_none('iat2_self_assessment') or "No especificado"
        iat2_assessment_probability = player.field_maybe_none('iat2_assessment_probability') or 0

        return dict(
            show_dscore1=show_dscore1,
            show_dscore2=show_dscore2,
            dscore1=dscore1_result if show_dscore1 else None,
            dscore2=dscore2_result if show_dscore2 else None,
            pos_pairs_iat1=pos_pairs_iat1,
            neg_pairs_iat1=neg_pairs_iat1,
            pos_pairs_iat2=pos_pairs_iat2,
            neg_pairs_iat2=neg_pairs_iat2,
            player_name=player_name,
            player_age=player_age,
            player_sports=player_sports,
            player_random_number=player_random_number,
            moral_question=moral_question,
            iat1_self_assessment=iat1_self_assessment,
            iat1_assessment_probability=iat1_assessment_probability,
            iat2_self_assessment=iat2_self_assessment,
            iat2_assessment_probability=iat2_assessment_probability,
        )

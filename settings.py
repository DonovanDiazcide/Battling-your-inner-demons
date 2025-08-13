from os import environ
SESSION_CONFIGS = [
    dict(
        name="iat_images",
        display_name="iat using images",
        num_demo_participants=4,
        app_sequence=["iat"],
        # Opción A: exactamente 3 ST-IAT
        iat_n_st=3, iat_n_2cat=0,

        # Opción B: exactamente 3 de 2 categorías
        # iat_n_st=0, iat_n_2cat=3,

        # Opción C: 1 ST y 2 de 2 categorías
        # iat_n_st=1, iat_n_2cat=2,

        # Opción D: total=3, y que el tipo (ST/2CAT) se decida aleatoriamente por jugador
        # iat_total=3, iat_randomize_types=True,

        # Si no pones nada, por defecto tomamos iat_total=Constants.num_rounds

        #iats de minno:
        use_minno_iat = True,
        

        # st-iats de minno
        use_minno_stiat=True,   # ⬅️ Activa/desactiva la página de Minno (ST-IAT). 
        use_minno_stiat_sex = True,
        use_minno_stiat_dis = True,  # ⬅️ Activa/desactiva la página de Minno (ST-IAT) para disforia de género.



        # opcional, pero yo lo pongo explícito: (comenario mío, creo que esta es un línea de código para indicarle al programa de donde jalar el iat, creo que entonces para dejar 
        #el iat dinámico voy a tener que tener 6 links en total, espero sea eso, primero quiero ver que su enfoque para calcular el d-score sea correcto.)
        stiat_task_url = "https://cdn.jsdelivr.net/gh/baranan/minno-tasks@0.*/stiat/qualtrics/exampleSTIAT.js",
        # si alguna vez necesitas fallback por bloque:
        # stiat_block_map = {'compatible':[5], 'incompatible':[7]},


        #quitar esto para cuando se corra en Prolific
        prolific_completion_url="https://app.prolific.com/submissions/complete?cc=XXXXXXX",
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    # cada punto vale 0 unidades monetarias ahora, cambiar a 1 cuando se corra en Prolific. 
    # comentario justo después de probar lo de arriba: ok, ya el payoff bonus es 0, buenísimo. 
    real_world_currency_per_point=0.001, participation_fee=0.001, doc=""
)

PARTICIPANT_FIELDS = ['is_dropout', 'finished']

#session fields to store parameters and prolific url, esto es para implementar el experimento en Prolific, se necesita un link de completación. 
SESSION_FIELDS = ['params', 'prolific_completion_url']

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = "en"

# e.g. EUR, GBP, CNY, JPY. Nota: hay que cambiar esto a dólares cuando se corra el experimento en pROLIFIC
REAL_WORLD_CURRENCY_CODE = "MXN"
USE_POINTS = True  # if True, then points are used instead of real-world currency

ADMIN_USERNAME = "admin"
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get("OTREE_ADMIN_PASSWORD")

DEMO_PAGE_TITLE = "Welcome to iat based experiment"
DEMO_PAGE_INTRO_HTML = """
Espera las instrucciones para saber a qué página del iat ingresar
"""

SECRET_KEY = "2015765205890"

# adjustments for testing
# generating session configs for all varieties of features
import sys

ROOMS = [
    dict(
        name='iat_experiment',
        display_name='iat_experiment',
        participant_label_file='_rooms/econ101.txt',
    ),
    dict(name='live_demo', display_name='Room for live demo (no participant labels)'),

    dict(
        name='your_prolific_study',
        display_name='your_prolific_study',
        # participant_label_file='_rooms/your_study.txt',
        # use_secure_urls=True,
    ),
]


if sys.argv[1] == 'test':
    MAX_ITERATIONS = 5
    FREEZE_TIME = 100
    TRIAL_PAUSE = 200
    TRIAL_TIMEOUT = 300

    SESSION_CONFIGS = [
        dict(
            name=f"testing_generic",
            num_demo_participants=1,
            app_sequence=['generic'],
            auto_response_time=None,
            input_freezing_time=FREEZE_TIME,
            inter_trial_time=TRIAL_PAUSE,
            num_iterations=MAX_ITERATIONS,
            attempts_per_trial=1,
            categories={'foo': 'positive', 'bar': 'negative'},
            labels={'foo': 'Positive', 'bar': 'Negative'},
        ),
        dict(
            name=f"testing_generic_retries",
            num_demo_participants=1,
            app_sequence=['generic'],
            auto_response_time=None,
            input_freezing_time=FREEZE_TIME,
            inter_trial_time=TRIAL_PAUSE,
            num_iterations=MAX_ITERATIONS,
            attempts_per_trial=3,
            categories={'foo': 'positive', 'bar': 'negative'},
            labels={'foo': 'Positive', 'bar': 'Negative'},
        ),
        dict(
            name=f"testing_generic_gonogo",
            num_demo_participants=1,
            app_sequence=['generic'],
            auto_response_time=TRIAL_TIMEOUT,
            input_freezing_time=FREEZE_TIME,
            inter_trial_time=TRIAL_PAUSE,
            num_iterations=MAX_ITERATIONS,
            attempts_per_trial=1,
            categories={'foo': 'positive', 'bar': 'negative'},
            labels={'foo': 'Positive', 'bar': 'Negative'},
        ),
        dict(
            name=f"testing_iat",
            num_demo_participants=1,
            app_sequence=['iat'],
            trial_delay=TRIAL_PAUSE / 1000.0,
            retry_delay=FREEZE_TIME / 1000.0,
            primary=['canidae', 'felidae'],
            secondary=['positive', 'negative'],
            num_iterations={1: 2, 2: 2, 3: 3, 4: 3, 5: 2, 6: 3, 7: 3},
        ),
        dict(
            name=f"testing_sliders",
            num_demo_participants=1,
            app_sequence=['sliders'],
            trial_delay=TRIAL_PAUSE / 1000.0,
            retry_delay=FREEZE_TIME / 1000.0,
            num_sliders=3,
            attempts_per_slider=3,
        ),
    ]
    for task in ['decoding', 'matrix', 'transcription']:
        SESSION_CONFIGS.extend(
            [
                dict(
                    name=f"testing_{task}_defaults",
                    num_demo_participants=1,
                    app_sequence=['real_effort'],
                    puzzle_delay=TRIAL_PAUSE / 1000.0,
                    retry_delay=FREEZE_TIME / 1000.0,
                ),
                dict(
                    name=f"testing_{task}_retrying",
                    num_demo_participants=1,
                    app_sequence=['real_effort'],
                    puzzle_delay=TRIAL_PAUSE / 1000.0,
                    retry_delay=FREEZE_TIME / 1000.0,
                    attempts_per_puzzle=5,
                ),
                dict(
                    name=f"testing_{task}_limited",
                    num_demo_participants=1,
                    app_sequence=['real_effort'],
                    puzzle_delay=TRIAL_PAUSE / 1000.0,
                    retry_delay=FREEZE_TIME / 1000.0,
                    max_iterations=MAX_ITERATIONS,
                ),
            ]
        )
"""Configuración de rondas
Categories are configured in session config like:
```primary = ['male', 'female'], secondary = ['work', 'family']```
Numbers in block config corresponds to 1st and 2nd element of corresponding pair
"""
import copy
import random

BLOCKS1 = {
    # Rondas 1 a 7 (primer bloque: categorías 1 y 2)
    1: {
        'title': "Ronda 1 (práctica)",
        'practice': True,
        'left': {'primary': 1},
        'right': {'primary': 2},
    },
    2: {
        'title': "Ronda 2 (práctica)",
        'practice': True,
        'left': {'secondary': 1},
        'right': {'secondary': 2},
    },
    3: {
        'title': "Ronda 3",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    4: {
        'title': "Ronda 4",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    5: {
        'title': "Ronda 5 (práctica)",
        'practice': True,
        'left': {'primary': 2},
        'right': {'primary': 1},
    },
    6: {
        'title': "Ronda 6",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
    7: {
        'title': "Ronda 7",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
    # Rondas 8 a 14 (segundo bloque: categorías 3 y 4)
    8: {
        'title': "Ronda 1 (práctica)",
        'practice': True,
        'left': {'primary': 3},
        'right': {'primary': 4},
    },
    9: {
        'title': "Ronda 2 (práctica)",
        'practice': True,
        'left': {'secondary': 3},
        'right': {'secondary': 4},
    },
    10: {
        'title': "Ronda 3",
        'practice': False,
        'left': {'primary': 3, 'secondary': 3},
        'right': {'primary': 4, 'secondary': 4},
    },
    11: {
        'title': "Ronda 4",
        'practice': False,
        'left': {'primary': 3, 'secondary': 3},
        'right': {'primary': 4, 'secondary': 4},
    },
    12: {
        'title': "Ronda 5 (práctica)",
        'practice': True,
        'left': {'primary': 4},
        'right': {'primary': 3},
    },
    13: {
        'title': "Ronda 6",
        'practice': False,
        'left': {'primary': 4, 'secondary': 3},
        'right': {'primary': 3, 'secondary': 4},
    },
    14: {
        'title': "Ronda 7",
        'practice': False,
        'left': {'primary': 4, 'secondary': 3},
        'right': {'primary': 3, 'secondary': 4},
    },
    # Bloques adicionales: feedback, juego y agradecimiento
    15: {
        'title': "Ronda 15 (Feedbackiat, resultados, juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    16: {
        'title': "Ronda 16 (juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    17: {
        'title': "Ronda 17 (juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    18: {
        'title': "Ronda 18 (juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    19: {
        'title': "Agradecimiento",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    }
}

# Configuración de bloques – Orden 2 (BLOCKS2)
BLOCKS2 = {
    # Rondas 1 a 7: invertimos el orden de las categorías primarias (2 y 1)
    1: {
        'title': "Ronda 1 (práctica)",
        'practice': True,
        'left': {'primary': 3},
        'right': {'primary': 4},
    },
    2: {
        'title': "Ronda 2 (práctica)",
        'practice': True,
        'left': {'secondary': 3},
        'right': {'secondary': 4},
    },
    3: {
        'title': "Ronda 3",
        'practice': False,
        'left': {'primary': 3, 'secondary': 3},
        'right': {'primary': 4, 'secondary': 4},
    },
    4: {
        'title': "Ronda 4",
        'practice': False,
        'left': {'primary': 3, 'secondary': 3},
        'right': {'primary': 4, 'secondary': 4},
    },
    5: {
        'title': "Ronda 5 (práctica)",
        'practice': True,
        'left': {'primary': 4},
        'right': {'primary': 3},
    },
    6: {
        'title': "Ronda 6",
        'practice': False,
        'left': {'primary': 4, 'secondary': 3},
        'right': {'primary': 3, 'secondary': 4},
    },
    7: {
        'title': "Ronda 7",
        'practice': False,
        'left': {'primary': 4, 'secondary': 3},
        'right': {'primary': 3, 'secondary': 4},
    },
    # Rondas 8 a 14: para el segundo bloque, invertimos el orden (4 y 3)
    8: {
        'title': "Ronda 1 (práctica)",
        'practice': True,
        'left': {'primary': 1},
        'right': {'primary': 2},
    },
    9: {
        'title': "Ronda 2 (práctica)",
        'practice': True,
        'left': {'secondary': 1},
        'right': {'secondary': 2},
    },
    10: {
        'title': "Ronda 3",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    11: {
        'title': "Ronda 4",
        'practice': False,
        'left': {'primary': 1, 'secondary': 1},
        'right': {'primary': 2, 'secondary': 2},
    },
    12: {
        'title': "Ronda 5 (práctica)",
        'practice': True,
        'left': {'primary': 2},
        'right': {'primary': 1},
    },
    13: {
        'title': "Ronda 6",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
    14: {
        'title': "Ronda 7",
        'practice': False,
        'left': {'primary': 2, 'secondary': 1},
        'right': {'primary': 1, 'secondary': 2},
    },
    # Bloques adicionales: feedback, juego y agradecimiento (idénticos a BLOCKS1)
    15: {
        'title': "Ronda 15 (Feedbackiat, resultados, juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    16: {
        'title': "Ronda 16 (juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    17: {
        'title': "Ronda 17 (juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    18: {
        'title': "Ronda 18 (juego)",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    },
    19: {
        'title': "Agradecimiento",
        'practice': False,
        'left': {'primary': '', 'secondary': ''},
        'right': {'primary': '', 'secondary': ''}
    }
}

# Genera el iat_ordering
direct = list(range(1, 15))
invertido = list(range(8, 15)) + list(range(1, 8))
iat_ordering = random.choice([direct, invertido])

# Condicional para asignar la configuración de bloques
if iat_ordering == direct:
    BLOCKS = BLOCKS1
else:
    BLOCKS = BLOCKS2

def configure(block, config):
    """Insertar nombres de categorías desde la configuración en el setup del bloque.
    block: {'left': {'primary': 1, 'secondary': 1}, 'right': {'primary': 2, 'secondary': 2}}
    config: {'primary': ['maledsadsa', 'female'], 'secondary': ['work', 'family']}
    result: {'left': {'primar   y': 'male', 'secondary': 'work'}, 'right': {'primary': 'female', 'secondary': 'family'}}
    """
    result = copy.deepcopy(block)
    for side in ['left', 'right']:
        for cls, idx in block[side].items():
            if isinstance(idx, int):
                try:
                    # Asegurarse de que el índice esté dentro del rango
                    result[side][cls] = config[cls][idx - 1]
                except (IndexError, KeyError):
                    # Si el índice está fuera de rango o la clave no existe, asignar una cadena vacía
                    result[side][cls] = ''
            else:
                # Si idx no es un entero, asignar una cadena vacía o manejarlo según tu lógica
                result[side][cls] = ''
    return result

"""Dictionary of all words by category

The categories should be paired and put into `primary` or `secondary` session config parameters:
```primary = ['male', 'female'], secondary = ['work', 'family']```

If a file stimuli.csv is present in app dir,
it's content is loaded into the DICT.
the csv should contain (at least) two columns: category, stimulus.
"""

from pathlib import Path
import csv

DICT = {
    'Personas obesas': ['dog', 'wolf', 'coyote', 'fox', 'jackal'],
    'Personas delgadas': ['cat', 'tiger', 'lynx', 'wildcat', 'cougar'],
    'Personas homosexuales': ['word1', 'word2', 'word3', 'word4', 'word5'],
    'Personas heterosexuales': ['word1', 'word2', 'word3', 'word4', 'word5'],

    'images:Personas homosexuales': [
        "homofinal.png",
        "05_GAY.jpg",
        "homo1.png",
        "homo2.png",
        "07_lesbian.jpg",
        "15_lesbian.jpg",
        "14_gay.jpg"
    ],
    "images:Personas heterosexuales": [
        "heterofinal.png",
        "06_hetero.jpg",
        "hetero1.png",
        "hetero2.png",
        "13_hetero.jpg",
    ],
    # ojo, esto era gato/canidae
    'images:Personas delgadas': [
        "1_A.jpg",
        "2_A.jpg",
        "3_A.jpg",
        "4_A.jpg",
        "5_A.jpg",
        "6_A.jpg",
        "7_A.jpg",
        "8_A.jpg",
        "9_A.jpg",
        "10_A.jpg",
    ],
    "images:Personas obesas": [
        "1_B.jpg",
        "2_B.jpg",
        "3_B.jpg",
        "4_B.jpg",
        "5_B.jpg",
        "6_B.jpg",
        "7_B.jpg",
        "8_B.jpg",
        "9_B.jpg",
        "10_B.jpg",
    ],
    'bueno': ['amusement', 'fun', 'friendship', 'happyness', 'joy'],
    'malo': ['anger', 'hate', 'fear', 'panic', 'sickness'],
    #bueno obeso
    'images:Bueno': [
        #aquí le puedo pedir a chatgpt que genere pngs de las midmas dimensiones al igual que la imagen de etc.
        "bueno1.png",
        "bueno2.png",
        "bueno3.png",
        "bueno4.png",
        "bueno5.png",
        "bueno6.png",
        "bueno7.png",
        "bueno8.png",
    ],
    #malo obseo
    'images:Malo': [
        "malo1.png",
        "malo2.png",
        "malo3.png",
        "malo4.png",
        "malo5.png",
        "malo6.png",
        "malo7.png",
        "malo8.png",
    ],
    #bueno sexualidad
'images:bueno sexualidad': [
        #aquí le puedo pedir a chatgpt que genere pngs de las midmas dimensiones al igual que la imagen de etc.
        "emoji_u263a.png",
        "emoji_u1f600.png",
        "emoji_u1f601.png",
        "emoji_u1f60a.png",
        "emoji_u1f60d.png",
    ],
    #malo sexualidad
    'images:malo sexualidad': [
        "emoji_u2639.png",
        "emoji_u1f612.png",
        "emoji_u1f616.png",
        "emoji_u1f623.png",
        "emoji_u1f62c.png",
    ],
}

csvfile = Path(__file__).parent / "stimuli.csv"

if csvfile.exists():
    with open(csvfile, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row['category']
            word = row['stimulus']
            if cat not in DICT:
                DICT[cat] = []
            DICT[cat].append(word)

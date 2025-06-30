"""Calculating d-score in pure python

All data are list of float values

Implementation of d-score according to this snapshot:
http://faculty.washington.edu/agg/iatmaterials/Summary%20of%20Improved%20Scoring%20Algorithm.pdf
"""

import math

def mean(data: list):
    """Calcula la media de una lista de valores."""
    if not data:  # Manejo para listas vacías
        return 0
    return sum(data) / len(data)

def std(data: list):
    """Calcula la desviación estándar de una lista de valores."""
    if len(data) < 2:  # Manejo para listas con menos de dos elementos
        return 0
    cnt = len(data)
    m = sum(data) / cnt
    sqs = sum((v - m) ** 2 for v in data)
    ssq = sqs / (cnt - 1)
    return math.sqrt(ssq)


def dscore1(data3: list, data4: list, data6: list, data7: list):
    # Filtrar valores demasiado largos
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
    if len(short_data) / len(total_data) > 0.1:
        return None

    # Calcular el d-score
    combined_3_6 = data3 + data6
    combined_4_7 = data4 + data7

    std_3_6 = std(combined_3_6)
    std_4_7 = std(combined_4_7)

    mean_3_6 = mean(data6) - mean(data3)
    mean_4_7 = mean(data7) - mean(data4)

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
    if len(short_data) / len(total_data) > 0.1:
        return None

    # Calcular el d-score
    combined_10_11 = data10 + data11
    combined_13_14 = data13 + data14

    std_10_11 = std(combined_10_11)
    std_13_14 = std(combined_13_14)

    mean_10_11 = mean(data11) - mean(data10)
    mean_13_14 = mean(data14) - mean(data13)

    dscore_10_11 = mean_10_11 / std_10_11 if std_10_11 > 0 else 0
    dscore_13_14 = mean_13_14 / std_13_14 if std_13_14 > 0 else 0

    dscore_mean2 = (dscore_10_11 + dscore_13_14) * 0.5
    return dscore_mean2

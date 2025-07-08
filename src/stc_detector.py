# src/stc_detector.py
import math

def calcular_riesgo(muestras):
    """
    Calcula un índice 0-100 a partir de la magnitud RMS
    de la velocidad angular (rad/s) recibida en 'muestras'.
    """
    if not muestras:
        return 0
    suma = sum(x*x + y*y + z*z for x, y, z in muestras)
    rms = math.sqrt(suma / len(muestras))          # valor medio cuadrático
    indice = min(100, (rms / 7.0) * 100)           # escala arbitraria
    return round(indice, 1)

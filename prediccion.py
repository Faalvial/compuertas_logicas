"""Predicción de la CNN con numpy, sin TensorFlow.

TensorFlow ocupa más de 1 GB y no entra en el plan gratuito de PythonAnywhere.
Pero una red ya entrenada solo hace multiplicaciones con sus pesos, así que
aquí se repiten con numpy las mismas capas de la CNN del notebook.
Los pesos se guardan desde el notebook en pesos_cnn.npz.
"""
import os

import numpy as np
from PIL import Image

TAM = 64        # tamaño de entrada de la CNN, igual que en el notebook
MARGEN = 0.08   # margen alrededor del dibujo, igual que en el notebook


def cargar_pesos(ruta):
    """Lista de arreglos [kernel, sesgo, kernel, sesgo, ...] o None si no hay modelo."""
    if not os.path.exists(ruta):
        return None
    with np.load(ruta) as datos:
        return [datos[f"arr_{i}"] for i in range(len(datos.files))]


def preprocesar(imagen):
    """Mismo preprocesamiento que el notebook: recorte a la tinta, cuadrado con margen y 64x64."""
    alfa = imagen.convert("RGBA").getchannel("A")
    caja = alfa.getbbox()
    if caja is None:
        return None
    x0, y0, x1, y1 = caja
    lado = int(max(x1 - x0, y1 - y0) * (1 + 2 * MARGEN))
    cuadrado = Image.new("L", (lado, lado), 0)
    cuadrado.paste(alfa.crop(caja), ((lado - (x1 - x0)) // 2, (lado - (y1 - y0)) // 2))
    pequena = cuadrado.resize((TAM, TAM), Image.Resampling.LANCZOS)
    return np.asarray(pequena, dtype=np.float32) / 255.0


def convolucion(x, kernel, sesgo):
    """Conv2D 3x3 con padding "same" y ReLU. x: (alto, ancho, canales)."""
    alto, ancho = x.shape[:2]
    k = kernel.shape[0]
    x = np.pad(x, ((k // 2, k // 2), (k // 2, k // 2), (0, 0)))
    salida = np.zeros((alto, ancho, kernel.shape[3]), dtype=np.float32) + sesgo
    for i in range(k):
        for j in range(k):
            salida += x[i:i + alto, j:j + ancho] @ kernel[i, j]
    return np.maximum(salida, 0)


def max_pooling(x):
    """MaxPooling2D 2x2: se queda con el máximo de cada bloque de 2x2."""
    alto, ancho, canales = x.shape
    return x.reshape(alto // 2, 2, ancho // 2, 2, canales).max(axis=(1, 3))


def predecir(entrada, pesos):
    """Probabilidad de cada clase para una imagen de TAM x TAM.

    El aumento de datos y el dropout solo actúan al entrenar, por eso no aparecen.
    """
    c1, s1, c2, s2, c3, s3, c4, s4, c5, s5, d1, t1, d2, t2 = pesos
    x = entrada[:, :, None]
    x = max_pooling(convolucion(convolucion(x, c1, s1), c2, s2))
    x = max_pooling(convolucion(convolucion(x, c3, s3), c4, s4))
    x = max_pooling(convolucion(x, c5, s5))
    x = x.reshape(-1)                  # Flatten
    x = np.maximum(x @ d1 + t1, 0)     # Dense(128) + ReLU
    z = x @ d2 + t2                    # Dense(6)
    z = np.exp(z - z.max())            # Softmax
    return z / z.sum()

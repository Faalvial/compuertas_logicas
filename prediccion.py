"""Predicción de la CNN con numpy, sin TensorFlow.

TensorFlow ocupa más de 1 GB y no entra en el plan gratuito de PythonAnywhere.
Pero una red ya entrenada solo hace multiplicaciones con sus pesos, así que
aquí se repiten con numpy las mismas capas de la CNN del notebook.
Los pesos se guardan desde el notebook en pesos_cnn.npz.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TAM = 64        # tamaño de entrada de la CNN, igual que en el notebook
MARGEN = 0.08   # margen alrededor del dibujo, igual que en el notebook
LIENZO = 256    # lado del lienzo de la app
GROSOR = 8      # grosor del trazo en el lienzo de la app


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


def umbral_otsu(gris):
    """Umbral que mejor separa los píxeles oscuros (tinta) de los claros (papel)."""
    hist = np.bincount(gris.ravel(), minlength=256).astype(np.float64)
    p = hist / hist.sum()
    w = np.cumsum(p)
    mu = np.cumsum(p * np.arange(256))
    varianza = (mu[-1] * w - mu) ** 2 / (w * (1 - w) + 1e-12)
    return int(np.argmax(varianza))


def quitar_lo_que_no_es_compuerta(mascara):
    """Deja solo la compuerta cuando la imagen trae además texto, marcas o manchas.

    Se engrosa la tinta para que los trazos cercanos de un mismo dibujo queden unidos y se
    separa en manchas. La compuerta es la mancha con la caja más grande: un texto ocupa una
    franja delgada aunque sea ancho. Se conservan también las manchas que caen dentro de esa
    caja o muy cerca de ella (por ejemplo, el arco suelto de un XOR)."""
    lado = max(mascara.size)
    unida = mascara.filter(ImageFilter.MaxFilter(2 * max(1, lado // 80) + 1))
    etiquetas = unida.point(lambda v: 255 if v else 0)
    cajas = []
    while len(cajas) < 254:
        a = np.asarray(etiquetas)
        libres = np.flatnonzero(a == 255)
        if not libres.size:
            break
        y, x = divmod(int(libres[0]), a.shape[1])
        ImageDraw.floodfill(etiquetas, (x, y), len(cajas) + 1)
        cajas.append(etiquetas.point(lambda v, n=len(cajas) + 1: 255 if v == n else 0).getbbox())
    if len(cajas) <= 1:
        return mascara
    # Se parte de la mancha con la caja más grande y se le suman las que están cerca de ella.
    principal = max(range(len(cajas)), key=lambda n: (cajas[n][2] - cajas[n][0]) * (cajas[n][3] - cajas[n][1]))
    x0, y0, x1, y1 = cajas[principal]
    dentro, cambio = {principal + 1}, True
    while cambio:
        cambio = False
        limite = 0.05 * max(x1 - x0, y1 - y0)
        for n, (a0, b0, a1, b1) in enumerate(cajas):
            if n + 1 not in dentro and max(a0 - x1, x0 - a1, b0 - y1, y0 - b1) <= limite:
                dentro.add(n + 1)
                x0, y0, x1, y1 = min(x0, a0), min(y0, b0), max(x1, a1), max(y1, b1)
                cambio = True
    conservar = np.isin(np.asarray(etiquetas), list(dentro))
    return Image.fromarray(np.where(conservar, np.asarray(mascara), 0).astype(np.uint8))


def desde_imagen(imagen):
    """Convierte una imagen subida (foto de un dibujo en papel, captura, etc.) en un dibujo
    como los del lienzo: trazo en el canal alfa, en 256x256 y con un grosor de unos 8 píxeles.
    Devuelve None si no encuentra trazo."""
    fondo = Image.new("RGBA", imagen.size, "white")
    gris = np.asarray(Image.alpha_composite(fondo, imagen.convert("RGBA")).convert("L"))
    tinta = gris <= umbral_otsu(gris)
    if tinta.mean() > 0.5:          # trazo claro sobre fondo oscuro
        tinta = ~tinta
    mascara = Image.fromarray(tinta.astype(np.uint8) * 255).filter(ImageFilter.MedianFilter(3))
    mascara = quitar_lo_que_no_es_compuerta(mascara)
    caja = mascara.getbbox()
    if caja is None:
        return None

    # Se escala para que mida como un dibujo típico del lienzo (unos 210 píxeles de ancho o alto).
    recorte = mascara.crop(caja)
    escala = 210 / max(recorte.size)

    # Antes de escalar, se engrosa o adelgaza el trazo para que después quede de unos 8 píxeles.
    # Grosor del trazo = 2 * área / píxeles del borde.
    t = np.asarray(recorte) > 0
    borde = t & ~(np.roll(t, 1, 0) & np.roll(t, -1, 0) & np.roll(t, 1, 1) & np.roll(t, -1, 1))
    grosor = 2 * t.sum() / max(borde.sum(), 1)
    pasos = min(round(abs(GROSOR / escala - grosor) / 2), 12)
    if pasos and grosor < GROSOR / escala:
        recorte = recorte.filter(ImageFilter.MaxFilter(2 * pasos + 1))
    elif pasos:
        recorte = recorte.filter(ImageFilter.MinFilter(2 * min(pasos, int(grosor / 4)) + 1))
    recorte = recorte.resize((max(1, round(recorte.width * escala)), max(1, round(recorte.height * escala))),
                             Image.Resampling.LANCZOS).point(lambda v: 255 if v >= 128 else 0)

    lienzo = Image.new("L", (LIENZO, LIENZO), 0)
    lienzo.paste(recorte, ((LIENZO - recorte.width) // 2, (LIENZO - recorte.height) // 2))
    dibujo = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0))
    dibujo.putalpha(lienzo)
    return dibujo


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
    z = x @ d2 + t2                    # Dense(7)
    z = np.exp(z - z.max())            # Softmax
    return z / z.sum()

"""Genera dibujos de la clase OTRO: cosas que no son compuertas (formas, letras, flechas, garabatos).
Cada dibujo imita el lienzo de la app: 256x256, trazo negro de 8 px con puntas redondas, en el canal alfa."""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

LIENZO, GROSOR = 256, 8
rng = np.random.default_rng(int(sys.argv[3]) if len(sys.argv) > 3 else 0)

def arco(cx, cy, rx, ry, a0, a1, n=40):
    t = np.linspace(a0, a1, n)
    return list(zip(cx + rx * np.cos(t), cy + ry * np.sin(t)))

def poli(*pts):
    return [tuple(p) for p in pts]

# Cada forma devuelve una lista de trazos en coordenadas aproximadamente dentro de [0, 1].
LETRAS = {
    "A": [poli((0, 1), (0.5, 0), (1, 1)), poli((0.25, 0.55), (0.75, 0.55))],
    "E": [poli((1, 0), (0, 0), (0, 1), (1, 1)), poli((0, 0.5), (0.7, 0.5))],
    "F": [poli((1, 0), (0, 0), (0, 1)), poli((0, 0.5), (0.7, 0.5))],
    "H": [poli((0, 0), (0, 1)), poli((1, 0), (1, 1)), poli((0, 0.5), (1, 0.5))],
    "K": [poli((0, 0), (0, 1)), poli((1, 0), (0, 0.55), (1, 1))],
    "L": [poli((0, 0), (0, 1), (0.8, 1))],
    "M": [poli((0, 1), (0, 0), (0.5, 0.6), (1, 0), (1, 1))],
    "N": [poli((0, 1), (0, 0), (1, 1), (1, 0))],
    "T": [poli((0, 0), (1, 0)), poli((0.5, 0), (0.5, 1))],
    "V": [poli((0, 0), (0.5, 1), (1, 0))],
    "W": [poli((0, 0), (0.25, 1), (0.5, 0.4), (0.75, 1), (1, 0))],
    "Y": [poli((0, 0), (0.5, 0.5), (1, 0)), poli((0.5, 0.5), (0.5, 1))],
    "Z": [poli((0, 0), (1, 0), (0, 1), (1, 1))],
    "1": [poli((0.2, 0.25), (0.6, 0), (0.6, 1))],
    "4": [poli((0.7, 1), (0.7, 0), (0, 0.65), (1, 0.65))],
    "7": [poli((0, 0), (1, 0), (0.4, 1))],
    "C": [arco(0.55, 0.5, 0.5, 0.5, 0.3 * math.pi, 1.7 * math.pi)],
    "O": [arco(0.5, 0.5, 0.4, 0.5, 0, 2 * math.pi)],
    "S": [arco(0.5, 0.27, 0.35, 0.25, -0.2 * math.pi, 1.5 * math.pi)[::-1][:-1] + arco(0.5, 0.75, 0.35, 0.25, -0.5 * math.pi, 1.2 * math.pi)],
    "B": [poli((0, 0), (0, 1)), arco(0, 0.25, 0.7, 0.25, -0.5 * math.pi, 0.5 * math.pi), arco(0, 0.75, 0.85, 0.25, -0.5 * math.pi, 0.5 * math.pi)],
    "P": [poli((0, 1), (0, 0)), arco(0, 0.27, 0.8, 0.27, -0.5 * math.pi, 0.5 * math.pi)],
    "R": [poli((0, 1), (0, 0)), arco(0, 0.27, 0.8, 0.27, -0.5 * math.pi, 0.5 * math.pi), poli((0.3, 0.54), (0.9, 1))],
    "2": [arco(0.5, 0.3, 0.4, 0.3, math.pi, 2.2 * math.pi) + [(0, 1), (1, 1)]],
    "3": [arco(0.4, 0.27, 0.45, 0.25, -0.9 * math.pi, 0.5 * math.pi), arco(0.4, 0.75, 0.5, 0.25, -0.5 * math.pi, 0.9 * math.pi)],
    "8": [arco(0.5, 0.27, 0.3, 0.25, 0, 2 * math.pi), arco(0.5, 0.75, 0.38, 0.25, 0, 2 * math.pi)],
}

def letra():
    return LETRAS[rng.choice(list(LETRAS))]

def palabra():
    n = int(rng.integers(2, 4)); trazos = []
    for k, c in enumerate(rng.choice(list(LETRAS), n)):
        trazos += [[(x * 0.8 + 1.1 * k, y) for x, y in t] for t in LETRAS[c]]
    return trazos

def figura():
    tipo = rng.choice(["circulo", "elipse", "cuadrado", "rectangulo", "triangulo", "estrella", "rombo", "pentagono", "corazon", "nube"])
    if tipo == "circulo": return [arco(0.5, 0.5, 0.5, 0.5, 0, 2 * math.pi + rng.uniform(0, 0.4))]
    if tipo == "elipse": return [arco(0.5, 0.5, 0.5, rng.uniform(0.2, 0.4), 0, 2 * math.pi + 0.2)]
    if tipo == "cuadrado": return [poli((0, 0), (1, 0), (1, 1), (0, 1), (0, 0))]
    if tipo == "rectangulo": h = rng.uniform(0.3, 0.6); return [poli((0, 0), (1, 0), (1, h), (0, h), (0, 0))]
    if tipo == "triangulo": return [poli((0.5, 0), (1, 0.9), (0, 0.9), (0.5, 0))]
    if tipo == "rombo": return [poli((0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5), (0.5, 0))]
    if tipo == "pentagono": return [[(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)) for a in np.linspace(-math.pi / 2, 1.5 * math.pi, 6)]]
    if tipo == "estrella":
        pts = [(0.5 + (0.5 if k % 2 == 0 else 0.2) * math.cos(-math.pi / 2 + k * math.pi / 5), 0.5 + (0.5 if k % 2 == 0 else 0.2) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(11)]
        return [pts]
    if tipo == "corazon":
        t = np.linspace(0, 2 * math.pi, 60)
        return [list(zip(0.5 + 0.03 * 16 * np.sin(t) ** 3, 0.45 - 0.03 * (13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))))]
    # nube
    trazo = []
    for k, cx in enumerate(np.linspace(0.15, 0.85, 4)):
        trazo += arco(cx, 0.5, 0.15, 0.2, math.pi, 2 * math.pi, 15)
    return [trazo + [(0.85, 0.6), (0.15, 0.6), trazo[0]]]

def simbolo():
    tipo = rng.choice(["flecha", "x", "mas", "check", "zigzag", "onda", "espiral", "carita", "casa", "rayas", "igual", "interrogacion", "linea"])
    if tipo == "flecha": return [poli((0, 0.5), (1, 0.5)), poli((0.75, 0.3), (1, 0.5), (0.75, 0.7))]
    if tipo == "x": return [poli((0, 0), (1, 1)), poli((1, 0), (0, 1))]
    if tipo == "mas": return [poli((0.5, 0), (0.5, 1)), poli((0, 0.5), (1, 0.5))]
    if tipo == "check": return [poli((0, 0.6), (0.35, 1), (1, 0))]
    if tipo == "zigzag": n = int(rng.integers(3, 7)); return [[(k / n, 0.2 + 0.6 * (k % 2)) for k in range(n + 1)]]
    if tipo == "onda": t = np.linspace(0, 1, 50); f = rng.uniform(1, 3); return [list(zip(t, 0.5 + 0.25 * np.sin(2 * math.pi * f * t)))]
    if tipo == "espiral": t = np.linspace(0, rng.uniform(3, 6) * math.pi, 120); r = 0.5 * t / t.max(); return [list(zip(0.5 + r * np.cos(t), 0.5 + r * np.sin(t)))]
    if tipo == "carita": return [arco(0.5, 0.5, 0.5, 0.5, 0, 2 * math.pi + 0.2), arco(0.35, 0.38, 0.03, 0.03, 0, 2 * math.pi, 8), arco(0.65, 0.38, 0.03, 0.03, 0, 2 * math.pi, 8), arco(0.5, 0.55, 0.25, 0.2, 0.15 * math.pi, 0.85 * math.pi)]
    if tipo == "casa": return [poli((0.1, 0.45), (0.1, 1), (0.9, 1), (0.9, 0.45)), poli((0, 0.5), (0.5, 0), (1, 0.5))]
    if tipo == "rayas": return [poli((rng.uniform(0, 0.6), y), (rng.uniform(0.6, 1), y + rng.uniform(-0.1, 0.1))) for y in np.linspace(0, 1, int(rng.integers(2, 5)))]
    if tipo == "igual": return [poli((0, 0.35), (1, 0.35)), poli((0, 0.65), (1, 0.65))]
    if tipo == "interrogacion": return [arco(0.5, 0.25, 0.3, 0.25, math.pi, 2.5 * math.pi) + [(0.5, 0.7)], arco(0.5, 0.92, 0.03, 0.03, 0, 2 * math.pi, 8)]
    return [poli((0, rng.uniform(0, 1)), (1, rng.uniform(0, 1)))]

def garabato():
    """Curvas suaves que pasan por puntos al azar (suavizado de Chaikin)."""
    trazos = []
    for _ in range(int(rng.integers(1, 3))):
        pts = rng.uniform(0, 1, (int(rng.integers(4, 9)), 2))
        for _ in range(4):
            q = 0.75 * pts[:-1] + 0.25 * pts[1:]
            r = 0.25 * pts[:-1] + 0.75 * pts[1:]
            pts = np.vstack([pts[:1], np.column_stack([q, r]).reshape(-1, 2), pts[-1:]])
        trazos.append([tuple(p) for p in pts])
    return trazos

def dibujar(trazos):
    pts = np.concatenate([np.array(t, float) for t in trazos])
    ang = rng.uniform(0, 2 * math.pi) if rng.random() < 0.5 else rng.normal(0, 0.15)
    rot = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    centro = (pts.min(0) + pts.max(0)) / 2
    trazos = [(np.array(t, float) - centro) @ rot.T for t in trazos]
    pts = np.concatenate(trazos)
    lado = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]), 1e-3)
    escala = rng.uniform(110, 220) / lado
    desplaz = LIENZO / 2 + rng.uniform(-20, 20, 2)
    img = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for t in trazos:
        t = t * escala + desplaz
        t = t + np.cumsum(rng.normal(0, 0.6, t.shape), axis=0) * 0.3   # pulso de la mano
        t = np.clip(t, 6, LIENZO - 6)
        lista = [tuple(p) for p in t]
        if len(lista) > 1:
            d.line(lista, fill="black", width=GROSOR, joint="curve")
        for x, y in (lista[0], lista[-1]):
            d.ellipse((x - GROSOR / 2, y - GROSOR / 2, x + GROSOR / 2, y + GROSOR / 2), fill="black")
    return img

GENERADORES = [(letra, 0.25), (palabra, 0.1), (figura, 0.25), (simbolo, 0.25), (garabato, 0.15)]
if __name__ == "__main__":
    salida, n = sys.argv[1], int(sys.argv[2])
    os.makedirs(salida, exist_ok=True)
    funciones, pesos = zip(*GENERADORES)
    for k in range(n):
        f = funciones[rng.choice(len(funciones), p=np.array(pesos) / sum(pesos))]
        img = dibujar(f())
        if (np.asarray(img)[:, :, 3] > 0).sum() < 300:
            continue
        img.save(os.path.join(salida, f"20261013-{k:06d}_sintetico_{rng.integers(16**6):06x}.png"))
    print("generados:", len(os.listdir(salida)))

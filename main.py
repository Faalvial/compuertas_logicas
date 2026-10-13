"""App de recolección de compuertas lógicas dibujadas a mano.

Adaptada de https://github.com/PeterTXS09/letras_uni (letras U, N, I).
Cada dibujo se guarda como PNG en data/<CLASE>/. El canal alfa del PNG
contiene el trazo, igual que en el repo original.
"""
import base64
import hmac
import io
import os
import random
import re
import shutil
import time
import uuid
import zipfile

import numpy as np
from flask import Flask, abort, jsonify, render_template, request, send_file, send_from_directory
from PIL import Image

import prediccion

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DESCARTES_DIR = os.path.join(BASE_DIR, "descartados")
RUTA_PESOS = os.path.join(BASE_DIR, "pesos_cnn.npz")  # lo genera el notebook

CLASES = ["AND", "OR", "NOT", "NAND", "NOR", "XOR"]
META_POR_CLASE = 500
TAM_LIENZO = 256
MIN_PIXELES = 300  # menos tinta que esto se considera un lienzo vacío

COMPUERTAS = {
    "AND": {
        "svg": '<path d="M2 15H20M2 35H20M20 5H40A20 20 0 0 1 40 45H20Z M60 25H88"/>',
        "tip": "Parte trasera recta y frente redondeado, como una D.",
    },
    "OR": {
        "svg": '<path d="M2 15H22.5M2 35H22.5M18 5Q30 25 18 45Q45 45 62 25Q45 5 18 5Z M62 25H88"/>',
        "tip": "Parte trasera curva y frente en punta.",
    },
    "NOT": {
        "svg": '<path d="M2 25H20M20 8L52 25L20 42Z M60 25H88"/><circle cx="56" cy="25" r="4"/>',
        "tip": "Triángulo con un círculo en la punta.",
    },
    "NAND": {
        "svg": '<path d="M2 15H20M2 35H20M20 5H40A20 20 0 0 1 40 45H20Z M68 25H88"/><circle cx="64" cy="25" r="4"/>',
        "tip": "Igual que AND, con un círculo bien visible en la salida.",
    },
    "NOR": {
        "svg": '<path d="M2 15H22.5M2 35H22.5M18 5Q30 25 18 45Q45 45 62 25Q45 5 18 5Z M70 25H88"/><circle cx="66" cy="25" r="4"/>',
        "tip": "Igual que OR, con un círculo bien visible en la salida.",
    },
    "XOR": {
        "svg": '<path d="M2 15H20.5M2 35H20.5M14 5Q26 25 14 45 M24 5Q36 25 24 45Q51 45 68 25Q51 5 24 5Z M68 25H88"/>',
        "tip": "Igual que OR, con una segunda curva separada detrás.",
    },
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


@app.url_defaults
def version_estaticos(endpoint, valores):
    """Agrega ?v=<fecha de modificación> a los archivos de static/ para que el navegador
    no siga usando un style.css o .js viejo después de actualizar el sitio."""
    if endpoint == "static" and "filename" in valores:
        ruta = os.path.join(app.static_folder, valores["filename"])
        if os.path.exists(ruta):
            valores["v"] = int(os.path.getmtime(ruta))


# Se crean al importar el módulo (no solo en __main__) para que también
# existan cuando la app corre con gunicorn o en PythonAnywhere.
for _clase in CLASES:
    os.makedirs(os.path.join(DATA_DIR, _clase), exist_ok=True)

# Pesos de la CNN para la página principal (None hasta que se copie pesos_cnn.npz y se recargue la app).
PESOS = prediccion.cargar_pesos(RUTA_PESOS)


def archivos(clase):
    carpeta = os.path.join(DATA_DIR, clase)
    return sorted(f for f in os.listdir(carpeta) if f.endswith(".png"))


def contar():
    return {clase: len(archivos(clase)) for clase in CLASES}


def siguiente_clase(conteos):
    """Elige la clase con menos dibujos para que el dataset quede balanceado."""
    minimo = min(conteos.values())
    return random.choice([c for c in CLASES if conteos[c] == minimo])


def leer_imagen(datos, del_lienzo=True):
    """Convierte el dataURL que envía la página en una imagen PIL (None si no se puede).

    Las imágenes del lienzo deben medir 256x256; las subidas pueden tener otro tamaño."""
    try:
        img_b64 = (datos.get("imagen") or "").split(",", 1)[-1]
        img = Image.open(io.BytesIO(base64.b64decode(img_b64)))
        img.load()
    except Exception:
        return None
    if del_lienzo and img.size != (TAM_LIENZO, TAM_LIENZO):
        return None
    if max(img.size) > 2048:
        return None
    return img.convert("RGBA")


def limpiar_autor(texto):
    texto = re.sub(r"[^a-z0-9]+", "-", (texto or "").strip().lower()).strip("-")
    return texto[:20] or "anonimo"


@app.route("/recolectar")
def main():
    conteos = contar()
    return render_template(
        "index.html",
        clases=CLASES,
        compuertas=COMPUERTAS,
        conteos=conteos,
        clase=siguiente_clase(conteos),
        meta=META_POR_CLASE,
        tam=TAM_LIENZO,
    )


@app.route("/")
@app.route("/probar")
def probar():
    """Dibuja (o sube una imagen) y la red adivina la compuerta."""
    return render_template("probar.html", tam=TAM_LIENZO, compuertas=COMPUERTAS)


@app.route("/predecir", methods=["POST"])
def predecir():
    if PESOS is None:
        return jsonify(ok=False, error="Todavía no hay un modelo entrenado"), 503
    datos = request.get_json(silent=True) or {}
    subida = bool(datos.get("subida"))
    img = leer_imagen(datos, del_lienzo=not subida)
    if img is None:
        return jsonify(ok=False, error="La imagen no se pudo leer."), 400
    if subida:
        # Una foto o captura se convierte primero en un dibujo como los del lienzo.
        img = prediccion.desde_imagen(img)
        if img is None:
            return jsonify(ok=False, error="No se encontró un dibujo en la imagen"), 400
    entrada = prediccion.preprocesar(img)
    if entrada is None:
        return jsonify(ok=False, error="Dibuja una compuerta"), 400
    probabilidades = prediccion.predecir(entrada, PESOS)
    respuesta = {"ok": True, "clases": CLASES, "probabilidades": [round(float(p), 4) for p in probabilidades]}
    if subida:
        buf = io.BytesIO()
        img.save(buf, "PNG")
        respuesta["dibujo"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    return jsonify(respuesta)


@app.route("/upload", methods=["POST"])
def upload():
    datos = request.get_json(silent=True) or {}
    clase = datos.get("clase")
    if clase not in CLASES:
        return jsonify(ok=False, error="Clase desconocida."), 400

    img = leer_imagen(datos)
    if img is None:
        return jsonify(ok=False, error="La imagen no se pudo leer."), 400
    if (np.array(img)[:, :, 3] > 0).sum() < MIN_PIXELES:
        return jsonify(ok=False, error="El dibujo está vacío o es muy pequeño."), 400

    nombre = "{}_{}_{}.png".format(
        time.strftime("%Y%m%d-%H%M%S"), limpiar_autor(datos.get("autor")), uuid.uuid4().hex[:6]
    )
    img.save(os.path.join(DATA_DIR, clase, nombre))

    conteos = contar()
    return jsonify(ok=True, guardado=clase, siguiente=siguiente_clase(conteos), conteos=conteos)


@app.route("/stats")
def stats():
    conteos = contar()
    return jsonify(conteos=conteos, total=sum(conteos.values()), meta_por_clase=META_POR_CLASE)


@app.route("/prepare")
def prepare_dataset():
    """Arma X.npy (imágenes tam x tam, canal alfa) e y.npy (etiquetas), como el repo original."""
    tam = max(16, min(TAM_LIENZO, request.args.get("tam", 64, type=int)))
    images, digits = [], []
    for clase in CLASES:
        for nombre in archivos(clase):
            with Image.open(os.path.join(DATA_DIR, clase, nombre)) as img:
                alfa = img.convert("RGBA").getchannel("A")
                alfa = alfa.resize((tam, tam), Image.Resampling.LANCZOS)
            images.append(np.array(alfa, dtype=np.uint8))
            digits.append(clase)
    if not images:
        return jsonify(ok=False, error="Todavía no hay dibujos."), 400
    np.save(os.path.join(BASE_DIR, "X.npy"), np.stack(images))
    np.save(os.path.join(BASE_DIR, "y.npy"), np.array(digits))
    return jsonify(ok=True, n=len(digits), tam=tam, conteos=contar())


@app.route("/X.npy")
def download_X():
    return send_file(os.path.join(BASE_DIR, "X.npy"), as_attachment=True)


@app.route("/y.npy")
def download_y():
    return send_file(os.path.join(BASE_DIR, "y.npy"), as_attachment=True)


@app.route("/dataset.zip")
def download_zip():
    """Todos los PNG originales (256x256), en carpetas por clase."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for clase in CLASES:
            for nombre in archivos(clase):
                zf.write(os.path.join(DATA_DIR, clase, nombre), "{}/{}".format(clase, nombre))
    buffer.seek(0)
    nombre_zip = "compuertas_{}.zip".format(time.strftime("%Y%m%d-%H%M"))
    return send_file(buffer, mimetype="application/zip", as_attachment=True, download_name=nombre_zip)


@app.route("/img/<clase>/<nombre>")
def imagen(clase, nombre):
    if clase not in CLASES:
        abort(404)
    return send_from_directory(os.path.join(DATA_DIR, clase), nombre)


@app.route("/revisar")
def revisar():
    clase = request.args.get("clase", CLASES[0])
    if clase not in CLASES:
        abort(404)
    pagina = max(1, request.args.get("pagina", 1, type=int))
    por_pagina = 120
    todos = archivos(clase)[::-1]  # los más recientes primero
    total_paginas = max(1, -(-len(todos) // por_pagina))
    return render_template(
        "revisar.html",
        clases=CLASES,
        clase=clase,
        conteos=contar(),
        imagenes=todos[(pagina - 1) * por_pagina : pagina * por_pagina],
        pagina=pagina,
        total_paginas=total_paginas,
        borrado_activo=bool(os.environ.get("CLAVE_ADMIN")),
    )


@app.route("/descartar", methods=["POST"])
def descartar():
    """Mueve un dibujo malo a descartados/ (no se borra, se puede recuperar)."""
    clave_admin = os.environ.get("CLAVE_ADMIN")
    if not clave_admin:
        return jsonify(ok=False, error="El descarte está desactivado: falta CLAVE_ADMIN."), 403
    datos = request.get_json(silent=True) or {}
    if not hmac.compare_digest(str(datos.get("clave", "")), clave_admin):
        return jsonify(ok=False, error="Clave incorrecta."), 403
    clase, nombre = datos.get("clase"), str(datos.get("nombre", ""))
    if clase not in CLASES or not re.fullmatch(r"[\w.-]+\.png", nombre):
        return jsonify(ok=False, error="Archivo inválido."), 400
    origen = os.path.join(DATA_DIR, clase, nombre)
    if not os.path.isfile(origen):
        return jsonify(ok=False, error="El archivo ya no existe."), 404
    destino = os.path.join(DESCARTES_DIR, clase)
    os.makedirs(destino, exist_ok=True)
    shutil.move(origen, os.path.join(destino, nombre))
    return jsonify(ok=True, conteos=contar())


if __name__ == "__main__":
    app.run(debug=True)

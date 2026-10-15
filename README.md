# Compuertas lógicas dibujadas a mano

PC2 de Computación Gráfica (UNI). Clasificación de 6 compuertas lógicas dibujadas a mano con una red neuronal: **AND, OR, NOT, NAND, NOR, XOR**, más una clase **OTRO** para los dibujos que no son ninguna de ellas.

Adaptado de [PeterTXS09/letras_uni](https://github.com/PeterTXS09/letras_uni), que recolectaba las letras U, N, I.

## Qué cambió respecto al repo original

| Original | Esta versión |
|---|---|
| Clases U, N, I | Compuertas AND, OR, NOT, NAND, NOR, XOR |
| Clase elegida al azar | Se pide la compuerta con menos dibujos, así el dataset queda balanceado |
| Sin referencia | Imagen de referencia y consejo para cada compuerta |
| Solo mouse | Mouse, dedo y lápiz (se puede dibujar desde el celular) |
| Recarga la página en cada envío | Envío sin recargar, con botón Deshacer y atajos (Enter envía, Esc borra) |
| Guarda cualquier envío | Rechaza lienzos vacíos, clases desconocidas e imágenes inválidas |
| Rutas relativas al directorio actual | Rutas absolutas: funciona igual con gunicorn y en PythonAnywhere |
| `/prepare` a 200×200 | `/prepare?tam=64` reduce al tamaño pedido |
| | Descarga de todos los PNG en `/dataset.zip` |
| | Página `/revisar` para ver los dibujos y descartar los malos |
| | Contador de progreso por compuerta (meta: 500) |
| | Página principal “Adivina tu dibujo”, que predice la compuerta con la CNN entrenada al pulsar Predecir |

## Rutas

| Ruta | Qué hace |
|---|---|
| `/` | “Adivina tu dibujo”: dibujas o subes una imagen y la red dice qué compuerta es (también en `/probar`) |
| `/recolectar` | Página para dibujar y guardar dibujos del dataset |
| `/predecir` (POST) | Devuelve la probabilidad de cada compuerta para un dibujo |
| `/upload` (POST) | Guarda un dibujo en `data/<CLASE>/` |
| `/stats` | Conteo por clase en JSON |
| `/revisar?clase=AND` | Galería de dibujos de una clase |
| `/descartar` (POST) | Mueve un dibujo a `descartados/` (necesita `CLAVE_ADMIN`) |
| `/dataset.zip` | Descarga todos los PNG (256×256) en carpetas por clase |
| `/prepare?tam=64` | Genera `X.npy` y `y.npy` a 64×64, como el repo original |
| `/X.npy`, `/y.npy` | Descarga esos archivos |

Cada dibujo se guarda como `data/<CLASE>/<fecha>_<autor>_<id>.png`. El trazo está en el canal alfa, igual que en el original.

## Correr en local

```bash
pip install -r requirements.txt
python main.py
```

Abrir http://127.0.0.1:5000. Para activar el descarte de dibujos en `/revisar`, definir antes la variable `CLAVE_ADMIN`:

```bash
# Linux / Mac
CLAVE_ADMIN=mi-clave python main.py
```

```powershell
# Windows (PowerShell)
$env:CLAVE_ADMIN = "mi-clave"
python main.py
```

## Desplegar gratis en PythonAnywhere

PythonAnywhere conserva los archivos guardados en disco, así que los dibujos no se pierden al reiniciar (en Railway o Render se borrarían). El plan gratuito da 512 MB, y cada dibujo pesa unos 3 KB.

1. Crear una cuenta **Beginner** (gratis) en https://www.pythonanywhere.com. El nombre de usuario será parte de la dirección: `https://<usuario>.pythonanywhere.com`.
2. En la pestaña **Consoles**, abrir una consola **Bash** y ejecutar:
   ```bash
   git clone https://github.com/<usuario-github>/<repo>.git
   cd <repo>
   python3.11 -m pip install --user -r requirements.txt
   ```
3. En la pestaña **Web**, pulsar **Add a new web app** → **Manual configuration** → **Python 3.11**.
4. En esa misma pestaña, en **Code**, poner **Source code**: `/home/<usuario>/<repo>`.
5. Abrir el **WSGI configuration file** (enlace en la misma pestaña), borrar su contenido y pegar:
   ```python
   import os
   import sys

   path = "/home/<usuario>/<repo>"
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ["CLAVE_ADMIN"] = "elijan-una-clave"

   from main import app as application
   ```
6. (Opcional, más rápido) En **Static files**, agregar URL `/static/` con directorio `/home/<usuario>/<repo>/static`.
7. Pulsar **Reload** y abrir `https://<usuario>.pythonanywhere.com`.

Para actualizar el código: en la consola, `cd <repo> && git pull`, y luego **Reload** en la pestaña Web. Los dibujos de `data/` no se tocan porque están en `.gitignore`. Si la carpeta no se creó con `git clone`, subir los archivos cambiados desde la pestaña **Files** (sin borrar `data/`) y pulsar **Reload**.

La app gratuita se apaga a los 3 meses si nadie pulsa **Run until 3 months from today** en la pestaña Web.

## Entrenamiento (notebook)

`entrenamiento_compuertas.ipynb` hace lo que pide la tarea: carga, preprocesamiento, exploración, división en entrenamiento, validación y prueba, una CNN, métricas (accuracy, precisión, recall, F1, matriz de confusión), los dibujos mal clasificados, la exportación de los pesos para la app y las conclusiones.

Para correrlo en Google Colab:
1. Abrir https://colab.research.google.com y subir el notebook (Archivo → Subir notebook).
2. Entorno de ejecución → Cambiar tipo de entorno → GPU (T4). Sin GPU también funciona, pero tarda más.
3. Entorno de ejecución → Ejecutar todo. El notebook descarga solo el `dataset.zip` de este repositorio.
4. Completar los números de las conclusiones y guardar el notebook ejecutado en el repositorio.

## Adivina tu dibujo (página principal)

Al pulsar **Predecir**, la página envía el dibujo a `/predecir` y el servidor lo pasa por la CNN entrenada. Junto a cada porcentaje se muestra el símbolo de la compuerta. La predicción se pide con el botón y no al levantar el lápiz, para no mostrar una respuesta para un dibujo a medio hacer. Si la red elige OTRO, la página muestra «No parece una compuerta».

También se puede **subir una imagen** (una foto de una compuerta dibujada en papel, una captura, etc.). El servidor separa el trazo del fondo, descarta lo que está lejos de la compuerta (un título, una marca de agua), lo centra en un lienzo de 256×256 y ajusta el grosor del trazo a unos 8 píxeles, para que se parezca a los dibujos con los que se entrenó la red (`desde_imagen` en `prediccion.py`). Luego la predice igual que un dibujo y la muestra en el lienzo.

El servidor no usa TensorFlow, porque ocupa más de 1 GB y el plan gratuito de PythonAnywhere da 512 MB. En su lugar, `prediccion.py` repite con numpy las capas de la CNN (convolución, max pooling y densas) usando los pesos que guarda el notebook, y aplica el mismo preprocesamiento del notebook (recorte a la tinta, margen y redimensionado a 64×64). Da las mismas probabilidades que Keras.

El repositorio ya trae `pesos_cnn.npz` con la CNN entrenada con el dataset final. En PythonAnywhere basta `cd <repo> && git pull` en la consola y **Reload** en la pestaña Web.

Si se vuelve a entrenar:
1. Correr el notebook completo. La sección de exportación guarda `pesos_cnn.npz` (en Colab se descarga solo).
2. Reemplazar `pesos_cnn.npz` en el repositorio, junto a `main.py`, y repetir `git pull` y **Reload**.

Mientras no haya modelo, la página muestra “Todavía no hay un modelo entrenado”.

## Datos

`dataset.zip` tiene los 3500 dibujos usados para entrenar, 500 por clase. Los 3000 de compuertas se descargaron de la app el 13 de octubre de 2026. Los 500 de OTRO (letras, números, formas, flechas y garabatos) se generaron con `python generar_otro.py OTRO 500`, que imita el trazo del lienzo; su autor figura como `sintetico`. Cada archivo se llama `<CLASE>/<fecha>_<autor>_<id>.png`.

Aporte de cada persona a las 3000 compuertas:

| Persona | Dibujos | Aporte |
|---|---|---|
| faalvial | 1133 | 37.8% |
| christmas | 873 | 29.1% |
| dodo | 685 | 22.8% |
| omar | 297 | 9.9% |
| sin nombre | 12 | 0.4% |

Antes de entrenar se revisaron los dibujos con modelos de validación cruzada: 9 estaban mal hechos (incompletos, con la forma de otra compuerta o con un punto suelto) y se reemplazaron por dibujos nuevos.

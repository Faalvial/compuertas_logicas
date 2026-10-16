# Compuertas lógicas dibujadas a mano

PC2 de Computación Gráfica (UNI). Clasificación de 6 compuertas lógicas dibujadas a mano con una red neuronal: **AND, OR, NOT, NAND, NOR, XOR**.

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

`cnn_compuertas_curso.ipynb` hace todo el proceso con lo visto en clase: carga, preprocesamiento, exploración, aumento de datos (giros, desplazamientos, zoom y volteo vertical como capas de Keras), tres modelos (un MLP base, una CNN como la de las diapositivas y una CNN con Global Average Pooling), métricas (accuracy, precisión, recall, F1, matriz de confusión), análisis de las parejas difíciles (AND/NAND, OR/NOR, OR/XOR, AND/OR) y mapas de activación de clase (CAM).

Para correrlo en Google Colab:
1. Abrir https://colab.research.google.com y subir el notebook (Archivo → Subir notebook).
2. Entorno de ejecución → Ejecutar todo. El notebook descarga solo el `dataset.zip` de este repositorio. Funciona con o sin GPU; en CPU cada época de las CNN toma unos segundos.

El notebook del repositorio ya está ejecutado con el dataset final, así que los resultados se ven sin correrlo.

### Resultados

10 épocas, 450 dibujos de prueba:

| Modelo | Parámetros | Accuracy |
|---|---|---|
| MLP (base) | 525,190 | 97.8% (10 errores) |
| CNN | 78,598 | 98.4% (7 errores) |
| CNN con Global Average Pooling | 23,686 | 83.6% (74 errores) |

Sin aumento de datos, la CNN da 98.9% y la CNN con GAP 85.8%. Las conclusiones completas, con la comparación y lo que muestran los mapas CAM, están al final del notebook.

## Adivina tu dibujo (página principal)

Al pulsar **Predecir**, la página envía el dibujo a `/predecir` y el servidor lo pasa por la CNN entrenada. Junto a cada porcentaje se muestra el símbolo de la compuerta. La predicción se pide con el botón y no al levantar el lápiz, para no mostrar una respuesta para un dibujo a medio hacer.

También se puede **subir una imagen** (una foto de una compuerta dibujada en papel, una captura, etc.). El servidor separa el trazo del fondo, descarta lo que está lejos de la compuerta (un título, una marca de agua), lo centra en un lienzo de 256×256 y ajusta el grosor del trazo a unos 8 píxeles, para que se parezca a los dibujos con los que se entrenó la red (`desde_imagen` en `prediccion.py`). Luego la predice igual que un dibujo y la muestra en el lienzo.

El servidor no usa TensorFlow, porque ocupa más de 1 GB y el plan gratuito de PythonAnywhere da 512 MB. En su lugar, `prediccion.py` repite con numpy las capas de la CNN (convolución, max pooling y densas) usando los pesos que guarda el notebook, y aplica el mismo preprocesamiento del notebook (recorte a la tinta, margen y redimensionado a 64×64). Da las mismas probabilidades que Keras.

La página usa `pesos_cnn_curso.npz`, los pesos de la CNN que guarda `cnn_compuertas_curso.ipynb`. Como la red solo conoce las 6 compuertas, ante un dibujo que no es ninguna igual elige una de ellas. En PythonAnywhere basta `cd <repo> && git pull` en la consola y **Reload** en la pestaña Web.

Si se vuelve a entrenar:
1. Correr el notebook completo. La sección de exportación guarda `pesos_cnn_curso.npz` (en Colab se descarga solo).
2. Reemplazar `pesos_cnn_curso.npz` en el repositorio, junto a `main.py`, y repetir `git pull` y **Reload**.

Mientras no haya modelo, la página muestra “Todavía no hay un modelo entrenado”.

## Datos

`dataset.zip` tiene los 3000 dibujos de compuertas usados para entrenar, 500 por clase, descargados de la app el 13 de octubre de 2026. Cada archivo se llama `<CLASE>/<fecha>_<autor>_<id>.png`. El zip trae además una carpeta `OTRO` con 500 dibujos sintéticos de una versión anterior con 7 clases; el notebook la ignora.

Aporte de cada persona a las 3000 compuertas:

| Persona | Dibujos | Aporte |
|---|---|---|
| faalvial | 1133 | 37.8% |
| christmas | 873 | 29.1% |
| dodo | 685 | 22.8% |
| omar | 297 | 9.9% |
| sin nombre | 12 | 0.4% |

Antes de entrenar se revisaron los dibujos con modelos de validación cruzada: 9 estaban mal hechos (incompletos, con la forma de otra compuerta o con un punto suelto) y se reemplazaron por dibujos nuevos.

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

## Rutas

| Ruta | Qué hace |
|---|---|
| `/` | Página para dibujar |
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

Para actualizar el código: en la consola, `cd <repo> && git pull`, y luego **Reload** en la pestaña Web. Los dibujos de `data/` no se tocan porque están en `.gitignore`.

La app gratuita se apaga a los 3 meses si nadie pulsa **Run until 3 months from today** en la pestaña Web.

## Entrenamiento (notebook)

`entrenamiento_compuertas.ipynb` hace todo el proceso: carga, preprocesamiento, exploración, un MLP base, la CNN, métricas (accuracy, precisión, recall, F1, matriz de confusión), análisis de las parejas difíciles (AND/NAND, OR/NOR, OR/XOR), el experimento de resolución (16, 28 y 64 píxeles) y la prueba con personas que no se usaron para entrenar.

Para correrlo en Google Colab:
1. Abrir https://colab.research.google.com y subir el notebook (Archivo → Subir notebook).
2. En la primera celda de código, poner la dirección de la app en `URL_DATASET` (por ejemplo `https://<usuario>.pythonanywhere.com/dataset.zip`), o dejarla vacía y subir el `.zip` cuando lo pida.
3. Entorno de ejecución → Ejecutar todo. Con GPU (Entorno de ejecución → Cambiar tipo de entorno) es más rápido, pero no es obligatorio.

## Recolección

- Meta: 500 dibujos por compuerta, 3000 en total (unos 750 por integrante).
- Escribir el nombre en la casilla “Tu nombre” para saber cuánto aportó cada uno.
- Al terminar, descargar `/dataset.zip` y usarlo en el notebook de entrenamiento.

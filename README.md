# Compuertas lógicas dibujadas a mano

**PC2 de Computación Gráfica — Universidad Nacional de Ingeniería (UNI).** Aplicación web para **recolectar, revisar y clasificar dibujos de compuertas lógicas** mediante una red neuronal convolucional (CNN). Reconoce seis clases: **AND, OR, NOT, NAND, NOR y XOR**. Permite dibujar directamente en un lienzo o subir una imagen para obtener la predicción y la probabilidad asignada a cada compuerta.

Proyecto adaptado de [PeterTXS09/letras_uni](https://github.com/PeterTXS09/letras_uni), originalmente desarrollado para recolectar dibujos de las letras U, N e I.

**Aplicación publicada:** https://faalvial.pythonanywhere.com/  
**Repositorio:** https://github.com/Faalvial/compuertas_logicas

> **Estado actual:** la página utiliza `pesos_cnn_curso.npz`, entrenado para **6 clases**. Aunque `dataset.zip` contiene 500 dibujos adicionales en la carpeta `OTRO`, **la versión actual no está entrenada para rechazar dibujos ajenos a las seis compuertas**: siempre asigna alguna de ellas. El notebook y los pesos del antiguo modelo de 7 clases ya no forman parte de este commit.

## Qué cambió respecto al repo original

| Original (`letras_uni`) | Esta versión (`compuertas_logicas`) |
|---|---|
| Recolección de las letras U, N e I | Recolección y clasificación de seis compuertas: AND, OR, NOT, NAND, NOR y XOR. |
| Selección aleatoria de la clase solicitada | Se propone una de las clases con menos dibujos para mantener equilibrada la recolección. |
| Sin referencia visual específica | Referencia SVG, indicaciones de forma y consejos para dibujar cada compuerta. |
| Dibujo mediante mouse | Lienzo compatible con mouse, pantalla táctil y lápiz digital mediante *Pointer Events*. |
| Envíos con recarga de página | Guardado asíncrono sin recargar, con **Deshacer**, **Borrar** y atajos de teclado. |
| Validación básica de los envíos | Validación de clase, imagen, dimensiones y cantidad mínima de píxeles dibujados. |
| Rutas dependientes del directorio de ejecución | Rutas construidas desde la ubicación de `main.py`, compatibles con ejecución local y WSGI. |
| Preparación del dataset a una resolución fija | Endpoint `/prepare?tam=64` para generar arreglos NumPy con tamaño configurable. |
| Sin herramientas equivalentes de revisión y seguimiento | Estadísticas por clase, galería paginada, descarte protegido por clave y descarga de dibujos. |
| Sin clasificador de compuertas integrado | Página **«Adivina tu dibujo»** que ejecuta una CNN entrenada y muestra probabilidades. |
| Sin carga de fotografías para inferencia | Carga de imágenes con conversión a trazos, limpieza heurística, centrado y normalización. |
| Sin comparativa de modelos para este problema | Notebook con **MLP, CNN y CNN + Global Average Pooling**, métricas, aumento de datos y mapas CAM. |

La interfaz se implementa con **HTML, CSS y JavaScript**, el servidor con **Flask**, el procesamiento de imágenes con **Pillow** y la inferencia en producción con **NumPy**. **Keras** se utiliza en el notebook para entrenar los modelos, pero no es necesario instalarlo para ejecutar la web.

## Rutas

| Ruta | Qué hace |
|---|---|
| `/` | Página principal **«Adivina tu dibujo»**: dibujar o subir una imagen y solicitar una clasificación. |
| `/probar` | Acceso alternativo a la misma página de predicción. |
| `/recolectar` | Formulario para dibujar y guardar ejemplos de las seis compuertas. |
| `/predecir` (**POST**) | Recibe una imagen en JSON y devuelve las seis clases con sus probabilidades; admite `subida: true` para imágenes cargadas. |
| `/upload` (**POST**) | Valida y guarda un dibujo PNG dentro de `data/<CLASE>/`. |
| `/stats` | Devuelve el número de dibujos por clase, el total y la meta por clase en JSON. |
| `/revisar?clase=AND` | Galería para inspeccionar dibujos; muestra hasta 120 imágenes por página. |
| `/img/<clase>/<nombre>` | Sirve una imagen guardada de una de las seis clases. |
| `/descartar` (**POST**) | Mueve un dibujo de `data/` a `descartados/`; requiere la variable `CLAVE_ADMIN` y la clave correcta. |
| `/dataset.zip` | Genera una descarga de los **dibujos existentes en `data/`** para las seis clases. |
| `/prepare?tam=64` | Genera `X.npy` e `y.npy` con las imágenes almacenadas en `data/`; acepta tamaños entre 16 y 256 píxeles. |
| `/X.npy`, `/y.npy` | Descarga los arreglos generados previamente con `/prepare`. |

Los dibujos recolectados se guardan como `data/<CLASE>/<fecha>_<autor>_<id>.png`, con lienzos de **256 × 256 píxeles** y el trazo en el **canal alfa** (fondo transparente). El servidor exige al menos **300 píxeles con alfa distinto de cero** para aceptar un dibujo y limita las solicitudes a **2 MB**.

**Importante:** el endpoint `/dataset.zip` genera un ZIP a partir de los archivos presentes en `data/`; **no es lo mismo** que el archivo histórico `dataset.zip` incluido en el repositorio. Una instalación nueva crea `data/` vacía, por lo que sus contadores comienzan en cero hasta que se recolecten o se importen dibujos. La clase `OTRO` no participa en los endpoints de recolección o preparación actuales.

## Correr en local

Se recomienda **Python 3.11** y disponer de Git para clonar el proyecto.

```bash
git clone https://github.com/Faalvial/compuertas_logicas.git
cd compuertas_logicas
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Instalar las dependencias y arrancar el servidor:

```bash
python -m pip install -r requirements.txt
python main.py
```

Abrir **http://127.0.0.1:5000**. Las dependencias de la aplicación son **Flask 3.1.3**, **Gunicorn 23.0.0**, **NumPy 2.2.6** y **Pillow 12.0.0**. Gunicorn se utiliza para despliegues compatibles; no es necesario para ejecutar `python main.py`.

El repositorio incluye los pesos `pesos_cnn_curso.npz`, por lo que la predicción puede funcionar sin volver a entrenar. Para disponer también de los **3.000 dibujos históricos de compuertas** en la galería y los contadores locales, extraer el ZIP suministrado:

```bash
python -c "import zipfile; zipfile.ZipFile('dataset.zip').extractall('data')"
```

Esta extracción también crea `data/OTRO`, pero la aplicación ignora esa carpeta. No hace falta realizar este paso para usar la predicción, ya que el modelo entrenado se encuentra en el archivo `.npz`.

Para activar el botón **Descartar** en `/revisar`, definir `CLAVE_ADMIN` antes de iniciar la aplicación:

```bash
# Linux / macOS
CLAVE_ADMIN=una-clave-segura python main.py
```

```powershell
# Windows (PowerShell)
$env:CLAVE_ADMIN = "una-clave-segura"
python main.py
```

Los archivos de `data/` y `descartados/`, así como `X.npy` e `y.npy`, están excluidos del control de versiones mediante `.gitignore`.

## Desplegar gratis en PythonAnywhere

El proyecto puede publicarse como aplicación **Flask** mediante la configuración **WSGI** de PythonAnywhere. A diferencia de algunas plataformas con disco efímero, PythonAnywhere permite conservar los PNG en el directorio de la cuenta. Los límites y condiciones del plan gratuito deben revisarse en la documentación vigente del servicio.

1. Crear una cuenta en [PythonAnywhere](https://www.pythonanywhere.com/) y abrir una consola **Bash** en **Consoles**.
2. Clonar el repositorio e instalar las dependencias con una versión de Python que coincida con la elegida para la aplicación web:

   ```bash
   git clone https://github.com/Faalvial/compuertas_logicas.git
   cd compuertas_logicas
   python3.11 -m pip install --user -r requirements.txt
   ```

3. En **Web**, crear una aplicación mediante **Manual configuration** y seleccionar **Python 3.11**, si está disponible en la cuenta.
4. En **Code**, configurar **Source code** como `/home/<usuario>/compuertas_logicas`.
5. Editar el **WSGI configuration file** de la aplicación para importar Flask desde `main.py`:

   ```python
   import os
   import sys

   path = "/home/<usuario>/compuertas_logicas"
   if path not in sys.path:
       sys.path.insert(0, path)

   # Opcional: configurarla fuera del repositorio público.
   os.environ["CLAVE_ADMIN"] = "reemplazar-con-una-clave-segura"

   from main import app as application
   ```

6. Opcionalmente, en **Static files** asociar `/static/` con `/home/<usuario>/compuertas_logicas/static`.
7. Pulsar **Reload** y abrir la URL asignada por PythonAnywhere.

Para incorporar cambios subidos a GitHub:

```bash
cd ~/compuertas_logicas
git pull origin main
```

Después, pulsar **Reload** en la pestaña **Web**. Como `data/` se encuentra en `.gitignore`, una actualización normal del código no reemplaza los dibujos guardados. Antes de operaciones de mantenimiento es recomendable hacer una copia de `data/` y `descartados/`.

**Nota:** `Procfile` incluye `web: gunicorn -b 0.0.0.0:$PORT main:app` para plataformas que utilizan Gunicorn y una variable `PORT`; **PythonAnywhere usa el archivo WSGI**, no ese `Procfile`. Si se despliega en una plataforma con almacenamiento efímero, los PNG requieren un volumen persistente u otro sistema de almacenamiento. No publiques una clave real en el repositorio.

## Entrenamiento (notebook)

El notebook vigente es **`cnn_compuertas_curso.ipynb`**. Utiliza las **3.000 imágenes de las seis compuertas** (500 por clase) y compara tres arquitecturas:

- **MLP:** imagen de 64 × 64 aplanada, capa densa de 128 neuronas con ReLU y salida *softmax* de seis clases.
- **CNN:** tres convoluciones de **16, 32 y 64 filtros de 3 × 3**, dos capas de *max pooling*, aplanamiento y salida *softmax* de seis clases. Es el modelo exportado para la aplicación web.
- **CNN + GAP:** conserva las convoluciones de la CNN, pero sustituye `Flatten` por **Global Average Pooling**, lo que reduce parámetros y permite visualizar **Class Activation Maps (CAM)**.

El notebook implementa carga de datos, recorte al trazo, centrado con un margen del 8 %, redimensionado a **64 × 64**, normalización a `[0, 1]`, exploración, entrenamiento, métricas, matrices de confusión, análisis de errores y visualización CAM.

La división estratificada utiliza **2.100 imágenes para entrenamiento (70 %)**, **450 para validación (15 %)** y **450 para prueba (15 %)**, con semilla `42`. Los tres modelos se entrenan durante **10 épocas**, con lotes de **64** y optimizador **Adam**. Las dos CNN usan por defecto aumento de datos: rotación de hasta ±15°, desplazamiento y zoom de hasta ±10 %, y volteo vertical. El MLP no usa aumento.

Para ejecutarlo en **Google Colab**:

1. Abrir [Google Colab](https://colab.research.google.com/) y cargar `cnn_compuertas_curso.ipynb`.
2. Seleccionar **Entorno de ejecución → Ejecutar todo**. Si `dataset.zip` no está presente, el notebook intenta descargarlo desde el repositorio.
3. Revisar las métricas y visualizaciones. El notebook contiene salidas guardadas de su ejecución; no es obligatorio ejecutarlo solo para consultar los resultados.

Se puede cambiar `USAR_AUMENTO = False` para repetir el entrenamiento sin aumento de datos. La ejecución de entrenamiento requiere **Keras, scikit-learn y Matplotlib**, además de las bibliotecas usadas para procesar imágenes; estas herramientas no se incluyen en `requirements.txt` porque ese archivo está orientado a ejecutar la web.

### Resultados

Resultados registrados en `cnn_compuertas_curso.ipynb` para el **mismo conjunto de 450 imágenes de prueba**, con 10 épocas y aumento de datos activado en ambas CNN:

| Modelo | Accuracy | F1 macro | Errores | Parámetros |
|---|---:|---:|---:|---:|
| MLP | **97,8 %** | 0,978 | 10 | 525.190 |
| **CNN (modelo de la web)** | **98,4 %** | **0,984** | **7** | **78.598** |
| CNN + GAP | **83,6 %** | 0,831 | 74 | 23.686 |

La CNN acertó **443 de 450** dibujos de prueba. Sus siete errores se concentraron en compuertas con formas similares, especialmente en **NAND → AND** cuando el círculo de negación era pequeño o quedaba unido al cuerpo. La versión con GAP tiene aproximadamente **3,3 veces menos parámetros** que la CNN, pero en esta ejecución de 10 épocas obtuvo una precisión inferior.

El notebook también documenta una comparación de las CNN **con y sin aumento de datos**:

| Modelo | Con aumento | Sin aumento |
|---|---:|---:|
| CNN | 98,4 % | 98,9 % |
| CNN + GAP | 83,6 % | 85,8 % |

Esos resultados **no demuestran que el aumento sea perjudicial**: las diferencias corresponden a pocas imágenes y el conjunto de prueba contiene dibujos limpios de las mismas personas que aportaron al entrenamiento. El aumento busca mejorar la robustez ante variaciones de orientación, posición y tamaño; para evaluar generalización fuera del grupo se necesitaría una prueba independiente con nuevos autores e imágenes reales.

Los **mapas CAM** de la CNN con GAP permiten examinar qué regiones contribuyen a una clasificación. En el análisis del notebook aparecen detalles importantes como la curvatura trasera, el arco adicional de XOR y la burbuja de negación.

## Adivina tu dibujo (página principal)

La ruta `/` abre la interfaz de clasificación. La persona puede dibujar en un lienzo de **256 × 256 píxeles** con mouse, dedo o lápiz digital, y pulsar **Predecir** cuando termine; también puede pulsar **Subir imagen** para seleccionar una fotografía o captura. La interfaz incluye **Deshacer**, **Borrar**, la compuerta más probable y las probabilidades de las seis clases acompañadas de sus símbolos SVG.

El proceso de predicción es el siguiente:

1. **Captura:** JavaScript convierte el lienzo a PNG; las imágenes subidas se reducen, si es necesario, a un máximo de 512 píxeles por lado antes del envío.
2. **Conversión de una imagen subida:** `prediccion.desde_imagen()` separa tinta y fondo mediante escala de grises y umbral de Otsu; aplica filtrado, intenta retirar manchas o texto alejados, centra el dibujo y adapta su trazo a un lienzo transparente de 256 × 256. Esta limpieza es heurística y puede fallar en fotografías complejas.
3. **Preprocesamiento:** `prediccion.preprocesar()` extrae el canal alfa, recorta al contenido, añade un margen del 8 %, redimensiona a **64 × 64** y normaliza los píxeles entre 0 y 1.
4. **Inferencia:** `prediccion.predecir()` aplica las convoluciones, funciones ReLU, operaciones *max pooling*, aplanamiento, capa densa y *softmax* de la CNN entrenada.
5. **Respuesta:** Flask devuelve las probabilidades en JSON y la interfaz las presenta ordenadas de mayor a menor. Para una imagen subida también devuelve el dibujo procesado para mostrarlo en el lienzo.

**Inferencia ligera:** el entrenamiento se realiza en Keras, pero el servidor web **no necesita TensorFlow**. `prediccion.py` reproduce las operaciones de inferencia con NumPy y carga los **78.598 parámetros** almacenados en `pesos_cnn_curso.npz`. Así se reducen las dependencias necesarias para el alojamiento web.

**Limitación importante:** la salida contiene exclusivamente **AND, OR, NOT, NAND, NOR y XOR**. Si el usuario dibuja una letra, un número u otra figura, el clasificador puede asignarle una compuerta con una probabilidad alta; **no cuenta actualmente con detección confiable de «OTRO»**. Aunque queda código heredado para interpretar pesos de otra arquitectura, **`pesos_cnn.npz` y `entrenamiento_compuertas.ipynb` se eliminaron del repositorio** y no pueden activarse simplemente cambiando la ruta.

Si se vuelve a entrenar la CNN actual:

1. Ejecutar el notebook `cnn_compuertas_curso.ipynb` hasta la sección **«Exportar los pesos de la CNN»**.
2. Guardar el nuevo `pesos_cnn_curso.npz` junto a `main.py` y confirmar que corresponde a la misma arquitectura de seis clases.
3. Subir los cambios al repositorio y actualizar/reiniciar la aplicación alojada.

Si falta el archivo de pesos al iniciar el servidor, `/predecir` devuelve el mensaje **«Todavía no hay un modelo entrenado»** con estado HTTP `503`.

## Datos

El archivo **`dataset.zip` incluido en el repositorio contiene 3.500 PNG de 256 × 256 píxeles**, organizados por carpeta:

| Clase | Dibujos | Uso actual |
|---|---:|---|
| AND | 500 | Entrenamiento y evaluación |
| OR | 500 | Entrenamiento y evaluación |
| NOT | 500 | Entrenamiento y evaluación |
| NAND | 500 | Entrenamiento y evaluación |
| NOR | 500 | Entrenamiento y evaluación |
| XOR | 500 | Entrenamiento y evaluación |
| OTRO | 500 | Conservados en el archivo; **no usados por la CNN actual** |
| **Total** | **3.500** | **3.000 usados para las seis clases** |

Los 3.000 ejemplos de compuertas proceden de la recolección con la aplicación. Los 500 ejemplos de `OTRO` figuran en el ZIP con autor `sintetico` y contienen dibujos que no representan compuertas. El script `generar_otro.py`, con el que se generaron originalmente, **ya no está en el commit actual**.

Distribución de aportes en las **3.000 imágenes de compuertas**, verificada a partir de los nombres de archivo:

| Persona / identificador | Dibujos | Aporte |
|---|---:|---:|
| faalvial | 1.133 | 37,8 % |
| christmas | 873 | 29,1 % |
| dodo | 685 | 22,8 % |
| omar | 297 | 9,9 % |
| anónimo | 12 | 0,4 % |
| **Total** | **3.000** | **100 %** |

El nombre de cada PNG sigue el patrón `<fecha>_<autor>_<id>.png`. Los dibujos incorrectos pueden separarse mediante `/revisar` y `/descartar` sin eliminarlos definitivamente, siempre que el servidor tenga configurada una clave de administrador. La recolección pública, el acceso a las imágenes y la descarga del dataset no requieren autenticación en la implementación actual: conviene tenerlo en cuenta antes de usar la aplicación para reunir datos fuera de un contexto académico.

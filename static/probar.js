// Página "Adivina tu dibujo": dibuja, preprocesa y predice en el navegador.
const lienzo = document.getElementById('lienzo');
const ctx = lienzo.getContext('2d');
const GROSOR = 8;

const elGanadora = document.getElementById('ganadora');
const elProbs = document.getElementById('probabilidades');
const elDetalle = document.getElementById('detalle');
const vistaRed = document.getElementById('entrada-red');

let trazos = [];
let trazoActual = null;
let modelo = null;

function posicion(e) {
  const r = lienzo.getBoundingClientRect();
  return [(e.clientX - r.left) * lienzo.width / r.width, (e.clientY - r.top) * lienzo.height / r.height];
}

function redibujar() {
  ctx.clearRect(0, 0, lienzo.width, lienzo.height);
  ctx.strokeStyle = 'black';
  ctx.lineWidth = GROSOR;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  for (const t of trazos) {
    ctx.beginPath();
    ctx.moveTo(t[0][0], t[0][1]);
    if (t.length === 1) ctx.lineTo(t[0][0] + 0.1, t[0][1]);
    for (let i = 1; i < t.length; i++) ctx.lineTo(t[i][0], t[i][1]);
    ctx.stroke();
  }
}

function mostrarEntrada(entrada, tam) {
  vistaRed.width = tam;
  vistaRed.height = tam;
  const c = vistaRed.getContext('2d');
  const img = c.createImageData(tam, tam);
  for (let i = 0; i < entrada.length; i++) {
    const v = 255 - Math.round(entrada[i] * 255);
    img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v;
    img.data[i * 4 + 3] = 255;
  }
  c.putImageData(img, 0, 0);
}

function limpiarResultado(texto) {
  elGanadora.textContent = texto;
  elGanadora.classList.add('mensaje');
  elProbs.innerHTML = '';
  vistaRed.getContext('2d').clearRect(0, 0, vistaRed.width, vistaRed.height);
}

function adivinar() {
  if (!modelo) return;
  const entrada = Modelo.preprocesar(lienzo, modelo.tam, modelo.margen);
  if (!entrada) {
    limpiarResultado('Dibuja una compuerta');
    return;
  }
  mostrarEntrada(entrada, modelo.tam);
  const t0 = performance.now();
  const probs = Modelo.predecir(modelo, entrada);
  const ms = Math.round(performance.now() - t0);
  const orden = probs.map((p, i) => [p, modelo.clases[i]]).sort((a, b) => b[0] - a[0]);
  elGanadora.textContent = orden[0][1] + ' · ' + Math.round(orden[0][0] * 100) + '%';
  elGanadora.classList.remove('mensaje');
  elProbs.innerHTML = '';
  for (const [p, clase] of orden) {
    const li = document.createElement('li');
    li.innerHTML = '<span class="nombre"></span><span class="barra-fondo"><span class="barra-lleno"></span></span><span class="numero"></span>';
    li.querySelector('.nombre').textContent = clase;
    li.querySelector('.barra-lleno').style.width = (p * 100).toFixed(1) + '%';
    li.querySelector('.numero').textContent = (p * 100).toFixed(1) + '%';
    elProbs.appendChild(li);
  }
  elDetalle.textContent = 'Así ve la red tu dibujo (' + modelo.tam + '×' + modelo.tam + ' píxeles). Predicción en ' + ms + ' ms.';
}

lienzo.addEventListener('pointerdown', (e) => {
  e.preventDefault();
  lienzo.setPointerCapture(e.pointerId);
  trazoActual = [posicion(e)];
  trazos.push(trazoActual);
  redibujar();
});
lienzo.addEventListener('pointermove', (e) => {
  if (!trazoActual) return;
  trazoActual.push(posicion(e));
  redibujar();
});
for (const tipo of ['pointerup', 'pointercancel']) {
  lienzo.addEventListener(tipo, () => {
    if (!trazoActual) return;
    trazoActual = null;
    adivinar();
  });
}

document.getElementById('borrar').addEventListener('click', () => { trazos = []; redibujar(); adivinar(); });
document.getElementById('deshacer').addEventListener('click', () => { trazos.pop(); redibujar(); adivinar(); });

Modelo.cargar(BASE_MODELO)
  .then((m) => {
    modelo = m;
    limpiarResultado('Dibuja una compuerta');
  })
  .catch(() => {
    limpiarResultado('Todavía no hay un modelo entrenado');
    elDetalle.textContent = 'Exporta el modelo desde el notebook y copia modelo_web.json y modelo_web.bin en static/modelo/.';
  });
redibujar();

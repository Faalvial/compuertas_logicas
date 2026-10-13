// Página "Adivina tu dibujo": envía el dibujo (o una imagen subida) al servidor
// y muestra lo que predice la CNN.
const lienzo = document.getElementById('lienzo');
const ctx = lienzo.getContext('2d');
const GROSOR = 8;
const LADO_MAX_SUBIDA = 512;  // las fotos se achican antes de enviarlas

const elGanadora = document.getElementById('ganadora');
const elProbs = document.getElementById('probabilidades');
const elArchivo = document.getElementById('archivo');

let trazos = [];
let trazoActual = null;
let imagenSubida = null;  // dibujo que devolvió el servidor al subir una imagen

function posicion(e) {
  const r = lienzo.getBoundingClientRect();
  return [(e.clientX - r.left) * lienzo.width / r.width, (e.clientY - r.top) * lienzo.height / r.height];
}

function redibujar() {
  ctx.clearRect(0, 0, lienzo.width, lienzo.height);
  if (imagenSubida) ctx.drawImage(imagenSubida, 0, 0);
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

function mostrarMensaje(texto) {
  elGanadora.textContent = texto;
  elGanadora.classList.add('mensaje');
  elProbs.innerHTML = '';
}

function mostrarResultado(datos) {
  const orden = datos.probabilidades.map((p, i) => [p, datos.clases[i]]).sort((a, b) => b[0] - a[0]);
  elGanadora.textContent = orden[0][1] + ' · ' + Math.round(orden[0][0] * 100) + '%';
  elGanadora.classList.remove('mensaje');
  elProbs.innerHTML = '';
  for (const [p, clase] of orden) {
    const li = document.createElement('li');
    li.innerHTML = '<svg class="icono" viewBox="0 0 90 50" fill="none" stroke="currentColor" stroke-width="3" '
      + 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + COMPUERTAS[clase].svg + '</svg>'
      + '<span class="nombre"></span><span class="barra-fondo"><span class="barra-lleno"></span></span><span class="numero"></span>';
    li.querySelector('.nombre').textContent = clase;
    li.querySelector('.barra-lleno').style.width = (p * 100).toFixed(1) + '%';
    li.querySelector('.numero').textContent = (p * 100).toFixed(1) + '%';
    elProbs.appendChild(li);
  }
}

async function enviar(datos) {
  const resp = await fetch('/predecir', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  });
  return resp.json();
}

async function adivinar() {
  if (!trazos.length) {
    mostrarMensaje('Dibuja una compuerta');
    return;
  }
  const datos = await enviar({ imagen: lienzo.toDataURL('image/png') });
  if (datos.ok) mostrarResultado(datos);
  else mostrarMensaje(datos.error);
}

// Subir una imagen: se achica en el navegador, el servidor la convierte en un dibujo
// como los del lienzo y lo devuelve para mostrarlo.
async function subirImagen(archivo) {
  mostrarMensaje('Analizando la imagen…');
  const original = await createImageBitmap(archivo);
  const escala = Math.min(1, LADO_MAX_SUBIDA / Math.max(original.width, original.height));
  const temporal = document.createElement('canvas');
  temporal.width = Math.round(original.width * escala);
  temporal.height = Math.round(original.height * escala);
  temporal.getContext('2d').drawImage(original, 0, 0, temporal.width, temporal.height);
  const datos = await enviar({ imagen: temporal.toDataURL('image/png'), subida: true });
  if (!datos.ok) {
    mostrarMensaje(datos.error);
    return;
  }
  const dibujo = new Image();
  dibujo.onload = () => {
    imagenSubida = dibujo;
    trazos = [];
    redibujar();
  };
  dibujo.src = datos.dibujo;
  mostrarResultado(datos);
}

lienzo.addEventListener('pointerdown', (e) => {
  e.preventDefault();
  lienzo.setPointerCapture(e.pointerId);
  if (imagenSubida) {  // al dibujar se empieza de cero
    imagenSubida = null;
    trazos = [];
  }
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

document.getElementById('borrar').addEventListener('click', () => { trazos = []; imagenSubida = null; redibujar(); adivinar(); });
document.getElementById('deshacer').addEventListener('click', () => { trazos.pop(); redibujar(); adivinar(); });
document.getElementById('subir').addEventListener('click', () => elArchivo.click());
elArchivo.addEventListener('change', () => {
  if (elArchivo.files.length) subirImagen(elArchivo.files[0]);
  elArchivo.value = '';
});

mostrarMensaje('Dibuja una compuerta');
redibujar();

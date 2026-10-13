// Página "Adivina tu dibujo": envía el dibujo al servidor y muestra lo que predice la CNN.
const lienzo = document.getElementById('lienzo');
const ctx = lienzo.getContext('2d');
const GROSOR = 8;

const elGanadora = document.getElementById('ganadora');
const elProbs = document.getElementById('probabilidades');

let trazos = [];
let trazoActual = null;

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

function mostrarMensaje(texto) {
  elGanadora.textContent = texto;
  elGanadora.classList.add('mensaje');
  elProbs.innerHTML = '';
}

async function adivinar() {
  if (!trazos.length) {
    mostrarMensaje('Dibuja una compuerta');
    return;
  }
  const resp = await fetch('/predecir', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ imagen: lienzo.toDataURL('image/png') }),
  });
  const datos = await resp.json();
  if (!datos.ok) {
    mostrarMensaje(datos.error);
    return;
  }
  const orden = datos.probabilidades.map((p, i) => [p, datos.clases[i]]).sort((a, b) => b[0] - a[0]);
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

mostrarMensaje('Dibuja una compuerta');
redibujar();

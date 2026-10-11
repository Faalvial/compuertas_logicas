// Lienzo con soporte para mouse, dedo y lápiz (pointer events).
const lienzo = document.getElementById('lienzo');
const ctx = lienzo.getContext('2d');
const GROSOR = 8;

const elClase = document.getElementById('clase');
const elRef = document.getElementById('ref-svg');
const elTip = document.getElementById('tip');
const elAviso = document.getElementById('aviso');
const elAutor = document.getElementById('autor');
const btnEnviar = document.getElementById('enviar');

let clase = elClase.textContent.trim();
let trazos = [];
let trazoActual = null;
let enviando = false;

try { elAutor.value = localStorage.getItem('autor') || ''; } catch (e) {}
elAutor.addEventListener('change', () => {
  try { localStorage.setItem('autor', elAutor.value); } catch (e) {}
});

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
  btnEnviar.disabled = trazos.length === 0 || enviando;
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
  lienzo.addEventListener(tipo, () => { trazoActual = null; });
}

function borrar() { trazos = []; redibujar(); }
function deshacer() { trazos.pop(); redibujar(); }

function mostrarClase(nueva) {
  clase = nueva;
  elClase.textContent = nueva;
  elRef.innerHTML = COMPUERTAS[nueva].svg;
  elTip.textContent = COMPUERTAS[nueva].tip;
}

function actualizarConteos(conteos) {
  for (const li of document.querySelectorAll('#conteos li')) {
    const n = conteos[li.dataset.clase] || 0;
    li.querySelector('.numero').textContent = n;
    li.querySelector('.barra-lleno').style.width = Math.min(100, Math.floor(n * 100 / META)) + '%';
  }
}

async function enviar() {
  if (!trazos.length || enviando) return;
  enviando = true;
  btnEnviar.disabled = true;
  elAviso.textContent = 'Guardando…';
  try {
    const resp = await fetch('/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clase, imagen: lienzo.toDataURL('image/png'), autor: elAutor.value }),
    });
    const datos = await resp.json();
    if (!datos.ok) throw new Error(datos.error || 'No se pudo guardar.');
    elAviso.textContent = 'Guardado ' + datos.guardado + ' (' + datos.conteos[datos.guardado] + '). Sigue con la siguiente.';
    actualizarConteos(datos.conteos);
    mostrarClase(datos.siguiente);
    trazos = [];
  } catch (err) {
    elAviso.textContent = err.message + ' Intenta de nuevo.';
  } finally {
    enviando = false;
    redibujar();
  }
}

document.getElementById('borrar').addEventListener('click', borrar);
document.getElementById('deshacer').addEventListener('click', deshacer);
btnEnviar.addEventListener('click', enviar);
document.addEventListener('keydown', (e) => {
  if (e.target === elAutor) return;
  if (e.key === 'Enter') { e.preventDefault(); enviar(); }
  if (e.key === 'Escape') borrar();
  if ((e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); deshacer(); }
});

redibujar();

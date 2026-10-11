// Inferencia de la CNN en el navegador, sin TensorFlow.
// Los pesos se exportan desde el notebook (modelo_web.json + modelo_web.bin).
// El preprocesamiento replica el del notebook: canal alfa, recorte a la tinta,
// relleno a cuadrado con margen y redimensionado Lanczos (como PIL).

const Modelo = (() => {
  // ---------- Preprocesamiento ----------

  function sinc(x) {
    if (x === 0) return 1;
    x *= Math.PI;
    return Math.sin(x) / x;
  }
  function lanczos(x) {
    return x > -3 && x < 3 ? sinc(x) * sinc(x / 3) : 0;
  }

  // Coeficientes de remuestreo, igual que precompute_coeffs de PIL.
  function coeficientes(entrada, salida) {
    const escala = entrada / salida;
    const escalaFiltro = Math.max(escala, 1);
    const soporte = 3 * escalaFiltro;
    const res = [];
    for (let xx = 0; xx < salida; xx++) {
      const centro = (xx + 0.5) * escala;
      const xmin = Math.max(Math.trunc(centro - soporte + 0.5), 0);
      const xmax = Math.min(Math.trunc(centro + soporte + 0.5), entrada);
      const pesos = [];
      let total = 0;
      for (let x = xmin; x < xmax; x++) {
        const w = lanczos((x - centro + 0.5) / escalaFiltro);
        pesos.push(w);
        total += w;
      }
      res.push({ xmin, pesos: pesos.map((w) => (total ? w / total : 0)) });
    }
    return res;
  }

  function clip8(v) {
    return Math.min(255, Math.max(0, Math.round(v)));
  }

  // Redimensiona una imagen en escala de grises (Uint8 lado x lado) a tam x tam.
  function redimensionar(src, lado, tam) {
    const cx = coeficientes(lado, tam);
    const horizontal = new Uint8ClampedArray(lado * tam);
    for (let y = 0; y < lado; y++) {
      for (let xx = 0; xx < tam; xx++) {
        const { xmin, pesos } = cx[xx];
        let s = 0;
        for (let k = 0; k < pesos.length; k++) s += src[y * lado + xmin + k] * pesos[k];
        horizontal[y * tam + xx] = clip8(s);
      }
    }
    const cy = coeficientes(lado, tam);
    const out = new Uint8ClampedArray(tam * tam);
    for (let yy = 0; yy < tam; yy++) {
      const { xmin, pesos } = cy[yy];
      for (let x = 0; x < tam; x++) {
        let s = 0;
        for (let k = 0; k < pesos.length; k++) s += horizontal[(xmin + k) * tam + x] * pesos[k];
        out[yy * tam + x] = clip8(s);
      }
    }
    return out;
  }

  // Devuelve Float32Array tam*tam con valores 0..1, o null si el lienzo está vacío.
  function preprocesar(lienzo, tam, margen) {
    const { width: W, height: H } = lienzo;
    const datos = lienzo.getContext('2d').getImageData(0, 0, W, H).data;
    let x0 = W, y0 = H, x1 = -1, y1 = -1;
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        if (datos[(y * W + x) * 4 + 3] > 0) {
          if (x < x0) x0 = x;
          if (x > x1) x1 = x;
          if (y < y0) y0 = y;
          if (y > y1) y1 = y;
        }
      }
    }
    if (x1 < 0) return null;
    const ancho = x1 - x0 + 1, alto = y1 - y0 + 1;
    const lado = Math.trunc(Math.max(ancho, alto) * (1 + 2 * margen));
    const cuadrado = new Uint8Array(lado * lado);
    const ox = Math.trunc((lado - ancho) / 2), oy = Math.trunc((lado - alto) / 2);
    for (let y = 0; y < alto; y++) {
      for (let x = 0; x < ancho; x++) {
        cuadrado[(y + oy) * lado + x + ox] = datos[((y + y0) * W + x + x0) * 4 + 3];
      }
    }
    const pequena = redimensionar(cuadrado, lado, tam);
    const entrada = new Float32Array(tam * tam);
    for (let i = 0; i < entrada.length; i++) entrada[i] = pequena[i] / 255;
    return entrada;
  }

  // ---------- Capas (formato alto x ancho x canales, como Keras) ----------

  function conv2d(x, h, w, cin, capa, pesos) {
    const k = capa.kernel, cout = capa.filtros, p = Math.floor(k / 2);
    const W = pesos.subarray(capa.w[0], capa.w[0] + capa.w[1]);
    const b = pesos.subarray(capa.b[0], capa.b[0] + capa.b[1]);
    const out = new Float32Array(h * w * cout);
    const acc = new Float32Array(cout);
    for (let oy = 0; oy < h; oy++) {
      for (let ox = 0; ox < w; ox++) {
        acc.set(b);
        for (let ky = 0; ky < k; ky++) {
          const iy = oy + ky - p;
          if (iy < 0 || iy >= h) continue;
          for (let kx = 0; kx < k; kx++) {
            const ix = ox + kx - p;
            if (ix < 0 || ix >= w) continue;
            const base = (iy * w + ix) * cin;
            const wbase = (ky * k + kx) * cin * cout;
            for (let ci = 0; ci < cin; ci++) {
              const v = x[base + ci];
              if (v === 0) continue;
              const fila = wbase + ci * cout;
              for (let co = 0; co < cout; co++) acc[co] += v * W[fila + co];
            }
          }
        }
        const o = (oy * w + ox) * cout;
        for (let co = 0; co < cout; co++) out[o + co] = activar(acc[co], capa.activacion);
      }
    }
    return out;
  }

  function maxpool(x, h, w, c, tam) {
    const oh = Math.floor(h / tam), ow = Math.floor(w / tam);
    const out = new Float32Array(oh * ow * c).fill(-Infinity);
    for (let oy = 0; oy < oh; oy++)
      for (let ox = 0; ox < ow; ox++)
        for (let dy = 0; dy < tam; dy++)
          for (let dx = 0; dx < tam; dx++) {
            const i = ((oy * tam + dy) * w + ox * tam + dx) * c, o = (oy * ow + ox) * c;
            for (let ch = 0; ch < c; ch++) if (x[i + ch] > out[o + ch]) out[o + ch] = x[i + ch];
          }
    return [out, oh, ow];
  }

  function dense(x, capa, pesos) {
    const n = capa.unidades, m = capa.entrada;
    const W = pesos.subarray(capa.w[0], capa.w[0] + capa.w[1]);
    const out = Float32Array.from(pesos.subarray(capa.b[0], capa.b[0] + capa.b[1]));
    for (let i = 0; i < m; i++) {
      const v = x[i];
      if (v === 0) continue;
      const fila = i * n;
      for (let j = 0; j < n; j++) out[j] += v * W[fila + j];
    }
    if (capa.activacion === 'softmax') {
      const max = Math.max(...out);
      let s = 0;
      for (let j = 0; j < n; j++) s += (out[j] = Math.exp(out[j] - max));
      for (let j = 0; j < n; j++) out[j] /= s;
      return out;
    }
    for (let j = 0; j < n; j++) out[j] = activar(out[j], capa.activacion);
    return out;
  }

  function activar(v, tipo) {
    return tipo === 'relu' ? (v > 0 ? v : 0) : v;
  }

  // ---------- API ----------

  async function cargar(base) {
    const resp = await fetch(base + 'modelo_web.json', { cache: 'no-cache' });
    if (!resp.ok) throw new Error('No hay modelo');
    const manifest = await resp.json();
    const bin = await fetch(base + 'modelo_web.bin', { cache: 'no-cache' });
    if (!bin.ok) throw new Error('Faltan los pesos del modelo');
    manifest.pesos = new Float32Array(await bin.arrayBuffer());
    return manifest;
  }

  function predecir(modelo, entrada) {
    let x = entrada, h = modelo.tam, w = modelo.tam, c = 1;
    for (const capa of modelo.capas) {
      if (capa.tipo === 'conv2d') {
        x = conv2d(x, h, w, c, capa, modelo.pesos);
        c = capa.filtros;
      } else if (capa.tipo === 'maxpool') {
        [x, h, w] = maxpool(x, h, w, c, capa.tam);
      } else if (capa.tipo === 'dense') {
        x = dense(x, capa, modelo.pesos);
      }
      // 'flatten' no cambia el arreglo: ya está en orden alto x ancho x canales.
    }
    return Array.from(x);
  }

  return { cargar, preprocesar, predecir };
})();

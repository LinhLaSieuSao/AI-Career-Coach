// A client-side three-step guide; it does not rerun the Streamlit app.
(() => {
  if (window.__careerHowCleanup) window.__careerHowCleanup();

  let boundRoot = null;
  let controller = null;

  const bind = () => {
    const root = document.getElementById('how-steps');
    if (root === boundRoot && controller) return;
    if (controller) controller.abort();
    controller = null;
    boundRoot = null;
    if (!root) return;

    const panels = [...root.querySelectorAll('[data-step-panel]')];
    const dots = [...root.querySelectorAll('.how-progress-dot')];
    const label = root.querySelector('.how-step-label');
    const progress = root.querySelector('.how-progress');
    const back = root.querySelector('.how-back');
    const next = root.querySelector('.how-next');
    const finish = root.querySelector('.how-finish');
    if (panels.length !== 3 || dots.length !== 3 || !label || !progress || !back || !next || !finish) return;

    boundRoot = root;
    controller = new AbortController();
    const signal = controller.signal;
    let step = Math.min(3, Math.max(1, Number(window.__careerHowStep) || 1));

    const showStep = (newStep, focusHeading = false) => {
      step = Math.min(3, Math.max(1, newStep));
      window.__careerHowStep = step;
      root.dataset.step = String(step);
      root.style.setProperty('--how-progress', `${(step - 1) * 50}%`);
      label.textContent = `Bước ${step} / 3`;
      progress.setAttribute('aria-valuenow', String(step));
      progress.setAttribute('aria-valuetext', `Bước ${step} trên 3`);

      panels.forEach((panel, index) => {
        panel.hidden = index !== step - 1;
      });
      dots.forEach((dot, index) => {
        dot.classList.toggle('is-complete', index < step - 1);
        dot.classList.toggle('is-current', index === step - 1);
      });
      back.hidden = step === 1;
      next.hidden = step === 3;
      next.disabled = false;
      finish.hidden = step !== 3;

      if (focusHeading) {
        const heading = panels[step - 1].querySelector('h3');
        heading?.focus({ preventScroll: true });
        requestAnimationFrame(() => root.closest('#how').scrollIntoView({
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth',
          block: 'start',
        }));
      }
    };

    next.addEventListener('click', () => showStep(step + 1, true), { signal });
    back.addEventListener('click', () => showStep(step - 1, true), { signal });
    showStep(step);
  };

  const observer = new MutationObserver(bind);
  observer.observe(document.body, { childList: true, subtree: true });
  bind();

  window.__careerHowCleanup = () => {
    observer.disconnect();
    if (controller) controller.abort();
    controller = null;
    boundRoot = null;
  };
})();

// Soft blue/white gradient waves within the existing landing sections.
(() => {
  if (window.__careerWavesCleanup) window.__careerWavesCleanup();

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const surfaces = new Map();
  let frame = 0;
  let lastFrame = 0;

  const draw = (state, time) => {
    const { context: ctx, width: w, height: h, dark } = state;
    if (!w || !h) return;
    ctx.clearRect(0, 0, w, h);

    const base = ctx.createLinearGradient(0, 0, w, h);
    if (dark) {
      base.addColorStop(0, '#071a3c');
      base.addColorStop(0.55, '#0b326f');
      base.addColorStop(1, '#071a3c');
    } else {
      base.addColorStop(0, '#f9fdff');
      base.addColorStop(0.52, '#e8f5ff');
      base.addColorStop(1, '#ffffff');
    }
    ctx.fillStyle = base;
    ctx.fillRect(0, 0, w, h);

    const layers = dark
      ? [
          { y: 0.34, amp: 0.085, color: '#0a7aff', alpha: 0.26, speed: 0.26 },
          { y: 0.57, amp: 0.11, color: '#59b9ff', alpha: 0.2, speed: -0.19 },
          { y: 0.81, amp: 0.07, color: '#d6ecff', alpha: 0.12, speed: 0.13 },
        ]
      : [
          { y: 0.25, amp: 0.08, color: '#59b9ff', alpha: 0.27, speed: 0.2 },
          { y: 0.48, amp: 0.1, color: '#0a7aff', alpha: 0.18, speed: -0.16 },
          { y: 0.72, amp: 0.075, color: '#59b9ff', alpha: 0.2, speed: 0.12 },
          { y: 0.91, amp: 0.055, color: '#ffffff', alpha: 0.72, speed: -0.1 },
        ];

    layers.forEach((layer, index) => {
      const phase = time * layer.speed + index * 1.7;
      const waveY = (x) => h * (layer.y
        + layer.amp * Math.sin((x / w) * Math.PI * 2.1 + phase)
        + layer.amp * 0.34 * Math.sin((x / w) * Math.PI * 4.2 - phase * 0.7));
      ctx.beginPath();
      ctx.moveTo(0, waveY(0));
      for (let x = 8; x < w + 8; x += 8) ctx.lineTo(Math.min(x, w), waveY(Math.min(x, w)));
      ctx.lineTo(w, h);
      ctx.lineTo(0, h);
      ctx.closePath();
      const fill = ctx.createLinearGradient(0, h * (layer.y - layer.amp), 0, h);
      fill.addColorStop(0, layer.color + '00');
      fill.addColorStop(0.22, layer.color + Math.round(layer.alpha * 255).toString(16).padStart(2, '0'));
      fill.addColorStop(1, layer.color + Math.round(layer.alpha * 0.36 * 255).toString(16).padStart(2, '0'));
      ctx.fillStyle = fill;
      ctx.fill();
    });
  };

  const resize = (state) => {
    const { width, height } = state.surface.getBoundingClientRect();
    if (width < 1 || height < 1) return;
    const scale = Math.min(window.devicePixelRatio || 1, 2);
    state.width = width;
    state.height = height;
    state.canvas.width = Math.round(width * scale);
    state.canvas.height = Math.round(height * scale);
    state.context.setTransform(scale, 0, 0, scale, 0, 0);
    draw(state, 0);
  };

  const tick = (timestamp) => {
    frame = 0;
    if (timestamp - lastFrame < 33) {
      start();
      return;
    }
    lastFrame = timestamp;
    let visible = false;
    for (const state of surfaces.values()) {
      if (!state.visible || !state.surface.isConnected) continue;
      visible = true;
      draw(state, timestamp / 1000);
    }
    if (visible) start();
  };

  const start = () => {
    if (!frame && !reducedMotion.matches && !document.hidden &&
        [...surfaces.values()].some((state) => state.visible)) {
      frame = requestAnimationFrame(tick);
    }
  };
  const stop = () => {
    if (frame) cancelAnimationFrame(frame);
    frame = 0;
  };
  const onMotionChange = () => {
    if (reducedMotion.matches) {
      stop();
      for (const state of surfaces.values()) draw(state, 0);
    } else start();
  };
  const onVisibilityChange = () => document.hidden ? stop() : start();

  const visibilityObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const state = surfaces.get(entry.target);
      if (state) state.visible = entry.isIntersecting;
    }
    start();
  }, { rootMargin: '100px' });
  const sizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const state = surfaces.get(entry.target);
      if (state) resize(state);
    }
  });
  const attach = (surface) => {
    if (surfaces.has(surface)) return;
    const canvas = document.createElement('canvas');
    canvas.className = 'wave-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    surface.prepend(canvas);
    const context = canvas.getContext('2d');
    if (!context) {
      canvas.remove();
      return;
    }
    const state = { surface, canvas, context, width: 0, height: 0, dark: surface.classList.contains('site-footer'), visible: false };
    surfaces.set(surface, state);
    resize(state);
    visibilityObserver.observe(surface);
    sizeObserver.observe(surface);
  };
  const attachAvailable = () => {
    document.querySelectorAll('.beams-surface, .site-footer').forEach(attach);
    if (surfaces.size >= 3) mountObserver.disconnect();
  };
  const mountObserver = new MutationObserver(attachAvailable);
  mountObserver.observe(document.body, { childList: true, subtree: true });
  reducedMotion.addEventListener('change', onMotionChange);
  document.addEventListener('visibilitychange', onVisibilityChange);
  attachAvailable();

  window.__careerWavesCleanup = () => {
    stop();
    reducedMotion.removeEventListener('change', onMotionChange);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    mountObserver.disconnect();
    visibilityObserver.disconnect();
    sizeObserver.disconnect();
    for (const state of surfaces.values()) state.canvas.remove();
    surfaces.clear();
  };
})();


// Client-side FAQ search and accordion; no profile data leaves the page.
(() => {
  if (window.__careerFaqCleanup) window.__careerFaqCleanup();

  let boundRoot = null;
  let controller = null;
  const saved = window.__careerFaqState || { query: '', openId: '1' };
  window.__careerFaqState = saved;

  const fold = (value) => value.normalize('NFD')
    .replace(/\p{M}/gu, '')
    .replace(/[đĐ]/g, 'd')
    .toLocaleLowerCase('vi');

  const highlightNode = (node, foldedQuery) => {
    const original = node.nodeValue;
    let folded = '';
    const offsets = [];
    let offset = 0;
    for (const character of original) {
      const normalized = fold(character);
      for (let index = 0; index < normalized.length; index += 1) {
        offsets.push([offset, offset + character.length]);
      }
      folded += normalized;
      offset += character.length;
    }

    const fragment = document.createDocumentFragment();
    let cursor = 0;
    let lastEnd = 0;
    let found = false;
    while (foldedQuery && (cursor = folded.indexOf(foldedQuery, cursor)) !== -1) {
      const start = offsets[cursor][0];
      const end = offsets[cursor + foldedQuery.length - 1][1];
      fragment.append(document.createTextNode(original.slice(lastEnd, start)));
      const mark = document.createElement('mark');
      mark.className = 'faq-match';
      mark.textContent = original.slice(start, end);
      fragment.append(mark);
      lastEnd = end;
      cursor += foldedQuery.length;
      found = true;
    }
    if (found) {
      fragment.append(document.createTextNode(original.slice(lastEnd)));
      node.replaceWith(fragment);
    }
  };

  const highlightWithin = (element, foldedQuery) => {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => highlightNode(node, foldedQuery));
  };

  const bind = () => {
    const root = document.getElementById('faq');
    if (root === boundRoot && controller) return;
    if (controller) controller.abort();
    controller = null;
    boundRoot = null;
    if (!root) return;

    const input = root.querySelector('.faq-search-input');
    const clear = root.querySelector('.faq-search-clear');
    const empty = root.querySelector('.faq-empty');
    const status = root.querySelector('.faq-search-status');
    const rows = [...root.querySelectorAll('.faq-item')];
    if (!input || !clear || !empty || !status || !rows.length) return;

    boundRoot = root;
    controller = new AbortController();
    const { signal } = controller;
    const searchable = new Map(rows.map((row) => [
      row,
      fold(`${row.querySelector('.faq-question').textContent} ${row.querySelector('.faq-answer').textContent}`),
    ]));
    input.value = saved.query;
    let previousQuery = input.value.trim();

    const setOpen = (selected) => {
      rows.forEach((row) => {
        const open = row === selected && !row.hidden;
        row.classList.toggle('is-open', open);
        row.querySelector('.faq-trigger').setAttribute('aria-expanded', String(open));
        const panel = row.querySelector('.faq-panel');
        panel.setAttribute('aria-hidden', String(!open));
        panel.toggleAttribute('inert', !open);
      });
      saved.openId = selected?.dataset.faqId ?? null;
    };

    const clearHighlights = () => {
      root.querySelectorAll('mark.faq-match').forEach((mark) => {
        const parent = mark.parentNode;
        mark.replaceWith(document.createTextNode(mark.textContent));
        parent.normalize();
      });
    };

    const updateSearch = () => {
      const query = input.value.trim();
      const foldedQuery = fold(query);
      clearHighlights();
      const visible = rows.filter((row) => {
        const matches = !foldedQuery || searchable.get(row).includes(foldedQuery);
        row.hidden = !matches;
        if (matches && foldedQuery) {
          highlightWithin(row.querySelector('.faq-question'), foldedQuery);
          highlightWithin(row.querySelector('.faq-answer'), foldedQuery);
        }
        return matches;
      });

      clear.hidden = !input.value;
      empty.hidden = visible.length > 0;
      status.textContent = query ? `${visible.length} câu hỏi phù hợp` : '';
      if (!query && previousQuery) {
        setOpen(rows[0]);
      } else {
        const current = visible.find((row) => row.dataset.faqId === saved.openId);
        setOpen(current || visible[0] || null);
      }
      saved.query = input.value;
      previousQuery = query;
    };

    rows.forEach((row) => {
      row.querySelector('.faq-trigger').addEventListener('click', () => {
        setOpen(row.classList.contains('is-open') ? null : row);
      }, { signal });
    });
    input.addEventListener('input', updateSearch, { signal });
    clear.addEventListener('click', () => {
      input.value = '';
      updateSearch();
      input.focus();
    }, { signal });
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && input.value) {
        input.value = '';
        updateSearch();
      }
    }, { signal });
    updateSearch();
  };

  const observer = new MutationObserver(bind);
  observer.observe(document.body, { childList: true, subtree: true });
  bind();

  window.__careerFaqCleanup = () => {
    observer.disconnect();
    if (controller) controller.abort();
    controller = null;
    boundRoot = null;
  };
})();


// WebGL Cloud Shader background for Feature, Toolkit (Form), and FAQ sections.
(() => {
  if (window.__careerCloudCleanup) window.__careerCloudCleanup();

  const VERT = `
attribute vec2 a_pos;
varying vec2 v_uv;
void main() {
  v_uv = a_pos * 0.5 + 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}
`;

  const FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif

varying vec2 v_uv;

uniform vec2 u_res;
uniform float u_time;
uniform float u_count;
uniform vec3 u_cloud;
uniform vec3 u_skyTop;
uniform vec3 u_skyBottom;

const mat2 R = mat2(0.80, 0.60, -0.60, 0.80);

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(41.31, 289.17))) * 26737.367);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
  float sum = 0.0;
  float amp = 0.5;
  for (int i = 0; i < 4; i++) {
    sum += amp * vnoise(p);
    p = R * p * 2.03 + 19.19;
    amp *= 0.5;
  }
  return sum;
}

float billow(vec2 p) {
  float sum = 0.0;
  float amp = 0.5;
  for (int i = 0; i < 5; i++) {
    sum += amp * (1.0 - abs(2.0 * vnoise(p) - 1.0));
    p = R * p * 2.11 + 13.37;
    amp *= 0.5;
  }
  return sum;
}

float cloudDensity(vec2 p, vec2 c, vec2 r, float seed, float t) {
  vec2 q = p - c;
  float ry = q.y > 0.0 ? r.y : r.y * 0.42;
  float env = 1.0 - length(vec2(q.x / r.x, q.y / ry));
  if (env < -0.35) return 0.0;

  vec2 dp = q * (2.4 / r.x) + seed;
  dp += 0.6 * vec2(
    fbm(dp * 1.4 + t * 0.04),
    fbm(dp * 1.4 + 7.7 - t * 0.03)
  );
  float detail = billow(dp * 1.6);
  return env + (detail - 0.62) * 0.62;
}

vec3 shadeCloud(vec3 color, vec3 sky, vec2 p, vec2 c, vec2 r, float seed, float t, float dist) {
  float d = cloudDensity(p, c, r, seed, t);
  if (d < 0.02) return color;

  float dUp = cloudDensity(p + vec2(0.0, r.y * 0.55), c, r, seed, t);
  float occl = clamp((dUp - d) * 1.1 + d * 0.55, 0.0, 1.0);

  vec3 lit = u_cloud * 1.04;
  vec3 shadow = mix(u_cloud * 0.60, sky, 0.38);
  vec3 cloudCol = mix(lit, shadow, occl * 0.85);

  float alpha = smoothstep(0.02, 0.38, d);
  float rim = smoothstep(0.02, 0.14, d) * (1.0 - smoothstep(0.14, 0.40, d));
  cloudCol += rim * 0.10;
  cloudCol = mix(cloudCol, sky, dist * 0.35);
  alpha *= mix(1.0, 0.8, dist);

  return mix(color, cloudCol, alpha);
}

vec3 cloudPass(vec3 color, vec3 sky, vec2 p, float aspect, float t,
               float spd, float phase, float y, vec2 r, float seed, float dist) {
  float cx = mix(-r.x - 0.25, aspect + r.x + 0.25, fract(t * spd + phase));
  float cy = y + sin(t * 0.05 + phase * 6.2831) * 0.012;
  return shadeCloud(color, sky, p, vec2(cx, cy), r, seed, t, dist);
}

void main() {
  float aspect = u_res.x / u_res.y;
  vec2 p = vec2(v_uv.x * aspect, v_uv.y);
  float t = u_time;

  vec3 sky = mix(u_skyBottom, u_skyTop, v_uv.y);
  vec3 color = sky;

  color = mix(color, u_skyBottom * 1.06, smoothstep(0.35, 0.0, v_uv.y) * 0.5);

  vec2 sunPos = vec2(aspect * 0.78, 0.92);
  float sunDist = length(p - sunPos);
  color += vec3(1.0, 0.95, 0.82) * exp(-sunDist * sunDist * 5.0) * 0.28;

  float cirrusBand = smoothstep(0.55, 0.8, v_uv.y) * (1.0 - smoothstep(0.9, 1.0, v_uv.y));
  if (cirrusBand > 0.01) {
    float streak = fbm(vec2(p.x * 1.6 - t * 0.006, p.y * 12.0));
    float wisp = smoothstep(0.52, 0.78, streak) * cirrusBand;
    color = mix(color, u_cloud * 0.98, wisp * 0.35);
  }

  if (u_count > 5.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.006, 0.10, 0.84, vec2(0.20, 0.10), 43.7, 1.0);
  }
  if (u_count > 4.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.008, 0.62, 0.73, vec2(0.24, 0.12), 71.3, 0.85);
  }
  if (u_count > 3.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.011, 0.33, 0.60, vec2(0.34, 0.16), 17.3, 0.55);
  }
  if (u_count > 2.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.013, 0.80, 0.47, vec2(0.30, 0.15), 29.9, 0.45);
  }
  if (u_count > 1.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.016, 0.05, 0.35, vec2(0.46, 0.20), 91.1, 0.15);
  }
  color = cloudPass(color, sky, p, aspect, t, 0.020, 0.48, 0.20, vec2(0.56, 0.24), 57.2, 0.0);

  gl_FragColor = vec4(color, 1.0);
}
`;

  const compileShader = (gl, type, source) => {
    const shader = gl.createShader(type);
    if (!shader) return null;
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.warn(gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  };

  const parseHex = (color) => {
    const value = color.trim();
    if (value.startsWith('#')) {
      const hex = value.slice(1);
      if (hex.length === 3) {
        return [
          parseInt(hex[0] + hex[0], 16) / 255,
          parseInt(hex[1] + hex[1], 16) / 255,
          parseInt(hex[2] + hex[2], 16) / 255,
        ];
      }
      return [
        parseInt(hex.slice(0, 2), 16) / 255,
        parseInt(hex.slice(2, 4), 16) / 255,
        parseInt(hex.slice(4, 6), 16) / 255,
      ];
    }
    return [0.95, 0.95, 0.95];
  };

  // Color palette: darker sky blue at top transitioning to lighter sky blue at bottom
  const CONFIG = {
    speed: 0.8,
    count: 5.0,
    cloudColor: parseHex('#fdfefe'),
    skyTopColor: parseHex('#1c5496'),     // Xanh hơi đậm (đồng bộ thương hiệu)
    skyBottomColor: parseHex('#d0e6fb'),  // Xanh hơi nhạt dịu mát
  };

  const cloudSurfaces = new Map();
  let animFrame = 0;
  let startTime = performance.now();
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const initGL = (canvas) => {
    const gl = canvas.getContext('webgl', {
      alpha: false,
      antialias: false,
      premultipliedAlpha: false,
    }) || canvas.getContext('experimental-webgl');
    if (!gl) return null;

    const vert = compileShader(gl, gl.VERTEX_SHADER, VERT);
    const frag = compileShader(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vert || !frag) return null;

    const program = gl.createProgram();
    if (!program) return null;
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.bindAttribLocation(program, 0, 'a_pos');
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.warn(gl.getProgramInfoLog(program));
      return null;
    }
    gl.useProgram(program);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    const loc = {
      res: gl.getUniformLocation(program, 'u_res'),
      time: gl.getUniformLocation(program, 'u_time'),
      count: gl.getUniformLocation(program, 'u_count'),
      cloud: gl.getUniformLocation(program, 'u_cloud'),
      skyTop: gl.getUniformLocation(program, 'u_skyTop'),
      skyBottom: gl.getUniformLocation(program, 'u_skyBottom'),
    };

    return { gl, program, buffer, vert, frag, loc };
  };

  const renderSurface = (state, elapsed) => {
    const { gl, loc, width, height } = state;
    if (!gl || width < 1 || height < 1) return;

    gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    gl.uniform2f(loc.res, gl.drawingBufferWidth, gl.drawingBufferHeight);
    gl.uniform1f(loc.time, elapsed);
    gl.uniform1f(loc.count, CONFIG.count);
    gl.uniform3f(loc.cloud, CONFIG.cloudColor[0], CONFIG.cloudColor[1], CONFIG.cloudColor[2]);
    gl.uniform3f(loc.skyTop, CONFIG.skyTopColor[0], CONFIG.skyTopColor[1], CONFIG.skyTopColor[2]);
    gl.uniform3f(loc.skyBottom, CONFIG.skyBottomColor[0], CONFIG.skyBottomColor[1], CONFIG.skyBottomColor[2]);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };

  const resize = (state) => {
    const rect = state.surface.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const w = Math.max(1, Math.floor(rect.width * dpr));
    const h = Math.max(1, Math.floor(rect.height * dpr));
    state.width = rect.width;
    state.height = rect.height;
    if (state.canvas.width !== w || state.canvas.height !== h) {
      state.canvas.width = w;
      state.canvas.height = h;
    }
    renderSurface(state, reducedMotion.matches ? 0 : ((performance.now() - startTime) / 1000) * CONFIG.speed);
  };

  const loop = (now) => {
    animFrame = 0;
    const elapsed = reducedMotion.matches ? 0 : ((now - startTime) / 1000) * CONFIG.speed;
    let anyVisible = false;

    for (const state of cloudSurfaces.values()) {
      if (!state.visible || !state.surface.isConnected) continue;
      anyVisible = true;
      renderSurface(state, elapsed);
    }

    if (anyVisible && !reducedMotion.matches && !document.hidden) {
      animFrame = requestAnimationFrame(loop);
    }
  };

  const startLoop = () => {
    if (!animFrame && !reducedMotion.matches && !document.hidden &&
        [...cloudSurfaces.values()].some((s) => s.visible)) {
      animFrame = requestAnimationFrame(loop);
    }
  };

  const stopLoop = () => {
    if (animFrame) cancelAnimationFrame(animFrame);
    animFrame = 0;
  };

  const visibilityObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const state = cloudSurfaces.get(entry.target);
      if (state) state.visible = entry.isIntersecting;
    }
    startLoop();
  }, { rootMargin: '120px' });

  const sizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      const state = cloudSurfaces.get(entry.target);
      if (state) resize(state);
    }
  });

  const attachCloud = (surface) => {
    if (cloudSurfaces.has(surface)) return;
    if (surface.querySelector(':scope > .cloud-shader-canvas')) return;

    const canvas = document.createElement('canvas');
    canvas.className = 'cloud-shader-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    surface.prepend(canvas);

    const glState = initGL(canvas);
    if (!glState) {
      canvas.remove();
      return;
    }

    const state = {
      surface,
      canvas,
      ...glState,
      width: 0,
      height: 0,
      visible: false,
    };

    cloudSurfaces.set(surface, state);
    resize(state);
    visibilityObserver.observe(surface);
    sizeObserver.observe(surface);
    startLoop();
  };

  // Attach WebGL Cloud Shader to Feature (#why) and FAQ (#faq) sections only.
  const attachTargets = () => {
    // Clean up any old canvas in profile panels if present
    document.querySelectorAll('.st-key-profile_entry_panel .cloud-shader-canvas, .st-key-profile_review_panel .cloud-shader-canvas').forEach((el) => el.remove());

    const selectors = [
      '#why',  // Phân hệ Tính năng
      '#faq',  // Phân hệ FAQ
    ];

    selectors.forEach((sel) => {
      document.querySelectorAll(sel).forEach(attachCloud);
    });
  };

  const domObserver = new MutationObserver(attachTargets);
  domObserver.observe(document.body, { childList: true, subtree: true });
  attachTargets();

  reducedMotion.addEventListener('change', () => {
    if (reducedMotion.matches) {
      stopLoop();
      for (const s of cloudSurfaces.values()) renderSurface(s, 0);
    } else {
      startLoop();
    }
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stopLoop();
    else startLoop();
  });



  // Bước 3: Bảo vệ vị trí cuộn khi người dùng click radio trong hộp thoại chọn nghề
  (() => {
    let savedScrollTop = 0;
    let observer = null;
    let timer = null;
    let userScrolled = false;

    const onUserScroll = () => {
      userScrolled = true;
    };

    document.addEventListener('pointerdown', (e) => {
      const radioItem = e.target.closest('[data-testid="stDialog"]:has(.role-dlg-marker) [data-testid="stRadioGroup"]');
      if (!radioItem) return;

      const dlg = document.querySelector('[data-testid="stDialog"]:has(.role-dlg-marker)');
      if (!dlg) return;

      const content = dlg.querySelector('[role="dialog"] > div:has([data-testid="stVerticalBlock"])') ||
                      dlg.querySelector('[role="dialog"] > div:nth-child(2)');
      if (!content) return;

      savedScrollTop = content.scrollTop;
      userScrolled = false;

      // Listen for genuine user scroll intent
      window.addEventListener('wheel', onUserScroll, { passive: true, once: true });
      window.addEventListener('touchmove', onUserScroll, { passive: true, once: true });
      window.addEventListener('keydown', onUserScroll, { passive: true, once: true });

      if (observer) observer.disconnect();
      if (timer) clearTimeout(timer);

      observer = new MutationObserver(() => {
        if (!userScrolled && content && content.scrollTop !== savedScrollTop) {
          content.scrollTop = savedScrollTop;
        }
      });

      observer.observe(dlg, { childList: true, subtree: true, attributes: true });

      timer = setTimeout(() => {
        if (observer) observer.disconnect();
        observer = null;
        window.removeEventListener('wheel', onUserScroll);
        window.removeEventListener('touchmove', onUserScroll);
        window.removeEventListener('keydown', onUserScroll);
      }, 800);
    }, { capture: true });
  })();

  window.__careerCloudCleanup = () => {
    stopLoop();
    domObserver.disconnect();
    visibilityObserver.disconnect();
    sizeObserver.disconnect();
    for (const state of cloudSurfaces.values()) {
      state.canvas.remove();
      if (state.gl) {
        state.gl.deleteBuffer(state.buffer);
        state.gl.deleteProgram(state.program);
        state.gl.deleteShader(state.vert);
        state.gl.deleteShader(state.frag);
      }
    }
    cloudSurfaces.clear();
  };
})();

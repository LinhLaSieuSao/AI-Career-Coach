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


// Decorative green beams for the three dark landing-page surfaces.
(() => {
  if (window.__careerBeamsCleanup) window.__careerBeamsCleanup();

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const surfaces = new Map();
  let frame = 0;

  const newBeam = (width, height) => ({
    x: Math.random() * width * 1.3 - width * 0.15,
    y: Math.random() * height * 1.5 - height * 0.5,
    width: 28 + Math.random() * 62,
    length: height * (0.9 + Math.random() * 0.6),
    angle: -36 + Math.random() * 12,
    speed: 0.25 + Math.random() * 0.55,
    opacity: 0.13 + Math.random() * 0.12,
    pulse: Math.random() * Math.PI * 2,
  });

  const draw = (state) => {
    const { context, width, height } = state;
    if (!width || !height) return;
    context.clearRect(0, 0, width, height);
    context.save();
    context.filter = 'blur(19px)';

    for (const beam of state.beams) {
      const alpha = beam.opacity * (0.82 + Math.sin(beam.pulse) * 0.18);
      const gradient = context.createLinearGradient(0, 0, 0, beam.length);
      gradient.addColorStop(0, 'hsla(153, 75%, 70%, 0)');
      gradient.addColorStop(0.22, `hsla(153, 75%, 70%, ${alpha * 0.55})`);
      gradient.addColorStop(0.5, `hsla(153, 75%, 70%, ${alpha})`);
      gradient.addColorStop(0.78, `hsla(153, 75%, 70%, ${alpha * 0.55})`);
      gradient.addColorStop(1, 'hsla(153, 75%, 70%, 0)');
      context.save();
      context.translate(beam.x, beam.y);
      context.rotate((beam.angle * Math.PI) / 180);
      context.fillStyle = gradient;
      context.fillRect(-beam.width / 2, 0, beam.width, beam.length);
      context.restore();
    }

    context.restore();
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
    state.beams = Array.from(
      { length: Math.max(9, Math.min(20, Math.round(width / 75))) },
      () => newBeam(width, height),
    );
    draw(state);
  };

  const tick = () => {
    frame = 0;
    let hasVisibleSurface = false;
    for (const state of surfaces.values()) {
      if (!state.visible || !state.surface.isConnected) continue;
      hasVisibleSurface = true;
      for (const beam of state.beams) {
        beam.y -= beam.speed;
        beam.pulse += 0.018;
        if (beam.y + beam.length < -80) {
          Object.assign(beam, newBeam(state.width, state.height));
          beam.y = state.height + 40;
        }
      }
      draw(state);
    }
    if (hasVisibleSurface && !reducedMotion.matches && !document.hidden) {
      frame = requestAnimationFrame(tick);
    }
  };

  const start = () => {
    if (!frame && !reducedMotion.matches && !document.hidden) frame = requestAnimationFrame(tick);
  };

  const onMotionChange = () => {
    if (reducedMotion.matches) {
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      for (const state of surfaces.values()) draw(state);
    } else {
      start();
    }
  };

  const onVisibilityChange = () => {
    if (document.hidden && frame) {
      cancelAnimationFrame(frame);
      frame = 0;
    } else if (!document.hidden) {
      start();
    }
  };

  reducedMotion.addEventListener('change', onMotionChange);
  document.addEventListener('visibilitychange', onVisibilityChange);

  const visibilityObserver = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const state = surfaces.get(entry.target);
      if (state) state.visible = entry.isIntersecting;
    }
    if ([...surfaces.values()].some((state) => state.visible)) start();
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
    canvas.className = 'beams-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    surface.prepend(canvas);
    const context = canvas.getContext('2d');
    if (!context) {
      canvas.remove();
      return;
    }
    const state = { surface, canvas, context, width: 0, height: 0, beams: [], visible: false };
    surfaces.set(surface, state);
    resize(state);
    visibilityObserver.observe(surface);
    sizeObserver.observe(surface);
  };

  const attachAvailable = () => {
    document.querySelectorAll('.beams-surface').forEach(attach);
    if (surfaces.size >= 3) mountObserver.disconnect();
  };
  const mountObserver = new MutationObserver(attachAvailable);
  mountObserver.observe(document.body, { childList: true, subtree: true });
  attachAvailable();

  window.__careerBeamsCleanup = () => {
    if (frame) cancelAnimationFrame(frame);
    reducedMotion.removeEventListener('change', onMotionChange);
    document.removeEventListener('visibilitychange', onVisibilityChange);
    mountObserver.disconnect();
    visibilityObserver.disconnect();
    sizeObserver.disconnect();
    for (const state of surfaces.values()) state.canvas.remove();
    surfaces.clear();
  };
})();

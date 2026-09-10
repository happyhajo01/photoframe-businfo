/**
 * Slideshow engine with 8 transition effects.
 *
 * Effects: crossFade | slideLeft | slideRight | slideUp |
 *          zoomIn | zoomOut | fadeBlur | kenBurns
 *
 * Usage:
 *   const show = new Slideshow('#slideshow', { interval: 30000, effects: ['crossFade','zoomIn'] });
 *   show.load(mediaItems);  // [{ path, type }]
 *   show.start();
 */
class Slideshow {
  /**
   * @param {string}   containerSelector  CSS selector for the slideshow div
   * @param {object}   opts
   * @param {number}   opts.interval       ms between slides (default 30000)
   * @param {string[]} opts.effects        enabled effect names
   * @param {number}   opts.speed          transition duration ms (default 800)
   */
  constructor(containerSelector, opts = {}) {
    this._container = document.querySelector(containerSelector);
    this._interval  = opts.interval ?? 30000;
    this._effects   = opts.effects  ?? ['crossFade'];
    this._speed     = opts.speed    ?? 800;
    this._items     = [];
    this._index     = 0;
    this._timer     = null;
    this._slides    = [null, null];  // double-buffer: [current, next]
    this._animating = false;
    this._enabled   = true;
    this._dots      = null;
  }

  /** Load media items and build initial DOM. */
  load(items) {
    this._items = _shuffle([...items]);
    if (!this._items.length || !this._container) return;
    this._container.innerHTML = '';
    // Create two slide layers for crossfade / transitions
    for (let i = 0; i < 2; i++) {
      const el = document.createElement('div');
      el.className = 'slideshow__slide';
      this._container.appendChild(el);
      this._slides[i] = el;
    }
    // 동영상 종료 이벤트 → 다음 슬라이드로
    this._container.addEventListener('video-ended', () => {
      this.stop();          // 기존 타이머 취소
      this._advance(1);     // 즉시 다음으로
    });
    this._showSlide(0, null, true);
    this._buildDots();
  }

  start() {
    this._scheduleNext();
  }

  stop() {
    if (this._timer) { clearTimeout(this._timer); this._timer = null; }
  }

  next() { this._advance(1); }
  prev() { this._advance(-1); }

  setEffects(effects) { this._effects = effects.length ? effects : ['crossFade']; }
  setInterval(ms)     { this._interval = ms; }
  setSpeed(ms)        { this._speed = ms; }

  toggleEffects() {
    this._enabled = !this._enabled;
    return this._enabled;
  }

  // ─── Internal ──────────────────────────────────────────────────────────────

  _advance(dir) {
    if (this._animating || !this._items.length) return;
    const next = _randomOther(this._index, this._items.length);
    this._showSlide(next, _pick(this._effects));
    this._scheduleNext();
  }

  _scheduleNext() {
    this.stop();
    this._timer = setTimeout(() => this._advance(1), this._interval);
  }

  _showSlide(index, effect, instant = false) {
    if (!this._items.length) return;
    const item = this._items[index];
    this._index = index;

    const [cur, nxt] = this._slides;

    if (instant) {
      // Reset styles first, THEN set content so backgroundImage is not cleared
      nxt.style.cssText = 'opacity:1;transform:none;filter:none;';
      _setContent(nxt, item);
      cur.style.cssText = 'opacity:0;';
      this._slides = [nxt, cur];
      this._updateDots(index);
      return;
    }

    this._animating = true;
    const e = this._enabled ? (effect || 'crossFade') : 'crossFade';
    // Pass item so _applyTransition can set content after its own cssText reset
    _applyTransition(cur, nxt, item, e, this._speed, () => {
      this._slides = [nxt, cur];
      this._animating = false;
      this._updateDots(index);
    });
  }

  _buildDots() {
    const counter = document.getElementById('slideCounter');
    if (!counter || !this._items.length) return;
    this._dots = counter;
    const max = Math.min(this._items.length, 15);
    counter.innerHTML = '';
    for (let i = 0; i < max; i++) {
      const d = document.createElement('div');
      d.className = 'slide-dot' + (i === 0 ? ' active' : '');
      counter.appendChild(d);
    }
  }

  _updateDots(index) {
    if (!this._dots) return;
    const dots = this._dots.querySelectorAll('.slide-dot');
    dots.forEach((d, i) => d.classList.toggle('active', i === index % dots.length));
  }
}

// ─── Content setter ──────────────────────────────────────────────────────────

function _setContent(el, item) {
  el.innerHTML = '';

  // Blurred background — always an image (video uses poster or first frame fallback)
  const bg = document.createElement('div');
  bg.className = 'slideshow__blur-bg';
  bg.style.backgroundImage = `url('/static/${item.path}')`;
  el.appendChild(bg);

  // Main media element
  if (item.type === 'video') {
    const vid = document.createElement('video');
    vid.src = `/static/${item.path}`;
    vid.className = 'slideshow__media';
    vid.autoplay = true;
    vid.muted = true;
    vid.loop = false;      // 영상 끝나면 다음으로 넘어가야 하므로 loop 해제
    vid.playsInline = true;
    // 영상이 끝나면 다음 슬라이드로 자동 이동
    vid.addEventListener('ended', () => {
      el.dispatchEvent(new CustomEvent('video-ended', { bubbles: true }));
    }, { once: true });
    el.appendChild(vid);
  } else {
    const img = document.createElement('img');
    img.src = `/static/${item.path}`;
    img.className = 'slideshow__media';
    img.alt = '';
    img.addEventListener('load', () => {
      if (img.naturalWidth > img.naturalHeight) {
        // 가로 이미지: 하단 30px 띄움
        el.style.alignItems = 'flex-end';
        el.style.paddingBottom = '250px';
      }
    }, { once: true });
    el.appendChild(img);
  }
}

// ─── Transition implementations ──────────────────────────────────────────────

function _applyTransition(cur, nxt, item, effect, speed, done) {
  const s = speed;
  const ease = 'cubic-bezier(0.16,1,0.3,1)';

  // Reset inline styles FIRST, then set content so backgroundImage survives
  nxt.style.cssText = '';
  _setContent(nxt, item);
  nxt.style.opacity = '0';
  nxt.style.zIndex  = '2';
  cur.style.zIndex  = '1';

  const transitions = {
    crossFade() {
      nxt.style.transition = `opacity ${s}ms ${ease}`;
      cur.style.transition = `opacity ${s}ms ${ease}`;
      requestAnimationFrame(() => {
        nxt.style.opacity = '1';
        cur.style.opacity = '0';
        setTimeout(() => { cur.style.cssText = 'opacity:0;z-index:1'; done(); }, s);
      });
    },

    slideLeft() {
      nxt.style.transform = 'translateX(100%)';
      nxt.style.opacity   = '1';
      requestAnimationFrame(() => {
        nxt.style.transition = `transform ${s}ms ${ease}`;
        cur.style.transition = `transform ${s}ms ${ease}`;
        nxt.style.transform = 'translateX(0)';
        cur.style.transform = 'translateX(-30%)';
        setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
      });
    },

    slideRight() {
      nxt.style.transform = 'translateX(-100%)';
      nxt.style.opacity   = '1';
      requestAnimationFrame(() => {
        nxt.style.transition = `transform ${s}ms ${ease}`;
        cur.style.transition = `transform ${s}ms ${ease}`;
        nxt.style.transform = 'translateX(0)';
        cur.style.transform = 'translateX(30%)';
        setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
      });
    },

    slideUp() {
      nxt.style.transform = 'translateY(100%)';
      nxt.style.opacity   = '1';
      requestAnimationFrame(() => {
        nxt.style.transition = `transform ${s}ms ${ease}, opacity ${s}ms`;
        cur.style.transition = `transform ${s}ms ${ease}, opacity ${s}ms`;
        nxt.style.transform = 'translateY(0)';
        cur.style.opacity   = '0';
        setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
      });
    },

    zoomIn() {
      nxt.style.transform = 'scale(1.15)';
      nxt.style.opacity   = '0';
      requestAnimationFrame(() => {
        nxt.style.transition = `transform ${s}ms ${ease}, opacity ${s}ms`;
        cur.style.transition = `opacity ${s}ms`;
        nxt.style.transform = 'scale(1)';
        nxt.style.opacity   = '1';
        cur.style.opacity   = '0';
        setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
      });
    },

    zoomOut() {
      nxt.style.transform = 'scale(0.85)';
      nxt.style.opacity   = '0';
      requestAnimationFrame(() => {
        nxt.style.transition = `transform ${s}ms ${ease}, opacity ${s}ms`;
        cur.style.transition = `opacity ${s}ms`;
        nxt.style.transform = 'scale(1)';
        nxt.style.opacity   = '1';
        cur.style.opacity   = '0';
        setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
      });
    },

    fadeBlur() {
      nxt.style.filter  = 'blur(20px)';
      nxt.style.opacity = '0';
      requestAnimationFrame(() => {
        nxt.style.transition = `filter ${s}ms ${ease}, opacity ${s}ms`;
        cur.style.transition = `filter ${s}ms ${ease}, opacity ${s}ms`;
        nxt.style.filter  = 'blur(0)';
        nxt.style.opacity = '1';
        cur.style.filter  = 'blur(20px)';
        cur.style.opacity = '0';
        setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
      });
    },

    kenBurns() {
      // Slow zoom + pan on current while new fades in
      cur.style.transition = `transform ${s * 2}ms linear, opacity ${s}ms`;
      nxt.style.transition = `opacity ${s}ms`;
      cur.style.transform  = 'scale(1.08) translateX(-2%)';
      nxt.style.opacity    = '1';
      setTimeout(() => { cur.style.opacity = '0'; }, s * 0.5);
      setTimeout(() => { cur.style.cssText = 'opacity:0'; done(); }, s);
    },
  };

  (transitions[effect] || transitions.crossFade)();
}

function _shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function _pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

// 현재 인덱스와 다른 랜덤 인덱스 반환 (이미지 1장이면 0 반환)
function _randomOther(current, length) {
  if (length <= 1) return 0;
  let next;
  do { next = Math.floor(Math.random() * length); } while (next === current);
  return next;
}

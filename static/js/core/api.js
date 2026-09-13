/**
 * Centralised API client.
 * All fetch calls go through here so error handling, timeouts,
 * and retry logic are consistent across pages.
 */
const API = (() => {
  const TIMEOUT_MS = 8000;

  async function _fetch(url, opts = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const res = await fetch(url, { ...opts, signal: controller.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      if (err.name === 'AbortError') throw new Error('요청 시간 초과');
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  return {
    /** GET /api/weather — current + forecast + date info */
    weather: () => _fetch('/api/weather'),

    /** GET /api/bus?refresh=true/false */
    bus: (force = false) => _fetch(`/api/bus?refresh=${force}`),

    /** GET /api/commute?refresh=true/false */
    commute: (force = false) => _fetch(`/api/commute?refresh=${force}`),

    /** GET /api/settings */
    getSettings: () => _fetch('/api/settings'),

    /** POST /api/settings */
    saveSettings: (data) => _fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

    /** POST /api/restart — Flask 프로세스 재시작 (systemd가 자동 재기동) */
    restart: () => _fetch('/api/restart', { method: 'POST' }),

    /** GET /api/media */
    media: () => _fetch('/api/media'),

    /** GET /api/thumbnail?path=... */
    thumbnail: (path) => _fetch(`/api/thumbnail?path=${encodeURIComponent(path)}`),
  };
})();

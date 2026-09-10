/**
 * Clock module — updates time display elements every second.
 *
 * Usage:
 *   Clock.start({ time: '#clockTime', seconds: '#clockSeconds' });
 *   Clock.start({ time: '#busClock' });   // seconds element optional
 */
const Clock = (() => {
  let _interval = null;

  function _pad(n) { return String(n).padStart(2, '0'); }

  function _tick(timeEl, secEl) {
    const now = new Date();
    const h   = _pad(now.getHours());
    const m   = _pad(now.getMinutes());
    const s   = _pad(now.getSeconds());
    if (timeEl) timeEl.textContent = `${h}:${m}`;
    if (secEl)  secEl.textContent  = s;
  }

  return {
    /**
     * @param {{ time: string, seconds?: string }} selectors  CSS selectors
     */
    start(selectors) {
      const timeEl = document.querySelector(selectors.time);
      const secEl  = selectors.seconds ? document.querySelector(selectors.seconds) : null;
      if (!timeEl) return;
      _tick(timeEl, secEl);
      if (_interval) clearInterval(_interval);
      _interval = setInterval(() => _tick(timeEl, secEl), 1000);
    },

    stop() {
      if (_interval) { clearInterval(_interval); _interval = null; }
    },
  };
})();

/**
 * Bus stop page controller.
 * Renders a card per stop with real-time arrival rows.
 * Auto-returns to main after `autoReturnMinutes`.
 */
(async () => {
  const grid       = document.getElementById('stopsGrid');
  const refreshEl  = document.getElementById('refreshCountdown');
  const timerEl    = document.getElementById('autoReturnTimer');

  // ─── Settings ─────────────────────────────────────────────────────────────
  let settings = {};
  try { ({ app_settings: settings } = await API.getSettings()); } catch (_) {}
  const busInterval   = (settings.bus_update_interval ?? 60) * 1000;
  const returnMinutes = settings.auto_return_minutes ?? 20;

  // ─── Clock ────────────────────────────────────────────────────────────────
  Clock.start({ time: '#busClock' });

  // ─── Countdown display (다음 갱신 / 화면 복귀) ───────────────────────────────
  const returnAt = Date.now() + returnMinutes * 60000;
  let nextLoadAt = Date.now() + busInterval;

  function fmt(ms) {
    const secs = Math.max(0, Math.round(ms / 1000));
    return `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`;
  }

  setInterval(() => {
    refreshEl.textContent = fmt(nextLoadAt - Date.now());
    const returnMs = returnAt - Date.now();
    timerEl.textContent = fmt(returnMs);
    if (returnMs <= 0) location.href = '/';
  }, 1000);

  // ─── Load & render ─────────────────────────────────────────────────────────
  async function load(force = false) {
    try {
      const { stops } = await API.bus(force);
      grid.innerHTML = stops.length
        ? stops.map(renderStop).join('')
        : emptyMsg('정류소 설정이 없습니다');
    } catch (e) {
      console.warn('Bus load error:', e);
    } finally {
      nextLoadAt = Date.now() + busInterval;
      clearTimeout(loadTimer);
      loadTimer = setTimeout(() => load(true), busInterval);
    }
  }
  let loadTimer;

  function renderStop(stop) {
    const rows = stop.arrivals.length
      ? stop.arrivals.map(renderArrivalRow).join('')
      : `<div class="arrival-row arrival-row--empty">도착 정보 없음</div>`;
    return `
      <div class="stop-card card">
        <div class="stop-card__name">${esc(stop.name)}</div>
        ${rows}
      </div>`;
  }

  function renderArrivalRow(arrival) {
    const times = arrival.times.slice(0, 2);
    const rowUrgency = times.length ? times[0].urgency : 'normal';
    const timeCells = times.map(t => `
      <div class="arrival-time ${t.urgency}">
        <span class="arrival-time__label">${esc(t.label)}</span>
        ${t.nth ? `<span class="arrival-time__nth">${esc(t.nth)}</span>` : ''}
      </div>`).join('');
    return `
      <div class="arrival-row ${rowUrgency}">
        <span class="arrival-row__route">${esc(arrival.route)}</span>
        <span class="arrival-row__icon">🚌</span>
        <div class="arrival-times">${timeCells}</div>
      </div>`;
  }

  function emptyMsg(msg) {
    return `<div style="grid-column:1/-1;text-align:center;color:var(--color-text-muted);padding:40px">${msg}</div>`;
  }

  // ─── Public interface for refresh button ───────────────────────────────────
  window.busPage = { refresh: () => load(true) };

  // ─── Start ────────────────────────────────────────────────────────────────
  await load();
})();

function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

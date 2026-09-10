/**
 * Bus stop page controller.
 * Renders a card per stop with real-time arrival rows.
 * Auto-returns to main after `autoReturnMinutes`.
 */
(async () => {
  const grid      = document.getElementById('stopsGrid');
  const metaEl    = document.getElementById('updateMeta');
  const timerEl   = document.getElementById('autoReturnTimer');

  // ─── Settings ─────────────────────────────────────────────────────────────
  let settings = {};
  try { ({ app_settings: settings } = await API.getSettings()); } catch (_) {}
  const busInterval   = (settings.bus_update_interval ?? 60) * 1000;
  const returnMinutes = settings.auto_return_minutes ?? 20;

  // ─── Clock ────────────────────────────────────────────────────────────────
  Clock.start({ time: '#busClock' });

  // ─── Auto-return countdown ─────────────────────────────────────────────────
  let returnSecs = returnMinutes * 60;
  const returnTimer = setInterval(() => {
    returnSecs--;
    const m = Math.floor(returnSecs / 60);
    const s = String(returnSecs % 60).padStart(2, '0');
    timerEl.textContent = `자동 복귀: ${m}:${s}`;
    if (returnSecs <= 0) { clearInterval(returnTimer); location.href = '/'; }
  }, 1000);

  // ─── Load & render ─────────────────────────────────────────────────────────
  async function load(force = false) {
    try {
      const { stops } = await API.bus(force);
      metaEl.textContent = `${new Date().toLocaleTimeString('ko-KR')} 갱신`;
      grid.innerHTML = stops.length
        ? stops.map(renderStop).join('')
        : emptyMsg('정류소 설정이 없습니다');
    } catch (e) {
      metaEl.textContent = '갱신 실패';
      console.warn('Bus load error:', e);
    }
  }

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
  // force=true: 캐시가 폴링 주기와 같아 항상 HIT되는 문제 방지
  setInterval(() => load(true), busInterval);
})();

function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

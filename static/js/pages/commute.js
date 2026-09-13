/**
 * Commute page controller.
 * Shows 1 card per bus route with 2 arrival time cards side by side.
 * Tapping a time card triggers a ripple indicating urgency.
 */
(async () => {
  const grid      = document.getElementById('stopsGrid');
  const refreshEl = document.getElementById('refreshCountdown');
  const timerEl   = document.getElementById('autoReturnTimer');

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
      const { stops } = await API.commute(force);

      // Flatten: one card per (stop × route)
      const cards = [];
      for (const stop of stops) {
        for (const arrival of stop.arrivals) {
          cards.push({ stop: stop.name, arrival });
        }
      }
      if (cards.length) {
        grid.innerHTML = cards.map(renderCard).join('');
      } else if (!stops.length) {
        grid.innerHTML = `<div style="text-align:center;color:var(--color-text-muted);padding:60px">출근 정류소 설정이 없습니다</div>`;
      } else {
        grid.innerHTML = `<div style="text-align:center;color:var(--color-text-muted);padding:60px">도착 정보를 가져오는 중…</div>`;
      }
    } catch (e) {
      console.warn('Commute load error:', e);
    } finally {
      nextLoadAt = Date.now() + busInterval;
      clearTimeout(loadTimer);
      loadTimer = setTimeout(() => load(true), busInterval);
    }
  }
  let loadTimer;

  function renderCard({ stop, arrival }) {
    const times = arrival.times.slice(0, 2);
    const timeCells = times.length
      ? times.map(t => `
          <div class="commute-time-card ${t.urgency}" onclick="ripple(this, '${t.urgency}')">
            <div class="commute-time-card__label urgency--${t.urgency}">${esc(t.label)}</div>
            <div class="commute-time-card__sub">${esc(stop)} · ${t.nth ? esc(t.nth) : '다음 버스'}</div>
          </div>`).join('')
      : `<div class="commute-time-card" style="grid-column:1/-1;color:var(--color-text-muted)">정보 없음</div>`;

    return `
      <div class="commute-card card">
        <div class="commute-card__route">${esc(arrival.route)}</div>
        <div class="commute-times">${timeCells}</div>
      </div>`;
  }

  // ─── Public interface ──────────────────────────────────────────────────────
  window.commutePage = { refresh: () => load(true) };

  // ─── Start ────────────────────────────────────────────────────────────────
  await load();
})();

/** Ripple animation on tap */
function ripple(el, urgency) {
  el.classList.remove('ripple-urgent', 'ripple-ok');
  void el.offsetWidth; // reflow
  el.classList.add(urgency === 'urgent' ? 'ripple-urgent' : 'ripple-ok');
}

function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

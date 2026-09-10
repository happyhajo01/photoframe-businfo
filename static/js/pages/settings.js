/**
 * Settings page controller.
 * Loads current settings, builds editable rows, and POSTs on save.
 */
(async () => {
  const statusEl = document.getElementById('saveStatus');

  // ─── Load settings ─────────────────────────────────────────────────────────
  let data = { bus_stops: { stops: [] }, commute_stops: { stops: [] }, app_settings: {} };
  try {
    data = await API.getSettings();
  } catch (e) {
    setStatus('설정을 불러오지 못했습니다', 'error');
  }

  // ─── Render stop tables ────────────────────────────────────────────────────
  renderStops('busStopsBody',     data.bus_stops?.stops     ?? []);
  renderStops('commuteStopsBody', data.commute_stops?.stops ?? []);

  // ─── Render app settings ───────────────────────────────────────────────────
  const s = data.app_settings ?? {};
  setValue('photoInterval',          s.photo_interval            ?? 30);
  setValue('busUpdateInterval',      s.bus_update_interval       ?? 60);
  setValue('autoReturnMinutes',      s.auto_return_minutes       ?? 20);
  setValue('weatherUpdateInterval',  Math.round((s.weather_update_interval ?? 1800) / 60));
  setValue('monitorOffTime',         s.monitor_off_time          ?? '23:50');
  setValue('monitorOnTime',          s.monitor_on_time           ?? '05:10');
  setValue('transitionSpeed',        s.transition_speed          ?? 800);

  // ─── Effect chips ──────────────────────────────────────────────────────────
  const activeEffects = new Set(s.slideshow_effects ?? ['crossFade','slideLeft','slideRight','zoomIn','zoomOut','fadeBlur']);
  document.querySelectorAll('.chip[data-effect]').forEach(chip => {
    if (activeEffects.has(chip.dataset.effect)) chip.classList.add('active');
    chip.addEventListener('click', () => chip.classList.toggle('active'));
  });

  // ─── Save ──────────────────────────────────────────────────────────────────
  window.settingsPage = {
    addBusStop:     () => addStopRow('busStopsBody'),
    addCommuteStop: () => addStopRow('commuteStopsBody'),
    save,
  };

  async function save() {
    setStatus('저장 중…', '');
    try {
      const payload = buildPayload();
      const res = await API.saveSettings(payload);
      setStatus(res.message ?? '저장 완료', res.ok ? 'success' : 'error');
    } catch (e) {
      setStatus('저장 중 오류 발생', 'error');
    }
  }

  // ─── Helpers ───────────────────────────────────────────────────────────────

  function renderStops(tbodyId, stops) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = '';
    stops.forEach(stop => addStopRow(tbodyId, stop));
  }

  function addStopRow(tbodyId, stop = {}) {
    const tbody = document.getElementById(tbodyId);
    const tr = document.createElement('tr');
    tr.className = 'stop-row';
    tr.innerHTML = `
      <td><input class="settings-input" type="text" placeholder="정류소 이름" value="${esc(stop.name ?? '')}"></td>
      <td><input class="settings-input" type="text" placeholder="정류소 ID" value="${esc(stop.id ?? '')}"></td>
      <td><input class="settings-input" type="text" placeholder="1143, 1137" value="${esc((stop.buses ?? []).join(', '))}"></td>
      <td><button class="btn btn--danger" onclick="this.closest('tr').remove()" aria-label="삭제">삭제</button></td>`;
    tbody.appendChild(tr);
    // Focus first empty input
    const first = tr.querySelector('input[value=""]');
    if (first) first.focus();
  }

  function buildPayload() {
    return {
      bus_stops:     { stops: collectStops('busStopsBody') },
      commute_stops: { stops: collectStops('commuteStopsBody') },
      app_settings: {
        photo_interval:           numVal('photoInterval'),
        bus_update_interval:      numVal('busUpdateInterval'),
        auto_return_minutes:      numVal('autoReturnMinutes'),
        weather_update_interval:  numVal('weatherUpdateInterval') * 60,
        monitor_off_time:         strVal('monitorOffTime'),
        monitor_on_time:          strVal('monitorOnTime'),
        transition_speed:         numVal('transitionSpeed'),
        slideshow_effects: [...document.querySelectorAll('.chip.active[data-effect]')]
          .map(c => c.dataset.effect),
      },
    };
  }

  function collectStops(tbodyId) {
    return [...document.querySelectorAll(`#${tbodyId} .stop-row`)].map(row => {
      const inputs = row.querySelectorAll('input');
      return {
        name:  inputs[0].value.trim(),
        id:    inputs[1].value.trim(),
        buses: inputs[2].value.split(',').map(b => b.trim()).filter(Boolean),
      };
    }).filter(s => s.name && s.id);
  }

  function setValue(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
  }
  function numVal(id) { return Number(document.getElementById(id)?.value ?? 0); }
  function strVal(id) { return document.getElementById(id)?.value ?? ''; }

  function setStatus(msg, cls) {
    statusEl.textContent = msg;
    statusEl.className   = 'settings-save-bar__status' + (cls ? ` ${cls}` : '');
  }

  // Keyboard shortcut Ctrl+S → save
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); save(); }
  });
})();

function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, c =>
    ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

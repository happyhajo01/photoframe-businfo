/**
 * Main page controller.
 * Orchestrates the clock, slideshow, weather display, and night mode.
 */
(async () => {
  // ─── Elements ──────────────────────────────────────────────────────────────
  const dateEl    = document.getElementById('dateDisplay');
  const dayEl     = document.getElementById('dayDisplay');
  const iconEl    = document.getElementById('weatherIcon');
  const tempEl    = document.getElementById('weatherTemp');
  const forecastEl= document.getElementById('forecastBlock');
  const effectBtn = document.getElementById('effectToggle');
  const nightEl   = document.getElementById('nightOverlay');
  const wifiEl    = document.getElementById('wifiStatus');

  // ─── Settings ─────────────────────────────────────────────────────────────
  let settings = {};
  try { ({ app_settings: settings } = await API.getSettings()); } catch (_) {}
  const photoInterval    = (settings.photo_interval    ?? 30)   * 1000;
  const weatherInterval  = (settings.weather_update_interval ?? 1800) * 1000;
  const transitionSpeed  = settings.transition_speed  ?? 800;
  const effects          = settings.slideshow_effects ?? ['crossFade', 'slideLeft', 'slideRight', 'zoomIn', 'zoomOut', 'fadeBlur'];

  // ─── Clock ────────────────────────────────────────────────────────────────
  Clock.start({ time: '#clockTime', seconds: '#clockSeconds' });

  // ─── Slideshow ────────────────────────────────────────────────────────────
  const show = new Slideshow('#slideshow', {
    interval: photoInterval,
    effects,
    speed: transitionSpeed,
  });

  // 화면이 DPMS로 꺼져있는 동안(monitor_off_time~monitor_on_time)에는 아무도 안 보므로
  // 슬라이드쇼/날씨·와이파이 폴링을 멈춰 라즈베리파이의 불필요한 작업을 줄인다.
  function isMonitorOff() {
    const start = settings.monitor_off_time ?? '23:50';
    const end   = settings.monitor_on_time  ?? '05:10';
    const now = new Date();
    const cur = now.getHours() * 60 + now.getMinutes();
    const [sh, sm] = start.split(':').map(Number);
    const [eh, em] = end.split(':').map(Number);
    const s = sh * 60 + sm, e = eh * 60 + em;
    return s > e ? (cur >= s || cur < e) : (cur >= s && cur < e);
  }
  let systemPaused = isMonitorOff();

  try {
    const { items } = await API.media();
    if (items.length) {
      show.load(items);
      if (!systemPaused) show.start();
    }
  } catch (e) {
    console.warn('Media load failed:', e);
  }

  // Effect toggle button
  effectBtn.addEventListener('click', () => {
    const on = show.toggleEffects();
    effectBtn.textContent = on ? '✨' : '▶';
    effectBtn.title = on ? '효과 끄기' : '효과 켜기';
  });

  // Keyboard controls
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') show.next();
    if (e.key === 'ArrowLeft')  show.prev();
    if (e.key === ' ') { e.preventDefault(); show.toggleEffects(); }
  });

  // ─── Weather ──────────────────────────────────────────────────────────────
  async function loadWeather() {
    if (systemPaused) return;
    try {
      const data = await API.weather();

      // Date & day
      const { full, day, is_sat, is_sun, holiday } = data.date;
      dateEl.textContent = full;
      dayEl.textContent  = holiday || day;
      dayEl.className    = 'date-block__day' +
        (holiday || is_sun ? ' holiday' : is_sat ? ' saturday' : '');

      // Current weather
      const cur = data.current;
      iconEl.src         = `/static/images/weather/${cur.icon}`;
      iconEl.alt         = cur.label;
      tempEl.textContent = `${cur.temperature}°C`;

      // 3-day forecast
      forecastEl.innerHTML = data.forecast.map(f => `
        <div class="forecast-item">
          <span class="forecast-item__date">${f.date}<br><span>${f.day}</span></span>
          <img src="/static/images/weather/${f.icon}" width="56" height="56" alt="${f.label}">
          <div class="forecast-item__temp">
            <span class="forecast-item__max">${f.max}°</span>
            <span class="forecast-item__min">${f.min}°</span>
          </div>
        </div>
      `).join('');
    } catch (e) {
      console.warn('Weather load failed:', e);
    }
  }

  loadWeather();
  setInterval(loadWeather, weatherInterval);

  // ─── Wi-Fi status ─────────────────────────────────────────────────────────
  async function loadNetwork() {
    if (systemPaused) return;
    try {
      const { connected } = await API.network();
      wifiEl.textContent = connected ? '📶' : '📵';
      wifiEl.classList.toggle('offline', !connected);
    } catch (e) {
      wifiEl.textContent = '📵';
      wifiEl.classList.add('offline');
    }
  }

  loadNetwork();
  setInterval(loadNetwork, 20000);

  // ─── Night mode ────────────────────────────────────────────────────────────
  function checkNightMode() {
    const start = settings.night_mode_start ?? '00:00';
    const end   = settings.night_mode_end   ?? '06:00';
    const now   = new Date();
    const cur   = now.getHours() * 60 + now.getMinutes();
    const [sh, sm] = start.split(':').map(Number);
    const [eh, em] = end.split(':').map(Number);
    const s = sh * 60 + sm, e = eh * 60 + em;
    const isNight = s > e ? (cur >= s || cur < e) : (cur >= s && cur < e);
    nightEl.classList.toggle('active', isNight);
  }

  checkNightMode();
  setInterval(checkNightMode, 60000);

  // ─── Monitor-off power saving ───────────────────────────────────────────────
  function checkMonitorOff() {
    const off = isMonitorOff();
    if (off === systemPaused) return;
    systemPaused = off;
    if (off) {
      show.stop();
    } else {
      show.start();
      loadWeather();
      loadNetwork();
    }
  }

  setInterval(checkMonitorOff, 60000);
})();

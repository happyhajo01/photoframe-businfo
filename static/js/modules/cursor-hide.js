/**
 * 마우스를 일정 시간 움직이지 않으면 커서를 숨긴다 (키오스크 화면용).
 */
(function () {
  const HIDE_AFTER_MS = 60000;
  let timer;

  function showCursor() {
    document.documentElement.classList.remove('hide-cursor');
    clearTimeout(timer);
    timer = setTimeout(() => document.documentElement.classList.add('hide-cursor'), HIDE_AFTER_MS);
  }

  document.addEventListener('mousemove', showCursor, { passive: true });
  showCursor();
})();

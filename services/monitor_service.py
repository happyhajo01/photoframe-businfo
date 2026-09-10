"""
Monitor power control using DPMS (Display Power Management Signaling).
Priority: vcgencmd (RPi HW) → wlopm (Wayland) → xset (X11) → wlr-randr (last resort)

DPMS 기반을 사용하는 이유: wlr-randr --off 는 Wayland 컴포지터가 출력 자체를
비활성화해 창이 사라지고 Chromium이 복구 불가 상태가 된다.
DPMS는 화면 신호만 차단하므로 컴포지터와 브라우저 상태가 유지된다.
"""

import glob
import logging
import subprocess

from config.settings import MONITOR_ENABLED, MONITOR_OUTPUT

logger = logging.getLogger(__name__)


class MonitorService:
    def turn_on(self) -> bool:
        self._set_backlight(True)
        return self._dpms("on")

    def turn_off(self) -> bool:
        result = self._dpms("off")
        self._set_backlight(False)
        return result

    def _set_backlight(self, on: bool) -> None:
        for path in glob.glob('/sys/class/backlight/*/brightness'):
            try:
                if on:
                    max_path = path.replace('brightness', 'max_brightness')
                    with open(max_path) as f:
                        val = f.read().strip()
                else:
                    val = '0'
                with open(path, 'w') as f:
                    f.write(val)
                logger.debug("Backlight %s via %s", "on" if on else "off", path)
            except OSError:
                pass

    def _dpms(self, action: str) -> bool:
        if not MONITOR_ENABLED:
            logger.debug("Monitor control disabled, skipping: %s", action)
            return True

        on = action == "on"

        # 1. vcgencmd — RPi VideoCore 하드웨어 레벨 (컴포지터 상태 유지, 가장 안전)
        if self._run(["vcgencmd", "display_power", "1" if on else "0"]):
            logger.debug("Monitor %s via vcgencmd", action)
            return True

        # 2. wlopm — Wayland output power management (DPMS, 창 유지)
        if self._run(["wlopm", "--on" if on else "--off", MONITOR_OUTPUT]):
            logger.debug("Monitor %s via wlopm", action)
            return True

        # 3. xset DPMS — X11 (창 유지)
        if self._run(["xset", "dpms", "force", "on" if on else "off"]):
            logger.debug("Monitor %s via xset dpms", action)
            return True

        # 4. wlr-randr — 최후 수단 (출력 비활성화, 창 배치가 흐트러질 수 있음)
        logger.warning("DPMS 명령 전부 실패 — wlr-randr %s 폴백 사용 (창 배치 초기화 가능)", action)
        return self._run(["wlr-randr", "--output", MONITOR_OUTPUT, "--on" if on else "--off"])

    def _run(self, cmd: list[str]) -> bool:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

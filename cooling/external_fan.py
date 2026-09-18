"""
외부 릴레이 팬 제어 진입점.
`python -m cooling.external_fan` 로 직접 실행하거나 external-fan.service(systemd)로 상시 실행한다.

SoC 온도가 EXTERNAL_FAN_ON_TEMP 이상이면 GPIO를 켜서(트랜지스터 → 릴레이 코일 구동)
외부 5V 팬 전원을 연결하고, EXTERNAL_FAN_OFF_TEMP 밑으로 떨어지면 끈다.
켜짐/꺼짐 온도를 다르게 둬(히스테리시스) 온도가 경계값 근처에서 오갈 때
릴레이가 잦게 딸깍거리는 것을 막는다. 배선은 INSTALL_GUIDE.md 참고.
"""

import logging
import time
from pathlib import Path

from gpiozero import DigitalOutputDevice

from config.settings import (
    EXTERNAL_FAN_GPIO_PIN,
    EXTERNAL_FAN_OFF_TEMP,
    EXTERNAL_FAN_ON_TEMP,
    EXTERNAL_FAN_POLL_SEC,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

_THERMAL_ZONE = Path("/sys/class/thermal/thermal_zone0/temp")


def _read_temp_c() -> float | None:
    try:
        return int(_THERMAL_ZONE.read_text().strip()) / 1000
    except (OSError, ValueError):
        return None


def main():
    relay = DigitalOutputDevice(EXTERNAL_FAN_GPIO_PIN, active_high=True, initial_value=False)
    fan_on = False
    logger.info(
        "외부 팬 제어 시작 (GPIO%d, ON=%.1f°C OFF=%.1f°C, %.0f초 간격)",
        EXTERNAL_FAN_GPIO_PIN, EXTERNAL_FAN_ON_TEMP, EXTERNAL_FAN_OFF_TEMP, EXTERNAL_FAN_POLL_SEC,
    )

    try:
        while True:
            temp = _read_temp_c()
            if temp is None:
                logger.warning("온도 읽기 실패 — 다음 주기에 재시도")
            elif not fan_on and temp >= EXTERNAL_FAN_ON_TEMP:
                relay.on()
                fan_on = True
                logger.info("외부 팬 ON (%.1f°C)", temp)
            elif fan_on and temp <= EXTERNAL_FAN_OFF_TEMP:
                relay.off()
                fan_on = False
                logger.info("외부 팬 OFF (%.1f°C)", temp)
            time.sleep(EXTERNAL_FAN_POLL_SEC)
    finally:
        relay.off()  # 서비스 종료 시 팬을 켜진 채로 방치하지 않음


if __name__ == "__main__":
    main()

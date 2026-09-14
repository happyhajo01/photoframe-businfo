"""
Pi Vitals 진입점.
`python -m display.pi_vitals` 로 직접 실행하거나 pi-vitals.service(systemd)로 상시 실행한다.
ST7789 모듈이나 st7789 패키지가 아직 없으면 자동으로 드라이런 모드로 전환해
렌더링 결과를 미리보기 이미지로 저장한다 — 화면 도착 전에도 로직을 확인할 수 있다.
매 틱마다 쓰는 파일이라 SSD가 아닌 /dev/shm(RAM, tmpfs)에 저장해 디스크 쓰기를 만들지 않는다.
"""

import logging
import time
from pathlib import Path

from config.settings import (
    BASE_DIR,
    PI_VITALS_DIRECTION,
    PI_VITALS_DISK_DEVICE,
    PI_VITALS_GPIO_BL,
    PI_VITALS_GPIO_DC,
    PI_VITALS_GPIO_RST,
    PI_VITALS_ORIENTATION,
    PI_VITALS_REFRESH_SEC,
    PI_VITALS_SPI_DEVICE,
    PI_VITALS_SPI_PORT,
    PI_VITALS_STYLE,
)
from display import renderer
from display.sensors import Sensors

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# /dev/shm(tmpfs, RAM)이 있으면 그쪽에 저장해 SSD 쓰기 마모를 피한다.
# 없는 환경(비-Linux 개발 PC 등)에서는 data/ 아래로 대체한다.
_SHM = Path("/dev/shm")
PREVIEW_PATH = (_SHM if _SHM.is_dir() else BASE_DIR / "data") / "pi_vitals_preview.png"


def _geometry() -> tuple[int, int, int, int, int]:
    """(width, height, rotation, offset_left, offset_top)을 반환한다.

    width/height는 패널의 실제 제조 방향(세로, 172x320) 기준이다.
    rotation은 st7789 라이브러리 규약(0/90/180/270)을 따른다.
    이 패널(GMT1475SPI, Waveshare 1.47인치 계열)은 컨트롤러 GRAM(240x320) 대비
    좌우 34px 오프셋이 있음 — st7789 라이브러리는 240x240/240x135 등만 자동
    인식하고 172x320은 offset 0으로 처리해 화면에 아무것도 안 그려지므로 직접 지정한다.
    가로 모드(offset_top=34)는 실기기로 검증 안 됨 — 확인 필요.
    """
    if PI_VITALS_ORIENTATION == "landscape":
        rotation = 90 if PI_VITALS_DIRECTION == "left" else 270
        return 172, 320, rotation, 0, 34
    return 172, 320, 0, 34, 0


def _init_device():
    try:
        import st7789
    except ImportError:
        logger.warning("st7789 패키지 없음 — 드라이런 모드로 전환 (pip install st7789 필요)")
        return None

    width, height, rotation, offset_left, offset_top = _geometry()
    try:
        device = st7789.ST7789(
            port=PI_VITALS_SPI_PORT,
            cs=PI_VITALS_SPI_DEVICE,
            dc=PI_VITALS_GPIO_DC,
            rst=PI_VITALS_GPIO_RST,
            backlight=PI_VITALS_GPIO_BL,
            width=width,
            height=height,
            rotation=rotation,
            offset_left=offset_left,
            offset_top=offset_top,
            # 점퍼선 배선 기준 60MHz는 너무 빨라 초기화 명령이 깨질 수 있음 — 우선 낮은 속도로 검증
            spi_speed_hz=4_000_000,
        )
        device.begin()

        # 설치된 st7789 라이브러리는 정사각형(240x240류) 패널을 가정하고 초기화 시 MADCTL을
        # 0x70(행/열 교환, MV=1)으로 고정한다. 172x320처럼 가로/세로가 다른 패널에서는 이 교환
        # 때문에 set_window()가 넣는 X/Y 좌표가 패널 내부에서 뒤바뀌어 그림이 화면 밖에 그려져
        # 아무것도 안 보이게 된다. MADCTL을 다시 써서 행/열 교환을 끈다(MV=0).
        device.command(0x36)  # MADCTL
        device.data(0x00)

        return device
    except Exception:
        logger.exception("ST7789 초기화 실패 — 드라이런 모드로 전환 (배선/SPI 활성화 확인)")
        return None


def main():
    device = _init_device()
    sensors = Sensors(disk_device=PI_VITALS_DISK_DEVICE)

    if device is None:
        PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.info("드라이런: %s 에 매 틱마다 저장합니다", PREVIEW_PATH)

    while True:
        data = sensors.read()
        image = renderer.render(data, PI_VITALS_ORIENTATION, PI_VITALS_STYLE)

        if device is not None:
            device.display(image)
        else:
            image.save(PREVIEW_PATH)

        time.sleep(PI_VITALS_REFRESH_SEC)


if __name__ == "__main__":
    main()

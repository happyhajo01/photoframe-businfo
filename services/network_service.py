"""
Wi-Fi 연결 및 상태 조회 (NetworkManager의 nmcli 사용, Raspberry Pi OS 기본).
.env에 WIFI_SSID가 설정돼 있으면 앱 시작 시 자동으로 연결을 시도한다.
"""

import logging
import subprocess

from config.settings import WIFI_PASSWORD, WIFI_SSID

logger = logging.getLogger(__name__)


class NetworkService:
    def connect(self) -> None:
        """설정된 Wi-Fi에 연결을 시도한다. 이미 같은 SSID에 연결돼 있으면 아무것도 하지 않는다."""
        if not WIFI_SSID:
            return

        status = self.get_status()
        if status["connected"] and status["ssid"] == WIFI_SSID:
            logger.info("[Network] 이미 '%s'에 연결됨", WIFI_SSID)
            return

        logger.info("[Network] '%s' 연결 시도", WIFI_SSID)
        cmd = ["nmcli", "device", "wifi", "connect", WIFI_SSID]
        if WIFI_PASSWORD:
            cmd += ["password", WIFI_PASSWORD]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30, text=True)
            if result.returncode == 0:
                logger.info("[Network] '%s' 연결 성공", WIFI_SSID)
            else:
                logger.warning("[Network] '%s' 연결 실패: %s", WIFI_SSID, result.stderr.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("[Network] nmcli 실행 불가: %s", e)

    def get_status(self) -> dict:
        """현재 Wi-Fi 연결 상태를 반환한다. nmcli가 없으면 연결 안 됨으로 취급한다."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device", "status"],
                capture_output=True, timeout=5, text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3 and parts[0] == "wifi" and parts[1] == "connected":
                        return {"connected": True, "ssid": parts[2]}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return {"connected": False, "ssid": None}

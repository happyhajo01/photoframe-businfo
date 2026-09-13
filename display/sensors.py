"""
Pi Vitals용 시스템 센서 수집.
CPU/메모리는 psutil, 온도는 thermal_zone, 팬은 hwmon(pwmfan), 디스크 활동은
/proc/diskstats 두 샘플의 차분으로 계산한다.
"""

import glob
import shutil
import socket
import time

import psutil

_THERMAL_ZONE = "/sys/class/thermal/thermal_zone0/temp"


class Sensors:
    def __init__(self, disk_device: str = "sda", disk_path: str = "/"):
        self._disk_device = disk_device
        self._disk_path = disk_path
        self._fan_dir = self._find_fan_hwmon()
        self._prev_disk_sectors: int | None = None
        self._prev_disk_time: float | None = None
        self._ip = self._detect_ip()
        psutil.cpu_percent(interval=None)  # 첫 호출은 기준점만 잡음(프라이밍)

    def read(self) -> dict:
        return {
            "cpu_pct": psutil.cpu_percent(interval=None),
            "temp_c": self._read_temp(),
            "ip": self._ip,
            "uptime_s": time.time() - psutil.boot_time(),
            **self._read_mem(),
            **self._read_disk(),
            **self._read_fan(),
        }

    # ─── 네트워크 ────────────────────────────────────────────────────────────
    def _detect_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # 실제 전송 없이 라우팅 인터페이스만 확인
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "0.0.0.0"

    # ─── CPU 온도 ────────────────────────────────────────────────────────────
    def _read_temp(self) -> float | None:
        try:
            with open(_THERMAL_ZONE) as f:
                return int(f.read().strip()) / 1000
        except OSError:
            return None

    # ─── 메모리 ──────────────────────────────────────────────────────────────
    def _read_mem(self) -> dict:
        vm = psutil.virtual_memory()
        return {
            "ram_pct": vm.percent,
            "ram_used_mb": round(vm.used / 1_048_576),
            "ram_total_mb": round(vm.total / 1_048_576),
        }

    # ─── 디스크 용량 + 활동(초당 전송량) ─────────────────────────────────────
    def _read_disk(self) -> dict:
        usage = shutil.disk_usage(self._disk_path)
        result = {
            "disk_pct": usage.used / usage.total * 100,
            "disk_used_gb": usage.used / 1_073_741_824,
            "disk_total_gb": usage.total / 1_073_741_824,
            "disk_kbps": 0.0,
        }
        sectors = self._read_disk_sectors()
        now = time.monotonic()
        if sectors is not None and self._prev_disk_sectors is not None:
            elapsed = now - self._prev_disk_time
            if elapsed > 0:
                delta_sectors = sectors - self._prev_disk_sectors
                result["disk_kbps"] = max(0.0, delta_sectors * 512 / 1024 / elapsed)
        self._prev_disk_sectors, self._prev_disk_time = sectors, now
        return result

    def _read_disk_sectors(self) -> int | None:
        try:
            with open("/proc/diskstats") as f:
                for line in f:
                    fields = line.split()
                    if fields[2] == self._disk_device:
                        # 필드: ... reads_completed reads_merged sectors_read ...
                        #       ... writes_completed writes_merged sectors_written ...
                        return int(fields[5]) + int(fields[9])
        except (OSError, IndexError, ValueError):
            pass
        return None

    # ─── 팬 RPM / PWM (라즈베리파이5 정식 액티브 쿨러 hwmon) ──────────────────
    def _find_fan_hwmon(self) -> str | None:
        for name_path in glob.glob("/sys/class/hwmon/hwmon*/name"):
            try:
                with open(name_path) as f:
                    if f.read().strip() == "pwmfan":
                        return name_path.rsplit("/", 1)[0]
            except OSError:
                continue
        return None

    def _read_fan(self) -> dict:
        if not self._fan_dir:
            return {"fan_rpm": None, "fan_pwm": None}
        try:
            with open(f"{self._fan_dir}/fan1_input") as f:
                rpm = int(f.read().strip())
            with open(f"{self._fan_dir}/pwm1") as f:
                pwm = int(f.read().strip())
            return {"fan_rpm": rpm, "fan_pwm": pwm}
        except OSError:
            return {"fan_rpm": None, "fan_pwm": None}

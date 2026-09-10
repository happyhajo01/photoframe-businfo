"""
Persistent settings and data management.
All application settings are stored as JSON files in the data/ directory.
"""

import json
import logging
from pathlib import Path
from typing import Any

from config.settings import (
    BUS_STOPS_FILE,
    COMMUTE_STOPS_FILE,
    APP_SETTINGS_FILE,
    DEFAULT_APP_SETTINGS,
)

logger = logging.getLogger(__name__)

_DEFAULT_BUS_STOPS = {"stops": []}
_DEFAULT_COMMUTE_STOPS = {"stops": []}


def _load(path: Path, default: dict) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load %s: %s", path, e)
    return default.copy()


def _save(path: Path, data: dict) -> tuple[bool, str]:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, "저장 완료"
    except OSError as e:
        logger.error("Failed to save %s: %s", path, e)
        return False, f"저장 실패: {e}"


class DataService:
    # ─── Bus Stops ───────────────────────────────────────────────────────────

    def get_bus_stops(self) -> dict:
        return _load(BUS_STOPS_FILE, _DEFAULT_BUS_STOPS)

    def save_bus_stops(self, data: dict) -> tuple[bool, str]:
        ok, msg = _validate_stops(data)
        if not ok:
            return False, msg
        return _save(BUS_STOPS_FILE, data)

    # ─── Commute Stops ───────────────────────────────────────────────────────

    def get_commute_stops(self) -> dict:
        return _load(COMMUTE_STOPS_FILE, _DEFAULT_COMMUTE_STOPS)

    def save_commute_stops(self, data: dict) -> tuple[bool, str]:
        ok, msg = _validate_stops(data)
        if not ok:
            return False, msg
        return _save(COMMUTE_STOPS_FILE, data)

    # ─── App Settings ────────────────────────────────────────────────────────

    def get_app_settings(self) -> dict:
        stored = _load(APP_SETTINGS_FILE, {})
        return {**DEFAULT_APP_SETTINGS, **stored}

    def save_app_settings(self, data: dict) -> tuple[bool, str]:
        ok, msg = _validate_app_settings(data)
        if not ok:
            return False, msg
        return _save(APP_SETTINGS_FILE, data)

    # ─── Combined ────────────────────────────────────────────────────────────

    def get_all(self) -> dict:
        return {
            "bus_stops":     self.get_bus_stops(),
            "commute_stops": self.get_commute_stops(),
            "app_settings":  self.get_app_settings(),
        }

    def save_all(self, data: dict) -> tuple[bool, str]:
        errors = []
        if "bus_stops" in data:
            ok, msg = self.save_bus_stops(data["bus_stops"])
            if not ok:
                errors.append(f"버스정류소: {msg}")
        if "commute_stops" in data:
            ok, msg = self.save_commute_stops(data["commute_stops"])
            if not ok:
                errors.append(f"출근정류소: {msg}")
        if "app_settings" in data:
            ok, msg = self.save_app_settings(data["app_settings"])
            if not ok:
                errors.append(f"앱설정: {msg}")
        if errors:
            return False, " / ".join(errors)
        return True, "모든 설정 저장 완료"


# ─── Validators ──────────────────────────────────────────────────────────────

def _validate_stops(data: Any) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "데이터 형식 오류"
    stops = data.get("stops")
    if not isinstance(stops, list):
        return False, "'stops' 배열이 없습니다"
    for i, stop in enumerate(stops):
        if not isinstance(stop, dict):
            return False, f"정류소 {i}: 객체 형식이어야 합니다"
        if not stop.get("name"):
            return False, f"정류소 {i}: 이름이 없습니다"
        if not stop.get("id"):
            return False, f"정류소 {i}: ID가 없습니다"
        if not isinstance(stop.get("buses", []), list):
            return False, f"정류소 {i}: buses는 배열이어야 합니다"
    return True, ""


def _validate_app_settings(data: Any) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "설정 데이터 형식 오류"
    int_keys = ["photo_interval", "bus_update_interval", "auto_return_minutes"]
    for key in int_keys:
        if key in data and not isinstance(data[key], (int, float)):
            return False, f"'{key}'는 숫자여야 합니다"
    return True, ""

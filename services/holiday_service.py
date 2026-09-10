"""
Korean public holiday data from the Korea Astronomy and Space Science Institute API.
Holidays are cached for 24 hours.
"""

import json
import logging
import time
from datetime import datetime

import requests

from config.settings import (
    HOLIDAY_API_KEY,
    HOLIDAY_API_URL,
    HOLIDAY_CACHE_FILE,
    HOLIDAY_CACHE_TTL,
    TEST_MODE,
)

logger = logging.getLogger(__name__)


class HolidayService:
    def __init__(self):
        self._cache: dict[str, str] = {}  # "YYYYMMDD" → holiday name
        self._cache_time: float = 0.0

    def is_holiday(self, date: datetime) -> str | None:
        """Return holiday name if date is a public holiday, else None."""
        holidays = self._load(date.year)
        return holidays.get(date.strftime("%Y%m%d"))

    def _load(self, year: int) -> dict[str, str]:
        now = time.time()
        if self._cache and now - self._cache_time < HOLIDAY_CACHE_TTL:
            return self._cache

        if HOLIDAY_CACHE_FILE.exists():
            try:
                disk = json.loads(HOLIDAY_CACHE_FILE.read_text(encoding="utf-8"))
                if now - disk.get("saved_at", 0) < HOLIDAY_CACHE_TTL:
                    self._cache = disk.get("holidays", {})
                    self._cache_time = disk["saved_at"]
                    return self._cache
            except (json.JSONDecodeError, OSError):
                pass

        fresh = self._fetch(year)
        self._cache = fresh
        self._cache_time = now
        try:
            HOLIDAY_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            HOLIDAY_CACHE_FILE.write_text(
                json.dumps({"saved_at": now, "holidays": fresh}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass
        return fresh

    def _fetch(self, year: int) -> dict[str, str]:
        if TEST_MODE or not HOLIDAY_API_KEY:
            return _dummy_holidays(year)
        try:
            resp = requests.get(
                HOLIDAY_API_URL,
                params={
                    "ServiceKey": HOLIDAY_API_KEY,
                    "solYear": year,
                    "numOfRows": 100,
                    "resultType": "json",
                },
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(items, dict):
                items = [items]
            return {str(it["locdate"]): it["dateName"] for it in items}
        except Exception as e:
            logger.warning("Holiday API error: %s", e)
            return {}


def _dummy_holidays(year: int) -> dict[str, str]:
    return {
        f"{year}0101": "신정",
        f"{year}0301": "삼일절",
        f"{year}0505": "어린이날",
        f"{year}0815": "광복절",
        f"{year}1003": "개천절",
        f"{year}1009": "한글날",
        f"{year}1225": "크리스마스",
    }

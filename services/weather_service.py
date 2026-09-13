"""
Weather data from Korean Meteorological Administration (KMA) Open API.
Ultra-short-range forecast (getUltraSrtFcst) is fetched and cached.
"""

import json
import logging
import time
from datetime import datetime, timedelta

import requests

from config.settings import (
    WEATHER_API_KEY,
    WEATHER_API_URL,
    WEATHER_CACHE_FILE,
    WEATHER_CACHE_TTL,
    WEATHER_NX,
    WEATHER_NY,
    TEST_MODE,
)

logger = logging.getLogger(__name__)

# Maps (sky_code, precipitation_code, is_daytime) → icon filename
_ICON_MAP = {
    # Sky: 1=맑음  3=구름많음  4=흐림
    # PTY: 0=없음  1=비  2=비/눈  3=눈  4=소나기
    (1, 0, True):  ("sunny_day",           "맑음"),
    (1, 0, False): ("clear_night",         "맑음"),
    (3, 0, True):  ("mostly_cloudy_day",   "구름 많음"),
    (3, 0, False): ("mostly_cloudy_night", "구름 많음"),
    (4, 0, True):  ("cloudy_day",          "흐림"),
    (4, 0, False): ("cloudy_night",        "흐림"),
    (1, 1, True):  ("rainy_day",           "비"),
    (1, 1, False): ("rainy_night",         "비"),
    (3, 1, True):  ("rainy_day",           "비"),
    (3, 1, False): ("rainy_night",         "비"),
    (4, 1, True):  ("rainy_day",           "강한 비"),
    (4, 1, False): ("rainy_night",         "강한 비"),
    (1, 2, True):  ("sleet_day",           "비/눈"),
    (1, 2, False): ("sleet_night",         "비/눈"),
    (1, 3, True):  ("snowy_day",           "눈"),
    (1, 3, False): ("snowy_night",         "눈"),
    (4, 3, True):  ("snowy_day",           "강한 눈"),
    (4, 3, False): ("snowy_night",         "강한 눈"),
    (1, 4, True):  ("rainy_day",           "소나기"),
    (1, 4, False): ("rainy_night",         "소나기"),
}
_DEFAULT_ICON = ("cloudy_day", "흐림")


class WeatherService:
    def __init__(self):
        self._cache: dict | None = None
        self._cache_time: float = 0.0

    # ─── Public ──────────────────────────────────────────────────────────────

    def get_current(self) -> dict:
        """Return current weather snapshot."""
        return self._load().get("current", _fallback_current())

    def get_forecast(self) -> list[dict]:
        """Return 3-day daily forecast."""
        return self._load().get("forecast", [])

    # ─── Cache ───────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        now = time.time()
        if self._cache and now - self._cache_time < WEATHER_CACHE_TTL:
            return self._cache

        # Try disk cache first (survive restarts)
        if WEATHER_CACHE_FILE.exists():
            try:
                disk = json.loads(WEATHER_CACHE_FILE.read_text(encoding="utf-8"))
                if now - disk.get("saved_at", 0) < WEATHER_CACHE_TTL:
                    self._cache = disk
                    self._cache_time = disk["saved_at"]
                    return self._cache
            except (json.JSONDecodeError, OSError):
                pass

        fresh = self._fetch()
        fresh["saved_at"] = now
        self._cache = fresh
        self._cache_time = now
        try:
            WEATHER_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            WEATHER_CACHE_FILE.write_text(json.dumps(fresh, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        return fresh

    # ─── Fetch ───────────────────────────────────────────────────────────────

    def _fetch(self) -> dict:
        if TEST_MODE or not _is_real_api_key(WEATHER_API_KEY):
            return _dummy_weather()
        try:
            base_date, base_time = _kma_base_time()
            resp = requests.get(
                WEATHER_API_URL,
                params={
                    "ServiceKey": WEATHER_API_KEY,
                    "numOfRows": 1000,   # getVilageFcst 3일치 ≈ 700~900개
                    "pageNo": 1,
                    "dataType": "JSON",
                    "base_date": base_date,
                    "base_time": base_time,
                    "nx": WEATHER_NX,
                    "ny": WEATHER_NY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json()["response"]["body"]["items"]["item"]
            return _parse(items)
        except Exception as e:
            logger.warning("Weather API error: %s", e)
            return _dummy_weather()


# ─── Parsing helpers ─────────────────────────────────────────────────────────

def _parse(items: list[dict]) -> dict:
    grid: dict[tuple, dict] = {}
    for it in items:
        key = (it["fcstDate"], it["fcstTime"])
        grid.setdefault(key, {})[it["category"]] = it["fcstValue"]

    now = datetime.now()
    now_key = _nearest_key(grid, now)
    current_raw = grid.get(now_key, {})

    is_day = 6 <= now.hour < 20
    sky  = int(current_raw.get("SKY", 1))
    pty  = int(current_raw.get("PTY", 0))
    # getVilageFcst: TMP (1시간 기온)
    temp = current_raw.get("TMP", "N/A")
    icon_name, label = _ICON_MAP.get((sky, pty, is_day), _DEFAULT_ICON)

    current = {
        "temperature": temp,
        "icon":        f"{icon_name}.png",
        "label":       label,
        "humidity":    current_raw.get("REH", ""),
        "is_daytime":  is_day,
        "updated":     now.strftime("%H:%M"),
    }

    # Build 3-day forecast
    # getVilageFcst: TMX=일최고기온(15시), TMN=일최저기온(06시), TMP=매시간기온
    today_str = now.strftime("%Y%m%d")
    daily: dict[str, dict] = {}
    for (date, ftime), vals in grid.items():
        if date < today_str:        # 과거 날짜 제외
            continue
        d = daily.setdefault(date, {"tmps": [], "max": None, "min": None, "sky": [], "pty": []})
        if "TMX" in vals:
            d["max"] = float(vals["TMX"])
        if "TMN" in vals:
            d["min"] = float(vals["TMN"])
        if "TMP" in vals:
            d["tmps"].append(float(vals["TMP"]))
        if "SKY" in vals:
            d["sky"].append(int(vals["SKY"]))
        if "PTY" in vals:
            d["pty"].append(int(vals["PTY"]))

    forecast = []
    for date in sorted(daily.keys())[:3]:
        d = daily[date]
        # TMX/TMN 없으면 TMP 최대/최솟값으로 대체
        max_t = d["max"] if d["max"] is not None else (max(d["tmps"]) if d["tmps"] else None)
        min_t = d["min"] if d["min"] is not None else (min(d["tmps"]) if d["tmps"] else None)
        sky_mode  = max(set(d["sky"]), key=d["sky"].count) if d["sky"] else 1
        pty_mode  = max(set(d["pty"]), key=d["pty"].count) if d["pty"] else 0
        icon_name, label = _ICON_MAP.get((sky_mode, pty_mode, True), _DEFAULT_ICON)
        dt = datetime.strptime(date, "%Y%m%d")
        forecast.append({
            "date":  dt.strftime("%m/%d"),
            "day":   ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()],
            "icon":  f"{icon_name}.png",
            "label": label,
            "max":   round(max_t) if max_t is not None else "N/A",
            "min":   round(min_t) if min_t is not None else "N/A",
        })

    return {"current": current, "forecast": forecast}


def _nearest_key(grid: dict, now: datetime) -> tuple:
    now_str = now.strftime("%Y%m%d")
    now_hhmm = f"{now.hour:02d}00"
    for hhmm in [now_hhmm, f"{(now.hour - 1) % 24:02d}00"]:
        if (now_str, hhmm) in grid:
            return (now_str, hhmm)
    return next(iter(grid))


def _kma_base_time() -> tuple[str, str]:
    """getVilageFcst 발표 시각: 02, 05, 08, 11, 14, 17, 20, 23시 (약 10분 후 제공)."""
    now = datetime.now()
    base_hours = [2, 5, 8, 11, 14, 17, 20, 23]
    avail = None
    for h in reversed(base_hours):
        if now.hour > h or (now.hour == h and now.minute >= 10):
            avail = h
            break
    if avail is None:
        # 02:10 이전 → 전날 23:00 기준
        yesterday = now - timedelta(days=1)
        return yesterday.strftime("%Y%m%d"), "2300"
    return now.strftime("%Y%m%d"), f"{avail:02d}00"


def _is_real_api_key(key: str) -> bool:
    """한글 등 non-ASCII 포함 시 플레이스홀더로 판단해 False 반환."""
    return bool(key) and all(ord(c) < 128 for c in key)


def _fallback_current() -> dict:
    return {"temperature": "N/A", "icon": "cloudy_day.png", "label": "정보 없음",
            "humidity": "", "is_daytime": True, "updated": ""}


def _dummy_weather() -> dict:
    import random
    # icon과 label이 항상 짝이 맞도록 쌍으로 선택 (기존엔 icon만 랜덤이라 서로 안 맞았음)
    icon_labels = [
        ("sunny_day",         "맑음"),
        ("mostly_cloudy_day", "구름 많음"),
        ("cloudy_day",        "흐림"),
        ("rainy_day",         "비"),
    ]
    temps = [str(random.randint(10, 30)) for _ in range(3)]
    icon, label = random.choice(icon_labels)
    days = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.today()
    forecast = []
    for i in range(3):
        dt = today + timedelta(days=i)
        f_icon, f_label = random.choice(icon_labels)
        forecast.append({
            "date": dt.strftime("%m/%d"),
            "day": days[dt.weekday()],
            "icon": f"{f_icon}.png",
            "label": f_label,
            "max": random.randint(20, 32),
            "min": random.randint(10, 19),
        })
    return {
        "current": {
            "temperature": temps[0],
            "icon": f"{icon}.png",
            "label": label,
            "humidity": "60",
            "is_daytime": True,
            "updated": datetime.now().strftime("%H:%M"),
        },
        "forecast": forecast,
    }

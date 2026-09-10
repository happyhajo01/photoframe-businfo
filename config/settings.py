"""
Application configuration and constants.
All environment-driven values are loaded here with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "config" / ".env")


# ─── Server ─────────────────────────────────────────────────────────────────
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", 5000))
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

# ─── Test / Development ──────────────────────────────────────────────────────
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# ─── Paths ───────────────────────────────────────────────────────────────────
DATA_DIR        = BASE_DIR / "data"
STATIC_DIR      = BASE_DIR / "static"
PHOTOS_DIR      = STATIC_DIR / "images" / "photos"
WEATHER_DIR     = STATIC_DIR / "images" / "weather"
THUMBNAILS_DIR  = DATA_DIR / "thumbnails"

BUS_STOPS_FILE      = DATA_DIR / "bus_stops.json"
COMMUTE_STOPS_FILE  = DATA_DIR / "commute_stops.json"
APP_SETTINGS_FILE   = DATA_DIR / "app_settings.json"
BUS_CACHE_FILE      = DATA_DIR / "bus_cache.json"
WEATHER_CACHE_FILE  = DATA_DIR / "weather_cache.json"
HOLIDAY_CACHE_FILE  = DATA_DIR / "holiday_cache.json"

# ─── API Keys ────────────────────────────────────────────────────────────────
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
HOLIDAY_API_KEY = os.getenv("HOLIDAY_API_KEY", "")
BUS_API_KEY     = os.getenv("BUS_API_KEY", "")

# ─── External API Endpoints ──────────────────────────────────────────────────
WEATHER_API_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
HOLIDAY_API_URL = "https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"
BUS_API_URL     = "http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid"

# ─── Weather Grid (Seoul Nowon) ───────────────────────────────────────────────
WEATHER_NX = int(os.getenv("WEATHER_NX", 61))
WEATHER_NY = int(os.getenv("WEATHER_NY", 127))

# ─── Cache TTL (seconds) ─────────────────────────────────────────────────────
BUS_CACHE_TTL     = int(os.getenv("BUS_CACHE_TTL", 60))
WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", 1800))   # 30 min
HOLIDAY_CACHE_TTL = int(os.getenv("HOLIDAY_CACHE_TTL", 86400))  # 24 h

# ─── Display ─────────────────────────────────────────────────────────────────
DISPLAY_WIDTH  = 1200
DISPLAY_HEIGHT = 1920

# ─── Default App Settings ─────────────────────────────────────────────────────
DEFAULT_APP_SETTINGS = {
    "photo_interval":       20,      # seconds between photo transitions
    "bus_update_interval":  30,      # seconds between bus data refresh
    "weather_update_interval": 1800, # seconds between weather refresh
    "auto_return_minutes":  20,      # minutes before returning to main
    "monitor_off_time":     "23:50", # HH:MM
    "monitor_on_time":      "05:10", # HH:MM
    "night_mode_start":     "00:00", # blank screen start
    "night_mode_end":       "05:00", # blank screen end
    "transition_speed":     800,     # ms for photo transitions
    "slideshow_effects":    ["crossFade", "slideLeft", "slideRight", "zoomIn", "zoomOut", "fadeBlur"],
}

# ─── Supported Media Extensions ──────────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# ─── Thumbnail Settings ───────────────────────────────────────────────────────
THUMBNAIL_WIDTH   = 1200
THUMBNAIL_HEIGHT  = 1920
THUMBNAIL_QUALITY = 85

# ─── Monitor Control (Wayland) ────────────────────────────────────────────────
MONITOR_OUTPUT  = os.getenv("MONITOR_OUTPUT", "HDMI-A-1")
MONITOR_ENABLED = os.getenv("MONITOR_CONTROL", "true").lower() == "true"

"""
Raspberry Pi Photo Frame — Main Flask Application
Serves four pages: main (clock+slideshow), bus, commute, settings.
All dynamic data is delivered via JSON API endpoints.
"""

import logging
import os
import sys
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from config.settings import DEBUG, HOST, PORT, SECRET_KEY
from services import (
    BusService,
    DataService,
    HolidayService,
    ImageService,
    MonitorService,
    WeatherService,
)

# ─── Logging ─────────────────────────────────────────────────────────────────
sys.stdout.reconfigure(line_buffering=True)  # 터미널 실시간 출력 보장
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

# ─── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ─── Services (singleton per process) ────────────────────────────────────────
data_svc    = DataService()
bus_svc     = BusService()
weather_svc = WeatherService()
holiday_svc = HolidayService()
image_svc   = ImageService()
monitor_svc = MonitorService()


# ═══════════════════════════════════════════════════════════════════════════════
#  Page routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def page_main():
    return render_template("main.html")

@app.route("/bus")
def page_bus():
    return render_template("bus.html")

@app.route("/commute")
def page_commute():
    return render_template("commute.html")

@app.route("/settings")
def page_settings():
    return render_template("settings.html")


# ═══════════════════════════════════════════════════════════════════════════════
#  API — Settings
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    return jsonify(data_svc.get_all())

@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "message": "요청 데이터가 없습니다"}), 400
    ok, message = data_svc.save_all(data)
    return jsonify({"ok": ok, "message": message}), (200 if ok else 422)

@app.route("/api/restart", methods=["POST"])
def api_restart():
    """systemd(Restart=always)가 자동으로 재기동하도록 프로세스를 종료한다."""
    def _delayed_exit():
        import time
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=_delayed_exit, daemon=True).start()
    return jsonify({"ok": True, "message": "서버를 재시작합니다"})


# ═══════════════════════════════════════════════════════════════════════════════
#  API — Weather
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/weather")
def api_weather():
    today = datetime.now()
    day_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    holiday = holiday_svc.is_holiday(today)
    return jsonify({
        "current":  weather_svc.get_current(),
        "forecast": weather_svc.get_forecast(),
        "date": {
            "full":    today.strftime("%Y년 %m월 %d일"),
            "day":     day_names[today.weekday()],
            "is_sat":  today.weekday() == 5,
            "is_sun":  today.weekday() == 6,
            "holiday": holiday,
        },
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  API — Bus
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/bus")
def api_bus():
    force = request.args.get("refresh", "false").lower() == "true"
    stops = data_svc.get_bus_stops().get("stops", [])
    return jsonify({"stops": bus_svc.get_stops_info(stops, force)})

@app.route("/api/commute")
def api_commute():
    force = request.args.get("refresh", "false").lower() == "true"
    stops = data_svc.get_commute_stops().get("stops", [])
    return jsonify({"stops": bus_svc.get_commute_info(stops, force)})


# ═══════════════════════════════════════════════════════════════════════════════
#  API — Media
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/media")
def api_media():
    return jsonify({"items": image_svc.list_media()})

@app.route("/api/thumbnail")
def api_thumbnail():
    rel_path = request.args.get("path", "")
    if not rel_path:
        return jsonify({"ok": False}), 400
    ok, thumb = image_svc.get_thumbnail(rel_path)
    return jsonify({"ok": ok, "path": thumb})


# ═══════════════════════════════════════════════════════════════════════════════
#  Error handlers
# ═══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def err404(e):
    return render_template("error.html", code=404, message="페이지를 찾을 수 없습니다"), 404

@app.errorhandler(500)
def err500(e):
    return render_template("error.html", code=500, message="서버 오류가 발생했습니다"), 500


# ═══════════════════════════════════════════════════════════════════════════════
#  Monitor scheduling background thread
# ═══════════════════════════════════════════════════════════════════════════════

def _monitor_scheduler():
    import time
    while True:
        settings = data_svc.get_app_settings()
        off_h, off_m = _parse_hhmm(settings.get("monitor_off_time", "23:50"))
        on_h,  on_m  = _parse_hhmm(settings.get("monitor_on_time",  "05:10"))
        now = datetime.now()
        total_now = now.hour * 60 + now.minute
        total_off = off_h * 60 + off_m
        total_on  = on_h  * 60 + on_m

        if total_off > total_on:  # overnight: off at 23:50, on at 05:10
            should_off = total_now >= total_off or total_now < total_on
        else:
            should_off = total_on <= total_now < total_off

        if should_off:
            monitor_svc.turn_off()
        else:
            monitor_svc.turn_on()
        time.sleep(60)


def _parse_hhmm(s: str) -> tuple[int, int]:
    try:
        h, m = s.split(":")
        return int(h), int(m)
    except (ValueError, AttributeError):
        return 0, 0


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    t = threading.Thread(target=_monitor_scheduler, daemon=True)
    t.start()
    app.run(host=HOST, port=PORT, debug=DEBUG)

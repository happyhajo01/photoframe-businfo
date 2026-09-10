"""
Real-time bus arrival data from Seoul public transport API.
Results are cached for BUS_CACHE_TTL seconds to reduce API load.
"""

import json
import logging
import random
import re
import time
from datetime import datetime

import requests

from config.settings import (
    BUS_API_KEY,
    BUS_API_URL,
    BUS_CACHE_FILE,
    BUS_CACHE_TTL,
    TEST_MODE,
)

logger = logging.getLogger(__name__)

# Arrival time thresholds for color coding (seconds)
URGENT_THRESHOLD = 180   # ≤ 3 min → red
WARNING_THRESHOLD = 240  # ≤ 4 min → blue


_FETCH_INTERVAL = 0.05  # seconds between successive API calls


class BusService:
    def __init__(self):
        self._cache: dict = {}  # {stop_id: {"data": [...], "time": float}}
        self._last_fetch_time: float = 0.0

    # ─── Public ──────────────────────────────────────────────────────────────

    def get_stops_info(self, stops: list[dict], force_refresh: bool = False) -> list[dict]:
        """Return arrival data for all configured stops."""
        result = []
        for stop in stops:
            stop_id   = stop.get("id", "")
            stop_name = stop.get("name", "")
            buses     = stop.get("buses", [])
            arrivals  = self._get_arrivals(stop_id, buses, force_refresh)
            result.append({"name": stop_name, "id": stop_id, "arrivals": arrivals})
        return result

    # ─── Caching ─────────────────────────────────────────────────────────────

    def _get_arrivals(self, stop_id: str, buses: list[str], force: bool) -> list[dict]:
        now = time.time()
        entry = self._cache.get(stop_id)
        if not force and entry and now - entry["time"] < BUS_CACHE_TTL:
            return entry["data"]

        elapsed = now - self._last_fetch_time
        if elapsed < _FETCH_INTERVAL:
            time.sleep(_FETCH_INTERVAL - elapsed)
        self._last_fetch_time = time.time()
        data = self._fetch(stop_id, buses)
        self._cache[stop_id] = {"data": data, "time": time.time()}
        self._persist_cache()
        return data

    def _persist_cache(self):
        try:
            BUS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            BUS_CACHE_FILE.write_text(
                json.dumps({"data": self._cache}, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    # ─── Fetch ───────────────────────────────────────────────────────────────

    def _fetch(self, stop_id: str, buses: list[str]) -> list[dict]:
        if TEST_MODE or not _is_real_api_key(BUS_API_KEY):
            reason = "TEST_MODE" if TEST_MODE else "API키 미설정"
            logger.info("[BUS] stop=%s 더미데이터 사용 (%s)", stop_id, reason)
            return _dummy_arrivals(buses)
        try:
            logger.info("[BUS 요청] stop=%s  설정버스=%s", stop_id, buses)
            resp = requests.get(
                BUS_API_URL,
                params={"ServiceKey": BUS_API_KEY, "arsId": stop_id, "resultType": "json"},
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get("msgBody", {}).get("itemList", [])

            logger.info("[BUS 원본] stop=%s  수신노선=%d개", stop_id, len(items))
            for item in items:
                logger.info("  원본  rtNm=%-8s  arrmsg1=%-28s  arrmsg2=%s",
                            item.get("rtNm", ""), item.get("arrmsg1", ""), item.get("arrmsg2", ""))

            result = _parse(items, buses)

            logger.info("[BUS 표출] stop=%s  표출노선=%d개", stop_id, len(result))
            for r in result:
                times_str = " | ".join(
                    f"{t.get('label','?')}({t.get('urgency','?')})" for t in r.get("times", [])
                )
                logger.info("  표출  노선=%-8s  %s", r["route"], times_str or "도착정보없음")

            return result
        except Exception as e:
            logger.warning("[BUS 오류] stop=%s  %s", stop_id, e)
            return _dummy_arrivals(buses)  # API 실패 시 더미 데이터 폴백

    # ─── Commute helper ──────────────────────────────────────────────────────

    def get_commute_info(self, stops: list[dict], force_refresh: bool = False) -> list[dict]:
        """Same as get_stops_info but returns only first 2 arrivals per bus."""
        result = []
        for stop in self.get_stops_info(stops, force_refresh):
            arrivals = [
                {**arr, "times": arr.get("times", [])[:2]}
                for arr in stop.get("arrivals", [])
            ]
            result.append({**stop, "arrivals": arrivals})
        return result


# ─── API key validation ──────────────────────────────────────────────────────

def _is_real_api_key(key: str) -> bool:
    """플레이스홀더(한글 포함) 또는 빈 키는 False."""
    return bool(key) and all(ord(c) < 128 for c in key)


# ─── Parsing helpers ─────────────────────────────────────────────────────────

def _parse(items: list[dict], buses: list[str]) -> list[dict]:
    route_map: dict[str, list] = {}
    for item in items:
        route = (item.get("rtNm") or "").strip()  # API가 공백 포함 문자열을 반환하는 경우 대응
        if buses and route not in buses:
            continue
        arrmsg1 = item.get("arrmsg1") or ""
        arrmsg2 = item.get("arrmsg2") or ""
        entry = route_map.setdefault(route, [])
        for arrmsg in (arrmsg1, arrmsg2):
            seconds = _to_seconds(arrmsg)
            if seconds is not None:
                entry.append(_make_time_entry(seconds, arrmsg, item.get("arsId", "")))
            else:
                term = _terminal_entry(arrmsg)
                if term:
                    entry.append(term)
                elif arrmsg:
                    logger.debug("arrmsg parse failed route=%s msg=%r", route, arrmsg)

    result = []
    for route, times in route_map.items():
        result.append({
            "route": route,
            "times": times[:4],
            "updated": datetime.now().strftime("%H:%M:%S"),
        })
    return sorted(result, key=lambda x: x["route"])


def _make_time_entry(seconds: int, raw_msg: str, stop_id: str) -> dict:
    minutes = max(0, (seconds + 30) // 60)
    urgency = (
        "urgent"  if seconds <= URGENT_THRESHOLD  else
        "warning" if seconds <= WARNING_THRESHOLD else
        "normal"
    )
    label = "곧 도착" if minutes == 0 else f"{minutes}분 후"
    # Extract nth bus position from raw message e.g. "[3번째 전]"
    match = re.search(r"\[(\d+)번째 전\]", raw_msg)
    nth = f"{match.group(1)}번째 전" if match else ""
    return {
        "minutes": minutes,
        "seconds": seconds,
        "label": label,
        "nth": nth,
        "urgency": urgency,
    }


def _terminal_entry(msg: str) -> dict | None:
    msg = (msg or "").strip()
    if "운행종료" in msg:
        return {"seconds": None, "minutes": None, "label": "운행종료", "nth": "", "urgency": "ended"}
    if "출발대기" in msg:
        return {"seconds": None, "minutes": None, "label": "출발대기", "nth": "", "urgency": "waiting"}
    if "차고지출발" in msg:
        return {"seconds": None, "minutes": None, "label": "차고지출발", "nth": "", "urgency": "waiting"}
    return None


def _to_seconds(msg: str) -> int | None:
    """Convert Korean bus arrival message to seconds."""
    if not msg:
        return None
    msg = msg.strip()
    if msg in ("운행종료", "출발대기", "차고지출발"):
        return None
    if "도착" in msg:
        return 0
    m = re.search(r"(\d+)\s*분\s*(\d+)?\s*초?", msg)  # 숫자와 분·초 사이 공백 허용
    if m:
        mins = int(m.group(1))
        secs = int(m.group(2)) if m.group(2) else 0
        return mins * 60 + secs
    m = re.search(r"(\d+)\s*초", msg)
    if m:
        return int(m.group(1))
    return None


def _dummy_arrivals(buses: list[str]) -> list[dict]:
    result = []
    for bus in buses:
        times = []
        base = random.randint(1, 20)
        for i in range(2):
            secs = (base + i * random.randint(8, 15)) * 60
            times.append(_make_time_entry(secs, f"{base + i*10}분후[{i+1}번째 전]", ""))
        result.append({"route": bus, "times": times, "updated": datetime.now().strftime("%H:%M:%S")})
    return result

"""
Pi Vitals 프레임 렌더링 (Pillow).
세로(172x320)/가로(320x172) 레이아웃 각 1개, 게이지 스타일(둥근/막대)은 같은 레이아웃 안에서
게이지 슬롯 하나만 다르게 그려 넣는 방식으로 공유한다 — 레이아웃 x 스타일 4벌을 따로 만들지 않는다.
"""

from collections import deque

from PIL import Image, ImageDraw, ImageFont

BG = (26, 26, 25)
TRACK = (47, 47, 46)          # rgba(255,255,255,0.09) on BG 근사값
INK_1 = (255, 255, 255)
INK_2 = (195, 194, 183)
INK_3 = (137, 135, 129)

COLOR_CPU = (0x39, 0x87, 0xe5)
COLOR_RAM = (0xd9, 0x59, 0x26)
COLOR_DISK = (0x19, 0x9e, 0x70)
COLOR_FAN = (0x90, 0x85, 0xe9)

STATUS_STEPS = [
    (55, (0x0c, 0xa3, 0x0c), "NORMAL"),
    (65, (0xfa, 0xb2, 0x19), "WARM"),
    (75, (0xec, 0x83, 0x5a), "HIGH"),
    (999, (0xd0, 0x3b, 0x3b), "CRITICAL"),
]

_HIST_LEN = 30
_history = {
    "cpu": deque([0] * _HIST_LEN, maxlen=_HIST_LEN),
    "temp": deque([45] * _HIST_LEN, maxlen=_HIST_LEN),
    "ram": deque([0] * _HIST_LEN, maxlen=_HIST_LEN),
    "disk": deque([0] * _HIST_LEN, maxlen=_HIST_LEN),
    "fan": deque([0] * _HIST_LEN, maxlen=_HIST_LEN),
}

_FONT_PATHS = {
    False: [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ],
    True: [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    ],
}
_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont] = {}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _font_cache:
        for path in _FONT_PATHS[bold]:
            try:
                _font_cache[key] = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        else:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def _fmt_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    return f"up {days}d {hours:02d}:{minutes:02d}"


def status_for(temp_c: float | None) -> tuple:
    if temp_c is None:
        return (INK_3, "N/A")
    for limit, color, label in STATUS_STEPS:
        if temp_c < limit:
            return (color, label)
    return (STATUS_STEPS[-1][1], STATUS_STEPS[-1][2])


# ─── 프리미티브 ────────────────────────────────────────────────────────────

def draw_ring(draw: ImageDraw.ImageDraw, cx, cy, r, pct, color, width=3):
    box = [cx - r, cy - r, cx + r, cy + r]
    draw.arc(box, 0, 359, fill=TRACK, width=width)
    pct = max(0, min(100, pct))
    if pct > 0:
        draw.arc(box, -90, -90 + pct / 100 * 360, fill=color, width=width)


def draw_hbar(draw: ImageDraw.ImageDraw, x, y, w, h, pct, color):
    radius = h // 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=TRACK)
    pct = max(0, min(100, pct))
    fw = max(h, w * pct / 100)
    if pct > 0:
        draw.rounded_rectangle([x, y, x + fw, y + h], radius=radius, fill=color)


def draw_spark(draw: ImageDraw.ImageDraw, x, y, w, h, values, vmin, vmax, color):
    values = list(values)
    n = len(values)
    if n < 2 or vmax <= vmin:
        return
    pts = []
    for i, v in enumerate(values):
        px = x + (i / (n - 1)) * w
        t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
        py = y + h - t * h
        pts.append((px, py))
    draw.line(pts, fill=color, width=2, joint="curve")
    ex, ey = pts[-1]
    draw.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=color)


def _gauge_slot(draw, x, y, w, h, pct, color, style):
    """게이지 슬롯 하나: style에 따라 둥근 링 또는 가로 막대를 같은 자리에 그린다."""
    if style == "round":
        r = min(w, h) / 2
        draw_ring(draw, x + w / 2, y + h / 2, r, pct, color, width=max(3, int(r * 0.22)))
    else:
        bar_h = max(4, int(h * 0.28))
        draw_hbar(draw, x, y + (h - bar_h) / 2, w, bar_h, pct, color)


# ─── 레이아웃: 세로 172x320 ──────────────────────────────────────────────

def _render_portrait(data: dict, style: str) -> Image.Image:
    W, H = 172, 320
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((8, 6), "PI · STATUS", font=_font(7, True), fill=INK_3)
    d.line([(0, 22), (W, 22)], fill=TRACK, width=1)

    y = 28
    row_h = 50
    gap = 4

    def gauge_row(label, dot_color, value_text, sub_text, pct, hist_key, vmin, vmax, spark_color=None):
        nonlocal y
        gy = y
        _gauge_slot(d, 8, gy + (row_h - 40) / 2, 40, 40, pct if pct is not None else 0, dot_color, style)
        tx = 8 + 40 + 8
        d.ellipse([tx, gy + 15, tx + 5, gy + 20], fill=dot_color)
        d.text((tx + 9, gy + 12), label, font=_font(7, True), fill=INK_3)
        d.text((tx, gy + 24), value_text, font=_font(15, True), fill=INK_1)
        if sub_text:
            d.text((tx, gy + 42), sub_text, font=_font(7), fill=INK_3)
        if hist_key:
            sc = spark_color or dot_color
            draw_spark(d, W - 8 - 44, gy + (row_h - 26) / 2, 44, 26, _history[hist_key], vmin, vmax, sc)
        y += row_h + gap

    # CPU
    _history["cpu"].append(data["cpu_pct"])
    gauge_row("CPU LOAD", COLOR_CPU, f"{round(data['cpu_pct'])}%", "4 cores", data["cpu_pct"], "cpu", 0, 100)

    # TEMP
    temp = data["temp_c"]
    st_color, st_label = status_for(temp)
    _history["temp"].append(temp if temp is not None else 0)
    temp_pct = None if temp is None else (temp - 30) / (85 - 30) * 100
    gauge_row("SOC TEMP", st_color, "N/A" if temp is None else f"{temp:.1f}°C", st_label,
               temp_pct, "temp", 35, 85, spark_color=st_color)

    # RAM
    _history["ram"].append(data["ram_pct"])
    gauge_row("MEMORY", COLOR_RAM, f"{round(data['ram_pct'])}%",
               f"{data['ram_used_mb']} / {data['ram_total_mb']} MB", data["ram_pct"], "ram", 0, 100)

    # DISK
    _history["disk"].append(data["disk_pct"])
    gauge_row("SSD", COLOR_DISK, f"{round(data['disk_pct'])}%",
               f"{data['disk_used_gb']:.0f} / {data['disk_total_gb']:.0f} GB",
               data["disk_pct"], "disk", 0, 100)

    # FAN
    fan_rpm, fan_pwm = data["fan_rpm"], data["fan_pwm"]
    _history["fan"].append(fan_rpm if fan_rpm is not None else 0)
    fan_pct = None if fan_pwm is None else fan_pwm / 255 * 100
    gauge_row("FAN", COLOR_FAN, "N/A" if fan_rpm is None else f"{fan_rpm} rpm",
               "N/A" if fan_pwm is None else f"PWM {fan_pwm} / 255",
               fan_pct, "fan", 0, 7000)

    d.line([(0, H - 20), (W, H - 20)], fill=TRACK, width=1)
    d.text((8, H - 15), data.get("ip", "0.0.0.0"), font=_font(7), fill=INK_3)
    d.text((W - 8, H - 15), _fmt_uptime(data.get("uptime_s", 0)), font=_font(7), fill=INK_3, anchor="ra")
    return img


# ─── 레이아웃: 가로 320x172 ──────────────────────────────────────────────

def _render_landscape(data: dict, style: str) -> Image.Image:
    W, H = 320, 172
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((10, 5), "PI · STATUS", font=_font(7, True), fill=INK_3)
    d.line([(0, 18), (W, 18)], fill=TRACK, width=1)

    body_top, body_bottom = 22, H - 18
    row_h = (body_bottom - body_top) / 5

    def row(i, label, color, value_text, pct, hist_key, vmin, vmax):
        ry = body_top + i * row_h
        cy = ry + row_h / 2
        d.ellipse([10, cy - 2.5, 15, cy + 2.5], fill=color)
        d.text((20, cy - 4), label, font=_font(7, True), fill=INK_3)
        d.text((188, cy - 5), value_text, font=_font(11, True), fill=INK_1, anchor="ra")
        gauge_x = 196
        gauge_w = 68
        _gauge_slot(d, gauge_x, ry + row_h * 0.2, gauge_w, row_h * 0.6,
                    pct if pct is not None else 0, color, style)
        spark_x = gauge_x + gauge_w + 8
        draw_spark(d, spark_x, ry + row_h * 0.15, W - 10 - spark_x, row_h * 0.7,
                   _history[hist_key], vmin, vmax, color)

    _history["cpu"].append(data["cpu_pct"])
    row(0, "CPU", COLOR_CPU, f"{round(data['cpu_pct'])}%", data["cpu_pct"], "cpu", 0, 100)

    temp = data["temp_c"]
    st_color, st_label = status_for(temp)
    _history["temp"].append(temp if temp is not None else 0)
    temp_pct = None if temp is None else (temp - 30) / (85 - 30) * 100
    row(1, "TEMP", st_color, "N/A" if temp is None else f"{temp:.1f}°C · {st_label}",
        temp_pct, "temp", 35, 85)

    _history["ram"].append(data["ram_pct"])
    row(2, "RAM", COLOR_RAM, f"{round(data['ram_pct'])}%", data["ram_pct"], "ram", 0, 100)

    _history["disk"].append(data["disk_pct"])
    row(3, "SSD", COLOR_DISK, f"{round(data['disk_pct'])}%", data["disk_pct"], "disk", 0, 100)

    fan_rpm, fan_pwm = data["fan_rpm"], data["fan_pwm"]
    _history["fan"].append(fan_rpm if fan_rpm is not None else 0)
    fan_pct = None if fan_pwm is None else fan_pwm / 255 * 100
    row(4, "FAN", COLOR_FAN, "N/A" if fan_rpm is None else f"{fan_rpm} rpm", fan_pct, "fan", 0, 7000)

    d.text((10, H - 14), data.get("ip", "0.0.0.0"), font=_font(7), fill=INK_3)
    d.text((W - 10, H - 14), _fmt_uptime(data.get("uptime_s", 0)), font=_font(7), fill=INK_3, anchor="ra")
    return img


def render(data: dict, orientation: str, style: str) -> Image.Image:
    """orientation: 'portrait' | 'landscape'. style: 'round' | 'bar'."""
    if orientation == "landscape":
        return _render_landscape(data, style)
    return _render_portrait(data, style)

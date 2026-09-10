# API 엔드포인트 레퍼런스

Base URL: `http://<라즈베리파이IP>:5000`

---

## 페이지 라우트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 메인 페이지 (시계 + 슬라이드쇼) |
| GET | `/bus` | 정류소 정보 페이지 |
| GET | `/commute` | 출근 정보 페이지 |
| GET | `/settings` | 설정 페이지 |

---

## JSON API

### `GET /api/weather`
현재 날씨, 3일 예보, 날짜 정보를 반환합니다.

**응답 예시:**
```json
{
  "current": {
    "temperature": "23",
    "icon": "sunny_day.png",
    "label": "맑음",
    "humidity": "55",
    "is_daytime": true,
    "updated": "17:30"
  },
  "forecast": [
    { "date": "05/11", "day": "월", "icon": "partly_cloudy.png", "label": "구름 조금", "max": 24, "min": 14 },
    { "date": "05/12", "day": "화", "icon": "rainy.png", "label": "비", "max": 19, "min": 13 }
  ],
  "date": {
    "full": "2026년 05월 10일",
    "day": "일요일",
    "is_sat": false,
    "is_sun": true,
    "holiday": null
  }
}
```

---

### `GET /api/bus?refresh=<bool>`
설정된 정류소의 버스 도착 정보를 반환합니다.

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `refresh` | `true`/`false` | `true`이면 캐시를 무시하고 즉시 API 호출 |

**응답 예시:**
```json
{
  "stops": [
    {
      "name": "보람1단지",
      "id": "11274",
      "arrivals": [
        {
          "route": "1143",
          "times": [
            { "minutes": 2, "seconds": 120, "label": "2분 후", "nth": "1번째 전", "urgency": "urgent" },
            { "minutes": 12, "seconds": 720, "label": "12분 후", "nth": "7번째 전", "urgency": "normal" }
          ],
          "updated": "17:30:05"
        }
      ]
    }
  ]
}
```

---

### `GET /api/commute?refresh=<bool>`
출근 설정 정류소의 버스 도착 정보를 반환합니다. `/api/bus`와 동일한 구조이며 최대 2개 도착 정보만 포함합니다.

---

### `GET /api/settings`
전체 설정(정류소 + 출근 + 앱 설정)을 반환합니다.

**응답 예시:**
```json
{
  "bus_stops":     { "stops": [ ... ] },
  "commute_stops": { "stops": [ ... ] },
  "app_settings":  { "photo_interval": 30, ... }
}
```

---

### `POST /api/settings`
설정을 저장합니다. `Content-Type: application/json` 필요.

**요청 본문:** `GET /api/settings` 응답 구조와 동일. 부분 업데이트 가능 (원하는 키만 포함).

**응답:**
```json
{ "ok": true, "message": "모든 설정 저장 완료" }
```
```json
{ "ok": false, "message": "정류소 0: 이름이 없습니다" }
```

---

### `GET /api/media`
`static/images/photos/` 디렉토리의 미디어 파일 목록을 반환합니다.

**응답 예시:**
```json
{
  "items": [
    { "path": "images/photos/vacation.jpg", "type": "image", "name": "vacation.jpg" },
    { "path": "images/photos/trip.mp4",     "type": "video", "name": "trip.mp4" }
  ]
}
```

---

### `GET /api/thumbnail?path=<rel_path>`
이미지 썸네일을 생성하거나 캐시된 썸네일 경로를 반환합니다.

| 파라미터 | 설명 |
|---------|------|
| `path` | `static/` 기준 상대 경로 (예: `images/photos/img.jpg`) |

**응답:**
```json
{ "ok": true,  "path": "data/thumbnails/abc123.jpg" }
{ "ok": false, "path": "images/photos/img.jpg" }
```

---

## 오류 코드

| HTTP 코드 | 의미 |
|-----------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파라미터 누락 등) |
| 404 | 존재하지 않는 경로 |
| 422 | 유효성 검사 실패 (설정 저장 시) |
| 500 | 서버 내부 오류 |

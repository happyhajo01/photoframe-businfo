# 변수 및 설정값 레퍼런스

## 환경 변수 (`.env`)

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `WEATHER_API_KEY` | — | 기상청 단기예보 API 키 (공공데이터포털) |
| `HOLIDAY_API_KEY` | — | 한국천문연구원 특일정보 API 키 |
| `BUS_API_KEY` | — | 서울시 버스도착정보 API 키 |
| `FLASK_HOST` | `0.0.0.0` | Flask 서버 바인딩 주소 |
| `FLASK_PORT` | `5000` | Flask 서버 포트 |
| `FLASK_DEBUG` | `false` | 디버그 모드 (개발 시 `true`) |
| `SECRET_KEY` | — | Flask 세션 암호화 키 (필수 변경) |
| `TEST_MODE` | `false` | `true`이면 실제 API 대신 더미 데이터 사용 |
| `WEATHER_NX` | `61` | 기상청 격자 X좌표 (서울 노원) |
| `WEATHER_NY` | `127` | 기상청 격자 Y좌표 (서울 노원) |
| `BUS_CACHE_TTL` | `60` | 버스 캐시 유효시간 (초) |
| `WEATHER_CACHE_TTL` | `1800` | 날씨 캐시 유효시간 (초, 30분) |
| `HOLIDAY_CACHE_TTL` | `86400` | 공휴일 캐시 유효시간 (초, 24시간) |
| `MONITOR_OUTPUT` | `HDMI-A-2` | wlr-randr 모니터 출력 이름 |
| `MONITOR_CONTROL` | `true` | 모니터 자동 전원 제어 활성화 |
| `PI_VITALS_ORIENTATION` | `portrait` | Pi Vitals 화면 방향 (`portrait`\|`landscape`) |
| `PI_VITALS_DIRECTION` | `left` | `landscape`일 때 리본 케이블 방향 (`left`\|`right`) |
| `PI_VITALS_STYLE` | `round` | 게이지 스타일 (`round`\|`bar`) |
| `PI_VITALS_REFRESH_SEC` | `1.0` | 화면 갱신 주기 (초) |
| `PI_VITALS_SPI_PORT` | `0` | SPI 포트 번호 |
| `PI_VITALS_SPI_DEVICE` | `0` | SPI 디바이스(CE) 번호 |
| `PI_VITALS_GPIO_DC` | `25` | ST7789 DC 핀 (BCM 번호) |
| `PI_VITALS_GPIO_RST` | `27` | ST7789 RST 핀 (BCM 번호) |
| `PI_VITALS_GPIO_BL` | `18` | ST7789 백라이트 핀 (BCM 번호) |
| `PI_VITALS_DISK_DEVICE` | `sda` | 디스크 활동량 측정 대상 (`/proc/diskstats` 디바이스명) |

---

## 앱 설정 (`data/app_settings.json`)

설정 페이지에서 저장되며 런타임에 적용됩니다.

| 키 | 기본값 | 단위 | 설명 |
|----|--------|------|------|
| `photo_interval` | `30` | 초 | 사진 슬라이드 전환 주기 |
| `bus_update_interval` | `60` | 초 | 버스 정보 자동 갱신 주기 |
| `weather_update_interval` | `1800` | 초 | 날씨 정보 갱신 주기 (30분) |
| `auto_return_minutes` | `20` | 분 | 버스/출근 페이지에서 메인으로 자동 복귀 시간 |
| `monitor_off_time` | `"23:50"` | HH:MM | 모니터가 꺼지는 시각 |
| `monitor_on_time` | `"05:10"` | HH:MM | 모니터가 켜지는 시각 |
| `night_mode_start` | `"00:00"` | HH:MM | 야간 모드(빈 화면) 시작 시각 |
| `night_mode_end` | `"06:00"` | HH:MM | 야간 모드 종료 시각 |
| `transition_speed` | `800` | ms | 슬라이드쇼 전환 애니메이션 시간 |
| `slideshow_effects` | (6가지) | 배열 | 활성화된 전환 효과 목록 (아래 참고) |

### 슬라이드쇼 전환 효과

| 효과 ID | 이름 | 설명 |
|---------|------|------|
| `crossFade` | 크로스 페이드 | 현재 사진이 서서히 사라지고 다음 사진이 나타남 |
| `slideLeft` | 슬라이드 ← | 다음 사진이 오른쪽에서 왼쪽으로 밀려 들어옴 |
| `slideRight` | 슬라이드 → | 다음 사진이 왼쪽에서 오른쪽으로 밀려 들어옴 |
| `slideUp` | 슬라이드 ↑ | 다음 사진이 아래에서 위로 밀려 들어옴 |
| `zoomIn` | 줌 인 | 다음 사진이 크게 확대되며 나타남 |
| `zoomOut` | 줌 아웃 | 다음 사진이 작은 크기에서 정상 크기로 나타남 |
| `fadeBlur` | 페이드 블러 | 흐림 효과와 함께 사진이 전환됨 |
| `kenBurns` | 켄 번즈 | 현재 사진이 서서히 이동하며 다음 사진으로 전환 |

---

## 버스 정류소 설정 (`data/bus_stops.json`, `data/commute_stops.json`)

```json
{
  "stops": [
    {
      "name": "보람1단지",   // 표시할 정류소 이름
      "id": "11274",         // 공공데이터포털 정류소 고유 ID (arsId)
      "buses": ["1143", "1137"]  // 도착 정보를 표시할 버스 번호 목록
    }
  ]
}
```

---

## 버스 도착 정보 데이터 구조 (API 응답)

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
            {
              "minutes": 5,        // 도착까지 남은 분
              "seconds": 300,      // 도착까지 남은 초
              "label": "5분 후",   // 표시 텍스트
              "nth": "3번째 전",   // 몇 번째 전 정류장인지
              "urgency": "normal"  // urgent(≤3분) | warning(≤4분) | normal
            }
          ],
          "updated": "17:30:00"
        }
      ]
    }
  ]
}
```

---

## CSS 디자인 토큰 (`static/css/variables.css`)

| 토큰 | 값 | 용도 |
|------|-----|------|
| `--color-bg` | `#1a1a2e` | 페이지 배경색 |
| `--color-surface` | `rgba(255,255,255,0.08)` | 카드/유리 효과 배경 |
| `--color-primary` | `#7c9ef8` | 강조색 (버튼, 포커스) |
| `--color-urgent` | `#ff7b7b` | 긴급 도착 (3분 이하) |
| `--color-warning` | `#7bb8ff` | 주의 도착 (4분 이하) |
| `--color-holiday` | `#ff6b6b` | 공휴일/일요일 날짜색 |
| `--color-saturday` | `#74b9ff` | 토요일 날짜색 |
| `--transition-slow` | `600ms` | 슬라이드쇼 기본 전환 시간 |

# 라즈베리파이 포토프레임 + 버스정보

라즈베리파이에서 실행되는 스마트 포토프레임 + 생활정보 대시보드입니다.

## 주요 기능

### 메인 화면
- 대형 디지털 시계 (시:분:초)
- **8가지 부드러운 전환 효과**의 사진·영상 슬라이드쇼 (JPG, PNG, MP4, WebM 등)
- 현재 날씨 아이콘 + 기온, 3일 예보
- 날짜 및 요일 (공휴일 빨간색, 토요일 파란색)
- 야간 모드 (설정 시간 동안 화면 완전히 끔)

### 정류소 페이지
- 설정된 정류소별 버스 도착 정보 카드
- 3분 이하 빨간색, 4분 이하 파란색 긴급도 표시
- 자동 갱신 (기본 60초), 설정 시간 후 메인으로 자동 복귀

### 출근 페이지
- 설정된 노선만 집중 표시, 2개 도착 시간 카드
- 카드 탭 시 긴급도 리플 애니메이션

### 설정 페이지
- 정류소·출근 정류소 추가/삭제
- 슬라이드 간격, 버스 갱신 주기, 모니터 스케줄 설정
- 슬라이드 전환 효과 개별 선택 (8가지)
- `Ctrl+S`로 빠른 저장

---

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 설정
cp config/.env.template config/.env
# .env 파일을 열어 API 키 입력

# 3. 사진 추가
# static/images/photos/ 폴더에 JPG, PNG, MP4 파일 복사

# 4. 실행
python app.py

# 브라우저에서 http://localhost:5000 접속
```

라즈베리파이 5 + Raspberry Pi OS Lite에 설치해서 부팅 시 자동 실행되게 하는
전체 절차는 [INSTALL_GUIDE.md](INSTALL_GUIDE.md) 를 참고하세요.

---

## 프로젝트 구조

```
photoframe-businfo/
├── app.py                   # Flask 앱, 모든 API 엔드포인트
├── config/
│   ├── settings.py          # 환경변수 로딩, 상수 정의
│   └── .env.template        # 환경변수 템플릿
├── services/
│   ├── bus_service.py       # 버스 도착 API 연동 + 캐시
│   ├── weather_service.py   # 기상청 API 연동 + 캐시
│   ├── holiday_service.py   # 공휴일 API 연동 + 캐시
│   ├── image_service.py     # 미디어 탐색, 썸네일 생성
│   ├── data_service.py      # 설정 파일 읽기/쓰기 + 유효성 검사
│   └── monitor_service.py   # 모니터 전원 제어 (DPMS)
├── templates/
│   ├── base.html            # 공통 레이아웃 (폰트, CSS 임포트)
│   ├── main.html            # 메인 페이지
│   ├── bus.html             # 정류소 페이지
│   ├── commute.html         # 출근 페이지
│   ├── settings.html        # 설정 페이지
│   └── error.html           # 오류 페이지
├── static/
│   ├── css/
│   │   ├── variables.css    # 디자인 토큰 (색상, 간격, 모션)
│   │   ├── base.css         # 리셋, 공통 컴포넌트
│   │   ├── main.css         # 메인 페이지 스타일
│   │   ├── bus.css          # 정류소/출근 페이지 스타일
│   │   └── settings.css     # 설정 페이지 스타일
│   ├── js/
│   │   ├── core/api.js      # 중앙화된 API 클라이언트
│   │   ├── modules/
│   │   │   ├── clock.js     # 시계 모듈
│   │   │   └── slideshow.js # 슬라이드쇼 엔진 (8가지 효과)
│   │   └── pages/
│   │       ├── main.js      # 메인 페이지 컨트롤러
│   │       ├── bus.js       # 정류소 페이지 컨트롤러
│   │       ├── commute.js   # 출근 페이지 컨트롤러
│   │       └── settings.js  # 설정 페이지 컨트롤러
│   └── images/
│       ├── weather/         # 날씨 아이콘 (sunny_day.png 등, 기본 플레이스홀더 포함)
│       └── photos/          # 슬라이드쇼 미디어 파일 (직접 추가)
├── data/                    # 런타임 데이터 (설정 JSON, 캐시, 썸네일) — git에는 포함되지 않음
├── scripts/
│   ├── kiosk-start.sh       # Lite OS 화면 자동 표시(sway + Chromium 키오스크) 진입 스크립트
│   ├── sway.config          # 키오스크용 sway 최소 설정 (커서 자동 숨김 등)
│   └── kiosk-browser.sh     # sway가 실행하는 Chromium 키오스크 실행 스크립트
├── docs/
│   ├── API.md               # API 엔드포인트 상세 문서
│   └── VARIABLES.md         # 설정값/변수 레퍼런스
├── photoframe.service       # systemd 서비스 (백엔드 자동 실행)
├── Dockerfile / docker-compose.yml  # 선택: Docker로 백엔드만 실행
└── requirements.txt
```

---

## 날씨 아이콘

`static/images/weather/`에 기본 플레이스홀더 아이콘 12종(해/달/구름/비/눈 조합)이 이미 포함되어 있어
설치 직후 바로 동작합니다. 마음에 드는 아이콘 세트로 바꾸고 싶다면 같은 파일명(`sunny_day.png` 등)으로
덮어쓰면 됩니다. 전체 파일명 목록은 [`docs/VARIABLES.md`](docs/VARIABLES.md)의 `_ICON_MAP`을 참고하세요.

## 날씨 API 좌표 설정

기상청 격자 좌표는 지역마다 다릅니다. `.env`에서 변경하세요:

| 지역 | NX | NY |
|------|----|----|
| 서울 노원 | 61 | 127 |
| 서울 강남 | 61 | 125 |
| 수원 | 60 | 121 |
| 부산 | 98 | 76 |

[격자 좌표 조회 도구](https://www.weather.go.kr/w/resources/viewer/grid_map_download.do)

---

## 키보드 단축키

| 키 | 페이지 | 동작 |
|----|--------|------|
| `←` / `→` | 메인 | 이전/다음 사진 |
| `Space` | 메인 | 전환 효과 토글 |
| `Ctrl+S` | 설정 | 설정 저장 |

---

## 기술 스택

- **백엔드**: Python 3.11+, Flask 3.1, Pillow
- **프론트엔드**: Vanilla JS (ES2022), CSS3 (Custom Properties, Backdrop-filter)
- **API**: 공공데이터포털 (기상청, 버스, 공휴일)
- **권장 환경**: 라즈베리파이 5, Raspberry Pi OS Lite (64-bit), 세로 디스플레이

# 파일 매니페스트

> 새 파일 생성 시 즉시 이 목록에 추가한다.

| 파일명 | 역할 | 생성일 |
|--------|------|--------|
| CLAUDE.md | 에이전트 가이드라인 핵심 헌법 | - |
| .claude/FILE_MANIFEST.md | 파일 목록 및 역할 추적 | - |
| .claude/rules/coding.md | 코딩 스타일 및 수정 규칙 | - |
| .claude/rules/security.md | 환경 및 보안 규칙 | - |
| .claude/rules/structure.md | 파일 구조 및 디렉토리 규칙 | - |
| INSTALL_GUIDE.md | 라즈베리파이 5 / Lite OS 설치·운영 매뉴얼 | 2026-09-10 |
| README.md | 프로젝트 개요, 기능, 빠른 시작 | 2026-09-10 |
| app.py | Flask 진입점 — 라우트, 모니터 스케줄러 | 2026-09-10 |
| config/settings.py | 환경변수 로드 및 전역 상수 정의 | 2026-09-10 |
| config/.env.template | 환경변수 템플릿 (실제 값은 config/.env, git 제외) | 2026-09-10 |
| requirements.txt | 파이썬 의존성 목록 | 2026-09-10 |
| services/__init__.py | 서비스 패키지 export | 2026-09-10 |
| services/data_service.py | bus_stops / commute_stops / app_settings JSON 읽기·쓰기 | 2026-09-10 |
| services/weather_service.py | 기상청 단기예보 API 조회 및 캐시 | 2026-09-10 |
| services/bus_service.py | 서울시 버스 도착 정보 API 조회 및 캐시 | 2026-09-10 |
| services/holiday_service.py | 공공데이터 공휴일 API 조회 | 2026-09-10 |
| services/image_service.py | 미디어 목록 탐색 및 썸네일 생성 | 2026-09-10 |
| services/monitor_service.py | 모니터 전원 제어 (DPMS: vcgencmd → wlopm → xset → wlr-randr) | 2026-09-10 |
| services/network_service.py | Wi-Fi 자동 연결 및 상태 조회 (nmcli) | 2026-09-18 |
| templates/*.html | 페이지 템플릿 (base/main/bus/commute/settings/error) | 2026-09-10 |
| static/css/*.css | 디자인 토큰 및 페이지별 스타일 | 2026-09-10 |
| static/js/**/*.js | API 클라이언트, 시계·슬라이드쇼 모듈, 페이지 컨트롤러 | 2026-09-10 |
| static/images/weather/*.png | 날씨 아이콘 12종 (기본 플레이스홀더, 자유 교체 가능) | 2026-09-10 |
| static/images/photos/.gitkeep | 슬라이드쇼 사진 폴더 자리표시 (실제 사진은 git 제외) | 2026-09-10 |
| docs/API.md | API 엔드포인트 상세 문서 | 2026-09-10 |
| docs/VARIABLES.md | 설정값/변수 레퍼런스 | 2026-09-10 |
| photoframe.service | systemd 서비스 — Flask 백엔드 부팅 시 자동 시작 | 2026-09-10 |
| display/__init__.py | Pi Vitals 패키지 마커 | 2026-09-13 |
| display/sensors.py | CPU/온도/메모리/디스크/팬RPM 수집 (psutil + hwmon + diskstats) | 2026-09-13 |
| display/renderer.py | Pillow로 세로/가로 · 둥근/막대 게이지 프레임 그리기 | 2026-09-13 |
| display/pi_vitals.py | Pi Vitals 진입점 — SPI 장치 초기화, 메인 루프, 드라이런 폴백 | 2026-09-13 |
| pi-vitals.service | systemd 서비스 — Pi Vitals(ST7789 SPI) 상시 실행 | 2026-09-13 |
| cooling/__init__.py | 외부 릴레이 팬 패키지 마커 | 2026-09-19 |
| cooling/external_fan.py | SoC 온도 기반 외부 릴레이 팬 on/off 제어 (gpiozero) | 2026-09-19 |
| external-fan.service | systemd 서비스 — 외부 릴레이 팬 제어 상시 실행 | 2026-09-19 |
| scripts/kiosk-start.sh | Flask 대기 후 sway 실행하는 진입 스크립트 (Lite OS) | 2026-09-10 |
| scripts/sway.config | 키오스크용 sway 최소 설정 (커서 자동 숨김 등) | 2026-09-11 |
| scripts/kiosk-browser.sh | sway가 exec로 실행하는 Chromium 키오스크 실행 스크립트 | 2026-09-11 |
| Dockerfile | Flask 앱 Docker 이미지 (선택적 배포 방식) | 2026-09-10 |
| docker-compose.yml | Docker Compose 구성 (선택적 배포 방식) | 2026-09-10 |
| .dockerignore | Docker 빌드 제외 목록 | 2026-09-10 |
| .gitignore | git 추적 제외 목록 (API 키, 개인 정류소 정보, 사진, 캐시) | 2026-09-10 |

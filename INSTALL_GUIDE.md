# 라즈베리파이 5 포토프레임 설치 가이드

> 대상: Raspberry Pi 5 + Raspberry Pi OS Lite (64-bit, 데스크톱 없음)
> 방식: GitHub(Git)로 설치, 전원이 꺼졌다 켜져도 자동 실행
> 난이도: 초보자도 따라 할 수 있도록 명령어를 그대로 복사·붙여넣기 하면 됩니다.

---

## 0. 전체 그림 먼저 이해하기

이 프로젝트는 **두 부분**으로 동작합니다.

1. **백엔드(Flask 서버)** — 시계·날씨·버스 정보를 계산해서 웹페이지로 제공. `systemd` 서비스로 등록해 **부팅 시 자동 실행**됩니다.
2. **화면 표시(키오스크 브라우저)** — 라즈베리파이 HDMI 화면에 그 웹페이지를 **자동으로 전체화면**으로 띄웁니다. Lite OS는 데스크톱이 없으므로 `sway`라는 가벼운 화면 프로그램(터치 시 마우스 커서 자동 숨김 지원)을 사용합니다.

둘 다 systemd/자동 로그인으로 등록하면, **전원 차단 → 재연결 시 아무 조작 없이** 시계·날씨·사진 슬라이드쇼가 화면에 뜹니다.

코드는 GitHub 저장소 `https://github.com/happyhajo01/photoframe-businfo` 에 이미 올라가 있으므로, 라즈베리파이에서는 `git clone` 한 줄로 내려받기만 하면 됩니다.

준비물 체크리스트:
- [ ] Raspberry Pi 5 (Raspberry Pi OS Lite 64-bit 설치 완료, 이미 SSH로 접속 가능하거나 키보드/모니터로 접속 가능)
- [ ] 세로로 세울 디스플레이(HDMI) 1대
- [ ] 인터넷 연결 (Wi-Fi 또는 유선랜)
- [ ] PC에서 라즈베리파이로 SSH 접속 가능 (터미널)
- [ ] (선택) 기상청·버스·공휴일 공공데이터포털 API 키 — 없어도 더미(테스트) 데이터로 우선 실행 가능

---

## STEP 1. 라즈베리파이에 SSH로 접속

PC 터미널에서:

```bash
ssh <사용자이름>@raspberrypi.local
```

- `<사용자이름>`은 Raspberry Pi Imager에서 설정한 계정명으로 바꿔주세요.
- `raspberrypi.local`이 안 되면 공유기 관리 페이지에서 라즈베리파이의 IP를 확인해 `ssh <사용자이름>@<IP주소>`로 접속하세요.
- SSH가 꺼져 있다면: `sudo raspi-config` → `Interface Options` → `SSH` → `Enable`.

이후 모든 명령어는 **라즈베리파이 SSH 터미널 안에서** 실행합니다.

### (선택) 유선 랜이 끊겼을 때를 대비한 와이파이 백업 연결

유선(이더넷)이 기본이더라도, 케이블이 빠지는 상황을 대비해 와이파이를 미리 등록해두면 자동으로 전환됩니다. 지금(유선 연결된 상태)에서 미리 설정해두세요.

```bash
sudo raspi-config
```
메뉴에서 `1 System Options` → `S1 Wireless LAN` → SSID·비밀번호 입력 → `Finish`.

- 유선과 와이파이가 둘 다 등록돼 있으면, 유선이 뽑혔을 때 자동으로 와이파이로 전환됩니다(둘 다 안 잡혀있으면 당연히 원격 접속 자체가 불가능하니 최초 등록은 꼭 유선이 연결된 상태에서 해두세요).
- 설정 후 확인: `hostname -I`로 와이파이 IP가 잡히는지, 이더넷 케이블을 뽑고 `ping`으로 계속 응답하는지 테스트해보세요.

---

## STEP 2. 콘솔 자동 로그인 설정 (화면 자동 표시를 위한 필수 설정)

Lite OS는 로그인 화면에서 멈춰 있으므로, 부팅 시 자동으로 로그인되도록 설정해야 키오스크 화면이 자동으로 뜹니다.

```bash
sudo raspi-config
```

메뉴에서 순서대로 선택:
1. `1 System Options`
2. `S5 Boot / Auto Login`
3. `B2 Console Autologin` (텍스트 콘솔에 자동 로그인)
4. `Finish` → 재부팅 여부는 "아니오"(뒤에서 한번에 재부팅합니다)

---

## STEP 3. 시스템 업데이트 및 필수 패키지 설치

```bash
    sudo apt update && sudo apt full-upgrade -y
```

```bash
# 공통 필수 패키지
sudo apt install -y git python3-venv python3-pip python3-dev \
    build-essential libjpeg-dev zlib1g-dev libwebp-dev \
    curl fonts-noto-cjk

# 화면 표시용 키오스크 패키지 (sway: 터치 시 마우스 커서 자동 숨김 지원)
sudo apt install -y sway

# 크롬 브라우저 설치 (패키지 이름이 배포판마다 달라 둘 다 시도)
sudo apt install -y chromium-browser || sudo apt install -y chromium
```

> `fonts-noto-cjk`는 한글이 화면에 깨지지 않고 나오게 하는 한글 글꼴입니다.

---

## STEP 4. 프로젝트 코드 내려받기 (git clone)

```bash
cd ~
git clone https://github.com/happyhajo01/photoframe-businfo.git
cd photoframe-businfo
```

---

## STEP 5. 파이썬 가상환경 및 라이브러리 설치

```bash
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

몇 분 정도 걸릴 수 있습니다 (Pillow 등 설치).

---

## STEP 6. 환경 설정 파일(.env) 작성

```bash
cp config/.env.template config/.env
nano config/.env
```

`nano` 편집기 조작법: 방향키로 이동 → 값 수정 → `Ctrl+O`(저장) → `Enter` → `Ctrl+X`(종료)

채워야 할 항목:

| 항목 | 설명 |
|------|------|
| `WEATHER_API_KEY` | 공공데이터포털의 "기상청_단기예보 조회서비스" API 키 |
| `HOLIDAY_API_KEY` | 공공데이터포털의 "특일 정보" API 키 |
| `BUS_API_KEY` | 공공데이터포털의 "서울특별시_버스도착정보" API 키 |
| `SECRET_KEY` | 아무 임의의 긴 문자열 (아래 명령으로 생성) |
| `WEATHER_NX` / `WEATHER_NY` | 내가 사는 지역의 기상청 격자 좌표 |

**API 키 발급:** [공공데이터포털](https://www.data.go.kr) 에서 회원가입 후 위 3개 서비스를 검색해 "활용 신청"하면 됩니다. 승인까지 몇 분~몇 시간 걸릴 수 있습니다.

**SECRET_KEY 랜덤 생성:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
나온 값을 복사해 `config/.env`의 `SECRET_KEY=` 뒤에 붙여넣으세요.

**지역별 기상청 격자 좌표 (README 참고):**

| 지역 | NX | NY |
|------|----|----|
| 서울 노원 | 61 | 127 |
| 서울 강남 | 61 | 125 |
| 수원 | 60 | 121 |
| 부산 | 98 | 76 |

다른 지역은 [기상청 격자 좌표 조회 도구](https://www.weather.go.kr/w/resources/viewer/grid_map_download.do)에서 확인하세요.

> **API 키가 아직 없어도 괜찮습니다.** `.env` 값을 템플릿 그대로(한글 안내문구) 두면 앱이 자동으로 감지해서 **테스트용 더미 데이터**로 동작합니다. 나중에 키를 받으면 다시 채워 넣고 서비스만 재시작하면 됩니다.
>
> ⚠️ **버스 도착 정보는 서울시 버스만 지원**합니다. 서울 외 지역이라면 버스 기능은 꺼두거나 더미 데이터로 참고용으로만 사용하세요.

---

## STEP 7. 사진 · 동영상 추가

**PC에서** 사진을 라즈베리파이로 복사합니다 (PC 터미널에서 실행, 사용자이름/IP는 본인 것으로 변경):

```bash
scp -r "내사진폴더경로"/* <사용자이름>@raspberrypi.local:~/photoframe-businfo/static/images/photos/
```

지원 형식: `.jpg .jpeg .png .gif .bmp .webp` (이미지), `.mp4 .webm .mov .avi .mkv` (동영상)
사진은 하위 폴더에 넣어도 자동으로 인식됩니다.

> 날씨 아이콘은 `static/images/weather/`에 기본 세트가 이미 포함되어 있어 이 단계에서 별도로 준비할 필요는 없습니다. 나중에 마음에 드는 아이콘으로 바꾸고 싶다면 같은 파일명으로 덮어쓰면 됩니다.

---

## STEP 8. 백엔드 자동 실행 등록 (systemd)

프로젝트에 이미 서비스 파일(`photoframe.service`)이 포함되어 있습니다. 현재 계정 이름에 맞게 경로만 자동으로 바꿔서 등록합니다.

```bash
sed -e "s#/home/pi#$HOME#g" -e "s#^User=pi#User=$USER#" \
    ~/photoframe-businfo/photoframe.service | sudo tee /etc/systemd/system/photoframe.service

sudo systemctl daemon-reload
sudo systemctl enable --now photoframe.service
```

상태 확인 (`active (running)`이면 정상):

```bash
sudo systemctl status photoframe.service
```

브라우저 없이도 서버가 응답하는지 확인:

```bash
curl -s http://localhost:5000/ | head -5
```

---

## STEP 9. 화면 자동 표시 (키오스크) 설정

`sway`(터치 시 마우스 커서 자동 숨김을 지원하는 화면 합성기)로 Chromium을 띄우는 스크립트가 `scripts/kiosk-start.sh`로 이미 프로젝트에 포함되어 있습니다. 실행 권한만 주고, 콘솔에 자동 로그인될 때 실행되도록 등록합니다.

### 9-1. 실행 권한 부여

```bash
chmod +x ~/photoframe-businfo/scripts/kiosk-start.sh ~/photoframe-businfo/scripts/kiosk-browser.sh
```

### 9-2. 콘솔 자동 로그인 시 스크립트 실행 등록

콘솔(tty1)에 자동 로그인될 때만 키오스크를 실행하고, SSH 등 다른 로그인은 평소처럼 동작하게 합니다.

```bash
cat > ~/.bash_profile <<'EOF'
if [ -z "$SSH_CONNECTION" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec ~/photoframe-businfo/scripts/kiosk-start.sh
fi
[ -f ~/.bashrc ] && . ~/.bashrc
EOF
```

### 9-3. 화면 권한 확인

키오스크 계정이 화면 장치 그룹에 속해 있는지 확인합니다 (보통 기본 계정은 이미 포함되어 있습니다):

```bash
groups $USER
# video, render, input 이 안 보이면 아래 실행 후 재부팅
sudo usermod -aG video,render,input $USER
```

---

## STEP 10. 재부팅 테스트

```bash
sudo reboot
```

30초~1분 정도 기다리면:
1. 콘솔에 자동 로그인됨
2. Flask 서버(`photoframe.service`)가 백그라운드에서 시작됨
3. `sway`가 Chromium을 전체화면으로 띄우고 포토프레임 메인 화면(시계·날씨·슬라이드쇼)이 표시됨

**전원 플러그를 완전히 뽑았다가 다시 꽂아서도** 동일하게 자동 실행되는지 한 번 더 확인해보세요. 이것이 정상적으로 되면 설치가 끝난 것입니다.

---

## 사용법 (동작 방법)

### 화면 구성

| 화면 | 접속 방법(직접 조작 시) | 내용 |
|------|--------|------|
| 메인 | 기본 화면 | 큰 시계, 날씨, 사진/영상 슬라이드쇼, 날짜(공휴일 빨강/토요일 파랑) |
| 정류소 | 메인 화면 하단 버튼 | 등록된 정류소들의 버스 도착 정보, 3분 이하 빨강·4분 이하 파랑 강조 |
| 출근 | 메인 화면 하단 버튼 | 출근용으로 지정한 노선만 크게 표시 |
| 설정 | `/settings` 페이지 접속 | 정류소·슬라이드 간격·모니터 시간 등 각종 설정 |

키오스크 화면에는 마우스/키보드가 없어도 되지만, 같은 네트워크의 **다른 PC나 스마트폰 브라우저**로도 접속해서 설정할 수 있습니다:

```
http://raspberrypi.local:5000
```
(안 되면 `http://<라즈베리파이IP>:5000`, IP는 라즈베리파이에서 `hostname -I`로 확인)

### 키보드 단축키 (외부 기기로 키오스크 화면에 키보드 연결 시)

| 키 | 화면 | 동작 |
|----|------|------|
| `←` / `→` | 메인 | 이전/다음 사진 |
| `Space` | 메인 | 전환 효과 토글 |
| `Ctrl+S` | 설정 | 설정 저장 |

### 설정 페이지에서 할 수 있는 것 (`/settings`)

- **정류소 추가/삭제**: 정류소 이름, 정류소 ID, 관심 버스 번호 등록
- **출근 정류소 지정**: 출근길에 자주 타는 노선만 별도 등록
- **슬라이드 간격**: 사진이 넘어가는 주기(초)
- **버스 정보 갱신 주기**: 기본 60초
- **자동 복귀 시간**: 정류소/출근 화면에서 아무 조작 없으면 메인으로 돌아가는 시간
- **모니터 자동 ON/OFF 시간**: 예) 23:50에 꺼지고 05:10에 켜짐 (전기 절약)
- **야간 모드**: 지정 시간 동안 화면을 완전히 검게
- **슬라이드 전환 효과**: 8가지 효과 중 원하는 것만 선택

### 사진 추가/삭제 (운영 중)

PC에서 아무 때나 다음처럼 전송하면 **재시작 없이 바로 반영**됩니다:

```bash
scp 새사진.jpg <사용자이름>@raspberrypi.local:~/photoframe-businfo/static/images/photos/
```

삭제하려면 라즈베리파이에서:

```bash
rm ~/photoframe-businfo/static/images/photos/삭제할파일.jpg
```

### 서비스 관리 명령어 모음 (라즈베리파이 SSH에서)

```bash
# 상태 확인
sudo systemctl status photoframe.service

# 재시작 (설정 변경 후, 오류 발생 시)
sudo systemctl restart photoframe.service

# 중지 / 재시작 중지
sudo systemctl stop photoframe.service

# 실시간 로그 보기 (오류 확인용, Ctrl+C로 종료)
journalctl -u photoframe.service -f

# 최근 로그 100줄만 보기
journalctl -u photoframe.service -n 100 --no-pager
```

### 업데이트 방법 (코드 최신화)

PC에서 코드를 수정하고 GitHub에 올린 뒤, 라즈베리파이에서:

```bash
cd ~/photoframe-businfo
git pull
./venv/bin/pip install -r requirements.txt   # 새 라이브러리가 추가된 경우만
sudo systemctl restart photoframe.service
sudo reboot   # 화면 표시 쪽 코드가 바뀐 경우
```

### 날씨 캐시 강제 초기화 (날씨가 이상할 때)

```bash
rm ~/photoframe-businfo/data/weather_cache.json
sudo systemctl restart photoframe.service
```

---

## 문제 해결 (자주 겪는 문제)

| 증상 | 원인 / 해결 |
|------|------------|
| 화면이 검은 화면/커서만 보임 | `journalctl -u photoframe.service -n 50`로 서버가 켜졌는지 확인. 켜졌다면 `sway`/`chromium` 설치 여부, `groups $USER`에 `video` 있는지 확인 후 재부팅 |
| 부팅해도 로그인 화면에서 멈춤 | STEP 2의 `raspi-config` → Console Autologin 재확인 |
| SSH로는 잘 되는데 화면엔 안 뜸 | `~/.bash_profile`이 정확히 생성됐는지, tty1 로그인인지 확인(`tty` 명령으로 확인) |
| 한글이 네모(□)로 깨짐 | `sudo apt install fonts-noto-cjk` 후 재부팅 |
| 버스/날씨 정보가 "정보 없음" | `.env`의 API 키가 실제 발급받은 값인지 확인. 발급 후 몇 분~몇 시간 지연될 수 있음 |
| 포트 5000 충돌 오류 | `sudo systemctl restart photoframe.service` (systemd가 자동으로 재시작을 처리함) |
| 전원 재연결 후 화면 안 뜸 | STEP 10을 다시 수행해 "전원 플러그 뽑았다 꽂기" 테스트로 재현 후, `journalctl -u photoframe.service -b`(이번 부팅 로그)로 원인 확인 |
| 세로 모니터인데 화면이 가로로 나옴 | 앱이 CSS로 자동 회전한다(`kiosk-start.sh`가 `?kiosk=1`로 접속). 화면이 뒤집혀 보이면 `static/css/base.css`의 `html.kiosk-rotate body` 블록에서 `rotate(90deg)`/`translate(100vw, 0)`를 `rotate(-90deg)`/`translate(0, 100vh)`로 바꾸고 서비스 재시작·재부팅 |

---

## 부록: 주요 파일 위치 요약

| 위치 | 내용 |
|------|------|
| `~/photoframe-businfo/config/.env` | API 키, 서버 설정 (직접 작성) |
| `~/photoframe-businfo/static/images/photos/` | 슬라이드쇼 사진·동영상 |
| `~/photoframe-businfo/data/*.json` | 정류소·설정 데이터 (설정 페이지에서 자동 저장) |
| `~/photoframe-businfo/scripts/kiosk-start.sh` | 화면 자동 표시 진입 스크립트 (저장소에 포함) |
| `~/photoframe-businfo/scripts/sway.config` | 키오스크용 sway 설정 (저장소에 포함) |
| `~/photoframe-businfo/scripts/kiosk-browser.sh` | Chromium 키오스크 실행 스크립트 (저장소에 포함) |
| `~/.bash_profile` | 콘솔 자동 로그인 시 키오스크 실행 트리거 (이번 가이드에서 생성) |
| `/etc/systemd/system/photoframe.service` | 백엔드 자동 실행 등록 파일 |

---

## 완료 체크리스트

- [ ] `photoframe.service` `active (running)` 상태 확인
- [ ] 브라우저로 `http://raspberrypi.local:5000` 접속 성공
- [ ] 재부팅 후 자동으로 키오스크 화면 표시 확인
- [ ] 전원 플러그 뽑았다 꽂기 테스트 통과
- [ ] `.env`에 실제 API 키 입력 (또는 더미 데이터로 우선 운영 결정)
- [ ] 원하는 사진/동영상 업로드 완료
- [ ] 설정 페이지에서 정류소·슬라이드 간격 등 커스터마이징 완료

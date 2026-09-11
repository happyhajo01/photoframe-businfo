#!/bin/bash
# 콘솔(tty1) 자동 로그인 시 ~/.bash_profile에서 호출된다.
# Flask 서버가 응답할 때까지 대기한 뒤, sway(Wayland 키오스크 컴포지터)로
# Chromium을 전체화면 실행한다. Raspberry Pi OS Lite(데스크톱 없음) 전용.
# sway는 터치 입력 시 마우스 커서를 자동으로 숨겨준다 (cage는 이 기능이 없음).

URL="http://localhost:5000/?kiosk=1"
TIMEOUT=90
ELAPSED=0

until curl -sf "$URL" > /dev/null 2>&1; do
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

exec sway --config "$(dirname "$0")/sway.config"

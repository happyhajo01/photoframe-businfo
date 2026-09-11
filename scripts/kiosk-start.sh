#!/bin/bash
# 콘솔(tty1) 자동 로그인 시 ~/.bash_profile에서 호출된다.
# Flask 서버가 응답할 때까지 대기한 뒤, cage(Wayland 키오스크 컴포지터)로
# Chromium을 전체화면 실행한다. Raspberry Pi OS Lite(데스크톱 없음) 전용.

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

BROWSER_CMD=""
if   command -v chromium-browser &>/dev/null; then BROWSER_CMD="chromium-browser"
elif command -v chromium          &>/dev/null; then BROWSER_CMD="chromium"
fi

exec cage -s -- "$BROWSER_CMD" \
    --start-fullscreen \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-features=TranslateUI \
    --check-for-update-interval=604800 \
    --ozone-platform=wayland \
    --password-store=basic \
    --remote-debugging-port=9222 \
    --remote-debugging-address=0.0.0.0 \
    --remote-allow-origins=* \
    "$URL"

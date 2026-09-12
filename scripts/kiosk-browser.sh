#!/bin/bash
# sway.config의 exec로 실행된다. Chromium을 키오스크 모드로 띄운다.

URL="http://localhost:5000/?kiosk=1"

BROWSER_CMD=""
if   command -v chromium-browser &>/dev/null; then BROWSER_CMD="chromium-browser"
elif command -v chromium          &>/dev/null; then BROWSER_CMD="chromium"
fi

# chromium이 죽어도 화면이 검게 남지 않도록 계속 재시작한다.
while true; do
    "$BROWSER_CMD" \
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
        "$URL"
    sleep 2
done

#!/bin/bash
# Headless 截圖:Xvfb + Mesa 軟體 GL 跑 xu4,抓 root window 存 /out/screen.png
set -u
export DISPLAY=:99
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe
export ALLEGRO_AUDIO_DRIVER=none

WAIT="${1:-8}"          # 啟動後等幾秒再截圖
SCALE="${2:-3}"         # xu4 顯示縮放(1-5);Xvfb 尺寸隨之對齊
XU4_ARGS="${3:-}"       # 額外 xu4 參數(如 --skip-intro);可自帶 --filter 覆蓋預設

# 預設平滑放大 filter(灰階 CJK AA 最佳);若第 3 參數已含 --filter 則不重複
FILTER_DEFAULT="--filter xBRZ"
case " $XU4_ARGS " in *" --filter "*) FILTER_DEFAULT="" ;; esac

W=$((320 * SCALE)); H=$((200 * SCALE))
Xvfb :99 -screen 0 ${W}x${H}x24 -ac +extension GLX +render -noreset >/out/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 2

cd /build/xu4
CMD="./src/xu4 -q -v -s $SCALE $FILTER_DEFAULT $XU4_ARGS"
echo "+ $CMD" >/out/xu4.log
$CMD >>/out/xu4.log 2>&1 &
XU4_PID=$!

sleep "$WAIT"

if import -window root /out/screen.png 2>/out/import.log; then
  echo "screenshot OK (import)"
elif xwd -root -silent 2>/dev/null | convert xwd:- /out/screen.png 2>>/out/import.log; then
  echo "screenshot OK (xwd)"
else
  echo "screenshot FAILED"; cat /out/import.log
fi

kill "$XU4_PID" 2>/dev/null
kill "$XVFB_PID" 2>/dev/null
echo "--- xu4.log tail ---"; tail -15 /out/xu4.log

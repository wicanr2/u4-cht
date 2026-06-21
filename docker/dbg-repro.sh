#!/bin/bash
# 在 u4cht/debug 容器內:xvfb + twm,跑 xu4(-g)於 gdb,自動跳過片頭→按 F2 重現 crash,
# SIGSEGV 時 dump backtrace 與關鍵變數(mode / binData / beastiesImg / tileset)。
# 用法:docker run --rm -v /tmp/u4dbg:/out --entrypoint bash u4cht/debug docker/dbg-repro.sh
#   (或把本檔 mount 進去)。輸出在 /out/gdb.log。第 1 參數 = 額外 xu4 參數(預設 -s 2)。
set -u
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe ALLEGRO_AUDIO_DRIVER=none
ARGS="${1:--s 2 --filter xBRZ}"
Xvfb :99 -screen 0 1280x800x24 -ac +extension GLX +render -noreset >/out/xvfb.log 2>&1 &
sleep 2
twm >/out/twm.log 2>&1 &
sleep 1
cd /build/xu4

# 背景送鍵:等視窗 → 跳過片頭(space 進 INTRO_MAP)→ F2
(
  for i in $(seq 1 40); do WID=$(xdotool search --name Ultima 2>/dev/null | head -1); [ -n "$WID" ] && break; sleep 0.5; done
  echo "WID=$WID" >/out/keys.log
  sleep 7
  xdotool windowactivate --sync "$WID" 2>>/out/keys.log
  xdotool windowfocus "$WID" 2>>/out/keys.log; sleep 0.5
  for k in space space; do xdotool key --clearmodifiers "$k" 2>>/out/keys.log; sleep 1; done
  echo "=== F2 ===" >>/out/keys.log
  xdotool key --clearmodifiers F2 2>>/out/keys.log
  sleep 5
) &

gdb -batch -nx \
  -ex "set pagination off" -ex "set print pretty on" \
  -ex run \
  -ex "echo \n##### SIGNAL / BT #####\n" -ex "bt" \
  -ex "echo \n##### frame 2 (intro draw) #####\n" -ex "frame 2" \
  -ex "print mode" -ex "print this->binData" -ex "print this->beastiesImg" \
  -ex "print this->beastiesVisible" -ex "info locals" \
  -ex "echo \n##### frame 1 #####\n" -ex "frame 1" -ex "info args" -ex "info locals" \
  -ex "echo \n##### frame 0 #####\n" -ex "frame 0" -ex "info args" \
  --args ./src/xu4 $ARGS >/out/gdb.log 2>&1
echo "=== EXIT $? ===" >>/out/gdb.log

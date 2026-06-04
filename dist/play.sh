#!/bin/bash
# 桌面遊玩(Docker + X11 forwarding)。需本機 X11。
#   U4CHT_FONT=firefly bash dist/play.sh
set -e
xhost +local:docker >/dev/null 2>&1 || true
docker run --rm -it \
  -e DISPLAY="$DISPLAY" -e U4CHT_FONT="${U4CHT_FONT:-}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --entrypoint /build/xu4/src/xu4 u4cht/xu4-allegro -s 2 --filter xBRZ

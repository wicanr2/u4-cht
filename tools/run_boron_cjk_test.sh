#!/bin/bash
# 在 u4cht/xu4-allegro image(已含 libboron + headers)內編譯並執行
# tools/test_boron_cjk.cpp —— vendor 商店對白 CJK 編碼轉換的回歸測試。
# 用法:bash tools/run_boron_cjk_test.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMG="${IMG:-u4cht/xu4-allegro}"

docker run --rm -v "$ROOT/tools":/t -w /t --entrypoint bash "$IMG" -c '
  set -e
  g++ -std=c++11 -I/usr/include test_boron_cjk.cpp -o /tmp/test_boron_cjk \
      -lboron -lpthread -lm -lz
  /tmp/test_boron_cjk
'

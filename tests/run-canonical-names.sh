#!/bin/bash
# 在容器內編譯並執行 canonical_names_test。
# 用法:bash tests/run-canonical-names.sh <已套 apply_cht.sh 的 xu4 目錄>
# 需要 u4cht/xu4-allegro 映像(docker/Dockerfile.zh),只用它的 g++。
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
XU4="$(cd "${1:?要指定 xu4 目錄}" && pwd)"
test -f "$XU4/src/names.cpp"
test -f "$ROOT/assets/u4_cht.tab"
timeout 300 docker run --rm --network none \
  --user "$(id -u):$(id -g)" --memory 2g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -v "$ROOT":/repo:ro -v "$XU4":/xu4:ro -e U4CHT_DIR=/repo/assets/ -w /tmp \
  --entrypoint sh u4cht/xu4-allegro -c '
    g++ -std=c++11 -I/xu4/src -I/repo/patches/engine \
      /repo/tests/canonical_names_test.cpp /xu4/src/names.cpp \
      /repo/patches/engine/cht.cpp -o /tmp/canonical_names_test \
    && /tmp/canonical_names_test'

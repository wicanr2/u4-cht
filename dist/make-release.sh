#!/bin/bash
# 從 u4cht/xu4-allegro image 產出 Linux 可執行包 tarball。
# 用法:bash dist/make-release.sh [輸出.tar.gz]
set -e
OUT="${1:-/tmp/u4-cht-linux-x86_64.tar.gz}"
TMP="$(mktemp -d)/u4-cht-linux"; mkdir -p "$TMP"
docker run --rm -v "$TMP":/out --entrypoint bash u4cht/xu4-allegro -c '
  cp /build/xu4/src/xu4 /out/
  cp /build/xu4/Ultima-IV.mod /build/xu4/U4-Upgrade.mod /build/xu4/render.pak /out/
  cp /build/xu4/cjk_font*.bin /build/xu4/u4_cht.tab /out/
  cp /build/xu4/ultima4.zip /build/xu4/u4upgrad.zip /out/ 2>/dev/null || true
  cp -L /usr/lib/x86_64-linux-gnu/libfaun.so.0 /out/'
cat > "$TMP/run.sh" <<'RUN'
#!/bin/bash
# 需系統:sudo apt install liballegro5.2 liballegro-acodec5.2 liballegro-audio5.2 libpng16-16 libvorbisfile3
# 字形切換:U4CHT_FONT=firefly|kai ./run.sh
cd "$(dirname "$0")"; LD_LIBRARY_PATH=".:$LD_LIBRARY_PATH" ./xu4 "$@"
RUN
chmod +x "$TMP/run.sh"
tar czf "$OUT" -C "$(dirname "$TMP")" u4-cht-linux
echo "→ $OUT ($(du -h "$OUT" | cut -f1))"

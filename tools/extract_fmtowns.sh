#!/usr/bin/env bash
# 從使用者自有的 FM Towns 光碟(.chd)抽出 FM Towns 主題資產並設定 U4-FMTowns 模組。
#   - tileset:ULTIMA4.TIL → fmt_tileset.png(build_fmtowns_tileset.py)
#   - 音樂:CD-DA 2 軌 → ogg(chdman + bchunk + ffmpeg)
#   - intro:U4OPEN/*.TIF(標準 TIFF)→ PNG
#   - 模組:複製 tools/fmtowns/module 的 config.b/graphics.b + 放 tileset/音樂
#
# 需工具:chdman(mame-tools)、bchunk、ffmpeg、7z、PIL → 走 docker image u4cht/extract
#   (見 docker/Dockerfile.extract)。FM Towns 光碟與抽出資產屬版權資料,不入 repo。
#
# 用法(在 repo root):
#   bash tools/extract_fmtowns.sh <xu4_dir> <fmtowns_chd>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
XU4="${1:?需 xu4 目錄}"
CHD="${2:?需 FM Towns .chd}"
WORK="$(mktemp -d)"
MOD="$XU4/module/U4-FMTowns"

echo "[1/5] chdman 抽 CD 軌"
chdman extractcd -i "$CHD" -o "$WORK/u4.cue" -ob "$WORK/u4.bin" >/dev/null

echo "[2/5] 抽 iso 資料軌 + bchunk 音軌"
( cd "$WORK" && bchunk -w u4.bin u4.cue trk >/dev/null )
7z x -y -o"$WORK/iso" "$WORK/trk01.iso" >/dev/null 2>&1

echo "[3/5] 解碼 tileset(ULTIMA4.TIL → fmt_tileset.png)"
TIL=$(find "$WORK/iso" -iname ULTIMA4.TIL | head -1)
mkdir -p "$MOD/image/vga" "$MOD/music"
python3 "$ROOT/tools/build_fmtowns_tileset.py" --til "$TIL" --out "$MOD/image/fmt_tileset.png"

echo "[4/5] CD 音樂 → ogg(2 軌)"
i=0
for w in "$WORK"/trk0[2-9].wav; do
    [ -f "$w" ] || continue
    i=$((i+1))
    name=$([ $i -eq 1 ] && echo fmt_main || echo fmt_town)
    ffmpeg -y -loglevel error -i "$w" -q:a 5 "$MOD/music/${name}.ogg"
done

echo "[5/5] 模組 def + intro"
cp "$ROOT/tools/fmtowns/module/config.b" "$ROOT/tools/fmtowns/module/graphics.b" "$MOD/"
cp "$XU4/module/U4-Upgrade/image/vga/tile_guard.png" "$MOD/image/vga/tile_guard.png"
# intro TIFF → PNG(供日後 intro 主題;放本機 materals,不入模組)
INTRO="$ROOT/materals/_extracted/fmtowns/intro"; mkdir -p "$INTRO"
find "$WORK/iso" -iname '*.TIF' -exec sh -c \
  'ffmpeg -y -loglevel error -i "$1" "'"$INTRO"'/$(basename "${1%.TIF}").png"' _ {} \; 2>/dev/null || true

rm -rf "$WORK"
echo "完成:U4-FMTowns 模組已設定(tileset + 音樂)。Makefile 需含 U4-FMTowns.mod。"

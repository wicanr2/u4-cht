#!/bin/bash
# 把 U4 繁中化(cht)套到一份乾淨的 xu4 clone:
#   - 複製 cht.cpp / cht.h
#   - 套 screen.cpp / project.b / Makefile.common patch
#   - 產生並複製 CJK 字型 atlas + en→zh lookup 到 xu4/(build context)
# 用法:bash tools/apply_cht.sh [xu4_dir]
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
XU4="${1:-$ROOT/xu4}"

echo "[1/3] 複製 cht 原始碼"
cp "$ROOT/patches/engine/cht.cpp" "$ROOT/patches/engine/cht.h" "$XU4/src/"

echo "[2/3] 套引擎 patch"
git -C "$XU4" apply --check "$ROOT/patches/engine/cht-engine.patch" 2>/dev/null \
  && git -C "$XU4" apply "$ROOT/patches/engine/cht-engine.patch" \
  || patch -d "$XU4" -p1 < "$ROOT/patches/engine/cht-engine.patch"

echo "[3/3] 產生並安裝資產"
# 三套 CJK atlas:Noto(預設)+ AR PL 宋(firefly)/ 楷(kai)。字集涵蓋 6 份雙語表
# (含 castle/ui),新增字後須刪 .bin 重建。重建環境見 docker/Dockerfile.font。
# 字型路徑可由環境變數覆寫(Mac / Android CI 的 Noto 不在 Linux 預設路徑)。
NOTO="${NOTO:-/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc}"
BSMI="${BSMI:-/usr/share/fonts/truetype/arphic-bsmi00lp/bsmi00lp.ttf}"
BKAI="${BKAI:-/usr/share/fonts/truetype/arphic-bkai00mp/bkai00mp.ttf}"
NOTO_INDEX="${NOTO_INDEX:-3}"
if [ ! -f "$ROOT/assets/cjk_font.bin" ] && [ -f "$NOTO" ]; then
  python3 "$ROOT/tools/build_cjk_font.py" --font "$NOTO" --index "$NOTO_INDEX" --size 22 --cell 24 \
    --out "$ROOT/assets/cjk_font.bin" --preview "$ROOT/assets/cjk_preview.png"
fi
if [ ! -f "$ROOT/assets/cjk_font_firefly.bin" ] && [ -f "$BSMI" ]; then
  python3 "$ROOT/tools/build_cjk_font.py" --font "$BSMI" --size 22 --cell 24 \
    --out "$ROOT/assets/cjk_font_firefly.bin"
fi
if [ ! -f "$ROOT/assets/cjk_font_kai.bin" ] && [ -f "$BKAI" ]; then
  python3 "$ROOT/tools/build_cjk_font.py" --font "$BKAI" --size 22 --cell 24 \
    --out "$ROOT/assets/cjk_font_kai.bin"
fi
# GUI SDF 字型(模組瀏覽器中文化):對乾淨 cfont.png 注入 CJK glyph + 產 cfont-cjk.txf。
# 走 MSDF shader 的 median(r,g,b),單通道 SDF 寫進 R=G=B 即可,毋須 msdfgen。
# 需 numpy/scipy(見 docker/Dockerfile.font)。idempotent:已產則略過。
if [ ! -f "$XU4/module/render/font/cfont-cjk.txf" ] && [ -f "$NOTO" ]; then
  python3 "$ROOT/tools/build_cjk_txf.py" --font "$NOTO" --index "$NOTO_INDEX" \
    --atlas "$XU4/module/render/font/cfont.png" \
    --out-txf "$XU4/module/render/font/cfont-cjk.txf"
fi

[ -f "$ROOT/assets/u4_cht.tab" ] || python3 "$ROOT/tools/build_lookup.py" --out "$ROOT/assets/u4_cht.tab"
# 字形切換:ship Noto(預設)+ Firefly 宋體/楷體(若已建);runtime env U4CHT_FONT 選用
cp "$ROOT"/assets/cjk_font*.bin "$ROOT/assets/u4_cht.tab" "$XU4/"

echo "[4/4] vendor module 中文化(vendors.b 模板 → 中文)"
python3 "$ROOT/tools/patch_vendor_boron.py" \
  --vendors "$XU4/module/Ultima-IV/vendors.b" \
  --bilingual "$ROOT/dumps/vendor_bilingual.json"

# 多平台美術主題(選用):各平台若已用對應解碼器從自有媒體產出 tileset(模組 image/
# 下有 <tileset>.png),就把該 .mod 加進 build;否則 F2 主題循環會優雅跳過該主題。
# 平台:模組名:tileset 檔名(對齊 game.cpp 的 themes[] 與各 tools/<p>/module)。
enable_theme() {   # $1=模組名 $2=tileset 檔名
  local mod="$1" ts="$2"
  [ -f "$XU4/module/$mod/image/$ts" ] || return 0
  echo "[5] 啟用主題 $mod(偵測到 $ts)"
  grep -q "$mod.mod" "$XU4/Makefile" || \
    sed -i "s/^MODULES=\\(.*\\)/MODULES=\\1 $mod.mod/" "$XU4/Makefile"
  grep -q "^$mod.mod:" "$XU4/Makefile" || \
    printf '\n%s.mod: module/%s/*.b module/%s/image/*.png\n\t$(BORON) -s tools/pack-xu4.b module/%s\n' \
      "$mod" "$mod" "$mod" "$mod" >> "$XU4/Makefile"
}
enable_theme U4-FMTowns fmt_tileset.png
enable_theme U4-Amiga   amiga_tileset.png
enable_theme U4-MSX2    msx_tileset.png
enable_theme U4-X68000  x68k_tileset.png
enable_theme U4-SMS     sms_tileset.png

echo "完成。重建:docker build -f docker/Dockerfile.zh -t u4cht/xu4-allegro xu4"
echo "自測截圖:docker run --rm -e U4CHT_SELFTEST=1 -v /tmp/u4shot:/out u4cht/xu4-test 6 3"
echo "FM Towns 主題(選用):bash tools/extract_fmtowns.sh xu4 <FM Towns .chd> 後再 apply + 重建"

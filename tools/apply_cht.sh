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
if [ ! -f "$ROOT/assets/cjk_font.bin" ]; then
  python3 "$ROOT/tools/build_cjk_font.py" \
    --font /usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc --index 3 --size 14 --cell 16 \
    --out "$ROOT/assets/cjk_font.bin" --preview "$ROOT/assets/cjk_preview.png"
fi
[ -f "$ROOT/assets/u4_cht.tab" ] || python3 "$ROOT/tools/build_lookup.py" --out "$ROOT/assets/u4_cht.tab"
# 字形切換:ship Noto(預設)+ Firefly 宋體/楷體(若已建);runtime env U4CHT_FONT 選用
cp "$ROOT"/assets/cjk_font*.bin "$ROOT/assets/u4_cht.tab" "$XU4/"

echo "[4/4] vendor module 中文化(vendors.b 模板 → 中文)"
python3 "$ROOT/tools/patch_vendor_boron.py" \
  --vendors "$XU4/module/Ultima-IV/vendors.b" \
  --bilingual "$ROOT/dumps/vendor_bilingual.json"

echo "完成。重建:docker build -f docker/Dockerfile.zh -t u4cht/xu4-allegro xu4"
echo "自測截圖:docker run --rm -e U4CHT_SELFTEST=1 -v /tmp/u4shot:/out u4cht/xu4-test 6 3"

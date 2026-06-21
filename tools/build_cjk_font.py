#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從四份 zh 翻譯收集實際用到的漢字子集,用 CJK TTF 烘成 16x16 點陣 atlas,
供 xu4 引擎 CHARSET 路徑渲染 CJK。

輸出 assets/cjk_font.bin(自訂二進位,引擎直接 fread):
  magic[8]   "U4CJK\0\1\0"
  uint16 glyphW (16)
  uint16 glyphH (16)
  uint32 count
  records[count]: uint32 codepoint(LE) + glyphW*glyphH bytes(alpha 0/255)
  (codepoint 升序,引擎二分查找)

另存 assets/cjk_preview.png 供人工目視驗證。

用法:
  python3 tools/build_cjk_font.py --font /usr/share/fonts/truetype/arphic/uming.ttc \
      --size 16 --out assets/cjk_font.bin --preview assets/cjk_preview.png
"""
import argparse
import json
import os
import struct
from PIL import Image, ImageFont, ImageDraw

JSON_FILES = ["talk_bilingual", "stringtable_bilingual",
              "hardcoded_strings", "vendor_bilingual",
              "castle_bilingual", "ui_bilingual", "config_bilingual",
              "names_bilingual", "creature_bilingual", "system_bilingual"]


def collect_codepoints():
    cps = set()
    for f in JSON_FILES:
        path = f"dumps/{f}.json"
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding="utf-8"))

        def walk(o):
            if isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, str):
                for ch in o:
                    # 引擎把所有 >= 0x80 的字送 CJK atlas 查找(< 0x80 走原 charset)。
                    # 故凡 >= 0x80 都要收,否則灰框。常見漏網:破折號 —(U+2014)、
                    # 刪節號 …(U+2026)、間隔號 ·(U+00B7)等 < 0x3000 的標點。
                    if ord(ch) >= 0x80:
                        cps.add(ch)
        walk(d)
    return sorted(cps, key=ord)


def render_glyph(font, ch, W, H, mode="gray", threshold=96):
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    # 量測並置中
    bbox = d.textbbox((0, 0), ch, font=font)
    gw, gh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - gw) // 2 - bbox[0]
    y = (H - gh) // 2 - bbox[1]
    d.text((x, y), ch, fill=255, font=font)
    if mode == "binary":
        return img.point(lambda p: 255 if p >= threshold else 0)
    return img   # gray:保留抗鋸齒 alpha(引擎 cjkBlit 以該值混色)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--index", type=int, default=0,
                    help=".ttc face index(Noto Sans CJK TC = 3)")
    ap.add_argument("--size", type=int, default=16,
                    help="字型 glyph 像素大小")
    ap.add_argument("--cell", type=int, default=0,
                    help="atlas cell 邊長(預設 = size);可大於 size 讓 glyph 縮小置中")
    ap.add_argument("--mode", choices=["gray", "binary"], default="gray",
                    help="gray=抗鋸齒 alpha(預設);binary=二值化")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview", default="")
    args = ap.parse_args()

    chars = collect_codepoints()
    font = ImageFont.truetype(args.font, args.size, index=args.index)
    W = H = args.cell if args.cell > 0 else args.size   # cell 可大於字型 → 留邊置中

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    glyphs = []
    for ch in chars:
        g = render_glyph(font, ch, W, H, args.mode)
        glyphs.append((ord(ch), g.tobytes()))

    with open(args.out, "wb") as f:
        f.write(b"U4CJK\0\1\0")
        f.write(struct.pack("<HHI", W, H, len(glyphs)))
        for cp, data in glyphs:
            f.write(struct.pack("<I", cp))
            f.write(data)
    sz = os.path.getsize(args.out)
    print(f"glyphs: {len(glyphs)}  cell {W}x{H}  → {args.out} ({sz} bytes)")

    if args.preview:
        # 前 256 字排成 16x16 grid 預覽
        n = min(256, len(chars))
        cols = 16
        rows = (n + cols - 1) // cols
        prev = Image.new("L", (cols * W, rows * H), 0)
        for i in range(n):
            g = render_glyph(font, chars[i], W, H)
            prev.paste(g, ((i % cols) * W, (i // cols) * H))
        prev.save(args.preview)
        print(f"preview → {args.preview}")


if __name__ == "__main__":
    main()

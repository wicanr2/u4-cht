#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
為 xu4 的 GPU GUI 文字層(MSDF .txf)產生 CJK 子集字型。

模組瀏覽器(xu4_selectGame,遊戲中按 ESC 進入)的固定標籤需要 CJK,
但該畫面走 SDF 紋理字型,既有 cfont.png/.txf 無中文字。本工具:

  1. 對指定的少量 CJK 字以 Noto CJK 算繪高解析遮罩,計算「單通道 SDF」。
     MSDF shader 取 median(r,g,b);把 SDF 同時寫進 R=G=B,median 即還原該 SDF,
     因此單通道即可正確算繪,毋須 msdfgen 的多通道演算法。
  2. 把這些 glyph cell 疊進 cfont.png **底部空白列**(不動既有 95+ 個 ASCII/符號 glyph)。
  3. 依 txf_draw.h 的 TxfHeader / TxfGlyph 版面輸出 cfont-cjk.txf(glyph 依碼位升序,
     供引擎二分查找;既有字型是密集索引,CJK 碼位稀疏故走查找路徑)。

格式參數對照既有 cfont-comfortaa.txf:fontSize=24、pixelRange=4、t 軸 = 1 - row/texH。

用法:
  python3 tools/build_cjk_txf.py \
      --font /usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc --index 3 \
      --atlas xu4/module/render/font/cfont.png \
      --out-txf xu4/module/render/font/cfont-cjk.txf
"""
import argparse
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import distance_transform_edt

# 模組瀏覽器標籤所需字(去重):遊戲模組 / 開始 / 離開 / 取消
DEFAULT_CHARS = "遊戲模組開始離取消"

FONT_SIZE = 24.0       # px per EM(對齊既有 .txf)
PIXEL_RANGE = 4.0      # SDF 擴散(px)
SS = 8                 # 超取樣倍率(高解析遮罩 → 乾淨 SDF)
LINE_HEIGHT = 1.20     # CJK 行高(僅當 CJK 為 active font 時生效;此處備值)
ASCENDER = 0.88
DESCENDER = -0.12


def glyph_sdf(font, ch):
    """回傳 (sd_target[h,w] float in [0,1], emRect[4], adv) 或 None(空白字)。"""
    px = int(FONT_SIZE * SS)
    pad_hi = int(round(PIXEL_RANGE * SS))
    asc, desc = font.getmetrics()           # hi-res 像素
    canvas_w = px + 4 * pad_hi
    canvas_h = asc + desc + 4 * pad_hi
    origin_x = 2 * pad_hi                    # pen x=0 對應 canvas x
    base_y = 2 * pad_hi + asc                # 基線 row(top-down)

    img = Image.new("L", (canvas_w, canvas_h), 0)
    d = ImageDraw.Draw(img)
    # anchor 'ls' = left-baseline:(origin_x, base_y) 即 pen 原點 + 基線
    d.text((origin_x, base_y), ch, font=font, fill=255, anchor="ls")

    bbox = img.getbbox()
    if bbox is None:
        return None
    l, t, r, b = bbox
    # 以 SDF 邊界外擴
    cl, ct = l - pad_hi, t - pad_hi
    cr, cb = r + pad_hi, b + pad_hi
    crop = img.crop((cl, ct, cr, cb))
    mask = np.array(crop) >= 128

    inside = distance_transform_edt(mask)
    outside = distance_transform_edt(~mask)
    sd_hi = (inside - outside) / SS          # 轉成 target px 的有號距離
    sd_norm = np.clip(0.5 + sd_hi / PIXEL_RANGE, 0.0, 1.0).astype(np.float32)

    # 高解析 → target 解析(SS 倍縮小)
    th = max(1, round((cb - ct) / SS))
    tw = max(1, round((cr - cl) / SS))
    sd_img = Image.fromarray((sd_norm * 255).astype(np.uint8), "L").resize(
        (tw, th), Image.BILINEAR)
    sd_target = np.array(sd_img).astype(np.float32) / 255.0

    # emRect(EM,基線=0,上為正,pen x=0 在 origin_x):cell 含 pad 外擴
    fs_hi = FONT_SIZE * SS
    emL = (cl - origin_x) / fs_hi
    emR = (cr - origin_x) / fs_hi
    emTop = (base_y - ct) / fs_hi
    emBot = (base_y - cb) / fs_hi
    return sd_target, (emL, emBot, emR, emTop), 1.0   # CJK 全形 advance=1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", required=True)
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--atlas", required=True, help="既有 cfont.png(就地疊加 CJK)")
    ap.add_argument("--out-txf", required=True)
    ap.add_argument("--chars", default=DEFAULT_CHARS)
    ap.add_argument("--free-top", type=int, default=264,
                    help="atlas 可用空白列起始(top-down row)")
    args = ap.parse_args()

    font = ImageFont.truetype(args.font, int(FONT_SIZE * SS), index=args.index)
    atlas = Image.open(args.atlas).convert("RGBA")
    texW, texH = atlas.size
    apx = np.array(atlas)

    chars = []
    seen = set()
    for ch in args.chars:
        if ch not in seen:
            seen.add(ch)
            chars.append(ch)

    # 由左至右、自 free_top 起逐列擺放
    cur_x, cur_y, row_h = 1, args.free_top + 1, 0
    glyphs = []   # (code, adv, emRect, ax0, ay0, w, h)
    for ch in sorted(chars, key=ord):
        res = glyph_sdf(font, ch)
        if res is None:
            print(f"  跳過空白字 {ch!r}", file=sys.stderr)
            continue
        sd, em, adv = res
        h, w = sd.shape
        if cur_x + w + 1 > texW:
            cur_x = 1
            cur_y += row_h + 1
            row_h = 0
        if cur_y + h + 1 > texH:
            print(f"ERROR: atlas 空白不足放 {ch!r}（需到 row {cur_y+h}）",
                  file=sys.stderr)
            sys.exit(1)
        # 寫入 R=G=B=SDF,A=255
        v = (sd * 255).astype(np.uint8)
        cell = np.dstack([v, v, v, np.full_like(v, 255)])
        apx[cur_y:cur_y + h, cur_x:cur_x + w] = cell
        glyphs.append((ord(ch), adv, em, cur_x, cur_y, w, h))
        cur_x += w + 1
        row_h = max(row_h, h)

    glyphs.sort(key=lambda g: g[0])     # 依碼位升序

    # 輸出 atlas
    Image.fromarray(apx, "RGBA").save(args.atlas)
    print(f"atlas 疊加 {len(glyphs)} 字 → {args.atlas}（用到 row {cur_y+row_h}/{texH}）")

    # 輸出 .txf
    with open(args.out_txf, "wb") as f:
        # TxfHeader：texW,texH,glyphCount,kernOffset(H*4) + fontSize,pixelRange,
        #            lineHeight,ascender,descender(f*5)
        f.write(struct.pack("<HHHH", texW, texH, len(glyphs), 0))
        f.write(struct.pack("<fffff", FONT_SIZE, PIXEL_RANGE,
                            LINE_HEIGHT, ASCENDER, DESCENDER))
        for code, adv, em, ax0, ay0, w, h in glyphs:
            s0 = ax0 / texW
            s1 = (ax0 + w) / texW
            t0 = 1.0 - (ay0 + h) / texH      # 對齊既有:t0=1-bottom/texH
            t1 = 1.0 - ay0 / texH            # t1=1-top/texH
            f.write(struct.pack("<HHf4f4f", code, 0, adv,
                                em[0], em[1], em[2], em[3],
                                s0, t0, s1, t1))
    print(f"cfont-cjk.txf: {len(glyphs)} glyph → {args.out_txf}")
    for code, adv, em, *_ in glyphs:
        print(f"  U+{code:04X} {chr(code)} adv={adv:.2f} "
              f"em=({em[0]:.3f},{em[1]:.3f},{em[2]:.3f},{em[3]:.3f})")


if __name__ == "__main__":
    main()

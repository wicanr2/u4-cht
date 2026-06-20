#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMS ROM 圖形區掃描輔助:
  band <rom> <out> <start_kb> <end_kb>   把指定 KB 區間當 8×8 tile strip 放大(SC 倍)輸出,
                                          每 32 列(=1KB)左側標 offset。
找未壓縮 tile bank:看哪段呈現規律可辨識形狀(非帶狀雜訊)。
"""
import sys
from PIL import Image, ImageDraw

GRAY = [(i * 17, i * 17, i * 17) for i in range(16)]


def decode_tile(tb):
    px = [0] * 64
    for row in range(8):
        b = [tb[row * 4 + p] for p in range(4)]
        for x in range(8):
            v = 0
            for p in range(4):
                if (b[p] >> (7 - x)) & 1:
                    v |= (1 << p)
            px[row * 8 + x] = v
    return px


mode = sys.argv[1]
rom = open(sys.argv[2], "rb").read()
out = sys.argv[3]

if mode == "band":
    start = int(float(sys.argv[4]) * 1024)
    end = int(float(sys.argv[5]) * 1024)
    COLS = 32           # 32 tile/row = 1KB/row
    SC = 3
    LM = 70             # 左邊界放 offset 文字
    seg = rom[start:end]
    NT = len(seg) // 32
    ROWS = (NT + COLS - 1) // COLS
    img = Image.new("RGB", (LM + COLS * 8 * SC, ROWS * 8 * SC), (20, 0, 30))
    p = img.load()
    for t in range(NT):
        tb = seg[t * 32:t * 32 + 32]
        if len(tb) < 32:
            break
        px = decode_tile(tb)
        ox, oy = LM + (t % COLS) * 8 * SC, (t // COLS) * 8 * SC
        for i, v in enumerate(px):
            col = GRAY[v]
            for dy in range(SC):
                for dx in range(SC):
                    p[ox + (i % 8) * SC + dx, oy + (i // 8) * SC + dy] = col
    d = ImageDraw.Draw(img)
    for r in range(ROWS):
        off = start + r * COLS * 32
        d.text((2, r * 8 * SC), f"{off:05X}", fill=(255, 230, 80))
    img.save(out)
    print(f"band 0x{start:X}-0x{end:X}: {NT} tiles, {ROWS} rows -> {out}")

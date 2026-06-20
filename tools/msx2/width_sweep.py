#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""寬度掃描:把檔案當 4bpp(與 1bpp)線性影像,掃多種 byte/row 找出不剪切的正確 stride。
輸出每個候選一張圖,並算「row 間相關性」分數(越高代表縱向連貫=正確寬度)。
用法:python3 width_sweep.py <file> <outdir> <mode:4bpp|1bpp>
"""
import sys
from PIL import Image

data = open(sys.argv[1], "rb").read()
outdir = sys.argv[2].rstrip("/")
mode = sys.argv[3] if len(sys.argv) > 3 else "4bpp"
print(f"size={len(data)} mode={mode}")

PAL = [(0, 0, 0)] + [(33, 200, 66)] + [(c, c, c) for c in
       [80, 110, 140, 70, 170, 100, 200, 130, 230, 90, 180, 210, 240, 255]]


def row_bytes_to_pixels(buf, mode):
    if mode == "4bpp":
        px = []
        for b in buf:
            px.append((b >> 4) & 0xF)
            px.append(b & 0xF)
        return px
    else:  # 1bpp MSB-first
        px = []
        for b in buf:
            for k in range(7, -1, -1):
                px.append((b >> k) & 1)
        return px


# 候選 byte/row(stride)
cands = [16, 24, 28, 32, 40, 44, 48, 56, 64, 80, 96, 112, 128]
scores = []
for bpr in cands:
    rows = len(data) // bpr
    if rows < 8:
        continue
    px_per_row = bpr * (2 if mode == "4bpp" else 8)
    img = Image.new("RGB", (px_per_row, rows), (20, 20, 20))
    p = img.load()
    rowpx = []
    for r in range(rows):
        line = row_bytes_to_pixels(data[r * bpr:(r + 1) * bpr], mode)
        rowpx.append(line)
        for x, v in enumerate(line):
            p[x, r] = PAL[v] if mode == "4bpp" else ((255, 255, 255) if v else (0, 0, 0))
    # 縱向連貫分數:相鄰 row 同位置相等比例
    same = tot = 0
    for r in range(1, rows):
        for x in range(min(len(rowpx[r]), len(rowpx[r - 1]))):
            tot += 1
            if rowpx[r][x] == rowpx[r - 1][x]:
                same += 1
    sc = same / tot if tot else 0
    scores.append((sc, bpr, px_per_row, rows))
    sf = max(1, 512 // px_per_row)
    img.resize((px_per_row * sf, rows * sf), Image.NEAREST).save(
        f"{outdir}/w_{mode}_{px_per_row}.png")

scores.sort(reverse=True)
print("top widths by vertical-coherence (px wide / stride bytes / rows / score):")
for sc, bpr, w, rows in scores[:6]:
    print(f"  w={w:4d}  stride={bpr:3d}B  rows={rows:4d}  score={sc:.3f}")

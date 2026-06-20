#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""掃 SMS ROM 找 CRAM palette 候選 + 用候選 palette 彩現一段 tile。
SMS color byte = --BBGGRR(各 2-bit)。一個 palette = 16 byte(16 色)。
  cand <rom>                     列出疑似 palette 區(連續 32 byte 內含多種顏色且 index0 常為黑/邊界)
  render <rom> <out> <tileoff> <ntile> <paloff>  用 paloff 起 16 色 palette 彩現
"""
import sys
from PIL import Image


def sms_color(b):
    r = b & 3
    g = (b >> 2) & 3
    bl = (b >> 4) & 3
    sc = [0, 85, 170, 255]
    return (sc[r], sc[g], sc[bl])


def decode_tile(tb):
    px = [0] * 64
    for row in range(8):
        bb = [tb[row * 4 + p] for p in range(4)]
        for x in range(8):
            v = 0
            for p in range(4):
                if (bb[p] >> (7 - x)) & 1:
                    v |= (1 << p)
            px[row * 8 + x] = v
    return px


mode = sys.argv[1]
rom = open(sys.argv[2], "rb").read()

if mode == "cand":
    # 找連續 16/32 byte 區段:不同顏色數 >=6,且 byte 值都 < 0x40(SMS color 高 2 bit 為 0)
    hits = []
    for off in range(0, len(rom) - 32):
        seg = rom[off:off + 32]
        if all(b < 0x40 for b in seg):
            ncol = len(set(seg))
            if ncol >= 8:
                hits.append((off, ncol))
    # 去掉相鄰密集(只保留每 0x20 取代表)
    out = []
    last = -100
    for off, n in hits:
        if off - last >= 16:
            out.append((off, n))
            last = off
    for off, n in out[:120]:
        print(f"0x{off:06X}  ncol={n}  bytes={rom[off:off+16].hex()}")
    print(f"total cand regions: {len(out)}")

elif mode == "render":
    out = sys.argv[3]
    toff = int(sys.argv[4], 0)
    ntile = int(sys.argv[5])
    poff = int(sys.argv[6], 0)
    pal = [sms_color(rom[poff + i]) for i in range(16)]
    COLS = 16
    ROWS = (ntile + COLS - 1) // COLS
    SC = 5
    img = Image.new("RGB", (COLS * 8 * SC, ROWS * 8 * SC), (120, 0, 120))
    p = img.load()
    for t in range(ntile):
        tb = rom[toff + t * 32:toff + t * 32 + 32]
        if len(tb) < 32:
            break
        px = decode_tile(tb)
        ox, oy = (t % COLS) * 8 * SC, (t // COLS) * 8 * SC
        for i, v in enumerate(px):
            col = pal[v]
            for dy in range(SC):
                for dx in range(SC):
                    p[ox + (i % 8) * SC + dx, oy + (i // 8) * SC + dy] = col
    img.save(out)
    print(f"render tile@0x{toff:X} n={ntile} pal@0x{poff:X} -> {out}")

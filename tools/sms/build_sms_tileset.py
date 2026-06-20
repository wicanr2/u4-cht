#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMS Ultima IV 圖形確定性解碼器。

實況(逆向結論):
  - ROM = materals/_extracted/genesis/u4.sms(512KB,`TMR SEGA` header)。
  - tile = SMS VDP 8×8 4bpp planar(32B/tile,每 row 4 byte plane0..3 weight 1/2/4/8,MSB=左)。
  - 圖形主場在 0x40000–0x44000:**已組好的全螢幕場景畫面(packed tilemap)**,
    非 xu4 期望的「256 個 16×16 sprite bank」。SMS 走 VDP name-table + pattern bank,
    raw ROM 順序切不出 xu4 的 256-tile 邏輯序(缺 name-table 對映)。
  - 熵分析全 ROM <6.5,圖形未壓縮。
  - palette:ROM 內未找到能讓 idx2=草綠/idx4=水藍/idx14=磚白 同時成立的 16-byte table;
    用實測 index 直方圖反推的固定盤(SMS_PAL)彩現正確。

本工具做兩件「可確定性交付」的事:
  scene  <rom> <out.png>          dump 0x40000 起的場景圖(8×8 連續排列,1024 tile = 256×256px)
  bank   <rom> <out.png> <off> <ntile> <cols>  任意區段彩現(逆向探索用)
"""
import sys
from PIL import Image

# 由 0x40A00 地形區 index 直方圖反推的固定 16 色盤
# idx2=主草綠 idx14=磚牆白/灰 idx4=水藍 idx0=黑 idx6=深棕(柱)
SMS_PAL = [
    (0, 0, 0),        # 0 black (邊界/陰影)
    (85, 85, 85),     # 1
    (40, 180, 40),    # 2 草綠 (dominant)
    (120, 220, 120),  # 3 淺綠
    (60, 90, 230),    # 4 水藍
    (130, 150, 255),  # 5 淺藍
    (150, 75, 50),    # 6 棕 (柱/門框)
    (200, 120, 90),   # 7
    (90, 60, 40),     # 8
    (170, 110, 70),   # 9
    (200, 200, 100),  # 10 黃
    (230, 220, 150),  # 11
    (255, 120, 200),  # 12
    (150, 150, 150),  # 13 灰
    (220, 220, 220),  # 14 磚牆白 (2nd dominant)
    (255, 255, 255),  # 15 白
]


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


def render(rom, off, ntile, cols, pal, sc=1):
    rows = (ntile + cols - 1) // cols
    img = Image.new("RGB", (cols * 8 * sc, rows * 8 * sc), (120, 0, 120))
    p = img.load()
    for t in range(ntile):
        tb = rom[off + t * 32:off + t * 32 + 32]
        if len(tb) < 32:
            break
        px = decode_tile(tb)
        ox, oy = (t % cols) * 8 * sc, (t // cols) * 8 * sc
        for i, v in enumerate(px):
            col = pal[v]
            for dy in range(sc):
                for dx in range(sc):
                    p[ox + (i % 8) * sc + dx, oy + (i // 8) * sc + dy] = col
    return img


if __name__ == "__main__":
    mode = sys.argv[1]
    rom = open(sys.argv[2], "rb").read()
    out = sys.argv[3]
    if mode == "scene":
        # 0x40000 起 1024 tile(32KB)= 32 tile 寬(256px)場景
        img = render(rom, 0x40000, 1024, 32, SMS_PAL, sc=2)
        img.save(out)
        print(f"scene dump 0x40000 (1024 tiles, 32-wide) -> {out}")
    elif mode == "bank":
        off = int(sys.argv[4], 0)
        ntile = int(sys.argv[5])
        cols = int(sys.argv[6])
        img = render(rom, off, ntile, cols, SMS_PAL, sc=3)
        img.save(out)
        print(f"bank 0x{off:X} n={ntile} cols={cols} -> {out}")

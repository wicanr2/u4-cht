#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 lr_dump 產出的 .vram(64K)+ .cram(128B)解碼成彩色 tile sheet。

SMS Mode 4 規格:
  VRAM:pattern generator table = 8×8 4bpp planar tile,32B/tile,前 16KB(0x4000)
        可放 448 個 tile;name table 通常在 0x3800 起。
  CRAM:Genesis-Plus-GX 把每個 SMS 1-byte 色(--BBGGRR,6-bit)存成 uint16 低 byte。
        取每 2 byte 的第 0 byte = 真色;32 色 = palette0(0..15) + palette1(16..31)。
        SMS 色:bit RRGGBB 各 2-bit → 0/85/170/255 四階。

用法:
  dump_vram.py sheet <prefix> <out.png> [ntile]   解碼前 ntile 個 tile(預設 448)成彩色 sheet
  dump_vram.py pal <prefix>                        印出 32 色 palette
"""
import sys
from PIL import Image


def load_cram(prefix):
    """回傳 32 個 (r,g,b)。"""
    raw = open(prefix + ".cram", "rb").read()
    pal = []
    for i in range(32):
        c = raw[i * 2]                 # 取低 byte(uint16 little-endian 的第 0 byte)
        r = (c & 0x03)
        g = (c >> 2) & 0x03
        b = (c >> 4) & 0x03
        lvl = [0, 85, 170, 255]
        pal.append((lvl[r], lvl[g], lvl[b]))
    return pal


def decode_tile(tb):
    """32 byte → 64 個 4-bit index(row-major)。planar:每 row 4 byte,plane0..3。"""
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


def main():
    mode = sys.argv[1]
    prefix = sys.argv[2]
    pal = load_cram(prefix)

    if mode == "pal":
        for i, c in enumerate(pal):
            tag = " (pal0)" if i < 16 else " (pal1)"
            print(f"{i:2d}{tag}: rgb{c}")
        return

    if mode == "crop":
        # 從重建好的 scene 裁出指定矩形(tile 座標),放大輸出。用來取地形 tile 取樣。
        # 參數: crop <prefix> <out> <col0> <row0> <ncol> <nrow> [nt_base]
        out = sys.argv[3]
        c0, r0, nc, nr = (int(sys.argv[i]) for i in range(4, 8))
        nt_base = int(sys.argv[8], 0) if len(sys.argv) > 8 else 0x3800
        vram = open(prefix + ".vram", "rb").read()
        SC = 6
        img = Image.new("RGB", (nc * 8 * SC, nr * 8 * SC), (20, 20, 20))
        p = img.load()
        for ty in range(nr):
            for tx in range(nc):
                e = nt_base + ((r0 + ty) * 32 + (c0 + tx)) * 2
                lo, hi = vram[e], vram[e + 1]
                idx = lo | ((hi & 1) << 8)
                hflip, vflip = bool(hi & 0x02), bool(hi & 0x04)
                palsel = pal[16:32] if (hi & 0x08) else pal[0:16]
                tb = vram[idx * 32: idx * 32 + 32]
                if len(tb) < 32:
                    continue
                px = decode_tile(tb)
                for yy in range(8):
                    for xx in range(8):
                        sx = 7 - xx if hflip else xx
                        sy = 7 - yy if vflip else yy
                        col = palsel[px[sy * 8 + sx]]
                        for dy in range(SC):
                            for dx in range(SC):
                                p[(tx * 8 + xx) * SC + dx, (ty * 8 + yy) * SC + dy] = col
        img.save(out)
        print(f"crop ({c0},{r0}) {nc}x{nr} -> {out} ({img.size})")
        return

    if mode == "scene":
        # 用 name table 重建整張畫面(32×28 tile),驗證 tile bank + palette。
        # SMS Mode 4 name table 預設在 VRAM 0x3800,每格 2 byte:
        #   低 byte = pattern index 低 8 bit;高 byte bit0 = index bit8,
        #   bit3 = palette select(0=pal0 / 1=pal1),bit1=hflip bit2=vflip。
        out = sys.argv[3]
        nt_base = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x3800
        vram = open(prefix + ".vram", "rb").read()
        COLS, ROWS = 32, 28
        SC = 2
        img = Image.new("RGB", (COLS * 8 * SC, ROWS * 8 * SC))
        p = img.load()
        for ty in range(ROWS):
            for tx in range(COLS):
                e = nt_base + (ty * COLS + tx) * 2
                lo, hi = vram[e], vram[e + 1]
                idx = lo | ((hi & 1) << 8)
                hflip = bool(hi & 0x02)
                vflip = bool(hi & 0x04)
                palsel = pal[16:32] if (hi & 0x08) else pal[0:16]
                tb = vram[idx * 32: idx * 32 + 32]
                if len(tb) < 32:
                    continue
                px = decode_tile(tb)
                for yy in range(8):
                    for xx in range(8):
                        sx = 7 - xx if hflip else xx
                        sy = 7 - yy if vflip else yy
                        col = palsel[px[sy * 8 + sx]]
                        for dy in range(SC):
                            for dx in range(SC):
                                p[(tx * 8 + xx) * SC + dx, (ty * 8 + yy) * SC + dy] = col
        img.save(out)
        print(f"scene @nt 0x{nt_base:X} -> {out} ({img.size})")
        return

    if mode == "sheet":
        out = sys.argv[3]
        ntile = int(sys.argv[4]) if len(sys.argv) > 4 else 448
        vram = open(prefix + ".vram", "rb").read()
        COLS = 16
        ROWS = (ntile + COLS - 1) // COLS
        SC = 4
        img = Image.new("RGB", (COLS * 8 * SC, ROWS * 8 * SC), (40, 0, 40))
        p = img.load()
        # 兩種 palette 都試:預設用 pal1(背景常用 16..31)。可在 sheet 同時畫兩半。
        usepal = pal[16:32]
        for t in range(ntile):
            tb = vram[t * 32:t * 32 + 32]
            if len(tb) < 32:
                break
            px = decode_tile(tb)
            ox, oy = (t % COLS) * 8 * SC, (t // COLS) * 8 * SC
            for i, v in enumerate(px):
                col = usepal[v]
                for dy in range(SC):
                    for dx in range(SC):
                        p[ox + (i % 8) * SC + dx, oy + (i // 8) * SC + dy] = col
        img.save(out)
        print(f"sheet: {ntile} tiles -> {out} ({img.size})")


if __name__ == "__main__":
    main()

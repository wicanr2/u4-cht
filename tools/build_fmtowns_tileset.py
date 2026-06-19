#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 FM Towns 版 Ultima IV 的 ULTIMA4.TIL 解碼成 xu4 可用的 tileset PNG。

ULTIMA4.TIL = 256 tile × (16×16 px × 2 byte) = 131072 byte,16-bit 直色(RGB565,
little-endian),且本來就是 U4 標準 256-tile 順序 → 直接堆成 16 寬 × 4096 高的
tileset(xu4 `tiles: 256` 格式),當 FM Towns 美術主題。

ULTIMA4.TIL 取自使用者自有的 FM Towns 光碟(.chd → iso → U4OPEN/U4_J/ULTIMA4.TIL),
屬版權遊戲資料,不入 repo(引擎/資料分離)。

用法:
  python3 tools/build_fmtowns_tileset.py --til <ULTIMA4.TIL> --out fmt_tileset.png
"""
import argparse
import struct

from PIL import Image

TILE = 16
N_TILES = 256
BYTES_PER_TILE = TILE * TILE * 2   # 16-bit/px


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--til", required=True, help="FM Towns ULTIMA4.TIL")
    ap.add_argument("--out", required=True, help="輸出 tileset PNG(16×4096)")
    args = ap.parse_args()

    d = open(args.til, "rb").read()
    need = N_TILES * BYTES_PER_TILE
    if len(d) < need:
        raise SystemExit(f"ULTIMA4.TIL 太小:{len(d)} < {need}")

    img = Image.new("RGB", (TILE, TILE * N_TILES))
    px = img.load()
    for t in range(N_TILES):
        base = t * BYTES_PER_TILE
        for i in range(TILE * TILE):
            w = struct.unpack_from("<H", d, base + i * 2)[0]   # RGB565 LE
            r = (w >> 11) & 0x1F
            g = (w >> 5) & 0x3F
            b = w & 0x1F
            px[i % TILE, t * TILE + i // TILE] = (
                r * 255 // 31, g * 255 // 63, b * 255 // 31)
    img.save(args.out)
    print(f"FM Towns tileset:{N_TILES} tile → {args.out} ({img.size[0]}×{img.size[1]})")


if __name__ == "__main__":
    main()

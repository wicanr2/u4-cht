#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 MSX2 版 Ultima IV(Pony Canyon 1987)的 SHAPE.DAT 解成 tileset PNG。

格式(以 byte 自相關 + 視覺驗證反推):
  SHAPE.DAT = 24576 byte = 256 tile × 96 byte
  每 tile = 16 row × 6 byte;6 byte = 12 px × 4bpp chunky(高 nibble 先,左→右)
  → 即 12 寬 × 16 高、16 色(MSX2 SCREEN5)。

自相關證據:dominant lag=6(row stride)、lag=96(tile stride)、lag=192(=2×96)。
192-tile/128B(16×16 4bpp)與各 3bpp planar 解讀皆為噪訊,僅本解法產出可辨識
sprite/地形。殘餘待校正:① 調色盤為 SCREEN5 近似(遊戲可能載自訂 palette)
② 12 寬語意 vs xu4 的 16×16(整合時需置中/補邊或等比放寬)。建議用 openMSX
VRAM dump 做 ground-truth 校正後定稿。

SHAPE.DAT 取自使用者自有的 MSX2 磁碟(.dsk → mtools mcopy),屬版權遊戲資料,
不入 repo(引擎/資料分離)。

用法:
  python3 tools/build_msx2_tileset.py --shape <SHAPE.DAT> --out msx_tileset.png
                                      [--cols 16] [--scale 2]
"""
import argparse

from PIL import Image

TILE_W, TILE_H = 12, 16
BYTES_PER_TILE = TILE_H * 6          # 96
N_TILES = 256

# MSX2 SCREEN5(V9938)預設 16 色近似(sRGB)
MSX2_PAL = [
    (0, 0, 0), (0, 0, 0), (33, 200, 66), (94, 220, 120),
    (84, 85, 237), (125, 118, 252), (181, 82, 77), (102, 235, 250),
    (252, 85, 84), (255, 121, 120), (212, 193, 84), (230, 206, 128),
    (33, 176, 59), (201, 91, 186), (204, 204, 204), (255, 255, 255),
]


def decode_tile(tb):
    """96 byte → 12×16 index list(row-major)。"""
    px = []
    for b in tb:
        px.append((b >> 4) & 0xF)
        px.append(b & 0xF)
    return px  # 192 index = 16 row × 12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shape", required=True, help="MSX2 SHAPE.DAT")
    ap.add_argument("--out", required=True, help="輸出 tileset PNG")
    ap.add_argument("--cols", type=int, default=16, help="每列幾個 tile")
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    d = open(args.shape, "rb").read()
    need = N_TILES * BYTES_PER_TILE
    if len(d) < need:
        raise SystemExit(f"SHAPE.DAT 太小:{len(d)} < {need}")

    cols = args.cols
    rows = (N_TILES + cols - 1) // cols
    img = Image.new("RGB", (cols * TILE_W, rows * TILE_H))
    p = img.load()
    for t in range(N_TILES):
        px = decode_tile(d[t * BYTES_PER_TILE:(t + 1) * BYTES_PER_TILE])
        ox, oy = (t % cols) * TILE_W, (t // cols) * TILE_H
        for i, idx in enumerate(px):
            p[ox + (i % TILE_W), oy + (i // TILE_W)] = MSX2_PAL[idx & 0xF]
    if args.scale > 1:
        img = img.resize((img.size[0] * args.scale, img.size[1] * args.scale),
                         Image.NEAREST)
    img.save(args.out)
    print(f"MSX2 tileset:{N_TILES} tile(12×16)→ {args.out} ({img.size[0]}×{img.size[1]})")


if __name__ == "__main__":
    main()

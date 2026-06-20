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

# Ultima IV(MSX2 / Pony Canyon)實際載入的 16 色自訂 palette。
# 來源:disk_1.dsk offset 0x02de9f 的 32-byte VDP palette table
#  (每色 2 byte:byte0=0RRR0BBB、byte1=00000GGG,各 3-bit → 8-bit)。
# 驗證方法:套用後渲染 II1X.MSX 風景圖,天空/樹/草/河顏色全部正確
#  (藍天、綠樹綠草、藍河、棕幹),確認為遊戲真實 palette 而非 SCREEN5 近似。
MSX2_PAL = [
    (0, 0, 0), (0, 0, 0), (0, 0, 255), (255, 0, 0),
    (218, 145, 0), (0, 255, 0), (0, 255, 255), (255, 255, 109),
    (72, 109, 145), (255, 218, 218), (182, 182, 182), (0, 109, 36),
    (0, 36, 72), (72, 36, 36), (109, 109, 109), (255, 255, 255),
]


def _3to8(v):
    return (v * 255) // 7


def load_palette(pal_path, off):
    """從含 32-byte VDP palette table 的檔案讀 16 色(MSX2 SCREEN5 格式)。"""
    pd = open(pal_path, "rb").read()
    pal = []
    for i in range(16):
        b0, b1 = pd[off + 2 * i], pd[off + 2 * i + 1]
        r, b, g = (b0 >> 4) & 7, b0 & 7, b1 & 7
        pal.append((_3to8(r), _3to8(g), _3to8(b)))
    return pal


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
    ap.add_argument("--palette", help="含 VDP palette table 的檔案(預設用內建真 palette)")
    ap.add_argument("--palette-off", default="0x02de9f",
                    help="palette table 在 --palette 檔內的 offset(hex)")
    args = ap.parse_args()

    pal = MSX2_PAL
    if args.palette:
        pal = load_palette(args.palette, int(args.palette_off, 16))

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
            p[ox + (i % TILE_W), oy + (i // TILE_W)] = pal[idx & 0xF]
    if args.scale > 1:
        img = img.resize((img.size[0] * args.scale, img.size[1] * args.scale),
                         Image.NEAREST)
    img.save(args.out)
    print(f"MSX2 tileset:{N_TILES} tile(12×16)→ {args.out} ({img.size[0]}×{img.size[1]})")


if __name__ == "__main__":
    main()

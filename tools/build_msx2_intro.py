#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 MSX2 版 Ultima IV 的 intro / 結局 / rune 畫面(II*.MSX / RUNE*.MSX / ENDPIC.MSX)
解成 PNG。

格式(已驗證):4-byte header + row-major chunky 4bpp(高 nibble 先),MSX2 SCREEN5
16 色。畫面尺寸由檔案大小回推:(len-4)*2 = W*H,常見 256×152(II*.MSX,19460 byte)。

  II1X.MSX = 19460 = 4 + 256×152/2 → 256×152
  其餘檔案依大小自動算高(W 預設 256);可 --width 覆寫。

來源檔取自使用者自有 MSX2 磁碟,屬版權資料,不入 repo。

用法:
  python3 tools/build_msx2_intro.py --in II1X.MSX --out ii1x.png [--width 256] [--header 4]
"""
import argparse

from PIL import Image

MSX2_PAL = [
    (0, 0, 0), (0, 0, 0), (33, 200, 66), (94, 220, 120),
    (84, 85, 237), (125, 118, 252), (181, 82, 77), (102, 235, 250),
    (252, 85, 84), (255, 121, 120), (212, 193, 84), (230, 206, 128),
    (33, 176, 59), (201, 91, 186), (204, 204, 204), (255, 255, 255),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=256)
    ap.add_argument("--header", type=int, default=4)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    d = open(args.inp, "rb").read()
    body = d[args.header:]
    W = args.width
    bpr = W // 2                       # bytes per row at 4bpp
    H = len(body) // bpr
    img = Image.new("RGB", (W, H))
    p = img.load()
    i = 0
    for y in range(H):
        for x in range(0, W, 2):
            if i >= len(body):
                break
            b = body[i]
            i += 1
            p[x, y] = MSX2_PAL[(b >> 4) & 0xF]
            if x + 1 < W:
                p[x + 1, y] = MSX2_PAL[b & 0xF]
    if args.scale > 1:
        img = img.resize((W * args.scale, H * args.scale), Image.NEAREST)
    img.save(args.out)
    print(f"MSX2 intro:{W}×{H} → {args.out}")


if __name__ == "__main__":
    main()

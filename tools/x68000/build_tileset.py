#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""X68000 Ultima IV:SWSHAPE.PAT → xu4 tileset PNG(16×4096)。

SWSHAPE.PAT = 16×16 2bpp(4 色,64 byte/tile);tile 序 = canonical U4 = xu4 256 序。
palette 預設 init.x @0x140(RGB555)= 室外 4 色盤(綠/亮灰/黑/藍),水藍草綠正確。
完整多場景彩色(town/dungeon 棕等)需 per-scene 子盤(見 u4-multiplatform-theme SKILL)。

用法:python3 build_tileset.py <SWSHAPE.PAT> <init.x> <pal_off_hex> <out.png> [N=256]
資料屬版權,輸出留本機。
"""
import sys,struct
from PIL import Image
shp=open(sys.argv[1],"rb").read()
palf=open(sys.argv[2],"rb").read(); off=int(sys.argv[3],16)
out=sys.argv[4]; N=int(sys.argv[5]) if len(sys.argv)>5 else 256
def rgb(w):
    r=(w>>10)&0x1F;g=(w>>5)&0x1F;b=w&0x1F; return (r*255//31,g*255//31,b*255//31)
pal=[rgb(struct.unpack_from(">H",palf,off+i*2)[0]) for i in range(16)]
# 16 寬 sheet,N tile 直堆(xu4 tiles 格式)
img=Image.new("RGB",(16,16*N)); p=img.load()
for t in range(N):
    base=t*64
    for r in range(16):
        for byi in range(4):
            b=shp[base+r*4+byi] if base+r*4+byi<len(shp) else 0
            for k in range(4):
                x=byi*4+k; v=(b>>((3-k)*2))&3
                p[x,t*16+r]=pal[v]
img.save(out); print("->",out,N,"tiles")
# 另存放大預覽(頭 64 tile,8 欄)
prev=Image.new("RGB",(8*16*4,8*16*4),(40,0,40)); pp=prev.load()
for t in range(64):
    ox,oy=(t%8)*16*4,(t//8)*16*4
    for r in range(16):
        for byi in range(4):
            b=shp[t*64+r*4+byi] if t*64+r*4+byi<len(shp) else 0
            for k in range(4):
                x=byi*4+k;v=(b>>((3-k)*2))&3
                for dy in range(4):
                    for dx in range(4): pp[ox+x*4+dx,oy+r*4+dy]=pal[v]
prev.save(out.replace(".png","_prev.png")); print("preview ok")

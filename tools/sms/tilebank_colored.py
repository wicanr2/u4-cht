#!/usr/bin/env python3
"""用 name-table 的 per-tile palette 正確上色 SMS VRAM tile bank。
掃 name-table(@0x3800)記錄每個 VRAM tile index 被哪個 palette(bit11)使用,
逐 tile 用該 palette 渲染;未用到的 tile 預設 palette 0。"""
import sys
from PIL import Image
vram=open(sys.argv[1]+".vram","rb").read()
craw=open(sys.argv[1]+".cram","rb").read()
def cram(i):
    c=craw[i*2]; lvl=[0,85,170,255]
    return (lvl[c&3],lvl[(c>>2)&3],lvl[(c>>4)&3])
pal=[cram(i) for i in range(32)]
# 掃 name-table 記錄每 tile 的 palette
tpal={}
NT=0x3800
for k in range(32*28):
    e=vram[NT+k*2]|(vram[NT+k*2+1]<<8)
    idx=e&0x1FF; ps=(e>>11)&1
    tpal.setdefault(idx,ps)
def tile_px(idx):
    base=idx*32; px=[0]*64
    for r in range(8):
        b=[vram[base+r*4+p] if base+r*4+p<len(vram) else 0 for p in range(4)]
        for x in range(8):
            px[r*8+x]=sum(((b[p]>>(7-x))&1)<<p for p in range(4))
    return px
N=448; COLS=16; SC=3
img=Image.new("RGB",(COLS*8*SC,(N//COLS)*8*SC),(40,0,40)); p=img.load()
for t in range(N):
    ps=tpal.get(t,0)
    tp=tile_px(t)
    ox,oy=(t%COLS)*8*SC,(t//COLS)*8*SC
    for i,v in enumerate(tp):
        c=pal[ps*16+(v&0xF)]
        for dy in range(SC):
            for dx in range(SC): p[ox+(i%8)*SC+dx,oy+(i//8)*SC+dy]=c
img.save(sys.argv[2]); print("->",sys.argv[2],"used tiles:",len(tpal))

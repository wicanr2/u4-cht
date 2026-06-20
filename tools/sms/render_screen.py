#!/usr/bin/env python3
"""用 SMS VRAM(name-table @0x3800 + pattern @0)+ CRAM 渲染當下螢幕。
name-table:32×28 entry,各 2 byte LE,bits0-8=tile index,bit11=palette select。
用法:render_screen.py <prefix> <out.png>"""
import sys
from PIL import Image
vram=open(sys.argv[1]+".vram","rb").read()
craw=open(sys.argv[1]+".cram","rb").read()
def cram(i):
    c=craw[i*2]; lvl=[0,85,170,255]
    return (lvl[c&3],lvl[(c>>2)&3],lvl[(c>>4)&3])
pal=[cram(i) for i in range(32)]
def tile_px(idx):
    base=idx*32; px=[0]*64
    for r in range(8):
        b=[vram[base+r*4+p] if base+r*4+p<len(vram) else 0 for p in range(4)]
        for x in range(8):
            v=sum(((b[p]>>(7-x))&1)<<p for p in range(4)); px[r*8+x]=v
    return px
NT=0x3800
img=Image.new("RGB",(32*8,28*8),(0,0,0)); p=img.load()
for ty in range(28):
    for tx in range(32):
        e=vram[NT+(ty*32+tx)*2] | (vram[NT+(ty*32+tx)*2+1]<<8)
        idx=e&0x1FF; palsel=(e>>11)&1
        tp=tile_px(idx)
        for r in range(8):
            for x in range(8):
                img.load()[tx*8+x,ty*8+r]=pal[palsel*16+(tp[r*8+x]&0xF)]
img=img.resize((512,448),Image.NEAREST)
img.save(sys.argv[2]); print("->",sys.argv[2])

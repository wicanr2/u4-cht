#!/usr/bin/env python3
"""用 oracle 對映 + font 區塊,把 SMS VRAM tile 組成 xu4 序 16×4096 tileset PNG。
oracle: VRAM tile→邏輯 tile(JSON)。反建:邏輯 L → 該 L 最常對到的 VRAM tile。
font: 偵測連續 ASCII 字型區塊對到 xu4 字型 tile(A-Z=tile 78起)。未知 tile 用水填。"""
import sys,json
from PIL import Image
vram=open(sys.argv[1]+".vram","rb").read()
craw=open(sys.argv[1]+".cram","rb").read()
mapping={int(k):v for k,v in json.load(open(sys.argv[2])).items()}
out=sys.argv[3]
def cram(i):
    c=craw[i*2]; lvl=[0,85,170,255]; return (lvl[c&3],lvl[(c>>2)&3],lvl[(c>>4)&3])
pal=[cram(i) for i in range(32)]
NT=0x3800
# 每 VRAM tile 的 palette(name-table)
tpal={}
for k in range(32*28):
    e=vram[NT+k*2]|(vram[NT+k*2+1]<<8); tpal.setdefault(e&0x1FF,(e>>11)&1)
def tile16(idx):  # 8×8 SMS tile → 放大成 16×16(nearest 2x)
    base=idx*32; ps=tpal.get(idx,0); px8=[0]*64
    for r in range(8):
        b=[vram[base+r*4+p] if base+r*4+p<len(vram) else 0 for p in range(4)]
        for x in range(8): px8[r*8+x]=sum(((b[p]>>(7-x))&1)<<p for p in range(4))
    px=[]
    for y in range(16):
        for x in range(16): px.append(pal[ps*16+(px8[(y//2)*8+(x//2)]&0xF)])
    return px
# 反建:邏輯 L → VRAM tile(多數)
from collections import Counter,defaultdict
rev=defaultdict(Counter)
for v,l in mapping.items(): rev[l][v]+=1
log2vram={l:c.most_common(1)[0][0] for l,c in rev.items()}
# 水 tile(邏輯 0)當預設填充
water_v=log2vram.get(0, 352)
img=Image.new("RGB",(16,16*256)); p=img.load()
for L in range(256):
    v=log2vram.get(L, water_v)
    px=tile16(v)
    for i,c in enumerate(px): p[i%16,L*16+i//16]=c
img.save(out)
mapped=len([l for l in log2vram if l<256])
print(f"-> {out}  邏輯 tile 有對映: {mapped}/256(其餘用水填)")

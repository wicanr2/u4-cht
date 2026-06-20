#!/usr/bin/env python3
"""用 MAP.BIN(Britannia)當 oracle 導出 SMS VRAM tile → 邏輯 tile 對映。
1. SMS 世界畫面 name-table → 每格 VRAM tile index;依顏色分類 水/陸。
2. MAP.BIN(16×16 chunk)→ 水(0)/陸 binary。
3. 滑動匹配找 SMS 畫面在 Britannia 的位置。
4. 對齊後:每格 SMS VRAM tile ↔ MAP.BIN 邏輯 tile → 對映表。"""
import sys,struct
vram=open(sys.argv[1]+".vram","rb").read()
craw=open(sys.argv[1]+".cram","rb").read()
mapd=open(sys.argv[2],"rb").read()  # X68000 MAP.BIN
def cram(i):
    c=craw[i*2]; lvl=[0,85,170,255]; return (lvl[c&3],lvl[(c>>2)&3],lvl[(c>>4)&3])
pal=[cram(i) for i in range(32)]
NT=0x3800
def nt(tx,ty):
    e=vram[NT+(ty*32+tx)*2]|(vram[NT+(ty*32+tx)*2+1]<<8); return (e&0x1FF,(e>>11)&1)
def tile_dom(idx,ps):
    base=idx*32; cnt={}
    for r in range(8):
        b=[vram[base+r*4+p] if base+r*4+p<len(vram) else 0 for p in range(4)]
        for x in range(8):
            v=sum(((b[p]>>(7-x))&1)<<p for p in range(4)); c=pal[ps*16+v]; cnt[c]=cnt.get(c,0)+1
    return max(cnt,key=cnt.get)
def is_water(c): return c[2]>c[0]+30 and c[2]>c[1]+20  # 藍為主
# SMS 地圖區 22×18(避開 HUD),取每格 (vram,water?)
W,H=20,16
smap=[]; swater=[]
for ty in range(H):
    rowv=[]; roww=[]
    for tx in range(W):
        idx,ps=nt(tx,ty); rowv.append(idx); roww.append(1 if is_water(tile_dom(idx,ps)) else 0)
    smap.append(rowv); swater.append(roww)
# MAP.BIN 水/陸(16×16 chunk)
def mtile(X,Y):
    cx,cy=X//16,Y//16; return mapd[(cy*16+cx)*256+(Y%16)*16+(X%16)]
mwater=[[1 if mtile(x,y)<4 else 0 for x in range(256)] for y in range(256)]
# 滑動匹配
best=(-1,0,0)
for oy in range(256-H):
    for ox in range(256-W):
        s=sum(1 for y in range(H) for x in range(W) if swater[y][x]==mwater[oy+y][ox+x])
        if s>best[0]: best=(s,ox,oy)
score,ox,oy=best
print(f"最佳匹配 @({ox},{oy}) 吻合 {score}/{W*H} ({100*score//(W*H)}%)")
# 導出對映:VRAM tile → 邏輯 tile(取多數決)
from collections import Counter,defaultdict
m=defaultdict(Counter)
for y in range(H):
    for x in range(W):
        m[smap[y][x]][mtile(ox+x,oy+y)]+=1
mapping={v:c.most_common(1)[0][0] for v,c in m.items()}
print("VRAM→邏輯 tile 對映(部分):")
for v in sorted(mapping)[:20]: print(f"  VRAM {v} → 邏輯 {mapping[v]}")
import json
json.dump({str(k):v for k,v in mapping.items()}, open(sys.argv[3],"w"))
print(f"→ {sys.argv[3]} ({len(mapping)} 對映)")

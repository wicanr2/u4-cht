import sys,struct
from PIL import Image
mapd=open(sys.argv[1],"rb").read(); shp=open(sys.argv[2],"rb").read()
outdir=sys.argv[-1].rstrip("/")
def grb(w):
    g=(w>>11)&0x1F;r=(w>>6)&0x1F;b=(w>>1)&0x1F; return (r*255//31,g*255//31,b*255//31)
def rgb(w):
    r=(w>>10)&0x1F;g=(w>>5)&0x1F;b=w&0x1F; return (r*255//31,g*255//31,b*255//31)
def mtile(X,Y):
    cx,cy=X//16,Y//16;tx,ty=X%16,Y%16; return mapd[(cy*16+cx)*256+ty*16+tx]
# 取樣:水 tile(idx0)中心 + 草 tile(idx5)中心,看 4 色用哪些
def tile_colors(idx,pal):
    base=idx*64; cnt={}
    for r in range(16):
        for byi in range(4):
            b=shp[base+r*4+byi] if base+r*4+byi<len(shp) else 0
            for k in range(4):
                v=(b>>((3-k)*2))&3; cnt[v]=cnt.get(v,0)+1
    # 主色
    return pal[max(cnt,key=cnt.get)]
best=[]
for fn in sys.argv[3:-1]:
    d=open(fn,"rb").read()
    for off in range(0,len(d)-32,2):
        for dec,nm in [(grb,"GRB"),(rgb,"RGB")]:
            pal=[dec(struct.unpack_from(">H",d,off+i*2)[0]) for i in range(16)]
            water=tile_colors(0,pal)   # 水主色應藍
            grass=tile_colors(5,pal)   # 草主色應綠
            # 評分:水藍(b>r,b>g) + 草綠(g>r,g>b)
            s=0
            if water[2]>water[0]+30 and water[2]>water[1]+10: s+=2
            if grass[1]>grass[0]+20 and grass[1]>grass[2]+20: s+=2
            if sum(water)>40: s+=1
            if s>=4: best.append((s,fn.split("/")[-1],off,nm,water,grass))
best.sort(key=lambda x:-x[0])
seen=set();top=[]
for b in best:
    k=(b[1],b[2]//8,b[3])
    if k in seen:continue
    seen.add(k);top.append(b)
    if len(top)>=6:break
for s,fn,off,nm,w,g in top:
    print(f"{fn} @0x{off:x} {nm} score={s} water={w} grass={g}")
print("候選數:",len(top))

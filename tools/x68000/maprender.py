import sys,struct
from PIL import Image
mapd=open(sys.argv[1],"rb").read()
shp=open(sys.argv[2],"rb").read()
palfile=sys.argv[3]; paloff=int(sys.argv[4],16); paldec=sys.argv[5]; out=sys.argv[6]
N=64  # 渲染 64x64 tile 區(左上,含大陸)
def grb(w):
    g=(w>>11)&0x1F;r=(w>>6)&0x1F;b=(w>>1)&0x1F; return (r*255//31,g*255//31,b*255//31)
def rgb555(w):
    r=(w>>10)&0x1F;g=(w>>5)&0x1F;b=w&0x1F; return (r*255//31,g*255//31,b*255//31)
dec=grb if paldec=="GRB" else rgb555
pd=open(palfile,"rb").read()
pal16=[dec(struct.unpack_from(">H",pd,paloff+i*2)[0]) for i in range(16)]
def mtile(X,Y):  # 16x16 chunk
    cx,cy=X//16,Y//16; tx,ty=X%16,Y%16
    return mapd[(cy*16+cx)*256+ty*16+tx]
def tpx(idx):
    base=idx*64; px=[]
    for r in range(16):
        for byi in range(4):
            b=shp[base+r*4+byi] if base+r*4+byi<len(shp) else 0
            for k in range(4): px.append((b>>((3-k)*2))&3)
    return px
TS=8
img=Image.new("RGB",(N*TS,N*TS),(0,0,0)); p=img.load()
for ty in range(N):
    for tx in range(N):
        tp=tpx(mtile(tx,ty))
        for dy in range(TS):
            for dx in range(TS):
                sx=dx*16//TS; sy=dy*16//TS
                p[tx*TS+dx,ty*TS+dy]=pal16[tp[sy*16+sx]&3]
img.save(out); print("->",out.split("/")[-1])

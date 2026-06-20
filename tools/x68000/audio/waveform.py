import wave,struct,math,sys
from PIL import Image
def load(wav):
    w=wave.open(wav,"rb"); n=w.getnframes()
    return struct.unpack(f"<{n}h",w.readframes(n)),n
def draw(s,n,W=512,H=120):
    img=Image.new("RGB",(W,H),(20,20,30)); p=img.load()
    for x in range(W):
        i0=x*n//W; i1=max(i0+1,(x+1)*n//W); seg=s[i0:i1]
        if not seg: continue
        y0=int(H/2-max(seg)/32768*H/2); y1=int(H/2-min(seg)/32768*H/2)
        for y in range(max(0,y0),min(H,y1+1)): p[x,y]=(80,220,120)
    return img
files=sys.argv[1:-1]; out=sys.argv[-1]
comb=Image.new("RGB",(512,123*len(files)),(0,0,0))
for k,f in enumerate(files):
    s,n=load(f); comb.paste(draw(s,n),(0,k*123))
    rms=math.sqrt(sum(v*v for v in s)/max(1,len(s)))
    print(f"{f.split('/')[-1]}: {n} samp RMS={rms:.0f} peak={max(abs(min(s)),abs(max(s)))}")
comb.save(out); print("->",out)

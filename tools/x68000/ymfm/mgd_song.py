#!/usr/bin/env python3
"""MGD 多 track 合奏 → YM2151 register events(8 聲道同時)。
給一組 track index,各分配一個 channel;解各 track 為 (abs_tick, action) 事件,
依絕對時間合併,產生統一 register 流(wait=事件間 tick 差×TICK)。"""
import sys,struct
d=open(sys.argv[1],"rb").read()
tracks=[int(x) for x in sys.argv[2].split(",")]
out=sys.argv[3]
TICK=int(sys.argv[4]) if len(sys.argv)>4 else 850
ttab=struct.unpack_from(">H",d,4)[0]
toffs=[]
i=ttab
while i<len(d)-1:
    o=struct.unpack_from(">H",d,i)[0]
    if o==0 or o>=len(d):
        if toffs: break
        i+=2; continue
    toffs.append(o); i+=2
    if len(toffs)>20: break
KC=[0,1,2,4,5,6,8,9,10,12,13,14]
def note_kc(n): return ((n//12)<<4)|KC[n%12]
SLOT=[0,8,16,24]
def voice_regs(vn,ch):
    base=0x09+(vn-1)*0x2a
    if base+25>=len(d): return []
    p=d[base+1:base+25]; cf=d[base+25]
    pr=[p[k*4:k*4+4] for k in range(6)]
    ev=[(0x20+ch,0xC0|(cf&0x3f))]
    for op in range(4):
        s=ch+SLOT[op]
        ev+=[(0x40+s,pr[0][op]&0x7f),(0x60+s,pr[1][op]&0x7f),(0x80+s,pr[2][op]&0x1f),
             (0xA0+s,pr[3][op]&0x9f),(0xC0+s,pr[4][op]&0x9f),(0xE0+s,pr[5][op])]
    return ev
# 收集所有 track 的事件 (abs_tick, [register writes])
sched=[]  # (tick, (addr,data))
for ci,ti in enumerate(tracks):
    ch=ci%8; o=toffs[ti]; end=toffs[ti+1] if ti+1<len(toffs) else len(d)
    seg=d[o:end]; t=0; i=0
    for a,v in voice_regs(1,ch): sched.append((0,(a,v)))
    while i<len(seg):
        b=seg[i]
        if b==0xff: break
        if b&0x80:
            cmd=b; param=seg[i+1] if i+1<len(seg) else 0; i+=2
            if cmd==0x92:
                for a,v in voice_regs(param or 1,ch): sched.append((t,(a,v)))
        else:
            note=seg[i]; dur=seg[i+1] if i+1<len(seg) else 8; i+=2
            sched.append((t,(0x28+ch,note_kc(note))))
            sched.append((t,(0x08,0x78|ch)))         # KON ch
            sched.append((t+dur,(0x08,0x00|ch)))      # KOFF ch at t+dur
            t+=dur
sched.sort(key=lambda x:x[0])
# 產 register 流:事件間 wait = tick 差 × TICK
fo=open(out,"w"); last=0
for tick,(a,v) in sched:
    w=(tick-last)*TICK; last=tick
    fo.write(f"{a:02x} {v:02x} {w}\n")
fo.close()
print(f"{len(tracks)} tracks → {len(sched)} 事件, 結束 tick={last} (~{last*TICK//62500}s)")

#!/usr/bin/env python3
"""X68000 ult.smp/ult.efc 樣本庫 → 各樣本 raw ADPCM。
格式:header = N×8 byte 的 (offset BE32, length BE32) 表(N=offset0/8),之後為
OKI MSM6258 ADPCM(4-bit)樣本資料。輸出各樣本 .adpcm + 一份 manifest。"""
import sys,struct,os
d=open(sys.argv[1],"rb").read(); outdir=sys.argv[2]
os.makedirs(outdir,exist_ok=True)
first_off=struct.unpack_from(">I",d,0)[0]
n=first_off//8
print(f"size={len(d)} first_off={first_off} → {n} 樣本")
ok=0
for i in range(n):
    off=struct.unpack_from(">I",d,i*8)[0]
    ln=struct.unpack_from(">I",d,i*8+4)[0]
    if off+ln>len(d) or ln==0 or ln>len(d): 
        print(f"  #{i} off={off:#x} ln={ln:#x} 越界,跳"); continue
    open(f"{outdir}/s{i:02d}.adpcm","wb").write(d[off:off+ln])
    ok+=1
print(f"抽出 {ok} 樣本到 {outdir}")

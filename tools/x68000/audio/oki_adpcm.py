#!/usr/bin/env python3
"""OKI MSM6258(Dialogic/VOX)4-bit ADPCM → 16-bit PCM WAV。X68000 PCM 用此晶片。
用法:oki_adpcm.py <in.adpcm> <out.wav> [sample_rate=15625] [hi_first=1]"""
import sys,struct,wave
STEP=[16,17,19,21,23,25,28,31,34,37,41,45,50,55,60,66,73,80,88,97,107,118,130,
143,157,173,190,209,230,253,279,307,337,371,408,449,494,544,598,658,724,796,
876,963,1060,1166,1282,1411,1552]
IDX=[-1,-1,-1,-1,2,4,6,8,-1,-1,-1,-1,2,4,6,8]
def decode(data,hi_first=True):
    out=bytearray(); pred=0; idx=0
    for b in data:
        nibs=[(b>>4)&0xF,b&0xF] if hi_first else [b&0xF,(b>>4)&0xF]
        for nib in nibs:
            step=STEP[idx]
            delta=step>>3
            if nib&1: delta+=step>>2
            if nib&2: delta+=step>>1
            if nib&4: delta+=step
            if nib&8: delta=-delta
            pred=max(-2048,min(2047,pred+delta))
            idx=max(0,min(48,idx+IDX[nib]))
            out+=struct.pack("<h",pred<<4)
    return bytes(out)
d=open(sys.argv[1],"rb").read()
sr=int(sys.argv[3]) if len(sys.argv)>3 else 15625
hi=(sys.argv[4] if len(sys.argv)>4 else "1")=="1"
pcm=decode(d,hi)
w=wave.open(sys.argv[2],"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
w.writeframes(pcm); w.close()
print(f"{sys.argv[1]} ({len(d)}B ADPCM) → {sys.argv[2]} ({len(pcm)//2} samples @ {sr}Hz)")

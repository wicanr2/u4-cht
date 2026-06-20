#!/usr/bin/env python3
"""Amiga 8-bit signed PCM → WAV。用法:s8_to_wav.py <in> <out.wav> [rate] [skip]"""
import sys,struct,wave
d=open(sys.argv[1],"rb").read()
rate=int(sys.argv[3]) if len(sys.argv)>3 else 10000
skip=int(sys.argv[4]) if len(sys.argv)>4 else 0
data=d[skip:]
pcm=b"".join(struct.pack("<h",struct.unpack("b",bytes([b]))[0]*256) for b in data)
w=wave.open(sys.argv[2],"wb");w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
w.writeframes(pcm);w.close()
print(f"{sys.argv[1].split('/')[-1]} → {len(data)} samp @{rate}Hz skip={skip}")

#!/usr/bin/env python3
"""FM Towns .SND → WAV。格式:0x20 header(名稱8B + 參數;@0x0c=資料長度)+ unsigned 8-bit PCM。
取樣率:header @0x08 值多為 0x1ef6(7926)→ 實測波形對則用之;預設 8000。
用法:snd2wav.py <in.SND> <out.wav> [rate=8000]"""
import sys,struct,wave
d=open(sys.argv[1],"rb").read()
dlen=struct.unpack_from("<I",d,0x0c)[0]
data=d[0x20:0x20+dlen] if dlen and 0x20+dlen<=len(d) else d[0x20:]
rate=int(sys.argv[3]) if len(sys.argv)>3 else 8000
# u8(0x80 中心)→ s16
pcm=b"".join(struct.pack("<h",(b-128)*256) for b in data)
w=wave.open(sys.argv[2],"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
w.writeframes(pcm); w.close()
print(f"{sys.argv[1].split('/')[-1]} dlen={dlen} → {len(data)} samp @ {rate}Hz")

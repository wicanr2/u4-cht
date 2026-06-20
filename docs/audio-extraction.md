# 各平台音效抽取手記 —— 用「看波形」確認你沒在解碼雜訊

> 把 Ultima IV 各移植版的音效從原始檔挖出來、轉成現代 WAV 的過程筆記。
> 重點不只是「怎麼轉」,而是 **headless 環境下沒喇叭、怎麼知道自己解對了**。

把老遊戲的聲音資料挖出來,最大的難處不是寫解碼器 —— 4-bit ADPCM、8-bit PCM 的演算法都不長 ——
而是**你聽不到**。在沒有音效卡的 docker 容器裡跑,轉出來的 WAV 到底是真的音效、還是參數猜錯
得到的一段白噪音?盯著一堆 16-bit 數字看不出所以然。

答案是:**把波形畫成圖,用眼睛驗收**。真實的音效有「起音—衰減」的包絡、有靜音的頭尾、有
規律的節奏;解錯的雜訊則是均勻、無結構的滿版。一張 512×120 的波形圖,一眼就分得出來。

下面那張圖,是 FM Towns 版四個音效的波形 —— 不用聽就知道全對:

```
ATTACK1  ┤▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌      ▁▁▁   ← 快速振盪(揮砍的嗡嗡聲)
MAHOU1   ┤████████████████▁▁▁▁▁▁▁▁▁▁▁▁     ← 長包絡(施法的持續音,~8 秒)
HORSE    ┤▌  ▌▌            ▌▌            ← 規律爆發(馬蹄聲,數得出蹄拍!)
BEEP     ┤▙▟▙▟▙▟▙▟▙▟▙▟▙▟▙▟▙▟▙▟▙▟▙▟▙▟   ← 方波(嗶聲)
```

`HORSE.SND` 那條規律的爆發,數得出是馬在跑的蹄拍;`BEEP` 是教科書般的方波。
這些都不是巧合能湊出來的形狀 —— 看到它們,就知道取樣率、PCM 格式、資料起點全都對了。

---

## 三個平台,三種 PCM,一套驗收法

| 平台 | 聲音晶片 / 格式 | 檔案 | 解法 |
|---|---|---|---|
| **X68000** | OKI MSM6258 **4-bit ADPCM**(Dialogic/VOX) | `ult.smp`(樂器樣本)、`ult.efc`(音效) | 自寫 OKI ADPCM 解碼器(~30 行) |
| **FM Towns** | RF5C68 **unsigned 8-bit PCM** | `*.SND`(具名音效:ATTACK/MAHOU/DOKU/HORSE…) | skip 0x20 header,u8→s16 |
| **Amiga** | Paula **signed 8-bit PCM** | `snds.bin`(音效庫) | skip 4-byte header,s8→s16 |

三家的 PCM 格式都不同(4-bit ADPCM / unsigned 8-bit / signed 8-bit),但驗收方法一樣:
**畫波形、看結構**。

### X68000:(offset, length) 樣本表 + OKI ADPCM

`ult.smp` / `ult.efc` 開頭是一張 **(offset, length) 表**(各為 BE32),表長 = 第一個 offset
(`0xd0` = 208 byte = 26 entry,實際用到前 6 / 13 個,其餘補 0)。每筆指向一段 OKI MSM6258
的 4-bit ADPCM。

驗證表結構的小訣竅:**offset[i] + length[i] 應該等於 offset[i+1]**。`0xd0 + 0x1771 = 0x1841`
正好是下一筆 offset —— 表的解讀一次確認。

OKI ADPCM 不是 ffmpeg 的內建輸入格式(`adpcm_ima_oki` 只是 codec、沒有 raw demuxer),
所以直接自寫:49 階 step table + 16 項 index 調整表,每個 nibble 累加 delta、clamp 到 12-bit,
輸出左移成 16-bit。工具:`tools/x68000/audio/oki_adpcm.py`。

### FM Towns:具名音效 + 8-bit unsigned PCM

`.SND` 檔頭很佛心 —— 開頭 8 byte 直接是音效名稱(`Attack1\0`、`BEEP\0`),
`@0x0c` 是資料長度(= 檔案大小 − 0x20),資料從 `0x20` 起是 unsigned 8-bit PCM
(以 `0x80` 為中心,看到 `8180 8181 8181` 就知道是 u8)。轉換:`(byte − 128) × 256` 成 s16。
工具:`tools/fmtowns/snd2wav.py`。

### Amiga:signed 8-bit PCM 音效庫

`snds.bin` 是多個音效串接的 Paula signed 8-bit PCM(看到 `0xef`(−17)、`0xfc`(−4) 這種
繞 0 的小正負值就是 s8)。波形圖看得出約 8–9 段、各有獨立包絡、段間有靜音。
工具:`tools/amiga/audio/s8_to_wav.py`。

---

## 能挖到哪、挖不到哪(誠實邊界)

- ✅ **音效 / 取樣(samples)**:三平台都能直接抽成 WAV。FM Towns 連名字都有(攻擊、魔法、
  中毒、馬、火、月相…),X68000 / Amiga 是音效庫,可整批轉或依靜音切段。
- ⛔ **背景音樂(songs)**:X68000 `ult.mgd`(MML 曲譜)、Amiga `mus*.bin`(序列)都是
  **給各自音源驅動跑的指令序列**,不是取樣 —— 要還原成音檔得**模擬該平台的聲音驅動**
  (X68000 的 "YODEL & BIG-X" 自訂驅動、Amiga 的播放器),屬模擬器領域,本手記未涵蓋。
- FM Towns 的**背景音樂**走另一條路:它是 CD 紅皮書音軌(CD-DA),直接 `chdman` + `bchunk`
  + `ffmpeg` 抽成 ogg,不需驅動模擬(見 `tools/extract_fmtowns.sh`)。

---

## 工具

| 平台 | 工具 |
|---|---|
| X68000 | `tools/x68000/extract_smp.py`(拆樣本表)、`tools/x68000/audio/oki_adpcm.py`(OKI ADPCM 解碼) |
| FM Towns | `tools/fmtowns/snd2wav.py` |
| Amiga | `tools/amiga/audio/s8_to_wav.py` |
| 共用 | `tools/x68000/audio/waveform.py`(**波形驗收圖**,headless 無喇叭時的眼睛) |

> 抽出的音訊屬各家版權資產,**不入 repo**(引擎/資料分離);這裡只放解碼工具與方法。
> 全程走 docker `u4cht/extract`(含 Pillow / ffmpeg),不污染系統。

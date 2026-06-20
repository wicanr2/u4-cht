# X68000 版 Ultima IV 音樂格式逆向手記(`ult.mgd` + YM2151)

> 在沒有規格、驅動是自訂("YODEL & BIG-X")的情況下,從零逆出 X68000 版 Ultima IV 的
> 背景音樂格式,並透過 YM2151 模擬器把它**實際發出聲音**。

這是三條音訊路裡最深的一條。X68000 的背景音樂不是取樣回放,而是 **FM 合成**:`ult.mgd`
是一份「曲譜」,描述「哪個聲部、什麼時候、用哪個音色、彈哪個音、彈多久」,交給 YM2151
(OPM)FM 晶片即時算出聲音。要把它變成 WAV,得做兩件事:**(1) 逆出 MGD 格式**、
**(2) 用 YM2151 模擬器照著彈**。晶片那一側的規格見 [YM2151 知識庫](ym2151-knowledge-base.md)。

## 渲染管線(已打通)

```
ult.mgd ──解析──► voice 定義(FM patch)+ track 事件(音符/時值/控制)
                          │
                          ▼
               YM2151 register 寫入序列(addr, data, wait)
                          │
                          ▼
              ymfm(Aaron Giles 的 YM2151 模擬器)──► WAV
```

工具:
- `tools/x68000/ymfm/render.cpp` —— register event → WAV 的 C++ harness(連 ymfm)。
- `tools/x68000/ymfm/build.sh` —— docker 內 clone ymfm(BSD,不入 repo)+ 編譯。
- `tools/x68000/ymfm/mgd_voice.py` —— 抽單一 voice(音色)渲染音階,驗證音色提取。
- `tools/x68000/ymfm/mgd_track.py` —— 解單 track 旋律。
- `tools/x68000/ymfm/mgd_song.py` —— 多 track 合奏(分配 8 channel + 絕對時間合併)。

## 逆出來的 MGD 結構

### 檔頭

開頭幾個 big-endian 16-bit 值是全域參數。關鍵是 **`header[2]` = track pointer 表的 offset**
(`0x011a`)—— 順著它就能找到所有聲部的入口。

### voice 定義(FM 音色 patch)

緊接檔頭是一連串 **voice 定義**,每個 **42 byte(0x2a)stride**,從 `0x09` 起。一個 voice 就是
一組 YM2151 FM 參數,結構是「**operator-major**」—— 每個參數欄位連續放 4 個 operator 的值:

```
index | DT/MUL[4] | TL[4] | AR[4] | D1R[4] | D2R[4] | D1L-RR[4] | CON/FB | slot
```

例如 voice 1:`TL=[30,28,25,0]`(階梯狀,最後一個 operator 當載波最大聲)、`AR=[31,31,31,31]`
(全部最快起音)、`CON/FB=0xfb`。把這些值寫進 YM2151 對應暫存器(`0x40+`/`0x60+`/`0x80+`…),
就還原了那個音色。**驗證**:用 voice 1 彈一段音階,波形是 5 個各有起音衰減的音 —— 音色提取正確。

### track pointer 表 + track 事件

`header[2]`(`0x11a`)指向一張 BE16 的 **track offset 表**:`0x142, 0x214, 0x3ca, 0x426 …`
每個 offset 指向一條 track 的事件流。

每條 track 是一串事件,規律是:
- **`8x param`(高位有設)= 控制命令**:其中 **`0x92 nn` = 選 voice nn**(換音色);其餘
  (音量、pan、tempo、LFO…)尚未全解。
- **`note dur`(note < 0x80)= 發音**:note 是半音值(`0x20`–`0x3f`),dur 是時值(tick)。
- **`0xff` = track 結束。**

把音符值換成 YM2151 的 **KC(key code)**要注意:KC 不是連續半音,每個 octave 只有 12 個
有效值、跳過 `note & 3 == 3`(值 3/7/11/15)。換算:`KC = (octave << 4) | kc_table[semitone]`,
`kc_table = [0,1,2,4,5,6,8,9,10,12,13,14]`。

**驗證**:解 track 1 得 266 個音符,套 voice、逐音設 KC + KON(key on)+ 等 dur + KOFF,
渲染出 **135 秒的旋律**,波形是連貫的逐音符序列 —— 全鏈路(MGD → register → ymfm → WAV)打通。

## 解到哪、還沒解到哪(誠實邊界)

- ✅ **檔案結構**:檔頭、voice 定義(42B stride、operator-major)、track 表、track 事件 —— 確定。
- ✅ **voice → 音色**:FM patch 寫進 YM2151 暫存器,音色正確發聲。
- ✅ **單 track 旋律**:音符 + 時值 + voice 切換解出,渲染成完整長度旋律。
- 🟡 **多 track 合奏**:整首歌有多條 track(旋律 + 和聲 + 低音 + 鼓),要分配到 YM2151 的
  8 個 channel **同時**演奏並依時間軸對齊 —— 目前只渲染單 track,合併尚未做。
- 🟡 **tempo / 時值單位**:`dur × TICK` 的 TICK 目前是近似值;真正的速度藏在控制命令裡,待解。
- 🟡 **控制命令**:音量、pan、detune、LFO、ADPCM 鼓點(走 MSM6258)等 `8x` 命令多數略過。
- ⛔ **完全保真**:要和原機一模一樣,需把所有控制命令 + 多 track + ADPCM 鼓全解。目前是
  **「FM 旋律可發聲」的里程碑**,不是保真全曲。

## 方法論

1. **header 裡找 offset**:`header[2]` 指向 track 表 —— 序列格式的檔頭常是「指向各區段的 offset」。
2. **固定 stride 的索引區塊 = 資源定義**:42 byte 一個、開頭遞增 index → 是 voice/instrument 表。
3. **operator-major vs register 順序**:FM patch 常把 4 個 operator 的同一參數放一起(operator-major),
   寫暫存器時要拆開分配到各 slot;留意 driver 的 operator 排序(M1/C1/M2/C2)與暫存器 slot
   (M1/M2/C1/C2)可能不同。
4. **byte 值域分類事件**:高位 set = 控制命令、低值 = 音符;音符後面跟時值。先把音符+時值抽出來,
   控制命令逐個試。
5. **先單 track 發聲、後多 track 保真**:先證明「一條旋律能透過模擬器發聲」,多 track / tempo /
   效果留待逐步補。

> ymfm 是外部 BSD library,`build.sh` 於 docker clone 編譯,**不入 repo**;抽出的音樂屬版權,
> 同樣不入 repo。這裡只放解碼/渲染工具與方法。相關:[YM2151 知識庫](ym2151-knowledge-base.md)、
> [各平台音效抽取手記](audio-extraction.md)、[Amiga 音樂格式手記](amiga-music-format.md)。

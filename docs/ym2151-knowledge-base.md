# YM2151 (OPM) FM 音源晶片知識庫

> 用途底盤:X68000 版 Ultima IV 的背景音樂為 `ult.mgd`(MML 曲譜),走自訂驅動 "YODEL & BIG-X",底層是 **YM2151 (OPM) FM 合成 + MSM6258 ADPCM**。
> 本文件整理 YM2151 的暫存器地圖、FM 合成模型與「序列如何驅動晶片」,供後續 Python 工具:RE MGD 格式 → 產生 **YM2151 暫存器寫入序列** → 餵 **ymfm**(Aaron Giles 的 C++ 模擬 library)渲染成 WAV。

---

## 認識 YM2151:那個年代的「電子樂器晶片」

YM2151 是日本 Yamaha 在 1980 年代初推出的 FM 合成音源晶片,代號 **OPM**(FM Operator Type-M)。它不是播放預錄聲音的裝置,而是一顆「會自己發出樂音的晶片」——軟體只要把一組參數寫進它的暫存器,它就能即時算出小號、貝斯、鐘琴、鼓點等各種音色。一顆晶片同時能發 8 個聲部,每個聲部用 4 個振盪器(operator)疊出複雜的音色,因此一首曲子的全部樂器都能靠這一顆晶片演奏出來。

它定義了一整個世代的遊戲與電腦音樂。大型電玩街機基板(Capcom 的快打旋風系列、Sega 的多款基板)、日本的 **SHARP X68000** 個人電腦,以及部分合成器與音樂硬體,都是用 YM2151 發聲。許多 1980 年代末到 1990 年代初玩家記憶中的遊戲配樂,音色根源就是這顆晶片。本知識庫要處理的 X68000 版 Ultima IV,背景音樂正是走 YM2151。

它聽起來「很有那個年代的味道」,關鍵在於 **FM 合成(頻率調變合成)和取樣(PCM)是兩種完全不同的發聲原理**。取樣(PCM,也就是現在 MP3、遊戲音效檔的做法)是把真實樂器錄下來再回放,音色擬真但需要大量記憶體存放波形。FM 合成則相反:它不存任何錄音,而是讓一個振盪器(調變子)去扭曲另一個振盪器(載波)的頻率,用純數學運算「算」出聲音。好處是幾乎不佔記憶體、即時可變、音色金屬感與顆粒感強烈;代價是音色不像真實樂器,而是帶有一種獨特的合成質感——明亮、清脆、略帶數位味。正是這種「不完全像真樂器、卻自成一格」的音色,成了那個年代電子遊戲音樂的招牌聲響。

理解了「FM 合成靠參數即時算聲音、不靠錄音回放」這一點,後面的暫存器表與合成模型就有了脈絡:我們要做的,就是把 X68000 曲譜還原成「該寫哪些參數、什麼時候寫」,再交給模擬器照樣算出聲音。

---

## 0. TL;DR(對「Python 產 register 序列 → ymfm 渲染」最關鍵的點)

1. **整套播放 = 一串 `(addr, data)` 暫存器寫入,加上時間推進**。設定一個音色 = 對 4 個 operator 各寫一組參數(DT1/MUL、TL、KS/AR、AMS/D1R、DT2/D2R、D1L/RR)+ 對 channel 寫 RL/FB/CON;發聲 = 寫 `0x08` KON。所以 Python 工具的輸出就是「帶 timestamp 的 register write list」。
2. **ymfm 介面極窄**:`ym2151.write(addr, data)` 寫暫存器,`ym2151.generate(&output, n)` 取樣,輸出是 stereo `output.data[0]/[1]`(32-bit)。只要把 register 序列照時間餵進去、中間用 `generate()` 推進取樣數即可。
3. **operator 在暫存器內的 slot offset 是頭號雷**:同一 channel 的 4 個 operator 散在 `base + ch + (0/8/16/24)`,順序是 **M1=+0, M2=+8, C1=+16, C2=+24**;但多數 driver/voice 格式(含 MDX/OPM)把 operator 資料排成 **M1, C1, M2, C2** 的順序——抄資料時要重新映射,否則調變關係全錯。
4. **KC(key code)不是連續半音**:每個 octave 只有 12 個有效值,`note & 0x03 == 0x03`(值 3,7,11,15)是未定義的,要跳過。note → KC 要查表,不能直接線性換算。
5. **時脈關係**:X68000 的 YM2151 主時脈是 **4 MHz**(街機常見 3.579545 MHz)。`sample_rate = ym2151.sample_rate(clock)`(ymfm 內部 ÷64);輸出取樣率由此決定,渲染 WAV 時用這個 sample rate 當 header,或在外層 resample 到 44100。

---

## 1. 晶片概觀

- **YM2151 (OPM = FM Operator Type-M)**:Yamaha 的 8 channel × 4 operator FM 合成晶片。
- 每個 channel:4 個 operator(運算子)、8 種 **algorithm**(連接方式)、operator 自我 **feedback**、可選 LFO(低頻振盪器)做 AM/PM。
- 立體聲輸出(每 channel 可獨立 enable 左/右)。
- 內建 noise generator(雜訊產生器,只作用於 CH8 的 C2)、兩組 timer(Timer A/B,給 CSM 與驅動同步用)。
- 常見於 **X68000**、街機基板(Capcom CPS-1、Sega System 16…)。X68000 的 OPM 與 MSM6258 ADPCM 並存,前者負責 FM 樂音、後者負責取樣音(打擊/人聲)。

---

## 2. 暫存器地圖

YM2151 用「先寫 address(`write_address`),再寫 data(`write_data`)」的兩步介面。下表 addr 以十六進位表示。bit 7 為最高位。

### 2.1 全域暫存器(每晶片一份)

| Addr | 名稱 | bit 欄位 | 說明 |
|---|---|---|---|
| `0x01` | TEST / LFORESET | bit1 = LFO reset | 測試用;bit1 置 1 會 reset LFO 相位。初始化常寫 `0x00`。 |
| `0x08` | **KON**(Key On/Off) | `[-, SN3, SN2, SN1, SN0, CH2, CH1, CH0]` | `SN0..SN3` = 4 個 operator slot 的發聲遮罩(對應 M1/C1/M2/C2,bit3..bit6);`CH0..CH2` = channel(0–7)。發聲寫 `(slotmask<<3)\|ch`,停聲寫 `0x00\|ch`。 |
| `0x0F` | NE / NFRQ(noise) | bit7 = NE(noise enable),bit0..4 = NFRQ | noise 只送到 CH8 的 C2;FM 樂音通常不開。 |
| `0x10` | CLKA1(Timer A 高 8 bit) | — | Timer A 週期高位。 |
| `0x11` | CLKA2(Timer A 低 2 bit) | bit0..1 | Timer A 週期低位。 |
| `0x12` | CLKB(Timer B 8 bit) | — | Timer B 週期。 |
| `0x14` | 控制 / CSM / timer flag | bit0=LOADA, bit1=LOADB, bit2=…, bit6=IRQEN-A, bit7=CSM | 啟動/重置 timer、CSM 模式。MML 驅動常用 timer 當 tempo tick。 |
| `0x18` | **LFRQ**(LFO 頻率) | 8-bit | LFO 速度,約 0.0008 Hz – 52.9 Hz,值越大越快。 |
| `0x19` | PMD / AMD | bit7=1 寫 PMD(相位調變深度),bit7=0 寫 AMD(振幅調變深度),bit0..6 = 深度值 | 同一暫存器靠 bit7 區分寫 PMD 或 AMD。 |
| `0x1B` | CT / W(LFO 波形) | bit0..1 = LFO 波形(0=鋸齒,1=方波,2=三角,3=noise);bit6..7 = CT(GPO pin) | 設定 LFO 波形。 |

### 2.2 Per-channel 暫存器(channel ch = 0..7,addr = base + ch)

| Addr | 名稱 | bit 欄位 | 說明 |
|---|---|---|---|
| `0x20`–`0x27` | **RL / FB / CON** | `[RL_R, RL_L, FB2, FB1, FB0, CON2, CON1, CON0]` | bit7=右聲道 enable、bit6=左聲道 enable、bit3..5=feedback(M1 自我回授 0–7)、bit0..2=algorithm(0–7)。**未開 RL 任一位 = 該 channel 無輸出**(常見靜音雷)。 |
| `0x28`–`0x2F` | **KC**(key code,音高) | `[-, OCT2, OCT1, OCT0, NOTE3, NOTE2, NOTE1, NOTE0]` | bit4..6 = octave(0–7),bit0..3 = note。見 §4 note 表。 |
| `0x30`–`0x37` | **KF**(key fraction,微調) | bit2..7 = KF(6-bit) | 細微音高,每階約 1.6 cents;bit0..1 不用。 |

### 2.3 Per-operator 暫存器(32 個 slot)

operator slot 的 addr = `base + ch + slot_offset`,其中 `ch = 0..7`,`slot_offset ∈ {0, 8, 16, 24}`(見 §3.2 的 M1/M2/C1/C2 對映)。例如 `0x40` base 的 CH0 4 個 operator 在 `0x40, 0x48, 0x50, 0x58`。

| Addr base | 名稱 | bit 欄位 | 說明 |
|---|---|---|---|
| `0x40`–`0x5F` | **DT1 / MUL** | `[-, DT1_2, DT1_1, DT1_0, MUL3, MUL2, MUL1, MUL0]` | DT1=細微 detune(0–7);MUL=頻率倍率(0 → ×0.5,1–15 → ×1..×15)。 |
| `0x60`–`0x7F` | **TL**(total level) | bit0..6 = TL(7-bit) | 衰減量;0=最大音量、127=最小。dB ≈ 0.75 × TL。**只有 carrier 的 TL 影響音量,modulator 的 TL 影響調變深度(音色)**。 |
| `0x80`–`0x9F` | **KS / AR** | `[KS1, KS0, -, AR4, AR3, AR2, AR1, AR0]` | KS=key scaling(音高相關的包絡加速,0–3);AR=attack rate(0–31,越大越快)。 |
| `0xA0`–`0xBF` | **AMS-EN / D1R** | `[AMSEN, -, D1R4, D1R3, D1R2, D1R1, D1R0]` | bit7=AMS enable(此 op 是否吃 LFO 振幅調變);D1R=first decay rate(0–31)。 |
| `0xC0`–`0xDF` | **DT2 / D2R** | `[DT2_1, DT2_0, -, D2R4, D2R3, D2R2, D2R1, D2R0]` | DT2=粗 detune(約 0 / +600 / +781 / +950 cents,做金屬/鐘聲音色關鍵);D2R=second decay rate(0–31)。 |
| `0xE0`–`0xFF` | **D1L / RR** | `[D1L3, D1L2, D1L1, D1L0, RR3, RR2, RR1, RR0]` | D1L=first decay 的 sustain level(0–15,dB ≈ −3 × D1L);RR=release rate(0–15)。 |

---

## 3. FM 合成模型

### 3.1 operator 與包絡

每個 operator(運算子)是一個正弦振盪器 + ADSR 風格包絡。輸出可當「載波(carrier)」直接發聲,或當「調變子(modulator)」去調變下一個 operator 的相位。

包絡參數(對映上表):
- **AR**(attack rate):起音速度。
- **D1R**(first decay rate)→ 衰減到 **D1L**(first decay level / sustain level)。
- **D2R**(second decay rate):sustain 階段持續衰減。
- **RR**(release rate):放開鍵(KOFF)後的釋音速度。
- **TL**(total level):整體衰減 / 音量(或對 modulator 而言是調變深度)。
- **KS**(key scaling):高音時包絡自動加速。

音色設計口訣:**carrier 的 TL 控音量;modulator 的 TL 控音色亮度;DT2 與 MUL 控泛音與和諧/不和諧**。

### 3.2 operator slot 對映(最容易出錯)

晶片內部把 32 個 operator register 依 `ch + offset` 編址,offset 與「M1/M2/C1/C2」的對應是:

```
slot_offset  晶片內 operator   常見命名
   +0            OP1            M1 (modulator 1)
   +8            OP3            M2 (modulator 2)
   +16           OP2            C1 (carrier 1)
   +24           OP4            C2 (carrier 2)
```

即 channel ch 的四個 operator 暫存器在 `base + ch`、`base + ch + 8`、`base + ch + 16`、`base + ch + 24`。

⚠️ **driver / voice 檔(MDX、.OPM/VOPM preset)裡的 operator 資料順序通常是 `M1, C1, M2, C2`**,與晶片 offset 順序 `M1(+0), M2(+8), C1(+16), C2(+24)` 不同。RE MGD 抄音色時,要把資料的第 2、3 個 operator 對調再寫進對應 offset,否則 algorithm 的調變鏈會接錯。

### 3.3 algorithm(8 種連接)

`0x20-0x27` 的 CON(bit0..2)選 0–7。`M1` 帶 feedback(`0x20` 的 FB)。`→` 表示「調變」,`⊕` 表示並聯相加,最終 `OUT` 是各 carrier 輸出總和:

| CON | 連接 | 性質 |
|---|---|---|
| 0 | `M1→C1→M2→C2→OUT` | 全串接 4-op(M1 自回授)。音色最複雜、泛音最多。 |
| 1 | `[M1⊕C1]→M2→C2→OUT` | M1、C1 並聯調變 M2。 |
| 2 | `M1→[C1⊕M2]→C2→OUT` | C1、M2 並聯調變 C2。 |
| 3 | `[M1→C1]⊕M2→C2→OUT` | M1 調 C1,C1 與 M2 並聯調 C2。 |
| 4 | `[M1→C1]⊕[M2→C2]→OUT` | 兩組串接對並聯。常用於雙音色疊加。 |
| 5 | `M1→[C1⊕M2⊕C2]→OUT` | M1 同時調三個 carrier。 |
| 6 | `[M1→C1]⊕M2⊕C2→OUT` | 一組串接 + 兩個純正弦 carrier。 |
| 7 | `[M1⊕C1⊕M2⊕C2]→OUT` | 四個 operator 全並聯(加法合成,接近風琴/正弦疊加)。 |

實作渲染時不需手刻 algorithm —— ymfm 內部已照 CON 接好,只要把 CON/FB 寫進 `0x20-0x27` 即可。algorithm 圖在「哪些 operator 是 carrier(需要設音量 TL)」時有用:CON 越大,carrier 越多。

### 3.4 feedback

`0x20-0x27` 的 FB(bit3..5,0–7)是 **M1 的自我回授量**:M1 把自己的輸出回授到自己的相位輸入,值越大泛音越多(0=無,7=最強,接近鋸齒)。只有 M1 有 feedback。

---

## 4. 音高:KC + KF

音高由 **KC(key code,`0x28-0x2F`)** 的 octave + note,加上 **KF(key fraction,`0x30-0x37`)** 的微調決定。

### 4.1 KC 結構

```
KC = (OCT << 4) | NOTE      (OCT: 0–7, NOTE: 4-bit)
```

### 4.2 note 值對映(注意非連續)

每個 octave 內,note 4-bit 只有 12 個有效值,**`NOTE & 0x03 == 0x03`(值 3, 7, 11, 15)未定義,要跳過**:

| 音 | NOTE 值 | 音 | NOTE 值 |
|---|---|---|---|
| C# | `0x0` | G | `0x8` |
| D | `0x1` | G# | `0x9` |
| D# | `0x2` | A | `0xA` |
| (跳 `0x3`) | — | (跳 `0xB`) | — |
| E | `0x4` | A# | `0xC` |
| F | `0x5` | B | `0xD` |
| F# | `0x6` | C | `0xE` |
| (跳 `0x7`) | — | (跳 `0xF`) | — |

基準:`ΦM = 3.579545 MHz` 時,OCT=4 / A(`0xA`)= 440 Hz。例:中央 C 在 CH0 → `0x28` 寫 `(4<<4)\|0xE = 0x4E`。

注意 note 表「C# 起算、C 在最後(`0xE`)」的循環方式:同一八度從 C# 排到下一個 C。MML 的 note number(0–11 線性)轉 KC 時用查表(linear 0..11 → 上表的有效值),不要直接位移。

### 4.3 KF 微調

KF(`0x30-0x37` 的 bit2..7,6-bit)做半音內的細部音高,每階約 1.6 cents,用於滑音(portamento)、顫音(detune chorus)或非平均律微調。

---

## 5. 播放驅動方式(序列 → 暫存器寫入時序)

### 5.1 概念:一切都是 timed register writes

MML / MGD 曲譜經驅動解譯後,本質上是一串「在某個時間點,對某 channel 做某事」的事件,展開成晶片動作:

1. **載入音色(set voice)**:對目標 channel 的 4 個 operator 各寫 6 個暫存器(DT1/MUL、TL、KS/AR、AMS/D1R、DT2/D2R、D1L/RR),再寫 channel 的 RL/FB/CON(`0x20+ch`)。
2. **設定音高**:寫 KC(`0x28+ch`)與 KF(`0x30+ch`)。
3. **發聲(Key On)**:寫 `0x08`,值 = `(slotmask<<3) | ch`,slotmask 一般 `0x0F`(四個 operator 全發聲)。
4. **持續 N tick**:推進時間(見 §5.3),期間不動暫存器(或做 LFO/音量包絡的即時改寫)。
5. **停聲(Key Off)**:寫 `0x08`,值 = `0x00 | ch`(slotmask=0),operator 進入 release。

### 5.2 實際寫法範例(Arduino_YM2151 player)

低階 `write(addr, data)`:先讀 status(addr `0x00`)bit1 等 busy flag 清除,再 strobe address、strobe data,每步約 300 ns wait。模擬器(ymfm)不需要管 busy/timing,直接 `write()` 即可。

載入音色 `loadTimbre()`(每 channel 4 operator,`offset` 走 §3.2 的 slot offset):
```
write(0x40+offset, DT1_MUL);
write(0x60+offset, TL);
write(0x80+offset, KS_AR);
write(0xA0+offset, AMS_D1R);
write(0xC0+offset, DT2_D2R);
write(0xE0+offset, D1L_RR);
```
設音高 `setTone()`:
```
write(0x30+ch, KF);          // key fraction
write(0x28+ch, KeyCode);     // 查 KeyCodeTable
```
發聲 / 停聲:
```
// Key On:  slotmask 通常 0x0F
write(0x08, (slotmask << 3) | ch);
// Key Off:
write(0x08, ch);
```
panning / 音量(沿用 channel 的 FL/CON):
```
write(0x20+ch, (pan << 6) | FB_CON);   // pan: bit7=R, bit6=L
```

初始化:硬體版拉 IC(reset)pin low→high;模擬器版呼叫 `reset()`。之後常寫 `0x01=0x00`(清 LFO reset)、設 LFO 暫存器。

### 5.3 timing 怎麼推進

- 硬體 player 用 **Timer A/B**(`0x10-0x14`)產生固定 tick(IRQ),每 tick 跑一次 MML 解譯,推進音符時值。
- **渲染成 WAV 時不需要真的用 timer**:把曲譜的「tick → 秒數」算出來(tempo / tick rate),換成「每個事件之間要 `generate()` 多少 sample」。流程是:

```
for each event (sorted by time):
    samples_to_advance = round((event.time - cur_time) * sample_rate)
    chip.generate(out_buffer, samples_to_advance)   # 推進並收集音訊
    for (addr, data) in event.register_writes:
        chip.write(addr & 1 ? data... )              # 見 §6 介面
    cur_time = event.time
```

關鍵:**register write 是瞬時的,sample 推進才是耗時間的那一步**。Python 工具只要產出「排序好的事件 + 每事件的 register write list + 事件時間」,渲染端就能照上面迴圈跑。

---

## 6. 用 ymfm 渲染的介面

ymfm(Aaron Giles,C++)是我們實際 link 的模擬 library;`ymfm_opm.h` 提供 `ymfm::ym2151`。

### 6.1 對外方法(`ymfm::ym2151`)

```cpp
class ym2151 {
public:
    static constexpr uint32_t OUTPUTS = 2;          // stereo
    ym2151(ymfm_interface &intf);                   // 建構需傳一個 interface

    void reset();
    void write_address(uint8_t data);               // 兩步寫:先 address
    void write_data(uint8_t data);                  // 再 data
    void write(uint32_t offset, uint8_t data);      // offset bit0=0→address, =1→data
    uint8_t read_status();

    uint32_t sample_rate(uint32_t input_clock) const;  // 由主時脈算輸出取樣率

    void generate(output_data *output, uint32_t numsamples = 1);
};
```

- **寫暫存器有兩種等價方式**:
  - `write_address(addr); write_data(data);`
  - `write(0, addr); write(1, data);`(`write` 用 offset bit0 區分 address/data)
- **`generate(&out, n)`** 產生 n 個 stereo sample;讀 `out.data[0]`(左)、`out.data[1]`(右),型別是 32-bit 整數(內部 sample,需自行 clip/scale 成 16-bit PCM 寫 WAV)。

### 6.2 必須實作的 callback(`ymfm_interface` 子類別)

ymfm 透過 `ymfm_interface` 回呼宿主。最小實作只需 override 會用到的:

```cpp
class my_interface : public ymfm::ymfm_interface {
public:
    // FM 樂音渲染通常只需處理「外部讀取」(ADPCM/PCM ROM),YM2151 FM 不依賴它
    virtual uint8_t ymfm_external_read(ymfm::access_class type, uint32_t offset) override {
        return 0;   // 純 FM 不需要;若混 ADPCM 才回 PCM data
    }
    // 其餘 callback(ymfm_set_timer / ymfm_update_irq / ymfm_sync_mode_write 等)
    // 用基底類別預設即可,離線渲染不需要 timer/IRQ。
};
```

離線渲染(我們的場景)**不需要** timer/IRQ 回呼——因為時間推進由外層「算好 sample 數再 `generate()`」掌控(§5.3),不靠晶片內部 timer。

### 6.3 主時脈與取樣率

- YM2151 內部分頻 **÷64**:`output_sample_rate = clock / 64`。
- **X68000 的 OPM 主時脈 = 4 MHz** → 輸出取樣率 = 4_000_000 / 64 = **62500 Hz**。
- 街機常見 **3.579545 MHz** → 約 55930 Hz。
- 用法:
  ```cpp
  uint32_t clock = 4000000;               // X68000
  uint32_t srate = chip.sample_rate(clock);  // = clock/64
  ```
- 渲染 WAV:可直接用 `srate` 當 WAV header 的取樣率,或在外層 resample 到 44100/48000(線性內插即可,FM 音訊頻寬有限)。

### 6.4 ADPCM(MSM6258)另路混音

- X68000 的取樣音走 **MSM6258 ADPCM**,**不是 YM2151 的一部分**。
- ymfm 沒有 MSM6258;若 MGD 用到 ADPCM 軌,需另做 MSM6258 OKI-ADPCM 解碼(4-bit nibble → 16-bit PCM,標準 OKI step table),解出 PCM 後與 ymfm 的 FM 輸出**在外層按時間軸混音相加**(注意取樣率不同,需先 resample 對齊)。
- 第一版可先只渲染 YM2151 FM 軌,ADPCM 軌列為後續工作。

---

## 7. 參考連結

**模擬 library / player 原始碼**
- ymfm(Aaron Giles,我們會 link 的 library):https://github.com/aaronsgiles/ymfm
  - `ymfm_opm.h`(`ymfm::ym2151` 介面):https://github.com/aaronsgiles/ymfm/blob/main/src/ymfm_opm.h
  - vgmrender 範例(`ymfm_interface` 子類化、generate 迴圈、output 讀取):https://github.com/aaronsgiles/ymfm/blob/main/examples/vgmrender/vgmrender.cpp
- Arduino_YM2151(MAME 移植到 Arduino 的 MDX player,init/write/loadTimbre 寫法):https://github.com/ooISHoo/Arduino_YM2151/blob/develop/SketchMDXPlayer/YM2151.cpp
- YMulator-Synth(ymfm-based YM2151 VST/AU,voice/operator 參數映射):https://github.com/hiroaki0923/YMulator-Synth

**暫存器 / algorithm 文件**
- YM2151 (OPM) 使用教學(register map、algorithm、note 表;本文 §2/§3/§4 主要來源):https://oykenkyu.blogspot.com/2022/05/ym2151.html
- Yamaha YM2151 OPM 官方 application manual(PDF):http://map.grauw.nl/resources/sound/yamaha_ym2151_synthesis.pdf
- Yamaha YM2151 datasheet(bitsavers):https://bitsavers.org/components/yamaha/YM2151_199112.pdf
- MAME `ym2151.txt`(slot offset / 內部結構說明):https://github.com/mamedev/mame/blob/master/src/devices/sound/ym2151.txt
- XEiJ YM2151.java(X68000 模擬器的 OPM 實作):https://github.com/wyatt8740/xeij/blob/master/YM2151.java
- 4-op FM algorithm 圖解:https://gist.github.com/bryc/e997954473940ad97a825da4e7a496fa

**MDX / 驅動格式**(RE MGD 時對照)
- MDX File Format(vgmrips wiki):https://vgmrips.net/wiki/MDX_File_Format
- mdxtools `ym2151.c`(slot 映射範例):https://github.com/vampirefrog/mdxtools/blob/master/ym2151.c

---

## 附:來源讀取狀態

| 來源 | 狀態 |
|---|---|
| ymfm `ymfm_opm.h` | 成功(取得 `ym2151` 完整對外介面) |
| ymfm `vgmrender.cpp` | 成功(取得 interface 子類化、generate 迴圈、output 讀取) |
| Arduino_YM2151 `YM2151.cpp` | 成功(init/write/loadTimbre/KON/setTone 寫法) |
| YMulator-Synth | 部分(README 層級;細節需讀 `src/`,已取得 operator 命名與 ymfm 用法概念) |
| oykenkyu OPM 教學 | 成功(register map、8 algorithm、note 表的主要來源) |
| grauw 官方 manual PDF | 未取得(WebFetch 拿到 binary PDF stream,無法抽文字;已存 1.3MB 檔備查,內容以 oykenkyu / MAME 交叉佐證) |
| stdkmd XEiJ YM2151.java | 未取得(原 URL 404;改用 oykenkyu + MAME 補,並保留 wyatt8740 鏡像連結) |
| slot offset 映射 | 成功(MAME / mdxtools 搜尋結果確認 M1=+0/M2=+8/C1=+16/C2=+24,driver 資料序為 M1/C1/M2/C2) |
</content>
</invoke>

---
name: u4-multiplatform-theme
description: 把同一款經典遊戲(此處 Ultima IV)各家移植版的 tileset / intro / 音樂抽出來,做成「遊戲中按 F2 循環切換主題」的多主題系統(xu4 引擎)。涵蓋逐平台的磁碟/光碟/ROM 抽取格式、tile 解碼、音樂抽取、xu4 extension 模組 + 主題循環引擎、reproducibility 與 headless 雷。觸發:「抽某平台的 tileset/intro/音樂」「F2 切主題」「多版本美術主題」「FM Towns/X68000/MSX/Apple II/SMS/Amiga U4 資產」。
---

# Ultima IV 多平台美術/音樂主題 — 抽取與整合 SOP

目標:同一份 U4 地圖/邏輯,玩家按 `F2` 在各移植版的**畫風 + 音樂**間循環切換
(EGA → VGA → FM Towns → MSX2 → …)。每個平台 = 一個 xu4 extension 模組,覆寫
`tiles`(+ 可選 `music`),不動地圖/邏輯。**引擎/資料分離**:抽出的版權資產留本機
(materals/_extracted),repo 只放「解碼工具 + 模組定義 + 條件式 apply」。

## 引擎多主題管線(已通,FM Towns 為證)

1. **extension 模組**:`module/U4-<Theme>/`,`config.b` 宣告 `rules: "Ultima-IV/1.4"`
   (繼承父模組),`graphics.b` **只覆寫 `tiles` 影像**(+ `tile_guard`),其餘繼承。
   - graphics.b 的 `tiles` 影像 subimage 名/座標複製自 U4-Upgrade(同 256-tile 順序)。
   - tileset 放 `image/<theme>_tileset.png`(filename 相對 `module/<mod>/image/`,**勿加 `image/` 前綴**,否則 packer 找 `image/image/...`)。
   - PNG tileset 用 `tiles: 256`(免 width/height/depth/filetype=u4raw)。
2. **F2 主題循環**(`gameToggleGraphics`,game.cpp):改成主題清單陣列
   `{mod,label}[]` + `static Config* cache[]` + `cur` 索引,`configInit(themes[nxt].mod,...)`
   取(快取);**缺模組回 NULL → 跳下一主題**(故公開 repo 無該模組時優雅只循環 EGA↔VGA)。
3. **音樂綁主題**:切 config 後 `musicStop()`(重置 `currentTrack`,否則相同 track ID
   不重載)+ `musicPlayLocale()`(`config_musicFile` 從**新 config** 取檔)。
   各主題用自己 config 的 `music:` 區段;**無自訂音樂的主題沿用父模組 DOS 音樂**。
   music ID:world=1 town=2 shrine=3 merchant=4 rule=5 fanfare=6 dungeon=7 combat=8 castle=9。
4. **Makefile**:`MODULES += U4-<Theme>.mod` + pack 規則
   `U4-<Theme>.mod: module/U4-<Theme>/*.b module/U4-<Theme>/image/*.png`。
   **條件式**:`apply_cht.sh` 偵測到 `image/<theme>_tileset.png` 才加(否則不破乾淨 build)。

## 抽取工具容器(`docker/Dockerfile.extract`)

`ubuntu:24.04` + `mame-tools`(chdman)、`bchunk`、`ffmpeg`、`p7zip-full`、`mtools`、
`dosfstools`、`python3-pil`/`numpy`、`default-jre-headless` + AppleCommander(`ac`)。
逐平台用對應工具(見下)。

## 逐平台抽取(格式 / 工具 / 狀態)

### FM Towns(1990,日)— ✅ 完成
- 媒體:`.chd`(MAME 壓縮光碟)。`chdman extractcd -i x.chd -o cue -ob bin` → CD 軌。
- **tileset**:`bchunk` 切資料軌 → `7z x trk01.iso` → `U4OPEN/U4_J/ULTIMA4.TIL`
  = **256 tile × 16×16 × 2 byte(RGB565 little-endian)**,本來就 xu4 順序 → 直接堆
  16 寬 × 4096 高 PNG(`tools/build_fmtowns_tileset.py`)。
- **音樂**:CD-DA 2 軌 → `bchunk` wav → `ffmpeg` ogg(fmt_main/fmt_town)。
- **intro**:`U4OPEN/*.TIF` 是**標準 TIFF**(`4949 2a00`)→ `ffmpeg` 直接轉 PNG(32 張)。
- 整合:`tools/extract_fmtowns.sh`(端到端)+ `tools/fmtowns/module/{config.b,graphics.b}`。

### MSX2(1987,Pony Canyon)— 🟢 tile 解碼破解(到可辨識,待調色盤校正)
> 詳細單平台 SOP + 方法論見 `skills/u4-msx2-extract/`。
- 媒體:`.dsk`(MSX-DOS **FAT12**,`mtools` 可讀:`mdir -i x.dsk ::`,需 `MTOOLS_SKIP_CHECK=1`)。
- 檔案:`SHAPE.DAT`(24576)=tileset、`FONT.DAT`(8064)、`CARD1-3.MSX`(吉普賽卡)、
  `II*.MSX`/`RUNE*.MSX`/`ENDPIC.MSX`(intro/結局)、`U4MAP.BIN`/`TALKDATA.BIN` 等。
- **像素格式**:全螢幕圖 = row-major chunky 4bpp(高 nibble 先)+ SCREEN5 16 色。
  `II1X.MSX`(19460 = 4B header + 256×152×4bpp)解出清楚風景 ✅(`build_msx2_intro.py`)。
- **`SHAPE.DAT` tileset 已破解**(`build_msx2_tileset.py`):**byte 自相關**鎖定
  dominant `lag=6`(row)/`lag=96`(tile)/`lag=192` → `256 tile × 96B`、`16 row × 6B`、
  `6B = 12px × 4bpp chunky`(**非** 192-tile/128B,**非** 3bpp planar)→ 解出可辨識
  sprite + dither 地形、無剪切。**殘餘**:調色盤為 SCREEN5 近似(偏 dither)、12 寬
  對齊 xu4 16×16。**校正法**:openMSX headless 跑到地圖畫面 dump VRAM 取 ground-truth。
- **教訓**:先用全螢幕圖定像素格式,再用 byte 自相關量 tile/row stride(別盲猜維度);
  uniform-tile 正確+細節噪訊 = 格式對、tile 內序錯;無對角剪切 = stride 正確。

### X68000 — 🟢 recon 完成(意外最可做!FS+圖形已打通、音樂檔案層可抽)
- 媒體:`Ultima IV [FD].zip` = 4 個 `.hdm`(2HD,1232 sec × 1024B);`[extras].zip` 只有 3 PDF 手冊。
- **Human68k FS = 標準 FAT12**(boot sector 是 Hudson soft 自訂、無 BPB → mtools 報 "non DOS
  media";**自寫 reader 即解**:FAT@sec1-2、root@sec5-6、data@sec11=cluster2)。**64 檔全抽出**
  (Britannia 32 + Program 32)→ `materals/_extracted/x68000/files{,_prog}/`。**不需模擬器/專屬工具**。
- **tileset = `SWSHAPE.PAT` 16×16 2bpp(4 色),無壓縮**:byte 自相關 lag=4 = 4 byte/row;
  16 寬 → **2bpp**(非 4bpp,agent 初判錯);`62464/64 = 976 tiles`;`decode_shape.py --mode
  twobpp` 解出**乾淨可辨識 sprite**(人形/劍/箭,無倍增——chunky4 的「8px 成對」是把 2 真實
  row 擠 1 row 的假象)。Program disk 另有 `shape.pat`(212KB,autocorr lag=18 結構不同,疑
  portrait/大圖)、`FONT.PAT`、`MOON.PAT`、`intro1-7.img`/`title.img`。`MAP.BIN` 已驗證
  = 256×256 世界地圖(水=0 佔 34009)。
- **✅ 地圖 + palette 已破解(map oracle 法)**:
  - `MAP.BIN`(65536)= **16×16 個 chunk,每 chunk 16×16 tile**(chunk row-major、chunk 內
    row-major)→ de-chunk 後**完整還原 Britannia 世界地圖**(大陸/中央湖/群島/山脈)。
    tile 索引語意 = canonical U4(0=水、4-7=草林、8+=山)→ **SWSHAPE 序 = xu4 256 序**(免對映)。
  - **palette**:`init.x @0x140`(RGB555 `xRRRRRGGGGGBBBBB`)= 室外 4 色盤
    `綠(90,197,0)/亮灰(156,172,205)/黑/藍(16,49,131)`。用 MAP oracle 自動評分(水區藍+陸區綠)
    找到;`maprender.py` 渲染地圖對照參考圖一致確認。
  - `build_tileset.py` 用此 palette 把 SWSHAPE → xu4 16×4096 PNG,**解出可辨識 U4 tile**
    (水藍、樹、生物)。
  - **殘餘**:① 室外只 4 色(2bpp 本質),山的棕需 **per-scene 子盤**(town/dungeon/combat
    各重載 palette block,在 `ult4.x` 繪圖碼)→ 完整多場景彩色需抽 block 表或 emulator dump
    ② 模組 + F2 整合(tileset 已可產,差包裝)。
  - **方法論**:console/computer 的地圖常是 **chunk 化**(U4 經典 16×16 chunk),線性讀=帶狀
    噪訊,de-chunk 即還原;有了「已知該長怎樣」的地圖就是**最強 palette/tile oracle**。
- **音樂(YODEL/BIG-X)檔案層可抽,免錄音**:`ult.mgd`(MML 曲譜)+ `ult.smp`(PCM)+
  `ult.efc`(音效)是磁碟獨立檔。轉現代格式需逆向 MGD 結構(較重),但抽檔本身已可。
- **可行性:易-中**。**教訓**:「Human68k 讀不出」是 boot sector 無 BPB 的假象,底層仍 FAT12,
  自寫 reader 即破——別被 mtools 的 "non DOS media" 嚇退。

### Amiga — 🟢 完整破解(LZW 解壓 + 內嵌 palette + 逐列交錯 bitplane,16 色色彩正確)
- `7z` 解 `ultima4_amiga_win.7z` = GamesNostalgia WHDLoad 包(Psygore 1988 Origin 官方版),
  資料**已解包在硬碟映像目錄,不需破 .adf**:`.../data/ultmapp/`(路徑含空格 "Hard Drives"
  → 先 cp 到無空格路徑再 docker -v)。
- **tileset 管線(`tools/amiga/`)**:
  1. `U4SH.LWZ`(16658B,熵 7.58 = 壓縮)是 **U4 專屬 12-bit LZW** —— **直接用 xu4 引擎的
     `lzw/u4decode.cpp`+`lzw.c`+`hash.c`**(`lzw_unpack.c` C wrapper,`decompress_u4_memory`,
     **skip=0**,skip 2/4 會壞)→ 解出 **32800 byte**。**不需自寫 LZW、不需跳 header**。
  2. 解壓資料 = **前 32 byte = 16 色 palette**(Amiga `0x0RGB`,4-bit/分量)+ 256 tile × 128 byte。
  3. 每 tile 16×16 = **逐列交錯 bitplane**(每 row 8 byte = 4 plane × 2 byte,MSB 左)——
     **非**連續 plane、**非** chunky;autocorr lag=8(row)/lag=128(tile)。
  4. tile 序 = canonical U4 = xu4 256 序;解出**清楚彩色 U4 tile**(ankh/城堡/船/磚牆/生物)。
  - 工具:`extract_amiga.sh`(端到端)、`build_amiga_tileset.py`、`lzw_unpack.c`。
- 音樂:`mus[tbcdo].bin` + `snds.bin` = Origin 自訂格式(非 MOD),檔案層可抽、需逆向(留後)。
- **教訓**:遊戲自家壓縮格式(U4 LZW)別自己重寫——**目標引擎(xu4)常已有現成 decoder**,
  編個 C wrapper 連它最穩;解壓後的 palette 常**內嵌在資料開頭**(省去 palette 大海撈針)。

### Apple II(1985,原版)— ⏸ 跳過待回頭
- 媒體:4× `.dsk`(DOS 3.3)。`ac -l disk.dsk`(AppleCommander)列 catalog;`ac -g` 取檔。
- tileset:SHAPES(Apple II **高解析**,位元打包 6 色 + artifact),需專屬解碼。
- 卡點:AppleCommander jar URL 要對版本(`1-9-0` 失效過,改 SourceForge 或 cppo/a2tools)。

### Sega Master System(SMS,非 Genesis)— 🟡 格式已解、圖形區已定位
> 媒體資料夾名標 `sega-genesis` 但實為 `.sms`(512KB Master System ROM,`TMR SEGA`
> @0x7FF0)。`7z x` 出 ROM,複製本機。
- **tile 格式**:SMS VDP tile = **8×8 4bpp planar**,每 row 4 byte(plane0..3,weight
  1/2/4/8),MSB=左,32B/tile。`tools/sms/sms_tiles.py`(overview 掃 + page 放大)。
- **圖形區已定位但切不出 tile bank(架構性卡點)**:整 ROM overview 多 code/未壓縮資料
  (熵 <6.5,**非壓縮**);唯一清晰圖形區 `0x40000–0x44000` 放大後是**「已用 name-table
  排好的整張場景 bitmap」**(連續磚牆+草地+水域 + 標題曲線),**不是** 256 個分離 16×16
  sprite。SMS 走 **VDP name-table + pattern bank**:8×8 pattern 散在 VRAM、靠 name-table
  組畫面;raw ROM 線性序 ≠ xu4 邏輯 tile 序,缺 name-table 對映無法歸位 → **靜態切 ROM
  做不出對齊 xu4 的 256-tile sheet(0/256)**。tile 格式(8×8 4bpp planar)本身已驗證正確。
- **palette**:ROM 內找不到能讓 idx2=草綠/idx4=水藍/idx14=磚白同時成立的 16-byte CRAM
  table;用 0x40A00 地形區 index 直方圖**反推**固定盤可正確彩現(`build_sms_tileset.py`
  的 SMS_PAL),但非 ROM 原盤。
- **✅ 已解:libretro genesis-plus-gx 核心 headless dump VRAM**(`tools/sms/lr_dump.c` +
  `dump_vram.py`)。用 libretro core 跑 `u4.sms`、進世界/城/title 畫面,dump **VRAM(64K)+
  CRAM(128B)**:
  - VRAM = pattern generator table(8×8 4bpp planar,32B/tile,前 16K=448 tile);
  - CRAM = 32 色真 palette(genesis-plus-gx 把每色 1 byte `--BBGGRR` 存成 uint16 低 byte;
    取低 byte → RRGGBB 各 2-bit → 0/85/170/255 四階)。**免反推、色彩正確**。
  - 解出**色彩完美的世界地圖**(藍水/綠林/金船/灰城堡/洞穴/山),SMS 從「受阻」變「已解」。
  - **殘餘**:VRAM 只含「當下載入」的 tile(進不同畫面 dump 不同子集),要湊滿 256 + 對 xu4
    序需多畫面 dump 合併;但 emulator headless dump 的**核心方法已通**(libretro core 是最
    容易 headless 自動化的路,比 GUI 模擬器穩)。
- **方法論教訓**:console ROM 的圖形未必是「tile bank」——可能是 name-table 排好的
  **場景 bitmap**;raw ROM 線性切 ≠ 邏輯 tile 序。確認方式:放大看是「連續鋪滿的畫面」
  還是「格狀分離 sprite」。FM Towns 有現成 256-tile sheet(省事),SMS/console 多半要 VRAM dump。

### Amiga — ⏳ 未動
- `7z` 解 → planar bitplane tile(Amiga 5-6 plane);音樂 MOD/samples。

## Headless / 容器雷(必踩)

- **F2 熱切換 / `-m <module>` 載入在 Docker 軟體 GL(llvmpipe)死鎖**:`screenReInit` 重建
  GPU 紋理卡死。**真機硬體 GL 正常**。→ 多主題畫面**無法 headless 截圖驗證**,需真機。
- **絕不留卡死容器**:截圖一律走 `srun.sh`(容器**內** `timeout -s KILL` + 具名 + 結尾
  `docker kill`),F2/載入死鎖也自我了結。只靠外層 `timeout` 只殺 client、容器永生(曾掛 32h)。
- 檔名含空格:`for d in $(find...)` 會被切斷 → 用 `while IFS= read -r`。

## 通用原則

- **tileset 必須對齊 xu4 的 256-tile 順序**;若平台 tile 序不同,需逐 tile 對映表
  (FM Towns 的 `ULTIMA4.TIL` 剛好同序,省事;MSX/其他不一定)。
- **引擎/資料分離**:抽出資產 + 模組內 tileset/音樂(版權)**不入 repo**;repo 放
  解碼工具 + 模組 def + 條件式 apply。decode 工具須**確定性**(同輸入同輸出,可驗 reproducibility)。
- 解碼新格式 SOP:① 算 size/tile-count 候選 ② 對照已知 tile 0 的視覺特徵 ③ 試 nibble 序 /
  layout 變體 ④ grid 預覽目視 ⑤ 確認後輸出 16×4096 PNG。

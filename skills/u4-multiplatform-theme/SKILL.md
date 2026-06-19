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

### MSX2(1987,Pony Canyon)— 🟡 tile 解碼 mid-RE
- 媒體:`.dsk`(MSX-DOS **FAT12**,`mtools` 可讀:`mdir -i x.dsk ::`,需 `MTOOLS_SKIP_CHECK=1`)。
- 檔案:`SHAPE.DAT`(24576)=tileset、`FONT.DAT`(8064)、`CARD1-3.MSX`(吉普賽卡)、
  `II1X-7X.MSX`/`RUNE*.MSX`/`ENDPIC.MSX`(intro/結局,~19460/11620,SCREEN 圖)、
  `U4MAP.BIN`/`TALKDATA.BIN` 等 game data。`mcopy -i x.dsk ::FILE .` 取檔。
- **未解**:`SHAPE.DAT` 24576 = 192×128(4bpp 16×16)或 256×96。標準 row-major
  chunky 4bpp(高/低 nibble 兩序)解出**噪訊** → MSX VRAM 排列另有玄機
  (待試:Y-interlace、quadrant 8×8 切、planar、或 SCREEN5 line 交錯)。調色盤用
  MSX2 SCREEN5 標準 16 色。**下一步**:對照已知 U4 tile 0(深水雙色橫紋)逐 byte 反推 layout。

### X68000 — 🔴 最難(未動)
- 媒體:`.hdm`(**Human68k FS**,`7z`/`mtools` **讀不出**)→ 需 Human68k 專屬讀碟工具。
- tileset:程式碼 `_loadshape`/`_shapebuf`/`_shapecount`(shape 從 `.dat` 載入,X68k 格式)。
- **音樂**:`"Ultima music driver (C) YODEL & BIG-X"` = **自訂序列驅動**(非 CD-DA/標準 MDX)
  → 幾乎只能**從 X68000 模擬器(px68k/XM6)跑遊戲錄製**,或逆向該驅動。建議最後做。

### Apple II(1985,原版)— ⏸ 跳過待回頭
- 媒體:4× `.dsk`(DOS 3.3)。`ac -l disk.dsk`(AppleCommander)列 catalog;`ac -g` 取檔。
- tileset:SHAPES(Apple II **高解析**,位元打包 6 色 + artifact),需專屬解碼。
- 卡點:AppleCommander jar URL 要對版本(`1-9-0` 失效過,改 SourceForge 或 cppo/a2tools)。

### Sega SMS / Amiga — ⏳ 未動
- SMS:`.sms` ROM,VDP tile(planar 4bpp)+ palette;音樂 PSG。
- Amiga:`7z` 解 → planar bitplane tile;音樂 MOD/samples。

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

# Ultima IV: Quest of the Avatar 中文化 — 評估與執行計畫 (PLAN)

> 本檔由 `CLAUDE.md` 潤飾展開,並把「掃描 `u4remastered` 原始碼 → 可行性評估 → 規劃」三步合併產出。
> 立案日:2026-06-04 ・ 維護:L.CY (anr2) + Claude
> 風格參考:`u3-cht/PLAN.md`、`u6-cht/README.md`。

---

## 0. TL;DR(先說結論)

| 問題 | 結論 |
|---|---|
| `u4remastered` 能當 SDL2 + Linux/Windows + 中文化的基礎嗎? | **不能,且是最差選擇。** 它是 **C64 6502 組合語言**移植版(23,101 行 `.s`),整個引擎綁死 C64 硬體(VIC-II、fastloader、EasyFlash),**沒有任何可攜遊戲邏輯可保留**。 |
| 那它的價值在哪? | **作為對話文字的 oracle / 乾淨字料來源**。`src/talk/talk.json`(175KB,256 NPC)已是結構化、且修過數十個對白 bug 的高品質英文字料,可直接拿來當翻譯底本。 |
| 中文化最佳基礎是什麼? | **`xu4`(xu4-engine/u4)** —— Allegro 5 / GLFW 跨平台 C++、Linux/Windows 都跑、已可全破,**且已有德文在地化前例**。這是 U4 版的「Nuvie 路線」,對應 U6-cht 用 ScummVM 的成功經驗。 |
| 需要哪些原始檔案? | xu4 路線:**PC/DOS 版 U4 資料檔**(`ultima4` upgrade 版,GOG / 免費釋出版皆可)。`u4remastered` 自身 build 才需要 4 個 C64 `.d64`。 |
| 工程量級 | xu4 路線屬「移植已有在地化機制 + 翻譯 + 中文字型」,與 U6-cht 同量級;**重寫 u4remastered 為 SDL2 則是「從零重寫整個遊戲」,不建議。** |

> ⚠️ **這是與 CLAUDE.md 原始假設的重大衝突點**:CLAUDE.md 寫「scan remastered source code、用 SDL2 繪製」,但實測 `u4remastered` 是 C64 組語,對 SDL2 重繪而言是死巷。本計畫據實調整為 **xu4 路線**,並在 §12 標示為待確認決策。

---

## 1. 評估目標與方法

### 1.1 CLAUDE.md 要求
1. 使用 SDL2 繪製圖形;支援 Linux / Windows。
2. 確認需要哪些原始檔案 (U4)。
3. 中文化可行性評估。
4. 掃描 `./u4remastered` 原始碼。
5. 搜尋此 U4 remaster 的背景資訊。
6. 參考 u6-cht / u3-cht 風格(尤其 README.md)規劃 PLAN.md。

### 1.2 方法
- 直接 clone 後實測 `u4remastered` 檔案結構、原始碼語言、文字/字型/資產格式(本機證據,非臆測)。
- 對照 U4 開源引擎生態(xu4),確認跨平台 + 中文化可行路徑。
- 依 L.CY 「先驗證、再下結論」原則:所有結論附本機證據或來源連結。

---

## 2. `u4remastered` 是什麼(實測證據)

**身分**:MagerValp(Per Olofsson)的 **Ultima IV C64 重製版**(2006–2015,Apache 2.0)。官方 repo `MagerValp/u4remastered`,改善了 tileset 配色、角色創建美術、地牢渲染、joystick、fastloader、EasyFlash 卡匣等。**目標平台是實體 Commodore 64**。

### 2.1 原始碼語言組成(本機統計)

| 副檔名 | 行數 | 性質 |
|---|---|---|
| `.s` (6502 asm) | **23,101** | 遊戲本體,**全部綁 C64 硬體** |
| `.c` | 3,334 | 僅 host 端工具 / save editor,**非遊戲邏輯** |
| `.h` | 191 | 工具 header |
| `.py` (tools) | — | 資產建置(Python 2.x,`print` 舊語法) |

> 對照 U3 的 LairWare 版是 **MIT C 遊戲邏輯**(可攜、可剝離平台層)。U4 這個 remaster **完全相反**:沒有 C 遊戲邏輯,只有 6502 組語。

### 2.2 目錄結構透露的硬體耦合

```
src/
├── drivecode/      ← 1541/1571/1581 磁碟機 fastloader 組語
├── easyflash/      ← EasyFlash 卡匣 bank switching
├── efloader/ ifflloader/ u4loader/  ← C64 載入器
├── crackintro/     ← C64 crack intro + SID 音樂
├── gamemain/ patchedgame/  ← 遊戲主體(6502),patch 原版 binary
├── charcreate/     ← 角色創建,美術為 .koa (Koala Painter C64 格式)
├── talk/           ← talk.json + talk.s(對話資料 + 6502 顯示碼)
└── tiles/          ← tiles.png 256×256 + font.png 256×32(C64 charset)
```

- **繪圖**:VIC-II multicolor、hires bitmap;tile 是 `tiles.png`(C64 調色板 8-bit colormap),字型是 `font.png`(256×32 = 128 個 **8×8** 字元 charset)。
- **音樂**:SID 晶片(`crackintro` 內 `.sid`)。
- **載入**:自製 fastloader drivecode + IFFL + exomizer 壓縮。
- **build 產物**:`.d64` 磁碟映像 / `.crt` 卡匣,**只能在 C64 或 VICE 模擬器上跑**。

### 2.3 文字機制(關鍵)

`src/talk/talk.json` — 256 個 NPC 條目,結構乾淨:
```json
{"name":"Joshua","description":"a wise mage.","health":"Well.",
 "job":"I can help.","keyword_1":"HELP","keyword_response_1":"The riddle!",
 "question":"More?","question_yes_answer":"What one thing\ncreates and is\ncreated by all\ntruths..."}
```

但 `tools/gen_talk.py` 暴露了**死巷**:
- 文字編碼為 `ord(c) | 0x80` —— **單位元組、高位元設旗標的 PETSCII/ASCII**,無多位元組空間。
- 硬性檢查 `len(line) > 16` → **每行上限 16 字元**(C64 對話框寬度)。
- 顯示走 8×8 charset,一格一字元。

> ⇒ 在**真實 C64 顯示管線**上做中文:8×8 格塞不下漢字、16 字元行寬、單位元組編碼,三重死巷。這與 U3 評估裡「改 DOS 原版 binary」被判死刑是同一類問題。

---

## 3. 為何 `u4remastered` 不適合本專案目標

CLAUDE.md 要的是 **SDL2 / Linux / Windows / 中文**。把 `u4remastered` 推到這個目標,只有兩條路,都不可行:

| 路徑 | 做法 | 為何不可行 |
|---|---|---|
| A. 6502 → SDL2 重寫 | 把 23,101 行組語的遊戲邏輯逐段翻成 C/SDL2 | 等於**從零重寫整個遊戲引擎**;組語無模組邊界、無型別、與 C64 記憶體映射糾纏。工程量遠大於直接用現成 C++ 引擎,且無 oracle 保證行為一致。 |
| B. 跑在 VICE 模擬器 | 直接用它的 `.d64` / `.crt` | 那就是**原汁 C64**:8×8 charset、16 字元行寬、SID 音樂。**SDL2 重繪與中文字型完全用不上**,中文化仍是死巷。 |

**結論**:`u4remastered` 的工程價值不在「當引擎基礎」,而在「當乾淨字料 + 行為對照 oracle」(見 §7)。

---

## 4. 候選基礎比較

| 方案 | 技術 | 授權 | 跨平台 | 中文化適性 | 評價 |
|---|---|---|---|---|---|
| **`xu4` (xu4-engine/u4)** ⭐ 採用 | C++ + **Allegro 5 / GLFW** | GPL | **Linux / Windows / Mac** 原生 | 高(已有德文在地化前例、文字外部化) | **最佳基礎** |
| `u4remastered` (MagerValp) | 6502 asm + cc65 | Apache 2.0 | **C64 only** | 極低(8×8 / 16 寬 / 單位元組) | **只當字料 oracle** |
| ScummVM 內 Ultima4 | C++(吸收自 xu4) | GPL | 多平台 | 中(engine 較重,改動面大) | 次選;U6 走過 ScummVM,但 U4 standalone xu4 更輕 |
| 改 DOS 原版 binary | x86 patch | EA IP | — | 極低 | 不考慮 |

> 註:xu4 本身已用 **Allegro 5** 繪圖,**「用現代繪圖庫取代 C64 native」這個需求在 xu4 路線是現成的**,不需要像 U3 那樣自己重寫繪圖層。這讓 U4 中文化比 U3 更省工。(CLAUDE.md 原寫「SDL2」,實務上由 Allegro 5 達標,見 §5.1a 決策 D3。)

---

## 5. 採用方案:`xu4` + 中文化

### 5.1 為什麼是 xu4
- **跨平台引擎**,Linux / Windows 開箱即跑,符合 CLAUDE.md 平台需求。
- **可完整破關**,維護中(Karl Robillard / Whitesmoke,Codeberg + SourceForge)。
- **已有德文在地化**,證明文字外部化 + 在地化管線存在,非從零開。
- 對應 U6-cht 用 ScummVM/Nuvie 的成功路線:**用成熟開源引擎 + hook 翻譯**,而非重寫。
- ✅ **內建 `Dockerfile.gcc`(Linux)+ `Dockerfile.mingw`(Windows 跨編)** → 直接滿足 Docker-first + 雙平台需求。

### 5.1a ⚠️ 後端不是 SDL2,是 Allegro 5(實測,待決)
clone 後實測現役 xu4(xu4-engine/u4):
- **平台 API = Allegro 5.2 / GLFW 3**;`configure` 內 **SDL 1.2 已註解為 legacy**。**沒有 SDL2 路徑。**
- 渲染:預設 `GPU=scale`,可開 `--gpu`(OpenGL,`gpu_opengl.cpp`)。
- 字型:**`.txf` GPU texture-atlas 字型**(`module/render/font/cfont-*.txf` + `cfont.png`),非 U6 那種 8×8 bitmap `.fnt`。
- 對話資料:`discourse_tlk.cpp` 讀原版 **`.TLK`**;遊戲資料打包為 `module/Ultima-IV` + `module/U4-Upgrade`。

→ **決策 D3**:CLAUDE.md 寫「用 SDL2」。現役 xu4 是 Allegro 5。兩個子選項:
  - **(a) 採 Allegro 5 版 xu4(建議)**:Linux+Win+Docker 全現成,維護最新;把「SDL2」理解為「用現代繪圖庫取代 C64 native」的泛指即達標。
  - (b) 硬要 SDL2:得退回舊版 SDL xu4(1.x / ScummVM-Ultima4),版本較舊、需自行接 SDL2。**不建議**,徒增工。

### 5.2 中文化策略(沿用 U6-cht 心法)
U6-cht 的核心經驗可直接套用:
1. **Load-time 替換,不改原始 bytecode**(U6 的 Plan B):英文字串照常解析,輸出前查表換中文 → 零位元組對齊風險。
2. **找齊所有輸出 codepath**:grep 所有顯示 / print call site,逐一 hook 或繞回統一翻譯函式。
3. **Binary length-prefixed lookup**:避開編碼 escape 衝突(U6 踩過 Big5 trail `0x5C`)。
4. **中文字型走點陣 .fnt 或 TTF embedded bitmap**:xu4 用自己的 bitmap font,需擴成支援 CJK glyph。

> 與 U6-cht 不同處:xu4 字型與 U6 不同、文字資料來源不同(xu4 從原版 PC 資料檔抽 talk),需重新定位 hook 點。但**方法論完全可複用**。

---

## 6. 需要哪些原始檔案 (U4)

| 路徑 | 需要的原始檔 | 來源 |
|---|---|---|
| **xu4(採用)** | **PC/DOS 版 U4 資料檔**:`ultima4` upgrade 版整包(`AVATAR.EXE`、`TLK`/`WORLD.MAP`/`*.ULT`/`*.DNG` 等)。xu4 讀標準 PC U4 資料。 | U4 自 2011 起由 GOG / EA 免費釋出;xu4 文件提供取得方式。**合法免費取得。** |
| u4remastered build(僅當需重建字料 oracle) | 4 個 C64 `.d64`:`u4britannia.d64` / `u4program.d64` / `u4towne.d64` / `u4underworld.d64`(README 附 SHA1) | 原版 C64 磁碟映像 |

**待辦**:確認本機是否已有 PC 版 U4 資料(U3 專案目錄有 `Ultima_III_..._1983.zip`,U4 需另備)。

---

## 7. `u4remastered` 的剩餘價值(不浪費)

掃描它**不是白工**,它對 xu4 中文化有兩個實際用途:

1. **`talk/talk.json` 當翻譯底本**:這是**修過數十個對白 bug** 的乾淨字料(Changelog 列出 Thevel / Serpent's Hold / Estro 等修正),結構化、欄位清楚(name/description/job/keyword_response/question…),比直接從原版二進位抽字更好讀。可作為**翻譯來源與校對 oracle**。
2. **行為 / 對白觸發 oracle**:keyword 觸發、question trigger 等邏輯在 `talk.json` 標得很清楚,可對照 xu4 行為。

> 對應 U3 專案裡 mcmagi 反組譯文件的角色定位:**不是引擎,是 ground-truth oracle。**

---

## 8. 中文化工作拆解(xu4 路線)

| 模組 | 工作 | 對應 U6-cht 經驗 |
|---|---|---|
| **引擎建置** | Docker 內 build xu4(Allegro 5);Linux ELF 跑起來、可進主畫面 | U6 ScummVM build |
| **文字 hook** | 定位 xu4 所有文字輸出 codepath(對話 / 選單 / look / 戰鬥訊息),統一繞回翻譯查表 | U6 的 8 個 engine hook |
| **字串抽取** | 從 xu4 / 原版資料抽英文字串,對齊 `u4remastered/talk.json` 當底本 | U6 dump translations |
| **翻譯** | 對話 + 系統字串中文化,文白並用,沿用聖者之書譯名體系(八德 / 城市 / 咒語) | U6 glossary + 文白策略 |
| **中文字型** | xu4 bitmap font 擴 CJK;選可商用 TTF 或點陣 .fnt | U6 `big5_*.fnt` / AR PL UMing |
| **lookup 格式** | binary length-prefixed,byte-safe | U6 v3 binary format |
| **驗證** | Docker build + headless 截圖 diff + game tester 背景跑 | U6 in-game test |

---

## 9. 字型策略 + 文字架構(P2 實測,2026-06-04)

### 9.1 xu4 有兩個中文化文字面(實測 `src/screen.cpp` + `src/support/txf_draw.{h,c}`)

| 文字面 | 渲染路徑 | 編碼現況 | CJK 改法 | 對應 U6 |
|---|---|---|---|---|
| **遊戲內文字**(對話/訊息) | `screenMessage`/`screenTextAt` → `screenShowChar(byte,col,line)` → 原版 U4 **CHARSET 點陣字**(`BKGD_CHARSET` image,逐 byte 索引一格,格寬 = `charset->width()` 方形) | 單位元組 ASCII(128 字) | 換 CHARSET + 改多格渲染 + tokenizer/行高 | `U6Font`(坑 #3 tokenizer、#4 行高) |
| **GUI / 選單 / 遊戲瀏覽器** | `.txf` SDF 紋理字(`cfont-comfortaa/avatar/symbols.txf` + `cfont.png`) | glyph `code` = **uint16**(可定址 BMP/CJK);但 `txf_genText` 第 165 行 `txf_glyph(tf, *it++)` **逐 byte、不解 UTF-8** | 加局部 UTF-8 解碼 patch(`txf_genText`)+ 產 CJK SDF atlas | `ConvFont`/`WOUFont` |

### 9.2 字型 PoC 結論(決定性)
- ✅ **編碼有 headroom**:txf glyph code 為 **uint16**,可定址常用漢字;`txf_glyph(tf,int c)` 已支援大碼位。**遠優於 u4remastered**(單位元組、8×8、16 字寬死巷)。
- ⚠️ **txf 逐 byte**:`txf_genText` 目前不解 UTF-8 → 需一個**局部 UTF-8 解碼 patch**(decode 多 byte → codepoint → `txf_glyph`),約十餘行,bounded。
- ⚠️ **要看到中文字需先建字型資產**(P4 主工,二擇一或併用):
  - (a) **CHARSET 路徑**:把 U4 CHARSET 點陣字擴成 CJK(每格放一漢字),改 `screenShowChar` 支援多格/全形寬。適合遊戲內對話。
  - (b) **txf SDF 路徑**:用 **msdf-atlas-gen** 從 CJK TTF 烘一套子集 SDF atlas（只烘 `talk.json` + 系統字串去重後的漢字),加 UTF-8 patch。適合 GUI/選單。
- 來源 TTF 依 CLAUDE.md「優質系統中文 TTF」:**Noto Sans CJK TC** / **AR PL UMing** / **文泉驛**。
- ⚠️ atlas 全字集大 → **只烘實際用到的漢字子集**控制尺寸。

---

## 10. 分階段交付(每階段一個 pass/fail loop + commit/push)

| Phase | 內容 | 可驗證產出 |
|---|---|---|
| **P0 決策確認** ★ | 確認改走 xu4(見 §12);取得 PC 版 U4 資料檔 | ✅ **已完成**:決策拍板;`make download` 自動抓 freeware 資料 |
| **P1 引擎建置** | Docker(Allegro 5)build xu4 → 二進位 + 模組 + 資料就位 | ✅ **已完成**:`Dockerfile.zh` build 成功(見 §6a) |
| **P2 字型 PoC** | headless 截圖 loop + 文字架構盤點 + 字型可行性驗證 | ✅ **loop+驗證完成**(§10a/§9);畫出中文字移至 P4(需先建字型資產) |
| **P3 文字 hook 盤點** | grep xu4 所有輸出 codepath,產 hook backlog | ✅ **已完成**:`docs/P3-hooks.md`(H1–H8 + 字串來源 + P4 backlog) |
| **P4 字串抽取 + 對齊** | 抽英文字串,對齊 `talk.json` 底本,建雙語表 | 🔵 **資料面已完成**:`tools/extract_tlk.py` → 256 NPC 雙語表 `dumps/talk_bilingual.json`(§10c);intro/硬編字串待抽 |
| **P5 翻譯** | 對話 + 系統字串中文化(glossary + 文白並用) | ✅ **四源全譯**:talk 256 NPC + stringtable 114 + 硬編 318 + vendor 278;format/佔位符 0 不符(§10e) |
| **P6 整合驗證** | lookup 接上、CJK 換行、game tester 背景跑最小遊玩迴圈 | tester 無 regression |
| **P7 收尾** | 跨平台(Win)打包、README/CREDITS、授權聲明 | 可散布(自用)版本 |

### 10a. P1 建置結果(2026-06-04 實測)

`u4-cht/docker/Dockerfile.zh`(Ubuntu 24.04 + Allegro 5;`docker build -f docker/Dockerfile.zh -t u4cht/xu4-allegro xu4`)成功,image `u4cht/xu4-allegro`:

| 產物 | 內容 |
|---|---|
| `src/xu4` | 1.1MB 二進位,**xu4 vDR-1.0**;`ldd` 確認連結 `liballegro.so.5.2` + `libfaun.so.0` + png + vorbis |
| `Ultima-IV.mod` | 7.4MB,完整遊戲資料模組 |
| `U4-Upgrade.mod` / `render.pak` | VGA upgrade 模組 / 渲染資源(含 `cfont.png` 字型) |
| `ultima4.zip` + `u4upgrad.zip` | **`make download` 自動下載**(freeware:`ultima.thatfleminggent.com` + sourceforge) |

**建置鏈**:apt(allegro5/png/vorbis/pulse)→ 自源碼建 Boron v2.0.8(程式 + libboron.a)→ 自 submodule 建 Faun(`--no_flac`)→ `./configure --allegro && make download && make`。
**原始檔結論**:U4 原版資料由 `make download` 自動取得,**無需手動準備**(R4 解除)。
**CLI 驗證**:`xu4 --help` 正常列出選項(`--skip-intro`/`--module`/`--scale`/`--filter`);無內建 headless 截圖模式。

### 10b. P2 headless 截圖 loop(2026-06-04 實測)

- `u4-cht/docker/Dockerfile.test`(FROM `u4cht/xu4-allegro` + xvfb + Mesa 軟體 GL + ImageMagick)+ `docker/shot.sh`:`Xvfb :99` + `LIBGL_ALWAYS_SOFTWARE=1`(llvmpipe)跑 `xu4 -q -s <scale> --filter xBRZ`,等 N 秒後 `import -window root` 截圖。
- **用法**:`docker run --rm -v /out:/out u4cht/xu4-test <等待秒數> <scale> [額外 xu4 args]`。`shot.sh` **預設帶 `--filter xBRZ`**(灰階 CJK AA 最平滑);第 3 參數自帶 `--filter` 可覆蓋,或附加 `--skip-intro` 等(已防重複 `--filter`)。實際指令記於 `/out/xu4.log` 首行 `+ ...`。
- ✅ **驗證通過**:截到完整「**Ultima IV — Quest of the Avatar**」標題畫面 + 動態世界地圖(960×600,scale 3)→ 證明 Allegro 5 + GL 渲染管線在 Docker headless 全程可跑。**此即 P3+ 的決定性 pass/fail loop。**
- ⚠️ intro 為動畫,截圖時點影響畫面;後續做穩定基準時改用固定狀態(如進遊戲後固定座標)再 diff。

### 10c. P4 資料面:.TLK 抽取 + 對齊(2026-06-04 實測)

`tools/extract_tlk.py`(**不改引擎**,依 `src/discourse_tlk.cpp` U4Talk_load 格式抽 16 個 DOS `.TLK`):

| 項目 | 數字 |
|---|---|
| 抽出 NPC 對話 | **256**(16 城 × 16 record × 288 byte) |
| 以 name 對齊 `talk.json` | 250 / 256 |
| name 無對應(DOS name 欄位異常,疑似 remaster 修過的 broken NPC) | 6 |
| 英文內容差異(remaster 修對白 + DOS keyword 4 字截斷 + 換行) | 188 |

- 產出 `dumps/talk_bilingual.json`(每 NPC × 12 欄 `{en, zh}`,en = `.TLK` 原文 = H1 lookup key,description 已套引擎執行時修飾;zh 待填)+ `dumps/talk_alignment_report.md`。
- 翻譯 key 以 DOS `.TLK` en 為準;`talk.json` 作校對參考。raw `.TLK`/zip 不入庫(`/data/`)。
- 詳見 `docs/P3-hooks.md` §6。

### 10d. P4 資料面續:stringtable + 硬編字串抽取(2026-06-04 實測)

純資料抽取/報告,**不改引擎**:

| 工具 | 來源 | 結果 | 產出 |
|---|---|---|---|
| `tools/extract_stringtable.py` | `title.exe` + `avatar.exe`(`u4read_stringtable`) | **114** 字串(intro 28+24+15、codex 11、endgame 7+5、shrine 24) | `dumps/stringtable_bilingual.json` + `_report.md` |
| `tools/extract_hardcoded.py` | `xu4/src` 靜態分析 `screenMessage` 系列字面 | **420** call site / **318** 唯一 / 128 含 format / 26 dynamic | `dumps/hardcoded_strings.json` + `_report.md` |
| `tools/extract_vendor_boron.py` | `module/Ultima-IV/vendors.b` Boron 腳本 | **278** 唯一 vendor 字串(19 braced / 62 含佔位) | `dumps/vendor_bilingual.json` + `_report.md` |

- 翻譯注意:`%c…%c` 顏色碼保留;含 `%s/%d` 需 format-aware hook;vendor 佔位 `@ % $ # = $gp` 保留;原版拼寫不一致需 glossary 正規化。
- **資料面收尾**:`.TLK` 256 NPC + stringtable 114 + 硬編 318 + vendor 278 = **資料面四源齊備**;僅剩 `maps.b`/`config.b` 零星告示牌(低優先)。
- 詳見 `docs/P3-hooks.md` §7。

### 10e. P5 翻譯:NPC 對話(2026-06-04)

`talk_bilingual.json` 256 NPC 翻譯,**分批平行 + 共享 glossary**(純資料,不改引擎):

- **共享 glossary**:`docs/glossary-u4.md`(八德/城市/真言/職業/夥伴固定譯名 + 文白並用規則 + 欄位規則),所有 agent 必須遵守 → 避免術語漂移(U6 坑 #7)。
- **流程**:`tools/talk_batches.py split`(8 批,每批 2 城 32 NPC)→ 8 個平行 agent 翻譯 → `merge` 回填 → 正規化(空槽 `"A"` 還原、keyword 強制空)。
- **結果**:非 keyword 欄位 **2560/2560 = 100%** 已譯;`keyword_1/2` 不譯(玩家輸入英文指令);真言代碼(AHM/MU…)6/6 保留;`Avatar→聖者`、`Lord British→不列顛王` 跨批 **0 不一致**。
- 中間批次檔(`dumps/batches/`)已 gitignore;canonical 為 `dumps/talk_bilingual.json`。

**其餘三源(2026-06-04,`tools/string_batches.py` split/merge + 8 平行 agent)**:
- `stringtable_bilingual.json` 113 譯(intro/codex/shrine,1 空字串);`hardcoded_strings.json` 318(292 譯 + 26 控制 zh=en);`vendor_bilingual.json` 278。
- **全域校驗**:hardcoded `%s/%d/%c` + `\n` 計數 **0 不符/318**;vendor 佔位符 `@ % $ # =` **0 不符/278**。
- 控制/純 format 字串自動 zh=en 不送翻譯;批次檔 `dumps/batches2/` gitignore。

### 10f. P6 字型 + 接 hook 垂直切片(2026-06-04,動引擎)

CJK 字型 + H1 hook PoC,headless Docker 驗證通過:

- **資料側**:`tools/build_cjk_font.py`(掃四源 zh → 1978 唯一漢字 → **Noto Sans CJK TC Medium**(`--index 3`)烘 16×16 atlas `assets/cjk_font.bin`)+ `tools/build_lookup.py`(四源合併 en→zh 二進位 `assets/u4_cht.tab`,2614 條,依 en 排序)。
  - **字型可讀性**(2026-06-04):
    - 字型:Noto Sans CJK TC **Medium** 優於 AR PL UMing(Ming serif 細筆易斷)與 Noto Bold(密筆糊);對比 `docs/screenshots/03_font_compare.png`。
    - **灰階 AA**:`build_cjk_font.py --mode gray`(預設)存抗鋸齒 alpha,`cjkBlit` 用該值混黑底(二值 atlas 仍相容)→ 斜筆/曲線鋸齒減少;對比 `docs/screenshots/04_aa_compare.png`。
    - **放大 filter**:xu4 預設 `--filter point`(nearest-neighbor)會把 AA gray 邊緣放大成方塊、部分削弱 AA。`--filter` 無字面 linear,但平滑放大器(`xBRZ` / `HQX`)會把 AA 邊緣補成連續筆畫 → **`--filter xBRZ` + 灰階 AA 最平滑可讀**;對比 `docs/screenshots/05_filter_compare.png`。**`docker/shot.sh` 已將 `--filter xBRZ` 設為 headless 截圖預設**(可被第 3 參數覆蓋)。
- **引擎側**(`patches/engine/`,套用 `tools/apply_cht.sh`):
  - 新模組 `cht.cpp/h`:載入資產 + `chtLookup`(二分)+ `chtGlyph`。
  - `screen.cpp`:`cjkBlit`(16×16 全形,**灰階 alpha 混色** blit 到 `xu4.screenImage`)+ `screenMessageCJK`(UTF-8、CJK-aware 換行)+ **H1 `screenMessageN` 進入查表命中改走 CJK**;`chtSelfTest`(env 守護)。
- **驗證**:`U4CHT_SELFTEST=1` 用真實 `chtLookup` 渲染已知 NPC 對白 → 截圖顯示「一位迷人的吟遊詩人。」「馬精西亞城為其驕傲所毀。」(`docs/screenshots/02_cjk_ingame.png`)。log:`loaded 2614 translations / 1978 glyphs`。
- **限制**:文字區 16×12@8px → CJK 每行 8 字;含 `%s/%d` 硬編字串需 format-aware;vendor Boron 路徑待驗;長對白 CJK 換行/捲動待精修(P7)。

### 10g. P7 多文字面 hook + 實機驗證(2026-06-04,動引擎)

**新增 hook**(`patches/engine/cht-engine.patch` 已含 screen.cpp 148 行 + textview.cpp 43 行):
- **#3 format-aware**:`screenMessage` 先查 `fmt` 字串,命中以中文 format 餵 vsnprintf(`%s/%d/%c` 同序);`screenMessageN` 偵測 buffer 含 CJK 即走 CJK 渲染(涵蓋已翻 format 字串)。
- **#4 HUD**:`screenTextAt` 查表命中 → `screenDrawCJKAt`(絕對 cell CJK)。
- **#4 intro 選單 / 角色創建**:`TextView::textAt` + `textAtKey` 查表/含 CJK → CJK 渲染(view 原點)。新增 `dumps/ui_bilingual.json`(12 條選單/prompt)併入 lookup(2626 條)。

**#1 實機驗證**(`docker/verify.sh`,xdotool 驅動,**真流程非 self-test**):
- ✅ 主選單中文(啟程冒險/開始新遊戲/設定/關於)、命名提示、**性別提問「汝為男子抑或女子?」完美**。
- 截圖 `docs/screenshots/06_intro_menu_cht.png`、`07_charcreate_cht.png`。

**固定版面列距 — ✅ 已修(2026-06-04)**:
- `intro.cpp` 主選單 5 項改 2 列距(rows 2/4/6/8/10,捨「Options:」)、命名提示兩行改 row 2/4。
- **CJK 縮為 14px 置中於 16px cell**(`build_cjk_font.py --size 14 --cell 16`)→ 行距有呼吸空間、更清晰、「文字小一點」;引擎 `cjkBlit` 仍以 cell(16)為步距,免改。
- 對比 `docs/screenshots/08_cjk_14px.png`(16px 滿格相黏 → 14px 行距清楚)、主選單 `06_intro_menu_cht.png`。
- ⚠️ 仍屬「2 列距」方案:固定螢幕用較多垂直空間(選項較少可見)。徹底解 = 640×400 內部解析度(見 §10h spike)。

**建置 gotcha 修正**:Docker `COPY` 層快取會用舊 source/資產 → `Dockerfile.zh` 加 `ARG CACHEBUST`(改碼後 `--build-arg CACHEBUST=<新值>` 強制重編);`textview.cpp` 補 `<cstring>`。

### 10h. B spike:640×400 內部解析度可行性(2026-06-04)

**結論:✅ 可行**(throwaway spike 驗證,程式碼已還原,僅留證據截圖)。

- **架構**:`GPU=scale` 全程把 320×200 CPU 合成 framebuffer 上傳 GPU 放大;**無內建影像預縮放**。
- **spike 改動**(4 行):`u4.h` `U4_SCREEN_W/H`→640/400、`screen.cpp` `screenImage`→640×400、**`gpu_opengl.cpp` 螢幕紋理 + shader scDim 硬編 320×200→640×400**(黑畫面主因,GPU 管線唯二硬編處)。
- **結果**(`docs/screenshots/09_640_spike.png`):遊戲正常渲染,標題 + Britannia 地圖正確,**但美術/座標仍 320×200 → 畫面落在 640×400 左上 1/4**。證明解析度路徑可跑、GPU 耦合僅 2 處。
- **剩餘 productionize 工作**(中-大):`CHAR_WIDTH/HEIGHT` 8→16(`TILE` 自動 32)+ **全美術 2x**(charset/tiles/UI/intro 圖,需載入時 upscale 或 2x blit)。完成後 CJK 16px = 1 cell,**徹底免 2 列距、可放更多文字**。
- **決策**:A(14px + 2 列距)已可用且 ship-able;B(640)為「更佳但中-大工」的後續選項,待決定是否投入。

### 10i. B-full:640×400 全美術 2x regime(2026-06-04,**取代 A**)

**達成**:內部解析度 640×400 + 全美術 2x + **CJK 1-cell(16px)**,徹底解決 320 regime 的 CJK 重疊。

| 改動 | 內容 |
|---|---|
| 常數 | `u4.h`/`textview.h`:`CHAR_WIDTH/HEIGHT` 8→16(`TILE` 自動 32)、`U4_SCREEN` 640×400、`BORDER` 16 |
| GPU | `gpu_opengl.cpp` 螢幕紋理 + shader scDim 320×200→640×400 |
| 美術 2x | `imagemgr.cpp` 載入後 RGBA nearest 2x + **subimage 座標 2x**(集中式,涵蓋 charset/tiles/UI/border) |
| CJK | `screen.cpp`/`textview.cpp` CJK 進位 2→**1 cell**、line stride 2→1;`intro.cpp` 列距**還原**(16px 列已容 14px CJK) |
| 修 | `intro.cpp` beastie 硬編 `320-48`→`U4_SCREEN_W-96` |

**驗證**(xdotool 真流程,`docs/screenshots/`):
- `10_bfull_menu.png`:主選單 **CJK 1-cell 全乾淨**(返回畫面/啟程冒險/開始新遊戲/設定/關於,beasties + 標頭正確)。
- `12_bfull_charcreate.png`:命名提示「汝之名…為何 / 於此世此刻?」連續兩行**不再重疊**。
- `11_bfull_map.png`:Britannia 地圖 2x 正確填滿。

**標題動畫 2x — ✅ 已修(2026-06-04,第三次成功)**:
- `AnimPlot` x,y `uint8_t`→`int16_t`(容 640 座標);`addTitle` 座標 `x,y,w,h` ×2(抽取/destImage/落點全 640 space);SIGNATURE plot ×2 位置(漸層仍用 1x y)+ fillRect 2×1→4×2;TITLE plot int16 + PRESENT 排除 133→266/y<6→y<12;`BKGD_OPTIONS_BTM` 13 處 (0,120)→(0,240)。
- 結果:**標題畫面 + 選單完美**(「Ultima IV」清晰、QUEST OF THE AVATAR、雙龍、藍框位置正確、CJK 選單乾淨)。`docs/screenshots/17_bfull_title_fixed.png`、`10_bfull_menu.png`。
- 註:先前「選單頂部糊」實為**截圖時機太早**(title 動畫轉場中);settle 後完美。

**A regime**(320/14px/2 列距)保留於 git 歷史 `ddca555`,可復原。

**深度驗證(2026-06-04,xdotool + self-test)**:
- ✅ **H1 訊息區**(`screenMessageN`/`cjkBlit`)在 640 正確:self-test 渲染「一位迷人的吟遊詩人。」1 行 + 「馬精西亞城/為其驕傲/所毀。」行距乾淨(`docs/screenshots/14_bfull_msgarea_640.png`)。
- ✅ **2x 美術對 cinematic 場景絕佳**:intro 月之門故事場景全 640×400 細緻渲染(`docs/screenshots/13_bfull_story_2x.png`)。
- 🟠 **新發現:intro 故事文字 `showText` 未 hook**(英文)—— 另一文字路徑(不同於 textAt/screenMessageN),與標題動畫同屬 intro 子系統,follow-up。
- 標題動畫 2x 嘗試兩種 approach(2x 元素系統 / 排除 BKGD_INTRO + drawTitle 2x-blit)皆因 **BKGD_INTRO 雙重用途(背景 + 元素源)+ uint8 plot 座標 + SIGNATURE 漸層**糾纏,已還原;屬獨立深度子任務。

**vendor / 戰鬥 驗證 + 修(2026-06-04)**:
- 追路徑:vendor `>>` → `script_boron.cpp:cf_screenMessage` → `screenMessage()`(經 H1 hook);**但 Boron `construct` 在 screenMessage 前已代入佔位符 `@ % $`** → en lookup 不命中 → vendor 多數英文。
- **戰鬥 ✅**:`screenMessage(fmt,args)` 字面 → **format-aware hook 命中**(已翻)。
- **vendor 修 = module 層中文化**:`tools/patch_vendor_boron.py` 把 `vendors.b` 的 en 模板就地換 zh(佔位符保留;`@ % $` ASCII <0x80 不撞 UTF-8)→ construct 填入 zh 模板 → screenMessage 收 zh → CJK 渲染。**295/300 字串替換,模組打包 + 開機正常**。整合進 `apply_cht.sh [4/4]`。
- ⚠️ vendor 實機(進城商店)截圖驗證待補(headless 難達);機制與已運作的訊息路徑相同。

---

### 10j. 字形切換功能(2026-06-04)

- 三套 CJK atlas:Noto Sans CJK TC(預設)/ Firefly 文鼎PL細上海宋(明體)/ Firefly 文鼎PL中楷(楷體)。
- `cht.cpp` 依 env `U4CHT_FONT`(firefly/sung/kai)選 `cjk_font_<name>.bin`,預設 Noto。
- Firefly = study-area firefly-font(AR PL Big5);`apt-get download` + `dpkg -x` 取 ttf,`build_cjk_font.py` 烘 atlas。
- 對比 `docs/screenshots/18_font_switch.png`(黑體/明體/楷體三style)。三套 ship 於 `assets/`,`apply_cht.sh` 全 cp。
- 後續可加 in-game 設定選單切換(目前 env)。

---

## 11. 風險與待決 (RAID)

| # | 風險/待決 | 等級 | 處置 |
|---|---|---|---|
| R1 | **基礎選錯**:CLAUDE.md 假設 u4remastered 可 SDL2 化,實測為死巷 | 🔴 | 本計畫改走 xu4,§12 待使用者確認 |
| R2 | xu4 文字外部化程度 / hook 點數量未實測 | 🟠 | P3 盤點;以 U6 八 hook 為心理預期 |
| R3 | 中文字型塞進 xu4 UI 行高 | 🟡 | P2 PoC 先驗證 |
| R4 | PC 版 U4 原始資料檔取得 | 🟡 | P0 確認;GOG/免費釋出版 |
| R5 | xu4 vs ScummVM-Ultima4 選型 | 🟡 | 預設 standalone xu4(較輕);ScummVM 為備案 |
| D1 | 字型最終選用(預設 UMing 12px) | 待確認 | 預設先行 |
| D2 | 譯名體系沿用聖者之書(同 U6) | 建議採納 | 與 U6-cht glossary 對齊 |

---

## 12. 立即下一步(含決策點)

1. **★ 決策確認(P0)— ✅ 已拍板(2026-06-04)**:使用者確認**放棄 u4remastered 作引擎基礎,改用 xu4**;後端採 Allegro 5(D3-a)。
2. **P1 引擎建置 — ✅ 已完成(2026-06-04)**:`Dockerfile.zh` build 成功,xu4 vDR-1.0 + 完整資料模組就位(見 §10a)。
3. **P2 引擎/字型驗證 — ✅ 已完成(2026-06-04)**:headless 截圖 loop 成立(截到標題畫面,見 §10b);文字架構盤點 + 字型可行性定讞(§9)。
4. **P3 文字 hook 盤點 — ✅ 已完成(2026-06-04)**:`docs/P3-hooks.md`。核心:**H1 `screenMessageN` 是遊戲內所有捲動文字(含 NPC 對話)的單一中央漏斗(417 個 `screenMessage` call site 匯入)**,對應 U6 `MsgScroll` hook。
5. **P4 資料面 — 🔵 進行中(2026-06-04)**:純資料抽取,**不改引擎**。
   - (a) `.TLK` 256 NPC 對話 → 雙語表(§10c)。
   - (b) `u4read_stringtable` 114 字串(intro/codex/endgame/shrine)→ `dumps/stringtable_bilingual.json`(§10d)。
   - (c) 硬編 `screenMessage` 字面 420 site / 318 唯一 → `dumps/hardcoded_strings.json`(§10d)。
   - (d) vendor Boron 腳本 `vendors.b` 278 唯一字串 → `dumps/vendor_bilingual.json`(§10d)。
   - **資料面四源齊備**;下一步進字型 / 翻譯 / 接 hook(才動引擎)。
6. 保留 `u4remastered/src/talk/talk.json` 作為翻譯底本與 oracle。
7. **git repo — ✅ 本地已 init(2026-06-04)**:納管 PLAN/SETUP/docker/docs/tools/dumps;上游 `xu4/`、`u4remastered/`、原始資料 `data/` 由 `.gitignore` 排除。**push 遠端待使用者確認**。

---

## 附錄:資料來源

- `MagerValp/u4remastered`(C64,Apache 2.0): https://github.com/MagerValp/u4remastered
- MagerValp 改版說明: http://magervalp.github.io/2015/03/30/u4-remastered.html
- `xu4-engine/u4`(Allegro 5 / GLFW 跨平台 C++): https://github.com/xu4-engine/u4
- xu4 官網: https://xu4.sourceforge.net/
- xu4 德文在地化: https://ultima4.ultimacodex.com/xu4-ultima-iv-recreated-in-german/
- 本機證據:`u4remastered/`(src 23,101 行 `.s`、`talk/talk.json`、`tools/gen_talk.py`)
- 風格參考:`u3-cht/PLAN.md`、`u6-cht/README.md`

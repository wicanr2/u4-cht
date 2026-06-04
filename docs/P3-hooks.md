# P3 — xu4 文字輸出 hook 盤點(中文化 backlog)

> 盤點日:2026-06-04 ・ 對象:`xu4-engine/u4`(vDR-1.0)・ 方法:grep + 讀 `src/screen.cpp`、`discourse*.cpp`、`gui.cpp`、`intro.cpp`
> 目的:定位所有文字輸出 codepath 與字串來源,產出 P4(字型 + 翻譯)可執行的 hook backlog。
> 策略對齊 U6-cht「Plan B(load-time 替換)」:**英文照常解析,輸出前查表換中文**,在中央漏斗 hook。

---

## 1. 文字架構總覽

xu4 有**兩條獨立文字管線**:

```
A. 遊戲內文字(原版 CHARSET 點陣字,逐 byte 索引)──── 中文化主戰場
   screenMessage(fmt,…)  ─┐                          (417 call sites)
   screenMessageCenter ───┼─→ screenMessageN(buf,len) ─→ screenShowChar(byte,col,line) ─→ BKGD_CHARSET
   discourse 對話 reply ──┘        ↑ 換行/tokenize          ↑ glyph blit(最底層 chokepoint)
   screenTextAt(x,y,…) ──────────────────────────────────→ screenShowChar  (HUD/狀態列,12 sites)

B. GUI / 選單 / 遊戲瀏覽器(.txf SDF 紋理字,uint16 碼位)──── 次要
   gamebrowser / gui widget ─→ gui_emitText ─→ txf_genText(逐 byte,不解 UTF-8)─→ cfont-*.txf + cfont.png
```

---

## 2. Hook 點清單(依優先序)

| # | Hook 點 | 檔案:行 | call sites | 角色 | 中文化動作 |
|---|---|---|---|---|---|
| H1 | `screenMessageN(const char* buf, int len)` | `src/screen.cpp:449` | 中央漏斗 | **所有捲動訊息**(NPC 對話 + 系統訊息)最終都經此 | ✦ **主 hook**:進入時 en→中文 查表;tokenize/wrap 改 CJK-aware |
| H2 | `screenShowChar(int chr, int x, int y)` | `src/screen.cpp:959` | 5(+H1/H3 內部) | glyph 最底層 blit,索引 CHARSET 一格 | ✦ 擴成可繪 CJK glyph(多格/全形寬,從 CJK 字庫) |
| H3 | `screenTextAt(int x,int y,fmt,…)` | `src/screen.cpp:353` | 12 | 定位 HUD 文字(狀態列、提示) | 同 H1 查表 + 經 H2 CJK 繪製 |
| H4 | `screenMessage(fmt,…)` | `src/screen.cpp:399` | **417** | 格式化入口(vsnprintf → H1) | 不直接 hook;字串來源見 §3 |
| H5 | `screenMessageCenter` | `src/screen.cpp:419` | 2 | 置中首行 → H1 | 隨 H1 |
| H6 | `gui_emitText` / `txf_genText` | `src/gui.cpp:61` / `src/support/txf_draw.c:165` | GUI | 紋理字繪製,逐 byte | UTF-8 解碼 patch(`txf_genText`)+ CJK SDF atlas |
| H7 | `MenuArea::textAt / textAtKey` | `src/intro.cpp:788`… | intro 選單 | 主選單/角色創建文字(走 CHARSET) | 同 H1/H2 |
| H8 | `showText` / intro 故事 | `src/intro.cpp:964` | intro | 開場故事字幕 | 同 H1/H2;字串來源見 §3 |

> **關鍵收斂**:H1 `screenMessageN` 是遊戲內所有捲動文字(含 NPC 對話)的單一出口 —— 對應 U6 的 `MsgScroll::display_string` 中央 hook。攻下 H1 + H2 即覆蓋遊戲主文字面。

---

## 3. 翻譯字串來源(抽取清單)

| 來源 | 位置 / 機制 | 內容 | 抽取/翻譯方式 |
|---|---|---|---|
| **NPC 對話** | U4 `.TLK` 檔(`DISCOURSE_U4_TLK`,每城 16 段,載入 `U4Talk` struct,`discourse_tlk.cpp:403`) | 全部 NPC 問答 | 抽 .tlk → 對齊 **`u4remastered/talk/talk.json`**(乾淨 256-NPC 字料)當雙語底本 |
| **開場故事 / 標題** | `u4read_stringtable`(`intro.cpp:102`)→ AVATAR.EXE string table | intro 字幕、職業選擇旁白 | 抽 stringtable → 雙語表 |
| **城堡/Lord British** | `discourse_castle.cpp`(`messageParts`,`"He says: "` 等) | 城堡對話 + 硬編前綴 | 對話走資料;前綴屬硬編字串 |
| **硬編 UI/系統字串** | **417 個 `screenMessage("…")` 字面** + intro 選單字面(`"Journey Onward"`/`"Initiate New Game"`/`"By what name shalt thou be known"`)+ discourse 字面(`"Yes or no!"`) | 指令回饋、戰鬥、選單 | grep 全抽成 string table;H1 查表時命中 |
| **GUI 瀏覽器** | `gamebrowser.cpp` 模組名/about | 模組選單 | txf 路徑(H6) |

---

## 4. P4 執行 backlog(依賴序)

1. **抽字串**:
   - (a) ✅ **已完成**:`tools/extract_tlk.py` 抽 16 個 DOS `.TLK`(256 NPC 對話)→ 對齊 `talk.json` → 雙語表 `dumps/talk_bilingual.json` + 對齊報告 `dumps/talk_alignment_report.md`(見 §6)。
   - (b) 待做:`u4read_stringtable`(intro/故事/vendor)→ en 字串集。
   - (c) 待做:grep 抽 417 `screenMessage` 字面 + 選單/discourse 字面 → 硬編 string table。
2. **lookup 格式**:binary length-prefixed(byte-safe,避 U6 的 0x5C trail 坑);en 一律從 source 抽取,禁手打(U6 坑 #9)。
3. **CJK 字庫**(二選一或併用):
   - CHARSET 路徑:用 Noto/UMing 烘 CJK 點陣字庫,改 `screenShowChar`(H2)支援全形/多格 + `screenMessageN`(H1)tokenizer 把每個 CJK 字當獨立 token(U6 坑 #3)、調行高(U6 坑 #4)。
   - txf 路徑:`msdf-atlas-gen` 烘 CJK 子集 SDF atlas + `txf_genText`(H6)UTF-8 解碼 patch。
4. **接 H1 hook**:`screenMessageN` 進入時查表;miss 時 fragment 替換(runtime 變數如角色名,U6 坑 #11)。
5. **驗證**:headless 截圖 loop(`docker/Dockerfile.test`)逐畫面比對;對話/選單/HUD/戰鬥四面各取樣。

---

## 5. 與 U6-cht 對照(可複用經驗)

| U6-cht | xu4 對應 | 備註 |
|---|---|---|
| `MsgScroll::display_string` 中央 hook | **H1 `screenMessageN`** | 單一漏斗,策略直接套用 |
| `U6Font` 8×8 bitmap | CHARSET + H2 `screenShowChar` | 同型:點陣、逐 byte、需多格 CJK |
| binary v3 lookup(0x5C trail 坑) | P4 step 2 | 直接沿用格式 |
| tokenizer 把 Big5 lead pair 當 token(坑 #3) | H1 tokenizer 改 CJK-aware | U4 文字框更窄,行寬更需注意 |
| 8 個 engine hook | H1–H8(本表) | 數量相近 |

---

## 6. P4(a) .TLK 抽取結果(2026-06-04)

`tools/extract_tlk.py`(不改引擎,純資料抽取,依 `discourse_tlk.cpp` U4Talk_load 格式):

| 項目 | 數字 |
|---|---|
| DOS `.TLK` 檔(`ultima4.zip`) | 16(BRITAIN/COVE/DEN/EMPATH/JHELOM/LCB/LYCAEUM/MAGINCIA/MINOC/MOONGLOW/PAWS/SERPENT/SKARA/TRINSIC/VESPER/YEW) |
| 抽出 NPC 對話 | **256**(16 檔 × 16 record × 288 byte) |
| 以 name 對齊 `talk.json` | 250 / 256 |
| name 無對應(DOS name 欄位異常) | 6 — 疑似 remaster 修過的 broken dialogue(Serpent's Hold 門衛、Yew 乞丐等),報告列出供人工核對 |
| 英文內容有差異 | 188 — 多為 remaster 修對白 + DOS keyword **4 字截斷**(`DANC`/`COMP`)+ 換行格式 |

**產出**:
- `dumps/talk_bilingual.json`:雙語表雛形,每 NPC × 12 欄 `{en, zh}`(en = DOS `.TLK` 原文 = H1 hook 的 lookup key;description 已套 `U4Talk_load` 執行時修飾使 en 等於引擎輸出;zh 待填;keyword/topic 預設不譯)。
- `dumps/talk_alignment_report.md`:對齊摘要 + 無對應清單 + 英文差異明細。

**翻譯原則**:以 **DOS `.TLK` 的 en 為翻譯 key**(引擎實際輸出);`talk.json` 作乾淨參考(校對、補 remaster 修正)。**raw `.TLK` / zip 不入庫**(`/data/`,Origin © 1985),由 `make download` 重建。

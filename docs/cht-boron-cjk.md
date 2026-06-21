# Boron 模組 × CJK 渲染:商店亂碼 / 位移 / 缺字灰框 與翻譯涵蓋缺口

> 2026-06 實機測試商店買賣時發現一連串 CJK 顯示問題,逐一追到根因並修復。
> 本文記錄機制與修法,供日後維護與「補譯」工作參考。

相關檔案:
- 引擎:`xu4/src/script_boron.cpp`(`cf_screenMessage`)、`xu4/src/screen.cpp`(CJK 渲染)
- 模組:`xu4/module/Ultima-IV/vendors.b`
- 工具:`tools/patch_vendor_boron.py`、`tools/test_boron_cjk.cpp`(回歸測試)
- patch:`patches/engine/cht-engine.patch`(含 `cf_screenMessage` hunk)

---

## 背景:vendor 文字為何走「不同的路」

非 vendor 的玩家文字(NPC 對話、系統訊息、硬編字串)都是**英文進 C → `chtLookup` 查表 → 中文出**,翻譯與輸出全在 C 端,由 `chtSelfTest` 涵蓋。

vendor(商店)不同:中文**住在 Boron 模組** `vendors.b` 裡,經
`>>` / `=>` / `input-shop` → `construct`(代入佔位符)→ `script_boron.cpp:cf_screenMessage`
→ `screenMessage()` → `screenMessageN` → CJK 渲染。

這條「Boron 模組內 CJK → C」的路徑是 vendor 獨有,**沒有任何既有自測涵蓋**,因此一連串 bug 直到實機才現形。

---

## Bug 1:整段亂碼 + 一堆空白(UCS2 被當 UTF-8)

**症狀**:店家對白是亂碼夾雜大量空白;但按 Y/Enter 仍能買到 → 純顯示問題。

**根因**:Boron 把含 CJK(codepoint 256–65535)的字串字面存成 **UR_ENC_UCS2**
(每字 16-bit;見 Boron `ur_strInitUtf8`:≤255→Latin1、256–65535→**UCS2**、>65535→UTF-8)。
`construct` 又沿用輸入編碼。修復前 `cf_screenMessage` 直接把 buffer 的 `ptr.c` 當 UTF-8
byte 字串輸出:

```c
screenMessage(si.buf->ptr.c + si.it);   // ← UCS2 被當 UTF-8 byte 讀
```

UCS2 當 byte 讀:ASCII/空白/`^/`(如 `0x0A 0x00`)高位 0x00 → C 字串被 NUL 截斷(空白);
CJK 低位 byte → 壞 UTF-8(亂碼)。

**修法**:依 `buf->form` **自行逐 codepoint 編 UTF-8**(`chtAppendUtf8`),再
`screenMessage("%s", utf)`("%s" 防文字內 `%` 被當 printf 格式)。

> ⚠️ **不要用 `ur_toText` 寫進 UR_ENC_UTF8 buffer**(本檔 `script_reportError` 的範式)。
> 實測它按「字數」而非 UTF-8 byte 數配置容量,CJK(3 byte/字)會 **heap 溢位**
> (`corrupted size vs. prev_size`)。逐 codepoint 自編可完全繞開。

---

## Bug 2:武器/醫療/材料店「整段右移」

**症狀**:某些店進場對白整段往右位移、換行錯亂;food / inn 卻正常。

**根因**:原始英文用 `{{ 多行縮排 }}` 雙括號字串,每行有 12 格**原始碼縮排空白**。
抽取→翻譯→回填時這些空白被當成內容保留(`vendor_bilingual.json` 的 en、zh 都含)。
文字區只有 `TEXT_AREA_W = 16` 欄、`CHAR_WIDTH = 24`,12 格空白吃掉 12 欄 → 嚴重右移。
food / inn 因翻成沒縮排的單行字串而正常。

**修法**:去掉每行(`^/` 之後)的前導空白/tab → 全部靠左對齊(同 food/inn 風格)。
見 `patch_vendor_boron.py` 的 `re.sub(r"\^/[ \t]+", "^/", text)`。

---

## Bug 3:買賣物品清單「B/C/D 後面是灰白色方塊」

**症狀**:買單列出 `B`、`C`、`D` 選擇鍵正常,但其後的中文物品名是灰白色方塊。

**根因**:`vendors.b` 的 `inventory: ""` 是**空 Latin1 字串**。`build-items` 用
`append inventory rejoin [uppercase key ' ' name '^/']` 組清單:

- `append` 把 CJK 物品名塞進 Latin1 buffer 時,Boron **有損降轉**:每個中文字變 `0x BF`(¿)。
- `rejoin` 以 char(`uppercase key`)起頭也會先成 Latin1 buffer,隨後 `name` 一樣降轉。

`0xBF` 不在 CJK 字型 atlas → `cjkBlitPx` 畫灰框(`fillRect 60,60,60`)= 灰白色方塊。
(`B/C/D` 是 ASCII 所以正常。)

> 對照:`>> rejoin ["^/汝只買得起 " <數> " 份。^/"]`(L583/L652)以 **CJK 字串起頭**,
> 整個 rejoin buffer 即為 UCS2,故安全。問題只在「以 char/空字串起頭」的情形。

**修法**(`patch_vendor_boron.py`):
1. `inventory: ""` → `inventory: "　"`:種一個全形空白(U+3000)使 buffer 為 **UCS2**
   (`build-items` 會先 `clear`,種子不顯示;`clear` 保留 buffer 編碼)。
2. 把 `rejoin` 拆成逐段 `append`,讓 `name`(CJK 字串)直接 append 到已是 UCS2 的
   `inventory`,不經 rejoin 的 Latin1 中間 buffer。

實測(`tools/test_boron_cjk.cpp` 同手法):seed UCS2 + 逐段 append 字串 → `form=2`、codepoint 正確。

---

## 回歸測試

`tools/test_boron_cjk.cpp` 在**真實 Boron 直譯器**裡重現 vendor 情境(字面 / construct 價格 /
construct 多佔位店名店主 / 行首換行),用與修復後 `cf_screenMessage` 相同的轉碼比對 UTF-8,
並斷言來源確為 UCS2(證明舊路徑必壞)。執行:

```sh
bash tools/run_boron_cjk_test.sh     # 於 u4cht/xu4-allegro image 內編譯+執行
```

這補上 `chtSelfTest` 的盲區(它走 `chtLookup`,不走 Boron 字串路徑)。

---

## 原則:輸入比對只能用英文,顯示才在地化

**玩家無法在遊戲中輸入中文**(沒有 IME)。因此凡是會被拿去**跟玩家輸入比對**的字串,
其 canonical 值**必須維持英文**;翻譯只能用於「顯示」。

### 為何重要(實際踩到的 bug)

`getVirtueName()` 原本被 `CHT()` 包成中文。但它同時用於:
- **輸入比對**:聖壇冥想 `shrine.cpp` `strncasecmp(input, getVirtueName(virtue), 6)`、
  codex `codex.cpp`、城堡 `discourse_castle.cpp` `inputEq(...)`、`item.cpp`。
  → 玩家打 `justice`,卻和中文「正義」比對,**永遠失敗**(功能性 bug,不只顯示)。
- **位元組操作**:stats 面板 `stats.cpp` 取 `getVirtueName(...)[0]` 當縮寫首字母。
  → 中文 UTF-8 的 `[0]` 是半個位元組 → 亂碼。

### 解法(範式)

把「canonical 名」與「顯示名」分開:

| 函式 | 回傳 | 用途 |
|---|---|---|
| `getVirtueName(v)` | **英文** canonical(`"Justice"`) | 輸入比對、`[0]` 首字母、`strlen` |
| `getDisplayVirtueName(v)` | **中文(英文)**(`"正義(Justice)"`) | 顯示;讓玩家知道要輸入的英文 |

- 比對端用 `getVirtueName`(英文)→ 自動正確。
- 顯示端用 `getDisplayVirtueName` → 玩家看到「正義(Justice)」,知道聖壇要打 `Justice`。
  (括號用 **ASCII `()`**:`<0x80` 走 ASCII 字模,免進 atlas。)
- **fail-safe**:canonical 維持英文,將來新程式忘了在地化只會「顯示英文」,
  不會默默壞掉比對邏輯(比反過來安全)。

> **同類檢查結果**:`getClassName()`(職業名,也被 `CHT()` 包成中文)經查**只用於顯示**
> (`stats.cpp` 面板、`game.cpp`「A %s may NOT use…」),無輸入比對 / `[0]` / `strlen`,
> 故維持中文**安全**,不需拆分。talk 關鍵字本就維持英文、`(可問 %s)` 提示也是英文 → OK。

## 翻譯涵蓋缺口

四大來源(對話 256 / stringtable 114 / 硬編 318 / vendor 278,約 859 entry)已全譯。
但 `extract_hardcoded.py` **只抓 `screenMessage*()` 呼叫點**的字面,漏掉了兩類,
已於本輪補上:

### (a) 變數賦值 / 陣列初始化的硬編字串 ✅ 已補

這些檔皆透過 `screenMessage`(→ `screenMessageN` 自動 `chtLookup`)或自帶 hook 顯示,
只差字串沒進翻譯表:

| 檔案 | 內容 | 數 | 處置 |
|---|---|---|---|
| `discourse_castle.cpp` | Lord British 對白 / `help` 漸進指引 | 9 | 譯入 `castle_bilingual.json` |
| `death.cpp` | 死亡 / 復活(`deathMsgs[]` 陣列) | 7 | 譯入 `hardcoded_strings.json` |
| `shrine.cpp` | 聖壇靈視 | 1 | 譯入 `hardcoded_strings.json` |
| `codex.cpp` | 深淵(Abyss)結局問答 | — | **本來就已譯**(先前廣掃的 `\n` 比對誤報) |
| `item.cpp` / `intro.cpp` | — | — | **本來就已譯**(同上誤報) |

> 註:`discourse_castle.cpp` 的 Lord British 指引是 C 多行字面**串接成一整串**後
> 才 `chtLookup(text, …)`,故翻譯表的 key 必須是**完整串接後**的英文(非個別片段)。

例:王城問 Lord British `help` → `"Travel not the open lands alone..."` 現已中文。

### (b) NPC 名稱(`DS_NAME`)未查表 ✅ 已修

`discourse_tlk.cpp` 原 `case DS_NAME: return USTR(name);` **沒有 `chtLookup`**
(對比同檔 `DS_LOOK` 有 hook、`DS_PRONOUN` 有 He/She/It→他/她/它)。
故問 NPC 名字時:`message("%s says: I am %s\n", pronoun, name)` 的格式雖譯成
「我是 %s」,`name`(如 `a guard`)卻原樣輸出 → **「我是 a guard」**。

**譯名其實早已備妥**:`talk_bilingual.json` 的 `name` 欄已含 zh(`a guard`→`衛兵`、
`Iolo`→`尤洛`…),且 `build_lookup.py` 已把 name 欄收進 `u4_cht.tab`。缺的只是
`DS_NAME` 沒查表。修法:給 `DS_NAME` 加 `chtLookup` hook(同 `DS_LOOK`)即可,免新譯。
(格式為「我是 %s」會留一個半形空格 →「我是 衛兵」,可接受。)

### (c) 顯示路徑未接 chtLookup ✅ 已修

譯文**早已存在**(在 talk/maps 表),但特定顯示路徑沒查表:

| 症狀 | 根因 | 修法 |
|---|---|---|
| 問 NPC 名「我是 a guard」 | `discourse_tlk.cpp` `DS_NAME` 回傳原字串(它在「我是 %s」中是 %s 引數,不被 screenMessageN 查表) | `DS_NAME` 加 chtLookup |
| NPC yes/no 提問顯示英文(如 EMPATH「Hast thou solved the altars?」、LCB「Art thou the most valiant warrior?」) | 同上,`DS_QUESTION` 是「\n%s\n\nYou say: 」的 %s 引數,未查表 | `DS_QUESTION` 加 chtLookup(譯文在 talk_bilingual 的 question 欄) |
| 戰鬥中怪物名英文(Flees!/Divides!/Killed! 等) | `creature.cpp` 這幾處用 `CSTR(name)` 繞過已有 hook 的 `getName()` | 改用 `getName()` |
| 進城地名英文且偏移(Empath Abbey…) | `portal.cpp` `screenMessageCenter(city->getName())`:地名非獨立 key + 置中先補前導空白破壞查表 + 以 byte 長置中(CJK 偏移) | `screenMessageCenter` 先 chtLookup、再依「顯示格數」(CJK 算 1 格)置中;地名建表(見下) |

### (d) maps.b module 資料 ✅ 已補

`vendors.b` 以外的 module 字串(`maps.b` 的樓層/地城 portal 訊息 + 城市/地城名)未處理。
這些經 `screenMessage`→`screenMessageN`→`chtLookup`(或置中路徑)顯示,故**進表即可**,
不必 patch maps.b。新增 `dumps/maps_bilingual.json`(11 訊息 + 24 地名),接進
`build_lookup.py` 與 `build_cjk_font.py`。地名譯名依 `docs/glossary-u4.md`
(Britain→不列顛城、Jhelom→哲倫、Yew→紫衫城、Empath Abbey→共感修道院、Lycaeum→學院…)。

> 殘留小缺口:`portal.cpp` SHRINE 分支 `"Enter the %s!"` 以美德名當 %s 引數,未查表
> (聖壇進入,玩家較少觸發;美德名已在 names 表,待補 hook)。

### 字型 atlas

各輪新譯文(castle 5 字 + maps 3 字…)會引入新 CJK 字,須重建 3 套 atlas
(`tools/build_cjk_font.py`,字源 json 已含 castle/hardcoded/maps)。**新增字後須刪 `.bin` 重建**。

**收字門檻 bug(已修)**:`build_cjk_font.py` 原本只收 `codepoint ≥ 0x3000` 的字,
但引擎 `screenMessageCJK` 對**所有 ≥ 0x80** 的 codepoint 都走 `cjkBlit`(查 atlas)。
於是 0x80–0x2FFF 範圍的標點只要被用到就顯示灰框 —— 主要是 `…`(U+2026,**用了 152 次**,
如 Yew 德魯依對 `beh` 的回應「貝……貝……」)、`—`(U+2014)、`·`(U+00B7)、`‧`(U+2027)。
已把門檻改為 `≥ 0x80`(對齊引擎 `chtHasCJK`)。目前 2023 glyph。

### 非玩家面(不需譯)

CLI `--help`、`gpu_opengl` shader 編譯錯誤、debug 訊息等掃描到的英文字面屬此類,略過。

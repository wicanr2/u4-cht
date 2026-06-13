# Ultima IV: Quest of the Avatar — 繁體中文版

> 沒有要打倒的大魔王。沒有公主要救。
> 1985 年,Richard Garriott 問了一個別的遊戲不敢問的問題:**你願不願意,成為一個有德之人?**
>
> 這是 *Ultima IV: Quest of the Avatar* —— 電玩史上第一款把「道德」做成核心機制的 RPG。
> 本專案以開源引擎 **[xu4](https://github.com/xu4-engine/u4)** 為基礎,把這款四十年的經典**完整繁體中文化**,
> 跨平台(Linux / Windows)、640×400 全美術重繪、**遊戲中一鍵切換 EGA / VGA 美術**。

![title](docs/screenshots/17_bfull_title_fixed.png)
*Lord British 與 Origin Systems 呈獻 ——「Ultima IV:聖者的追尋」。標題動畫、雙龍、Britannia 地圖,逐幀重現於 640×400。*

---

<a name="gallery"></a>
## 🖼️ 走進不列顛尼亞

> 一個午後,你在自家後院的森林裡迷了路。林間一輛吉普賽篷車,一位老婦人以塔羅牌測你的心性 ——
> 你最契合哪一種美德?於是,旅程開始了。

| 吉普賽人的牌局 —— 你的道路由八張牌決定 | 開場:柳樹下的史書 |
|---|---|
| ![charcreate](docs/screenshots/12_bfull_charcreate.png) | ![story](docs/screenshots/13_bfull_story_2x.png) |
| *「且思量此事⋯⋯」誠實?慈悲?犧牲?七道問題,定下你的職業與初心。* | *月之門開啟前,你倚在溪畔柳樹下,翻開《不列顛尼亞之史》。全文白並用的譯筆。* |

| 主選單 —— 純粹的中文 | 啟程:Britannia 世界地圖 |
|---|---|
| ![menu](docs/screenshots/10_bfull_menu.png) | ![map](docs/screenshots/19_gameplay_s2.png) |
| *返回畫面 / 啟程冒險 / 開始新遊戲 / 設定 / 關於 —— 每字一格,乾淨俐落。* | *水波、森林、城堡、隨風而行的你。HUD、風向、訊息欄,全部說中文。* |

> 以上皆為 Docker headless(Allegro 5 + Mesa 軟體 GL)實機渲染截圖,非合成。

---

<a name="lordbritish"></a>
## 🗣️ 謁見不列顛王

走進城堡、登上二樓,向 **Lord British** 詢問世間種種 —— 八德的真義、聖壇所在、冥河大深淵與典籍密室、三位大邪君的下場。整段對白(載自原版 `avatar.exe`)逐句中文化,連初見時喚你之名的問候都不放過。

| 初見:王起身相迎 | 詢問「冥河大深淵」 | 詢問「蒙丹」 |
|---|---|---|
| ![lbgreet](docs/screenshots/23_lb_greet.png) | ![lbabyss](docs/screenshots/24_lb_abyss.png) | ![lbmondain](docs/screenshots/25_lb_mondain.png) |
| *「不列顛王起身說道:汝終於來了!Avatar,吾等已等候許久,許久……」名字即時帶入。* | *「乃典籍密室之所在!……方能入此密室,譬如聖者!!!」深淵與典籍兩段,忠實分頁。* | *「他說道:蒙丹已亡!」三大邪君,各有交代。* |

> 實機驗證:`goto` 不列顛城堡 → 二樓 Klimb → 謁見 Lord British,逐 keyword 截圖。LB 座標由原版 `LCB_2.ULT` 解出。

---

<a name="art"></a>
## 🎨 兩個時代的美術,一鍵之間 —— `F2`

Ultima IV 當年有 EGA(16 色)與後來社群重製的 VGA(256 色)兩套美術。本專案讓你**在遊戲進行中按 `F2` 即時切換**,同一局、同一個位置,瞬間換皮 —— 隊伍、進度、座標分毫不動。

| EGA — 1985 年的原味 | VGA — 256 色的華麗 |
|---|---|
| ![ega](docs/screenshots/22_f2_ega.png) | ![vga](docs/screenshots/21_f2_vga.png) |
| *扁平俐落的 16 色像素,經典 DOS 風味。* | *漸層水波、立體樹叢、精細怪物 —— 訊息欄記下「圖形:VGA」。* |

而那 256 個 tile —— 地形、城堡、Avatar、各路怪物、Britannia 符文字母 —— 兩套全貌並陳:

| EGA tileset(256 tile) | VGA tileset(256 tile) |
|---|---|
| ![tega](docs/sprites/tileset_ega.png) | ![tvga](docs/sprites/tileset_vga.png) |

*獸人、蝙蝠、巨蛇、飛龍、骷髏、石像鬼、漂浮的眼魔⋯⋯ 從 ankh 聖符記到月相,1983 的想像力盡在其中。(由原版 `SHAPES.EGA` / `shapes.vga` 解碼渲染,工具見 [`tools/render_tilesheet.py`](tools/render_tilesheet.py)。)*

> 另有 **`F3` 切換解析度**(tile 物理放大)與 **三套中文字形**(Noto 黑體 / Firefly 宋體 / Kai 楷體)。見 [遊戲中熱鍵](#hotkeys)。

---

## 目錄

1. [走進不列顛尼亞(畫廊)](#gallery)
2. [謁見不列顛王](#lordbritish)
3. [兩個時代的美術 F2](#art)
4. [這是什麼](#這是什麼)
5. [為何選 xu4(而非 u4remastered)](#為何選-xu4)
6. [八德 — Avatar 之道的起點](#八德)
7. [遊戲中熱鍵](#hotkeys)
8. [快速開始](#快速開始)
9. [目前進度](#目前進度)
10. [技術架構](#技術架構)
11. [資料抽取成果](#資料抽取成果)
12. [Roadmap](#roadmap)
13. [License & Credits](#credits)

---

<a name="這是什麼"></a>
## 🏰 這是什麼

**Ultima IV** 是電玩史上第一款以「**成為道德的化身(Avatar)**」為核心的 RPG —— 沒有大魔王,目標是在真理、愛、勇氣三原則下修練八大美德,走遍八座聖壇,成為 Avatar。

本專案把這款 1985 年的經典,以維護中的開源引擎 **[xu4](https://github.com/xu4-engine/u4)**(Allegro 5 / GLFW 跨平台 C++)為基礎,進行**完整繁體中文化**:跨平台(Linux / Windows)、Docker 全程建置、文字以 load-time 查表替換(對齊 [u6-cht](https://github.com/wicanr2/u6-cht) 的成功經驗)。

> 目前狀態:**可玩**。標題 / 選單 / 角色創建 / intro 故事 / NPC 對話 / 系統訊息 / vendor 商店全部中文,640×400 全美術 2x、CJK 一格一字;遊戲中 `F2` 切 EGA/VGA、`F3` 切解析度;Linux AppImage 與 Windows zip 皆已打包(含全部 DLL、遊戲資料、三套字形)。

---

<a name="為何選-xu4"></a>
## 🧭 為何選 xu4(而非 u4remastered)

本專案最初評估 `MagerValp/u4remastered`,結論是**不適合**:

| | `u4remastered` | **`xu4`(採用)** |
|---|---|---|
| 技術 | **C64 6502 組合語言**(23,101 行 `.s`) | C++ + **Allegro 5 / GLFW** |
| 平台 | 僅 Commodore 64 / VICE | **Linux / Windows / Mac** 原生 |
| 文字編碼 | 單位元組、8×8 charset、**每行 16 字**死巷 | CHARSET + `.txf`(uint16 碼位) |
| 中文化 | 需從零重寫整個引擎 | hook 中央文字漏斗即可 |

`u4remastered` 並未浪費:它的 `src/talk/talk.json`(修過數十個對白 bug 的乾淨 256-NPC 字料)被用作**翻譯底本與對齊 oracle**。完整評估見 [`PLAN.md`](PLAN.md)。

---

<a name="八德"></a>
## 🔮 八德 — Avatar 之道的起點

U4 是「八德系統」的起源。Garriott 把所有德目歸納到三個底層原則 **Truth / Love / Courage**,八大美德是三者的**全部組合**(2³ = 8):

| 美德 | 中文 | 構成 | 真言 | 城市 | 職業 |
|---|---|---|---|---|---|
| Honesty | 誠實 | Truth | **ahm** | 月光城 Moonglow | 法師 |
| Compassion | 慈悲 | Love | **mu** | 不列顛城 Britain | 吟遊詩人 |
| Valor | 勇敢 | Courage | **ra** | 哲倫 Jhelom | 戰士 |
| Justice | 正義 | Truth+Love | **beh** | 紫衫城 Yew | 德魯依 |
| Sacrifice | 犧牲 | Love+Courage | **cah** | 米諾克 Minoc | 技工 |
| Honor | 榮譽 | Truth+Courage | **summ** | 特林希克 Trinsic | 聖騎士 |
| Spirituality | 靈性 | Truth+Love+Courage | **om** | 史卡拉布雷 Skara Brae | 遊俠 |
| Humility | 謙卑 | （三者皆無） | **lum** | 新馬精西亞 New Magincia | 牧人 |

> 譯名沿用台灣《創世紀聖者之書》體系,與 u6-cht 對齊。開場的 gypsy 心理測驗(已抽出 28 題)決定你最契合的美德與起始職業。

---

<a name="hotkeys"></a>
## ⌨️ 遊戲中熱鍵

| 鍵 | 作用 |
|---|---|
| **`F2`** | 即時切換 **EGA ↔ VGA** 美術(同一局,保留進度) |
| **`F3`** | 循環 **解析度 / 縮放**(tile 物理放大) |
| `U4CHT_FONT` | 環境變數切字形:`firefly`(宋)/ `kai`(楷),省略=Noto 黑體 |

> Linux:`U4CHT_FONT=firefly ./u4-cht-x86_64.AppImage`;Windows:`run.bat` 前 `set U4CHT_FONT=kai`。

---

<a name="快速開始"></a>
## ⚡ 快速開始

完整指令見 [`SETUP.md`](SETUP.md)。最小流程:

```bash
# 1. 取得 xu4 引擎(本 repo 不含上游,clone 重建)
git clone https://github.com/xu4-engine/u4.git xu4
cd xu4 && git submodule update --init --recursive && cd ..

# 2. Docker 建置(Allegro 5;make download 自動抓 freeware U4 資料)
docker build -f docker/Dockerfile.zh -t u4cht/xu4-allegro xu4

# 3. headless 截圖驗證
docker build -f docker/Dockerfile.test -t u4cht/xu4-test docker
mkdir -p /tmp/u4shot
docker run --rm -v /tmp/u4shot:/out u4cht/xu4-test 22 3   # → /tmp/u4shot/screen.png
# shot.sh 預設帶 --filter xBRZ(灰階 CJK AA 最平滑);第 3 參數可自帶 --filter 覆蓋,
# 或附加其他 xu4 args,如:... u4cht/xu4-test 22 3 "--skip-intro"
```

> 原版 U4 資料(`ultima4.zip`)為 Origin © 1985 的 **freeware**,由 `make download` 自動取得,不需手動準備、不入庫。

---

<a name="目前進度"></a>
## 📊 目前進度

| Phase | 內容 | 狀態 |
|---|---|---|
| P0 | 引擎選型決策(改用 xu4 + Allegro 5) | ✅ |
| P1 | Docker 建置 xu4(二進位 + 資料模組) | ✅ |
| P2 | headless 截圖 loop + 文字架構 / 字型可行性 | ✅ |
| P3 | 文字輸出 hook 盤點(H1–H8) | ✅ |
| P4 資料面 | `.TLK` / stringtable / 硬編 / vendor 四源抽取 | ✅ |
| P5 翻譯 | 四源全譯(talk 256 + stringtable 114 + 硬編 318 + vendor 278) | ✅ |
| P6 | CJK 字型(Noto Sans CJK TC 灰階 AA)+ 接 H1 hook | ✅ |
| P7 多面 hook | 對話 / 系統訊息 / 選單 / 角色創建 / intro 故事 hook | ✅ |
| **B 640×400** | 全美術 2x regime + CJK 1-cell(menu/prompt/訊息/故事/cinematic 全乾淨) | ✅ |
| 標題動畫 2x | AnimPlot int16 + 元素座標 2x → 標題畫面/選單完美 | ✅ |
| vendor / showText | module 層 vendor 中文化、intro 故事 hook | ✅ |
| **F2 EGA/VGA** | 遊玩中即時切換 graphics 模組(full config swap + map 堆疊 re-point) | ✅ |
| **F3 解析度** | 遊玩中循環 scale(tile 物理放大) | ✅ |
| 打包 | AppImage(靜態 runtime)+ Windows zip(全 DLL + 遊戲資料) | ✅ |

![f3](docs/screenshots/20_gameplay_f3_s3.png)
*`F3` 切換解析度:同一畫面物理放大,tile 與 HUD 一起變大、更有臨場感。*

---

<a name="技術架構"></a>
## 🔧 技術架構

xu4 有兩條文字管線(詳見 [`docs/P3-hooks.md`](docs/P3-hooks.md)):

```
A. 遊戲內文字(CHARSET 點陣,中文化主戰場)
   screenMessage ×417 ┐
   NPC 對話 / vendor ─┼─→ H1 screenMessageN ─→ H2 screenShowChar ─→ CHARSET
   screenMessageCenter┘     (換行/tokenize)       (glyph blit)

B. GUI / 選單(.txf SDF 紋理字,uint16 碼位)
   gui_emitText ─→ txf_genText ─→ cfont-*.txf
```

**關鍵收斂**:`screenMessageN` 是遊戲內所有捲動文字(含 NPC 對話)的**單一中央漏斗** —— 對應 u6-cht 的 `MsgScroll::display_string` hook。攻下 H1 + H2(CJK glyph)即覆蓋遊戲主文字面。

**字型策略**:CHARSET 路徑烘 CJK 點陣字庫 + 多格渲染;`.txf` 路徑用 `msdf-atlas-gen` 烘 CJK 子集 + UTF-8 解碼 patch。來源 TTF 用 Noto Sans CJK TC / AR PL UMing。

---

<a name="資料抽取成果"></a>
## 📦 資料抽取成果(P4 資料面)

純資料抽取,**不改引擎**;產物在 [`dumps/`](dumps/),工具在 [`tools/`](tools/):

| 來源 | 機制 | 數量 | 工具 |
|---|---|---|---|
| NPC 對話 | DOS `.TLK`(16 城)→ 對齊 talk.json | **256** NPC × 12 欄 | `extract_tlk.py` |
| intro / codex / shrine | `u4read_stringtable`(title/avatar.exe) | **114** 字串 | `extract_stringtable.py` |
| 硬編 UI / 戰鬥 | `screenMessage` 字面(靜態分析) | **318** 唯一 | `extract_hardcoded.py` |
| vendor 商店對白 | `vendors.b` Boron 腳本 | **278** 唯一 | `extract_vendor_boron.py` |

每份均為 `{en, zh}` 雙語表雛形(`en` 已填 = 引擎實際 lookup key,`zh` 待填)+ 統計/對齊報告。

---

<a name="roadmap"></a>
## 🗺️ Roadmap

**已完成**:四源全譯(talk 256 / stringtable 114 / 硬編 318 / vendor 278)→ CJK 灰階字庫(Noto / Firefly / Kai)→ H1–H8 文字 hook → 640×400 全美術 2x → 標題動畫 → `F2` EGA/VGA 即時切換 → `F3` 解析度 → AppImage + Windows 打包 → **Lord British 城堡對白**(LCB 二樓,載自 `avatar.exe`)→ **vendor 買賣面板**(武器/防具名 + 標題,經 `getName` 查表;`config.b` 受 Boron UCS-2 限制改在存取端中文化)。

**未來方向**:戰鬥畫面用詞校對、裝備/物品面板標籤(火把/寶石/鑰匙…)、`.txf` GUI 字(存檔瀏覽器)SDF 子集烘焙、譯文潤飾(文白比例與專名一致性)。

---

<a name="credits"></a>
## 🙏 License & Credits

- **引擎**:[xu4 — Ultima IV Recreated](https://github.com/xu4-engine/u4)(GPL;Karl Robillard 等維護)。
- **對話字料 oracle**:[MagerValp/u4remastered](https://github.com/MagerValp/u4remastered)(Apache 2.0)的 `talk.json`。
- **原始遊戲**:*Ultima IV: Quest of the Avatar* © 1985 Origin Systems / Richard Garriott。EA / Origin 多年前已將其釋出為 **freeware**,可於 [The Ultima Codex](https://ultimacodex.com/) 等處公開取得;本 repo 內的 tileset 展示圖由原版資料解碼渲染,僅供說明。
- **VGA 美術**:U4 Upgrade / Remastered 社群專案。
- **前例經驗**:[wicanr2/u6-cht](https://github.com/wicanr2/u6-cht) 的 load-time 替換架構與字型 pipeline。
- **譯名體系**:台灣《創世紀聖者之書》。

> repo 納管:中文化工具 / 雙語表 / Docker / 文件 / tileset 展示圖。完整可玩遊戲請依 [`SETUP.md`](SETUP.md) 用 `make download` 自行取得 freeware 資料重建。

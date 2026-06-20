# Sega Master System 版 Ultima IV tileset 提取手記

> 靜態切 ROM 切不出對齊的 tileset(SMS 走 VDP name-table + pattern bank,raw ROM 順序 ≠
> 邏輯 tile 序)。正解:**用模擬器跑進遊戲、dump VRAM**。本文記錄如何 headless 自動化
> 跑到世界地圖、把畫面與 tile 正確還原出來。

## 為什麼非得跑進遊戲

SMS(Master System)的圖形不是「256 個排好的 tile」存在 ROM 裡。它的 VDP 用兩張表:
**pattern generator table**(8×8 圖樣,VRAM 0x0000 起)+ **name table**(畫面排版,
VRAM 0x3800 起,每格指向一個 pattern + palette)。ROM 裡的圖形是壓給特定畫面用的,
線性切出來是錯位的(`tools/sms/sms_tiles.py` 直切只得帶狀噪訊)。

所以要拿到「世界地圖實際用的 tile + 正確顏色」,只能**讓遊戲自己把 tile 載進 VRAM**,
再把 VRAM 倒出來。

## headless 模擬器管線(`tools/sms/`)

### 1. libretro 無頭前端 `lr_dump.c`

載入 **genesis-plus-gx** libretro core(支援 SMS),跑 ROM N 幀後 dump **VRAM(64K)+
CRAM(128B,32 色)**。全 headless:video/audio callback 收下即丟,不開視窗不出聲。

兩個關鍵能力(本專案加的):
- **`U4_SCRIPT="f0:b0,f1:b1,…"`**:按鍵腳本 —— 到第 fN 幀起改按 button bN(離散 edge,
  每 60 幀按 6 放 54)。RETRO id:`B=0 SELECT=2 START=3 UP=4 DOWN=5 LEFT=6 RIGHT=7 A=8`。
- **`U4_SAVESTATE` / `U4_LOADSTATE`**(`retro_serialize`/`unserialize`):**把長導航切成
  可重現小段** —— 跑到某畫面存 state,下次從 state 續跑,不用每次重播 title + 創角。
  這是穿越完整創角的關鍵:盲調計時會卡死,分段存讀才穩。

### 2. `render_screen.py` —— 用 name-table 重建螢幕

讀 VRAM 的 name table(@0x3800,32×28,每格 2 byte:bits0-8=tile、bit11=palette select)+
pattern + CRAM,**完整重建當下螢幕**(每 tile 用 name-table 指定的 palette)。這是驗收
導航走到哪、以及確認顏色對不對的眼睛。

### 3. 穿越創角到世界地圖(savestate 鏈)

SMS U4 沒有預設存檔,`Journey Onward` 無效 → 必須走完整創角。用 savestate 分段:

| 段 | 輸入 | 存檔 |
|---|---|---|
| title → 主選單 | `START` 連續脈衝跳 title | — |
| 選 Initiate → 命名畫面 | 選單預設游標 + `A` 連續脈衝 | `s_name` |
| 命名 → 性別 | **`DOWN×4` 到數字列 + `RIGHT×11` 到 END + `A` 確認**(END 在 row4 col11,該列只 12 欄,RIGHT×12 會繞回!)| `s_aftername` |
| 性別 → intro 敘事 | `A` 選 Male | `s_q1` |
| intro + 吉普賽問答 → **世界地圖** | `A` 連續脈衝衝過敘事與 7 問 | `s_world` |

到世界地圖後 dump VRAM,就拿到**完整世界 tileset + 字型 + UI + HUD**,顏色正確。

### 4. `tilebank_colored.py` —— per-tile 正確上色

SMS 有 2 個 palette(背景 / sprite),不同 tile 用不同 palette(name-table 的 bit11 決定)。
直接用單一 palette 倒整個 tile bank → 地形會出 magenta/yellow 噪訊。本工具掃 name-table
記錄每個 VRAM tile 被哪個 palette 用,**逐 tile 用正確 palette 渲染** → 乾淨彩色 tile bank。

## 解到哪、還沒解到哪

- ✅ **headless 跑進世界地圖**:savestate 分段導航穿過完整創角,可重現。
- ✅ **VRAM + CRAM dump + 螢幕重建**:`render_screen.py` 完美重建畫面。
- ✅ **正確顏色 tile bank**:`tilebank_colored.py` per-tile palette,水藍/草綠/岸/字型全對。
- ✅ **關鍵 tile 識別**:世界地圖 name-table 頻率分析 → 水=VRAM tile `352`(海洋最頻)、
  草/陸 = `292`/`296` 一帶;字型為獨立連續區塊(`! " # … A-Z a-z 0-9`)。
- 🟡 **對齊 xu4 256 canonical 序**:把每個 VRAM tile 對到 xu4 邏輯 tile(`tile_water`/
  `tile_grass`/`tile_A`…)是逐 tile 識別,屬機械性套用;地形 + 字型已可對,完整生物 tile
  需再 dump 戰鬥畫面(savestate 法可達,只是多幾段)。

## 方法論(可移植到其他 console)

1. **console ROM 的圖形未必是 tile bank**:可能是 name-table 排好的畫面;raw 線性切是錯的。
2. **跑模擬器 dump VRAM 才是正解**:libretro core 最容易 headless 自動化(無 GUI)。
3. **savestate 是長導航的命脈**:把「穿過創角」切成可重現小段,逐段試輸入、存檔續跑,
   遠比盲調計時穩 —— 這是能不能走進遊戲的關鍵。
4. **name-table 給 palette**:per-tile palette 來自 name-table 的 select bit,別用單一 palette 倒全部。
5. **頻率 + 已知地圖反推語意**:海洋最頻 = 水;對照已知世界地圖(本專案有 X68000 解出的
   `MAP.BIN` Britannia 當 oracle)可把螢幕 tile 反推成邏輯 tile。

> ROM / 抽出的 tile 屬版權資料,不入 repo;libretro core 與 ymfm 同為外部相依,於 docker
> 內取得。repo 只放解碼/dump 工具與本方法。相關:[多平台主題 skill](../skills/u4-multiplatform-theme/SKILL.md)。

## 組裝 xu4 序 tileset(`map_oracle.py` + `build_world_tileset.py`)

- `map_oracle.py`:SMS 世界畫面水/陸 pattern 滑動匹配 `MAP.BIN` → 找到 Britannia 對應位置
  (實測 (216,110)、吻合 83%)→ 導出 VRAM tile → 邏輯 tile 對映。
- `build_world_tileset.py`:反建(邏輯→VRAM)+ 8×8 放大 16×16 → xu4 序 PNG。
- **實測**:單一世界畫面只能對到 **~15 個邏輯 tile**(該畫面可見的地形),其餘用水填。
- **結論**:完整 256 tile 需**多畫面 dump**(world=地形、town=建築/NPC、dungeon、combat=生物、
  命名畫面=字型),各用 savestate 導航到位、各跑一次 oracle 對映、合併。method 已全通,
  完整化是系統化的多畫面套用。

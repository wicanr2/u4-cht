---
name: u4-msx2-extract
description: 從 MSX2 版 Ultima IV(Pony Canyon 1987)的 .dsk 磁碟抽出 tileset(SHAPE.DAT)、intro 畫面(II*.MSX / RUNE*.MSX / ENDPIC / CARD)、字型(FONT.DAT)並解碼成 PNG。涵蓋 FAT12 取檔、用 byte 自相關反推未知圖形格式的方法、MSX2 SCREEN5 4bpp 解碼,以及殘餘待校正項。觸發:「抽 MSX2 U4 tileset/intro」「SHAPE.DAT 解碼」「MSX 圖形格式反推」。
---

# MSX2 版 Ultima IV 圖形抽取與解碼 SOP

把 Pony Canyon 1987 MSX2 版的圖形資產(tileset / intro / 字型)從磁碟抽出、
解碼成 PNG,供 xu4 多主題系統當「MSX2 畫風」。屬 `u4-multiplatform-theme` 的
單平台深掘;通用引擎整合見該 skill。**引擎/資料分離**:磁碟與抽出資產屬版權
資料,留本機 `materals/_extracted/msx2/`,repo 只放解碼工具。

## 1. 取檔(FAT12)

媒體:3× `.dsk`(MSX-DOS,**FAT12**,720KB)。用 mtools(免掛載):

```bash
export MTOOLS_SKIP_CHECK=1
mdir  -i "Disk 1 of 3.dsk" ::            # 列目錄
mcopy -i "Disk 1 of 3.dsk" ::SHAPE.DAT . # 取檔
```

關鍵檔(分佈三片):
| 檔 | 大小 | 內容 |
|---|---|---|
| `SHAPE.DAT` | 24576 | **tileset**(256 tile) |
| `FONT.DAT` | 8064 | 字型(格式另解,見 §4) |
| `II1X.MSX` | 19460 | intro 風景畫(256×152) |
| `RUNE*.MSX` / `ENDPIC.MSX` | 11620 | rune / 結局畫(寬度待定) |
| `CARD1-3.MSX` | ~3078 | 吉普賽算命卡 |
| `U4MAP.BIN` / `TALKDATA.BIN` | — | 地圖 / 對話資料 |

## 2. tileset:SHAPE.DAT(✅ 已破解到可辨識)

**格式**(以 byte 自相關 + 視覺驗證反推):
- `24576 = 256 tile × 96 byte`(對上 U4 的 256 tile 數)。
- 每 tile = `16 row × 6 byte`;`6 byte = 12 px × 4bpp chunky`(高 nibble 先,左→右)。
- 即 **12 寬 × 16 高、16 色(MSX2 SCREEN5)**。

工具:`tools/build_msx2_tileset.py --shape SHAPE.DAT --out msx_tileset.png`。

**怎麼推出來的(可複用方法論)**:
1. 全螢幕圖(II1X.MSX)先確認**像素格式 = 4bpp chunky 高 nibble 先**(直接 row-major
   解出可辨識風景)。→ 引擎用 SCREEN5 chunky,非 planar。
2. 但 SHAPE.DAT 用 16×16/128B row-major 解 = **噪訊**,只有 uniform tile(全黑/白)
   正確 → 判定「像素格式對、tile 內 byte 序不同」。
3. **byte 自相關**(對每個 lag 算 `data[i]==data[i+lag]` 比例)是決定性診斷:
   dominant `lag=6`(row stride)、`lag=96`(tile stride)、`lag=192`。
   → tile=96B(非 128B!)、row=6B、16 row/tile。**192-tile 假設是錯方向**。
4. `6 byte/row` 在已確認的 4bpp 下唯一吻合 = **12 px 寬**(非 16)。試解 → 出現
   可辨識人形 sprite(膚色、衣著)+ dither 地形,**無對角剪切**(代表 row stride 精確)。
5. 排除過的錯誤解讀(全噪訊或梳狀,勿重試):16×16/128B row/col/quad/evenodd、
   planar 4bpp(block/interleave)、16×16×3bpp(planar/chunky/byte-interleave)、
   nibble-plane split(hi 左/lo 右)。

**殘餘待校正(非結構性)**:
- ✅ **調色盤已解**:真 16 色 palette 在 `disk_1.dsk @ offset 0x02de9f`(32-byte VDP
  table,SCREEN5 格式 `byte0=0RRR0BBB`、`byte1=00000GGG`,3-bit/分量→8-bit)。
  `build_msx2_tileset.py` 已內建(並加 `--palette <file> --palette-off <hex>` 參數)。
  **驗證**:套用後渲染 II1X.MSX 風景圖天空/樹/草/河/幹顏色全對(dither 是 SCREEN5
  原生有序抖動,非 palette 錯)。**找法**:寫 palette pattern 掃描器掃三張 .dsk,
  disk_1 出乾淨候選,用 II1X 當 ground-truth 一發命中(未動 emulator)。
- 🟡 **12 寬 vs xu4 的 16×16**:MSX 邏輯 tile 寬 12,整合進 xu4 16×16 grid 需置中補邊
  或等比放寬;或直接以 openMSX VRAM dump(整屏 tilesheet)取 16×16 版本繞過。
- 🟡 **SHAPE.DAT 前段非 tile?**:套真 palette 後,tileset **下半部 sprite 顏色正確可辨識**
  (膚色、藍/紅衣、綠地形),但**上半部仍噪訊** → 前段可能是非 tile 資料(header/字型/
  meta)或不同編碼,**非 palette 問題**。下一步:用 II1X 同套 palette 比對 SHAPE 前段是什麼。
- ✅ **ground-truth 校正建議**:openMSX headless 跑遊戲 → 進地圖畫面 → dump VRAM page
  存 PNG,一次校正調色盤 + 確認 tile 真實寬度,終結 file-format 推測。

## 3. intro 畫面:II*.MSX / RUNE / ENDPIC(✅ II1X 已驗證)

**格式**:`4-byte header + row-major chunky 4bpp(高 nibble 先)`,SCREEN5 16 色。
尺寸由檔案大小回推:`(len-4)*2 = W*H`。`II1X.MSX`(19460)= 256×152 ✅(風景圖)。

工具:`tools/build_msx2_intro.py --in II1X.MSX --out ii1x.png --width 256`。

- 🟡 `RUNE*/ENDPIC`(11616 body)非 256 寬(11616 不整除 128);候選寬 192/176/...
  需逐一試寬度找不剪切者,或 header 長度不同。`CARD*.MSX`(~3078)尺寸更小,同法。
- 🟡 同 tileset 的調色盤近似問題;openMSX VRAM 校正一併解。

## 4. 字型:FONT.DAT(🔴 未解)

8064 byte,byte 值像像素(0x22/0xff/0x0f)但非單純 4bpp/1bpp row-major。寬度掃描
(4bpp / 1bpp)無強勝出,頂部有規則直筆畫(疑混多段)。低優先(中文化用自建 CJK
字型,不需原版字型)。

## 5. 方法論:反推未知圖形格式(可移植到其他平台)

1. **先用全螢幕圖定像素格式**(整屏 row-major 最易出圖)→ 得知 bpp / nibble 序 / chunky vs planar。
2. **uniform-tile 測試**:若小資產 row-major 解出「uniform tile 正確、細節 tile 噪訊」
   → 像素格式對,只是 tile 內 byte 序不同。
3. **byte 自相關找週期**:dominant lag = row stride / tile stride。**先用資料說話,別盲猜維度**。
4. **算術交叉**:tile-count 應對上遊戲已知 tile 數(U4=256);row stride × bpp 得寬度。
5. **無剪切 = stride 正確**:解出的圖若無對角剪切,row stride 必對;殘餘條紋才是
   列內 pixel/nibble 順序問題。
6. **單色(任一 bit on=白)只看形狀**,排除調色盤干擾判 layout。
7. **ground-truth 兜底**:結構推不到 pixel-perfect 時,emulator VRAM dump 取真值校正。

## 6. 容器紀律

所有 Python 解碼走 `u4cht/extract` docker image 同步前景跑(PIL/numpy 內建),
**不污染系統 Python、不留背景容器**。預覽圖 dump 後用 Read 看,不開 GUI viewer。

# U4-cht 開發環境設定

本 repo 只納管**自有產出**(PLAN、Dockerfile、腳本、docs)。上游引擎 `xu4/` 與參考用 `u4remastered/`
**不入庫**(見 `.gitignore`),由下列指令重建。

## 1. 取得上游

```bash
# xu4 引擎(Allegro 5 後端 / 跨平台 C++)
git clone https://github.com/xu4-engine/u4.git xu4
cd xu4 && git submodule update --init --recursive && cd ..

# (可選)u4remastered:僅作對話字料 oracle
git clone https://github.com/MagerValp/u4remastered.git u4remastered
```

## 2. 建置 xu4(Allegro 5,Docker)

```bash
# 建置引擎 image(自源碼建 Boron + Faun,make download 自動抓 freeware U4 資料)
docker build -f docker/Dockerfile.zh -t u4cht/xu4-allegro xu4
```

產物(image 內 `/build/xu4/`):`src/xu4`(vDR-1.0)、`Ultima-IV.mod`、`U4-Upgrade.mod`、`render.pak`、`ultima4.zip`、`u4upgrad.zip`。

## 3. headless 截圖 pass/fail loop

```bash
# 建置測試 image(xvfb + Mesa 軟體 GL + ImageMagick)
docker build -f docker/Dockerfile.test -t u4cht/xu4-test docker

# 跑遊戲並截圖:<等待秒數> <scale> [額外 xu4 args]
mkdir -p /tmp/u4shot
docker run --rm -v /tmp/u4shot:/out u4cht/xu4-test 22 3
# → /tmp/u4shot/screen.png
# shot.sh 預設帶 --filter xBRZ(灰階 CJK AA 最平滑);
# 第 3 參數自帶 --filter 可覆蓋,或附加其他 args(如 "--skip-intro")
```

## 4. 抽取 NPC 對話 → 雙語表(P4 資料面)

原始 `.TLK` 來自 `ultima4.zip`(Origin © 1985,**不入庫**),先從 image 取出:

```bash
mkdir -p data/zip data/tlk
docker run --rm -v "$PWD/data/zip:/out" u4cht/xu4-allegro \
  bash -c 'cp /build/xu4/ultima4.zip /out/'
python3 - <<'PY'
import zipfile
zf=zipfile.ZipFile('data/zip/ultima4.zip')
for n in zf.namelist():
    if n.lower().endswith('.tlk'):
        open(f'data/tlk/{n.upper()}','wb').write(zf.read(n))
PY

# 抽取 + 對齊 talk.json → 雙語表 + 報告
python3 tools/extract_tlk.py \
  --tlk-dir data/tlk \
  --talk-json u4remastered/src/talk/talk.json \
  --out-bilingual dumps/talk_bilingual.json \
  --out-report dumps/talk_alignment_report.md
```

stringtable(intro/codex/shrine)與硬編 `screenMessage` 字串(需先取出 `avatar.exe`/`title.exe`):

```bash
# 從 ultima4.zip 取出 exe(同上,放 data/)
python3 - <<'PY'
import zipfile
zf=zipfile.ZipFile('data/zip/ultima4.zip')
for n in zf.namelist():
    if n.lower() in ('avatar.exe','title.exe'):
        open(f'data/{n.lower()}','wb').write(zf.read(n))
PY

# u4read_stringtable(title.exe/avatar.exe)→ 114 字串
python3 tools/extract_stringtable.py --data-dir data \
  --out dumps/stringtable_bilingual.json --out-report dumps/stringtable_report.md

# 硬編 screenMessage 字面(靜態分析 xu4/src)→ 420 site / 318 唯一
python3 tools/extract_hardcoded.py --src-dir xu4/src \
  --out dumps/hardcoded_strings.json --out-report dumps/hardcoded_report.md

# vendor Boron 腳本(vendors.b)→ 278 唯一字串
python3 tools/extract_vendor_boron.py --files xu4/module/Ultima-IV/vendors.b \
  --out dumps/vendor_bilingual.json --out-report dumps/vendor_report.md
```

## 5. 翻譯 NPC 對話(P5,分批平行 + 共享 glossary)

```bash
# 切批(8 批,每批 2 城)
python3 tools/talk_batches.py split --in dumps/talk_bilingual.json --batches 8
# → 8 個平行翻譯 agent 各翻一批,依 docs/glossary-u4.md 填 zh,寫 batch_NN.zh.json
# 合併回填 + 覆蓋率
python3 tools/talk_batches.py merge --in dumps/talk_bilingual.json
```

譯名/風格權威:`docs/glossary-u4.md`(八德/城市/真言/夥伴固定譯名 + 文白並用)。

## 檔案

| 路徑 | 說明 |
|---|---|
| `PLAN.md` | 評估 + 執行計畫(權威文件) |
| `docs/glossary-u4.md` | 共享翻譯 glossary(術語權威) |
| `tools/talk_batches.py` | talk 雙語表分批 / 合併(供平行翻譯) |
| `docker/Dockerfile.zh` | xu4 Allegro 5 Linux build |
| `docker/Dockerfile.test` | 在上者之上加 headless 截圖工具 |
| `docker/shot.sh` | Xvfb + llvmpipe 跑 xu4 並截圖 |
| `tools/extract_tlk.py` | 抽 DOS `.TLK` NPC 對話 + 對齊 talk.json → 雙語表 |
| `tools/extract_stringtable.py` | 抽 `u4read_stringtable`(intro/codex/shrine)114 字串 |
| `tools/extract_hardcoded.py` | 靜態抽硬編 `screenMessage` 字面 → 318 唯一字串 |
| `tools/extract_vendor_boron.py` | 抽 `vendors.b` Boron 腳本 → 278 唯一 vendor 字串 |
| `dumps/talk_bilingual.json` | 256 NPC × 12 欄雙語表雛形(en 已填,zh 待填) |
| `dumps/stringtable_bilingual.json` | 114 intro/codex/shrine 字串雙語雛形 |
| `dumps/hardcoded_strings.json` | 318 唯一硬編字串(en + zh 待填 + has_format) |
| `dumps/vendor_bilingual.json` | 278 唯一 vendor 字串(en + zh 待填 + has_placeholder) |
| `dumps/*_report.md` | 各抽取的對齊/統計報告 |
| `docs/` | P3 hook 盤點等工程文件 |
| `data/`(gitignore) | 原始遊戲資料(zip / `.TLK`),由 `make download` 重建 |

## 6. 字型 + 接 hook(P6,動引擎)

```bash
# 產生 CJK 字型 atlas(掃四源 zh,1978 漢字)+ en→zh 二進位 lookup
python3 tools/build_cjk_font.py --font /usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc \
  --index 3 --size 14 --cell 16 --mode gray --out assets/cjk_font.bin --preview assets/cjk_preview.png
# (--index 3 = Noto Sans CJK TC;--mode gray = 灰階抗鋸齒,預設;Medium 比 Ming/Bold 易讀)
python3 tools/build_lookup.py --out assets/u4_cht.tab

# 套引擎 patch 到 xu4 + 安裝資產 → 重建
bash tools/apply_cht.sh
docker build -f docker/Dockerfile.zh -t u4cht/xu4-allegro xu4
docker build -f docker/Dockerfile.test -t u4cht/xu4-test docker

# headless 自測(env 守護,渲染已知 NPC 對白驗證全鏈路)
docker run --rm -e U4CHT_SELFTEST=1 -v /tmp/u4shot:/out u4cht/xu4-test 6 3
```

引擎改動見 `patches/engine/`(cht.cpp/h + cht-engine.patch)。

## 7. 字形切換(Firefly / Noto)

三套 CJK atlas 已隨 `assets/` 提供;執行時以 env `U4CHT_FONT` 選用:

| `U4CHT_FONT` | 字形 | 來源 |
|---|---|---|
| (未設) | Noto Sans CJK TC Medium(黑體,預設) | system noto |
| `firefly` / `sung` | 文鼎PL細上海宋(明體) | fonts-arphic-bsmi00lp |
| `kai` | 文鼎PL中楷(楷體) | fonts-arphic-bkai00mp |

```bash
# 取 Firefly 字型(study-area firefly-font = AR PL Big5)→ 建 atlas
apt-get download fonts-arphic-bsmi00lp fonts-arphic-bkai00mp
dpkg -x fonts-arphic-bsmi00lp_*.deb /tmp/bsmi; dpkg -x fonts-arphic-bkai00mp_*.deb /tmp/bkai
python3 tools/build_cjk_font.py --font /tmp/bsmi/usr/share/fonts/truetype/arphic-bsmi00lp/bsmi00lp.ttf \
  --size 14 --cell 16 --mode gray --out assets/cjk_font_firefly.bin
python3 tools/build_cjk_font.py --font /tmp/bkai/usr/share/fonts/truetype/arphic-bkai00mp/bkai00mp.ttf \
  --size 14 --cell 16 --mode gray --out assets/cjk_font_kai.bin

# 用 Firefly 宋體跑
docker run --rm -e U4CHT_FONT=firefly -v /tmp/u4shot:/out u4cht/xu4-test 22 1
```

## 8. 全平台打包

前置:`bash tools/apply_cht.sh`(套 patch + 產資產到 `xu4/`)。

```bash
# Linux AppImage(Allegro5,遞迴 ldd 收庫,靜態 runtime)
docker build -f dist/appimage/Dockerfile -t u4cht/appimage xu4
docker run --rm -v "$PWD/dist/out":/out u4cht/appimage          # → u4-cht-x86_64.AppImage

# Linux tarball
bash dist/make-release.sh "$PWD/dist/out/u4-cht-linux-x86_64.tar.gz"

# Windows x64(mingw64 交叉編譯,GLFW 後端 + 全 DLL)
docker build -f dist/win/Dockerfile -t u4cht/win xu4
bash dist/win/make-zip.sh "$PWD/dist/out/u4-cht-windows-x64.zip" # → exe + 全 DLL + 模組 + 字型 + 資料
```

| 平台 | 方式 | 後端 | 驗證 |
|---|---|---|---|
| Linux AppImage / tarball | 本地 Docker | Allegro 5 | ✅ 本地實建 |
| Windows x64 zip | 本地 Docker(mingw64) | GLFW | ✅ objdump 確認全 DLL |
| macOS(arm64/x86_64) | GitHub Actions `build-mac.yml` | Allegro 5 | CI(macOS runner) |
| Android APK | GitHub Actions `build-android.yml` | GLV | CI(scaffold,需驗證) |

- **Mac/Android 走 CI**:Mac 需 macOS runner(Linux 無法跨編 Mach-O);Android 用 xu4 上游
  GLV 移植 + NDK。觸發:`gh workflow run build-mac.yml` / `build-android.yml`,或 push `v*` tag
  自動建並附到 Release。CI 會自行 clone xu4 上游(pinned commit)+ 跑 `apply_cht.sh`。

## 9. dev-setup-bundle(換機接續 + claude -r)

把整個開發環境打包成私用 tar.zst,讓另一台機器 (1) 重建 build/打包環境 (2) 用 `claude -r`
接續同一個 Claude 對話與記憶。詳見 `previous-work.md`。**屬私用,含對話記錄與版權素材,勿公開。**

```bash
# 打包(排除可重建的 build 產物與 image)
ENC=-home-anr2-u3-cht-u4-cht                       # cwd 編碼:絕對路徑 / → -,開頭加 -
mkdir -p claude-session/projects
cp -a ~/.claude/projects/$ENC claude-session/projects/   # *.jsonl + memory/
tar --zstd -cf ../u4-cht-dev-setup-$(date +%Y%m%d).tar.zst \
  --exclude='*/dist/out' --exclude='*/.copr' --exclude='*/obj' --exclude='__pycache__' \
  --exclude='*.AppImage' --exclude='*/build' \
  -C "$(dirname "$PWD")" "$(basename "$PWD")"

# 另一台機器:解到相同絕對路徑 → 還原 claude-session → cd 專案
cp -a claude-session/projects/$ENC ~/.claude/projects/
cd /home/anr2/u3-cht/u4-cht && claude --continue
#   路徑不同時:claude --resume 942d4cbc-4e7e-4387-85e3-86546d359c87  (用 UUID 不卡路徑)
```

#!/bin/bash
# 在本機 macOS(Apple Silicon / Intel)原生建置 Ultima IV 繁中版 .app。
# 等同 .github/workflows/build-mac.yml,但在自己的 Mac 上跑,免等 CI runner。
#
# 用法:bash dist/build-mac-local.sh
# 產出:./xu4/Ultima4-cht.app(雙擊即玩;首次右鍵「打開」繞 Gatekeeper)
#
# 需要:Homebrew、git、python3。會用到 sudo(裝 Boron / Faun 到 /usr/local)。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
XU4="$ROOT/xu4"
XU4_UPSTREAM="https://github.com/xu4-engine/u4.git"
XU4_COMMIT="6a7ee3d0079cfdc1c8fb9ba7a3c710a957155a71"
ARCH="$(uname -m)"
BREW="$(brew --prefix)"

echo "==> [1/9] brew 相依"
brew install allegro pkg-config libpng libvorbis libogg dylibbundler curl || true
python3 -m pip install --break-system-packages pillow numpy scipy \
  || pip3 install pillow numpy scipy

echo "==> [2/9] clone xu4 上游(pinned)+ submodule(faun / glv)"
if [ ! -d "$XU4" ]; then
  git clone "$XU4_UPSTREAM" "$XU4"
fi
( cd "$XU4" && git checkout "$XU4_COMMIT" && git submodule update --init src/faun src/glv )

echo "==> [3/9] 建 Boron(程式 + 靜態庫)→ /usr/local"
if [ ! -d /tmp/boron ]; then
  git clone https://git.code.sf.net/p/urlan/boron/code /tmp/boron
fi
( cd /tmp/boron && git checkout v2.0.8 && ./configure --static --thread && make
  make DESTDIR=/usr/local install
  make DESTDIR=/usr/local install-dev )

echo "==> [4/9] 取中文字型(Noto Sans CJK TC Medium)"
mkdir -p /tmp/noto
curl -fsSL -A "Mozilla/5.0" -o /tmp/noto/NotoSansCJK.otf \
  "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Medium.otf"
test -s /tmp/noto/NotoSansCJK.otf

echo "==> [5/9] 套繁中化 patch + 產資產(apply_cht.sh)"
( cd "$ROOT" && NOTO=/tmp/noto/NotoSansCJK.otf NOTO_INDEX=0 bash tools/apply_cht.sh "$XU4" )

echo "==> [6/9] 建 Faun(注入 CoreAudio 後端)"
cd "$XU4"
cp "$ROOT/patches/mac/sys_coreaudio.c" src/faun/
perl -0pi -e 's/(#include "sys_wasapi.c"\n)(#else\n#error "Unsupported system")/$1#elif defined(__APPLE__)\n#include "sys_coreaudio.c"\n$2/' src/faun/faun.c
grep -q 'sys_coreaudio.c' src/faun/faun.c
perl -pi -e 's/(typedef dispatch_semaphore_t Semaphore;)/$1\ntypedef struct timespec MsgTime;/' src/faun/support/tmsg.c
perl -0pi -e 's/#else\n    int r;\n\n    r = sem_timedwait\(&mp->reader, ts\);/#elif defined(__APPLE__)\n    if (dispatch_semaphore_wait(mp->reader, dispatch_walltime(ts, 0)))\n        return 1;\n#else\n    int r;\n\n    r = sem_timedwait(&mp->reader, ts);/' src/faun/support/tmsg.c
grep -q 'dispatch_walltime' src/faun/support/tmsg.c
( cd src/faun && ./configure --no_flac --static && \
  make libfaun.a OPT="-DUSE_LOAD_MEM -DUSE_SFX_GEN -I$BREW/include" && \
  make install )

echo "==> [7/9] 設定 + patch xu4(GL3 核心 + Makefile 連結)"
./configure --allegro
perl -pi -e 's{#include <OpenGL/gl\.h>}{#include <OpenGL/gl3.h>}' src/gpu_opengl.h
perl -pi -e "s{^CXXFLAGS=-Wall -I\. -Isupport}{CXXFLAGS=-Wall -I. -Isupport -I/usr/local/include -I$BREW/include -DGL_SILENCE_DEPRECATION -DGL_DO_NOT_WARN_IF_MULTI_GL_VERSION_HEADERS_INCLUDED}" src/Makefile
perl -pi -e 's{^LIBS=.*}{LIBS=\$(UILIBS) -lallegro_main -lvorbisfile -lvorbis -logg -lpng -lz -framework OpenGL -framework AudioToolbox -framework CoreFoundation}' src/Makefile
perl -pi -e "s{^(-include \.\./make.config)}{\$1\nLDFLAGS+=-L/usr/local/lib -L$BREW/lib}" src/Makefile
grep -q 'AudioToolbox' src/Makefile

echo "==> [8/9] 取 U4 freeware 資料 + 編譯 xu4"
make download
make MFILE_OS=Makefile
test -x src/xu4

echo "==> [9/9] 組裝 Ultima4-cht.app + bundle dylib + 簽章"
APP="Ultima4-cht.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources/share"
cp src/xu4 "$APP/Contents/MacOS/xu4"
cp Ultima-IV.mod U4-Upgrade.mod render.pak cjk_font*.bin u4_cht.tab "$APP/Contents/Resources/share/"
cp ultima4.zip u4upgrad.zip "$APP/Contents/Resources/share/" 2>/dev/null || true
cat > "$APP/Contents/MacOS/launch" <<'LAUNCH'
#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../Resources/share"
exec "$HERE/xu4" -s 2 --filter xBRZ "$@"
LAUNCH
chmod +x "$APP/Contents/MacOS/launch" "$APP/Contents/MacOS/xu4"
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Ultima4-cht</string>
  <key>CFBundleExecutable</key><string>xu4</string>
  <key>CFBundleIdentifier</key><string>tw.xu4.ultima4cht</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
dylibbundler -od -b \
  -x "$APP/Contents/MacOS/xu4" \
  -d "$APP/Contents/Frameworks/" \
  -p "@executable_path/../Frameworks/"
codesign --force --deep --sign - "$APP" || true

echo ""
echo "✅ 完成:$XU4/$APP"
echo "   執行:open \"$XU4/$APP\"   (首次若被擋:右鍵「打開」)"
echo "   或直接跑:( cd \"$XU4/$APP/Contents/Resources/share\" && ../MacOS/xu4 -s 2 --filter xBRZ )"
echo "   字形切換:export U4CHT_FONT=firefly(或 kai),省略=Noto 黑體"
echo "   熱鍵:F2 切 EGA/VGA · F3 切解析度"

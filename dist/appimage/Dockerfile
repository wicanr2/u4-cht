# Ultima IV CHT — AppImage builder(Ubuntu 22.04,老 glibc 提升相容性)
# context = xu4/(內含 patched source + cjk_font*.bin + u4_cht.tab + appimage/ 支援檔)
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential git make curl ca-certificates pkg-config file desktop-file-utils \
      libpng-dev libvorbis-dev libogg-dev libpulse-dev \
      liballegro5-dev liballegro-acodec5-dev liballegro-audio5-dev \
 && rm -rf /var/lib/apt/lists/*

# Boron(程式 + lib)
RUN git clone https://git.code.sf.net/p/urlan/boron/code /tmp/boron \
 && cd /tmp/boron && git checkout v2.0.8 && ./configure --static --thread \
 && make && make DESTDIR=/usr install && make DESTDIR=/usr install-dev

ARG CACHEBUST=1
RUN echo "cachebust=$CACHEBUST"
COPY . /build/xu4
WORKDIR /build/xu4
RUN cd src/faun && ./configure --no_flac && make && make DESTDIR=/usr install
RUN ./configure --allegro && make download && make -C src clean && make

# appimagetool + 靜態 runtime(自帶 FUSE,現代桌面不需系統 libfuse2)
RUN curl -sSL -o /usr/local/bin/appimagetool \
      https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage \
 && chmod +x /usr/local/bin/appimagetool \
 && curl -sSL -o /usr/local/bin/runtime-x86_64 \
      https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64 \
 && chmod +x /usr/local/bin/runtime-x86_64

# 組 AppDir
RUN set -e; \
    AD=/build/AppDir; mkdir -p $AD/usr/bin $AD/usr/lib $AD/usr/share/u4-cht; \
    cp src/xu4 $AD/usr/bin/; \
    cp Ultima-IV.mod U4-*.mod render.pak cjk_font*.bin u4_cht.tab $AD/usr/share/u4-cht/; \
    cp ultima4.zip u4upgrad.zip $AD/usr/share/u4-cht/ 2>/dev/null || true; \
    cp appimage/AppRun $AD/AppRun; chmod +x $AD/AppRun; \
    cp appimage/u4-cht.desktop $AD/u4-cht.desktop; \
    cp appimage/u4-cht.png $AD/u4-cht.png; \
    # 遞迴 ldd 收集所有非 glibc 庫 \
    collect() { ldd "$1" 2>/dev/null | awk '/=> \//{print $3}'; }; \
    queue=$(collect $AD/usr/bin/xu4); seen=""; \
    while [ -n "$queue" ]; do \
      next=""; \
      for lib in $queue; do \
        case "$seen" in *" $lib "*) continue;; esac; seen="$seen $lib "; \
        base=$(basename "$lib"); \
        case "$base" in ld-linux*|libc.so*|libm.so*|libdl.so*|libpthread.so*|librt.so*|libstdc++*|libgcc_s*) continue;; esac; \
        cp -L "$lib" $AD/usr/lib/ 2>/dev/null || true; \
        next="$next $(collect $lib)"; \
      done; queue="$next"; \
    done; \
    ls $AD/usr/lib | wc -l

# 打包 AppImage(用靜態 runtime,免系統 libfuse2)
RUN cd /build && ARCH=x86_64 appimagetool --appimage-extract-and-run \
      --runtime-file /usr/local/bin/runtime-x86_64 \
      AppDir u4-cht-x86_64.AppImage 2>&1 | tail -5

CMD ["bash","-c","cp /build/u4-cht-x86_64.AppImage /out/ && echo done"]

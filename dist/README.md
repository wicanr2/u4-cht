# 散布 / 遊玩

## 桌面遊玩(Docker + X11,最簡)
```bash
U4CHT_FONT=firefly bash dist/play.sh    # 字形:firefly(宋體)/ kai(楷體)/ 省略=Noto
```

## Linux 可執行包
```bash
bash dist/make-release.sh u4-cht-linux.tar.gz
tar xzf u4-cht-linux.tar.gz && cd u4-cht-linux
sudo apt install liballegro5.2 liballegro-acodec5.2 liballegro-audio5.2 libpng16-16 libvorbisfile3
U4CHT_FONT=firefly ./run.sh -s 2 --filter xBRZ
```
`libfaun.so.0` 已隨包(自建,非 apt);`liballegro5.2` 等由系統提供。

## Windows
xu4 內建 `dist/Dockerfile.mingw` + `tools/cbuild` 可跨編(需下載 mingw SDK);本專案尚未產出 Windows 包。

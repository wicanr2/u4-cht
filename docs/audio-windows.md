# Windows 音樂「頓頓」修正(WASAPI underrun)

## 症狀
Windows 版(`xu4.exe`,GLFW 後端)一啟動,標題音樂的**背景 bass / 長音週期性「頓頓」**(掉幀),
但**速度/音高正確**。Linux(Allegro / PulseAudio)無此問題。

## 根因
xu4 的音訊走 [Faun](https://codeberg.org/WickedSmoke/faun),Windows 後端是 **WASAPI**(`src/faun/sys_wasapi.c`):

- 串流緩衝很小:`bufTime = defPeriod × dpMultiple`,`dpMultiple` 初值 3 → 約 **30–40ms**。
- Faun 補緩衝用 `Sleep(2)`,但 **Windows 預設計時器精度約 15.6ms** —— 想睡 2ms 實際睡 ~15ms。
- 15ms 的睡眠抖動 vs 30–40ms 的緩衝 → **週期性 underrun**。連續的 bass/pad 長音把每次掉幀都暴露出來,
  短促鼓點則被遮蔽,所以聽起來是「bass 頓頓」。
- 音高正確,是因為 Faun 內部固定 44100 混音、WASAPI 用 `AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM`
  自動把 44100 轉成裝置取樣率(常見 48000),轉換器處理掉了音高。

## 修正
在 xu4 啟動時(`src/xu4.cpp`,`#ifdef _WIN32`)呼叫 **`timeBeginPeriod(1)`**,把系統計時器精度拉到 1ms。
這樣 `Sleep(2)` 才準,**預設緩衝即足夠,毋須放大緩衝**(放大緩衝雖也能解,但會增加音效延遲)。
連結需加 `winmm`(`project.b` 的 win32 glfw libs)。

- patch:[`patches/engine/win-audio.patch`](../patches/engine/win-audio.patch)(由 `tools/apply_cht.sh` 套在 `cht-engine.patch` 之上)
- 對非 Windows build 無影響(`timeBeginPeriod` 在 `#ifdef _WIN32` 內,`winmm` 僅 win32 連結)。

## 備援(免重編)
若在某些機器上仍有殘餘頓頓,Faun 支援用環境變數放大緩衝(無須改碼):

```bat
set FAUN_BTIME=600000:40   rem ~60ms 緩衝;頓頓沒好可加大到 1000000(100ms)
xu4.exe -s 2 --filter xBRZ
```

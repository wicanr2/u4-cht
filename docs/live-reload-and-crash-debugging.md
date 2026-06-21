# Live-reload 懸空指標 與 崩潰除錯經驗

做「遊玩中即時切換」功能(本專案的 `F2` 切美術主題、`F3` 切解析度)時,踩到一整類
**use-after-free 崩潰**:切換會重建 `imageMgr` / `tileanims` / `config`,把先前**快取的指標
全部變懸空**,下一次繪製就 segfault。同一根因在這個 session 觸發了四個不同的崩潰點,
修法有固定套路。連同「release 才崩、debug 重現不出」的除錯方法,記在這裡。

## 一、live-reload 會弄懸空哪些東西

`screenReInit()`(主題切換時呼叫)會:`screenDelete_data` → `new ImageMgr` →
`screenInit_data`。於是**所有在重建前抓好的指標都失效**:

| 快取的東西 | 在哪 | 切換後 |
|---|---|---|
| `tile->anim`(TileAnim*) | 每個 tile,綁到 `state.tileanims` | 舊集合被 delete → 懸空 |
| `beastiesImg`(ImageInfo*) | IntroController 成員 | 舊 imageMgr 釋放 → 懸空 |
| `TextView::charset`(static Image*) | 所有 TextView 共用 | 舊 charset 圖釋放 → 懸空 |
| `loc->map` 的 runtime 物件 | Map.objects(NPC/怪物) | 換成另一個 config 的 Map → 物件全丟 |

**release(-O3)才崩,debug(-O0)常常不崩** —— 因為 debug 下釋放的記憶體沒被立刻重用,
懸空指標還讀得到舊值;release + 真實負載會立刻重用那塊記憶體 → deref 即爆。
**所以不要用 debug build「跑一下沒崩」就當修好;release 才是真考驗。**

## 二、修法(依穩健度排序,擇一或併用)

1. **用時重抓,不跨 reload 快取**(最簡單)。
   `drawBeasties()` 每幀 `xu4.imageMgr->get(BKGD_ANIMATE)`,拿到的必屬現用 imageMgr。
2. **在 choke point 統一刷新**。
   `screenInit_data`(啟動 + 每次 reInit 都會跑、imageMgr 剛就緒)裡刷新 static 快取
   (`TextView::reloadCharset()`),涵蓋所有走該資源的繪製路徑,不靠個別呼叫時序。
3. **用前驗證成員資格**(指標可能懸空、無法 null 判定時)。
   `TileAnimSet::contains(anim)` 只比對指標**值**、不 deref 傳入指標,對懸空安全;
   不在現用集合 → 退回靜態繪製。
4. **re-entrancy guard**。重載期間 `init()` 內的 `musicPlay/updateScreen` 會 pump 事件,
   re-entrant 的計時器/滑鼠會踩到半重建狀態。設一個 `reloadingTheme` 旗標涵蓋整段重載,
   `timerFired`/`inputEvent` 一律早退。**注意**:只 guard `binData==NULL` 不夠,因為
   `init()` 很早就把 binData 重建成非 NULL。
5. **不要換掉「持有 runtime 狀態」的物件,只換便宜的參考**。
   切主題別把 `loc->map` 換成另一個 config 的 Map(會丟掉現場 NPC/怪物);改成
   `loc->map->tileset = newConfig->tileset()`,地圖與物件原封不動,只換繪製圖塊集。
   (Object 存的是 MapTile id,與 config 無關,渲染時用新 tileset 查 id。)

## 三、崩潰除錯方法

### release 崩潰要能自報 backtrace
裝一個 signal handler,用 `backtrace_symbols_fd()`(signal-safe、不 malloc)把訊號 + 呼叫
堆疊印到 stderr;連結帶 `-rdynamic`、打包設 `NO_STRIP`,函式名才解析得出來。這樣使用者
在自己機器(能穩定重現)上一崩就吐 backtrace,等於把 debug loop 搬到真正會崩的環境。

```c
static void crashHandler(int sig) {
    void* bt[40]; int n = backtrace(bt, 40);
    backtrace_symbols_fd(bt, n, 2);   // 寫 stderr
    signal(sig, SIG_DFL); raise(sig);
}
```

### headless 重現:gdb-call 勝過送鍵
WM-less 的 xvfb 下 `xdotool` 送鍵/點擊很不可靠(沒有 window manager、焦點在 root)。
改用 **gdb 直接呼叫函式**重現,確定性高:

```
break IntroController::timerFired
run
call (bool)xu4.intro->keyPressed(315)        # F2
# 自己 malloc 一個 InputEvent 再 call inputEvent 模擬滑鼠
```

但要小心:gdb-call 繞過真實事件佇列時序與 release 的記憶體重用,**可能就是不會崩**
(本 session 五種 gdb 重現都沒觸發,真兇要靠使用者 release 版的 backtrace 才定位)。
此時別硬猜,讓 release crash handler 在使用者端報位置最快。

### 背景任務存活性
編排背景 build / 容器時同步前景執行、等回傳;不要寫 `until [ -f x ]; do sleep; done`
這種 sentinel 迴圈空轉。docker 跑 headless app 要帶 `--frames N` 或 `timeout`,別讓它
無上限 poll 吃 CPU。

## 四、合併「產生檔」的雷(cht-engine.patch)

`patches/engine/cht-engine.patch` 是 `git -C xu4 diff HEAD` 產生的。兩個分支各自改引擎時,
**不要文字合併這個 patch 檔**(index 雜湊行、行偏移會假衝突)。正解:在 xu4 源碼層做
per-file 3-way merge(`git merge-file ours base theirs`),再從合併結果重新 `diff` 產生 patch。
注意 `git merge-file` 對「雙方都從共享 base 新增同一段」可能**重複**該段(編譯期才抓到
redefinition);遇到就改「取一方乾淨版 + 套另一方的小修」。

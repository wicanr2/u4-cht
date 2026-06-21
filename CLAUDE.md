# 評估 u4rematered.git 中文化
- 使用 SDL2 繪製圖形
- 支援 linux / windows 
- 確認需要哪些原始檔案(u4)
- 中文化可行性評工
- scan remastered source code @./u4remastered
- 搜尋相關訊息 關於這個 u4 remaster 
- 參考 u6-cht / u3-cht 專案風格尤其是 README.MD - 規劃 PLAN.md

# 中文化原則(踩過的坑,詳見 docs/cht-boron-cjk.md)
- **輸入比對只能用英文**:凡會被拿去跟玩家輸入比對的字串(`strcasecmp`/`strncasecmp`/
  `inputEq` 等),其 canonical 值**必須維持英文** —— 玩家無法在遊戲中輸入中文。
  翻譯只能用於「顯示」。作法:`getXxxName()` 回英文 canonical(比對/`[0]`首字母/`strlen`),
  另開 `getDisplayXxxName()` 回「中文(英文)」如 `正義(Justice)`,讓玩家知道要打什麼。
  已知適用:美德名(聖壇冥想/codex/城堡/item);**疑似同類待查:職業名 getClassName**。
- **字型 atlas 收字門檻 ≥0x80**:引擎對所有 codepoint ≥0x80 都查 atlas;漏收(如 `…`)會顯示灰框。
- **Boron 字串是 UCS2**:module(vendors.b 等)內 CJK 經 `cf_screenMessage` 須自行轉 UTF-8;
  `append` CJK 到空 Latin1 `""` 會有損降轉成 0xBF(灰框)→ 需 seed UCS2。
- **顯示路徑**:`%s` 引數不會被 `screenMessageN` 查表 → 需在來源(getter)自行 chtLookup;
  整串傳給 `screenMessage` 才會自動查表。`screenMessageCenter` 已改為先查表再依顯示格數置中。


/*
 * 回歸測試:Boron 字串 → C 端 UTF-8 的編碼轉換(對應 vendor 商店對白亂碼修復)。
 *
 * 背景:Boron 把含 CJK(codepoint 256–65535)的字串字面存成 UR_ENC_UCS2(每字
 * 16-bit);construct(vendor `=>` / input-shop 用)又沿用該編碼。修復前
 * script_boron.cpp:cf_screenMessage 直接把 buffer 的 ptr.c 當 UTF-8 byte 輸出,
 * UCS2 被誤讀 → 店家對白「怪怪的字 + 一堆空白」。修復:輸出前先轉 UTF-8。
 *
 * 本測試在真實 Boron 直譯器裡重現 vendor 情境(字面 + construct),用與修復後
 * cf_screenMessage 完全相同的轉碼法取出 UTF-8,逐 byte 比對預期值。
 *   - 同時斷言來源 buffer 確為 UCS2(證明舊路徑必錯,測試有意義)。
 *   - 退出碼 0 = 全過;非 0 = 有失敗。
 *
 * 編譯/執行見 tools/run_boron_cjk_test.sh(於 u4cht/xu4-allegro image 內,
 * 該 image 已含 libboron + headers)。
 */
#include <boron/boron.h>
#include <cstdio>
#include <cstring>
#include <string>

static int failures = 0;

static void appendUtf8(std::string& out, uint32_t cp) {
    if (cp < 0x80) { out += (char) cp; }
    else if (cp < 0x800) {
        out += (char) (0xC0 | (cp >> 6));
        out += (char) (0x80 | (cp & 0x3F));
    } else if (cp < 0x10000) {
        out += (char) (0xE0 | (cp >> 12));
        out += (char) (0x80 | ((cp >> 6) & 0x3F));
        out += (char) (0x80 | (cp & 0x3F));
    } else {
        out += (char) (0xF0 | (cp >> 18));
        out += (char) (0x80 | ((cp >> 12) & 0x3F));
        out += (char) (0x80 | ((cp >> 6) & 0x3F));
        out += (char) (0x80 | (cp & 0x3F));
    }
}

/* 與修復後 cf_screenMessage 相同的轉碼:Boron 字串 cell → UTF-8 C 字串。 */
static std::string boronStrToUtf8(UThread* ut, const UCell* cell, bool* wasUcs2) {
    USeriesIter si;
    ur_seriesSlice(ut, &si, cell);
    if (wasUcs2)
        *wasUcs2 = ur_strIsUcs2(si.buf);

    std::string out;
    if (si.buf->form == UR_ENC_UCS2) {
        const uint16_t* s = si.buf->ptr.u16;
        for (UIndex i = si.it; i < si.end; ++i) appendUtf8(out, s[i]);
    } else if (si.buf->form == UR_ENC_UTF8) {
        out.assign(si.buf->ptr.c + si.it, si.end - si.it);
    } else {
        const uint8_t* s = si.buf->ptr.b;
        for (UIndex i = si.it; i < si.end; ++i) appendUtf8(out, s[i]);
    }
    return out;
}

/* 評估一段 Boron,回傳結果 cell(失敗回 NULL)。 */
static const UCell* eval(UThread* ut, const char* src) {
    return boron_evalUtf8(ut, src, (int) strlen(src));
}

static void check(UThread* ut, const char* desc, const char* src,
                  const char* expectUtf8) {
    const UCell* r = eval(ut, src);
    if (! r || ! ur_is(r, UT_STRING)) {
        printf("FAIL  %-22s eval 未得 string!:%s\n", desc, src);
        ++failures;
        return;
    }
    bool ucs2 = false;
    std::string got = boronStrToUtf8(ut, r, &ucs2);

    bool ok = (got == expectUtf8);
    printf("%s  %-22s ucs2=%d  got=\"%s\"  expect=\"%s\"\n",
           ok ? "PASS" : "FAIL", desc, ucs2 ? 1 : 0,
           got.c_str(), expectUtf8);
    if (! ok)
        ++failures;

    /* 含 CJK 的來源必為 UCS2 —— 證明舊的「直接讀 ptr.c」路徑會壞,本測試才有意義。
     * 若 Boron 改變編碼策略使其非 UCS2,本測試雖可能仍 PASS 卻失去覆蓋舊 bug 觸發條件
     * 的意義 → 視為失敗,逼 CI 正視。 */
    if (! ucs2) {
        printf("FAIL  %-22s 來源非 UCS2 → 失去舊 bug 觸發條件覆蓋\n", desc);
        ++failures;
    }
}

int main() {
    UEnvParameters param;
    UThread* ut = boron_makeEnv(boron_envParam(&param));
    if (! ut) {
        printf("FAIL  boron_makeEnv 失敗\n");
        return 2;
    }

    /* 1) 純字面(vendor 一般招呼語走純 `>>`)。 */
    check(ut, "literal-cjk", "\"歡迎光臨\"", "歡迎光臨");

    /* 2) construct(vendor `=>` / input-shop 的價格描述)—— $ 代入價格。 */
    check(ut, "construct-price",
          "construct \"僅售 $gp。\" ['$' 300]", "僅售 300gp。");

    /* 3) construct 多佔位(店名 @ / 店主 % / 價格 $)。 */
    check(ut, "construct-multi",
          "construct \"@ 的 % 說:$gp\" ['@' \"溫莎兵器行\" '%' \"溫斯頓\" '$' 20]",
          "溫莎兵器行 的 溫斯頓 說:20gp");

    /* 4) 行首換行 + 中文(舊 bug 下 ^/=0x0A0x00 會立即 NUL 截斷成空白)。 */
    check(ut, "leading-newline", "\"^/要嗎? \"", "\n要嗎? ");

    boron_freeEnv(ut);

    printf("\n%s  失敗 %d 項\n", failures ? "==== 測試未通過 ====" : "==== 全數通過 ====",
           failures);
    return failures ? 1 : 0;
}

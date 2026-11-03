// 回歸測試:載入 u4_cht.tab 後,拿來和玩家輸入比對的名稱必須維持英文,
// 顯示用的名稱才翻譯。規則見 docs/cht-boron-cjk.md「輸入比對」。
//
// 這類錯誤在只有英文的環境看不出來:沒載入對照表時 chtLookup 回傳 NULL,
// 所以測試第一步先確認對照表真的載入了。
#include <cstdio>
#include <cstring>

#include "cht.h"
#include "names.h"

static int gFail = 0;

static void eq(const char* what, const char* got, const char* want) {
    if (strcmp(got, want) != 0) {
        printf("FAIL %s: got [%s], want [%s]\n", what, got, want);
        ++gFail;
    }
}

int main() {
    chtInit();
    const char* truth = chtLookup("Truth", 5);
    if (! truth || strcmp(truth, "Truth") == 0) {
        printf("FAIL u4_cht.tab 沒有載入,測試不成立(請設定 U4CHT_DIR)\n");
        return 2;
    }

    static const char* const virtues[8] = {
        "Honesty", "Compassion", "Valor", "Justice",
        "Sacrifice", "Honor", "Spirituality", "Humility"
    };
    static const char* const stones[8] = {
        "Blue", "Yellow", "Red", "Green", "Orange", "Purple", "White", "Black"
    };
    for (int i = 0; i < 8; ++i) {
        eq("getVirtueName", getVirtueName((Virtue) i), virtues[i]);
        eq("getStoneName", getStoneName((Virtue) i), stones[i]);
    }

    eq("getBaseVirtueName", getBaseVirtueName(VIRT_TRUTH), "Truth");
    eq("getBaseVirtueName", getBaseVirtueName(VIRT_LOVE), "Love");
    eq("getBaseVirtueName", getBaseVirtueName(VIRT_COURAGE), "Courage");

    // 顯示端仍要是中文。
    eq("getDisplayBaseVirtueName", getDisplayBaseVirtueName(VIRT_TRUTH), truth);
    eq("getDisplayVirtueName", getDisplayVirtueName(VIRT_HONESTY), "誠實(Honesty)");

    if (gFail) {
        printf("%d 項失敗\n", gFail);
        return 1;
    }
    printf("OK\n");
    return 0;
}

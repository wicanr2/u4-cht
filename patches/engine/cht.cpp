/*
 * U4 繁中化(cht):en→zh lookup + CJK 點陣字 glyph。
 * 純載入/查表,不依賴引擎其他模組。資產由 cwd / U4CHT_DIR 載入。
 */
#include "cht.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

struct Pair { std::string en, zh; };
std::vector<Pair> gTable;                 // 依 en bytes 升序
std::vector<uint32_t> gCodes;             // 依 codepoint 升序
std::vector<const uint8_t*> gGlyphPtr;
uint8_t* gGlyphData = NULL;
int gDim = 16;
bool gLoaded = false;

FILE* openAsset(const char* name) {
    char path[600];
    const char* env = getenv("U4CHT_DIR");
    const char* dirs[3] = { "", "/build/xu4/", env };
    for (int i = 0; i < 3; ++i) {
        if (i == 2 && !env) continue;
        snprintf(path, sizeof(path), "%s%s", dirs[i] ? dirs[i] : "", name);
        FILE* f = fopen(path, "rb");
        if (f) return f;
    }
    return NULL;
}

bool rd(FILE* f, void* p, size_t n) { return fread(p, 1, n, f) == n; }

void loadLookup() {
    FILE* f = openAsset("u4_cht.tab");
    if (!f) { fprintf(stderr, "cht: u4_cht.tab not found\n"); return; }
    char magic[8];
    uint32_t count = 0;
    if (!rd(f, magic, 8) || !rd(f, &count, 4)) { fclose(f); return; }
    gTable.reserve(count);
    for (uint32_t i = 0; i < count; ++i) {
        uint16_t el = 0, zl = 0;
        if (!rd(f, &el, 2)) break;
        std::string en(el, '\0'); if (el && !rd(f, &en[0], el)) break;
        if (!rd(f, &zl, 2)) break;
        std::string zh(zl, '\0'); if (zl && !rd(f, &zh[0], zl)) break;
        Pair p; p.en.swap(en); p.zh.swap(zh);
        gTable.push_back(p);
    }
    fclose(f);
    fprintf(stderr, "cht: loaded %zu translations\n", gTable.size());
}

/* 字形切換:env U4CHT_FONT 選 atlas(noto 預設 / firefly / kai) */
static const char* fontFile() {
    const char* sel = getenv("U4CHT_FONT");
    if (sel) {
        if (!strcmp(sel, "firefly") || !strcmp(sel, "sung"))
            return "cjk_font_firefly.bin";
        if (!strcmp(sel, "kai"))
            return "cjk_font_kai.bin";
    }
    return "cjk_font.bin";
}

void loadFont() {
    const char* fname = fontFile();
    FILE* f = openAsset(fname);
    if (!f) { fprintf(stderr, "cht: %s not found\n", fname); return; }
    fprintf(stderr, "cht: font = %s\n", fname);
    char magic[8];
    uint16_t W = 0, H = 0;
    uint32_t count = 0;
    if (!rd(f, magic, 8) || !rd(f, &W, 2) || !rd(f, &H, 2) || !rd(f, &count, 4)) {
        fclose(f); return;
    }
    gDim = W;
    size_t gb = (size_t) W * H;
    gGlyphData = (uint8_t*) malloc((size_t) count * gb);
    if (!gGlyphData) { fclose(f); return; }
    gCodes.reserve(count); gGlyphPtr.reserve(count);
    for (uint32_t i = 0; i < count; ++i) {
        uint32_t cp = 0;
        if (!rd(f, &cp, 4)) break;
        uint8_t* dst = gGlyphData + (size_t) i * gb;
        if (!rd(f, dst, gb)) break;
        gCodes.push_back(cp);
        gGlyphPtr.push_back(dst);
    }
    fclose(f);
    fprintf(stderr, "cht: loaded %zu glyphs (%dx%d)\n", gCodes.size(), W, H);
}

} // namespace

void chtInit(void) {
    if (gLoaded) return;
    gLoaded = true;
    loadLookup();
    loadFont();
}

const char* chtLookup(const char* en, int len) {
    if (gTable.empty()) return NULL;
    std::string key(en, len);
    int lo = 0, hi = (int) gTable.size() - 1;
    while (lo <= hi) {
        int mid = (lo + hi) >> 1;
        int cmp = gTable[mid].en.compare(key);
        if (cmp == 0) return gTable[mid].zh.c_str();
        if (cmp < 0) lo = mid + 1; else hi = mid - 1;
    }
    return NULL;
}

const uint8_t* chtGlyph(uint32_t cp) {
    int lo = 0, hi = (int) gCodes.size() - 1;
    while (lo <= hi) {
        int mid = (lo + hi) >> 1;
        if (gCodes[mid] == cp) return gGlyphPtr[mid];
        if (gCodes[mid] < cp) lo = mid + 1; else hi = mid - 1;
    }
    return NULL;
}

int chtGlyphDim(void) { return gDim; }

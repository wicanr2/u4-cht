#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把四份雙語表合併成單一 en→zh 二進位 lookup(byte-safe、length-prefixed、依 en 排序),
供 xu4 引擎在 H1 screenMessageN load-time 查表。

輸出 assets/u4_cht.tab:
  magic[8]  "U4LK\0\1\0\0"
  uint32    count
  records[count](依 en bytes 升序,引擎二分查找):
    uint16 en_len + en bytes (UTF-8)
    uint16 zh_len + zh bytes (UTF-8)

用法:
  python3 tools/build_lookup.py --out assets/u4_cht.tab
"""
import argparse
import json
import os
import struct


def collect():
    pairs = {}  # en -> zh(後到不覆蓋已有非空)

    def add(en, zh):
        if not en or not zh:
            return
        if en == zh:
            return  # 無翻譯意義(控制字串)
        if en not in pairs:
            pairs[en] = zh

    # talk:每 NPC 每欄位
    d = json.load(open("dumps/talk_bilingual.json", encoding="utf-8"))
    for n in d["npcs"]:
        for f, v in n["fields"].items():
            if f in ("keyword_1", "keyword_2"):
                continue
            add(v["en"], v["zh"])
    # stringtable
    d = json.load(open("dumps/stringtable_bilingual.json", encoding="utf-8"))
    for sec, sd in d["sections"].items():
        for e in sd["entries"]:
            add(e["en"], e["zh"])
            # intro_gypsy:引擎在 intro.cpp 載入後會 pop 掉結尾 \n,runtime 字串
            # 與含 \n 的 key 不符 → 補一份去尾 \n 的 variant 才查得到。
            if sec == "intro_gypsy":
                en2, zh2 = e["en"].rstrip("\n"), e["zh"].rstrip("\n")
                if en2 != e["en"]:
                    add(en2, zh2)
    # hardcoded
    d = json.load(open("dumps/hardcoded_strings.json", encoding="utf-8"))
    for e in d["strings"]:
        add(e["en"], e["zh"])
    # vendor
    d = json.load(open("dumps/vendor_bilingual.json", encoding="utf-8"))
    for e in d["strings"]:
        add(e["en"], e["zh"])
    # castle:Lord British 城堡對白(discourse_castle.cpp,自 avatar.exe 載入)
    try:
        d = json.load(open("dumps/castle_bilingual.json", encoding="utf-8"))
        for e in d["strings"]:
            add(e["en"], e["zh"])
    except FileNotFoundError:
        pass
    # UI(intro 選單 / 角色創建 / prompt,TextView::textAt)
    try:
        d = json.load(open("dumps/ui_bilingual.json", encoding="utf-8"))
        for e in d["strings"]:
            add(e["en"], e["zh"])
    except FileNotFoundError:
        pass
    # config(武器/防具名 + stats 標題,TextView::textAt / setTitle)
    # names(職業/試劑/美德/物品/方向)、creature(怪物名)、system(系統/戰鬥/面板訊息)
    for src in ("config_bilingual", "names_bilingual",
                "creature_bilingual", "system_bilingual",
                "location_types",      # 進城型別字 castle/towne/village/ruins
                "maps_bilingual"):     # maps.b 樓層/地城訊息 + 城市/地城名(置中顯示)
        try:
            d = json.load(open(f"dumps/{src}.json", encoding="utf-8"))
            for e in d["strings"]:
                add(e["en"], e["zh"])
        except FileNotFoundError:
            pass
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pairs = collect()
    items = sorted(pairs.items(), key=lambda kv: kv[0].encode("utf-8"))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(b"U4LK\0\1\0\0")
        f.write(struct.pack("<I", len(items)))
        for en, zh in items:
            eb = en.encode("utf-8")
            zb = zh.encode("utf-8")
            f.write(struct.pack("<H", len(eb))); f.write(eb)
            f.write(struct.pack("<H", len(zb))); f.write(zb)
    sz = os.path.getsize(args.out)
    print(f"lookup 條目: {len(items)}  → {args.out} ({sz} bytes)")
    # 抽樣驗證
    for en, zh in items[:2]:
        print("  e.g.", repr(en[:40]), "→", repr(zh[:30]))


if __name__ == "__main__":
    main()

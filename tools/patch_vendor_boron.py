#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 xu4 module vendors.b 的英文 vendor 模板字串就地換成中文(module 層中文化)。

原理:vendor `>>` → cf_screenMessage → screenMessage();但 Boron `construct` 在
screenMessage 前就把佔位符 @ % $ # = 代入,故 en lookup 不命中。解法是讓模組本身
帶中文模板 —— construct 填入中文模板,screenMessage 收到中文 → 引擎 CJK 渲染。

用 dumps/vendor_bilingual.json 的 en→zh,對 vendors.b 的 "…"/{…} 字串原地替換;
佔位符 @ % $ # = 與 ^/(換行)保留。

用法:
  python3 tools/patch_vendor_boron.py \
      --vendors xu4/module/Ultima-IV/vendors.b \
      --bilingual dumps/vendor_bilingual.json
"""
import argparse
import json
import re

CARET = {"/": "\n", "-": "\t", '"': '"', "^": "^", "{": "{", "}": "}",
         "(": "(", ")": ")"}


def decode(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == "^" and i + 1 < len(s):
            out.append(CARET.get(s[i + 1], s[i + 1])); i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)


def encode(s):
    """zh → Boron(\\n→^/, ^→^^);保留佔位符。"""
    out = []
    for ch in s:
        if ch == "\n":
            out.append("^/")
        elif ch == "^":
            out.append("^^")
        else:
            out.append(ch)
    return "".join(out)


def find_strings(text):
    """回傳 [(start, end, kind, decoded)] —— start/end 為含分隔符的 raw span。"""
    res = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if c == "'":
            i += 1; continue
        if c == '"':
            start = i; i += 1; buf = []
            while i < n and text[i] != '"':
                if text[i] == "^" and i + 1 < n:
                    buf.append(text[i]); buf.append(text[i+1]); i += 2; continue
                buf.append(text[i]); i += 1
            i += 1
            res.append((start, i, "quote", decode("".join(buf))))
            continue
        if c == "{":
            start = i; depth = 0; buf = []
            while i < n:
                ch = text[i]
                if ch == "^" and i + 1 < n:
                    buf.append(ch); buf.append(text[i+1]); i += 2; continue
                if ch == "{":
                    depth += 1
                    if depth > 1: buf.append(ch)
                    i += 1; continue
                if ch == "}":
                    depth -= 1
                    if depth == 0: i += 1; break
                    buf.append(ch); i += 1; continue
                buf.append(ch); i += 1
            dec = decode("".join(buf))
            st = dec.strip()
            if st.startswith("{") and st.endswith("}"):
                dec = st[1:-1]
            res.append((start, i, "brace", dec))
            continue
        i += 1
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vendors", required=True)
    ap.add_argument("--bilingual", required=True)
    args = ap.parse_args()

    text = open(args.vendors, encoding="utf-8").read()
    bil = json.load(open(args.bilingual, encoding="utf-8"))
    en2zh = {e["en"]: e["zh"] for e in bil["strings"] if e.get("zh")}

    spans = find_strings(text)
    repls = []
    hit = 0
    for start, end, kind, dec in spans:
        zh = en2zh.get(dec)
        if not zh or zh == dec:
            continue
        enc = encode(zh)
        new = ('"' + enc + '"') if kind == "quote" else ('{' + enc + '}')
        repls.append((start, end, new))
        hit += 1

    # 反向套用,保 offset
    for start, end, new in sorted(repls, reverse=True):
        text = text[:start] + new + text[end:]

    # ── 中文化的結構性副作用修正(與翻譯內容無關,但 CJK 才會現形)──
    # (1) 去掉每行(^/ 之後)前導縮排空白:原 {{ }} 模板的原始碼縮排,在 CJK 全形
    #     (CHAR_WIDTH=24、文字區僅 16 欄)下會把整段嚴重右移。
    text, indent = re.subn(r"\^/[ \t]+", "^/", text)

    # (2) build-items 的 inventory:`inventory: ""` 是空 Latin1 字串,append CJK 物品名
    #     會被 Boron 有損降轉成 0xBF(顯示為缺字灰框)。種 1 個全形空白使 buffer 為
    #     UCS2(build-items 會先 clear,種子不顯示),其後 append 維持 UCS2。
    seed = 'inventory: "　"   ; 種 UCS2,使 append CJK 物品名不被降轉(見 patch_vendor_boron.py)'
    text = text.replace('inventory: ""', seed)
    # (3) 同上:rejoin 以 char(uppercase key)起頭會先成 Latin1 buffer,name 隨即降轉。
    #     改為逐段 append 到已是 UCS2 的 inventory。
    text = text.replace(
        "        append inventory rejoin [uppercase key ' ' name '^/']",
        '        append inventory uppercase key\n'
        '        append inventory " "\n'
        '        append inventory name\n'
        '        append inventory "^/"')

    open(args.vendors, "w", encoding="utf-8").write(text)
    print(f"vendors.b 字串替換: {hit} / {len(spans)} 個;去前導縮排 {indent} 處;"
          f"inventory UCS2 seed + 逐段 append")


if __name__ == "__main__":
    main()

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
        if kind == "brace":
            # 上游用雙括號 {{ }} 字串,Boron 解析時會去縮排(剝除每行行首空白)。
            # 本工具一律輸出單括號 { },不會去縮排,故 zh 內鏡射原始碼版面的行首
            # 縮排會被當成實際空白印出(各 vendor 對白整段右推、亂折行)。在此自行
            # 去縮排,等價於 {{ }} 行為:剝除每個換行後的行首空白。
            zh = re.sub(r"\n[ \t]+", "\n", zh)
        enc = encode(zh)
        new = ('"' + enc + '"') if kind == "quote" else ('{' + enc + '}')
        repls.append((start, end, new))
        hit += 1

    # 反向套用,保 offset
    for start, end, new in sorted(repls, reverse=True):
        text = text[:start] + new + text[end:]

    # build-items 的 inventory 緩衝修正(CJK 品名顯示)。
    # Boron 的 Latin1 字串只在設了 ENC_UP 旗標時才會自動加寬成 UCS-2;字面 ""
    # 是 Latin1 無此旗標,append 含 CJK(碼位>255)的品名會被窄化成 '¿'(武器/防具
    # 行品名全空白)。且 rejoin 會先以 char(key)建一個 Latin1 中介字串,品名在併入
    # 時即被窄化。故:(1) 以含 CJK 的字面建 UCS-2 緩衝(clear 保留 form);
    # (2) 逐段直接 append,不經 rejoin。
    text = text.replace(
        'inventory: ""',
        'inventory: "　"   ; 全形空白 → UCS-2 緩衝;clear 保留 form(見下)',
        1,
    )
    text = text.replace(
        "append inventory rejoin [uppercase key ' ' name '^/']",
        "append append append append inventory uppercase key ' ' name '^/'",
        1,
    )

    open(args.vendors, "w", encoding="utf-8").write(text)
    print(f"vendors.b 字串替換: {hit} / {len(spans)} 個")


if __name__ == "__main__":
    main()

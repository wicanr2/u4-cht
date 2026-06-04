#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抽取 xu4 / DOS Ultima IV 的 .TLK NPC 對話,並對齊 u4remastered talk.json,
產出雙語表雛形(en 來自 DOS .TLK,zh 待填)+ 對齊/差異報告。

不改引擎、不碰遊戲二進位。格式依 xu4 `src/discourse_tlk.cpp` U4Talk_load:
  每個 .TLK = 16 record × 288 byte。
  record: byte0=askAfter, byte1=questionHumility, byte2=turnAway,
          其後 12 個 null 結尾字串(offset 3 起):
          name, pronoun, look, job, health, response1, response2,
          question, yes, no, topic1, topic2

用法:
  python3 tools/extract_tlk.py \
      --tlk-dir data/tlk \
      --talk-json u4remastered/src/talk/talk.json \
      --out-bilingual dumps/talk_bilingual.json \
      --out-report dumps/talk_alignment_report.md
"""
import argparse
import json
import os
import re

TLK_SIZE = 288
RECORDS_PER_FILE = 16

# DOS .TLK 欄位 → talk.json 欄位 對應
FIELD_MAP = [
    ("name", "name"),
    ("pronoun", "pronoun"),
    ("look", "description"),
    ("job", "job"),
    ("health", "health"),
    ("response1", "keyword_response_1"),
    ("response2", "keyword_response_2"),
    ("question", "question"),
    ("yes", "question_yes_answer"),
    ("no", "question_no_answer"),
    ("topic1", "keyword_1"),
    ("topic2", "keyword_2"),
]
STRING_FIELDS = [t for t, _ in FIELD_MAP]  # 12 個


# 需補 "a " 冠詞的角色(對齊 xu4 U4Talk_load EDIT_A)
_ARTICLE_NAMES = {"Iolo", "Tracie", "Dupre", "Traveling Dan"}


def edit_look(look, name):
    """複製 xu4 U4Talk_load 對 description(look)的執行時修飾:
    小寫首字 → \\n 換空白 → 補句點 → 特定角色補 'a '。
    使 en 等於引擎實際輸出(= H1 hook 的 lookup key)。"""
    if not look:
        return look
    s = look[0].lower() + look[1:]
    s = s.replace("\n", " ")
    if s and s[-1] not in ".,!?;:":
        s = s + "."
    if name in _ARTICLE_NAMES:
        s = "a " + s
    return s


def parse_record(buf):
    """解一個 288-byte record → dict(欄位 → str)+ header。回傳 None 表示空 NPC。"""
    askAfter, questionHumility, turnAway = buf[0], buf[1], buf[2]
    body = buf[3:]
    parts = body.split(b"\x00")
    # 取前 12 段,以 latin-1 解(原版單位元組);trail 不足補空字串
    vals = []
    for i in range(12):
        raw = parts[i] if i < len(parts) else b""
        vals.append(raw.decode("latin-1"))
    rec = {STRING_FIELDS[i]: vals[i] for i in range(12)}
    if not rec["name"].strip():
        return None  # 空槽
    # description(look)套用引擎執行時修飾
    rec["look"] = edit_look(rec["look"], rec["name"])
    rec["_askAfter"] = askAfter
    rec["_questionHumility"] = questionHumility
    rec["_turnAway"] = turnAway
    return rec


def extract_tlk_dir(tlk_dir):
    out = []
    for fn in sorted(os.listdir(tlk_dir)):
        if not fn.lower().endswith(".tlk"):
            continue
        data = open(os.path.join(tlk_dir, fn), "rb").read()
        town = os.path.splitext(fn)[0].upper()
        for idx in range(RECORDS_PER_FILE):
            off = idx * TLK_SIZE
            chunk = data[off:off + TLK_SIZE]
            if len(chunk) < TLK_SIZE:
                break
            rec = parse_record(chunk)
            if rec is None:
                continue
            rec["_tlk_file"] = town
            rec["_conv_index"] = idx
            out.append(rec)
    return out


def norm(s):
    """寬鬆比對:壓平空白、去頭尾、小寫。"""
    return re.sub(r"\s+", " ", s or "").strip().lower()


def build_bilingual(tlk_records, talk_json):
    """以 name 對齊 talk.json;產出雙語表 + 報告資料。"""
    # talk.json: list[dict],以 name 建索引(可能重名,存 list)
    by_name = {}
    for e in talk_json:
        by_name.setdefault(norm(e.get("name", "")), []).append(e)

    bilingual = []
    report = {"matched": 0, "name_only": 0, "no_match": 0,
              "text_diffs": [], "no_match_list": []}

    used = set()
    for rec in tlk_records:
        key = norm(rec["name"])
        cand = by_name.get(key, [])
        # 取尚未用過的第一個同名
        match = None
        for i, c in enumerate(cand):
            cid = id(c)
            if cid not in used:
                match = c
                used.add(cid)
                break
        entry = {
            "tlk_file": rec["_tlk_file"],
            "conv_index": rec["_conv_index"],
            "name": rec["name"],
            "talk_json_matched": bool(match),
            "header": {
                "askAfter": rec["_askAfter"],
                "questionHumility": rec["_questionHumility"],
                "turnAway": rec["_turnAway"],
            },
            "fields": {},
        }
        diffs = []
        for tlk_f, tj_f in FIELD_MAP:
            en = rec[tlk_f]
            tj_val = match.get(tj_f, "") if match else ""
            # zh 雛形:預設空字串待填;keyword(topic)通常不譯,先帶原值
            zh = ""
            entry["fields"][tj_f] = {"en": en, "zh": zh}
            if match and norm(en) != norm(str(tj_val)):
                diffs.append({"field": tj_f, "tlk_en": en, "talk_json": tj_val})
        if match:
            if diffs:
                report["matched"] += 1
                report["text_diffs"].append(
                    {"name": rec["name"], "tlk_file": rec["_tlk_file"], "diffs": diffs})
            else:
                report["matched"] += 1
        else:
            report["no_match"] += 1
            report["no_match_list"].append({
                "tlk_file": rec["_tlk_file"], "conv_index": rec["_conv_index"],
                "name_field": rec["name"], "job": rec["job"]})
        bilingual.append(entry)

    return bilingual, report


def write_report(report, tlk_n, talk_n, path):
    lines = []
    lines.append("# .TLK ↔ talk.json 對齊報告\n")
    lines.append(f"> 自動產生 by `tools/extract_tlk.py`\n")
    lines.append("## 摘要\n")
    lines.append(f"- DOS `.TLK` 抽出 NPC:**{tlk_n}**")
    lines.append(f"- u4remastered `talk.json` 條目:**{talk_n}**")
    lines.append(f"- 以 name 對齊成功:**{report['matched']}**")
    lines.append(f"- 找不到對應(僅 .TLK 有):**{report['no_match']}**")
    nd = len(report["text_diffs"])
    lines.append(f"- 英文內容有差異的 NPC(remaster 修過對白 / 格式):**{nd}**\n")
    if report["no_match_list"]:
        lines.append("## 無對應 NPC(DOS .TLK name 欄位異常,疑似 remaster 修過的 broken dialogue)\n")
        lines.append("這些 record 的 `name` 欄位實際是描述片語,需人工依 town/index 對 talk.json 核對。\n")
        lines.append("| TLK | idx | name 欄位(原始) | job |")
        lines.append("|---|---|---|---|")
        for m in report["no_match_list"]:
            nf = re.sub(r"\s+", " ", m["name_field"]).strip()
            jb = re.sub(r"\s+", " ", m["job"]).strip()
            lines.append(f"| {m['tlk_file']} | {m['conv_index']} | `{nf}` | `{jb[:40]}` |")
        lines.append("")
    lines.append("## 英文差異明細(前 40 筆)\n")
    lines.append("差異多源於 u4remastered 修正對白 bug 與 C64 16-col 換行;"
                 "**翻譯底本以 DOS `.TLK` 的 en 為準**(引擎實際輸出),talk.json 作參考。\n")
    for d in report["text_diffs"][:40]:
        lines.append(f"### {d['name']} ({d['tlk_file']})")
        for x in d["diffs"]:
            tlk = re.sub(r"\s+", " ", x["tlk_en"]).strip()
            tj = re.sub(r"\s+", " ", str(x["talk_json"])).strip()
            lines.append(f"- `{x['field']}`:")
            lines.append(f"    - TLK: `{tlk[:120]}`")
            lines.append(f"    - JSON: `{tj[:120]}`")
        lines.append("")
    open(path, "w", encoding="utf-8").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tlk-dir", required=True)
    ap.add_argument("--talk-json", required=True)
    ap.add_argument("--out-bilingual", required=True)
    ap.add_argument("--out-report", required=True)
    args = ap.parse_args()

    tlk_records = extract_tlk_dir(args.tlk_dir)
    talk_json = json.load(open(args.talk_json, encoding="utf-8"))
    talk_json = [e for e in talk_json if str(e.get("name", "")).strip()]

    bilingual, report = build_bilingual(tlk_records, talk_json)

    os.makedirs(os.path.dirname(args.out_bilingual), exist_ok=True)
    meta = {
        "_meta": {
            "source_tlk": "DOS Ultima IV .TLK (ultima4.zip)",
            "reference": "u4remastered/src/talk/talk.json",
            "npc_count": len(bilingual),
            "field_map": dict(FIELD_MAP),
            "note": "en = DOS .TLK 原文(引擎實際輸出,翻譯 key);zh 待填。keyword(topic)預設不譯。",
        },
        "npcs": bilingual,
    }
    json.dump(meta, open(args.out_bilingual, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    write_report(report, len(tlk_records), len(talk_json), args.out_report)

    print(f"NPC 抽出: {len(tlk_records)}  /  talk.json: {len(talk_json)}")
    print(f"對齊成功: {report['matched']}  無對應: {report['no_match']}  "
          f"有英文差異: {len(report['text_diffs'])}")
    print(f"→ {args.out_bilingual}")
    print(f"→ {args.out_report}")


if __name__ == "__main__":
    main()

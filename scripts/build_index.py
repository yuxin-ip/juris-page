# -*- coding: utf-8 -*-
"""从全书 OCR(jsonl) 构建 罪名/考点 -> 印刷页码 索引。
标题层级匹配 + 行合并 + 一行多考点 + 顿号归一化。
印刷页码 = PDF索引 - OFFSET。
"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"D:\code\juris_page"

BOOK = sys.argv[1] if len(sys.argv) > 1 else "beisong"
if BOOK == "jingjiang":
    OFFSET = 21
    IN_PATH = base + r"\data\ocr_jingjiang_xingfa.jsonl"
    OUT_PATH = base + r"\data\index_jingjiang.json"
    START_IDX = 24  # 跳过目录(idx16-20)与体系图(idx22-23)
else:
    OFFSET = 5
    IN_PATH = base + r"\data\ocr_beisong_xingfa.jsonl"
    OUT_PATH = base + r"\data\index_beisong.json"
    START_IDX = 8   # 跳过封面/使用说明/目录(idx0-7)

lex = json.load(open(base + r"\data\xingfa_lexicon.json", encoding="utf-8"))
kw_list = []
for cat in lex["分则"].values():
    kw_list += cat
for cat in lex["总论"].values():
    kw_list += cat
kw_list = sorted(set(kw_list), key=len, reverse=True)
KW_SET = set(kw_list)

def norm(s):
    """只去顿号，消除“拐卖妇女、儿童罪”写法差异；保留逗号避免跨句误匹配"""
    return s.replace("、", "")

def load_pages(path):
    pages = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            lines = [{"t": ln["t"].strip(), "y": ln["y"], "x": ln["x"]} for ln in d["lines"]]
            pages.append({"page": d["page"], "lines": lines})
    return pages

def merge_lines(lines, y_thresh=16, max_merge_len=15):
    """合并同一水平线（y 接近）的分栏行；长行不参与合并（避免“短标签+长正文”误合并）"""
    lines = sorted(lines, key=lambda l: (l["y"], l["x"]))
    groups = []
    for ln in lines:
        t = re.sub(r"\s+", "", ln["t"])
        if len(t) > max_merge_len:
            groups.append([ln])
            continue
        if groups and abs(ln["y"] - groups[-1][-1]["y"]) <= y_thresh:
            groups[-1].append(ln)
        else:
            groups.append([ln])
    merged = []
    for g in groups:
        g = sorted(g, key=lambda l: l["x"])
        merged.append("".join(l["t"] for l in g))
    return merged

def level_beisong(t):
    """背诵一本通标题层级（真标题都短，正文列举被长度过滤）"""
    L = len(t)
    if "简述" in t and L <= 45:
        return 3
    if re.match(r"^第[一二三四五六七八九十百]+[章节]", t) and L <= 20:
        return 2.5
    if re.match(r"^[一二三四五六七八九十]+、", t) and L <= 20:
        return 2
    if re.match(r"^\d+[.．、]", t) and L <= 12:
        return 1.5
    if re.match(r"^[（(][一二三四五六七八九十\d]+[）)]", t) and L <= 12:
        return 1
    return 0

def level_jingjiang(t):
    """精讲一本通标题层级"""
    L = len(t)
    if re.match(r"^第[一二三四五六七八九十百]+章", t) and L <= 24:
        return 4
    if re.match(r"^第[一二三四五六七八九十百]+节", t) and L <= 20:
        return 3
    if re.match(r"^[一二三四五六七八九十]+、", t) and L <= 20:
        return 2
    if re.match(r"^\d+[.．、]", t) and L <= 12:
        return 1.5
    if re.match(r"^[（(][一二三四五六七八九十\d]+[）)]", t) and L <= 12:
        return 1
    return 0

def is_bare_title(t):
    """裸行加粗标题：短行且以‘罪’结尾，或短行恰好是某关键词"""
    tn = norm(t)
    if 2 <= len(tn) <= 8 and tn.endswith("罪"):
        return True
    if 2 <= len(tn) <= 5 and tn in KW_SET:
        return True
    return False

def build(pages, kw_list, start_idx=0, level_fn=None):
    index = {}
    for p in pages:
        if p["page"] < start_idx:
            continue
        for line in merge_lines(p["lines"]):
            t = re.sub(r"\s+", "", line)
            if not t or len(t) > 45:
                continue
            tn = norm(t)
            lv = level_fn(t) if level_fn else level_beisong(t)
            if lv <= 0:
                lv = 0.5 if is_bare_title(t) else 0
            if lv <= 0:
                continue
            hits = [kw for kw in kw_list if norm(kw) in tn]
            if not hits:
                continue
            # 一行多考点都建索引，但跳过“被更长词完全包含”的子串词
            hits = sorted(hits, key=len, reverse=True)
            chosen = []
            for h in hits:
                if any(h in c for c in chosen):
                    continue
                chosen.append(h)
            for h in chosen:
                cur = index.get(h)
                if cur is None or lv > cur[0] or (lv == cur[0] and p["page"] < cur[1]):
                    index[h] = (lv, p["page"])
    return {k: v[1] for k, v in index.items()}

if __name__ == "__main__":
    pages = load_pages(IN_PATH)
    print(f"[{BOOK}] 已加载页数", len(pages))
    if BOOK == "jingjiang":
        idx = build(pages, kw_list, start_idx=START_IDX, level_fn=level_jingjiang)
    else:
        idx = build(pages, kw_list, start_idx=START_IDX, level_fn=level_beisong)
    printed = {k: (v - OFFSET) for k, v in idx.items()}
    json.dump(printed, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[{BOOK}] 已匹配关键词数", len(printed), "/", len(kw_list))
    for k in ["诈骗罪","盗窃罪","抢劫罪","故意杀人罪","正当防卫","犯罪未遂","共同犯罪","数罪并罚","贪污罪","受贿罪","累犯","自首","直接故意","间接故意","从犯","主犯","拐卖妇女儿童罪","聚众斗殴罪","徇私枉法罪"]:
        print(f"  {k}: P.{printed.get(k,'未匹配')}")

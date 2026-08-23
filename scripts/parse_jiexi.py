# -*- coding: utf-8 -*-
"""解析基础课解析PDF（文本型）-> 结构化题目JSON（兼容各年份括号/编号变体）"""
import sys, io, os, re, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r"D:/code/juris_page"
tdir = base + r"\法硕小程序开发\考研法硕历年真题，法学+非法学\09.法硕非法学历年真题\02.法硕（非法学）基础课解析（2010-2024）\02.法硕（非法学）基础课解析（2010-2024）"

NUM = r"([0-9lI]{1,2})"
BR_O = r"[\[【\[]"
BR_C = r"[\]】\]]"
ANSWER_PAT = re.compile(NUM + r"\s*[.．]?\s*" + BR_O + r"\s*答案\s*" + BR_C + r"\s*([A-E]+)")

def norm_no(s):
    s = s.lower()
    s = s.replace("l", "1").replace("i", "1")
    return int(s)

def parse_year(pdf_path, year):
    r = PdfReader(pdf_path)
    full = "\n".join((pg.extract_text() or "") for pg in r.pages)
    text = re.sub(r"\s+", "", full)
    mm = re.search(r"多项选择题", text)
    single_txt = text[:mm.start()] if mm else text
    multi_txt = text[mm.start():] if mm else ""

    def parse_section(sec):
        ms = list(ANSWER_PAT.finditer(sec))
        items = []
        for i, m in enumerate(ms):
            end = ms[i+1].start() if i+1 < len(ms) else len(sec)
            items.append({
                "no": norm_no(m.group(1)),
                "answer": m.group(2),
                "analysis": sec[m.end():end].strip()
            })
        return items

    singles = parse_section(single_txt)
    multis = parse_section(multi_txt)
    # 结构性分界：非法学基础课 单选1-20刑法/21-40民法；多选41-45刑法/46-50民法
    def assign(items, single):
        for it in items:
            if single:
                it["subject"] = "刑法" if it["no"] <= 20 else "民法"
            else:
                it["subject"] = "刑法" if it["no"] <= 45 else "民法"
    assign(singles, True)
    assign(multis, False)
    for it in singles: it["type"] = "single"
    for it in multis: it["type"] = "multi"
    return {"year": year, "singles": singles, "multis": multis}

out = {}
for pdf in sorted(glob.glob(tdir + r"\*.pdf")):
    year = int(os.path.basename(pdf)[:4])
    d = parse_year(pdf, year)
    out[year] = d
    xs = [q for q in d["singles"]+d["multis"] if q["subject"]=="刑法"]
    sn = [q["no"] for q in d["singles"]]
    mn = [q["no"] for q in d["multis"]]
    print(f"{year}: 单选{len(sn)}({sn[0] if sn else '-'}..{sn[-1] if sn else '-'}) 多选{len(mn)}({mn[0] if mn else '-'}..{mn[-1] if mn else '-'}) 刑法题{len(xs)}")

with open(base + r"\data\jiexi_jichu.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("已保存 data/jiexi_jichu.json")

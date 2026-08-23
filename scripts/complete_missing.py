# -*- coding: utf-8 -*-
"""补回解析漏掉的「无答案」题和格式变体题"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r"D:\code\juris_page"
tdir = base + r"\法硕小程序开发\考研法硕历年真题，法学+非法学\09.法硕非法学历年真题\02.法硕（非法学）基础课解析（2010-2024）\02.法硕（非法学）基础课解析（2010-2024）"
lex = json.load(open(base + r"\data\xingfa_lexicon.json", encoding="utf-8"))
ZUIMING = sorted({z for c in lex["分则"].values() for z in c}, key=len, reverse=True)
ZONGLUN = sorted({k for c in lex["总论"].values() for k in c}, key=len, reverse=True)

# 缺失题：(year, no, 答案)
missing = {
    2011: [(10, "无答案", "原答案为C"), (29, "C", "")],
    2012: [(15, "无答案", "原答案为D")],
    2013: [(22, "无答案", "")],
    2015: [(25, "无答案", "原答案为C"), (26, "无答案", "")],
}

def get_year_text(year):
    p = tdir + f"\\{year}年法硕（非法学）基础课解析.pdf"
    r = PdfReader(p)
    full = "\n".join((pg.extract_text() or "") for pg in r.pages)
    return re.sub(r"\s+", "", full)

def extract_analysis(text, no):
    """提取 no 题答案标记到下一答案标记之间的文本（限制长度）"""
    # 答案标记：数字. 各种左括号 + 答案
    mark = r"\d{1,2}\.??[\[【\[［\(（]\s*(?:参考)?答案"
    pat = re.compile(mark)
    marks = list(pat.finditer(text))
    # 找到 no 题的标记位置
    start = None
    for m in marks:
        if re.match(rf"{no}\.?[\[【\[［\(（]", text[m.start():m.start()+4]):
            start = m.start()
            break
    if start is None:
        return ""
    # 下一个标记（任意题号）
    end = len(text)
    for m in marks:
        if m.start() > start:
            end = m.start()
            break
    return text[start:end].strip()[:800]

qj = json.load(open(base + r"\data\questions_jichu.json", encoding="utf-8"))

# 先清理已补的题（避免重复）
for year, items in missing.items():
    arr = qj[str(year)]
    qj[str(year)] = [q for q in arr if q["no"] not in [n for n, _, _ in items]]

for year, items in missing.items():
    text = get_year_text(year)
    for no, answer, note in items:
        analysis = extract_analysis(text, no)
        # 提取考点
        zuis = [z for z in ZUIMING if z in analysis]
        zong = [k for k in ZONGLUN if k in analysis and k not in ("刑法","犯罪","故意","过失","责任")]
        typ = "single" if no <= 40 else "multi"
        subject = ("刑法" if no <= 20 else "民法") if typ == "single" else ("刑法" if no <= 45 else "民法")
        q = {
            "no": no, "answer": answer, "type": typ, "subject": subject,
            "analysis": analysis, "zuiming": zuis, "kaodian_zonglun": zong,
            "note": note or None
        }
        # 插入（保持 no 排序）
        arr = qj[str(year)]
        arr.append(q)
        arr.sort(key=lambda x: x["no"])
        print(f"补回 {year}-{no} [{subject}/{typ}] 答案[{answer}] 罪名{zuis[:3]} 解析{len(analysis)}字")

json.dump(qj, open(base + r"\data\questions_jichu.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n=== 补漏后各年刑法题数 ===")
for y in sorted(qj, key=int):
    arr = qj[y]
    xs = [q["no"] for q in arr if q["subject"] == "刑法"]
    print(f"{y}: 总{len(arr)} 刑法{len(xs)}")

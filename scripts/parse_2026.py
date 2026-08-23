# -*- coding: utf-8 -*-
"""解析 2026 非法学基础课（试题+纯答案表，无解析）→ 结构化题目"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r"D:\code\juris_page"
pdf = base + r"\法硕小程序开发\考研法硕历年真题，法学+非法学\09.法硕非法学历年真题\2026年全国硕士研究生招生考试法律硕士专业基础（非法学）及参考答案.pdf"

lex = json.load(open(base + r"\data\xingfa_lexicon.json", encoding="utf-8"))
ZUIMING = sorted({z for c in lex["分则"].values() for z in c}, key=len, reverse=True)
ZONGLUN = sorted({k for c in lex["总论"].values() for k in c}, key=len, reverse=True)

r = PdfReader(pdf)
full = "\n".join((pg.extract_text() or "") for pg in r.pages)

# 定位答案表（第二个“一、单项选择题”）
pos = [m.start() for m in re.finditer(r"一、单项选择题", full)]
ans_pos = pos[-1]
question_text = full[:ans_pos]
answer_text = full[ans_pos:]

def clean_lines(txt):
    """去水印/页眉页脚"""
    out = []
    for line in txt.split("\n"):
        l = line.strip()
        if not l:
            continue
        if any(w in l for w in ["秋北", "KK139201213", "藏宝阁", "备考群", "添加", "公众号", "小红书"]):
            continue
        if re.match(r"^\d+\s*/\s*\d+$", l):  # 页码
            continue
        out.append(l)
    return out

# ---- 解析题目 ----
lines = clean_lines(question_text)
questions = []
cur = None
for line in lines:
    m = re.match(r"^(\d{1,2})\.(.*)$", line)
    if m and not re.match(r"^[A-D]\.", line):
        no = int(m.group(1))
        if cur:
            questions.append(cur)
        cur = {"no": no, "stem": m.group(2).strip(), "options": {}}
        continue
    m2 = re.match(r"^([A-D])\.(.*)$", line)
    if m2 and cur:
        cur["options"][m2.group(1)] = m2.group(2).strip()
        continue
    if cur:
        # 题干续行
        cur["stem"] += line
if cur:
    questions.append(cur)

# ---- 解析答案表 ----
single_ans = []
multi_ans = []
# 单选：一、单项选择题 与 二、多项选择题 之间
seg_s = answer_text[answer_text.find("一、单项选择题"):]
m_single_end = re.search(r"二、多项选择题", seg_s)
single_seg = seg_s[:m_single_end.start()] if m_single_end else seg_s
single_ans = re.findall(r"[A-D]", re.sub(r"\s+", "", single_seg))[:40]
# 多选：二、多项选择题 与 三、简答题 之间
m_multi_start = re.search(r"二、多项选择题", answer_text)
m_multi_end = re.search(r"三、简答题", answer_text)
if m_multi_start:
    multi_seg = answer_text[m_multi_start.start():(m_multi_end.start() if m_multi_end else len(answer_text))]
    # 去掉题号数字行，按空白切 token
    tokens = re.findall(r"[A-D\(\)]+", multi_seg)
    multi_ans = [t for t in tokens if re.search(r"[A-D]", t)][:10]

print("单选答案数", len(single_ans), "多选答案数", len(multi_ans))
print("多选答案:", multi_ans)

def classify_subject(no, typ):
    if typ == "single":
        return "刑法" if no <= 20 else "民法"
    return "刑法" if no <= 45 else "民法"

def extract_kd(stem, options):
    txt = stem + " " + " ".join(options.values())
    zuis = [z for z in ZUIMING if z in txt]
    zong = [k for k in ZONGLUN if k in txt and k not in ("刑法","犯罪","故意","过失","责任")]
    return zuis, zong

def clean_answer(token):
    """A(BC)D -> 答案 AD，争议 BC"""
    note = ""
    m = re.search(r"\(([A-D]+)\)", token)
    if m:
        note = m.group(1) + "存争议"
    outer = re.sub(r"\([A-D]+\)", "", token)
    return outer, note

out = []
for q in questions:
    no = q["no"]
    if no > 50:  # 只取客观题
        continue
    typ = "single" if no <= 40 else "multi"
    raw = single_ans[no-1] if typ == "single" else (multi_ans[no-41] if no-41 < len(multi_ans) else "")
    answer, note = clean_answer(raw)
    zuis, zong = extract_kd(q["stem"], q["options"])
    subject = classify_subject(no, typ)
    out.append({
        "no": no, "answer": answer, "type": typ, "subject": subject,
        "analysis": q["stem"], "stem": q["stem"], "options": q["options"],
        "zuiming": zuis, "kaodian_zonglun": zong,
        "note": note or None
    })

xs = [q for q in out if q["subject"] == "刑法"]
print(f"2026: 总{len(out)}题 刑法{len(xs)}题")
for q in xs[:10]:
    print(f"  {q['no']}({q['type']}) 答案{q['answer']} 罪名{q['zuiming'][:4]}")

json.dump(out, open(base + r"\data\questions_2026.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已保存 questions_2026.json")

# -*- coding: utf-8 -*-
"""解析 2025 非法学基础课（扫描件 OCR）+ 答案表（人工从图读到的 40 单选 + 10 多选）"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"D:\code\juris_page"
lex = json.load(open(base + r"\data\xingfa_lexicon.json", encoding="utf-8"))
ZUIMING = sorted({z for c in lex["分则"].values() for z in c}, key=len, reverse=True)
ZONGLUN = sorted({k for c in lex["总论"].values() for k in c}, key=len, reverse=True)

# 单选答案（人工从答案表图片读到）
SINGLE_ANS = "DDABAACDBCDDDBAABBCCDDDACCABACACBDACCAACBAA".replace(" ", "")
MULTI_ANS = ["BCD", "ABD", "CD", "ACD", "ABCD", "AB", "ACD", "AD", "ABC", "ABD"]

ocr_path = base + r"\data\ocr_zhenti_jichu_2025.jsonl"
pages = []
with open(ocr_path, encoding="utf-8") as f:
    for ln in f:
        d = json.loads(ln)
        if d["page"] >= 8:
            break  # 答案表+主观题不要
        pages.append(d)

def clean(text):
    text = re.sub(r"扫码[^一-龥]*APP[^一-龥]*", "", text)
    text = re.sub(r"^[\d\.\s　/—\-—]+$", "", text, flags=re.M)
    return text.strip()

# 合并所有行
all_lines = []
for p in pages:
    for l in sorted(p["lines"], key=lambda x:(x["y"], x["x"])):
        t = clean(l["t"])
        if t:
            all_lines.append(t)

# 预处理：拆分行内被吞的题号（如 "D.丙25.甲..." 拆为两行）
INLINE_NO = re.compile(r"([A-D]\.[^\d]{0,8}?)(\d{1,2}[.．])")
flat = []
for line in all_lines:
    parts = INLINE_NO.sub(r"\1<<<SPLIT>>>\2", line).split("<<<SPLIT>>>")
    for p in parts:
        if p.strip():
            flat.append(p)
all_lines = flat

# 切分题号
questions = []
cur = None
NO_PAT = re.compile(r"^(\d{1,2})[.．]\s*(.*)$")
OPT_PAT = re.compile(r"^([A-D])[.．]\s*(.*)$")
for line in all_lines:
    m = NO_PAT.match(line)
    if m:
        no = int(m.group(1))
        if no > 50:
            break
        if cur:
            questions.append(cur)
        cur = {"no": no, "stem": m.group(2).strip(), "options": {}}
        continue
    m2 = OPT_PAT.match(line)
    if m2 and cur:
        cur["options"][m2.group(1)] = m2.group(2).strip()
        continue
    if cur:
        cur["stem"] += line
if cur:
    questions.append(cur)

print("题数", len(questions))

# OCR 错误词修正映射（题干匹配 lexicon 失败时手动替换）
OCR_FIX = {
    "寻滋事罪": "寻衅滋事罪", "伺私枉法罪": "徇私枉法罪",
    "畏缩身份": "猥亵儿童",  # 兜底，按实际修正
}

def extract_kd(stem, options):
    txt = stem + " " + " ".join(options.values())
    for k, v in OCR_FIX.items():
        txt = txt.replace(k, v)
    zuis = [z for z in ZUIMING if z in txt]
    zong = [k for k in ZONGLUN if k in txt and k not in ("刑法","犯罪","故意","过失","责任")]
    return zuis, zong

out = []
for q in questions:
    no = q["no"]
    if no > 50:
        continue
    typ = "single" if no <= 40 else "multi"
    answer = SINGLE_ANS[no-1] if typ == "single" else MULTI_ANS[no-41]
    zuis, zong = extract_kd(q["stem"], q["options"])
    subject = ("刑法" if no <= 20 else "民法") if typ == "single" else ("刑法" if no <= 45 else "民法")
    out.append({
        "no": no, "answer": answer, "type": typ, "subject": subject,
        "analysis": q["stem"], "stem": q["stem"], "options": q["options"],
        "zuiming": zuis, "kaodian_zonglun": zong,
        "note": "答案参考kaoyan.cn整理（官方未公布）"
    })

xs = [q for q in out if q["subject"] == "刑法"]
print(f"2025: 总{len(out)}题 刑法{len(xs)}题")
for q in xs[:8]:
    print(f"  {q['no']}({q['type']}) 答{q['answer']} 考点{q['kaodian_zonglun'][:2]} 罪名{q['zuiming'][:3]}")

json.dump(out, open(base + r"\data\questions_2025.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已保存 questions_2025.json")

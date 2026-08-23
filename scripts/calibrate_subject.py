# -*- coding: utf-8 -*-
"""用题号结构校准刑法/民法（非法学基础课结构固定：单选1-20刑法、多选41-45刑法）。
2010 年例外（分块式：单选1-20刑法 + 多选21-25刑法），保持原分类。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"D:\code\juris_page"
qj = json.load(open(base + r"\data\questions_jichu.json", encoding="utf-8"))

for year, arr in qj.items():
    if year == "2010":
        continue  # 分块结构，保持原分类
    for q in arr:
        no = q["no"]
        if no <= 40:
            q["type"] = "single"
            q["subject"] = "刑法" if no <= 20 else "民法"
        else:
            q["type"] = "multi"
            q["subject"] = "刑法" if no <= 45 else "民法"

json.dump(qj, open(base + r"\data\questions_jichu.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for y in sorted(qj, key=int):
    arr = qj[y]
    xs = [q["no"] for q in arr if q["subject"] == "刑法"]
    print(f"{y}: 总{len(arr)} 刑法{len(xs)}")

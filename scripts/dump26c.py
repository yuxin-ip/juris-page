# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2026年全国硕士研究生招生考试法律硕士专业基础（非法学）及参考答案.pdf"
r = PdfReader(p)
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
# 找答案表，保留原始换行
idx = full.find("参考答案") if "参考答案" in full else full.find("答案")
# 找"一、单项选择题"第二次出现（答案表）位置
positions = [m.start() for m in re.finditer(r"一、单项选择题", full)]
print("所有'一、单项选择题'位置:", positions)
# 打印答案表附近的原始文本
ans_idx = positions[-1] if positions else 0
print("=== 答案表原始文本 ===")
print(full[ans_idx:ans_idx+1500])

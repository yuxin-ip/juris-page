# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2026年全国硕士研究生招生考试法律硕士专业基础（非法学）及参考答案.pdf"
r = PdfReader(p)
# 前2页题目部分原始文本
for i in [0,1]:
    print(f"===== 页{i} =====")
    print((r.pages[i].extract_text() or "")[:1200])

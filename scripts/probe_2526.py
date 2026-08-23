# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
files = {
    "2025非法学真题及答案": r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2025年法硕非法学真题及答案/2025年法硕非法学真题及答案.pdf",
    "2026非法学基础课": r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2026年全国硕士研究生招生考试法律硕士专业基础（非法学）及参考答案.pdf",
}
for name, p in files.items():
    r = PdfReader(p)
    n = len(r.pages)
    txt = ""
    for i in [0,1,n//2]:
        txt += (r.pages[i].extract_text() or "")
    compact = re.sub(r"\s+","",txt)
    print(f"===== {name} | pages={n} | 前几页文本长度={len(txt.strip())}")
    print("样本:", compact[:400])
    print()

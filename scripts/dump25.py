# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2025年法硕非法学真题及答案/2025年法硕非法学真题及答案.pdf"
r = PdfReader(p)
for i, pg in enumerate(r.pages):
    t = re.sub(r"\s+","",(pg.extract_text() or ""))
    print(f"页{i}: {t[:60]}")

# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
import glob, os
tdir = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）"
for pdf in sorted(glob.glob(tdir+r"\*.pdf")):
    y = os.path.basename(pdf)[:4]
    r = PdfReader(pdf)
    n = len(r.pages)
    t = "".join((pg.extract_text() or "") for pg in r.pages[:3])
    print(f"{y}: pages={n} 前3页文本长度={len(t.strip())}")

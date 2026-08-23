# -*- coding: utf-8 -*-
import sys, io, os, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
from collections import Counter
tdir = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）"
cnt = Counter()
for pdf in sorted(glob.glob(tdir+r"\*.pdf")):
    r = PdfReader(pdf)
    full = "\n".join((pg.extract_text() or "") for pg in r.pages)
    text = re.sub(r"\s+","",full)
    for m in re.finditer(r"答案", text):
        pre = text[max(0,m.start()-3):m.start()]
        # 找紧邻的编号：形如 数字[.] 或 数字 直接
        mm = re.search(r"([0-9A-Za-z]{1,2})[.．]?$", pre)
        if mm:
            cnt[mm.group(1)] += 1
print("编号 token 计数:")
for k,v in sorted(cnt.items(), key=lambda x:-x[1]):
    print(repr(k), v)

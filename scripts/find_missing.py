# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
tdir = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）"
def find(year, no):
    p = tdir + f"\\{year}年法硕（非法学）基础课解析.pdf"
    r = PdfReader(p)
    full = "\n".join((pg.extract_text() or "") for pg in r.pages)
    text = re.sub(r"\s+","",full)
    # 找 "10.【答案】" 或 "10.［答案" 或 "10.【参考答案" 附近
    pat = re.compile(rf"{no}\.??[\[【\[]\s*(?:参考)?答案")
    for m in pat.finditer(text):
        print(f"{year}-{no}:", text[m.start():m.start()+160])
        return
    # 也搜"无答案"
    for m in re.finditer(r"无答案", text):
        ctx = text[max(0,m.start()-20):m.start()+40]
        if str(no) in ctx or True:
            print(f"{year}-{no} 附近'无答案':", ctx)
            return
    print(f"{year}-{no}: 未找到")
find(2011, 10)
find(2012, 15)
find(2011, 29)
find(2013, 22)
find(2015, 25)
find(2015, 26)

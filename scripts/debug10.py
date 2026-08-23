# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）/2010年法硕（非法学）基础课解析.pdf"
r = PdfReader(p)
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
text = re.sub(r"\s+", "", full)
print("长度", len(text), "答案次数", text.count("答案"))
for m in re.finditer(r"答案", text):
    s = max(0, m.start()-8); e = min(len(text), m.end()+5)
    ctx = text[s:e]
    if re.search(r"选择题|答案|简答|辨析|案例", ctx):
        print(repr(ctx))

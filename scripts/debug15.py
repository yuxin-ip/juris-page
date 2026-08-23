# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）/2015年法硕（非法学）基础课解析.pdf"
r = PdfReader(p)
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
text = re.sub(r"\s+", "", full)
print("总长度", len(text), "含'答案'次数", text.count("答案"))
# 找所有 答案 出现位置的前后文
for m in re.finditer(r"答案", text):
    s = max(0, m.start()-6); e = min(len(text), m.end()+6)
    print(repr(text[s:e]))

# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）/2024年法硕（非法学）基础课解析.pdf"
r = PdfReader(p)
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
# 字符间有空格/OCR式分隔，压缩空白
compact = re.sub(r"\s+", "", full)
print(compact[:3000])

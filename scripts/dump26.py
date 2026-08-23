# -*- coding: utf-8 -*-
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader
p = r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2026年全国硕士研究生招生考试法律硕士专业基础（非法学）及参考答案.pdf"
r = PdfReader(p)
full = "\n".join((pg.extract_text() or "") for pg in r.pages)
compact = re.sub(r"\s+","",full)
# 找"答案"部分起点和结构
print("总长度", len(compact), "含'答案'次数", compact.count("答案"))
# 找参考答案/解析的标题位置
for m in re.finditer(r"(参考答案|答案详解|答案解析|一、单项选择题)", compact):
    print(m.start(), repr(compact[m.start():m.start()+20]))

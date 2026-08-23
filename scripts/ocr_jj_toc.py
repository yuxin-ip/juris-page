# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
doc = fitz.open(r"D:/code/juris_page/法硕小程序开发/一本通/27法硕精讲一本通-刑法学-车润海.pdf")
print("总页数", len(doc))
# 先探测前12页，找"目录"
for pno in range(0, 12):
    pix = doc[pno].get_pixmap(dpi=120)
    result,_ = ocr(pix.tobytes("png"))
    text = " ".join(line[1] for line in result) if result else ""
    print(f"--- PDF索引{pno}: {text[:90]}")

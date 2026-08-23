# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
doc = fitz.open(r"D:/code/juris_page/法硕小程序开发/一本通/27法硕精讲一本通-刑法学-车润海.pdf")
for pno in list(range(12, 30)):
    pix = doc[pno].get_pixmap(dpi=110)
    result,_ = ocr(pix.tobytes("png"))
    text = " ".join(line[1] for line in result) if result else ""
    print(f"--- PDF索引{pno}: {text[:80]}")

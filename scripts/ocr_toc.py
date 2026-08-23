# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
doc = fitz.open(r"D:/code/juris_page/法硕小程序开发/27法硕背诵一本通/27刑法背诵一本通.pdf")
for pno in [5,6,7]:
    pix = doc[pno].get_pixmap(dpi=200)
    result,_ = ocr(pix.tobytes("png"))
    text = "\n".join(line[1] for line in result) if result else ""
    print(f"===== 目录页 PDF索引{pno} =====")
    print(text)
    print()

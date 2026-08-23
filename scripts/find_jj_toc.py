# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
doc = fitz.open(r"D:/code/juris_page/法硕小程序开发/一本通/27法硕精讲一本通-刑法学-车润海.pdf")
# 扫描 idx 12..40，找"目录"页
for pno in range(12, 40):
    pix = doc[pno].get_pixmap(dpi=110)
    result,_ = ocr(pix.tobytes("png"))
    text = " ".join(line[1] for line in result) if result else ""
    mark = " <<<< 目录" if ("目录" in text or "Contents" in text or "CONTENTS" in text) else ""
    print(f"idx{pno}: {text[:60]}{mark}")

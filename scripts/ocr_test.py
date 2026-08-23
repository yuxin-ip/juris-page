# -*- coding: utf-8 -*-
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()
doc = fitz.open(r"D:/code/juris_page/法硕小程序开发/27法硕背诵一本通/27刑法背诵一本通.pdf")
print("pages:", len(doc))
for pno in range(1, 6):
    page = doc[pno]
    pix = page.get_pixmap(dpi=180)
    img = pix.tobytes("png")
    t0 = time.time()
    result, _ = ocr(img)
    dt = time.time() - t0
    text = " ".join(line[1] for line in result) if result else ""
    print(f"--- PDF页{pno} (索引{pno}) 耗时{dt:.1f}s ---")
    print(text[:800])
    print()

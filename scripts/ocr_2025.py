# -*- coding: utf-8 -*-
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
doc = fitz.open(r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/2025年法硕非法学基础课真题.pdf")
out = open(r"D:/code/juris_page/data/ocr_zhenti_jichu_2025.jsonl", "w", encoding="utf-8")
for pno in range(len(doc)):
    pix = doc[pno].get_pixmap(dpi=180)
    result, _ = ocr(pix.tobytes("png"))
    lines = []
    if result:
        for box, text, score in result:
            ys = [p[1] for p in box]; xs = [p[0] for p in box]
            lines.append({"t": text, "y": round(min(ys)), "x": round(min(xs)), "s": round(float(score),2)})
    out.write(json.dumps({"page": pno, "lines": lines}, ensure_ascii=False) + "\n")
    # 打印每页开头
    head = " ".join(l["t"] for l in sorted(lines, key=lambda x:(x["y"],x["x"]))[:6])
    print(f"页{pno}: {head[:90]}")
out.close()
print("已保存 ocr_zhenti_jichu_2025.jsonl")

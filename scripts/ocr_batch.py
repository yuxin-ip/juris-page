# -*- coding: utf-8 -*-
"""批量 OCR：整本 PDF -> JSONL（每页：页索引 + 各行文本及位置）"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
from rapidocr_onnxruntime import RapidOCR

def ocr_pdf(pdf_path, out_path, tag):
    if os.path.exists(out_path):
        done = sum(1 for _ in open(out_path, encoding='utf-8'))
    else:
        done = 0
    doc = fitz.open(pdf_path)
    n = len(doc)
    if done >= n:
        print(f"[{tag}] 已完成 {done}/{n}，跳过")
        return
    ocr = RapidOCR()
    mode = 'a' if done else 'w'
    f = open(out_path, mode, encoding='utf-8')
    t0 = time.time()
    for pno in range(done, n):
        pix = doc[pno].get_pixmap(dpi=180)
        result, _ = ocr(pix.tobytes("png"))
        lines = []
        if result:
            for box, text, score in result:
                # box: 4点坐标；记录顶部y和左侧x供版式分析
                ys = [p[1] for p in box]; xs = [p[0] for p in box]
                lines.append({"t": text, "y": round(min(ys)), "x": round(min(xs)), "s": round(float(score),2)})
        f.write(json.dumps({"page": pno, "lines": lines}, ensure_ascii=False) + "\n")
        f.flush()
        if (pno+1) % 20 == 0:
            el = time.time()-t0
            print(f"[{tag}] {pno+1}/{n} 已用{el/60:.1f}min 预计剩余{(el/(pno+1-done))*(n-pno-1)/60:.1f}min")
    f.close()
    print(f"[{tag}] 完成 {n} 页，耗时 {(time.time()-t0)/60:.1f} min")

if __name__ == "__main__":
    which = sys.argv[1]
    base = r"D:/code/juris_page"
    if which == "beisong":
        ocr_pdf(base + r"\法硕小程序开发\27法硕背诵一本通\27刑法背诵一本通.pdf",
                base + r"\data\ocr_beisong_xingfa.jsonl", "背诵一本通")
    elif which == "jingjiang":
        ocr_pdf(base + r"\法硕小程序开发\一本通\27法硕精讲一本通-刑法学-车润海.pdf",
                base + r"\data\ocr_jingjiang_xingfa.jsonl", "精讲一本通")
    elif which == "zhenti":
        import glob
        tdir = base + r"\法硕小程序开发\考研法硕历年真题，法学+非法学\09.法硕非法学历年真题\01.法硕（非法学）基础课真题（2010-2024）\01.法硕（非法学）基础课真题（2010-2024）"
        for pdf in sorted(glob.glob(tdir + r"\*.pdf")):
            year = os.path.basename(pdf)[:4]
            ocr_pdf(pdf, base + rf"\data\ocr_zhenti_jichu_{year}.jsonl", f"真题{year}")

# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

files = {
    "真题2024": r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/01.法硕（非法学）基础课真题（2010-2024）/01.法硕（非法学）基础课真题（2010-2024）/2024年法硕（非法学）基础课真题.pdf",
    "解析2024": r"D:/code/juris_page/法硕小程序开发/考研法硕历年真题，法学+非法学/09.法硕非法学历年真题/02.法硕（非法学）基础课解析（2010-2024）/02.法硕（非法学）基础课解析（2010-2024）/2024年法硕（非法学）基础课解析.pdf",
    "刑法背诵一本通": r"D:/code/juris_page/法硕小程序开发/27法硕背诵一本通/27刑法背诵一本通.pdf",
    "刑法精讲一本通": r"D:/code/juris_page/法硕小程序开发/一本通/27法硕精讲一本通-刑法学-车润海.pdf",
}
for name, path in files.items():
    try:
        r = PdfReader(path)
        n = len(r.pages)
        txt = ""
        for i in [0, 1, 2, n//2]:
            txt += r.pages[i].extract_text() or ""
        outline = []
        try:
            def walk(o, d=0):
                for it in o:
                    if isinstance(it, list):
                        walk(it, d+1)
                    else:
                        outline.append(("  "*d) + str(it.title))
            walk(r.outline)
        except Exception as e:
            outline = [f"<outline error: {e}>"]
        print(f"===== {name} | pages={n} | 文本长度(4页样本)={len(txt.strip())} | 书签数={len(outline)}")
        print("样本:", txt.strip()[:200].replace("\n"," / "))
        print("书签前15:", outline[:15])
        print()
    except Exception as e:
        print(f"===== {name} 读取失败: {e}")

# -*- coding: utf-8 -*-
"""解析基础课解析PDF -> 客观题结构化（按答案长度判单选/多选，按内容判刑法/民法）"""
import sys, io, os, re, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pypdf import PdfReader

base = r"D:/code/juris_page"
tdir = base + r"\法硕小程序开发\考研法硕历年真题，法学+非法学\09.法硕非法学历年真题\02.法硕（非法学）基础课解析（2010-2024）\02.法硕（非法学）基础课解析（2010-2024）"

NUM = r"([0-9lIbBoOsSzZ]{1,2})"
# 答案块：编号 + 可选点 + 非词符 + "答案" + 至多4个非A-E字符 + A-E(1~4)
ANSWER_PAT = re.compile(NUM + r"[.．]?[\s\W]*(?:参考)?答案[^A-E]{0,4}([A-E]{1,4})")

# 刑法关键词（总论 + 分则常用罪名），用于内容判定；后续会与教材罪名表合并
XINGFA_KW = ["刑法","犯罪","刑事责任","刑罚","量刑","累犯","自首","立功","缓刑","假释","减刑",
    "数罪并罚","共同犯罪","主犯","从犯","胁从犯","教唆犯","正当防卫","紧急避险","防卫过当",
    "故意","过失","未遂","既遂","预备","中止","着手","实行","结果加重","想象竞合","牵连犯",
    "犯罪构成","犯罪客体","犯罪对象","犯罪主体","责任能力","责任年龄","故意杀人","故意伤害",
    "抢劫","抢夺","盗窃","诈骗","敲诈勒索","侵占","挪用","职务侵占","贪污","受贿","行贿","挪用公款",
    "绑架","非法拘禁","强奸","强制猥亵","拐卖","收买","遗弃","虐待","重婚","破坏军婚",
    "危害公共安全","放火","爆炸","投放危险物质","以危险方法危害公共安全","破坏交通工具",
    "交通肇事","危险驾驶","生产销售伪劣","走私","伪造货币","洗钱","信用卡","集资诈骗","贷款诈骗",
    "非法经营","合同诈骗","假冒注册商标","侵犯著作权","侵犯商业秘密","非法吸收公众存款",
    "毒品","贩卖毒品","运输毒品","制造毒品","容留","非法持有毒品","窝藏","包庇","掩饰隐瞒",
    "寻衅滋事","聚众斗殴","组织卖淫","强迫卖淫","传播淫秽","赌博","开设赌场","伪证","妨害作证",
    "妨害公务","袭警","侮辱","诽谤","诬告陷害","侵犯公民个人信息","非法侵入","破坏计算机",
    "危害国家安全","间谍","叛逃","颠覆国家政权","窃取国家秘密","泄露国家秘密","非法获取国家秘密",
    "渎职","滥用职权","玩忽职守","徇私枉法","枉法裁判","环境","污染","盗伐","滥伐","非法狩猎",
    "故意毁坏财物","破坏生产经营","拒不支付劳动报酬","逃税","抗税","骗税","虚开"]

def norm_no(s):
    M={"l":"1","i":"1","I":"1","b":"6","B":"8","o":"0","O":"0","s":"5","S":"5","z":"2","Z":"2"}
    s = s.lower()
    s2="".join(M.get(c,c) for c in s)
    try: return int(s2)
    except: return 0

def is_xingfa(txt):
    return any(k in txt for k in XINGFA_KW)

def parse_year(pdf_path, year):
    r = PdfReader(pdf_path)
    full = "\n".join((pg.extract_text() or "") for pg in r.pages)
    text = re.sub(r"\s+", "", full)
    ms = list(ANSWER_PAT.finditer(text))
    qs = []
    for i, m in enumerate(ms):
        no = norm_no(m.group(1))
        ans = m.group(2)
        end = ms[i+1].start() if i+1 < len(ms) else len(text)
        analysis = text[m.end():end]
        # 排除简答/辨析/案例：只保留客观题（no<=50 且答案为A-E）
        if no > 50:
            continue
        qs.append({
            "no": no,
            "answer": ans,
            "type": "single" if len(ans)==1 else "multi",
            "subject": "刑法" if is_xingfa(analysis) else "民法",
            "analysis": analysis.strip()
        })
    return qs

out = {}
for pdf in sorted(glob.glob(tdir + r"\*.pdf")):
    year = int(os.path.basename(pdf)[:4])
    qs = parse_year(pdf, year)
    out[year] = qs
    xs = [q for q in qs if q["subject"]=="刑法"]
    sn = len([q for q in qs if q["type"]=="single"])
    mn = len([q for q in qs if q["type"]=="multi"])
    print(f"{year}: 共{len(qs)}题 单选{sn} 多选{mn} 刑法{len(xs)}")

with open(base + r"\data\questions_jichu.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("已保存 data/questions_jichu.json")

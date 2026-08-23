# -*- coding: utf-8 -*-
"""基于罪名词表对题目做精确分类，并提取考点候选（罪名/总论考点）"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"D:\code\juris_page"
lex = json.load(open(base + r"\data\xingfa_lexicon.json", encoding="utf-8"))

# 分则罪名（扁平，按长度降序）
ZUIMING = set()
for cat in lex["分则"].values():
    for z in cat:
        ZUIMING.add(z)
ZUIMING_SORTED = sorted(ZUIMING, key=len, reverse=True)

# 总论考点（扁平）
ZONGLUN = []
for cat in lex["总论"].values():
    ZONGLUN += cat
ZONGLUN_SORTED = sorted(set(ZONGLUN), key=len, reverse=True)

# 强总论术语（不含“故意/过失”等泛词，避免与民法混淆）
ZONGLUN_STRONG = ["犯罪构成","犯罪客体","犯罪客观方面","犯罪主体","犯罪主观方面","刑事责任","刑事责任能力",
    "刑事责任年龄","量刑","数罪并罚","累犯","自首","立功","缓刑","假释","减刑","主犯","从犯","胁从犯","教唆犯",
    "共同犯罪","正当防卫","紧急避险","防卫过当","避险过当","犯罪预备","犯罪未遂","犯罪中止","犯罪既遂",
    "结果加重犯","想象竞合","牵连犯","连续犯","吸收犯","继续犯","追诉时效","赦免","单位犯罪","犯罪集团",
    "刑法的解释","罪刑法定","罪责刑相适应","刑法的效力","溯及力","不作为","不作为犯罪","因果关系","认识错误",
    "事实认识错误","对象错误","打击错误","手段错误","危险犯","实害犯","行为犯","结果犯","刑罚","主刑","附加刑",
    "死刑","罚金","没收财产","剥夺政治权利","驱逐出境","管制","拘役","有期徒刑","无期徒刑","坦白","特别累犯"]

# 强民法特征（出现即倾向民法）
MINFA_STRONG = ["民法典","民事","合同","物权","债权","债的","侵权责任","婚姻","继承","法人","代理","所有权",
    "担保物权","抵押权","质权","留置","要约","承诺","不当得利","无因管理","宣告死亡","宣告失踪","遗嘱",
    "继承权","离婚","收养","人格权","姓名权","肖像权","名誉权","隐私权","著作权","专利权","商标权",
    "善意取得","买卖合同","租赁合同","赠与合同","借款合同","保证","定金","违约金","动产","不动产","宅基地",
    "地役权","居住权","配偶权","亲权","监护","宣告失踪","诉讼时效","占有","添附","混合","共有","建筑物区分所有权"]

def classify(analysis):
    xf = 0
    # 罪名信号 +3
    for z in ZUIMING_SORTED:
        if z in analysis:
            xf += 3
    # 总论强信号 +2
    for k in ZONGLUN_STRONG:
        if k in analysis:
            xf += 2
    # 民法强信号 -3
    for k in MINFA_STRONG:
        if k in analysis:
            xf -= 3
    return "刑法" if xf > 0 else "民法"

def extract_kaodian(analysis):
    """返回 (罪名列表, 总论考点列表)"""
    zuis = [z for z in ZUIMING_SORTED if z in analysis]
    zong = [k for k in ZONGLUN_SORTED if k in analysis]
    return zuis, zong

qs = json.load(open(base + r"\data\questions_jichu.json", encoding="utf-8"))
tot = {"刑法": 0, "民法": 0}
for year, arr in qs.items():
    for q in arr:
        subj = classify(q["analysis"])
        q["subject"] = subj
        zuis, zong = extract_kaodian(q["analysis"])
        q["zuiming"] = zuis
        q["kaodian_zonglun"] = zong
        tot[subj] += 1

json.dump(qs, open(base + r"\data\questions_jichu.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for year in sorted(qs, key=int):
    arr = qs[year]
    xs = [q for q in arr if q["subject"]=="刑法"]
    print(f"{year}: 刑法{len(xs)} 民法{len(arr)-len(xs)} | 刑法罪名示例:", [q['zuiming'][:2] for q in xs[:3]])
print("总计", tot)

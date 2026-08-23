# -*- coding: utf-8 -*-
"""合并：真题 -> 一题多考点，每个考点带背诵/精讲页码"""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

base = r"D:\code\juris_page"
qs = json.load(open(base + r"\data\questions_jichu.json", encoding="utf-8"))
idx_bs = json.load(open(base + r"\data\index_beisong.json", encoding="utf-8"))
lex = json.load(open(base + r"\data\xingfa_lexicon.json", encoding="utf-8"))

# 精讲索引（若已生成则加载）
idx_jj = {}
try:
    idx_jj = json.load(open(base + r"\data\index_jingjiang.json", encoding="utf-8"))
except FileNotFoundError:
    pass

ZUIMING = sorted({z for c in lex["分则"].values() for z in c}, key=len, reverse=True)
ZONGLUN = sorted({k for c in lex["总论"].values() for k in c}, key=len, reverse=True)

# 过泛的表述，不作为具体考点
STOP_KW = {"刑法", "犯罪", "故意", "过失", "责任"}

# 常见简称 -> 标准罪名
ALIAS = {
    "拐卖儿童罪": "拐卖妇女儿童罪", "拐卖妇女罪": "拐卖妇女儿童罪",
    "收买被拐卖儿童罪": "收买被拐卖的妇女儿童罪",
    "走私毒品罪": "走私贩卖运输制造毒品罪", "贩卖毒品罪": "走私贩卖运输制造毒品罪",
    "运输毒品罪": "走私贩卖运输制造毒品罪", "制造毒品罪": "走私贩卖运输制造毒品罪",
    "非法持有枪支罪": "非法持有私藏枪支弹药罪",
    "盗窃枪支罪": "盗窃枪支弹药罪", "抢夺枪支罪": "抢夺枪支弹药罪",
    "介绍卖淫罪": "引诱容留介绍卖淫罪",
}

def lookup(name, idx):
    if name in idx:
        return idx[name]
    if name in ALIAS and ALIAS[name] in idx:
        return idx[ALIAS[name]]
    return None

def resolve_kaodian(q):
    a = q["analysis"]
    zuis = q.get("zuiming", [])
    zong = q.get("kaodian_zonglun", [])
    m = re.search(r"本题考查的是对(.{2,16}?)(?:的理解|的把握|的规定)", a)
    if m:
        cand = m.group(1).strip()
        for k in ZONGLUN:
            if k == cand or k in cand:
                return k, "zonglun"
    m2 = re.search(r"(?:构成|认定为|成立|应定)([一-龥]{2,10}罪)", a)
    if m2:
        zm = m2.group(1)
        for z in ZUIMING:
            if z == zm or z in zm:
                return z, "zuiming"
        return zm, "zuiming"
    if zuis:
        return zuis[0], "zuiming"
    if zong:
        return zong[0], "zonglun"
    return "", "none"

final = []
for year in sorted(qs, key=int):
    for q in qs[year]:
        if q["subject"] != "刑法":
            continue
        zuis = q.get("zuiming", [])
        zong = q.get("kaodian_zonglun", [])
        # 组装考点列表（去重、保序）
        points, seen = [], set()
        def add(name, typ):
            if name and name not in seen and name not in STOP_KW:
                seen.add(name)
                points.append({
                    "name": name, "type": typ,
                    "beisong_page": lookup(name, idx_bs),
                    "jingjiang_page": lookup(name, idx_jj),
                })
        # 罪名优先（按长度降序更具体在前）
        for z in sorted(zuis, key=len, reverse=True):
            add(z, "zuiming")
        for k in zong:
            add(k, "zonglun")

        kd, kd_type = resolve_kaodian(q)
        # 主考点：优先有页码的
        primary = None
        for p in points:
            if p["name"] == kd:
                primary = p; break
        if primary is None and points:
            primary = next((p for p in points if p["beisong_page"] is not None), points[0])

        rec = {
            "id": f"{year}-{q['no']}",
            "year": int(year), "no": q["no"], "type": q["type"],
            "subject": "刑法", "answer": q["answer"],
            "kaodian": primary["name"] if primary else kd,
            "points": points,
            "analysis": q["analysis"][:300]
        }
        final.append(rec)

json.dump(final, open(base + r"\data\dataset_xingfa_v1.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

n = len(final)
n_bs = sum(1 for x in final if any(p["beisong_page"] is not None for p in x["points"]))
n_jj = sum(1 for x in final if any(p["jingjiang_page"] is not None for p in x["points"]))
multi = sum(1 for x in final if len(x["points"]) >= 2)
print(f"刑法题 {n} | 至少一个背诵页码 {n_bs} | 至少一个精讲页码 {n_jj} | 多考点题 {multi}")
print("样例（多考点）:")
for x in final:
    if len(x["points"]) >= 2:
        print(f"  {x['id']} 主考点[{x['kaodian']}] 考点数{len(x['points'])}:")
        for p in x["points"]:
            print(f"      - {p['name']} ({p['type']}) 背诵P.{p['beisong_page']} 精讲P.{p['jingjiang_page']}")
        break

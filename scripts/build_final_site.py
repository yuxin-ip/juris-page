"""Build the final dual-track criminal-law page index.

The build deliberately keeps the two extraction results as sources:

* questions.source.json / topics.source.json: 675-question, dual-track source.
* dataset_xingfa_v1.json and index_*.json: the earlier 425-question non-law source.

Question links are merged conservatively.  Page numbers use the printed page shown
in the physical 2027 books; known disagreements were checked against rendered PDF
pages and are recorded in data/page_audit.json.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"

BOOK_JJ = "zhonghe-jingjiang-xingfa-2027"
BOOK_BS = "zhonghe-beisong-xingfa-2027"
OFFSETS = {BOOK_JJ: 22, BOOK_BS: 6}


def load_json(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def norm(value: str) -> str:
    value = value or ""
    return re.sub(r"[\s、，。·,（）()《》〈〉“”\"'：:；;—\-]", "", value).lower()


def first_printed_page(topic: dict, book_id: str):
    for ref in topic.get("references", []):
        if ref.get("book_id") == book_id and ref.get("printed_pages"):
            return ref["printed_pages"][0]["start"]
    return None


def set_printed_page(topic: dict, book_id: str, page: int, status: str, source: str):
    refs = topic.setdefault("references", [])
    ref = next((item for item in refs if item.get("book_id") == book_id), None)
    if ref is None:
        ref = {"book_id": book_id}
        refs.append(ref)
    ref["printed_pages"] = [{"start": page, "end": page}]
    offset = OFFSETS[book_id]
    ref["pdf_pages"] = [{"start": page + offset, "end": page + offset}]
    ref["review_status"] = status
    ref["page_source"] = source


# All 22 exact-label disagreements found in the two indexes.  The chosen side was
# checked against the OCR text and rendered source pages.  Topics absent from one
# source are not counted as disagreements here.
PAGE_RESOLUTIONS = [
    # 背诵一本通：the earlier index matched a homonym or a nearby occurrence.
    ("背诵", "侮辱罪", 130, 136, 136, "Codex", "P.130 是强制猥亵、侮辱罪；普通侮辱罪从 P.136 开始"),
    ("背诵", "刑罚", 47, 49, 49, "Codex", "P.47 仍属于刑事责任；刑罚论及概念从 P.49 开始"),
    ("背诵", "刑事责任", 19, 46, 46, "Codex", "P.19 只是因果关系语境；刑事责任专章从 P.46 开始"),
    # 精讲一本通：细分小标题采用更精确页；章/节主题采用起始页。
    ("精讲", "避险过当", 113, 110, 113, "other", "细分标题在 P.113"),
    ("精讲", "剥夺政治权利", 208, 204, 208, "other", "细分标题在 P.208"),
    ("精讲", "犯罪构成", 33, 32, 32, "Codex", "第三章标题、概念与构成要件从 P.32 开始"),
    ("精讲", "犯罪主体", 65, 63, 63, "Codex", "第六章标题、定义与年龄制度从 P.63 开始"),
    ("精讲", "防卫过当", 107, 101, 107, "other", "细分标题在 P.107"),
    ("精讲", "拘役", 200, 199, 200, "other", "拘役细分标题在 P.200"),
    ("精讲", "聚众斗殴罪", 466, 490, 490, "Codex", "P.466 是其他章节表格；罪名正文从 P.490 开始"),
    ("精讲", "量刑", 213, 212, 212, "Codex", "第十四章标题、概念从 P.212 开始"),
    ("精讲", "没收财产", 206, 204, 206, "other", "没收财产细分标题在 P.206"),
    ("精讲", "抢劫罪", 424, 422, 422, "Codex", "抢劫罪标题及四种类型从 P.422 开始"),
    ("精讲", "死刑", 202, 199, 202, "other", "死刑细分标题在 P.202"),
    ("精讲", "坦白", 221, 228, 221, "other", "自首与坦白一节从 P.221 开始；P.228 是立功"),
    ("精讲", "特别累犯", 220, 218, 220, "other", "特别累犯细分标题在 P.220"),
    ("精讲", "伪造货币罪", 335, 333, 333, "Codex", "罪名条文及构成特征从 P.333 开始"),
    ("精讲", "无期徒刑", 201, 199, 201, "other", "无期徒刑细分标题在 P.201"),
    ("精讲", "侮辱罪", 410, 409, 409, "Codex", "普通侮辱罪构成特征从 P.409 开始"),
    ("精讲", "刑法的解释", 11, 5, 11, "other", "刑法解释细分标题在 P.11"),
    ("精讲", "刑事责任", 191, 190, 190, "Codex", "第十二章概述、定义从 P.190 开始"),
    ("精讲", "有期徒刑", 201, 199, 201, "other", "有期徒刑细分标题在 P.201"),
]


def build_topic_catalog():
    topics = load_json("topics.source.json")
    index_jj = load_json("index_jingjiang.json")
    index_bs = load_json("index_beisong.json")

    by_norm: dict[str, list[dict]] = defaultdict(list)
    for topic in topics:
        by_norm[norm(topic["label"])].append(topic)
        for alias in topic.get("aliases", []):
            by_norm[norm(alias)].append(topic)

    # Add concise general-rule/offence entries present only in the other index.
    # The original 322-topic catalog was heading-oriented and did not contain a
    # number of useful labels referenced by questions (for example 属地管辖).
    for book_id, index in ((BOOK_JJ, index_jj), (BOOK_BS, index_bs)):
        for label, page in index.items():
            matches = by_norm.get(norm(label), [])
            unique = {item["id"]: item for item in matches}
            if not unique:
                topic = {
                    "id": f"xingfa.imported.{label}",
                    "label": label,
                    "kind": "offense" if label.endswith("罪") else "general_rule",
                    "aliases": [],
                    "parent_id": None,
                    "references": [],
                }
                topics.append(topic)
                by_norm[norm(label)].append(topic)
                unique = {topic["id"]: topic}
            if len(unique) != 1:
                continue
            topic = next(iter(unique.values()))
            if first_printed_page(topic, book_id) is None:
                set_printed_page(topic, book_id, int(page), "candidate", "other-index-fill")

    # Apply the rendered-page decisions.  These are authoritative over both OCRs.
    book_ids = {"精讲": BOOK_JJ, "背诵": BOOK_BS}
    for book, label, _theirs, _ours, chosen, _winner, _reason in PAGE_RESOLUTIONS:
        matches = {item["id"]: item for item in by_norm.get(norm(label), [])}
        if len(matches) == 1:
            set_printed_page(
                next(iter(matches.values())), book_ids[book], chosen, "verified", "rendered-page-audit"
            )

    # Rebuild lookup after additions and aliases.
    by_norm = defaultdict(list)
    for topic in topics:
        by_norm[norm(topic["label"])].append(topic)
        for alias in topic.get("aliases", []):
            by_norm[norm(alias)].append(topic)
    return topics, by_norm


BAD_LABELS = {"刑法", "意杀人罪", "博罪"}
CATEGORY_LABELS = {"危害公共安全罪", "渎职罪"}
LABEL_ALIASES = {
    norm("意杀人罪"): norm("故意杀人罪"),
    norm("博罪"): norm("赌博罪"),
    norm("拐卖儿童罪"): norm("拐卖妇女、儿童罪"),
    norm("拐卖妇女儿童罪"): norm("拐卖妇女、儿童罪"),
    norm("走私毒品罪"): norm("走私、贩卖、运输、制造毒品罪"),
    norm("贩卖毒品罪"): norm("走私、贩卖、运输、制造毒品罪"),
    norm("窝藏包庇罪"): norm("窝藏、包庇罪"),
}

# Questions whose parser retained only the over-broad word “刑法”.  These labels
# come from the source analysis text (or, for 2026, the source question text).
MANUAL_QUESTION_TOPICS = {
    "2010-法学-刑法-01": ["属人管辖", "属地管辖", "保护管辖", "普遍管辖"],
    "2010-法学-刑法-06": ["犯罪故意", "犯罪过失"],
    "2014-法学-刑法-01": ["刑法的体系"],
    "2014-法学-刑法-02": ["普遍管辖"],
    "2017-法学-刑法-21": ["刑法的解释"],
    "2019-法学-刑法-01": ["罪刑法定原则", "从旧兼从轻"],
    "2019-法学-刑法-21": ["但书"],
    "2022-法学-刑法-25": ["非法植入基因编辑、克隆胚胎罪"],
    "2023-法学-刑法-08": ["为境外窃取、刺探、收买、非法提供国家秘密、情报罪"],
    "2026-法学-刑法-02": ["罪刑法定原则"],
    "2013-非法学-刑法-05": ["教唆犯", "教唆未遂"],
    "2013-非法学-刑法-16": ["罪状、罪名、法定刑"],
    "2014-非法学-刑法-12": ["罪状、罪名、法定刑"],
    "2017-非法学-刑法-41": ["刑法的解释"],
    "2020-非法学-刑法-01": ["属地管辖"],
    "2022-非法学-刑法-16": ["属地管辖", "拐卖妇女、儿童罪"],
    "2023-非法学-刑法-18": ["为境外窃取、刺探、收买、非法提供国家秘密、情报罪"],
}


def topic_refs(topic: dict):
    out = {}
    for ref in topic.get("references", []):
        pages = ref.get("printed_pages") or []
        if not pages:
            continue
        ranges = []
        for item in pages:
            ranges.append([item["start"], item.get("end", item["start"])])
        key = "jingjiang" if ref["book_id"] == BOOK_JJ else "beisong"
        out[key] = {
            "pages": ranges,
            "status": ref.get("review_status", "candidate"),
        }
    return out


def resolve_topic(label: str, by_norm: dict[str, list[dict]]):
    key = LABEL_ALIASES.get(norm(label), norm(label))
    matches = {item["id"]: item for item in by_norm.get(key, [])}
    if len(matches) == 1:
        return next(iter(matches.values()))
    return None


def build_questions(topic_by_norm):
    source_questions = load_json("questions.source.json")
    other_questions = load_json("dataset_xingfa_v1.json")
    other_map = {item["id"]: item for item in other_questions}

    rows = []
    merge_stats = Counter()
    for question in source_questions:
        key = f"{question['year']}-{question['question_number']}"
        other = other_map.get(key) if question["track"] == "非法学" else None
        candidates: dict[str, dict] = {}

        def add_candidate(label, source, role="related", relation_status="candidate", kind_hint=None):
            raw_label = label or ""
            if raw_label in BAD_LABELS:
                if norm(raw_label) not in LABEL_ALIASES:
                    return
            topic = resolve_topic(raw_label, topic_by_norm)
            if topic is None:
                # Keep a specific unresolved label visible as “no page found”.
                # This is preferable to inventing a page or hiding the question.
                if not raw_label or raw_label in BAD_LABELS:
                    return
                topic = {
                    "id": f"xingfa.unresolved.{raw_label}",
                    "label": raw_label,
                    "kind": "offense" if raw_label.endswith("罪") else (kind_hint or "other"),
                    "aliases": [],
                    "references": [],
                }
            canonical = topic["label"]
            if canonical in BAD_LABELS:
                return
            item = candidates.setdefault(topic["id"], {
                "topic": topic,
                "sources": set(),
                "roles": set(),
                "relation_statuses": set(),
                "kind_hint": kind_hint,
            })
            item["sources"].add(source)
            item["roles"].add(role)
            item["relation_statuses"].add(relation_status)

        for relation in question.get("topics", []):
            topic_id = relation.get("topic_id")
            # Correct two OCR-truncated topic IDs before lookup.
            if topic_id == "xingfa.offense.意杀人罪":
                topic_id = "xingfa.offense.故意杀人罪"
            elif topic_id == "xingfa.offense.博罪":
                topic_id = "xingfa.offense.赌博罪"
            label = topic_id.rsplit(".", 1)[-1]
            add_candidate(
                label,
                "codex",
                relation.get("role", "related"),
                relation.get("review_status", "candidate"),
            )

        # A 28-link record and a 15-link record were caused by analysis-page spillover.
        # For records with more than 12 extracted points, keep the independent source only.
        if other and len(other.get("points", [])) <= 12:
            # The other extraction sometimes identified a useful main topic even
            # when its point list was empty.
            if other.get("kaodian"):
                add_candidate(other["kaodian"], "other", "primary", "candidate")
            for index, point in enumerate(other.get("points", [])):
                role = "primary" if point.get("name") == other.get("kaodian") else "related"
                add_candidate(point.get("name"), "other", role, "candidate", point.get("type"))
            merge_stats["other_question_links_used"] += len(other.get("points", []))
        elif other:
            merge_stats["other_spillover_records_skipped"] += 1

        for index, label in enumerate(MANUAL_QUESTION_TOPICS.get(question["id"], [])):
            add_candidate(label, "manual", "primary" if index == 0 else "related", "verified")

        has_specific_offense = any(
            item["topic"].get("kind") == "offense" and item["topic"]["label"] not in CATEGORY_LABELS
            for item in candidates.values()
        )

        ranked = []
        other_primary_norm = norm(other.get("kaodian", "")) if other else ""
        for item in candidates.values():
            topic = item["topic"]
            label = topic["label"]
            if label in BAD_LABELS:
                continue
            if has_specific_offense and label in CATEGORY_LABELS:
                continue
            refs = topic_refs(topic)
            score = 0
            if "codex" in item["sources"]:
                score += 10
            if "other" in item["sources"]:
                score += 12
            if "manual" in item["sources"]:
                score += 35
            if len(item["sources"]) == 2:
                score += 18
            if "primary" in item["roles"]:
                score += 8
            if norm(label) == other_primary_norm:
                score += 18
            if topic.get("kind") == "offense":
                score += 4
            score += 8 if len(refs) == 2 else 3 if refs else -5
            ranked.append((score, label, item, refs))

        ranked.sort(key=lambda row: (-row[0], row[1]))
        # Four options can legitimately involve several offences and doctrines. Eight
        # review entries keeps those cases useful while suppressing OCR spillover.
        ranked = ranked[:8]
        output_topics = []
        for _score, label, item, refs in ranked:
            output_topics.append({
                "label": label,
                "kind": item["topic"].get("kind", item.get("kind_hint") or "other"),
                "role": "primary" if "primary" in item["roles"] else "related",
                "mapping_status": "verified" if "verified" in item["relation_statuses"] else "candidate",
                "references": refs,
            })

        primary = next((item for item in output_topics if item["role"] == "primary"), None)
        if primary is None and output_topics:
            primary = output_topics[0]

        rows.append({
            "id": question["id"],
            "year": question["year"],
            "track": question["track"],
            "type": question["question_type"],
            "number": question["question_number"],
            "primary_topic": primary["label"] if primary else None,
            "topics": output_topics,
        })

    rows.sort(key=lambda item: (-item["year"], item["track"] != "非法学", item["number"]))
    return rows, merge_stats


def audit_payload(rows, topics, merge_stats):
    by_track = Counter(row["track"] for row in rows)
    mapped = sum(bool(row["topics"]) for row in rows)
    both_book_topics = sum(len(topic_refs(topic)) == 2 for topic in topics)
    resolutions = []
    for book, label, theirs, ours, chosen, winner, reason in PAGE_RESOLUTIONS:
        resolutions.append({
            "book": book,
            "topic": label,
            "other_page": theirs,
            "codex_page": ours,
            "chosen_page": chosen,
            "chosen_source": winner,
            "reason": reason,
        })
    return {
        "generated": date.today().isoformat(),
        "scope": {
            "years": [2010, 2026],
            "questions": len(rows),
            "mapped_questions": mapped,
            "by_track": dict(by_track),
            "other_site_questions_before_merge": 425,
            "missing_track_in_other_site": "法学",
            "missing_questions_in_other_site": by_track["法学"],
        },
        "page_comparison": {
            "exact_label_disagreements": len(PAGE_RESOLUTIONS),
            "chosen_from_codex": sum(item[5] == "Codex" for item in PAGE_RESOLUTIONS),
            "chosen_from_other": sum(item[5] == "other" for item in PAGE_RESOLUTIONS),
            "resolutions": resolutions,
        },
        "catalog": {
            "topics": len(topics),
            "topics_with_both_books": both_book_topics,
        },
        "merge": dict(merge_stats),
        "notes": [
            "2010 年法学卷第 21—25 题经原解析复核为民法题，未计入刑法库。",
            "2022 年法学第 25 题涉及非法植入基因编辑、克隆胚胎罪；现有两本教材未检出该罪名。",
            "网站只显示教材印刷页，不提供教材 PDF 或解析全文。",
        ],
    }


HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="2010—2026 年法硕法学、非法学刑法客观题与众合 2027 刑法教材印刷页码速查">
<title>法硕刑法真题 · 教材页码速查</title>
<style>
:root{--bg:#f3f5f8;--card:#fff;--line:#e1e6ee;--text:#172033;--muted:#667085;--blue:#2357a6;--blue-soft:#eef4ff;--teal:#087f6d;--amber:#a85b00;--law:#7c3aed;--nonlaw:#0f6b63;--shadow:0 1px 3px rgba(16,24,40,.06)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.55}.wrap{width:min(980px,100%);margin:auto;padding:26px 18px 72px}.hero{margin-bottom:20px}.hero h1{font-size:26px;margin:0 0 6px;letter-spacing:-.02em}.hero p{margin:0;color:var(--muted);font-size:14px}.controls{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 94%,transparent);backdrop-filter:blur(10px);padding:12px 0 10px}.search{width:100%;height:46px;border:1px solid var(--line);border-radius:11px;background:#fff;padding:0 14px;font-size:15px;outline:none}.search:focus,select:focus{border-color:var(--blue);box-shadow:0 0 0 3px #dbeafe}.filters{display:grid;grid-template-columns:1.15fr 1fr 1fr 1fr;gap:8px;margin-top:9px}.filters.active{padding:8px;border:1px solid #bfd3fb;border-radius:11px;background:var(--blue-soft)}select{min-width:0;height:38px;border:1px solid var(--line);border-radius:9px;background:#fff;padding:0 10px;color:var(--text);font-size:13px}select.active{border-color:var(--blue);background:#e3edff;color:#17458a;font-weight:650}.filter-state{display:flex;align-items:center;gap:9px;margin-top:8px;padding:7px 9px;border:1px solid #bfd3fb;border-radius:9px;background:var(--blue-soft);color:#17458a;font-size:12px}.filter-state[hidden]{display:none}.reset-filters{margin-left:auto;border:1px solid #9dbbf2;border-radius:7px;background:#fff;color:#17458a;padding:4px 9px;font:inherit;font-weight:650;cursor:pointer;white-space:nowrap}.hot{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.hot button{border:1px solid var(--line);background:#fff;color:var(--muted);border-radius:999px;padding:5px 10px;font-size:12px;cursor:pointer}.hot button.on{color:#fff;background:var(--blue);border-color:var(--blue)}.bar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:13px 1px 10px;color:var(--muted);font-size:13px}.notice{background:#fff8e8;border:1px solid #f2d89a;border-radius:10px;padding:9px 12px;color:#7a4a00;font-size:12px;margin-bottom:12px}.list{display:grid;gap:11px}.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px 16px;box-shadow:var(--shadow)}.head{display:flex;gap:7px;align-items:center;flex-wrap:wrap}.qid{font-weight:750;color:var(--blue);font-size:15px}.badge{display:inline-flex;align-items:center;border-radius:6px;padding:2px 7px;font-size:11px;border:1px solid var(--line);color:var(--muted)}.badge.law{color:var(--law);border-color:#ddd0ff;background:#f6f1ff}.badge.nonlaw{color:var(--nonlaw);border-color:#bae3dd;background:#eefaf8}.primary{margin:8px 0 0;font-size:14px}.primary b{color:var(--blue)}.points{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.point{display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap;border:1px solid var(--line);border-radius:8px;background:#fafbfc;padding:4px 8px;font-size:12px}.point.primary-point{background:var(--blue-soft);border-color:#cfe0ff}.point .name{font-weight:620}.page.bs{color:var(--teal);font-weight:650}.page.jj{color:var(--amber);font-weight:650}.page.missing{color:#98a2b3;font-weight:500}.verified{width:7px;height:7px;border-radius:50%;background:#22a06b;display:inline-block}.more,.load{border:1px solid var(--line);background:#fff;color:var(--blue);border-radius:8px;cursor:pointer}.more{font-size:12px;padding:4px 8px}.load{display:block;margin:18px auto 0;padding:9px 22px}.empty{text-align:center;padding:48px 10px;color:var(--muted)}footer{margin-top:28px;border-top:1px solid var(--line);padding-top:16px;color:var(--muted);font-size:12px}footer p{margin:4px 0}.legend{display:flex;gap:14px;flex-wrap:wrap}.legend span{display:inline-flex;align-items:center;gap:5px}
@media(max-width:680px){.wrap{padding:18px 14px 56px}.hero h1{font-size:22px}.filters{grid-template-columns:1fr 1fr}.filter-state{align-items:flex-start}.reset-filters{margin-left:0}.controls{padding-top:8px}.card{padding:14px}.point{width:100%;justify-content:flex-start}.hot{flex-wrap:nowrap;overflow-x:auto;padding-bottom:3px}.hot button{flex:none}.bar{align-items:flex-start;flex-direction:column;gap:2px}}
</style>
</head>
<body><main class="wrap">
<section class="hero"><h1>法硕刑法真题 · 教材页码速查</h1><p>2010—2026 法学 + 非法学客观题 · 众合 2027《背诵一本通》《精讲一本通》</p></section>
<section class="controls" aria-label="题目筛选">
<input id="search" class="search" aria-label="搜索题目" placeholder="搜索年份、题号、考点或罪名，如：2025 法学 抢劫罪">
<div class="filters" id="filters"><select id="track" aria-label="考生类别"><option value="">全部</option><option value="非法学">非法学</option><option value="法学">法学</option></select><select id="year" aria-label="年份"><option value="">全部年份</option></select><select id="type" aria-label="题型"><option value="">全部</option><option value="single">单选</option><option value="multiple">多选</option></select><select id="pageState" aria-label="页码状态"><option value="">全部页码状态</option><option value="both">两本都有页码</option><option value="verified">含已核页码</option><option value="missing">含缺失页码</option></select></div><div class="filter-state" id="filterState" aria-live="polite" hidden><span>当前已启用筛选条件，搜索结果可能减少。</span><button id="resetFilters" class="reset-filters" type="button">重置筛选</button></div>
<div class="hot" id="hot" aria-label="热门考点"></div></section>
<div class="bar"><span id="stats"></span><span>页码均为纸质书页脚的印刷页</span></div>
<div class="notice">提示：同一道题可关联多个罪名或总则考点。绿色圆点表示该页已对照教材页面核验；其余为 OCR/目录候选，仍建议结合题目解析判断。</div>
<section class="list" id="list" aria-live="polite"></section><button id="load" class="load" hidden>显示更多</button>
<footer><div class="legend"><span><i class="verified"></i> 已核页码</span><span>背 P. = 背诵一本通</span><span>精 P. = 精讲一本通</span></div><p>范围：2010—2026 年刑法客观题，法学 250 道、非法学 425 道，共 675 道；2025、2026 两年均已收录。</p><p>本站不提供教材扫描件、真题题面或第三方解析全文。</p><p>版权所有 © 2026 郑宇昕。作者：南京理工大学知识产权学院 郑宇昕。</p></footer>
</main><script>
const DATA=__DATA__;const HOT=__HOT__;const PAGE_SIZE=80;let visible=PAGE_SIZE;const state={q:"",track:"",year:"",type:"",pageState:"",hot:""};
const $=s=>document.querySelector(s);const esc=s=>String(s??"").replace(/[&<>\"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function formatRanges(ranges){return ranges.map(([a,b])=>a===b?String(a):a+"–"+b).join("、")}
function refHtml(topic,key,label,cls){const ref=topic.references[key];if(!ref)return `<span class="page missing">${label} P.—</span>`;const dot=ref.status==="verified"?'<i class="verified" title="已核页码"></i>':'';return `<span class="page ${cls}">${label} P.${formatRanges(ref.pages)}</span>${dot}`}
function hasState(row,value){if(value==="both")return row.topics.some(t=>t.references.beisong&&t.references.jingjiang);if(value==="verified")return row.topics.some(t=>Object.values(t.references).some(r=>r.status==="verified"));if(value==="missing")return row.topics.some(t=>!t.references.beisong||!t.references.jingjiang);return true}
function filtered(){const q=state.q.trim().toLowerCase();return DATA.filter(x=>{if(state.track&&x.track!==state.track)return false;if(state.year&&String(x.year)!==state.year)return false;if(state.type&&x.type!==state.type)return false;if(!hasState(x,state.pageState))return false;if(state.hot&&!x.topics.some(t=>t.label===state.hot))return false;if(q){const hay=[x.id,x.year,x.track,x.number,x.primary_topic,...x.topics.map(t=>t.label)].join(" ").toLowerCase();if(!hay.includes(q))return false}return true})}
function pointHtml(t,index){return `<span class="point ${index===0?'primary-point':''}"><span class="name">${esc(t.label)}</span>${refHtml(t,'beisong','背','bs')}${refHtml(t,'jingjiang','精','jj')}</span>`}
function cardHtml(x){const primary=x.primary_topic?`主考点：<b>${esc(x.primary_topic)}</b>`:'暂未识别主考点';const shown=x.topics.slice(0,6),hidden=x.topics.slice(6);return `<article class="card" data-id="${esc(x.id)}"><div class="head"><span class="qid">${x.year} · 第 ${x.number} 题</span><span class="badge ${x.track==='法学'?'law':'nonlaw'}">${x.track}</span><span class="badge">${x.type==='single'?'单选':'多选'}</span></div><p class="primary">${primary}</p><div class="points">${shown.map(pointHtml).join('')}${hidden.length?`<button class="more" data-more="${esc(x.id)}">另 ${hidden.length} 个考点</button>`:''}</div><template>${hidden.map((t,i)=>pointHtml(t,i+shown.length)).join('')}</template></article>`}
function syncFilterState(){const ids=['track','year','type','pageState'];const active=ids.some(id=>Boolean(state[id]));$('#filters').classList.toggle('active',active);$('#filterState').hidden=!active;for(const id of ids){$('#'+id).classList.toggle('active',Boolean(state[id]))}}
function render(){const rows=filtered();const current=rows.slice(0,visible);syncFilterState();$('#stats').textContent=`找到 ${rows.length} 道题（法学 ${rows.filter(x=>x.track==='法学').length} · 非法学 ${rows.filter(x=>x.track==='非法学').length}）`;$('#list').innerHTML=current.length?current.map(cardHtml).join(''):'<div class="empty">没有匹配的题目</div>';$('#load').hidden=rows.length<=visible}
function resetRender(){visible=PAGE_SIZE;render()}
for(let y=2026;y>=2010;y--){$('#year').insertAdjacentHTML('beforeend',`<option value="${y}">${y} 年</option>`)}
$('#hot').innerHTML=HOT.map(x=>`<button data-hot="${esc(x)}">${esc(x)}</button>`).join('');
$('#search').addEventListener('input',e=>{state.q=e.target.value;resetRender()});for(const id of ['track','year','type','pageState']){$('#'+id).addEventListener('change',e=>{state[id]=e.target.value;resetRender()})}$('#resetFilters').addEventListener('click',()=>{for(const id of ['track','year','type','pageState']){state[id]='';$('#'+id).value=''}resetRender()});
$('#hot').addEventListener('click',e=>{const b=e.target.closest('[data-hot]');if(!b)return;state.hot=state.hot===b.dataset.hot?'':b.dataset.hot;document.querySelectorAll('[data-hot]').forEach(x=>x.classList.toggle('on',x.dataset.hot===state.hot));resetRender()});
$('#list').addEventListener('click',e=>{const b=e.target.closest('[data-more]');if(!b)return;const card=b.closest('.card'),tpl=card.querySelector('template');b.insertAdjacentHTML('beforebegin',tpl.innerHTML);b.remove()});$('#load').addEventListener('click',()=>{visible+=PAGE_SIZE;render()});render();
</script></body></html>'''


def main():
    topics, topic_by_norm = build_topic_catalog()
    rows, merge_stats = build_questions(topic_by_norm)
    audit = audit_payload(rows, topics, merge_stats)

    topic_counts = Counter()
    for row in rows:
        for topic in row["topics"]:
            if topic["kind"] == "offense":
                topic_counts[topic["label"]] += 1
    hot = [label for label, _count in topic_counts.most_common(14)]

    payload = {
        "meta": {
            "generated": date.today().isoformat(),
            "edition": "2027",
            "questions": len(rows),
            "page_definition": "printed",
        },
        "questions": rows,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "topics.json").write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "site_dataset.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "page_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    html = HTML.replace("__DATA__", json.dumps(rows, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__HOT__", json.dumps(hot, ensure_ascii=False, separators=(",", ":")))
    (WEB_DIR / "index.html").write_text(html, encoding="utf-8")
    # GitHub Pages can publish this repository directly from the main branch root.
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"Built {len(rows)} questions: {dict(Counter(row['track'] for row in rows))}")
    print(f"Mapped: {sum(bool(row['topics']) for row in rows)}")
    print(f"Page disagreements resolved: {len(PAGE_RESOLUTIONS)}")


if __name__ == "__main__":
    main()

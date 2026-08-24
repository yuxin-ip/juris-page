"""Link civil-law objective questions to numbered headings in 背诵一本通.

The public catalog has one hard boundary: a civil topic is eligible only when it
has an explicit part-number / sequence-number heading in the 2027 memorisation
book.  Matching therefore starts from that closed catalog and never invents a
finer label from an answer explanation.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GENERIC = {
    "民法", "民法典", "合同", "权利", "义务", "责任", "规则", "原则", "制度",
    "法律责任", "民事责任", "法律关系", "构成要件", "具体情形", "具体类型",
}
SUFFIXES = [
    "的含义和特征", "的含义与特征", "的概念和特征", "的概念与特征", "的概念",
    "的构成要件和效力", "的构成要件与效力", "的构成要件", "的成立要件",
    "的适用条件", "的适用规则", "的承担规则", "的认定规则", "的具体规则",
    "的具体情形", "的具体类型", "的主要类型", "的主要内容", "的内容",
    "的法律后果", "的法律效力", "的效力", "的特征", "的区别", "的联系",
    "的方式", "的范围", "的顺位", "的顺序", "的原则", "的规则",
]
MANUAL_ALIASES = {
    "自甘风险": ["自愿参加具有一定风险的文体活动", "自甘风险"],
    "人体临床试验": ["人体临床试验", "临床试验", "伦理委员会", "知情同意"],
    "民法的时间效力": ["时间效力", "溯及适用", "施行前后"],
    "第三人清偿": ["第三人代为履行", "第三人清偿", "代为清偿"],
    "代物清偿": ["代物清偿", "以物抵债"],
    "违反安全保障义务": ["安全保障义务"],
}

# A small number of explanations describe the rule without using the exact book
# title.  Overrides still point only to numbered headings in the closed catalog.
QUESTION_OVERRIDES = {
    "2010-法学-民法-31": ["4-9"],
    "2010-法学-民法-34": ["3-82"],
    "2010-非法学-民法-37": ["3-35"],
    "2010-非法学-民法-45": ["2-4"],
    "2011-法学-民法-14": ["3-17"],
    "2011-非法学-民法-29": ["4-13"],
    "2011-非法学-民法-34": ["6-22"],
    "2011-非法学-民法-47": ["3-8"],
    "2012-法学-民法-12": ["1-90"],
    "2012-法学-民法-19": ["3-102"],
    "2012-法学-民法-28": ["5-122"],
    "2012-非法学-民法-28": ["3-96"],
    "2012-非法学-民法-29": ["5-60"],
    "2012-非法学-民法-38": ["6-5"],
    "2012-非法学-民法-50": ["6-50"],
    "2013-法学-民法-20": ["4-19"],
    "2013-法学-民法-30": ["4-5"],
    "2013-非法学-民法-31": ["1-1"],
    "2013-非法学-民法-35": ["2-19"],
    "2014-法学-民法-12": ["1-90"],
    "2014-非法学-民法-34": ["5-28"],
    "2014-非法学-民法-50": ["6-22", "6-29"],
    "2014-非法学-民法-49": ["5-43"],
    "2015-非法学-民法-50": ["6-52"],
    "2016-法学-民法-26": ["1-74"],
    "2016-非法学-民法-35": ["1-80"],
    "2018-法学-民法-17": ["7-38"],
    "2018-非法学-民法-27": ["7-38"],
    "2019-法学-民法-16": ["2-35", "2-37"],
    "2019-非法学-民法-26": ["2-35", "2-37"],
    "2019-非法学-民法-34": ["5-45", "5-46"],
    "2019-非法学-民法-37": ["7-28"],
    "2019-非法学-民法-40": ["7-22"],
    "2020-法学-民法-19": ["3-10"],
    "2020-非法学-民法-29": ["3-10"],
    "2020-非法学-民法-37": ["4-18"],
    "2020-非法学-民法-39": ["1-45"],
    "2020-法学-民法-17": ["6-37"],
    "2020-非法学-民法-27": ["6-37"],
    "2021-法学-民法-15": ["5-60"],
    "2021-非法学-民法-25": ["5-60"],
    "2021-非法学-民法-31": ["2-19"],
    "2022-非法学-民法-40": ["4-13"],
    "2023-法学-民法-28": ["2-19", "2-22", "2-21"],
    "2023-非法学-民法-33": ["1-55"],
    "2023-非法学-民法-48": ["2-19", "2-22", "2-21"],
    "2025-非法学-民法-22": ["2-35", "2-37"],
    "2025-非法学-民法-26": ["1-104"],
    "2025-非法学-民法-40": ["1-26", "6-52"],
    "2025-非法学-民法-48": ["1-10"],
    "2026-法学-民法-14": ["5-100"],
    "2026-非法学-民法-24": ["5-100"],
    "2026-法学-民法-16": ["3-37"],
    "2026-非法学-民法-26": ["3-37"],
    "2026-法学-民法-29": ["5-10"],
    "2026-非法学-民法-49": ["5-10"],
    "2025-法学-民法-11": ["3-27"],
    "2025-法学-民法-12": ["2-36"],
    "2025-法学-民法-13": ["5-90"],
    "2025-法学-民法-14": ["5-35"],
    "2025-法学-民法-15": ["7-31"],
    "2025-法学-民法-16": ["1-104"],
    "2025-法学-民法-17": ["5-115"],
    "2025-法学-民法-18": ["3-41", "3-35"],
    "2025-法学-民法-19": ["5-71"],
    "2025-法学-民法-20": ["7-13"],
    "2025-法学-民法-26": ["5-18", "5-56"],
    "2025-法学-民法-27": ["6-72", "6-73"],
    "2025-法学-民法-28": ["1-10"],
    "2025-法学-民法-29": ["2-28"],
    "2025-法学-民法-30": ["3-65"],
    "2011-非法学-民法-48": ["5-54"],
    "2012-非法学-民法-21": ["1-27"],
    "2012-非法学-民法-33": ["4-13"],
    "2012-非法学-民法-39": ["6-35"],
    "2013-非法学-民法-22": ["1-49"],
    "2014-法学-民法-19": ["3-89"],
    "2014-法学-民法-27": ["4-9", "4-13"],
    "2014-非法学-民法-40": ["3-100"],
    "2015-法学-民法-13": ["4-18"],
    "2015-非法学-民法-31": ["5-7"],
    "2016-法学-民法-17": ["3-21"],
    "2016-非法学-民法-27": ["3-21"],
    "2016-非法学-民法-34": ["7-18"],
    "2017-法学-民法-26": ["1-64"],
    "2017-非法学-民法-46": ["1-64"],
    "2018-法学-民法-11": ["1-48"],
    "2018-非法学-民法-21": ["1-48"],
    "2019-非法学-民法-33": ["2-8"],
    "2019-非法学-民法-36": ["4-3"],
    "2020-法学-民法-15": ["2-19"],
    "2020-法学-民法-29": ["6-15"],
    "2020-非法学-民法-25": ["2-19"],
    "2020-非法学-民法-32": ["3-20"],
    "2020-非法学-民法-36": ["7-36"],
    "2020-非法学-民法-49": ["6-15"],
    "2021-法学-民法-17": ["6-4"],
    "2022-非法学-民法-22": ["1-96"],
    "2022-非法学-民法-26": ["2-37"],
    "2022-非法学-民法-27": ["5-33", "5-34"],
    "2022-非法学-民法-30": ["5-23"],
    "2022-非法学-民法-37": ["6-55"],
    "2022-非法学-民法-38": ["1-52"],
    "2024-法学-民法-27": ["3-53", "3-63"],
    "2024-非法学-民法-47": ["3-53", "3-63"],
    "2024-非法学-民法-32": ["7-32"],
    "2024-法学-民法-29": ["3-92", "5-35"],
    "2024-非法学-民法-49": ["3-92", "5-35"],
    "2025-非法学-民法-23": ["5-90"],
    "2025-非法学-民法-24": ["5-3"],
    "2025-非法学-民法-25": ["7-31"],
    "2025-非法学-民法-28": ["3-41", "3-35"],
    "2025-非法学-民法-30": ["7-13"],
    "2025-非法学-民法-32": ["3-20"],
    "2025-非法学-民法-38": ["4-11"],
    "2025-非法学-民法-39": ["1-100"],
    "2025-非法学-民法-49": ["2-28"],
    "2026-法学-民法-13": ["7-38"],
    "2026-法学-民法-18": ["7-13"],
    "2026-非法学-民法-23": ["7-38"],
    "2026-非法学-民法-28": ["7-13"],
    "2026-非法学-民法-33": ["1-28"],
    "2026-非法学-民法-35": ["3-45"],
    "2026-非法学-民法-40": ["6-13"],
}


def norm(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", value or "").lower()


def phrases(label: str) -> list[str]:
    cleaned = re.sub(r"（.*?）|\(.*?\)", "", label)
    values = {norm(label), norm(cleaned)}
    for suffix in SUFFIXES:
        if cleaned.endswith(suffix):
            values.add(norm(cleaned[: -len(suffix)]))
    values.update(norm(item) for item in re.findall(r"（(.*?)）|\((.*?)\)", label) for item in item if item)
    # Comparison headings are useful if both named concepts occur in the analysis.
    for separator in ("与", "和", "、"):
        if separator in cleaned:
            values.update(norm(part) for part in cleaned.split(separator))
    return sorted(
        (value for value in values if len(value) >= 4 and value not in GENERIC),
        key=len,
        reverse=True,
    )


def topic_score(topic: dict, text: str) -> int:
    label = topic["label"]
    normalized_label = norm(label)
    best = 0
    if len(normalized_label) >= 5 and normalized_label in text:
        best = 200 + len(normalized_label)
    for phrase in phrases(label):
        if phrase in text:
            best = max(best, 100 + len(phrase))
    for key, aliases in MANUAL_ALIASES.items():
        if key in label and any(norm(alias) in text for alias in aliases):
            best = max(best, 125 + len(norm(key)))
    return best


def fuzzy_score(topic: dict, text: str) -> float:
    """Lexical fallback for explanations that paraphrase the numbered title."""
    best = 0.0
    for phrase in phrases(topic["label"]):
        bigrams = {phrase[index:index + 2] for index in range(len(phrase) - 1)}
        if not bigrams:
            continue
        coverage = sum(token in text for token in bigrams) / len(bigrams)
        # Three-character overlaps are especially useful for legal terms such as
        # 善意取得、代位继承、无权代理 and 安全保障义务.
        trigrams = {phrase[index:index + 3] for index in range(len(phrase) - 2)}
        tri_coverage = sum(token in text for token in trigrams) / len(trigrams) if trigrams else 0
        best = max(best, coverage * 60 + tri_coverage * 40 + min(len(phrase), 16) / 4)
    return best


def select_topics(question: dict, topics: list[dict]) -> list[dict]:
    by_code = {topic["code"]: topic for topic in topics}
    if question["id"] in QUESTION_OVERRIDES:
        return [by_code[code] for code in QUESTION_OVERRIDES[question["id"]]]
    text = norm(" ".join(str(question.get(key, "")) for key in ("source_analysis_text", "source_question_text")))
    ranked = [(topic_score(topic, text), topic) for topic in topics]
    ranked = [(score, topic) for score, topic in ranked if score]
    ranked.sort(key=lambda item: (-item[0], int(item[1]["code"].split("-")[0]), int(item[1]["code"].split("-")[1])))
    if not ranked:
        fuzzy = sorted(((fuzzy_score(topic, text), topic) for topic in topics), key=lambda item: -item[0])
        if not fuzzy or fuzzy[0][0] < 38:
            return []
        # A fuzzy fallback supplies one conservative umbrella heading.  Further
        # headings are added only by direct terminology matches above.
        return [fuzzy[0][1]]
    top = ranked[0][0]
    # Keep the strongest heading and genuinely independent additional headings;
    # closely related variants of the same phrase are capped to avoid noisy cards.
    selected: list[dict] = []
    seen_core: list[set[str]] = []
    for score, topic in ranked:
        if score < max(104, top - 38) or len(selected) >= 5:
            break
        chars = set(phrases(topic["label"])[-1] if phrases(topic["label"]) else norm(topic["label"]))
        if any(chars and len(chars & previous) / len(chars) > 0.85 for previous in seen_core):
            continue
        selected.append(topic)
        seen_core.append(chars)
    return selected


def load_jingjiang_pages(paths: list[Path]) -> dict[int, str]:
    pages: dict[int, str] = {}
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(raw)
            pages[record["pdf_page"]] = norm(record.get("text", ""))
    return pages


PART_PDF_RANGES = {
    "民法总则": (15, 134),
    "人格权": (135, 154),
    "物权": (155, 243),
    "知识产权": (244, 275),
    "合同": (276, 412),
    "婚姻家庭与继承": (413, 462),
    "侵权责任": (463, 528),
}


def locate_jingjiang(topic: dict, pages: dict[int, str]) -> int | None:
    start, end = PART_PDF_RANGES[topic["part"]]
    candidates = phrases(topic["label"])
    for phrase in candidates:
        matches = [page for page in range(start, end + 1) if phrase in pages.get(page, "")]
        if matches:
            return matches[0] - 10
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=Path(".work/questions/civil.json"))
    parser.add_argument("--topics", type=Path, default=Path(".work/topics/civil-numbered-headings.json"))
    parser.add_argument("--jingjiang-ocr", nargs="*", type=Path, default=[Path("data/ocr_jingjiang_minfa_full.jsonl")])
    parser.add_argument("--links", type=Path, default=Path("data/civil_question_topics.json"))
    parser.add_argument("--pages", type=Path, default=Path("data/civil_topic_pages.json"))
    parser.add_argument("--output", type=Path, default=Path(".work/civil/site_rows.json"))
    parser.add_argument("--audit", type=Path, default=Path(".work/civil/audit.json"))
    args = parser.parse_args()

    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    topics = json.loads(args.topics.read_text(encoding="utf-8"))
    curated_links = json.loads(args.links.read_text(encoding="utf-8")) if args.links.exists() else {}
    curated_pages = json.loads(args.pages.read_text(encoding="utf-8")) if args.pages.exists() else {}
    by_code = {topic["code"]: topic for topic in topics}
    jj_pages = load_jingjiang_pages(args.jingjiang_ocr)
    rows = []
    used = Counter()
    for question in questions:
        link = curated_links.get(question["id"])
        selected = [by_code[code] for code in link["topics"] if code in by_code] if link else select_topics(question, topics)
        mapped = []
        for topic in selected:
            used[topic["code"]] += 1
            page_entry = curated_pages.get(topic["code"], {})
            jj_page = page_entry.get("jingjiang") or (locate_jingjiang(topic, jj_pages) if jj_pages else None)
            bs_page = page_entry.get("beisong", topic["beisong_printed_page"])
            mapped.append({
                "id": f"minfa.numbered.{topic['code']}",
                "code": topic["code"],
                "label": topic["label"],
                "kind": "numbered_knowledge",
                "part": topic["part"],
                "references": {
                    "beisong": {"pages": [[bs_page, bs_page]], "status": "verified"},
                    **({"jingjiang": {"pages": [[jj_page, jj_page]], "status": "candidate"}} if jj_page else {}),
                },
            })
        rows.append({
            "id": question["id"], "year": question["year"], "track": question["track"],
            "subject": "民法", "type": question["question_type"], "number": question["question_number"],
            "answer": question.get("answer"),
            "primary_topic": mapped[0]["label"] if mapped else "",
            "topics": mapped,
        })

    unmapped = [question["id"] for question, row in zip(questions, rows) if not row["topics"]]
    # The published mapping is curated in civil_topic_pages.json.  Auditing the
    # literal OCR locator here produced false negatives when a 精讲 heading used
    # different wording, even though its printed page had already been checked.
    missing_jj = sorted(
        code for code in used
        if not curated_pages.get(code, {}).get("jingjiang")
    )
    audit = {
        "questions": len(rows), "mapped_questions": len(rows) - len(unmapped),
        "unmapped_questions": unmapped, "used_numbered_topics": len(used),
        "missing_jingjiang_topics": missing_jj,
        "part_counts": dict(Counter(topic["part"] for row in rows for topic in row["topics"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

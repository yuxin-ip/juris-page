"""Build copyright-minimal candidate datasets from local extraction artifacts."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


BOOKS = {
    "jingjiang": {
        "id": "zhonghe-jingjiang-xingfa-2027",
        "headings": [
            Path(".work/topics/精讲-heading-candidates.json"),
            Path(".work/topics/精讲-general-heading-candidates.json"),
            Path("data/manual_jingjiang_general_index.json"),
        ],
    },
    "beisong": {
        "id": "zhonghe-beisong-xingfa-2027",
        "headings": [
            Path(".work/topics/背诵-heading-candidates.json"),
            Path(".work/topics/背诵-general-heading-candidates.json"),
            Path("data/manual_beisong_general_index.json"),
        ],
    },
}

ALIASES = {
    "刑法的解释": ["刑法解释", "扩大解释", "缩小解释", "当然解释", "类推解释"],
    "刑罚的目的": ["刑罚目的", "一般预防", "特殊预防"],
    "刑法中的因果关系的认定": ["刑法中的因果关系", "因果关系"],
    "刑法对刑事责任年龄的规定": ["刑事责任年龄"],
    "犯罪主观方面与罪过责任原则": ["犯罪主观方面", "罪过责任原则"],
    "正当防卫的成立条件": ["正当防卫"],
    "特别防卫的成立条件": ["特别防卫"],
    "紧急避险的成立条件": ["紧急避险"],
    "故意犯罪的停止形态": ["犯罪停止形态"],
    "共同犯罪的形式": ["共同犯罪"],
    "共同犯罪与犯罪的停止形态": ["共同犯罪的停止形态"],
    "教唆未遂": ["教唆犯"],
    "关于罪数的判断标准": ["罪数"],
    "死刑": ["死刑缓期执行", "死刑缓期执行的变更"],
    "直接故意和间接故意的异同": ["直接故意", "间接故意"],
    "犯罪过失": ["疏忽大意的过失", "过于自信的过失"],
    "不作为构成犯罪的条件": ["不作为犯罪", "不纯正不作为犯", "作为义务"],
    "自首": ["自动投案", "如实供述"],
    "关于罪数的判断标准": ["处断的一罪", "法定的一罪", "连续犯", "牵连犯", "吸收犯"],
    "挪用公款罪": ["挪用公款归个人使用"],
    "内幕交易、泄露内幕信息罪": ["内幕信息交易罪", "内幕交易罪"],
    "虚开增值税专用发票、用于骗取出口退税、抵扣税款发票罪": ["虚开增值税专用发票罪"],
    "生产、销售、提供假药罪": ["生产、销售假药罪", "销售假药罪"],
    "生产、销售、提供劣药罪": ["生产、销售劣药罪", "销售劣药罪"],
    "生产、销售伪劣产品罪": ["销售伪劣产品罪", "制造销售伪劣产品罪"],
    "拐卖妇女、儿童罪": ["拐卖妇女罪", "拐卖儿童罪"],
    "收买被拐卖的妇女、儿童罪": ["收买被拐卖的妇女罪", "收买被拐卖的儿童罪"],
    "走私、贩卖、运输、制造毒品罪": ["走私毒品罪", "贩卖毒品罪", "运输毒品罪", "制造毒品罪"],
    "组织、领导、参加黑社会性质组织罪": ["组织黑社会性质组织罪", "领导黑社会性质组织罪", "参加黑社会性质组织罪"],
    "窝藏、包庇罪": ["窝藏罪", "包庇罪"],
    "强制猥亵、侮辱罪": ["强制猥亵罪", "强制侮辱罪"],
    "非法持有、私藏枪支、弹药罪": ["非法持有枪支罪", "私藏枪支罪", "非法持有弹药罪", "私藏弹药罪"],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def topic_kind(label: str) -> str:
    doctrine_markers = ("普通型", "携带凶器", "转化型", "罪与", "与职务侵占罪")
    return "doctrine" if any(marker in label for marker in doctrine_markers) else "offense"


def topic_id(label: str, kind: str) -> str:
    return f"xingfa.{kind}.{label}"


def build_topics() -> list[dict]:
    by_label: dict[str, dict] = {}
    for book in BOOKS.values():
        for heading_path in book["headings"]:
            if not heading_path.exists():
                continue
            for heading in load_json(heading_path):
                label = heading["label"]
                kind = heading.get("kind", topic_kind(label))
                topic = by_label.setdefault(
                    label,
                    {
                        "id": topic_id(label, kind),
                        "label": label,
                        "kind": kind,
                        "aliases": ALIASES.get(label, []),
                        "parent_id": None,
                        "references": [],
                    },
                )
                reference = {
                    "book_id": book["id"],
                    "printed_pages": [
                        {"start": heading["printed_page"], "end": heading["printed_page"]}
                    ],
                    "pdf_pages": [
                        {"start": heading["pdf_page"], "end": heading["pdf_page"]}
                    ],
                    "review_status": heading.get("review_status", "candidate"),
                }
                if reference not in topic["references"]:
                    topic["references"].append(reference)
    return sorted(by_label.values(), key=lambda item: (item["kind"], item["label"]))


def text_for_matching(question: dict) -> str:
    return question.get("source_analysis_text") or question.get("source_question_text") or ""


def find_topic_links(text: str, topics: list[dict]) -> list[dict]:
    matches: list[tuple[int, str]] = []
    for topic in topics:
        positions = [text.find(name) for name in [topic["label"], *topic["aliases"]]]
        positions = [position for position in positions if position >= 0]
        if positions:
            matches.append((min(positions), topic["id"]))
    return [
        {"topic_id": topic, "role": "related", "review_status": "candidate"}
        for _, topic in sorted(matches)
    ]


def build_questions(topics: list[dict], raw_path: Path, overrides_dir: Path) -> list[dict]:
    questions: dict[str, dict] = {}
    for raw in load_json(raw_path):
        public = {
            "id": raw["id"],
            "year": raw["year"],
            "track": raw["track"],
            "subject": "刑法",
            "question_type": raw["question_type"],
            "question_number": raw["question_number"],
            "answer": raw.get("answer"),
            "topics": find_topic_links(text_for_matching(raw), topics),
        }
        questions[public["id"]] = public

    labels = {
        name: topic
        for topic in topics
        for name in [topic["label"], *topic["aliases"]]
    }
    for path in sorted(overrides_dir.glob("*.json")):
        override = load_json(path)
        for source in override["questions"]:
            question_id = (
                f"{override['year']}-{override['track']}-刑法-{source['number']:02d}"
            )
            links = []
            linked_ids: dict[str, dict] = {}
            for role in ("primary", "related"):
                for label in source.get(role, []):
                    topic = labels.get(label)
                    if not topic:
                        continue
                    existing = linked_ids.get(topic["id"])
                    if existing:
                        if role == "primary":
                            existing["role"] = "primary"
                        continue
                    link = {
                        "topic_id": topic["id"],
                        "role": role,
                        "review_status": "candidate",
                    }
                    linked_ids[topic["id"]] = link
                    links.append(link)
            questions[question_id] = {
                "id": question_id,
                "year": override["year"],
                "track": override["track"],
                "subject": "刑法",
                "question_type": source["type"],
                "question_number": source["number"],
                "answer": source.get("answer"),
                "topics": links,
            }
    return sorted(
        questions.values(), key=lambda item: (item["year"], item["track"], item["question_number"])
    )


def build_coverage(questions: list[dict]) -> dict:
    by_source: dict[tuple[int, str], Counter] = defaultdict(Counter)
    for question in questions:
        bucket = by_source[(question["year"], question["track"])]
        bucket["questions"] += 1
        bucket["mapped"] += bool(question["topics"])
        bucket["unmapped"] += not question["topics"]
        bucket["topic_links"] += len(question["topics"])
    return {
        "summary": {
            "questions": len(questions),
            "mapped": sum(bool(question["topics"]) for question in questions),
            "unmapped": sum(not question["topics"] for question in questions),
            "topic_links": sum(len(question["topics"]) for question in questions),
        },
        "by_year_track": [
            {"year": year, "track": track, **dict(counts)}
            for (year, track), counts in sorted(by_source.items())
        ],
    }


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path(".work/questions/criminal.json"))
    parser.add_argument("--overrides", type=Path, default=Path("data/source_overrides"))
    parser.add_argument("--output", type=Path, default=Path("data"))
    args = parser.parse_args()
    topics = build_topics()
    questions = build_questions(topics, args.raw, args.overrides)
    coverage = build_coverage(questions)
    coverage["topics"] = {
        "total": len(topics),
        "with_both_books": sum(len(topic["references"]) >= 2 for topic in topics),
        "with_one_book": sum(len(topic["references"]) == 1 for topic in topics),
    }
    coverage["scope_notes"] = [
        "2010 年法学卷第 21—25 题为民法客观题，未纳入刑法题库。",
        "2022 年法学第 25 题涉及非法植入基因编辑、克隆胚胎罪；两本现有教材未检出该罪名，暂不提供页码。",
    ]
    write_json(args.output / "topics.json", topics)
    write_json(args.output / "questions.json", questions)
    write_json(args.output / "coverage.json", coverage)
    print(json.dumps(coverage["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()

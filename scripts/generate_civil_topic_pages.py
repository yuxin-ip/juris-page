"""Locate used numbered civil topics in the two 2027 textbooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_civil_dataset import PART_PDF_RANGES, norm, phrases  # noqa: E402


BEISONG_RANGES = {
    "民法总则": (3, 57), "人格权": (59, 71), "物权": (74, 110),
    "知识产权": (114, 124), "合同": (127, 179),
    "婚姻家庭与继承": (183, 214), "侵权责任": (206, 224),
}
JINGJIANG_PAGE_OVERRIDES = {
    "4-12": 244,
    "4-13": 245,
    "4-14": 248,
}


def estimate_pdf_page(topic: dict) -> float:
    bs_start, bs_end = BEISONG_RANGES[topic["part"]]
    jj_start, jj_end = PART_PDF_RANGES[topic["part"]]
    ratio = (topic["beisong_printed_page"] - bs_start) / max(1, bs_end - bs_start)
    return jj_start + max(0, min(1, ratio)) * (jj_end - jj_start)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--topics", type=Path, default=Path(".work/topics/civil-numbered-headings.json"))
    parser.add_argument("--links", type=Path, default=Path("data/civil_question_topics.json"))
    parser.add_argument("--ocr", type=Path, default=Path("data/ocr_jingjiang_minfa_full.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/civil_topic_pages.json"))
    args = parser.parse_args()

    topics = json.loads(args.topics.read_text(encoding="utf-8"))
    links = json.loads(args.links.read_text(encoding="utf-8"))
    used = {code for link in links.values() for code in link["topics"]}
    topics = [topic for topic in topics if topic["code"] in used]
    pages = {}
    for raw in args.ocr.read_text(encoding="utf-8").splitlines():
        record = json.loads(raw)
        # Headings and rule names usually occur in the first portion of a page.
        pages[record["pdf_page"]] = record.get("text", "")[:2200]

    model = SentenceTransformer(args.model)
    page_numbers = sorted(pages)
    page_vectors = model.encode(
        [pages[page] for page in page_numbers], normalize_embeddings=True,
        batch_size=32, show_progress_bar=False,
    )
    page_index = {page: index for index, page in enumerate(page_numbers)}
    topic_vectors = model.encode(
        [f"{topic['part']}：{topic['label']}" for topic in topics],
        normalize_embeddings=True, batch_size=64, show_progress_bar=False,
    )

    result = {}
    for index, topic in enumerate(topics):
        start, end = PART_PDF_RANGES[topic["part"]]
        estimate = estimate_pdf_page(topic)
        normalized_pages = {page: norm(pages.get(page, "")) for page in range(start, end + 1)}
        exact = []
        for phrase in phrases(topic["label"]):
            matches = [page for page, text in normalized_pages.items() if phrase in text]
            if matches:
                exact.extend(matches)
                break
        if exact:
            pdf_page = min(set(exact), key=lambda page: abs(page - estimate))
            method = "term+order"
            confidence = 0.99
        else:
            # Compare pages near the topic's proportional position.  The order
            # of the two books is nearly parallel, so this removes attractive
            # but irrelevant mentions elsewhere in the same part.
            window = [page for page in range(start, end + 1) if abs(page - estimate) <= 12]
            scores = []
            for page in window:
                semantic = float(topic_vectors[index] @ page_vectors[page_index[page]])
                proximity = max(0.0, 1.0 - abs(page - estimate) / 13) * 0.11
                scores.append((semantic + proximity, semantic, page))
            combined, semantic, pdf_page = max(scores)
            method = "semantic+order"
            confidence = round(semantic, 4)
        result[topic["code"]] = {
            "beisong": topic["beisong_printed_page"],
            "jingjiang": pdf_page - 10,
            "method": method,
            "confidence": confidence,
        }
        if topic["code"] in JINGJIANG_PAGE_OVERRIDES:
            result[topic["code"]].update({
                "jingjiang": JINGJIANG_PAGE_OVERRIDES[topic["code"]],
                "method": "rendered-page-audit",
                "confidence": 1.0,
            })

    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Located {len(result)} used civil topics in both books")
    print("semantic candidates", sum(item["method"].startswith("semantic") for item in result.values()))


if __name__ == "__main__":
    main()

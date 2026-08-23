"""Extract candidate criminal-law general-rule headings from OCR output.

The output contains labels and page coordinates only; it intentionally omits
the textbook body text so it can safely feed the public page-index dataset.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CHINESE_NUMBER = "一二三四五六七八九十百〇零两"
PREFIX = rf"^[{CHINESE_NUMBER}0-9]+[、.]\s*[简筒首]述\s*"
PATTERN = re.compile(
    PREFIX
    + r"(?P<label>.+?)(?:的概念(?:和|及|与)?|的特征|的内容|的构成|的效力|$)"
)

OCR_CORRECTIONS = {
    "犯墨构成的章义": "犯罪构成的意义",
    "因果关系与荆事责任的关系": "因果关系与刑事责任的关系",
    "刑法对别事责任年龄的规定": "刑法对刑事责任年龄的规定",
    "过失犯暴的罪责": "过失犯的罪责",
    "犯罪既遵": "犯罪既遂",
    "把罪中止的类型": "犯罪中止的类型",
    "共月犯罪与犯罪的停止形态": "共同犯罪与犯罪的停止形态",
    "教喷未遂": "教唆未遂",
    "刑事贵任": "刑事责任",
    "数罪井罚": "数罪并罚",
    "数罪开罚的原期": "数罪并罚的原则",
    "数罪井罚原则的限制加重原则": "数罪并罚原则的限制加重原则",
    "数免": "赦免",
}


def clean_label(label: str) -> str:
    label = re.sub(r"[（(].*$", "", label).strip(" ：:，,。.")
    return OCR_CORRECTIONS.get(label, label)


def extract(path: Path, offset: int, max_pdf_page: int | None = None) -> list[dict]:
    headings: list[dict] = []
    seen: set[tuple[int, str]] = set()
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            record = json.loads(raw_line)
            if max_pdf_page is not None and record["pdf_page"] > max_pdf_page:
                continue
            for line in record["lines"]:
                match = PATTERN.match(line["text"].strip())
                if not match:
                    continue
                label = clean_label(match.group("label"))
                # Specific罪名 already live in the 分则 index.  This script is
                # for general-rule concepts and must not duplicate them.
                if not label or label.endswith("罪"):
                    continue
                key = (record["pdf_page"], label)
                if key in seen:
                    continue
                seen.add(key)
                headings.append(
                    {
                        "label": label,
                        "kind": "general_rule",
                        "printed_page": record["pdf_page"] - offset,
                        "pdf_page": record["pdf_page"],
                        "ocr_score": line["score"],
                    }
                )
    return sorted(headings, key=lambda item: (item["pdf_page"], item["label"]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ocr", type=Path)
    parser.add_argument("--offset", type=int, required=True)
    parser.add_argument("--max-pdf-page", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    headings = extract(args.ocr, args.offset, args.max_pdf_page)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(headings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Extracted {len(headings)} candidate general-rule headings to {args.output}")


if __name__ == "__main__":
    main()

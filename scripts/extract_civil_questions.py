"""Extract civil-law objective-question blocks from the local exam corpus.

The working output keeps source question/explanation text under ``.work`` only.
Public site data is built separately and contains only question metadata, the
numbered textbook heading, and printed-page references.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]

from extract_criminal_questions import (
    ANSWER,
    QUESTION_START,
    normalize_pdf_text,
    parse_answer_table,
    parse_ocr_jsonl,
    source_files,
)


def is_civil_objective(year: int, track: str, number: int) -> tuple[bool, str | None]:
    if track == "法学":
        if year == 2010:
            if 20 <= number <= 29:
                return True, "single"
            if 30 <= number <= 34:
                return True, "multiple"
            return False, None
        if 11 <= number <= 20:
            return True, "single"
        if 26 <= number <= 30:
            return True, "multiple"
        return False, None
    if year == 2010:
        if 31 <= number <= 50:
            return True, "single"
        if 51 <= number <= 55:
            return True, "multiple"
        return False, None
    elif 21 <= number <= 40:
        return True, "single"
    if 46 <= number <= 50:
        return True, "multiple"
    return False, None


def parse_analysis_text(year: int, track: str, text: str, source_pdf: str) -> list[dict]:
    text = re.sub(r"\s+", "", text)
    matches = list(QUESTION_START.finditer(text))
    records: list[dict] = []
    seen: set[int] = set()
    for index, match in enumerate(matches):
        raw_number = match.group("number")
        number = 1 if raw_number in {"l", "I"} else int(raw_number)
        include, question_type = is_civil_objective(year, track, number)
        if not include or number in seen:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        explanation = text[match.start():end]
        answer_match = ANSWER.search(explanation[:80])
        records.append({
            "id": f"{year}-{track}-民法-{number:02d}",
            "year": year,
            "track": track,
            "subject": "民法",
            "question_type": question_type,
            "question_number": number,
            "answer": answer_match.group(1) if answer_match else None,
            "source_pdf": source_pdf,
            "source_analysis_text": explanation,
        })
        seen.add(number)
    return records


def parse_question_paper_2026(path: Path, track: str, root: Path) -> list[dict]:
    reader = PdfReader(str(path))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    marker = f"专业基础（{track}）答案"
    split_at = full_text.find(marker, 500)
    if split_at < 0:
        raise ValueError(f"Could not find answer section in {path}")
    paper_text, answer_text = full_text[:split_at], full_text[split_at:]
    answers = parse_answer_table(answer_text)
    starts = list(re.finditer(r"(?m)^\s*(\d{1,2})[.．]\s*", paper_text))
    records: list[dict] = []
    seen: set[int] = set()
    for index, match in enumerate(starts):
        number = int(match.group(1))
        include, question_type = is_civil_objective(2026, track, number)
        if not include or number in seen:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(paper_text)
        records.append({
            "id": f"2026-{track}-民法-{number:02d}",
            "year": 2026,
            "track": track,
            "subject": "民法",
            "question_type": question_type,
            "question_number": number,
            "answer": answers.get(number),
            "source_pdf": str(path.relative_to(root)).replace("\\", "/"),
            "source_question_text": paper_text[match.start():end].strip(),
        })
        seen.add(number)
    return records


def add_2025_nonlaw(records: list[dict], source: Path) -> None:
    if not source.exists():
        return
    for item in json.loads(source.read_text(encoding="utf-8")):
        if item.get("subject") != "民法":
            continue
        number = item["no"]
        records.append({
            "id": f"2025-非法学-民法-{number:02d}",
            "year": 2025,
            "track": "非法学",
            "subject": "民法",
            "question_type": "single" if item["type"] == "single" else "multiple",
            "question_number": number,
            "answer": item.get("answer"),
            "source_pdf": "2025年法硕非法学基础课真题.pdf",
            "source_question_text": item.get("stem", "") + " " + " ".join(item.get("options", {}).values()),
        })


def enrich_from_question_paper(records: list[dict], year: int, track: str, path: Path) -> None:
    """Attach the stem/options when an analysis PDF contains only a bare answer."""
    text = normalize_pdf_text(path)
    starts = list(re.finditer(r"(?<!\d)(\d{1,2})[.．](?=[A-Za-z\u4e00-\u9fff])", text))
    target = {(row["question_number"]): row for row in records if row["year"] == year and row["track"] == track}
    for index, match in enumerate(starts):
        number = int(match.group(1))
        if number not in target:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        target[number]["source_question_text"] = text[match.start():end].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("法硕小程序开发/考研法硕历年真题，法学+非法学"))
    parser.add_argument("--output", type=Path, default=Path(".work/questions/civil.json"))
    parser.add_argument("--questions-2025", type=Path, default=Path("data/questions_2025.json"))
    parser.add_argument("--ocr-2022-law", type=Path, default=Path("data/ocr_2022_law_foundation.jsonl"))
    args = parser.parse_args()

    records: list[dict] = []
    for year, track, path in source_files(args.root):
        text = normalize_pdf_text(path)
        records.extend(parse_analysis_text(year, track, text, str(path.relative_to(args.root)).replace("\\", "/")))
        if year == 2010 and track == "非法学":
            malformed = re.search(r"5I[.．].*?(?=52[.．])", text)
            if malformed:
                records.append({
                    "id": "2010-非法学-民法-51", "year": 2010, "track": "非法学",
                    "subject": "民法", "question_type": "multiple", "question_number": 51,
                    "answer": "AC", "source_pdf": str(path.relative_to(args.root)).replace("\\", "/"),
                    "source_analysis_text": malformed.group(0),
                })
    if args.ocr_2022_law.exists():
        records = [row for row in records if not (row["year"] == 2022 and row["track"] == "法学")]
        records.extend(parse_analysis_text(
            2022, "法学", parse_ocr_jsonl(args.ocr_2022_law),
            "2022年全国法律硕士（法学）基础课解析.pdf",
        ))
    add_2025_nonlaw(records, args.questions_2025)
    override_path = ROOT / "data" / "source_overrides" / "2025-law-civil.json"
    if override_path.exists():
        records.extend(json.loads(override_path.read_text(encoding="utf-8")))
    for track in ("法学", "非法学"):
        filename = f"2026年全国硕士研究生招生考试法律硕士专业基础（{track}）及参考答案.pdf"
        matches = list(args.root.rglob(filename))
        if matches:
            records.extend(parse_question_paper_2026(matches[0], track, args.root))

    question_patterns = {
        "法学": "2022年全国法律硕士（法学）专业基础课真题.pdf",
        "非法学": "2022年法硕（非法学）基础课真题.pdf",
    }
    for track, filename in question_patterns.items():
        matches = list(args.root.rglob(filename))
        if matches:
            enrich_from_question_paper(records, 2022, track, matches[0])

    by_id = {record["id"]: record for record in records}
    output = sorted(by_id.values(), key=lambda row: (row["year"], row["track"], row["question_number"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(output)} civil-law objective questions")
    for year in range(2010, 2027):
        counts = {track: sum(row["year"] == year and row["track"] == track for row in output) for track in ("法学", "非法学")}
        print(year, counts)


if __name__ == "__main__":
    main()

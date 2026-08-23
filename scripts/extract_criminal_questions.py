"""Extract criminal-law objective-question explanations from source PDFs.

The extracted explanation text is written under .work/ and is not intended for
publication. Public datasets should contain only metadata, topic labels, and
book-page references derived from these sources.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader


QUESTION_START = re.compile(
    r"(?<!\d)(?P<number>\d{1,2}|[lI])"
    r"[.．、](?=[【\[［（(]?(?:参考)?答案)"
)
ANSWER = re.compile(r"(?:参考)?答案[】\]］）)]*([A-D]{1,4})")


def normalize_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    # Some source PDFs position every glyph separately, producing one character
    # per line. Whitespace is not semantically important for the parsing below.
    return re.sub(r"\s+", "", text)


def source_files(root: Path) -> list[tuple[int, str, Path]]:
    sources: list[tuple[int, str, Path]] = []
    for path in root.rglob("*.pdf"):
        if "基础课解析（2010-2024）" not in str(path):
            continue
        match = re.match(r"(20\d{2})", path.name)
        if not match:
            continue
        track = "非法学" if "09.法硕非法学" in str(path) else "法学"
        sources.append((int(match.group(1)), track, path))
    return sorted(sources)


def is_criminal_objective(year: int, track: str, number: int) -> tuple[bool, str | None]:
    if track == "法学":
        if 1 <= number <= 10:
            return True, "single"
        # 2010 法学卷的第 21—25 题为民法客观题，不能按后续年份
        # 的法学卷结构套用为刑法多选题。
        if year == 2010:
            return False, None
        if 21 <= number <= 25:
            return True, "multiple"
        return False, None
    if year == 2010:
        if 1 <= number <= 20:
            return True, "single"
        if 21 <= number <= 25:
            return True, "multiple"
        return False, None
    if 1 <= number <= 20:
        return True, "single"
    if 41 <= number <= 45:
        return True, "multiple"
    return False, None


def parse_analysis_text(
    year: int, track: str, text: str, source_pdf: str
) -> list[dict]:
    text = re.sub(r"\s+", "", text)
    matches = list(QUESTION_START.finditer(text))
    records: list[dict] = []
    seen: set[int] = set()
    for index, match in enumerate(matches):
        number_text = match.group("number")
        number = 1 if number_text in {"l", "I"} else int(number_text)
        include, question_type = is_criminal_objective(year, track, number)
        if not include or number in seen:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        explanation = text[match.start():end]
        answer_match = ANSWER.search(explanation[:80])
        records.append(
            {
                "id": f"{year}-{track}-刑法-{number:02d}",
                "year": year,
                "track": track,
                "subject": "刑法",
                "question_type": question_type,
                "question_number": number,
                "answer": answer_match.group(1) if answer_match else None,
                "source_pdf": source_pdf,
                "source_analysis_text": explanation,
            }
        )
        seen.add(number)
    return records


def parse_source(year: int, track: str, path: Path, root: Path) -> list[dict]:
    return parse_analysis_text(
        year,
        track,
        normalize_pdf_text(path),
        str(path.relative_to(root)).replace("\\", "/"),
    )


def parse_ocr_jsonl(path: Path) -> str:
    pages: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            pages.append((record["pdf_page"], record["text"]))
    return "\n".join(text for _, text in sorted(pages))


def parse_answer_table(text: str) -> dict[int, str]:
    answers: dict[int, str] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index in range(len(lines) - 1):
        if not re.fullmatch(r"\d{1,2}(?:\s+\d{1,2})+", lines[index]):
            continue
        numbers = [int(value) for value in lines[index].split()]
        values = re.findall(r"[A-D](?:\([A-D]+\))?[A-D]*", lines[index + 1])
        if len(numbers) == len(values):
            answers.update(zip(numbers, values))
    return answers


def parse_stacked_answer_table(text: str) -> dict[int, str]:
    """Read OCR answer tables whose question numbers and answers are stacked.

    The 2025 scanned answer sheet prints each eight-question group as two
    columns: first eight number rows, then eight answer rows.  This helper is
    deliberately narrow and preserves only answer letters, never explanations.
    """
    tokens = [line.strip() for line in text.splitlines() if line.strip()]
    answers: dict[int, str] = {}
    index = 0
    while index < len(tokens):
        if not re.fullmatch(r"\d{1,2}", tokens[index]):
            index += 1
            continue
        numbers: list[int] = []
        cursor = index
        while cursor < len(tokens) and re.fullmatch(r"\d{1,2}", tokens[cursor]):
            numbers.append(int(tokens[cursor]))
            cursor += 1
        values: list[str] = []
        while cursor < len(tokens) and len(values) < len(numbers):
            token = tokens[cursor].replace(" ", "")
            if re.fullmatch(r"[A-D]{1,5}", token):
                values.append(token)
                cursor += 1
                continue
            break
        if len(numbers) >= 2 and len(values) == len(numbers):
            answers.update(zip(numbers, values))
            index = cursor
        else:
            index += 1
    return answers


def parse_question_paper_2026(path: Path, track: str, root: Path) -> list[dict]:
    reader = PdfReader(str(path))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    answer_marker = f"专业基础（{track}）答案"
    split_at = full_text.find(answer_marker, 500)
    if split_at < 0:
        raise ValueError(f"Could not find answer section in {path}")
    paper_text, answer_text = full_text[:split_at], full_text[split_at:]
    answers = parse_answer_table(answer_text)
    starts = list(re.finditer(r"(?m)^\s*(\d{1,2})[.．]\s*", paper_text))
    records: list[dict] = []
    seen: set[int] = set()
    for index, match in enumerate(starts):
        number = int(match.group(1))
        include, question_type = is_criminal_objective(2026, track, number)
        if not include or number in seen:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(paper_text)
        question_text = paper_text[match.start():end].strip()
        records.append(
            {
                "id": f"2026-{track}-刑法-{number:02d}",
                "year": 2026,
                "track": track,
                "subject": "刑法",
                "question_type": question_type,
                "question_number": number,
                "answer": answers.get(number),
                "source_pdf": str(path.relative_to(root)).replace("\\", "/"),
                "source_question_text": question_text,
            }
        )
        seen.add(number)
    return records


def parse_ocr_question_paper(
    year: int,
    track: str,
    paper_ocr: Path,
    answer_ocr: Path,
    source_pdf: str,
) -> list[dict]:
    """Extract objective question blocks from a scanned question paper."""
    paper_text = parse_ocr_jsonl(paper_ocr)
    answers = parse_stacked_answer_table(parse_ocr_jsonl(answer_ocr))
    starts = list(re.finditer(r"(?m)^\s*(\d{1,2})[.．、]\s*", paper_text))
    records: list[dict] = []
    seen: set[int] = set()
    for index, match in enumerate(starts):
        number = int(match.group(1))
        include, question_type = is_criminal_objective(year, track, number)
        if not include or number in seen:
            continue
        end = starts[index + 1].start() if index + 1 < len(starts) else len(paper_text)
        records.append(
            {
                "id": f"{year}-{track}-刑法-{number:02d}",
                "year": year,
                "track": track,
                "subject": "刑法",
                "question_type": question_type,
                "question_number": number,
                "answer": answers.get(number),
                "source_pdf": source_pdf,
                "source_question_text": paper_text[match.start():end].strip(),
            }
        )
        seen.add(number)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path("考研法硕历年真题，法学+非法学")
    )
    parser.add_argument("--output", type=Path, default=Path(".work/questions/criminal.json"))
    parser.add_argument(
        "--ocr-2022-law",
        type=Path,
        default=Path(".work/ocr/2022-法学-基础课解析.jsonl"),
    )
    parser.add_argument(
        "--ocr-2025-nonlaw-paper",
        type=Path,
        default=Path(".work/ocr/2025-非法学-专业基础-题干.jsonl"),
    )
    parser.add_argument(
        "--ocr-2025-nonlaw-answers",
        type=Path,
        default=Path(".work/ocr/2025-非法学-专业基础-答案.jsonl"),
    )
    args = parser.parse_args()

    records: list[dict] = []
    summaries: list[dict] = []
    for year, track, path in source_files(args.root):
        extracted = parse_source(year, track, path, args.root)
        records.extend(extracted)
        summaries.append(
            {
                "year": year,
                "track": track,
                "questions": len(extracted),
                "source": path.name,
            }
        )
    if args.ocr_2022_law.exists():
        records = [
            record
            for record in records
            if not (record["year"] == 2022 and record["track"] == "法学")
        ]
        extracted = parse_analysis_text(
            2022,
            "法学",
            parse_ocr_jsonl(args.ocr_2022_law),
            "2022年全国法律硕士（法学）基础课解析.pdf",
        )
        records.extend(extracted)
        summaries.append(
            {
                "year": 2022,
                "track": "法学",
                "questions": len(extracted),
                "source": "2022年全国法律硕士（法学）基础课解析.pdf (OCR)",
            }
        )
    for track in ("法学", "非法学"):
        filename = f"2026年全国硕士研究生招生考试法律硕士专业基础（{track}）及参考答案.pdf"
        matches = list(args.root.rglob(filename))
        if not matches:
            continue
        path = matches[0]
        extracted = parse_question_paper_2026(path, track, args.root)
        records.extend(extracted)
        summaries.append(
            {
                "year": 2026,
                "track": track,
                "questions": len(extracted),
                "source": path.name,
            }
        )
    if args.ocr_2025_nonlaw_paper.exists() and args.ocr_2025_nonlaw_answers.exists():
        extracted = parse_ocr_question_paper(
            2025,
            "非法学",
            args.ocr_2025_nonlaw_paper,
            args.ocr_2025_nonlaw_answers,
            "2025年法硕(非法学)专业基础真题.pdf",
        )
        records.extend(extracted)
        summaries.append(
            {
                "year": 2025,
                "track": "非法学",
                "questions": len(extracted),
                "source": "2025年法硕(非法学)专业基础真题.pdf (OCR)",
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    print(f"Total criminal-law objective questions: {len(records)}")


if __name__ == "__main__":
    main()

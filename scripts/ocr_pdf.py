"""OCR a PDF into resumable JSON Lines, one record per page."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pypdfium2 as pdfium


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / ".tools" / "python"))

from rapidocr_onnxruntime import RapidOCR  # noqa: E402


def parse_pages(value: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            pages.update(range(int(start_text), int(end_text) + 1))
        else:
            pages.add(int(part))
    invalid = [page for page in pages if page < 1 or page > page_count]
    if invalid:
        raise ValueError(f"Pages outside 1..{page_count}: {invalid}")
    return sorted(pages)


def completed_pages(output: Path) -> set[int]:
    if not output.exists():
        return set()
    completed: set[int] = set()
    with output.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                completed.add(json.loads(line)["pdf_page"])
    return completed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", required=True, help="One-based pages, e.g. 1-10,15")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scale", type=float, default=1.6)
    args = parser.parse_args()

    document = pdfium.PdfDocument(args.pdf)
    requested = parse_pages(args.pages, len(document))
    done = completed_pages(args.output)
    pending = [page for page in requested if page not in done]
    args.output.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"OCR {args.pdf.name}: requested={len(requested)} "
        f"completed={len(done & set(requested))} pending={len(pending)}",
        flush=True,
    )
    if not pending:
        return

    engine = RapidOCR()
    started = time.monotonic()
    with args.output.open("a", encoding="utf-8", newline="\n") as handle:
        for index, page_number in enumerate(pending, start=1):
            image = document[page_number - 1].render(scale=args.scale).to_numpy()
            result, _ = engine(image)
            lines = []
            for box, text, score in result or []:
                lines.append(
                    {
                        "text": text,
                        "score": round(float(score), 4),
                        "box": [[round(float(x), 1), round(float(y), 1)] for x, y in box],
                    }
                )
            record = {
                "pdf_page": page_number,
                "text": "\n".join(line["text"] for line in lines),
                "lines": lines,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            if index == 1 or index % 10 == 0 or index == len(pending):
                elapsed = time.monotonic() - started
                rate = index / elapsed if elapsed else 0
                print(
                    f"{args.pdf.name}: {index}/{len(pending)} pages "
                    f"({rate:.2f} pages/s), latest PDF page {page_number}",
                    flush=True,
                )


if __name__ == "__main__":
    main()

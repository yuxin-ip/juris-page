"""Render selected PDF pages to PNG files or a contact sheet.

Examples:
    python scripts/render_pdf_pages.py book.pdf --pages 1-20 --output tmp/book
    python scripts/render_pdf_pages.py book.pdf --pages 1,3,5 --contact-sheet tmp/sheet.jpg
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


def parse_pages(value: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start, end = int(start_text), int(end_text)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    invalid = [page for page in pages if page < 1 or page > page_count]
    if invalid:
        raise ValueError(f"Pages outside 1..{page_count}: {invalid}")
    return sorted(pages)


def render_page(document: pdfium.PdfDocument, page_number: int, scale: float) -> Image.Image:
    page = document[page_number - 1]
    bitmap = page.render(scale=scale)
    return bitmap.to_pil().convert("RGB")


def create_contact_sheet(images: list[tuple[int, Image.Image]], target: Path) -> None:
    thumb_width = 360
    label_height = 34
    columns = 4
    thumbs: list[tuple[int, Image.Image]] = []
    for page_number, image in images:
        height = round(image.height * thumb_width / image.width)
        thumbs.append((page_number, image.resize((thumb_width, height))))
    cell_height = max(image.height for _, image in thumbs) + label_height
    rows = math.ceil(len(thumbs) / columns)
    sheet = Image.new("RGB", (columns * thumb_width, rows * cell_height), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (page_number, image) in enumerate(thumbs):
        x = index % columns * thumb_width
        y = index // columns * cell_height
        sheet.paste(image, (x, y + label_height))
        draw.text((x + 8, y + 8), f"PDF page {page_number}", fill="black")
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, quality=88)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages", required=True, help="One-based pages, e.g. 1-10,15")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument("--scale", type=float, default=1.5)
    args = parser.parse_args()

    if not args.output and not args.contact_sheet:
        parser.error("Provide --output or --contact-sheet")

    document = pdfium.PdfDocument(args.pdf)
    pages = parse_pages(args.pages, len(document))
    rendered = [(page_number, render_page(document, page_number, args.scale)) for page_number in pages]

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        for page_number, image in rendered:
            image.save(args.output / f"page-{page_number:04d}.png")
    if args.contact_sheet:
        create_contact_sheet(rendered, args.contact_sheet)


if __name__ == "__main__":
    main()

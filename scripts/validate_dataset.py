"""Validate the public, copyright-minimal dataset before publishing."""

from __future__ import annotations

import json
import sys
from pathlib import Path


DATA = Path("data")


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def unique(values: list[str], name: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            errors.append(f"duplicate {name}: {value}")
        seen.add(value)
    return seen


def main() -> None:
    books = load("books.json")
    topics = load("topics.json")
    questions = load("questions.json")
    errors: list[str] = []

    book_ids = unique([item["id"] for item in books], "book id", errors)
    topic_ids = unique([item["id"] for item in topics], "topic id", errors)
    unique([item["id"] for item in questions], "question id", errors)

    for topic in topics:
        for reference in topic["references"]:
            if reference["book_id"] not in book_ids:
                errors.append(f"unknown book in {topic['id']}")
            for key in ("printed_pages", "pdf_pages"):
                for page_range in reference[key]:
                    if page_range["start"] < 1 or page_range["end"] < page_range["start"]:
                        errors.append(f"invalid {key} in {topic['id']}")

    for question in questions:
        links = question["topics"]
        if len({link["topic_id"] for link in links}) != len(links):
            errors.append(f"duplicate topic link in {question['id']}")
        for link in links:
            if link["topic_id"] not in topic_ids:
                errors.append(f"unknown topic in {question['id']}: {link['topic_id']}")

    if errors:
        print("Dataset validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        sys.exit(1)
    mapped = sum(bool(question["topics"]) for question in questions)
    both_books = sum(len(topic["references"]) >= 2 for topic in topics)
    print(
        f"Valid: {len(books)} books, {len(topics)} topics "
        f"({both_books} with both-book references), {len(questions)} questions "
        f"({mapped} currently mapped)."
    )


if __name__ == "__main__":
    main()

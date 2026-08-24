"""Validate the generated offline Mini Program payload and project shell."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "miniprogram"
QUESTIONS = PROGRAM / "data" / "questions"


def read_js_data(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    prefix = "module.exports = "
    assert text.startswith(prefix) and text.endswith(";"), f"invalid data module: {path.name}"
    return json.loads(text[len(prefix):-1])


def main():
    modules = sorted(QUESTIONS.glob("20*.js"))
    assert len(modules) == 17, f"expected 17 year modules, got {len(modules)}"
    questions = [question for module in modules for question in read_js_data(module)]
    assert len(questions) == 675, f"expected 675 questions, got {len(questions)}"
    assert len({question["id"] for question in questions}) == 675, "question IDs must be unique"
    assert {question["year"] for question in questions} == set(range(2010, 2027))
    assert (PROGRAM / "app.json").exists()
    assert (PROGRAM / "pages" / "index" / "index.wxml").exists()
    index_js = (PROGRAM / "pages" / "index" / "index.js").read_text(encoding="utf-8")
    assert "termMatches" in index_js and "loadAllQuestions" in index_js
    config = json.loads((PROGRAM / "project.config.json").read_text(encoding="utf-8"))
    assert config["miniprogramRoot"] == "./"
    print(f"Valid Mini Program: {len(questions)} questions, {len(modules)} year modules")


if __name__ == "__main__":
    main()

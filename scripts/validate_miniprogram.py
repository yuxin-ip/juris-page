"""Validate the generated offline Mini Program payload and project shell."""

from __future__ import annotations

import json
from collections import Counter
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
    assert len(questions) == 1355, f"expected 1355 questions, got {len(questions)}"
    assert len({question["id"] for question in questions}) == 1355, "question IDs must be unique"
    assert {question["year"] for question in questions} == set(range(2010, 2027))
    assert Counter(question["subject"] for question in questions) == {"刑法": 675, "民法": 680}
    assert (PROGRAM / "app.json").exists()
    assert (PROGRAM / "pages" / "index" / "index.wxml").exists()
    index_js = (PROGRAM / "pages" / "index" / "index.js").read_text(encoding="utf-8")
    assert "termMatches" in index_js and "loadAllQuestions" in index_js
    assert "onCategoryChange" in index_js and "onTopicChange" in index_js
    assert "onSubjectChange" in index_js
    assert "showEndHint" in index_js and "hasMore" in index_js
    topic_filters = read_js_data(PROGRAM / "data" / "topic-filters.js")["groups"]
    assert Counter(item["subject"] for item in topic_filters) == {"刑法": 8, "民法": 7}
    appearing_topics = {topic["label"] for question in questions for topic in question["topics"]}
    assert all(set(item["topics"]) <= appearing_topics for item in topic_filters)
    wxml = (PROGRAM / "pages" / "index" / "index.wxml").read_text(encoding="utf-8")
    wxss = (PROGRAM / "pages" / "index" / "index.wxss").read_text(encoding="utf-8")
    card = (PROGRAM / "components" / "question-card" / "question-card.wxml").read_text(encoding="utf-8")
    assert "科目 · 刑法 / 民法" in wxml
    assert ".offense-selects{display:grid;grid-template-columns:1fr;" in wxss
    assert "{{question.track}} · {{question.subject}} · 第" in card
    config = json.loads((PROGRAM / "project.config.json").read_text(encoding="utf-8"))
    assert config["miniprogramRoot"] == "./"
    print(f"Valid Mini Program: {len(questions)} questions, {len(modules)} year modules")


if __name__ == "__main__":
    main()

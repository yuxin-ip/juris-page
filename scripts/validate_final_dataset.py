"""Validate the generated criminal- and civil-law static-site dataset."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
payload = json.loads((ROOT / "data" / "site_dataset.json").read_text(encoding="utf-8"))
rows = payload["questions"]
topic_filters = json.loads((ROOT / "data" / "topic_filters.json").read_text(encoding="utf-8"))
offense_filters = json.loads((ROOT / "data" / "offense_filters.json").read_text(encoding="utf-8"))

assert len(rows) == 1355, f"expected 1355 questions, got {len(rows)}"
assert len({row["id"] for row in rows}) == 1355, "question IDs must be unique"
assert Counter(row["track"] for row in rows) == {"法学": 505, "非法学": 850}
assert Counter(row["subject"] for row in rows) == {"刑法": 675, "民法": 680}
assert {row["year"] for row in rows} == set(range(2010, 2027))
assert all(
    any(row["year"] == year and row["track"] == track and row["subject"] == subject for row in rows)
    for year in (2025, 2026) for track in ("法学", "非法学") for subject in ("刑法", "民法")
)

for row in rows:
    assert row["type"] in {"single", "multiple"}
    assert row["track"] in {"法学", "非法学"}
    assert row["subject"] in {"刑法", "民法"}
    assert 2010 <= row["year"] <= 2026
    assert 1 <= row["number"] <= 55
    assert row["topics"]
    assert len(row["topics"]) <= 8
    for topic in row["topics"]:
        assert topic["label"] not in {"刑法", "意杀人罪", "博罪"}
        if row["subject"] == "民法":
            assert topic["kind"] == "numbered_knowledge"
            assert topic.get("code") and topic.get("part")
            assert topic["references"].get("beisong") and topic["references"].get("jingjiang")
        for ref in topic["references"].values():
            assert ref["status"] in {"candidate", "verified", "needs_review"}
            for start, end in ref["pages"]:
                assert 1 <= start <= end <= 600

html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
root_html = (ROOT / "index.html").read_text(encoding="utf-8")
assert "法硕刑民法真题" in html
assert "2010—2026" in html and "法学 + 非法学" in html
assert '<select id="track" aria-label="考生类别"><option value="">全部</option>' in html
assert '<select id="type" aria-label="题型"><option value="">全部</option>' in html
assert '<select id="subject" aria-label="科目">' in html
assert 'id="topicCategory" aria-label="知识门类"' in html
assert 'id="topic" aria-label="具体知识点"' in html
assert "科目、考点或罪名" in html
assert 'placeholder="搜索年份、题号、科目、考点或罪名"' in html
assert 'id="pageState"' not in html
assert "function termMatches" in html
assert 'id="resetFilters"' in html
assert "当前已启用筛选条件，搜索结果可能减少。" in html
assert "南京理工大学知识产权学院 郑宇昕" in html
assert 'id="hot"' not in html
assert 'id="endHint"' in html
assert "没有更多内容了，已显示全部" in html
assert 'class="summary"' not in html
assert "const DATA=" in html and "const TOPIC_FILTERS=" in html
assert root_html == html, "root GitHub Pages entry must match web/index.html"

expected_categories = [
    "危害国家安全罪", "危害公共安全罪", "破坏社会主义市场经济秩序罪",
    "侵犯公民人身权利、民主权利罪", "侵犯财产罪", "妨害社会管理秩序罪",
    "贪污贿赂罪", "渎职罪",
]
assert [item["label"] for item in offense_filters] == expected_categories
assert Counter(item["subject"] for item in topic_filters) == {"刑法": 8, "民法": 7}
appearing_topics = {topic["label"] for row in rows for topic in row["topics"]}
for category in topic_filters:
    assert category["subject"] in {"刑法", "民法"}
    assert category["topics"]
    assert set(category["topics"]) <= appearing_topics

print(
    f"Valid: {len(rows)} questions; subjects={dict(Counter(row['subject'] for row in rows))}; "
    f"tracks={dict(Counter(row['track'] for row in rows))}"
)

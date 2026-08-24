"""Validate the generated dual-track static-site dataset."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
payload = json.loads((ROOT / "data" / "site_dataset.json").read_text(encoding="utf-8"))
rows = payload["questions"]

assert len(rows) == 675, f"expected 675 questions, got {len(rows)}"
assert len({row["id"] for row in rows}) == 675, "question IDs must be unique"
assert Counter(row["track"] for row in rows) == {"法学": 250, "非法学": 425}
assert {row["year"] for row in rows} == set(range(2010, 2027))
assert any(row["year"] == 2025 and row["track"] == "法学" for row in rows)
assert any(row["year"] == 2025 and row["track"] == "非法学" for row in rows)
assert any(row["year"] == 2026 and row["track"] == "法学" for row in rows)
assert any(row["year"] == 2026 and row["track"] == "非法学" for row in rows)
assert sum(bool(row["topics"]) for row in rows) >= 674

for row in rows:
    assert row["type"] in {"single", "multiple"}
    assert row["track"] in {"法学", "非法学"}
    assert 2010 <= row["year"] <= 2026
    assert 1 <= row["number"] <= 45
    assert len(row["topics"]) <= 8
    for topic in row["topics"]:
        assert topic["label"] not in {"刑法", "意杀人罪", "博罪"}
        for ref in topic["references"].values():
            assert ref["status"] in {"candidate", "verified", "needs_review"}
            for start, end in ref["pages"]:
                assert 1 <= start <= end <= 600

html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
root_html = (ROOT / "index.html").read_text(encoding="utf-8")
assert "法学 + 非法学" in html
assert "2025、2026 两年均已收录" in html
assert '<select id="track" aria-label="考生类别"><option value="">全部</option>' in html
assert '<select id="type" aria-label="题型"><option value="">全部</option>' in html
assert "类别 · 法学 / 非法学" in html
assert "题型 · 单选 / 多选" in html
assert "搜索方法：" in html
assert "可单独输入年份、题号、考点或罪名" in html
assert "空格分隔组合筛选" in html
assert 'placeholder="搜索年份、题号、考点或罪名"' in html
assert 'id="pageState"' not in html
assert "function termMatches" in html
assert "x.track===term" in html
assert 'id="resetFilters"' in html
assert "当前已启用筛选条件，搜索结果可能减少。" in html
assert "南京理工大学知识产权学院 郑宇昕" in html
assert 'class="summary"' not in html
assert "const DATA=" in html
assert root_html == html, "root GitHub Pages entry must match web/index.html"

print(f"Valid: {len(rows)} questions; track counts={dict(Counter(row['track'] for row in rows))}")

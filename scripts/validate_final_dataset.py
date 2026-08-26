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

assert len(rows) == 1360, f"expected 1360 questions, got {len(rows)}"
assert len({row["id"] for row in rows}) == 1360, "question IDs must be unique"
assert Counter(row["track"] for row in rows) == {"法学": 510, "非法学": 850}
assert Counter(row["subject"] for row in rows) == {"刑法": 680, "民法": 680}
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
assert 'class="subject-switch" aria-label="科目筛选"' in html
assert 'data-subject="刑法"' in html and 'data-subject="民法"' in html
assert 'data-subject=""' not in html
assert '<select id="subject"' not in html
assert 'id="topicCategory"' in html
assert 'id="topic"' in html
assert "setAttribute('aria-label',categoryLabel)" in html
assert "setAttribute('aria-label',topicLabel)" in html
assert 'id="topicFilterGroup" hidden' in html and 'id="topicFilterTitle"' in html
assert "subjects:[]" in html and "state.subjects.length===1" in html
assert "state.subjects=[]" in html
assert "subjectPanel').classList.toggle('active',Boolean(singleSubject()))" in html
assert "['刑法分则罪名','犯罪类型','具体罪名']" in html
assert "['民法编号知识点','民法典全部七编','具体知识点']" in html
assert "民法部分" not in html
for book in ("第一编·总则", "第二编·物权", "第三编·合同", "第四编·人格权", "第五编·婚姻家庭", "第六编·继承", "第七编·侵权责任"):
    assert book in html
assert "民法典外·知识产权" in html
assert "知识门类" not in html
assert "科目、考点或罪名" in html
assert 'placeholder="搜索年份、题号、科目、考点或罪名"' in html
assert 'id="pageState"' not in html
assert "function termMatches" in html
assert 'id="resetFilters"' in html
assert "当前已启用筛选条件，搜索结果可能减少。" in html
assert 'class="sticky-filters"' in html
assert ".controls{position:static" in html
assert "function scrollToResults" in html and "resetRender(true)" in html
assert "问题反馈：微信 zlszyxdwx" in html
assert "南京理工大学知识产权学院 郑宇昕" in html
assert 'id="hot"' not in html
assert 'id="endHint"' in html
assert "没有更多内容了，已显示全部" in html
assert 'class="summary"' not in html
assert "const DATA=" in html and "const TOPIC_FILTERS=" in html
assert root_html == html, "root GitHub Pages entry must match web/index.html"

missing_2010 = [f"2010-法学-刑法-{number:02d}" for number in range(11, 16)]
by_id = {row["id"]: row for row in rows}
assert all(question_id in by_id for question_id in missing_2010)
assert all(by_id[question_id]["type"] == "multiple" for question_id in missing_2010)
assert all(
    topic["references"].get("beisong") and topic["references"].get("jingjiang")
    for question_id in missing_2010 for topic in by_id[question_id]["topics"]
)

expected_categories = [
    "危害国家安全罪", "危害公共安全罪", "破坏社会主义市场经济秩序罪",
    "侵犯公民人身权利、民主权利罪", "侵犯财产罪", "妨害社会管理秩序罪",
    "贪污贿赂罪", "渎职罪",
]
assert [item["label"] for item in offense_filters] == expected_categories
assert Counter(item["subject"] for item in topic_filters) == {"刑法": 8, "民法": 8}
appearing_topics = {topic["label"] for row in rows for topic in row["topics"]}
for category in topic_filters:
    assert category["subject"] in {"刑法", "民法"}
    assert category["topics"]
    assert set(category["topics"]) <= appearing_topics

print(
    f"Valid: {len(rows)} questions; subjects={dict(Counter(row['subject'] for row in rows))}; "
    f"tracks={dict(Counter(row['track'] for row in rows))}"
)

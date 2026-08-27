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
    assert len(questions) == 1360, f"expected 1360 questions, got {len(questions)}"
    assert len({question["id"] for question in questions}) == 1360, "question IDs must be unique"
    assert {question["year"] for question in questions} == set(range(2010, 2027))
    assert Counter(question["subject"] for question in questions) == {"刑法": 680, "民法": 680}
    assert (PROGRAM / "app.json").exists()
    assert (PROGRAM / "pages" / "index" / "index.wxml").exists()
    index_js = (PROGRAM / "pages" / "index" / "index.js").read_text(encoding="utf-8")
    assert "termMatches" in index_js and "loadAllQuestions" in index_js
    assert "onCategoryChange" in index_js and "onTopicChange" in index_js
    assert "onSubjectTap" in index_js and "onSubjectChange" not in index_js
    assert "scrollToResults" in index_js and "onPageScroll" in index_js and "onBackToFilters" in index_js
    assert "onShareAppMessage" in index_js and "onShareTimeline" in index_js
    assert "showEndHint" in index_js and "hasMore" in index_js
    topic_filters = read_js_data(PROGRAM / "data" / "topic-filters.js")["groups"]
    assert Counter(item["subject"] for item in topic_filters) == {"刑法": 8, "民法": 8}
    appearing_topics = {topic["label"] for question in questions for topic in question["topics"]}
    assert all(set(item["topics"]) <= appearing_topics for item in topic_filters)
    wxml = (PROGRAM / "pages" / "index" / "index.wxml").read_text(encoding="utf-8")
    wxss = (PROGRAM / "pages" / "index" / "index.wxss").read_text(encoding="utf-8")
    card = (PROGRAM / "components" / "question-card" / "question-card.wxml").read_text(encoding="utf-8")
    assert 'class="subject-switch"' in wxml and 'bindtap="onSubjectTap"' in wxml
    assert "subjectOptions: ['刑法', '民法']" in index_js
    assert "subjectOptions: ['全部', '刑法', '民法']" not in index_js
    assert "subjectSelected: [false, false]" in index_js
    assert "subjectIndex:" not in index_js and "subjectIndex" not in wxml
    assert 'wx:if="{{showCriminalFilters || showCivilFilters}}"' in wxml
    assert '<view class="sticky-filters">' in wxml
    assert "subjectPanelActive" in wxml and "subjectPanelActive" in index_js
    assert 'id="resultStart"' in wxml and "showBackToFilters" in wxml
    assert "showCriminalFilters" in wxml and "showCivilFilters" in wxml and "showBothTopicFilters" in wxml
    assert "criminalCategoryIndex" in index_js and "criminalTopicIndex" in index_js
    assert "civilCategoryIndex" in index_js and "civilTopicIndex" in index_js
    assert "categoryCaption" not in wxml and "categoryCaption" not in index_js
    assert "topicCaption" not in wxml and "topicCaption" not in index_js
    assert "'犯罪类型'" in index_js and "'具体罪名'" in index_js
    assert "'民法典全部七编'" in index_js and "'具体知识点'" in index_js
    assert "'民法部分'" not in index_js
    assert "知识门类" not in index_js and "全部门类" not in index_js
    assert ".offense-selects{display:grid;grid-template-columns:1fr;" in wxss
    assert ".topic-filter-groups-single{grid-template-columns:minmax(0,1fr);" in wxss
    assert ".topic-filter-groups-dual{grid-template-columns:repeat(2,minmax(0,1fr));" in wxss
    assert ".filters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));" in wxss
    assert ".topic-filter-groups-single{grid-template-columns:minmax(0,1fr);width:calc(33.333%" in wxss
    assert ".topic-filter-groups-dual{grid-template-columns:repeat(2,minmax(0,1fr));width:100%}" in wxss
    assert ".offense-select-long text:last-child" in wxss and ".offense-select-xlong text:last-child" in wxss
    assert ".subject-switch{display:flex;" in wxss
    assert ".subject-button{flex:1 1 0;width:0;min-width:0;" in wxss
    assert ".subject-panel" in wxss and "overflow:hidden" in wxss
    assert ".subject-panel-active{border-color:#bfd3fb;background:#eef4ff}" in wxss
    app_wxss = (PROGRAM / "app.wxss").read_text(encoding="utf-8")
    assert ".sticky-filters{position:sticky;" in app_wxss
    assert ".back-to-filters{display:flex;" in app_wxss and "border-radius:50%" in app_wxss
    assert "width:88rpx!important" in app_wxss and "height:88rpx!important" in app_wxss
    assert "返回" in wxml and "顶部" in wxml and "筛选 ↑" not in wxml
    assert "query.select('.sticky-filters').boundingClientRect()" in index_js
    assert "result[1].top + result[2].scrollTop - stickyHeight - 12" in index_js
    about = (PROGRAM / "pages" / "about" / "about.wxml").read_text(encoding="utf-8")
    assert "微信：zlszyxdwx" in about
    about_js = (PROGRAM / "pages" / "about" / "about.js").read_text(encoding="utf-8")
    assert "onShareAppMessage" in about_js and "onShareTimeline" in about_js
    assert "{{question.track}} · {{question.subject}} · 第" in card
    config = json.loads((PROGRAM / "project.config.json").read_text(encoding="utf-8"))
    assert config["miniprogramRoot"] == "./"
    print(f"Valid Mini Program: {len(questions)} questions, {len(modules)} year modules")


if __name__ == "__main__":
    main()

"""Generate a reviewable question-to-numbered-topic link table.

This is an offline curation helper, not part of the website runtime.  It combines
exact terminology matching with a Chinese sentence-embedding fallback, then
applies the manually audited exceptions from ``build_civil_dataset``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_civil_dataset import QUESTION_OVERRIDES, norm, topic_score  # noqa: E402


def code_number(topic: dict) -> tuple[int, int]:
    return tuple(map(int, topic["code"].split("-")))


def semantic_scope(text: str, topics: list[dict]) -> list[int]:
    """Restrict semantic ranking to the legal field named in the source."""
    value = norm(text)
    rules = [
        (("著作权", "作品", "邻接权", "署名权", "发表权"), 4, (3, 14)),
        (("专利", "发明", "实用新型", "外观设计"), 4, (4, 21)),
        (("商标", "驰名商标"), 4, (5, 27)),
        (("商业秘密", "不正当竞争"), 4, (6, 8)),
        (("抵押",), 3, (69, 85)),
        (("质押", "质权", "出质"), 3, (69, 91)),
        (("留置",), 3, (69, 98)),
        (("善意取得", "无权处分"), 3, (28, 30)),
        (("占有",), 3, (99, 102)),
        (("不动产登记", "预告登记", "异议登记"), 3, (10, 17)),
        (("共有", "共有人"), 3, (42, 47)),
        (("居住权",), 3, (53, 68)),
        (("相邻", "采光", "通风", "烟道"), 3, (34, 41)),
        (("收养",), 6, (31, 41)),
        (("继承", "遗产", "遗嘱", "遗赠"), 6, (42, 73)),
        (("离婚", "夫妻", "婚姻"), 6, (5, 30)),
        (("亲属", "亲等", "血亲"), 6, (1, 4)),
        (("肖像",), 2, (7, 32)),
        (("姓名",), 2, (5, 26)),
        (("名誉", "荣誉"), 2, (8, 33)),
        (("隐私", "个人信息"), 2, (22, 38)),
        (("产品责任", "产品缺陷"), 7, (34, 37)),
        (("饲养动物", "烈性犬", "动物致人"), 7, (46, 47)),
        (("机动车交通事故", "好意同乘", "搭载同事"), 7, (38, 38)),
        (("医疗", "医务人员"), 7, (39, 42)),
        (("网络服务提供者", "通知规则"), 7, (29, 30)),
        (("诉讼时效",), 1, (132, 144)),
        (("代理", "被代理人"), 1, (123, 131)),
        (("意思表示", "沉默"), 1, (95, 98)),
        (("监护", "被监护人"), 1, (54, 63)),
        (("民事行为能力", "限制民事行为能力", "完全民事行为能力"), 1, (51, 53)),
        (("合伙企业", "合伙人"), 1, (85, 90)),
        (("要约", "承诺"), 5, (12, 18)),
        (("格式条款",), 5, (23, 25)),
        (("保证人", "保证责任", "保证期间"), 5, (47, 52)),
        (("违约", "履行利益", "赔偿损失"), 5, (79, 93)),
        (("定金",), 5, (53, 56)),
        (("提存",), 5, (74, 78)),
        (("租赁", "承租人", "出租人"), 5, (101, 116)),
        (("买卖", "出卖人", "买受人"), 5, (98, 110)),
        (("赠与",), 5, (95, 112)),
        (("运输", "承运人", "托运人"), 5, (137, 143)),
        (("无因管理", "管理他人事务"), 5, (160, 163)),
        (("不当得利",), 5, (164, 167)),
    ]
    for keywords, part, number_range in rules:
        if any(norm(keyword) in value for keyword in keywords):
            indexes = [
                index for index, topic in enumerate(topics)
                if code_number(topic)[0] == part and number_range[0] <= code_number(topic)[1] <= number_range[1]
            ]
            if indexes:
                return indexes
    # Broad field fallback prevents a contract explanation from drifting into
    # an unrelated property or tort heading.
    broad = [
        (("著作", "专利", "商标", "知识产权"), "知识产权"),
        (("物权", "所有权", "抵押", "质权", "留置", "占有", "不动产"), "物权"),
        (("合同", "债权", "债务", "履行", "违约", "清偿"), "合同"),
        (("婚姻", "夫妻", "离婚", "收养", "继承", "遗产"), "婚姻家庭与继承"),
        (("侵权", "损害", "赔偿"), "侵权责任"),
        (("人格权", "肖像", "隐私", "名誉", "个人信息"), "人格权"),
    ]
    for keywords, part in broad:
        if any(norm(keyword) in value for keyword in keywords):
            return [index for index, topic in enumerate(topics) if topic["part"] == part]
    return list(range(len(topics)))


def question_text(question: dict) -> str:
    analysis = question.get("source_analysis_text", "") or ""
    stem = question.get("source_question_text", "") or ""
    # The opening part of an explanation normally names the applicable rule;
    # later paragraphs often discuss distractors and reduce semantic precision.
    return (analysis[:900] + " " + stem[:700]).strip()


def keyword_links(text: str) -> list[str] | None:
    """High-precision legal terminology rules audited against the source set."""
    value = norm(text)
    rules = [
        (("孳息", "孽息", "擎息"), ["1-28"]),
        (("意定监护",), ["1-59"]),
        (("监护职责", "被监护人利益"), ["1-60"]),
        (("被代理人死亡",), ["1-131"]),
        (("限制民事行为能力",), ["1-52", "1-115"]),
        (("遗失物", "拾得"), ["3-26"]),
        (("善意取得",), ["3-28", "3-30"]),
        (("指示交付", "简易交付", "占有改定"), ["3-16"]),
        (("非基于民事法律行为", "合法建造", "因继承取得物权"), ["3-17"]),
        (("业主共同决定", "业主大会"), ["3-41"]),
        (("同一动产上", "优先顺位"), ["3-98"]),
        (("职务作品",), ["4-10"]),
        (("委托创作", "受委托创作"), ["4-9"]),
        (("著作权的合理使用", "合理使用著作权", "著作权的法定许可"), ["4-13"]),
        (("邻接权",), ["4-13"]),
        (("署名权", "发表权", "修改权", "保护作品完整权"), ["4-12"]),
        (("侵犯著作权", "著作权侵权"), ["4-14"]),
        (("悬赏",), ["5-7"]),
        (("合同成立",), ["5-21"]),
        (("履行地点不明确", "合同漏洞", "价格条款约定不明确"), ["5-29"]),
        (("预期违约",), ["5-81"]),
        (("债务转移", "免责债务承担"), ["5-64", "5-65"]),
        (("连带债务",), ["5-33", "5-34"]),
        (("保证期间",), ["5-50"]),
        (("情势变更",), ["5-36"]),
        (("承运人", "托运人"), ["5-139"]),
        (("提存",), ["5-74", "5-76"]),
        (("违约金",), ["5-90"]),
        (("违约损失赔偿", "可得利益"), ["5-91"]),
        (("间接代理", "受托人以自己的名义与第三人"), ["5-153"]),
        (("收养人应当", "收养人的条件"), ["6-35"]),
        (("解除收养",), ["6-39", "6-41"]),
        (("探望权",), ["6-25"]),
        (("亲等", "旁系血亲的计算"), ["6-4"]),
        (("遗产分配", "可以适当分给", "多分遗产", "少分遗产"), ["6-55"]),
        (("遗产管理人",), ["6-65"]),
        (("精神损害赔偿",), ["7-20"]),
        (("共同侵权",), ["7-14"]),
        (("无意思联络",), ["7-17"]),
        (("网络服务提供者",), ["7-29", "7-30"]),
        (("建筑物", "倒塌"), ["7-51"]),
        (("饲养的动物", "烈性犬"), ["7-46", "7-47"]),
        (("产品存在缺陷",), ["7-35", "7-37"]),
    ]
    for keywords, codes in rules:
        if any(norm(keyword) in value for keyword in keywords):
            return codes
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument("--questions", type=Path, default=Path(".work/questions/civil.json"))
    parser.add_argument("--topics", type=Path, default=Path(".work/topics/civil-numbered-headings.json"))
    parser.add_argument("--output", type=Path, default=Path("data/civil_question_topics.json"))
    args = parser.parse_args()

    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    topics = json.loads(args.topics.read_text(encoding="utf-8"))
    model = SentenceTransformer(args.model)
    topic_vectors = model.encode(
        [f"{topic['part']}：{topic['label']}" for topic in topics],
        normalize_embeddings=True, batch_size=64, show_progress_bar=False,
    )
    texts = [question_text(question) for question in questions]
    question_vectors = model.encode(
        texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False,
    )

    result = {}
    review = []
    for index, question in enumerate(questions):
        if question["id"] in QUESTION_OVERRIDES:
            codes = QUESTION_OVERRIDES[question["id"]]
            method = "manual"
            confidence = 1.0
        else:
            keyword_codes = keyword_links(texts[index])
            if keyword_codes:
                result[question["id"]] = {"topics": keyword_codes, "method": "keyword-audit", "confidence": 0.98}
                continue
            normalized = norm(texts[index])
            exact = [(topic_score(topic, normalized), topic) for topic in topics]
            exact = [(score, topic) for score, topic in exact if score]
            exact.sort(key=lambda item: -item[0])
            if exact:
                best = exact[0][0]
                codes = [topic["code"] for score, topic in exact if score >= best - 30][:4]
                method = "terminology"
                confidence = min(0.99, best / 220)
            else:
                scores = question_vectors[index] @ topic_vectors.T
                scope = semantic_scope(texts[index], topics)
                top = sorted(scope, key=lambda item: -scores[item])[:5]
                codes = [topics[int(top[0])]["code"]]
                method = "semantic"
                confidence = float(scores[int(top[0])])
                review.append({
                    "id": question["id"], "confidence": round(confidence, 4),
                    "selected": codes,
                    "suggestions": [
                        {"code": topics[int(item)]["code"], "label": topics[int(item)]["label"],
                         "score": round(float(scores[int(item)]), 4)} for item in top
                    ],
                    "source_excerpt": texts[index][:350],
                })
        result[question["id"]] = {"topics": codes, "method": method, "confidence": round(confidence, 4)}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    review_path = Path(".work/civil/semantic_review.json")
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(result)} links; semantic review records={len(review)}")


if __name__ == "__main__":
    main()

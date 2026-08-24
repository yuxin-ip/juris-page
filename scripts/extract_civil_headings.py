"""Extract the numbered knowledge-point headings from 民法《背诵一本通》 OCR.

Only lines carrying an explicit ``编号-序号`` marker are eligible. This is the
scope rule for the public civil-law index: ordinary body subheadings are never
promoted to topics.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PARTS = {
    1: "民法总则",
    2: "人格权",
    3: "物权",
    4: "知识产权",
    5: "合同",
    6: "婚姻家庭与继承",
    7: "侵权责任",
}
HEADING = re.compile(r"^(?P<part>[1-7])\s*[-—－]\s*(?P<number>\d{1,3})\s*[.．、]?\s*(?P<label>.*)$")
OCR_REPLACEMENTS = {
    "其体": "具体", "具休": "具体", "客休": "客体", "夫要": "夫妻",
    "道产": "遗产", "遭产": "遗产", "遗瞩": "遗嘱", "永包": "承包",
    "非奠型": "非典型", "抗辨权": "抗辩权", "抵钾权": "抵押权",
    "著作财产权": "著作财产权", "动广": "动产", "不助产": "不动产",
}
MANUAL_HEADINGS = {
    "3-11": ("物权", "不动产登记簿与不动产权属证书的区别", 91),
    "3-17": ("物权", "非基于民事法律行为的物权变动", 93),
    "3-18": ("物权", "物权的保护方式", 93),
    "3-23": ("物权", "不动产所有权和动产所有权的区别", 95),
    "3-36": ("物权", "建筑物区分所有权的特征", 99),
    "3-55": ("物权", "地役权和相邻关系的区别", 107),
    "3-78": ("物权", "担保物权的消灭事由", 115),
    "3-85": ("物权", "抵押权的实现条件和方法", 117),
    "3-92": ("物权", "留置权的成立要件", 119),
    "3-98": ("物权", "同一动产上不同担保物权的优先顺位", 121),
    "4-4": ("知识产权", "专利权的含义和特征", 127),
    "4-14": ("知识产权", "侵犯著作人身权、著作财产权的具体情形", 131),
    "4-18": ("知识产权", "专利权人取得专利权的方式", 133),
    "5-38": ("合同", "同时履行抗辩权的构成要件", 150),
    "6-12": ("婚姻家庭与继承", "夫妻财产关系的内容", 198),
    "6-69": ("婚姻家庭与继承", "遗赠扶养协议解除的法律后果", 214),
}
LABEL_CORRECTIONS = {
    "1-26": "民事法律关系客体的具体类型",
    "1-28": "孳息的类型及归属",
    "1-60": "监护人的职责",
    "2-22": "隐私权的内容",
    "2-21": "荣誉权的内容",
    "2-36": "处理个人信息的免责情形",
    "3-26": "拾得遗失物的法律规范",
    "3-30": "善意取得的法律后果",
    "5-31": "选择之债的履行（简述选择之债中选择权人的确定）",
    "5-65": "免责债务承担的效力",
    "6-73": "继承人对遗产债务的清偿顺位",
}


def clean_label(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[0-9]+[.．、]\s*", "", value)
    value = re.sub(r"^[简筒首]述\s*", "", value)
    value = re.sub(r"[①②③④⑤⑥⑦⑧⑨⑩]+$", "", value)
    value = re.sub(r"[（(]\s*20\d{2}.*?[）)]\s*$", "", value)
    value = value.strip(" ：:，,。.;；")
    for bad, good in OCR_REPLACEMENTS.items():
        value = value.replace(bad, good)
    return value


def load_records(paths: list[Path]) -> list[dict]:
    by_page: dict[int, dict] = {}
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                record = json.loads(raw)
                by_page[record["pdf_page"]] = record
    return [by_page[page] for page in sorted(by_page)]


def extract(records: list[dict], printed_offset: int) -> list[dict]:
    found: dict[str, dict] = {}
    for record in records:
        texts = [line["text"].strip() for line in record.get("lines", [])]
        for index, text in enumerate(texts):
            match = HEADING.match(text)
            if not match:
                continue
            if int(match.group("number")) < 1:
                continue
            code = f"{int(match.group('part'))}-{int(match.group('number'))}"
            label = clean_label(match.group("label"))
            if not label and index + 1 < len(texts):
                label = clean_label(texts[index + 1])
            if len(label) < 2:
                continue
            item = {
                "code": code,
                "part": PARTS[int(match.group("part"))],
                "label": label,
                "beisong_printed_page": record["pdf_page"] - printed_offset,
                "beisong_pdf_page": record["pdf_page"],
            }
            previous = found.get(code)
            if previous is None or len(item["label"]) > len(previous["label"]):
                found[code] = item
    for code, (part, label, pdf_page) in MANUAL_HEADINGS.items():
        found[code] = {
            "code": code,
            "part": part,
            "label": label,
            "beisong_printed_page": pdf_page - printed_offset,
            "beisong_pdf_page": pdf_page,
        }
    for code, label in LABEL_CORRECTIONS.items():
        if code in found:
            found[code]["label"] = label
    return sorted(found.values(), key=lambda item: tuple(map(int, item["code"].split("-"))))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ocr", nargs="+", type=Path)
    parser.add_argument("--printed-offset", type=int, default=12)
    parser.add_argument("--output", type=Path, default=Path(".work/topics/civil-numbered-headings.json"))
    args = parser.parse_args()
    headings = extract(load_records(args.ocr), args.printed_offset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(headings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(headings)} numbered civil-law headings")
    for part_number, part_label in PARTS.items():
        numbers = [int(item["code"].split("-")[1]) for item in headings if item["part"] == part_label]
        missing = sorted(set(range(1, max(numbers, default=0) + 1)) - set(numbers))
        print(part_label, f"count={len(numbers)} max={max(numbers, default=0)} missing={missing}")


if __name__ == "__main__":
    main()

"""Extract candidate offense/topic headings from textbook OCR output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


CHINESE_NUMBER = "一二三四五六七八九十百〇零两"
HEADING_PATTERNS = [
    re.compile(rf"^第[{CHINESE_NUMBER}]+讲\s*(.+?罪)$"),
    re.compile(rf"^[（(]?[{CHINESE_NUMBER}]+[）)]?[、.]\s*(.+?罪)(?:[（(].*)?$"),
    # 背诵一本通不是按“第X讲”编排，而是“二十七、简述……罪的概念和
    # 构成特征”。只取罪名本身，避免把正文带进公开数据。
    re.compile(
        rf"^[{CHINESE_NUMBER}0-9]+[、.]\s*[简筒首]述\s*(.+?罪)(?:的概念|的构成|的特征|$)"
    ),
]

OCR_CORRECTIONS = {
    "端动分裂国家罪": "煽动分裂国家罪",
    "非法转让、侧卖土地使用权罪": "非法转让、倒卖土地使用权罪",
    "强制梁爽、悔辱罪": "强制猥亵、侮辱罪",
    "猥衰儿童罪": "猥亵儿童罪",
    "还告陷害罪": "诬告陷害罪",
    "虚待罪": "虐待罪",
    "悔辱罪": "侮辱罪",
    "非谤罪": "诽谤罪",
    "聚众斗酸罪": "聚众斗殴罪",
    "寻鲜滋事罪": "寻衅滋事罪",
    "赔博罪": "赌博罪",
    "窝藏、包底罪": "窝藏、包庇罪",
    "饰、隐犯罪所得、犯罪所得收益罪": "掩饰、隐瞒犯罪所得、犯罪所得收益罪",
    "组织参与国（境）外赠博罪": "组织参与国（境）外赌博罪",
    "走私、卖、运输、制造毒品罪": "走私、贩卖、运输、制造毒品罪",
    "客留他人吸毒罪": "容留他人吸毒罪",
    "制作、复制、出版、贩卖、传播淫移物品牟利罪": "制作、复制、出版、贩卖、传播淫秽物品牟利罪",
    "传播淫移物品罪": "传播淫秽物品罪",
    "避用职权罪": "滥用职权罪",
    "徇私柱法罪": "徇私枉法罪",
    "执行判决、裁定监用职权罪": "执行判决、裁定滥用职权罪",
    "食品、药品监管读职罪": "食品、药品监管渎职罪",
    "伪造货市罪": "伪造货币罪",
    "顺覆国家政权罪": "颠覆国家政权罪",
    "间谋罪": "间谍罪",
    "破环交通工具罪": "破坏交通工具罪",
}


def extract(path: Path, offset: int) -> list[dict]:
    headings: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            record = json.loads(raw_line)
            for line in record["lines"]:
                text = line["text"].strip()
                label = None
                for pattern in HEADING_PATTERNS:
                    match = pattern.match(text)
                    if match:
                        label = match.group(1).strip()
                        break
                if not label:
                    continue
                label = re.sub(r"^[简筒首]述\s*", "", label)
                label = OCR_CORRECTIONS.get(label, label)
                headings.append(
                    {
                        "label": label,
                        "printed_page": record["pdf_page"] - offset,
                        "pdf_page": record["pdf_page"],
                        "ocr_text": text,
                        "ocr_score": line["score"],
                    }
                )
    headings.sort(key=lambda item: (item["pdf_page"], item["label"]))
    return headings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ocr", type=Path)
    parser.add_argument("--offset", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    headings = extract(args.ocr, args.offset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(headings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Extracted {len(headings)} candidate headings to {args.output}")


if __name__ == "__main__":
    main()

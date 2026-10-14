"""把 D:\\项目2\\1\\cleaned\\ 的清洗文本导入 knowledge_base 分类目录并重建索引。

分类映射：
  适航指令 -> airworthiness_directives
  标准文件 + 其他 -> ccar_regulations
  C919 -> c919_manual
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(RAG_DIR.parent))

from rag.build_index import build_index  # noqa: E402

CLEANED_DIR = Path(r"D:\项目2\1\cleaned")
KNOWLEDGE_BASE = RAG_DIR / "knowledge_base"

CATEGORY_MAP = {
    "适航指令": "airworthiness_directives",
    "标准文件": "ccar_regulations",
    "其他": "ccar_regulations",
    "C919": "c919_manual",
}

MANAGED_DIRS = {"airworthiness_directives", "ccar_regulations", "c919_manual"}

TITLE_MAP = {
    "P020151103350113879351": "CCAR-34 涡轮发动机飞机燃油排泄和排气排出物规定",
    "P020180226364226951610": "CCAR-36 航空器型号和适航合格审定噪声规定",
    "P020220531594845199114": "CCAR-23 正常类飞机适航规定",
    "P020251217349889468777": "CCAR-35 螺旋桨适航规定",
    "P020260109540248294318": "CCAR-27 正常类旋翼航空器适航规定",
    "P020260109540448543665": "CCAR-29 运输类旋翼航空器适航规定",
    "P020230105510893621941": "CCAR-395 民用航空器事件技术调查规定",
    "P020240222622564730405": "民用航空器事件技术调查手册",
    "c919acap_en": "C919 ACAP 技术出版物",
    "c919rsoi": "C919 RSOI 机坪勤务操作指南",
}

_ILLEGAL_FS = re.compile(r'[\\/:*?"<>|\s]+')


def _safe_name(name: str) -> str:
    cleaned = _ILLEGAL_FS.sub("", name)
    return cleaned or "unnamed"


def _join_page_lines(page_text: str) -> str:
    """把 PDF 提取的单页多行合并为连贯段落：中文直接相连，英文间补空格。"""
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    if not lines:
        return ""
    merged = lines[0]
    for line in lines[1:]:
        prev_ascii = merged[-1].isascii() and merged[-1].isalnum()
        next_ascii = line[0].isascii() and line[0].isalnum()
        merged = f"{merged} {line}" if prev_ascii and next_ascii else merged + line
    return merged


def parse_cleaned_text(text: str) -> tuple[dict, str]:
    """解析清洗文本：返回（结构化字段, 按空行分页的正文）。"""
    header, _, body = text.partition("=" * 60)
    fields: dict[str, str] = {}
    for line in header.splitlines():
        match = re.match(r"#\s+(编号|修正案号|标题|生效日期|颁发日期|联系人)\s*[:：]\s*(.+)", line.strip())
        if match:
            fields[match.group(1)] = match.group(2).strip()

    pages = []
    for page in re.split(r"^##\s+Page\s+\d+\s*$", body, flags=re.MULTILINE):
        merged = _join_page_lines(page)
        if merged:
            pages.append(merged)
    return fields, "\n\n".join(pages)


def build_document(stem: str, fields: dict, body: str, source_pdf: str) -> str:
    lines: list[str] = []
    if fields:
        title = fields.get("标题", stem)
        lines.append(f"# 适航指令 {fields.get('编号', stem)}：{title}")
        lines.append("")
        for key in ("编号", "修正案号", "标题", "生效日期", "颁发日期", "联系人"):
            if key in fields:
                lines.append(f"{key}：{fields[key]}")
        lines.append(f"来源：{source_pdf}")
    else:
        lines.append(f"# {TITLE_MAP.get(stem, stem)}")
        lines.append("")
        lines.append(f"来源：{source_pdf}")
    lines.append("")
    lines.append(body)
    return "\n".join(lines)


def target_filename(stem: str, fields: dict) -> str:
    if fields:
        number = fields.get("编号", stem)
        title = _safe_name(fields.get("标题", ""))
        return f"{number}_{title}.md" if title else f"{number}.md"
    return f"{_safe_name(TITLE_MAP.get(stem, stem))}.md"


def main() -> None:
    cleaned_index = json.loads((CLEANED_DIR / "index.json").read_text(encoding="utf-8"))

    for name in MANAGED_DIRS:
        target_dir = KNOWLEDGE_BASE / name
        if target_dir.exists():
            for stale in target_dir.glob("*.md"):
                stale.unlink()
        target_dir.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int] = {}
    skipped: list[str] = []
    for entry in cleaned_index:
        source = Path(entry["source_file"])
        stem = source.stem
        text_path = Path(entry["output_file"])
        text = text_path.read_text(encoding="utf-8")
        fields, body = parse_cleaned_text(text)
        if not body.strip():
            skipped.append(f"{stem}（正文为空，{source.name} 疑似扫描件）")
            continue

        category = CATEGORY_MAP[entry["category"]]
        filename = target_filename(stem, fields)
        document = build_document(stem, fields, body, source.name)
        (KNOWLEDGE_BASE / category / filename).write_text(document, encoding="utf-8")
        stats[category] = stats.get(category, 0) + 1

    for name, count in sorted(stats.items()):
        print(f"{name}: 导入 {count} 篇")
    for item in skipped:
        print(f"跳过: {item}")

    records = build_index()
    categories: dict[str, int] = {}
    for record in records:
        categories[record["category"]] = categories.get(record["category"], 0) + 1
    print(f"重建索引完成：{len(records)} 个知识片段")
    print(f"分类统计：{categories}")


if __name__ == "__main__":
    main()

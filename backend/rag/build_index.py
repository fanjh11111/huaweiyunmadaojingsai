"""将知识库文本切分为可审计的本地 JSON 索引。"""

from __future__ import annotations

import json
import os
import re
from hashlib import sha256
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE = Path(os.getenv("KNOWLEDGE_BASE_DIR", str(RAG_DIR / "knowledge_base")))
INDEX_PATH = RAG_DIR / "index.json"

_MAX_CHUNK_CHARS = 800
_MIN_CHUNK_CHARS = 50


def _split_text(text: str) -> list[str]:
    # 对带二级标题的知识文档，保持“一个主题小节 = 一个检索片段”。这能避免
    # 多个不相干的维修规则被拼进同一段，从而降低检索命中后误引用的风险。
    sections = [section.strip() for section in re.split(r"(?m)^##\s+", text) if section.strip()]
    if len(sections) > 1:
        heading_sections = sections[1:]
        chunks: list[str] = []
        for section in heading_sections:
            if len(section) <= _MAX_CHUNK_CHARS:
                if len(section) >= _MIN_CHUNK_CHARS:
                    chunks.append(section)
                continue
            chunks.extend(_split_text(section))
        return chunks

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        if len(para) > _MAX_CHUNK_CHARS:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            for i in range(0, len(para), _MAX_CHUNK_CHARS):
                chunk = para[i:i + _MAX_CHUNK_CHARS]
                if len(chunk) >= _MIN_CHUNK_CHARS:
                    chunks.append(chunk)
        elif len(buffer) + len(para) + 2 <= _MAX_CHUNK_CHARS:
            buffer = f"{buffer}\n\n{para}" if buffer else para
        else:
            if buffer:
                chunks.append(buffer)
            buffer = para
    if buffer:
        chunks.append(buffer)
    return chunks


def build_records() -> list[dict]:
    records: list[dict] = []
    files = sorted(
        set(KNOWLEDGE_BASE.rglob("*.md")) | set(KNOWLEDGE_BASE.rglob("*.txt"))
    )
    for path in files:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = _split_text(text)
        category = path.parent.name
        title = path.stem
        source = str(path).replace("\\", "/")
        for number, content in enumerate(chunks, start=1):
            records.append({
                "id": f"{title}-{number}",
                "title": title,
                "category": category,
                "source": source,
                "content": content,
                "content_hash": sha256(content.encode("utf-8")).hexdigest(),
            })
    return records


def build_index() -> list[dict]:
    records = build_records()
    INDEX_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return records


def get_knowledge_base_version(records: list[dict] | None = None) -> str:
    records = records or build_records()
    fingerprint = "\n".join(
        f"{record['id']}:{record.get('content_hash', '')}"
        for record in sorted(records, key=lambda item: item["id"])
    )
    return sha256(fingerprint.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    records = build_index()
    cats: dict[str, int] = {}
    for r in records:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print(f"indexed {len(records)} chunks from {len(set(r['title'] for r in records))} files -> {INDEX_PATH}")
    print(f"categories: {cats}")

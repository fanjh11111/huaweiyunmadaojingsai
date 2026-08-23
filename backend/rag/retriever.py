"""无外部服务依赖的本地关键词检索器，保留来源便于报告追溯。"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from .build_index import INDEX_PATH, build_records

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")


def _tokens(text: str) -> set[str]:
    return set(_token_list(text))


def _token_list(text: str) -> list[str]:
    normalized = (text or "").replace("_", " ").lower()
    tokens = _WORD_RE.findall(normalized)
    for sequence in _CHINESE_RE.findall(normalized):
        tokens.extend(sequence)
        tokens.extend(sequence[index:index + 2] for index in range(len(sequence) - 1))
    return tokens


def _load_records() -> list[dict]:
    if not INDEX_PATH.exists():
        return build_records()
    try:
        records = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        if isinstance(records, list) and records:
            return records
    except (OSError, json.JSONDecodeError):
        pass
    return build_records()


def retrieve_ranked(
    query: str,
    top_k: int = 4,
    categories: list[str] | None = None,
    min_score: float = 0.0,
) -> tuple[list[dict], dict]:
    """返回带分数和命中词的检索结果，供外部工具调用。"""
    query_counts = Counter(_token_list(query))
    query_tokens = set(query_counts)
    requested_categories = {category.lower() for category in categories or []}
    records = _load_records()
    eligible = []
    eligible_records = 0

    for record in records:
        if requested_categories and record.get("category", "").lower() not in requested_categories:
            continue

        eligible_records += 1
        document_counts = Counter(_token_list(f"{record.get('title', '')} {record.get('content', '')}"))
        eligible.append((record, document_counts))

    document_frequency = Counter()
    for _, document_counts in eligible:
        document_frequency.update(document_counts.keys())

    corpus_size = max(len(eligible), 1)
    idf = {
        token: math.log((corpus_size + 1) / (frequency + 1)) + 1
        for token, frequency in document_frequency.items()
    }
    query_norm = math.sqrt(sum((count * idf.get(token, 1.0)) ** 2 for token, count in query_counts.items()))

    scored = []
    for record, document_counts in eligible:
        matched_terms = sorted(query_tokens & set(document_counts))
        document_norm = math.sqrt(sum((count * idf[token]) ** 2 for token, count in document_counts.items()))
        dot_product = sum(
            query_counts[token] * document_counts[token] * (idf[token] ** 2)
            for token in matched_terms
        )
        score = dot_product / (query_norm * document_norm) if query_norm and document_norm else 0.0
        if matched_terms and score >= min_score:
            scored.append((score, record.get("source", ""), record.get("id", ""), matched_terms, record))

    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    matches = [
        {
            **record,
            "score": round(score, 4),
            "matched_terms": matched_terms,
        }
        for score, _, _, matched_terms, record in scored[: max(1, top_k)]
    ]
    return matches, {
        "records_scanned": len(records),
        "eligible_records": eligible_records,
        "matched_records": len(scored),
        "query_token_count": len(query_tokens),
    }


def list_categories() -> list[str]:
    return sorted({str(record.get("category", "")) for record in _load_records() if record.get("category")})


def retrieve(query: str, top_k: int = 4) -> list[dict]:
    """一期兼容入口：保持只返回知识片段的原有合同。"""
    matches, _ = retrieve_ranked(query, top_k=top_k)
    return [
        {
            key: value
            for key, value in match.items()
            if key not in {"score", "matched_terms"}
        }
        for match in matches
    ]

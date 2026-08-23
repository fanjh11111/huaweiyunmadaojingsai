"""供外部维修智能体调用的只读知识检索工具。"""

from __future__ import annotations

import json
import logging
import time
import uuid
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .build_index import INDEX_PATH, build_records, get_knowledge_base_version
from .retriever import list_categories, retrieve_ranked

TOOL_NAME = "maintenance_knowledge_retriever"
TOOL_VERSION = "1.0.0"
MAX_CHUNK_CONTENT_LENGTH = 4_000

logger = logging.getLogger("rag.tool")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class RagToolRequest(BaseModel):
    """外部智能体调用合同。未知字段会被拒绝，避免静默参数漂移。"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(min_length=2, max_length=500, description="待检索的维修知识问题或故障描述")
    request_id: str | None = Field(
        default=None,
        min_length=8,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
        description="调用方提供的链路追踪 ID；未提供时自动生成",
    )
    top_k: int = Field(default=4, ge=1, le=10, description="返回知识片段数量")
    categories: list[str] = Field(default_factory=list, max_length=5, description="可选知识分类过滤")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="最小关键词匹配分数")

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, categories: list[str]) -> list[str]:
        normalized = []
        for category in categories:
            value = category.strip().lower()
            if not value or not value.isascii() or not value.replace("_", "").isalpha():
                raise ValueError("categories 只能包含英文字母和下划线")
            normalized.append(value)
        return sorted(set(normalized))


class RagToolDocument(BaseModel):
    document_id: str
    title: str
    category: str
    source: str
    content: str
    content_hash: str
    content_truncated: bool
    score: float = Field(ge=0.0, le=1.0)
    matched_terms: list[str]


class RagToolMetadata(BaseModel):
    retrieval_mode: str = "tfidf_cosine"
    knowledge_base_version: str
    index_mode: str
    records_scanned: int
    eligible_records: int
    matched_records: int
    query_token_count: int
    duration_ms: int


class RagToolResponse(BaseModel):
    tool_name: str = TOOL_NAME
    tool_version: str = TOOL_VERSION
    request_id: str
    query: str
    read_only: bool = True
    result_count: int
    documents: list[RagToolDocument]
    warnings: list[str]
    metadata: RagToolMetadata


class RagToolHealth(BaseModel):
    status: str
    tool_name: str = TOOL_NAME
    tool_version: str = TOOL_VERSION
    knowledge_base_version: str
    index_mode: str
    document_count: int
    chunk_count: int
    categories: list[str]


def _log_event(event: str, **fields: Any) -> None:
    """只记录调用元数据，不记录可能包含维修数据的原始 query。"""
    logger.info(json.dumps({"event": event, "tool": TOOL_NAME, **fields}, ensure_ascii=False, sort_keys=True))


class MaintenanceKnowledgeRetriever:
    """可嵌入任意智能体框架的稳定 RAG 工具入口。"""

    name = TOOL_NAME
    version = TOOL_VERSION
    description = "检索航空发动机维修知识库，返回带来源、分数和内容哈希的只读证据片段。"

    def search(self, request: RagToolRequest | Mapping[str, Any]) -> RagToolResponse:
        request_model = request if isinstance(request, RagToolRequest) else RagToolRequest.model_validate(request)
        request_id = request_model.request_id or str(uuid.uuid4())
        started_at = time.perf_counter()

        matches, retrieval_stats = retrieve_ranked(
            request_model.query,
            top_k=request_model.top_k,
            categories=request_model.categories,
            min_score=request_model.min_score,
        )
        documents = [self._to_document(match) for match in matches]
        duration_ms = round((time.perf_counter() - started_at) * 1000)
        known_categories = set(list_categories())
        unknown_categories = sorted(set(request_model.categories) - known_categories)
        warnings = [f"UNKNOWN_CATEGORY:{category}" for category in unknown_categories]
        if not documents:
            warnings.append("NO_MATCHING_DOCUMENTS")

        response = RagToolResponse(
            request_id=request_id,
            query=request_model.query,
            result_count=len(documents),
            documents=documents,
            warnings=warnings,
            metadata=RagToolMetadata(
                knowledge_base_version=get_knowledge_base_version(),
                index_mode="persisted_json" if INDEX_PATH.exists() else "in_memory",
                duration_ms=duration_ms,
                **retrieval_stats,
            ),
        )
        _log_event(
            "search_completed",
            request_id=request_id,
            query_length=len(request_model.query),
            category_count=len(request_model.categories),
            result_count=response.result_count,
            duration_ms=duration_ms,
        )
        return response

    @staticmethod
    def _to_document(match: dict) -> RagToolDocument:
        content = str(match.get("content", ""))
        content_truncated = len(content) > MAX_CHUNK_CONTENT_LENGTH
        content = content[:MAX_CHUNK_CONTENT_LENGTH]
        content_hash = str(match.get("content_hash") or sha256(content.encode("utf-8")).hexdigest())
        return RagToolDocument(
            document_id=str(match.get("id", "")),
            title=str(match.get("title", "")),
            category=str(match.get("category", "")),
            source=str(match.get("source", "")),
            content=content,
            content_hash=content_hash,
            content_truncated=content_truncated,
            score=float(match.get("score", 0.0)),
            matched_terms=list(match.get("matched_terms", [])),
        )


def search_maintenance_knowledge(payload: Mapping[str, Any]) -> dict:
    """给智能体直接调用的函数入口，返回 JSON 可序列化字典。"""
    return MaintenanceKnowledgeRetriever().search(payload).model_dump()


def get_tool_health() -> RagToolHealth:
    """供部署探针和调用方启动检查使用。"""
    records = build_records()
    return RagToolHealth(
        status="ready" if records else "degraded",
        knowledge_base_version=get_knowledge_base_version(records),
        index_mode="persisted_json" if Path(INDEX_PATH).exists() else "in_memory",
        document_count=len({record["source"] for record in records}),
        chunk_count=len(records),
        categories=list_categories(),
    )


def get_openai_function_definition() -> dict:
    """返回兼容 OpenAI function calling 的工具描述，方便其他智能体框架注册。"""
    return {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": MaintenanceKnowledgeRetriever.description,
            "parameters": RagToolRequest.model_json_schema(),
        },
    }

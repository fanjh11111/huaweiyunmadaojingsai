"""维修知识问答智能体编排器。

职责：
1. 接收用户问题，结合可选的故障预测上下文构造检索 query。
2. 调用已完成的 RAG Tool（rag.tool.search_maintenance_knowledge）检索证据。
3. 将证据交回 LLM 客户端生成回答。
4. 执行安全后处理：超知识库范围时仍生成建议性回答并附加声明、放行问题追加人工复核提示。
5. 记录会话历史，支持多轮对话。

不修改原 RAG Tool、/api/predict 和报告接口。
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from ..tool import search_maintenance_knowledge
from .llm import LlmClient, LocalLlmClient, get_llm_client
from .prompts import (
    BEYOND_KB_NOTICE,
    NO_EVIDENCE_REPLY,
    OUT_OF_SCOPE_REPLY,
    SAFETY_SUFFIX,
    is_maintenance_related,
    is_release_related,
)
from .session import Session, SessionStore

logger = logging.getLogger("rag.chat.orchestrator")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

DEFAULT_TOP_K = 4
DEFAULT_MIN_SCORE = 0.05


class MaintenanceChatAgent:
    """维修知识问答智能体。"""

    def __init__(
        self,
        llm: LlmClient | None = None,
        session_store: SessionStore | None = None,
    ) -> None:
        self.llm = llm or get_llm_client()
        self.sessions = session_store or SessionStore()

    def chat(
        self,
        user_message: str,
        session_id: str | None = None,
        fault_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """处理一轮用户问答，返回结构化响应。"""
        session = self.sessions.get_or_create(session_id, fault_context)
        user_message = (user_message or "").strip()
        if not user_message:
            return self._build_response(session, "请输入维修相关问题。", [], "empty_input")

        if not is_maintenance_related(user_message):
            session.add_user_message(user_message)
            answer = self._generate_beyond_kb_answer(session, user_message)
            if not answer:
                answer = OUT_OF_SCOPE_REPLY
            else:
                answer = self._post_process(answer, user_message)
            session.add_assistant_message(answer, sources=[])
            return self._build_response(
                session, answer, [], "out_of_scope", llm_name=self.llm.name
            )

        query = self._build_query(user_message, session.fault_context)
        tool_result = self._call_rag_tool(query, session.session_id)
        documents = tool_result.get("documents", [])
        warnings = list(tool_result.get("warnings", []))

        session.add_user_message(user_message)

        if not documents:
            answer = self._generate_beyond_kb_answer(session, user_message)
            if not answer:
                answer = NO_EVIDENCE_REPLY
            else:
                answer = self._post_process(answer, user_message)
            session.add_assistant_message(answer, sources=[], tool_call=tool_result)
            return self._build_response(
                session,
                answer,
                [],
                "no_evidence",
                warnings=warnings,
                knowledge_base_version=tool_result.get("metadata", {}).get("knowledge_base_version"),
                llm_name=self.llm.name,
            )

        evidence = [self._slim_document(doc) for doc in documents]
        try:
            answer = self.llm.generate(user_message, evidence, session.to_history(), session_id=session.session_id)
        except Exception as exc:
            logger.warning("LLM 生成异常，回退本地拼接: %s", exc)
            answer = LocalLlmClient().generate(user_message, evidence, session.to_history(), session_id=session.session_id)

        if not answer:
            answer = LocalLlmClient().generate(user_message, evidence, session.to_history(), session_id=session.session_id)

        answer = self._post_process(answer, user_message)
        sources = [
            {
                "source": doc.get("source", ""),
                "title": doc.get("title", ""),
                "score": doc.get("score", 0.0),
                "content_hash": doc.get("content_hash", ""),
            }
            for doc in documents
        ]
        session.add_assistant_message(answer, sources=sources, tool_call=tool_result)
        return self._build_response(
            session, answer, sources, "success", warnings=warnings,
            knowledge_base_version=tool_result.get("metadata", {}).get("knowledge_base_version"),
            llm_name=self.llm.name,
        )

    def get_history(self, session_id: str) -> dict[str, Any] | None:
        session = self.sessions.get(session_id)
        if not session:
            return None
        return {
            "session_id": session.session_id,
            "messages": session.to_history(),
            "fault_context": session.fault_context,
        }

    def clear_session(self, session_id: str) -> bool:
        return self.sessions.delete(session_id)

    def _generate_beyond_kb_answer(self, session: Session, user_message: str) -> str:
        """知识库范围外仍生成建议性回答，并在开头附加超出知识库范围声明。

        生成失败时返回空串，由调用方回退到保守拒答文案。
        """
        generated = ""
        try:
            generated = self.llm.generate(
                user_message,
                [],
                session.to_history(),
                session_id=session.session_id,
                beyond_scope=True,
            )
        except Exception as exc:
            logger.warning("LLM 超范围生成异常，回退本地拼接: %s", exc)
        if not generated:
            generated = LocalLlmClient().generate(
                user_message,
                [],
                session.to_history(),
                session_id=session.session_id,
                beyond_scope=True,
            )
        if not generated:
            return ""
        return f"{BEYOND_KB_NOTICE}\n\n{generated}"

    def _build_query(self, user_message: str, fault_context: dict[str, Any] | None) -> str:
        """把用户问题和故障上下文合并成具体可检索的 query。"""
        parts: list[str] = [user_message]
        if fault_context:
            for key in ("component", "fault_type", "risk_level", "description"):
                value = fault_context.get(key)
                if value:
                    parts.append(str(value))
            features = fault_context.get("abnormal_features") or []
            if isinstance(features, list):
                parts.extend(str(feature) for feature in features if feature)
        return " ".join(parts)[:500]

    def _call_rag_tool(self, query: str, session_id: str) -> dict[str, Any]:
        """调用 RAG 检索工具，捕获异常避免阻断对话。"""
        try:
            return search_maintenance_knowledge(
                {
                    "request_id": f"{session_id}-{len(query)}",
                    "query": query,
                    "top_k": DEFAULT_TOP_K,
                    "min_score": DEFAULT_MIN_SCORE,
                }
            )
        except Exception as exc:
            logger.warning("RAG Tool 调用异常: %s", exc)
            return {"documents": [], "warnings": ["TOOL_CALL_FAILED"], "metadata": {}}

    @staticmethod
    def _slim_document(doc: dict[str, Any]) -> dict[str, Any]:
        """传给 LLM 的证据只保留必要字段。"""
        return {
            "content": doc.get("content", ""),
            "source": doc.get("source", ""),
            "title": doc.get("title", ""),
            "score": doc.get("score", 0.0),
        }

    @staticmethod
    def _post_process(answer: str, user_message: str) -> str:
        """安全后处理：放行相关问题追加人工复核提示。"""
        if is_release_related(user_message) and SAFETY_SUFFIX.strip() not in answer:
            answer = answer.rstrip() + SAFETY_SUFFIX
        return answer

    def _build_response(
        self,
        session: Session,
        answer: str,
        sources: list[dict[str, Any]],
        status: str,
        warnings: list[str] | None = None,
        knowledge_base_version: str | None = None,
        llm_name: str | None = None,
    ) -> dict[str, Any]:
        response: dict[str, Any] = {
            "session_id": session.session_id,
            "answer": answer,
            "sources": sources,
            "status": status,
            "llm": llm_name or self.llm.name,
            "warnings": warnings or [],
        }
        if knowledge_base_version:
            response["knowledge_base_version"] = knowledge_base_version
        return response


_agent_lock = threading.Lock()
_chat_agent: MaintenanceChatAgent | None = None


def get_chat_agent() -> MaintenanceChatAgent:
    """进程级单例，避免每次请求重建会话存储。"""
    global _chat_agent
    with _agent_lock:
        if _chat_agent is None:
            _chat_agent = MaintenanceChatAgent()
        return _chat_agent

"""可插拔 LLM 客户端（AgentArts / DashScope 代理层）。

默认 LocalLlmClient 零依赖运行，基于检索证据用模板拼接回答。
配置 AGENTARTS_API_URL + AGENTARTS_API_KEY 后自动切换到 AgentArtsLlmClient，
调用华为 AgentArts 智能体 API（POST /runtimes/{runtime}/invocations，body: {"query": "..."}）。
未配置 AgentArts 且 DashScope 可用（DASHSCOPE_ENABLED=1 且有 Key，复用
rag.invoke_dashscope 的配置）时，切换到 DashScopeLlmClient 调用 qwen-plus。

AgentArts API 格式（参考最佳实践文档）：
- 请求 Header: Authorization: Bearer {api_key}, x-hw-agentarts-session-id: {会话ID}
- 请求 Body: {"query": "用户问题"}
- 会话历史由 AgentArts 平台通过 session-id header 自动管理
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from .prompts import SYSTEM_PROMPT, is_release_related

logger = logging.getLogger("rag.chat.llm")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class LlmClient(Protocol):
    """LLM 客户端协议。"""

    name: str

    def generate(
        self,
        user_message: str,
        evidence: list[dict[str, Any]],
        history: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> str:
        """根据用户问题、检索证据、会话历史生成回答文本。"""
        ...


class LocalLlmClient:
    """零依赖本地客户端：基于检索证据用模板拼接回答。"""

    name = "local-template"

    def generate(
        self,
        user_message: str,
        evidence: list[dict[str, Any]],
        history: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> str:
        if not evidence:
            return ""
        lines: list[str] = [f"针对问题：{user_message}", "", "检查要点："]
        for index, doc in enumerate(evidence[:3], 1):
            lines.append(f"{index}. {doc.get('content', '').strip()}")
        return "\n".join(lines)


class AgentArtsLlmClient:
    """华为 AgentArts 智能体 API 客户端。

    API 格式：POST {api_url}，body: {"query": "..."}，
    header: Authorization: Bearer {api_key}, x-hw-agentarts-session-id: {会话ID}。
    会话历史由 AgentArts 平台通过 session-id 自动管理。
    检索证据拼进 query 传入，让智能体基于证据回答。
    """

    name = "agentarts"

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        user_message: str,
        evidence: list[dict[str, Any]],
        history: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> str:
        query = user_message
        if evidence:
            query = f"{user_message}\n\n[检索证据]\n{self._format_evidence(evidence)}"

        payload: dict[str, Any] = {"query": query}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        safe_session = (session_id or "default-session").replace(" ", "-")[:64]
        request = urllib.request.Request(
            self.api_url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {self.api_key}",
                "x-hw-agentarts-session-id": safe_session,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = self._extract_content(data)
            return content or ""
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
            logger.warning("AgentArts 调用失败，回退本地拼接: %s", exc)
            return LocalLlmClient().generate(user_message, evidence, history, session_id)

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        """兼容多种 AgentArts 响应格式。"""
        for key in ("answer", "response", "output", "result", "reply", "content"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
        choices = data.get("choices")
        if choices and isinstance(choices, list):
            message = choices[0].get("message", {})
            return str(message.get("content", ""))
        nested = data.get("data")
        if isinstance(nested, dict):
            for key in ("answer", "response", "output", "content"):
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        return ""

    @staticmethod
    def _format_evidence(evidence: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for index, doc in enumerate(evidence[:4], 1):
            lines.append(f"[{index}] 来源：{doc.get('source', '未知')}")
            lines.append(doc.get("content", "").strip())
            lines.append("")
        return "\n".join(lines)


class DashScopeLlmClient:
    """阿里云 DashScope (qwen-plus) 客户端：把证据和历史交给大模型组织回答。

    复用 rag.invoke_dashscope 的 DASHSCOPE_* 配置（环境变量优先）。
    调用失败抛异常，由 orchestrator 捕获后降级 LocalLlmClient，不阻断对话。
    """

    name = "dashscope-qwen-plus"

    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

    def generate(
        self,
        user_message: str,
        evidence: list[dict[str, Any]],
        history: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> str:
        import requests  # 延迟导入：未安装 requests 时本类仍可被构造/测试

        from ..dashscope_client import (
            DASHSCOPE_API_KEY,
            DASHSCOPE_MODEL,
            DASHSCOPE_TIMEOUT,
            DASHSCOPE_URL,
        )

        # 会话历史：去掉末尾的当前用户消息（orchestrator 已单独传入），最多带 8 条
        prior_messages = list(history or [])
        if prior_messages and prior_messages[-1].get("role") == "user":
            prior_messages = prior_messages[:-1]
        prior_messages = prior_messages[-8:]

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for message in prior_messages:
            role = message.get("role")
            content = str(message.get("content", "")).strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content[:1500]})

        evidence_text = AgentArtsLlmClient._format_evidence(evidence)
        user_content = (
            f"{user_message}\n\n[检索证据]\n{evidence_text}" if evidence_text else user_message
        )
        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": DASHSCOPE_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1200,
        }
        headers = {
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            DASHSCOPE_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout or DASHSCOPE_TIMEOUT,
        )
        if response.status_code != 200:
            raise RuntimeError(f"DashScope HTTP {response.status_code}: {response.text[:200]}")
        content = (
            response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        )
        if not content.strip():
            raise RuntimeError("DashScope 返回空内容")
        return content.strip()


def get_llm_client() -> LlmClient:
    """工厂：根据环境变量返回 LLM 客户端。优先级 AgentArts > DashScope > 本地模板。

    环境变量：
    - AGENTARTS_API_URL：AgentArts 智能体调用路径（从控制台"调用路径"复制）
    - AGENTARTS_API_KEY：AgentArts 智能体 API Key
    - AGENTARTS_MODEL：模型名（可选，AgentArts 通常不需要）
    - AGENTARTS_TIMEOUT：超时秒数，默认 60
    - DASHSCOPE_ENABLED：DashScope 开关，默认 1（见 rag.invoke_dashscope）
    - DASHSCOPE_API_KEY / DASHSCOPE_URL / DASHSCOPE_MODEL：DashScope 配置
    """
    api_url = os.getenv("AGENTARTS_API_URL")
    api_key = os.getenv("AGENTARTS_API_KEY")
    model = os.getenv("AGENTARTS_MODEL") or None
    timeout = int(os.getenv("AGENTARTS_TIMEOUT", "60"))
    if api_url and api_key:
        logger.info("使用 AgentArts 智能体: api_url=%s", api_url)
        return AgentArtsLlmClient(api_url, api_key, model=model, timeout=timeout)

    dashscope_ready = False
    try:
        from ..dashscope_client import DASHSCOPE_API_KEY, DASHSCOPE_ENABLED, DASHSCOPE_URL

        dashscope_ready = bool(DASHSCOPE_ENABLED and DASHSCOPE_API_KEY and DASHSCOPE_URL)
    except ImportError:
        dashscope_ready = False
    if dashscope_ready:
        logger.info("使用 DashScope qwen-plus 生成回答（失败自动降级本地模板）。")
        return DashScopeLlmClient()

    logger.info(
        "使用本地模板 LLM（零依赖，演示模式）。"
        "配置 AGENTARTS_API_URL + AGENTARTS_API_KEY 切换 AgentArts，"
        "或配置 DASHSCOPE_API_KEY 切换 DashScope。"
    )
    return LocalLlmClient()

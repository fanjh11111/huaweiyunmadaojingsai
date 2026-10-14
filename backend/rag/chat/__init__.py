"""维修知识问答智能体。

基于已完成的 RAG 检索工具（rag.tool）构建，提供多轮对话、证据回填、
引用追溯和安全边界能力。LLM 客户端可插拔：默认本地证据拼接器零依赖运行，
配置 AGENTARTS_API_URL + AGENTARTS_API_KEY 后自动切换到 AgentArts 智能体 API。
"""

from __future__ import annotations

from .orchestrator import MaintenanceChatAgent, get_chat_agent
from .session import SessionStore, Session

__all__ = [
    "MaintenanceChatAgent",
    "get_chat_agent",
    "SessionStore",
    "Session",
]
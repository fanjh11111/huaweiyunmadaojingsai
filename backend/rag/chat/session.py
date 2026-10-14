"""维修问答智能体的会话历史管理。

内存存储 + TTL 过期清理，适合单进程演示。后续可替换为 Redis 或数据库后端，
保持 Session 接口不变即可。
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    """单次问答会话。"""

    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    fault_context: dict[str, Any] | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_user_message(self, content: str) -> dict[str, Any]:
        message = {"role": "user", "content": content, "ts": time.time()}
        self.messages.append(message)
        self.updated_at = time.time()
        return message

    def add_assistant_message(
        self,
        content: str,
        sources: list[dict[str, Any]] | None = None,
        tool_call: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "ts": time.time(),
        }
        if sources:
            message["sources"] = sources
        if tool_call:
            message["tool_call"] = tool_call
        self.messages.append(message)
        self.updated_at = time.time()
        return message

    def to_history(self) -> list[dict[str, Any]]:
        """返回前端可展示的历史，去掉内部大字段。"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "ts": msg.get("ts"),
                "sources": msg.get("sources", []),
            }
            for msg in self.messages
        ]


class SessionStore:
    """线程安全的内存会话存储。"""

    def __init__(self, ttl_seconds: int = 3600, max_sessions: int = 200) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()
        self._ttl = ttl_seconds
        self._max = max_sessions

    def get_or_create(
        self,
        session_id: str | None = None,
        fault_context: dict[str, Any] | None = None,
    ) -> Session:
        now = time.time()
        with self._lock:
            self._cleanup_expired_locked(now)
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                if fault_context is not None:
                    session.fault_context = fault_context
                return session
            new_id = session_id or f"chat-{uuid.uuid4().hex[:12]}"
            session = Session(session_id=new_id, fault_context=fault_context)
            self._sessions[new_id] = session
            self._evict_oldest_locked()
            return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def clear(self) -> int:
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            return count

    def _cleanup_expired_locked(self, now: float) -> None:
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.updated_at > self._ttl
        ]
        for sid in expired:
            self._sessions.pop(sid, None)

    def _evict_oldest_locked(self) -> None:
        if len(self._sessions) <= self._max:
            return
        sorted_sessions = sorted(
            self._sessions.items(), key=lambda item: item[1].updated_at
        )
        while len(self._sessions) > self._max:
            sid, _ = sorted_sessions.pop(0)
            self._sessions.pop(sid, None)
"""DashScope 兼容接口客户端；密钥只从环境变量读取。"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
DASHSCOPE_URL = os.getenv(
    "DASHSCOPE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
)
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
DASHSCOPE_TIMEOUT = int(os.getenv("DASHSCOPE_TIMEOUT", "60"))
DASHSCOPE_ENABLED = os.getenv("DASHSCOPE_ENABLED", "1") == "1" and bool(DASHSCOPE_API_KEY)

_PROMPT_PATH = Path(__file__).parent / "agent_prompt_optimized.md"
_SYSTEM_PROMPT: str | None = None


def _get_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")
    return _SYSTEM_PROMPT


def _extract_json(text: str) -> dict | None:
    if not text:
        return None

    candidates = [text.strip()]
    if text.strip().startswith("```"):
        body = text.strip().split("\n", 1)
        if len(body) == 2:
            candidates.append(body[1].removesuffix("```").strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start, end = candidate.find("{"), candidate.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(candidate[start : end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
    return None


def invoke_llm(user_message: str, evidence: list[dict] | None = None) -> dict | None:
    """调用 Qwen 并返回结构化 JSON；未配置密钥或调用失败时返回 None。"""
    if not DASHSCOPE_ENABLED:
        return None

    evidence_text = ""
    if evidence:
        evidence_text = "\n\n".join(
            f"[{index}] 标题: {item.get('title', '')}\n片段: {item.get('content', '')[:500]}"
            for index, item in enumerate(evidence, 1)
        )

    content = user_message
    if evidence_text:
        content += f"\n\n检索证据：\n{evidence_text}"

    payload = {
        "model": DASHSCOPE_MODEL,
        "messages": [
            {"role": "system", "content": _get_system_prompt()},
            {"role": "user", "content": content},
        ],
        "temperature": 0.2,
    }
    try:
        response = requests.post(
            DASHSCOPE_URL,
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=DASHSCOPE_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return _extract_json(text)
    except (requests.RequestException, ValueError, IndexError, TypeError) as exc:
        logger.warning("DashScope 调用失败：%s", exc)
        return None

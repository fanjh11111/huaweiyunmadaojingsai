"""
华为云 AgentArts 智能体调用模块（API Key + SSE流式响应处理）

提供 invoke_agent() 和 invoke_rag_advice() 两个核心函数，
可独立运行测试，也可被 agent.py 导入作为 RAG 建议生成的后端。
"""
from __future__ import annotations

import json
import os
import uuid
import time
import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

GATEWAY_DOMAIN = os.getenv(
    "AGENTARTS_GATEWAY",
    "defaultgw-mm2tkn3cmn.cn-southwest-2.huaweicloud-agentarts.com",
)
RUNTIME_NAME = os.getenv(
    "AGENTARTS_RUNTIME",
    "agent-arts-43f093628fe94017bcfdec538c3dcc25",
)
INVOKE_URL = f"https://{GATEWAY_DOMAIN}/runtimes/{RUNTIME_NAME}/invocations"
API_KEY = os.getenv("AGENTARTS_API_KEY", "fa8bb892080d4df7b3c62e59a80c8fa2")

DEFAULT_TIMEOUT = int(os.getenv("AGENTARTS_TIMEOUT", "120"))
DEFAULT_RETRIES = int(os.getenv("AGENTARTS_RETRIES", "3"))
INVOKE_MODE = os.getenv("AGENTARTS_INVOKE_MODE", "debug")


@dataclass
class InvokeResult:
    success: bool
    output: str
    parsed: dict | None
    error: str | None
    error_code: str | None
    raw_events: list

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "parsed": self.parsed,
            "error": self.error,
            "error_code": self.error_code,
        }


def _parse_sse_stream(response):
    events = []
    text_parts = []

    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if not data_str:
            continue
        try:
            event = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        events.append(event)

        if event.get("event") == "error":
            break
        if event.get("event") == "done":
            break

        data = event.get("data")
        if isinstance(data, str):
            text_parts.append(data)
        elif isinstance(data, dict):
            content = data.get("content") or data.get("text") or data.get("output")
            if isinstance(content, str):
                text_parts.append(content)

    return events, "".join(text_parts)


def _extract_error(events):
    for event in events:
        if event.get("event") != "error":
            continue
        data = event.get("data", {})
        if isinstance(data, dict):
            message = data.get("message", "")
            code = data.get("code", "")
            if not code and "100025" in str(message):
                code = "100025"
            if not code and "103004" in str(message):
                code = "103004"
            return message, code
        if isinstance(data, str):
            return data, None
    return None, None


def _try_parse_json(text):
    if not text:
        return None

    candidates = [text]

    stripped = text.strip()
    if stripped.startswith("```"):
        for fence in ("```json", "```JSON", "```"):
            if stripped.startswith(fence):
                inner = stripped[len(fence):]
                if inner.endswith("```"):
                    inner = inner[:-3]
                candidates.append(inner.strip())

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(candidate[start:end + 1])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

    return None


def invoke_agent(input_text, session_id=None, max_retries=DEFAULT_RETRIES, timeout=DEFAULT_TIMEOUT):
    if session_id is None:
        session_id = str(uuid.uuid4()).replace("-", "")[:32]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "x-hw-agentarts-session-id": session_id,
        "Content-Type": "application/json",
        "X-Invoke-Mode": INVOKE_MODE,
    }
    payload = {"query": input_text}

    last_error = None
    last_error_code = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                INVOKE_URL, headers=headers, json=payload, timeout=timeout, stream=True
            )

            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                last_error_code = str(resp.status_code)
                logger.warning("AgentArts 调用失败 [%d/%d]: %s", attempt, max_retries, last_error)
                if resp.status_code in (401, 403):
                    return InvokeResult(False, "", None, last_error, last_error_code, [])
                time.sleep(min(2 ** attempt, 10))
                continue

            events, output_text = _parse_sse_stream(resp)
            err_msg, err_code = _extract_error(events)

            if err_msg:
                last_error = err_msg
                last_error_code = err_code
                logger.warning("AgentArts SSE错误 [%d/%d]: %s (code=%s)", attempt, max_retries, err_msg, err_code)
                if err_code in ("100025", "103004"):
                    time.sleep(min(2 ** attempt, 10))
                    continue
                return InvokeResult(False, output_text, _try_parse_json(output_text), err_msg, err_code, events)

            parsed = _try_parse_json(output_text)
            return InvokeResult(True, output_text, parsed, None, None, events)

        except requests.exceptions.Timeout:
            last_error = f"请求超时 ({timeout}s)"
            last_error_code = "timeout"
            logger.warning("AgentArts 超时 [%d/%d]", attempt, max_retries)
        except requests.exceptions.ConnectionError as e:
            last_error = f"连接错误: {e}"
            last_error_code = "connection"
            logger.warning("AgentArts 连接错误 [%d/%d]: %s", attempt, max_retries, e)
        except Exception as e:
            last_error = f"未知异常: {e}"
            last_error_code = "unknown"
            logger.warning("AgentArts 异常 [%d/%d]: %s", attempt, max_retries, e)

        time.sleep(min(2 ** attempt, 10))

    return InvokeResult(False, "", None, last_error, last_error_code, [])


def invoke_rag_advice(component="", fault_type="", risk_level="",
                      confidence=0.0, abnormal_features=None, description=""):
    input_data = {
        "component": component,
        "fault_type": fault_type,
        "risk_level": risk_level,
        "confidence": confidence,
        "abnormal_features": abnormal_features or [],
        "description": description,
    }
    return invoke_agent(json.dumps(input_data, ensure_ascii=False))


def is_available():
    return bool(API_KEY and RUNTIME_NAME and GATEWAY_DOMAIN)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    print("=" * 60)
    print("测试1: 简单对话")
    print("=" * 60)
    result1 = invoke_agent("针对特定型号的飞机的维修建议")
    print(f"成功: {result1.success}")
    print(f"错误: {result1.error}")
    print(f"输出: {result1.output[:500]}")
    if result1.parsed:
        print(f"解析JSON: {json.dumps(result1.parsed, ensure_ascii=False, indent=2)[:500]}")

    print("\n" + "=" * 60)
    print("测试2: 高压涡轮叶片维修建议（结构化输入）")
    print("=" * 60)
    result2 = invoke_rag_advice(
        component="高压涡轮一级转子叶片",
        fault_type="叶片裂纹风险",
        risk_level="高",
        confidence=0.88,
        abnormal_features=["HPT_Blade_Vibration", "EGT_Margin_Drop"],
        description="高压涡轮一级转子叶片振动异常，EGT裕度下降",
    )
    print(f"成功: {result2.success}")
    print(f"错误: {result2.error}")
    print(f"输出: {result2.output[:500]}")
    if result2.parsed:
        print(f"解析JSON: {json.dumps(result2.parsed, ensure_ascii=False, indent=2)[:500]}")

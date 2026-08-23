"""维修知识问答智能体集成测试。

覆盖：
1. 维修相关问题命中知识库并返回带来源回答。
2. 振动场景命中 engine_vibration.md。
3. 液压场景命中 hydraulic_leak.md。
4. 无证据问题拒答且不编造。
5. 超范围问题礼貌拒答。
6. 放行问题追加人工复核提示。
7. 多轮对话会话历史保持。
8. fault_context 增强检索。
9. 空消息返回 empty_input。
10. 会话清除生效。
11. LLM 异常时回退本地拼接不阻断。
"""

from __future__ import annotations

import unittest

from rag.chat import MaintenanceChatAgent
from rag.chat.llm import LocalLlmClient
from rag.chat.session import SessionStore


class MaintenanceChatAgentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = MaintenanceChatAgent(
            llm=LocalLlmClient(),
            session_store=SessionStore(),
        )

    def test_vibration_question_hits_evidence(self) -> None:
        result = self.agent.chat("发动机振动持续升高需要检查哪些部件？")
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["sources"])
        sources = [source["source"] for source in result["sources"]]
        self.assertTrue(any("engine_vibration" in source for source in sources))
        self.assertEqual(result["llm"], "local-template")

    def test_hydraulic_question_hits_evidence(self) -> None:
        result = self.agent.chat("液压系统压力下降疑似泄漏怎么处置？")
        self.assertEqual(result["status"], "success")
        sources = [source["source"] for source in result["sources"]]
        self.assertTrue(any("hydraulic_leak" in source for source in sources))

    def test_no_evidence_rejects_fabrication(self) -> None:
        from unittest.mock import patch

        with patch("rag.chat.orchestrator.search_maintenance_knowledge") as mock_search:
            mock_search.return_value = {
                "documents": [],
                "warnings": ["NO_MATCHING_DOCUMENTS"],
                "metadata": {},
            }
            result = self.agent.chat("发动机燃烧室第三方改装方案推荐")
        self.assertEqual(result["status"], "no_evidence")
        self.assertEqual(result["sources"], [])
        self.assertIn("现有信息不足", result["answer"])

    def test_out_of_scope_rejects_politely(self) -> None:
        result = self.agent.chat("今天天气怎么样？")
        self.assertEqual(result["status"], "out_of_scope")
        self.assertIn("只回答", result["answer"])

    def test_release_question_has_no_fixed_safety_suffix(self) -> None:
        result = self.agent.chat("发动机振动异常现在能否继续放行？")
        self.assertEqual(result["status"], "success")
        self.assertNotIn("安全提示", result["answer"])
        self.assertNotIn("特别提示", result["answer"])

    def test_generated_meta_explanation_is_removed(self) -> None:
        class NoticeLlm:
            name = "notice-test"

            def generate(self, *args, **kwargs) -> str:
                return (
                    "这是正常回答 [1]。\n\n"
                    "⚠️ **特别提示：**\n这段固定提示不应展示。\n\n"
                    "当前知识库仅提供原则性说明，不能替代具体手册。"
                )

        agent = MaintenanceChatAgent(llm=NoticeLlm(), session_store=SessionStore())
        result = agent.chat("发动机振动异常需要检查什么？")
        self.assertEqual(result["answer"], "这是正常回答。")

    def test_multi_turn_session_history(self) -> None:
        first = self.agent.chat("发动机振动异常需要检查什么？")
        session_id = first["session_id"]
        second = self.agent.chat("那轴承呢？", session_id=session_id)
        self.assertEqual(second["session_id"], session_id)
        history = self.agent.get_history(session_id)
        self.assertIsNotNone(history)
        roles = [message["role"] for message in history["messages"]]
        self.assertEqual(roles, ["user", "assistant", "user", "assistant"])

    def test_fault_context_enhances_query(self) -> None:
        result = self.agent.chat(
            "需要检查哪些部件？",
            fault_context={
                "component": "动力涡轮",
                "fault_type": "发动机振动异常",
                "risk_level": "高",
                "abnormal_features": ["Engine_Vibration_X_Axis"],
            },
        )
        self.assertEqual(result["status"], "success")
        sources = [source["source"] for source in result["sources"]]
        self.assertTrue(any("engine_vibration" in source for source in sources))

    def test_empty_input_returns_empty_status(self) -> None:
        result = self.agent.chat("")
        self.assertEqual(result["status"], "empty_input")
        self.assertEqual(result["sources"], [])

    def test_clear_session(self) -> None:
        first = self.agent.chat("发动机振动异常检查哪些部件？")
        session_id = first["session_id"]
        self.assertTrue(self.agent.clear_session(session_id))
        self.assertIsNone(self.agent.get_history(session_id))

    def test_llm_exception_falls_back(self) -> None:
        class FailingLlm:
            name = "failing"

            def generate(self, user_message, evidence, history):
                raise RuntimeError("模拟 LLM 故障")

        agent = MaintenanceChatAgent(
            llm=FailingLlm(),
            session_store=SessionStore(),
        )
        result = agent.chat("发动机振动异常检查哪些部件？")
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["answer"])
        self.assertTrue(result["sources"])


class TestDashScopeLlmClient(unittest.TestCase):
    """DashScopeLlmClient 消息组装与降级行为测试（mock 网络，不真实调用）。"""

    def test_generate_builds_messages_and_parses_content(self) -> None:
        from unittest.mock import patch

        from rag.chat.llm import DashScopeLlmClient

        captured: dict = {}

        class FakeResponse:
            status_code = 200

            def json(self):
                return {"choices": [{"message": {"content": " 大模型回答 "}}]}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["payload"] = json
            return FakeResponse()

        client = DashScopeLlmClient()
        history = [
            {"role": "user", "content": "上一轮问题"},
            {"role": "assistant", "content": "上一轮回答"},
            {"role": "user", "content": "当前问题"},
        ]
        evidence = [{"content": "振动处置知识", "source": "kb/a.md", "title": "a", "score": 0.5}]

        with patch("requests.post", side_effect=fake_post):
            answer = client.generate("当前问题", evidence, history)

        self.assertEqual(answer, "大模型回答")
        messages = captured["payload"]["messages"]
        # 系统提示词在最前，历史去掉了末尾重复的当前问题，最后一轮带检索证据
        self.assertEqual(messages[0]["role"], "system")
        roles = [message["role"] for message in messages]
        self.assertEqual(roles, ["system", "user", "assistant", "user"])
        self.assertIn("上一轮问题", messages[1]["content"])
        self.assertIn("检索证据", messages[-1]["content"])
        self.assertIn("振动处置知识", messages[-1]["content"])
        self.assertIn("当前问题", messages[-1]["content"])

    def test_http_error_raises_for_orchestrator_fallback(self) -> None:
        from unittest.mock import patch

        from rag.chat.llm import DashScopeLlmClient

        class FakeResponse:
            status_code = 429
            text = "rate limited"

            def json(self):
                return {}

        with patch("requests.post", return_value=FakeResponse()):
            with self.assertRaises(RuntimeError):
                DashScopeLlmClient().generate("发动机振动异常", [], [])


if __name__ == "__main__":
    unittest.main()

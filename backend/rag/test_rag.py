import unittest

from rag.agent import generate_advice, generate_followup


class RagAdviceTest(unittest.TestCase):
    def test_egt_evidence_and_high_risk_release_boundary(self):
        result = generate_advice({
            "fault_type": "EGT over temperature",
            "risk_level": "high",
            "abnormal_features": ["Exhaust_Gas_Temp"],
        })

        self.assertIn(result["status"], ("success", "fallback"))
        self.assertEqual(result["risk_level"], "高")
        self.assertIn("generated_by", result)
        if result["status"] == "success":
            self.assertTrue(result["references"])
            self.assertIn("不建议直接放行", result["release_recommendation"])

    def test_component_fallback_without_fault_type(self):
        result = generate_advice({"component": "动力涡轮", "risk_level": "中等"})

        self.assertTrue(result["abnormal_judgment"])
        self.assertIn(result["status"], ("success", "fallback"))

    def test_hydraulic_evidence(self):
        result = generate_advice({
            "fault_type": "hydraulic leak",
            "abnormal_features": "Hydraulic_System_Pressure",
        })

        self.assertIn(result["status"], ("success", "fallback"))
        self.assertIn("generated_by", result)

    def test_second_stage_actions_keep_references(self):
        context = generate_advice({
            "component": "动力涡轮",
            "fault_type": "发动机振动异常",
            "risk_level": "高",
        })

        for action in ("evidence", "why", "extra_checks"):
            result = generate_followup(context, action)
            self.assertEqual(result["status"], "success")
            self.assertTrue(result["references"])
            self.assertTrue(result["supported"])

    def test_release_question_is_conservative(self):
        context = generate_advice({"fault_type": "EGT 超温", "risk_level": "高"})
        result = generate_followup(context, "question", "现在能否继续放行？")

        self.assertTrue(result["supported"])
        self.assertTrue(result["answer"])

    def test_unknown_question_does_not_invent_answer(self):
        context = generate_advice({"fault_type": "发动机振动异常"})
        result = generate_followup(context, "question", "明天的天气怎么样？")

        self.assertFalse(result["supported"])
        self.assertIn("没有足够依据", result["answer"])


if __name__ == "__main__":
    unittest.main()

import unittest

from pydantic import ValidationError

from rag.tool import (
    MaintenanceKnowledgeRetriever,
    RagToolRequest,
    get_openai_function_definition,
    get_tool_health,
    search_maintenance_knowledge,
)


class RagToolContractTest(unittest.TestCase):
    def test_direct_call_returns_traceable_documents(self):
        result = search_maintenance_knowledge({
            "query": "engine vibration bearing rotor",
            "request_id": "agent-run-001",
            "top_k": 2,
        })

        self.assertEqual(result["tool_name"], "maintenance_knowledge_retriever")
        self.assertEqual(result["request_id"], "agent-run-001")
        self.assertGreater(result["result_count"], 0)
        self.assertLessEqual(result["result_count"], 2)
        self.assertEqual(len(result["documents"][0]["content_hash"]), 64)
        self.assertIn("source", result["documents"][0])
        self.assertIn("score", result["documents"][0])

    def test_category_filter_is_enforced(self):
        result = MaintenanceKnowledgeRetriever().search(RagToolRequest(
            query="发动机振动",
            categories=["engine_manual"],
        ))

        self.assertTrue(result.documents)
        self.assertTrue(all(item.category == "engine_manual" for item in result.documents))

    def test_tfidf_mode_and_min_score_are_enforced(self):
        result = search_maintenance_knowledge({
            "query": "engine vibration bearing rotor",
            "categories": ["engine_manual"],
            "min_score": 1.0,
        })

        self.assertEqual(result["metadata"]["retrieval_mode"], "tfidf_cosine")
        self.assertEqual(result["result_count"], 0)
        self.assertIn("NO_MATCHING_DOCUMENTS", result["warnings"])

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(ValidationError):
            RagToolRequest(query="x", top_k=11, unexpected=True)

    def test_no_match_is_explicit(self):
        result = MaintenanceKnowledgeRetriever().search({"query": "quantum banana"})

        self.assertEqual(result.result_count, 0)
        self.assertIn("NO_MATCHING_DOCUMENTS", result.warnings)
        self.assertEqual(result.metadata.matched_records, 0)

    def test_unknown_category_is_explicit(self):
        result = MaintenanceKnowledgeRetriever().search({
            "query": "engine vibration",
            "categories": ["unknown_category"],
        })

        self.assertIn("UNKNOWN_CATEGORY:unknown_category", result.warnings)
        self.assertIn("NO_MATCHING_DOCUMENTS", result.warnings)

    def test_tool_definition_is_callable_by_function_agents(self):
        definition = get_openai_function_definition()

        self.assertEqual(definition["type"], "function")
        self.assertEqual(definition["function"]["name"], "maintenance_knowledge_retriever")
        self.assertIn("properties", definition["function"]["parameters"])

    def test_health_reports_knowledge_base(self):
        health = get_tool_health()

        self.assertEqual(health.status, "ready")
        self.assertGreaterEqual(health.document_count, 3)
        self.assertGreaterEqual(health.chunk_count, health.document_count)
        self.assertIn("engine_manual", health.categories)


if __name__ == "__main__":
    unittest.main()

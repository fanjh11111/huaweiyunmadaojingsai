"""独立的本地 RAG 维修建议模块。"""

from .agent import generate_advice, generate_followup
from .tool import get_openai_function_definition, get_tool_health, search_maintenance_knowledge

__all__ = [
    "generate_advice",
    "generate_followup",
    "get_openai_function_definition",
    "get_tool_health",
    "search_maintenance_knowledge",
]

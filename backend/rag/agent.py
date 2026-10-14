"""根据故障上下文和检索证据生成固定结构的维修辅助建议。

优先调用阿里云 DashScope (qwen-plus) 生成建议，失败时降级到本地模板生成。
通过环境变量 DASHSCOPE_ENABLED=1 启用 DashScope（默认启用）。
"""

from __future__ import annotations

import json
import logging
import os

from .retriever import retrieve

logger = logging.getLogger(__name__)

_DASHSCOPE_ENABLED = os.getenv("DASHSCOPE_ENABLED", "1") == "1"


SCENARIOS = {
    "egt": {
        "name": "发动机参数超限（排气温度）",
        "keywords": ("egt", "排气温度", "超温", "温度超限", "过热", "排气系统", "燃烧室", "燃气涡轮"),
        "actions": ["核对排气温度峰值、持续时间和对应工况", "检查排气温度传感器、线束及安装状态", "复核燃油喷嘴、燃烧室和涡轮冷却/排气通道"],
    },
    "vibration": {
        "name": "发动机振动异常",
        "keywords": ("vibration", "振动", "振幅", "转子", "动力涡轮", "涡轮叶片", "压气机"),
        "actions": ["确认振动异常是否连续出现并核对转速关联", "检查传感器固定、线束和信号质量", "检查轴承、转子、叶片及传动连接状态"],
    },
    "hydraulic": {
        "name": "液压系统泄漏风险",
        "keywords": ("hydraulic", "液压", "泄漏", "液压油", "压力下降"),
        "actions": ["检查液压油量、压力趋势和泄漏位置", "依次检查管路、接头、作动筒及阀件", "必要时按维护手册隔离相关系统并执行复检"],
    },
}


def _scenario(context: dict) -> dict:
    text = " ".join(str(context.get(key, "")) for key in (
        "fault_type", "component", "description", "abnormal_features", "abnormal_judgment",
    ))
    text = text.lower()
    for scenario in SCENARIOS.values():
        if any(keyword.lower() in text for keyword in scenario["keywords"]):
            return scenario
    return {
        "name": "发动机综合异常",
        "keywords": ("发动机", "异常", "故障"),
        "actions": ["核对异常窗口、传感器趋势和模型输入质量", "按部件风险排行开展目视及功能检查", "结合最新维修手册和维护记录进行人工复核"],
    }


def _normalize_risk(risk: str) -> str:
    risk = str(risk or "中等")
    if risk.lower() in {"severe", "high", "高", "高风险", "严重"}:
        return "高"
    elif risk.lower() in {"minor", "low", "低", "低风险", "轻微"}:
        return "低"
    else:
        return "中"


def _try_dashscope(context: dict) -> dict | None:
    """调用 DashScope qwen-plus 生成建议，失败返回 None。"""
    if not _DASHSCOPE_ENABLED:
        return None

    try:
        from .dashscope_client import invoke_llm
    except ImportError:
        logger.warning("无法导入 DashScope 客户端模块")
        return None

    features = context.get("abnormal_features", []) or []
    if isinstance(features, str):
        features = [features]

    input_data = {
        "component": str(context.get("component", "")),
        "fault_type": str(context.get("fault_type", "")),
        "risk_level": _normalize_risk(context.get("risk_level") or context.get("levelText")),
        "confidence": float(context.get("confidence", 0.0) or 0.0),
        "abnormal_features": features,
        "description": str(context.get("description", "")),
    }
    user_message = json.dumps(input_data, ensure_ascii=False)

    scenario = _scenario(context)
    query = " ".join([
        scenario["name"],
        input_data["component"],
        input_data["fault_type"],
        " ".join(features),
    ])
    evidence = retrieve(query, top_k=6)

    parsed = invoke_llm(user_message, evidence)
    if parsed is None:
        logger.warning("DashScope 调用失败，降级到本地生成")
        return None

    return _map_dashscope_response(parsed, context, evidence)


def _map_dashscope_response(parsed: dict, context: dict, evidence: list[dict]) -> dict:
    """将 DashScope 响应映射为 generate_advice 输出格式。"""
    risk = _normalize_risk(parsed.get("risk_level") or context.get("risk_level") or context.get("levelText"))

    recommended_actions = parsed.get("recommended_actions", [])
    if recommended_actions and isinstance(recommended_actions[0], dict):
        actions = [item.get("action", "") for item in recommended_actions if item.get("action")]
    elif recommended_actions and isinstance(recommended_actions[0], str):
        actions = recommended_actions
    else:
        actions = []

    references = parsed.get("references", [])
    ref_mapped = []
    for ref in references:
        if isinstance(ref, dict):
            ref_mapped.append({
                "title": ref.get("title", ""),
                "source": ref.get("source_file", ref.get("source", "")),
                "content": ref.get("snippet", ref.get("content", "")),
            })

    if not ref_mapped and evidence:
        ref_mapped = [
            {"title": item["title"], "source": item["source"], "content": item["content"][:200]}
            for item in evidence[:4]
        ]

    return {
        "status": parsed.get("status", "success"),
        "generated_by": "dashscope-qwen-plus",
        "abnormal_judgment": parsed.get("abnormal_judgment", ""),
        "risk_level": risk,
        "recommended_actions": actions or ["请由有资质维修人员复核最新维修手册和适航指令"],
        "release_recommendation": parsed.get("release_recommendation", ""),
        "references": ref_mapped,
        "precautions": parsed.get("precautions", [
            "维修手册、适航指令和法规以最新有效官方版本为准。",
            "RAG 输出不能替代适航放行结论或人工检修记录。",
        ]),
    }


def generate_advice(context: dict) -> dict:
    if _DASHSCOPE_ENABLED:
        dashscope_result = _try_dashscope(context)
        if dashscope_result is not None:
            return dashscope_result

    return _generate_advice_local(context)


def _generate_advice_local(context: dict) -> dict:
    scenario = _scenario(context)
    risk = _normalize_risk(context.get("risk_level") or context.get("levelText"))

    features = context.get("abnormal_features", []) or []
    if isinstance(features, str):
        features = [features]

    query = " ".join([
        scenario["name"],
        str(context.get("component", "")),
        str(context.get("fault_type", "")),
        " ".join(map(str, features)),
    ])
    evidence = retrieve(query, top_k=4)
    references = [
        {"title": item["title"], "source": item["source"], "content": item["content"]}
        for item in evidence
    ]

    return {
        "status": "success",
        "generated_by": "local-rag-template",
        "abnormal_judgment": f"检索证据与当前输入共同指向：{scenario['name']}。该结论仅用于辅助排查。",
        "risk_level": risk,
        "recommended_actions": scenario["actions"],
        "release_recommendation": "不建议直接放行，应由有资质维修人员完成检查、复核最新手册要求后决定。" if risk == "高" else "完成建议检查并经有资质维修人员复核后，再按放行标准决定。",
        "references": references,
        "precautions": ["维修手册、适航指令和法规以最新有效官方版本为准。", "RAG 输出不能替代适航放行结论或人工检修记录。"],
    }


def _references_for_followup(context: dict, scenario: dict, question: str) -> list[dict]:
    existing = context.get("references") if isinstance(context, dict) else None
    if not question and isinstance(existing, list) and existing:
        return existing

    evidence = retrieve(f"{scenario['name']} {question}".strip(), top_k=4)
    return [
        {"title": item["title"], "source": item["source"], "content": item["content"]}
        for item in evidence
    ]


def generate_followup(context: dict, action: str = "question", question: str = "") -> dict:
    """生成第二阶段的单次解释、补充检查、依据查看或追问结果。"""
    context = context if isinstance(context, dict) else {}
    scenario = _scenario(context)
    action = action if action in {"evidence", "why", "extra_checks", "question"} else "question"
    question = str(question or "").strip()
    references = _references_for_followup(context, scenario, question if action == "question" else "")

    if action == "evidence":
        return {
            "status": "success",
            "action": action,
            "answer": "以下内容来自当前本地知识库检索结果，请以最新有效手册和规章为准。",
            "items": [],
            "references": references,
            "supported": bool(references),
        }

    if action == "why":
        return {
            "status": "success",
            "action": action,
            "answer": f"当前建议主要依据“{scenario['name']}”的排查流程：先确认异常趋势和信号质量，再检查相关部件，最后进行维修后复查。",
            "items": scenario["actions"],
            "references": references,
            "supported": bool(references),
        }

    if action == "extra_checks":
        extra_checks = [
            "保存异常发生时的时间窗口、发动机工况和维护记录",
            "检查相关传感器校准状态，并与人工检查结果交叉核对",
            "完成处置后记录复测结果，确认异常不再复现",
        ]
        return {
            "status": "success",
            "action": action,
            "answer": "在原建议之外，可补充以下检查项；是否执行由有资质维修人员结合手册决定。",
            "items": extra_checks,
            "references": references,
            "supported": bool(references),
        }

    if not question:
        return {
            "status": "success",
            "action": action,
            "answer": "请输入具体问题，例如“为什么这样建议”或“还需要检查哪些项目”。",
            "items": [],
            "references": references,
            "supported": False,
        }

    question_lower = question.lower()
    if any(keyword in question_lower for keyword in ("放行", "能否继续", "能不能飞", "release")):
        answer = context.get("release_recommendation") or "不能仅凭本系统结果决定放行，必须由有资质维修人员复核。"
        supported = True
    elif any(keyword in question_lower for keyword in ("检查", "排查", "怎么处理", "下一步", "check")):
        answer = "建议先按以下顺序开展检查，再依据最新维修手册决定后续处置。"
        supported = True
    elif any(keyword in question_lower for keyword in ("风险", "严重", "概率", "risk")):
        answer = f"当前报告标记为{context.get('risk_level', '中')}风险；该等级用于排序检查优先级，不替代人工故障确认。"
        supported = True
    else:
        answer = "当前本地知识库没有足够依据回答这个问题，请补充具体部件、异常参数或参考最新维修手册，由有资质人员复核。"
        supported = False

    return {
        "status": "success",
        "action": action,
        "answer": answer,
        "items": scenario["actions"] if supported and "检查" in answer else [],
        "references": references,
        "supported": supported and bool(references),
    }

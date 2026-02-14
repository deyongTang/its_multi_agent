"""
结果汇总与校验节点 (Merge & Verify Nodes)

架构说明：
- 智能助手系统不具备 RAG 能力，不做文档检索、Rerank、RRF 融合
- node_merge_results: 简单汇总多个来源的结果（知识库答案、搜索结果、本地数据）
- node_verify: 校验结果是否足够回答用户问题
"""

from multi_agent.workflow.state import AgentState
from infrastructure.logging.logger import logger


def node_merge_results(state: AgentState) -> dict:
    """
    结果汇总节点 (Fan-In)

    职责：
    1. 汇总并行检索节点返回的结果
    2. 简单去重（避免重复内容）
    3. 不做语义排序、不做 Rerank、不做 RRF

    输入来源：
    - node_query_knowledge: 知识库平台返回的答案 {"question": "...", "answer": "..."}
    - node_search_web: MCP 搜索返回的结果
    - node_query_local_tools: 本地数据库查询结果（服务站、POI 等）
    """
    raw_docs = state.get("retrieved_documents", [])
    logger.info(f"[Merge] 汇总 {len(raw_docs)} 条结果...")

    # 简单去重：基于 content 字段
    unique_docs = []
    seen = set()

    for doc in raw_docs:
        # 提取内容标识（可能是 answer、content 等字段）
        content_key = doc.get("answer") or doc.get("content") or str(doc)

        if content_key not in seen:
            seen.add(content_key)
            unique_docs.append(doc)

    logger.info(f"[Merge] 去重后剩余 {len(unique_docs)} 条结果")

    return {"retrieved_documents": unique_docs}


def node_verify(state: AgentState) -> dict:
    """
    结果校验节点

    职责：
    1. 检查汇总后的结果是否足够回答用户问题
    2. 决定是否需要重试或转人工

    校验逻辑：
    - 有结果 -> 通过校验，进入生成报告阶段
    - 无结果 & 重试次数 < 3 -> 触发查询扩展，重新检索
    - 无结果 & 重试次数 >= 3 -> 转人工服务
    """
    docs = state.get("retrieved_documents", [])
    retry_count = state.get("retry_count", 0)

    logger.info(f"[Verify] 校验 {len(docs)} 条结果，当前重试次数: {retry_count}")

    # 简单校验：有结果即通过
    # 未来可扩展：使用 LLM 判断结果质量

    # 此节点不更新状态，由后续的 route_verify_result 路由器决策
    return {}

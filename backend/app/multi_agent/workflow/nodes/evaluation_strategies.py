"""
检索结果评估策略 (Evaluation Strategies)

使用策略模式对不同数据源的检索结果进行质量评估：
- KBEvaluationStrategy       : KB 返回的是经过 Rerank + LLM 生成的完整答案，规则判断即可
- WebEvaluationStrategy      : Web 结果质量不稳定，需要 LLM 语义判断
- LocalToolsEvaluationStrategy: 结构化数据，按必要字段做 schema 校验

新增数据源时，只需新增一个 Strategy 类并注册到 STRATEGY_REGISTRY，
node_retrieval_evaluate 节点本身无需改动。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any

from infrastructure.logging.logger import logger
from infrastructure.ai.openai_client import sub_model
from infrastructure.utils.resilience import safe_parse_json, async_retry_with_timeout


@dataclass
class EvaluationResult:
    is_sufficient: bool
    suggestion: str   # "pass" | "retry_same" | "switch_source"
    reason: str


class BaseEvaluationStrategy(ABC):
    """评估策略抽象基类"""

    @abstractmethod
    async def evaluate(
        self,
        docs: List[Dict[str, Any]],
        original_query: str,
    ) -> EvaluationResult:
        ...


# ──────────────────────────────────────────────
# KB 策略：规则判断
# KB 服务内部已完成 Rerank + LLM 生成，质量已由 KB 保障
# 只需判断"有没有内容"，无需再调 LLM
# ──────────────────────────────────────────────
class KBEvaluationStrategy(BaseEvaluationStrategy):

    async def evaluate(
        self,
        docs: List[Dict[str, Any]],
        original_query: str,
    ) -> EvaluationResult:
        if not docs:
            logger.info("[Evaluate/KB] 无结果 → switch_source (fallback to web)")
            return EvaluationResult(
                is_sufficient=False,
                suggestion="switch_source",
                reason="KB 未返回任何结果",
            )

        content = docs[0].get("content", "").strip()
        if not content:
            logger.info("[Evaluate/KB] 内容为空 → switch_source")
            return EvaluationResult(
                is_sufficient=False,
                suggestion="switch_source",
                reason="KB 返回内容为空",
            )

        logger.info("[Evaluate/KB] 有效答案 → pass")
        return EvaluationResult(
            is_sufficient=True,
            suggestion="pass",
            reason="KB 已返回有效答案（内部已 Rerank 保障质量）",
        )


# ──────────────────────────────────────────────
# Web 策略：LLM 语义评估
# Web 结果为原始 snippet，质量参差不齐，需要 LLM 判断相关性
# ──────────────────────────────────────────────
class WebEvaluationStrategy(BaseEvaluationStrategy):

    @async_retry_with_timeout(timeout_s=20, max_retries=2)
    async def _call_llm(self, prompt: str) -> str:
        resp = await sub_model.ainvoke([{"role": "user", "content": prompt}])
        return resp.content if isinstance(resp.content, str) else str(resp.content)

    async def evaluate(
        self,
        docs: List[Dict[str, Any]],
        original_query: str,
    ) -> EvaluationResult:
        if not docs:
            logger.info("[Evaluate/Web] 无结果 → retry_same")
            return EvaluationResult(
                is_sufficient=False,
                suggestion="retry_same",
                reason="Web 未返回任何结果",
            )

        doc_summary = "\n".join(
            f"[{d.get('source', '')}] {d.get('content', '')[:200]}"
            for d in docs[:5]
        )

        prompt = f"""你是检索质量评估专家。请判断以下网络检索结果是否足够回答用户问题。

用户问题: {original_query}

检索结果:
{doc_summary}

评估标准：
- 只要结果与问题相关且含有用信息，就判 sufficient=true
- 网络结果本身有局限性，不要因不够完整就判 false
- 完全无关或空结果才判 false

只返回 JSON：
{{"sufficient": true/false, "reason": "简短理由", "suggestion": "pass"或"retry_same"}}"""

        try:
            text = await self._call_llm(prompt)
            result = safe_parse_json(text, {"sufficient": True, "suggestion": "pass"})
            is_sufficient = result.get("sufficient", True)
            suggestion = result.get("suggestion", "pass")
            reason = result.get("reason", "")
            logger.info(f"[Evaluate/Web] sufficient={is_sufficient}, suggestion={suggestion}, reason={reason}")
            return EvaluationResult(is_sufficient=is_sufficient, suggestion=suggestion, reason=reason)
        except Exception as e:
            logger.warning(f"[Evaluate/Web] LLM 判断失败，默认通过: {e}")
            return EvaluationResult(is_sufficient=True, suggestion="pass", reason="LLM 异常，默认通过")


# ──────────────────────────────────────────────
# Local Tools 策略：结构化字段校验
# local_tools 返回结构化数据（服务站、POI），按必要字段判断完整性
# ──────────────────────────────────────────────
class LocalToolsEvaluationStrategy(BaseEvaluationStrategy):

    # 不同 local_tools 意图必须包含的字段
    REQUIRED_FIELDS: Dict[str, List[str]] = {
        "service_station": ["content"],  # content 里含服务站名称 + 地址
        "poi_navigation":  ["content"],
    }

    async def evaluate(
        self,
        docs: List[Dict[str, Any]],
        original_query: str,
    ) -> EvaluationResult:
        if not docs:
            logger.info("[Evaluate/Local] 无结果 → retry_same")
            return EvaluationResult(
                is_sufficient=False,
                suggestion="retry_same",
                reason="本地工具未返回任何结果",
            )

        # 检查第一条结果的必要字段是否存在
        first = docs[0]
        source = first.get("source", "")
        intent_key = "service_station" if "LocalDB" in source else "poi_navigation"
        required = self.REQUIRED_FIELDS.get(intent_key, ["content"])

        missing = [f for f in required if not first.get(f, "").strip()]
        if missing:
            logger.info(f"[Evaluate/Local] 结果缺少必要字段 {missing} → retry_same")
            return EvaluationResult(
                is_sufficient=False,
                suggestion="retry_same",
                reason=f"结果缺少必要字段: {missing}",
            )

        logger.info(f"[Evaluate/Local] 结构校验通过，共 {len(docs)} 条结果 → pass")
        return EvaluationResult(
            is_sufficient=True,
            suggestion="pass",
            reason=f"本地工具返回 {len(docs)} 条有效结果",
        )


# ──────────────────────────────────────────────
# 策略注册表
# 新增数据源时，在此注册对应策略类即可
# ──────────────────────────────────────────────
STRATEGY_REGISTRY: Dict[str, BaseEvaluationStrategy] = {
    "kb":          KBEvaluationStrategy(),
    "web":         WebEvaluationStrategy(),
    "local_tools": LocalToolsEvaluationStrategy(),
}

_DEFAULT_STRATEGY = WebEvaluationStrategy()


def get_strategy(source: str) -> BaseEvaluationStrategy:
    """根据数据源名称获取对应评估策略，未注册时使用默认策略"""
    strategy = STRATEGY_REGISTRY.get(source, _DEFAULT_STRATEGY)
    if source not in STRATEGY_REGISTRY:
        logger.warning(f"[EvaluateStrategy] 未找到 source='{source}' 的策略，使用默认 Web 策略")
    return strategy

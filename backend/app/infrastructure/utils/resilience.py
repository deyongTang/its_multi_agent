"""
工业级弹性工具 (Resilience Utilities)

- safe_parse_json: 容错 JSON 解析，处理 LLM 输出格式不稳定问题
- async_retry_with_timeout: 异步超时 + 指数退避重试
"""
import re
import json
import asyncio
from functools import wraps
from typing import Any, Dict, Optional
from infrastructure.logging.logger import logger


def safe_parse_json(text: str, default: Optional[Dict] = None) -> Dict[str, Any]:
    """
    容错 JSON 解析，依次尝试：
    1. 直接解析
    2. 提取 ```json ... ``` 代码块
    3. 提取第一个 { ... } 片段
    解析失败返回 default。
    """
    if not text:
        return default or {}

    text = text.strip()

    # 1. 直接解析
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. markdown 代码块
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. 提取 { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    # 4. 截断修复：JSON 被截断时尝试补全（LLM 输出被 token limit 截断的情况）
    if start != -1:
        fragment = text[start:]
        # 统计未闭合的括号层数，补全缺失的 }
        depth = 0
        for ch in fragment:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        if depth > 0:
            try:
                return json.loads(fragment + "}" * depth)
            except (json.JSONDecodeError, ValueError):
                pass

    logger.warning(f"[safe_parse_json] 解析失败，返回默认值。原文: {text[:100]}")
    return default or {}


def async_retry_with_timeout(timeout_s: float = 30, max_retries: int = 2, backoff_base: float = 1.0):
    """
    异步超时 + 指数退避重试装饰器。

    Args:
        timeout_s: 单次调用超时秒数
        max_retries: 最大重试次数（不含首次）
        backoff_base: 退避基数（秒），实际等待 = base * 2^attempt
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            last_err = None
            for attempt in range(max_retries + 1):
                try:
                    return await asyncio.wait_for(fn(*args, **kwargs), timeout=timeout_s)
                except asyncio.TimeoutError:
                    last_err = TimeoutError(f"{fn.__name__} 超时 ({timeout_s}s)")
                    logger.warning(f"[Retry] {fn.__name__} 超时, attempt={attempt+1}/{max_retries+1}")
                except Exception as e:
                    last_err = e
                    logger.warning(f"[Retry] {fn.__name__} 异常: {e}, attempt={attempt+1}/{max_retries+1}")

                if attempt < max_retries:
                    wait = backoff_base * (2 ** attempt)
                    await asyncio.sleep(wait)

            raise last_err
        return wrapper
    return decorator

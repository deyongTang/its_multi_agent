"""
LangGraph 工作流测试

测试用例：
- T01: 闲聊场景（直接回复）
- T02: 技术问题（槽位不完整，触发追问）
"""

import asyncio
from multi_agent.workflow.runner import WorkflowRunner
from infrastructure.logging.logger import logger, trace_id_var
import uuid


async def test_case_01_chitchat():
    """
    T01: 闲聊场景测试

    预期流程：
    START -> node_intent -> route_intent -> node_general_chat -> END
    """
    print("\n" + "=" * 80)
    print("测试用例 T01: 闲聊场景")
    print("=" * 80)

    # 设置 trace_id
    trace_id = str(uuid.uuid4())[:8]
    trace_id_var.set(trace_id)

    runner = WorkflowRunner()

    result = await runner.run(
        user_query="你好啊，今天天气真不错",
        user_id="test_user",
        session_id="test_session_01",
    )

    print(f"\n最终状态:")
    print(f"  - 意图: {result.get('current_intent')}")
    print(f"  - 置信度: {result.get('intent_confidence')}")
    print(f"  - 回复消息: {result.get('messages', [])[-1].content if result.get('messages') else 'None'}")
    print(f"  - 错误日志: {result.get('error_log')}")

    assert result.get('current_intent') == 'chitchat', "意图识别错误"
    print("\n✅ T01 测试通过")


async def test_case_02_tech_incomplete():
    """
    T02: 技术问题（槽位不完整）

    预期流程：
    START -> node_intent -> route_intent -> node_slot_filling -> route_slot_check -> node_ask_user -> END (interrupt)
    """
    print("\n" + "=" * 80)
    print("测试用例 T02: 技术问题（槽位不完整）")
    print("=" * 80)

    # 设置 trace_id
    trace_id = str(uuid.uuid4())[:8]
    trace_id_var.set(trace_id)

    runner = WorkflowRunner()

    result = await runner.run(
        user_query="电脑蓝屏了",
        user_id="test_user",
        session_id="test_session_02",
    )

    print(f"\n最终状态:")
    print(f"  - 意图: {result.get('current_intent')}")
    print(f"  - 置信度: {result.get('intent_confidence')}")
    print(f"  - 已提取槽位: {result.get('slots')}")
    print(f"  - 缺失槽位: {result.get('missing_slots')}")
    print(f"  - 追问次数: {result.get('ask_user_count')}")
    print(f"  - 追问消息: {result.get('messages', [])[-1].content if result.get('messages') else 'None'}")
    print(f"  - 错误日志: {result.get('error_log')}")

    assert result.get('current_intent') == 'tech', "意图识别错误"
    assert result.get('ask_user_count') > 0, "应该触发追问"
    print("\n✅ T02 测试通过")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("LangGraph 工作流测试套件 - Phase 1")
    print("=" * 80)

    try:
        # T01: 闲聊
        await test_case_01_chitchat()

        # T02: 技术问题（槽位不完整）
        await test_case_02_tech_incomplete()

        print("\n" + "=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

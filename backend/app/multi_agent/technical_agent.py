from infrastructure.ai.prompt_loader import load_prompt
from infrastructure.ai.openai_client import sub_model
from infrastructure.tools.local.knowledge_base import query_knowledge
from infrastructure.tools.mcp.mcp_servers import get_search_mcp_client
from agents import Agent, ModelSettings
from agents import Runner,RunConfig


# 1. 定义技术智能体（延迟初始化 MCP 客户端）
def get_technical_agent():
    """
    获取技术智能体实例

    使用函数包装以延迟 MCP 客户端的初始化，
    确保在调用时 settings 已经完全加载
    """
    return Agent(
        name="资讯与技术专家",
        instructions=load_prompt("technical_agent"),
        model=sub_model,
        model_settings=ModelSettings(temperature=0),  # 不要发挥内容(软件层面限制模型的发挥)
        tools=[query_knowledge],
        mcp_servers=[get_search_mcp_client()],
    )

# 为了向后兼容，保留旧的变量名（但改为 None，需要时调用 get_technical_agent()）
technical_agent = None


# 2. 测试技术智能体
async def run_single_test(case_name: str, input_text: str):

    print(f"\n{'=' * 80}")
    print(f"测试用例: {case_name}")
    print(f"输入: \"{input_text}\"")
    print("-" * 80)
    try:
        search_client = get_search_mcp_client()
        await search_client.connect()
        print("思考中...")
        agent = get_technical_agent()
        result = await Runner.run(agent, input=input_text,run_config=RunConfig(tracing_disabled=True))
        print(f"\n\nAgent的最终输出: {result.final_output}")
    except Exception as e:
        print(f"\n Error: {e}\n")
    finally:
        try:
            search_client = get_search_mcp_client()
            await search_client.cleanup()
        except:
            pass


async def main():
    # 技术问题测试案例
    test_cases = [
        # ("Case 1: 技术问题", "如何使用U盘安装Windows 7操作系统"),
        # ("Case 2: 实时问题", "今天北京的天气怎么样，出行的时候需要多穿厚衣服嘛?"),
        # ("Case 3  技术问题", "导航去昌平区温都水城"),  # 应拒绝
        # ("Case 3  技术问题", "请帮我查下一下最近的服务站有哪些"),  # 应拒绝
        # ("Case 3  技术问题", "1+1等于多少?"),  # 应拒绝
        ("Case 4  闲聊", "你好啊，我今天真的很不开心,你有什么想对我说"),  # 应拒绝
    ]

    for name, question in test_cases:
        await run_single_test(name, question)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())


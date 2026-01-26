from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from typing import List
from config.settings import settings
import re

def clean_markdown_images(text: str) -> str:
    """将 [描述](url) 替换为纯 url，每张图单独一行"""
    pattern = r'!\$$[^$$]*\]\((https?://[^\s\)]+)\)'
    def replace_func(match):
        url = match.group(1)
        return f"\n{url}\n"
    cleaned = re.sub(pattern, replace_func, text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

class QueryService:
    def __init__(self):
        # 注意：api_key 和 base_url 已通过 main.py 的 setup_environment() 设置到环境变量
        # ChatOpenAI 会自动从 OPENAI_API_KEY 和 OPENAI_BASE_URL 环境变量读取
        self.llm = ChatOpenAI(
            model=settings.MODEL,
            temperature=0,
            timeout=60,  # 设置60秒超时，避免无限等待
            max_retries=2  # 最多重试2次
        )

    def rewrite_query(self, question: str) -> str:
        """
        利用 LLM 对用户问题进行重写，使其更适合知识库检索。
        例如：去除口语化词汇、补充缺失的主语、规范化术语。
        """
        prompt = f"""
        你是一个专业的搜索查询优化助手。你的任务是将用户的输入重写为一个更精准、更适合从 IT 知识库中检索文档的查询语句。

        请遵循以下规则：
        1. 去除无意义的语气词（如“啊”、“呢”、“怎么办”）。
        2. 补充可能的缺失信息（根据常识推断）。
        3. 将口语化描述转换为专业术语（例如“连不上网” -> “网络连接失败”）。
        4. 保持简洁，直接输出重写后的查询语句，不要包含任何解释或额外文字。

        用户输入: {question}
        重写后的查询:
        """
        try:
            from langchain_core.messages import HumanMessage
            # 调用 LLM 生成重写后的查询
            response = self.llm.invoke([HumanMessage(content=prompt)])
            rewritten_query = response.content.strip()
            
            # 简单的后处理，去掉可能包含的引号
            rewritten_query = rewritten_query.replace('"', '').replace("'", "")
            
            return rewritten_query
        except Exception as e:
            print(f"⚠️ 查询重写失败，使用原始问题: {e}")
            return question

    def generate_answer(self, question: str, context_docs: List[Document]) -> str:
        """生成回答"""
        if not context_docs:
            return "未找到相关知识，请上传相关文档后再查询。"

        context_text = "\n\n".join([f"资料{i + 1}：{doc.page_content}" for i, doc in enumerate(context_docs)])
        
        prompt = f"""
       请根据以下资料回答用户问题，不能基于资料中未提及的信息。

       【重要格式要求】
        - 资料中的图片链接必须保留，但**不要使用 Markdown 图片语法（如 [描述](链接)）**。
        - 请直接写出**完整的图片 URL**（例如：https://example.com/image.png），每张图占一行。
        - 回答应简洁、步骤清晰，避免冗余信息。
        - 不要提及具体设备型号、品牌或软件版本（如“联想”、“UltraISO”等），除非问题明确要求。
        - 如果当前问题和资料中的信息不相关，直接回复“资料中未提及相关信息”。
        
        资料：```
        {context_text}
        ```
        
        用户问题：```
        {question}
        ```

        回答：
        """
        
        try:
            # 使用消息格式调用 LLM（兼容阿里百炼等 API）
            from langchain_core.messages import HumanMessage

            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            answer = response.content
            cleaned_answer = clean_markdown_images(answer)
            return cleaned_answer
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return "抱歉，生成回答时出现错误。"

    def generate_answer_stream(self, question: str, context_docs: List[Document]):
        """
        流式生成回答（Generator）

        Args:
            question: 用户问题
            context_docs: 检索到的上下文文档

        Yields:
            str: 生成的文本片段
        """
        # 导入日志模块
        try:
            from infrastructure.logger import logger
        except ImportError:
            logger = None

        if not context_docs:
            yield "未找到相关知识，请上传相关文档后再查询。"
            return

        # 构建上下文（与 generate_answer 保持一致）
        context_text = "\n\n".join([f"资料{i + 1}：{doc.page_content}" for i, doc in enumerate(context_docs)])

        # 记录上下文长度
        if logger:
            logger.info(f"📝 上下文长度: {len(context_text)} 字符 | 文档数: {len(context_docs)}")

        prompt = f"""
       请根据以下资料回答用户问题，不能基于资料中未提及的信息。

       【重要格式要求】
        - 资料中的图片链接必须保留，但**不要使用 Markdown 图片语法（如 [描述](链接)）**。
        - 请直接写出**完整的图片 URL**（例如：https://example.com/image.png），每张图占一行。
        - 回答应简洁、步骤清晰，避免冗余信息。
        - 不要提及具体设备型号、品牌或软件版本（如"联想"、"UltraISO"等），除非问题明确要求。
        - 如果当前问题和资料中的信息不相关，直接回复"资料中未提及相关信息"。

        资料：```
        {context_text}
        ```

        用户问题：```
        {question}
        ```

        回答：
        """

        try:
            from langchain_core.messages import HumanMessage
            import time
            import os

            messages = [HumanMessage(content=prompt)]

            # 记录开始时间和环境变量（用于调试）
            start_time = time.time()
            if logger:
                logger.info("🚀 开始流式生成答案")
                logger.debug(f"🔧 API配置 | BASE_URL: {os.environ.get('OPENAI_BASE_URL', 'NOT_SET')} | MODEL: {settings.MODEL}")

            # 使用 stream() 方法进行流式生成
            chunk_count = 0
            total_chars = 0

            if logger:
                logger.info("📡 正在调用 LLM stream API...")

            for chunk in self.llm.stream(messages):
                if chunk.content:
                    chunk_count += 1
                    total_chars += len(chunk.content)

                    # 每收到第一个chunk时记录日志
                    if chunk_count == 1 and logger:
                        logger.info("✅ 已收到第一个响应块")

                    yield chunk.content

            # 记录结束时间和统计信息
            elapsed_time = time.time() - start_time
            if logger:
                logger.info(f"✅ 流式生成完成 | 耗时: {elapsed_time:.2f}秒 | 生成字符数: {total_chars} | 分块数: {chunk_count}")

        except Exception as e:
            if logger:
                logger.error(f"❌ LLM流式调用失败: {type(e).__name__}: {str(e)}")
                # 记录完整的异常堆栈
                import traceback
                logger.error(f"📋 异常堆栈:\n{traceback.format_exc()}")
            else:
                print(f"LLM流式调用失败: {e}")
            yield "抱歉，生成回答时出现错误。"
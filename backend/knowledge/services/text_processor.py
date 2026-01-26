"""
文本预处理和切分服务
负责中文分词、文本切分等预处理操作
"""

from typing import List, Dict, Any
import hashlib
import jieba
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from config.settings import settings
    from infrastructure.logger import logger
except ModuleNotFoundError:
    import sys
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from config.settings import settings
    from infrastructure.logger import logger


class TextProcessor:
    """文本预处理服务"""

    def __init__(self):
        """初始化分词器和切分器"""
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

        # 初始化 LangChain 的递归字符切分器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n## ",  # Markdown 二级标题
                "\n### ",  # Markdown 三级标题
                "\n#### ",  # Markdown 四级标题
                "\n\n",  # 段落分隔
                "\n",  # 换行
                "。",  # 中文句号
                "！",  # 中文感叹号
                "？",  # 中文问号
                "；",  # 中文分号
                ".",  # 英文句号
                "!",  # 英文感叹号
                "?",  # 英文问号
                " ",  # 空格
                "",  # 字符级别（最后的兜底）
            ],
        )
        logger.info(
            f"✅ 文本处理器初始化成功 (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )

    def segment_chinese(self, text: str) -> str:
        """
        中文分词，使用空格分隔

        Args:
            text: 原始文本

        Returns:
            str: 分词后的文本（空格分隔）
        """
        words = jieba.cut(text)
        return " ".join(words)

    def split_text(self, text: str, title: str = "") -> List[Dict[str, Any]]:
        """
        使用 LangChain 的 RecursiveCharacterTextSplitter 切分文本

        优势：
        1. 递归切分：优先按大分隔符（标题、段落），切不动再用小分隔符（句号、空格）
        2. 识别 Markdown 结构：保留标题层级，避免在标题中间切断
        3. 语义优先：在合适的语义边界处切分，保持上下文完整性

        Args:
            text: 原始文本
            title: 文档标题（可选，用于日志）

        Returns:
            List[Dict]: 切片列表，每个切片包含 content 和 chunk_index
        """
        # 如果文本长度小于 chunk_size，不切分
        if len(text) <= self.chunk_size:
            return [{"content": text, "chunk_index": 0}]

        # 使用 LangChain 的切分器进行智能切分
        text_chunks = self.text_splitter.split_text(text)

        # 转换为目标格式
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_text = chunk_text.strip()
            if chunk_text:  # 过滤空白 chunk
                chunks.append({"content": chunk_text, "chunk_index": i})

        logger.info(
            f"✅ 文本切分完成: {len(chunks)} 个 chunks (使用 LangChain RecursiveCharacterTextSplitter)"
        )
        return chunks

    @staticmethod
    def generate_knowledge_no(file_path: str) -> str:
        """
        生成知识点唯一标识符

        Args:
            file_path: 文件路径

        Returns:
            str: knowledge_no (文件路径的 MD5 hash)
        """
        return hashlib.md5(file_path.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    from infrastructure.logger import logger

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)

    processor = TextProcessor()

    print("\n" + "=" * 60)
    print("测试 1: 中文分词")
    print("=" * 60)
    text = "这是一个测试文本，用于验证中文分词功能。"
    segmented = processor.segment_chinese(text)
    print(f"原文: {text}")
    print(f"分词结果: {segmented}")

    print("\n" + "=" * 60)
    print("测试 2: Markdown 文档切分（带标题结构）")
    print("=" * 60)
    markdown_text = """# 联想手机K900常见问题汇总

## 问题1：如何插拔SIM卡

K900采用Micro-Sim卡，请按照以下步骤操作：
1. 关闭手机电源
2. 使用卡针打开卡槽
3. 将SIM卡放入卡槽

## 问题2：如何连接WiFi

进入设置 > 无线和网络 > WLAN，选择要连接的网络。

## 问题3：电池续航问题

如果电池续航时间短，请尝试以下方法：
- 降低屏幕亮度
- 关闭不必要的后台应用
- 开启省电模式

## 问题4：系统更新

定期检查系统更新可以获得更好的性能和安全性。
"""
    chunks = processor.split_text(markdown_text, "联想手机K900常见问题")
    print(f"切分结果: {len(chunks)} 个 chunks")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i} (长度: {len(chunk['content'])} 字符) ---")
        print(
            chunk["content"][:200] + "..."
            if len(chunk["content"]) > 200
            else chunk["content"]
        )

    print("\n" + "=" * 60)
    print("测试 3: 超长文本切分")
    print("=" * 60)
    long_text = "这是一段很长的文本。" * 500
    chunks = processor.split_text(long_text, "超长文本测试")
    print(f"切分结果: {len(chunks)} 个 chunks")
    print(f"第一个 chunk 长度: {len(chunks[0]['content'])} 字符")
    print(f"最后一个 chunk 长度: {len(chunks[-1]['content'])} 字符")

    print("\n" + "=" * 60)
    print("测试 4: 生成 knowledge_no")
    print("=" * 60)
    knowledge_no = TextProcessor.generate_knowledge_no("/path/to/file.md")
    print(f"knowledge_no: {knowledge_no}")

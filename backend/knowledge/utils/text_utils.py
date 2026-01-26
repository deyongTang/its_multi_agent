from bs4 import BeautifulSoup,Tag
from markdownify import markdownify as md
import re


class TextUtils:
    @staticmethod
    def html_to_markdown(html_content: str) -> str:
        """
        HTML转Markdown (包含必要的 DOM 清洗)
        """
        if not html_content:
            return ""

        # 1. 使用 BeautifulSoup 进行结构化清洗
        soup = BeautifulSoup(html_content, 'html.parser')

        # 1.1 移除完全无用的标签 (噪音) ---
        # 移除 script, style 标签
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose() # 标签移除掉了

        # 1.2  移除特定广告或无用元素（扩展）
        for ad in soup.select('.mceNonEditable'):
            ad.decompose() # 标签移除掉

        # 核心逻辑：合并相邻的 strong/b 标签
        # 场景：<strong>A</strong><strong>B</strong> -> <strong>AB</strong>

        # 查找所有的加粗标签
        bold_tags = soup.find_all(['strong', 'b'])
        for tag in bold_tags:
            # 安全检查：如果标签在之前的循环中已经被合并（删除）了，跳过
            if not tag.parent:
                continue
            # 获取下一个兄弟节点
            next_sibling = tag.next_sibling

            # 判断条件：
            # 1. 下一个兄弟存在
            # 2. 下一个兄弟也是 Tag 对象 (不是纯文本换行符)
            # 3. 下一个兄弟的标签名相同 (都是 strong 或 都是 b)
            if next_sibling and isinstance(next_sibling, Tag) and next_sibling.name == tag.name:
                # 【合并动作】
                # 1. 把下一个标签里的内容（文字或子标签）全部追加到当前标签里
                tag.extend(next_sibling.contents)
                # 2. 销毁下一个标签
                next_sibling.decompose()

        # 2. 将清洗后的 HTML 转为字符串
        cleaned_html = str(soup)

        # 3. 使用 markdownify 转换
        markdown_text = md(cleaned_html)
        return markdown_text

    @staticmethod
    def clean_filename(filename: str) -> str:
        """清洗文件名中的非法字符"""
        if not filename:
            return "untitled"
        illegal_chars = r'[\\/:*?"<>|]'
        return re.sub(illegal_chars, '-', filename)
from typing import Dict, Any
from  utils.text_utils import TextUtils


class HtmlParser:
    """专门负责解析Html格式数据成为MarkDown格式的数据"""

    def parse_html_to_markdown(self, knowledge_no: str, html_data: Dict[str, Any]) -> str:
        """
        解析html格式成为markdown格式
        :param html_data:html格式数据
        :return:markdown格式的字符串数据
        """

        # 1.判断内容是否有
        if  not html_data['content']:
            raise ValueError("要解析的数据不存在")

        # 2.从html_data中提起md文件需要的数据
        # 2.1 提取知识库编号
        items = [f"# 知识库 {knowledge_no}\n"]  # 知识库的项

        # 2.2 提取知识库的标题（必须要有）
        html_data_title = html_data.get('title', '暂无标题')
        items.append(f"## 标题\n{html_data_title.strip()}\n")

        # 2.3 提取digest(摘要 比标题还具有代表性)
        html_data_digest= html_data['digest']
        if html_data_digest and html_data_digest.strip():
            items.append(f"## 问题描述\n{html_data_digest.strip()}\n")

        # 2.4 提取知识库的分类（分类系）
        # a.firstTopicName(主分类) b.subTopicName（子分类） c.questionCategoryName（早起遗留的分类名，问题对应的分类）
        first_topic_name = html_data['firstTopicName']
        sub_topic_name = html_data['subTopicName']
        question_category_name = html_data['questionCategoryName']

        categories=[]
        if  first_topic_name and first_topic_name.strip():
            categories.append(f"主类别: {first_topic_name.strip()}")
        if  sub_topic_name and sub_topic_name.strip():
            categories.append(f"子类别: {sub_topic_name.strip()}")
        elif question_category_name and question_category_name.strip():
            categories.append(f"问题类别: {question_category_name}")

        if  categories:
            items.append(f"## 分类\n"+"\n".join(categories)+"\n")

        # 2.5 提取知识库关键词：打散 清洗 在组合（1.相似检索【原数据】可以根据关键词检索 2.提高召回率）
        html_data_key_words=html_data['keyWords']
        key_words_list=[]
        if html_data_key_words:
            for key_world in  html_data_key_words:
                if isinstance(key_world,str):
                   # ["U盘装系统","U盘系统盘","安装","U盘"]
                   parts = key_world.split(",")
                   for part in parts:
                       cleaned = part.strip()
                       if cleaned:
                           key_words_list.append(cleaned)
            if key_words_list:
                keywords = ", ".join(key_words_list)
                items.append(f"## 关键词\n{keywords}\n")


        # 2.6 构建元信息（时效性、版本）
        medata_data = []
        html_data_create_time=html_data['createTime']
        html_data_version_no=html_data['versionNo']
        if html_data_create_time and html_data_create_time.strip():
            medata_data.append(f"创建时间:{html_data_create_time.strip()}")
        if html_data_version_no and html_data_version_no.strip():
            medata_data.append(f"版本:{html_data_version_no.strip()}")
        if medata_data:
            items.append(f"## 元信息\n" + "|".join(medata_data) + "\n")

        # 2.7 构建内容（解决方案）
        html_data_content=html_data['content']
        if  html_data_content:

            # 1.html数据清洗和解析成md
            # 1.1 清洗的本质将html的结构进行压缩（把无用的标签都移除掉（css js 广告等）廋身）
            md_content=TextUtils.html_to_markdown(html_data_content)

            items.append(f"## 解决方案\n{md_content}\n")


        # 2.8 构建标题作为知识库的注释（防止切块之后导致文档上下文丢失）
        items.append(f"<!-- 文档主题：{html_data_title} (知识库库编号: {knowledge_no}) -->")

        return  "\n".join(items)



























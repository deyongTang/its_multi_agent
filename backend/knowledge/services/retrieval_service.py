import os
import re
import jieba
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.documents import Document

from config.settings import settings
from data_access.vector_store_manager import VectorStoreManager


class RetrievalService:
    def __init__(self):
        self.vector_manager = VectorStoreManager()

    def collect_md_metadata(self, folder_path: str) -> List[Dict[str, Any]]:
        """收集MD文件元数据（路径+标题）"""
        md_metadata = []
        if not os.path.exists(folder_path):
            return md_metadata

        filename_pattern = re.compile(r"^(.+?)-(.*?)\.md$")

        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                match = filename_pattern.match(filename)
                if match:
                    title = match.group(2).strip()
                else:
                    title = os.path.splitext(filename)[0].strip()

                md_metadata.append(
                    {"path": os.path.join(folder_path, filename), "title": title}
                )
        return md_metadata

    def rough_ranking(self, md_metadata: List[Dict], user_question: str) -> List[Dict]:
        """粗排：基于标题关键词重合度（混合模式）"""
        user_question = user_question.strip()
        if not user_question:
            for item in md_metadata:
                item["rough_score"] = 0
            return sorted(md_metadata, key=lambda x: x["rough_score"], reverse=True)[
                : settings.TOP_ROUGH
            ]

        JIEBA_WEIGHT = 0.7

        for item in md_metadata:
            title = item.get("title", "")
            if not title or not title.strip():
                item["rough_score"] = 0
                continue

            question_chars = set(user_question)
            title_chars = set(title.strip())
            ## len(question_chars & title_chars)`: 计算共有字符的数量
            char_score = (
                len(question_chars & title_chars) / (len(question_chars) + 1e-6)
                if question_chars
                else 0
            )

            question_words = set(jieba.lcut(user_question))
            title_words = set(jieba.lcut(title.strip()))
            word_score = (
                len(question_words & title_words) / (len(question_words) + 1e-6)
                if question_words
                else 0
            )

            combined_score = JIEBA_WEIGHT * word_score + (1 - JIEBA_WEIGHT) * char_score
            item["rough_score"] = combined_score

        return sorted(md_metadata, key=lambda x: x.get("rough_score", 0), reverse=True)[
            : settings.TOP_ROUGH
        ]

    def fine_ranking(self, rough_results: List[Dict], user_question: str) -> List[Dict]:
        """精排：结合Embedding语义相似度和粗排分数"""
        if not rough_results:
            return []

        question_embedding = self.vector_manager.embed_query(user_question)
        titles = [item["title"] for item in rough_results]
        title_embeddings = self.vector_manager.embed_documents(titles)

        # 转换为 numpy 数组
        question_embedding_array = np.array(question_embedding).reshape(1, -1)
        title_embeddings_array = np.array(title_embeddings)

        semantic_similarities = cosine_similarity(
            question_embedding_array, title_embeddings_array
        ).flatten()

        WEIGHT_ROUGH = 0.5
        WEIGHT_SEMANTIC = 0.5

        for i, item in enumerate(rough_results):
            semantic_score = max(0, float(semantic_similarities[i]))
            rough_score = item.get("rough_score", 0)
            combined_score = (
                WEIGHT_ROUGH * rough_score + WEIGHT_SEMANTIC * semantic_score
            )
            item["semantic_score"] = semantic_score
            item["combined_score"] = combined_score

        return sorted(rough_results, key=lambda x: x["combined_score"], reverse=True)[
            : settings.TOP_FINAL
        ]

    def retrieve(self, user_question: str) -> List[Document]:
        all_candidates = []

        # 第一路：向量库检索
        retriever = self.vector_manager.get_retriever()
        vector_docs = retriever.invoke(user_question)
        all_candidates.extend(vector_docs)

        # 第二路：标题匹配召回
        if os.path.exists(settings.MD_FOLDER_PATH):
            metadata = self.collect_md_metadata(settings.MD_FOLDER_PATH)
            rough = self.rough_ranking(metadata, user_question)
            final_title_matches = self.fine_ranking(rough, user_question)

            for item in final_title_matches[:5]:
                try:
                    with open(item["path"], "r", encoding="utf-8") as f:
                        content = f.read()
                        doc = Document(
                            page_content=content,
                            metadata={"source": item["path"], "title": item["title"]},
                        )
                        all_candidates.append(doc)
                except Exception as e:
                    print(f"读取文件失败 {item['path']}: {e}")

        # 去重
        seen = set()
        unique_candidates = []
        for doc in all_candidates:
            key = (doc.metadata.get("source", ""), doc.page_content[:100])
            if key not in seen:
                seen.add(key)
                unique_candidates.append(doc)

        if not unique_candidates:
            return []

        # 统一重排序
        question_emb = self.vector_manager.embed_query(user_question)
        candidate_texts = [doc.page_content for doc in unique_candidates]
        candidate_embs = self.vector_manager.embed_documents(candidate_texts)

        # 转换为 numpy 数组
        question_emb_array = np.array(question_emb).reshape(1, -1)
        candidate_embs_array = np.array(candidate_embs)

        similarities = cosine_similarity(question_emb_array, candidate_embs_array).flatten()

        scored_docs = [
            (unique_candidates[i], float(similarities[i]))
            for i in range(len(unique_candidates))
        ]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        top_docs = [doc for doc, score in scored_docs[: settings.TOP_FINAL]]

        return top_docs

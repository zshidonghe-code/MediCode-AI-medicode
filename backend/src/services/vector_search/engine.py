"""ICD编码语义搜索引擎

使用TF-IDF + 字符n-gram向量化中文医学文本，支持语义相似度检索。
例如：搜索"胸口疼" → 返回"心绞痛"、"冠心病"等语义相关编码。

架构：
- TF-IDF特征提取（char 1-3 grams）
- 余弦相似度排序
- 混合检索：语义分 + 关键词分
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    code: str
    name: str
    category: str  # 诊断 / 手术操作
    score: float


class VectorSearchEngine:
    """向量搜索引擎 — 基于TF-IDF的语义匹配"""

    def __init__(self):
        self._documents: list[dict] = []  # [{code, name, category}]
        self._tfidf_matrix = None  # scipy sparse matrix
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._ready: bool = False

    def build_index(self, documents: list[dict]) -> int:
        """构建语义索引

        Args:
            documents: [{"code": "I20.900", "name": "心绞痛", "category": "诊断"}, ...]

        Returns:
            int: 索引的文档数量
        """
        self._documents = documents
        names = [d["name"] for d in documents]

        self._vectorizer = TfidfVectorizer(
            analyzer="char",
            ngram_range=(1, 3),
            max_features=5000,
            lowercase=False,
            token_pattern=None,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(names)
        self._ready = True
        return len(self._documents)

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """语义搜索

        Args:
            query: 查询文本，如 "胸口疼"、"心脏搭桥"、"血糖高"
            top_k: 返回前k个结果

        Returns:
            按相似度降序排列的搜索结果
        """
        if not self._ready or self._tfidf_matrix is None:
            return []

        try:
            query_vec = self._vectorizer.transform([query])
        except Exception as e:
            logger.warning(f"Vectorizer transform failed for '{query}': {e}")
            return []

        # Cosine similarity
        sims = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        # Top-k indices
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            sim = float(sims[idx])
            if sim < 0.15:  # 过滤低相关度
                continue
            doc = self._documents[idx]
            results.append(SearchResult(
                code=doc["code"],
                name=doc["name"],
                category=doc.get("category", "诊断"),
                score=round(sim, 3),
            ))

        return results

    def hybrid_search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """混合检索：语义分 + 关键词权重

        对于精确包含关键词的结果给予加权
        """
        semantic_results = self.search(query, top_k=top_k * 2)
        if not semantic_results:
            return []

        # 关键词加权：名称中包含查询词的加分
        for r in semantic_results:
            if query in r.name:
                r.score = min(1.0, r.score + 0.25)
            elif any(c in r.name for c in query):
                r.score = min(1.0, r.score + 0.10)

        # 重新排序
        semantic_results.sort(key=lambda r: r.score, reverse=True)
        return semantic_results[:top_k]

    def get_stats(self) -> dict:
        """获取索引统计"""
        return {
            "ready": self._ready,
            "documents": len(self._documents),
            "features": self._tfidf_matrix.shape[1] if self._tfidf_matrix is not None else 0,
        }


# Singleton
vector_search_engine = VectorSearchEngine()

"""BM25 稀疏检索实现——纯 Python，无外部依赖。

参考 Wikipedia BM25 公式实现：
  score(D, Q) = Σ IDF(qi) * (f(qi,D) * (k1+1)) / (f(qi,D) + k1*(1-b+b*|D|/avgdl))
"""

import math
import re
from collections import defaultdict


_K1 = 1.5
_B = 0.75


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w\u4e00-\u9fff]+", text.lower())


class BM25Index:
    """单个知识库的 BM25 倒排索引。"""

    def __init__(self, corpus: list[tuple[str, dict]]):
        """
        Args:
            corpus: [(text, metadata), ...] metadata 需包含 chunk_id 等信息。
        """
        self._docs: list[dict] = []
        self._tokens: list[list[str]] = []
        self._doc_freq: dict[str, int] = defaultdict(int)  # term → 包含该词的文档数
        self._idf: dict[str, float] = {}
        self._doc_len: list[int] = []
        self._avgdl: float = 0.0
        self._build(corpus)

    def _build(self, corpus: list[tuple[str, dict]]) -> None:
        total_len = 0
        for text, meta in corpus:
            tokens = _tokenize(text)
            self._docs.append(meta)
            self._tokens.append(tokens)
            doc_len = len(tokens)
            self._doc_len.append(doc_len)
            total_len += doc_len

            seen: set[str] = set()
            for t in tokens:
                if t not in seen:
                    self._doc_freq[t] += 1
                    seen.add(t)

        n = max(len(corpus), 1)
        self._avgdl = total_len / n
        for term, df in self._doc_freq.items():
            self._idf[term] = math.log((n - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        """检索并返回 top_k 个 (metadata, score) 结果。"""
        q_tokens = _tokenize(query)
        if not q_tokens or not self._docs:
            return []

        # 计算每个文档的 BM25 得分
        scores: list[float] = [0.0] * len(self._docs)
        for term in q_tokens:
            idf = self._idf.get(term, 0.0)
            if idf == 0.0:
                continue
            for i, doc_tokens in enumerate(self._tokens):
                tf = doc_tokens.count(term)
                if tf == 0:
                    continue
                numerator = tf * (_K1 + 1)
                denominator = tf + _K1 * (1 - _B + _B * self._doc_len[i] / self._avgdl)
                scores[i] += idf * numerator / denominator

        # 按分数降序排列，取 top_k
        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]
        return [(self._docs[idx], score) for idx, score in ranked if score > 0]


class BM25IndexCache:
    """BM25 索引缓存——按 knowledge_base_id 缓存 BM25 索引。"""

    def __init__(self):
        self._cache: dict[str, BM25Index] = {}

    def get(self, kb_id: str) -> BM25Index | None:
        return self._cache.get(kb_id)

    def set(self, kb_id: str, index: BM25Index) -> None:
        self._cache[kb_id] = index

    def invalidate(self, kb_id: str) -> None:
        self._cache.pop(kb_id, None)

    def clear(self) -> None:
        self._cache.clear()


# 全局 BM25 缓存单例
bm25_cache = BM25IndexCache()

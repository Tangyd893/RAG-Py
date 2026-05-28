"""BM25 检索单元测试。"""

import pytest
from app.infrastructure.retrieval.bm25 import BM25Index, bm25_cache, _tokenize


class TestBM25Tokenize:
    def test_chinese(self):
        tokens = _tokenize("你好世界")
        assert "你好世界" in tokens

    def test_english(self):
        tokens = _tokenize("Hello World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_mixed(self):
        tokens = _tokenize("RAG 检索系统 v2.0")
        assert "rag" in tokens
        assert "检索系统" in tokens
        assert "v2" in tokens
        assert "0" in tokens

    def test_empty(self):
        assert _tokenize("") == []
        assert _tokenize("   ") == []


class TestBM25Index:
    def test_build_and_search_single_doc(self):
        corpus = [("Python 是一门编程语言", {"id": "1"})]
        index = BM25Index(corpus)
        results = index.search("Python", top_k=5)
        assert len(results) == 1
        assert results[0][0]["id"] == "1"
        assert results[0][1] > 0

    def test_search_no_match(self):
        corpus = [("Hello World", {"id": "1"})]
        index = BM25Index(corpus)
        results = index.search("不存在", top_k=5)
        assert results == []

    def test_ranking(self):
        corpus = [
            ("Python 机器学习 深度学习", {"id": "1"}),
            ("Java 后端开发 Spring 框架", {"id": "2"}),
            ("Python 数据分析 机器学习", {"id": "3"}),
        ]
        index = BM25Index(corpus)
        results = index.search("Python 机器学习", top_k=5)
        ids = [r[0]["id"] for r in results]
        assert ids[0] in ("1", "3")
        assert len(ids) <= 3

    def test_empty_corpus(self):
        index = BM25Index([])
        results = index.search("test", top_k=5)
        assert results == []

    def test_top_k_truncation(self):
        corpus = [(f"文档内容 {i}", {"id": str(i)}) for i in range(20)]
        index = BM25Index(corpus)
        results = index.search("文档内容", top_k=5)
        assert len(results) == 5


class TestBM25Cache:
    def setup_method(self):
        bm25_cache.clear()

    def test_set_and_get(self):
        corpus = [("测试文本", {"id": "1"})]
        index = BM25Index(corpus)
        bm25_cache.set("kb_1", index)
        assert bm25_cache.get("kb_1") is index

    def test_miss(self):
        assert bm25_cache.get("nonexistent") is None

    def test_invalidate(self):
        index = BM25Index([("test", {"id": "1"})])
        bm25_cache.set("kb_1", index)
        bm25_cache.invalidate("kb_1")
        assert bm25_cache.get("kb_1") is None

    def test_clear(self):
        bm25_cache.set("kb_1", BM25Index([("a", {"id": "1"})]))
        bm25_cache.set("kb_2", BM25Index([("b", {"id": "2"})]))
        bm25_cache.clear()
        assert bm25_cache.get("kb_1") is None
        assert bm25_cache.get("kb_2") is None

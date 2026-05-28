"""评测指标单元测试。"""

import pytest
from tests.eval.metrics import (
    recall_at_k,
    mrr,
    ndcg_at_k,
    compute_all_metrics,
    EvalResult,
)


class TestRecallAtK:
    def test_all_retrieved(self):
        assert recall_at_k(["a", "b", "c"], {"a", "b"}, 3) == 1.0

    def test_half_retrieved(self):
        assert recall_at_k(["a", "d", "e"], {"a", "b"}, 3) == 0.5

    def test_none_retrieved(self):
        assert recall_at_k(["x", "y"], {"a", "b"}, 3) == 0.0

    def test_empty_relevant(self):
        assert recall_at_k(["a", "b"], set(), 3) == 0.0

    def test_truncated_by_k(self):
        assert recall_at_k(["a", "b"], {"a", "b"}, 1) == 0.5


class TestMRR:
    def test_perfect(self):
        assert mrr([["a", "b"]], [{"a"}]) == 1.0

    def test_second_position(self):
        assert mrr([["x", "a", "b"]], [{"a"}]) == 0.5

    def test_not_found(self):
        assert mrr([["x", "y"]], [{"a"}]) == 0.0

    def test_multi_query_avg(self):
        # q1: rank=1 → 1.0, q2: rank=2 → 0.5, avg = 0.75
        m = mrr([["a", "b"], ["x", "c"]], [{"a"}, {"c"}])
        assert m == pytest.approx(0.75)


class TestNDCG:
    def test_perfect(self):
        # 完美排序：相关度递减
        rel_map = {"a": 3, "b": 2, "c": 1}
        score = ndcg_at_k(["a", "b", "c"], rel_map, 3)
        assert score == pytest.approx(1.0)

    def test_imperfect(self):
        rel_map = {"a": 3, "b": 2, "c": 1}
        score = ndcg_at_k(["b", "c", "a"], rel_map, 3)
        assert score < 1.0

    def test_empty(self):
        assert ndcg_at_k([], {}, 3) == 0.0
        assert ndcg_at_k(["a", "b"], {}, 3) == 0.0


class TestComputeAllMetrics:
    def test_basic(self):
        retrieved = [["c1", "c2", "c4", "c5", "c6"]]
        relevant_sets = [{"c1", "c2", "c3"}]
        relevance_maps = [{"c1": 3, "c2": 2, "c3": 1}]

        result = compute_all_metrics("test", retrieved, relevant_sets, relevance_maps)
        assert result.label == "test"
        assert result.num_queries == 1
        assert result.recall_1 == pytest.approx(1.0 / 3)
        assert result.recall_3 == pytest.approx(2.0 / 3)
        assert result.recall_5 == pytest.approx(2.0 / 3)
        assert result.mrr == pytest.approx(1.0)

    def test_multi_query(self):
        retrieved = [["a", "b"], ["x", "c"]]
        relevant_sets = [{"a"}, {"c"}]
        relevance_maps = [{"a": 3, "b": 1}, {"c": 2}]

        result = compute_all_metrics("multi", retrieved, relevant_sets, relevance_maps)
        assert result.num_queries == 2
        assert result.mrr == pytest.approx(0.75)

    def test_empty_input(self):
        result = compute_all_metrics("empty", [], [], [])
        assert result.num_queries == 0
        assert result.recall_1 == 0.0
        assert result.mrr == 0.0

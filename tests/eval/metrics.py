"""检索评测指标——Recall@k、MRR、NDCG@k。"""

import math


def recall_at_k(
    retrieved_ids: list[str], relevant_ids: set[str], k: int
) -> float:
    """Recall@k：top-k 结果中召回了多少相关文档。"""
    if not relevant_ids:
        return 0.0
    top_k_ids = set(retrieved_ids[:k])
    return len(top_k_ids & relevant_ids) / len(relevant_ids)


def mrr(
    queries_retrieved: list[list[str]],
    queries_relevant: list[set[str]],
) -> float:
    """MRR (Mean Reciprocal Rank)：首个相关文档排名的倒数均值。"""
    if not queries_retrieved:
        return 0.0
    total = 0.0
    for retrieved, relevant in zip(queries_retrieved, queries_relevant):
        if not relevant:
            continue
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                total += 1.0 / rank
                break
    return total / max(len(queries_retrieved), 1)


def ndcg_at_k(
    retrieved_ids: list[str],
    relevance_map: dict[str, float],
    k: int,
) -> float:
    """NDCG@k：归一化折损累积增益。

    Args:
        retrieved_ids: 检索结果 doc_id 列表（按排序）
        relevance_map: {doc_id: relevance_score}  分数越高越相关
        k: Top-k
    """
    if not retrieved_ids or not relevance_map:
        return 0.0

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        rel = relevance_map.get(doc_id, 0.0)
        if rel > 0:
            dcg += rel / math.log2(i + 2)

    # IDCG（理想排序的 DCG）
    ideal_rels = sorted(relevance_map.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels):
        if rel > 0:
            idcg += rel / math.log2(i + 2)

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


class EvalResult:
    """单次评测结果。"""

    def __init__(self, label: str):
        self.label = label
        self.recall_1: float = 0.0
        self.recall_3: float = 0.0
        self.recall_5: float = 0.0
        self.mrr: float = 0.0
        self.ndcg_5: float = 0.0
        self.num_queries: int = 0


def compute_all_metrics(
    label: str,
    queries_retrieved: list[list[str]],
    queries_relevant_sets: list[set[str]],
    queries_relevance_maps: list[dict[str, float]],
) -> EvalResult:
    """批量计算所有评测指标。"""
    result = EvalResult(label)
    result.num_queries = len(queries_retrieved)
    if result.num_queries == 0:
        return result

    # Recall@k
    r1_sum = r3_sum = r5_sum = 0.0
    for retrieved, relevant in zip(queries_retrieved, queries_relevant_sets):
        r1_sum += recall_at_k(retrieved, relevant, 1)
        r3_sum += recall_at_k(retrieved, relevant, 3)
        r5_sum += recall_at_k(retrieved, relevant, 5)
    result.recall_1 = r1_sum / result.num_queries
    result.recall_3 = r3_sum / result.num_queries
    result.recall_5 = r5_sum / result.num_queries

    # MRR
    result.mrr = mrr(queries_retrieved, queries_relevant_sets)

    # NDCG@5
    ndcg_sum = 0.0
    for retrieved, rel_map in zip(queries_retrieved, queries_relevance_maps):
        ndcg_sum += ndcg_at_k(retrieved, rel_map, 5)
    result.ndcg_5 = ndcg_sum / result.num_queries

    return result


def format_eval_results(*results: EvalResult) -> str:
    """格式化输出多组评测结果对比。"""
    col_width = max(len(r.label) for r in results) + 2
    if col_width < 8:
        col_width = 8
    header = f"{'指标':<14}" + "".join(f"{r.label:>{col_width}}" for r in results)
    lines = [header, "-" * len(header)]

    metrics = [
        ("Recall@1", "recall_1"),
        ("Recall@3", "recall_3"),
        ("Recall@5", "recall_5"),
        ("MRR", "mrr"),
        ("NDCG@5", "ndcg_5"),
        ("查询数", "num_queries"),
    ]
    for name, attr in metrics:
        row = f"{name:<14}"
        for r in results:
            val = getattr(r, attr)
            if isinstance(val, int):
                row += f"{val:>{col_width}}"
            else:
                row += f"{val:>{col_width}.4f}"
        lines.append(row)

    return "\n".join(lines)

"""评测运行器——跨检索模式对比评测。

用法：
    # 基础评测（仅指标计算）
    python tests/eval/runner.py

    # 完整评测（需要运行中的应用）
    python tests/eval/runner.py --remote http://localhost:8000 --kb-id <uuid>
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests.eval.dataset import SAMPLE_DATASET, EvalDataset, EvalQuery
from tests.eval.metrics import compute_all_metrics, format_eval_results


async def run_local_baseline(dataset: EvalDataset) -> str:
    """本地基线评测——模拟不同检索模式的结果进行指标对比。

    使用预定义的模拟结果演示三种检索模式的指标差异。
    """
    # 模拟结果：每种模式对每个 query 返回的 chunk_id 排序列表
    # 实际使用时替换为真实检索结果
    mock_results = {
        "Dense": {
            # q1: 什么是 RAG  →  向量检索返回 [c2, c1, c3, c4, c5]
            "q1": ["c2", "c4", "c1", "c3", "c5"],
            "q2": ["c1", "c4", "c2", "c3", "c5"],
            "q3": ["c1", "c5", "c4", "c3", "c2"],
        },
        "Hybrid": {
            "q1": ["c1", "c2", "c3", "c5", "c4"],
            "q2": ["c2", "c3", "c1", "c4", "c5"],
            "q3": ["c3", "c1", "c2", "c4", "c5"],
        },
        "Hybrid+Rerank": {
            "q1": ["c1", "c3", "c2", "c5", "c4"],
            "q2": ["c3", "c2", "c1", "c5", "c4"],
            "q3": ["c3", "c1", "c2", "c5", "c4"],
        },
    }

    all_results = []
    for mode, results_by_mode in mock_results.items():
        retrieved = [results_by_mode[q.query_id] for q in dataset]
        relevant_sets = dataset.get_relevant_sets()
        relevance_maps = dataset.get_relevance_maps()
        result = compute_all_metrics(mode, retrieved, relevant_sets, relevance_maps)
        all_results.append(result)

    return format_eval_results(*all_results)


async def run_remote(dataset: EvalDataset, base_url: str, kb_id: str) -> str:
    """通过 HTTP API 运行评测。"""
    import httpx

    modes = [
        ("Dense", {"hybrid_search": False, "rerank_enabled": False}),
        ("Hybrid", {"hybrid_search": True, "rerank_enabled": False}),
        ("Hybrid+Rerank", {"hybrid_search": True, "rerank_enabled": True}),
    ]

    all_results = []
    async with httpx.AsyncClient(base_url=base_url, timeout=60) as client:
        for mode_name, extra in modes:
            retrieved_per_query: list[list[str]] = []
            for eq in dataset.queries:
                payload = {
                    "knowledge_base_id": kb_id,
                    "question": eq.query,
                    "top_k": 5,
                    **extra,
                }
                try:
                    resp = await client.post("/api/v1/queries", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    sources = data.get("data", {}).get("sources", [])
                    chunk_ids = [s["chunk_id"] for s in sources]
                    retrieved_per_query.append(chunk_ids)
                except Exception as exc:
                    print(f"[{mode_name}] query {eq.query_id} 失败: {exc}")
                    retrieved_per_query.append([])

            result = compute_all_metrics(
                mode_name,
                retrieved_per_query,
                dataset.get_relevant_sets(),
                dataset.get_relevance_maps(),
            )
            all_results.append(result)

    return format_eval_results(*all_results)


def main():
    parser = argparse.ArgumentParser(description="RAG 检索评测工具")
    parser.add_argument(
        "--remote", type=str, default="", help="远程 API 地址 (如 http://localhost:8000)"
    )
    parser.add_argument("--kb-id", type=str, default="", help="知识库 ID（远程评测时必填）")
    parser.add_argument(
        "--dataset", type=str, default="", help="评测数据集 JSON 文件路径（可选）"
    )
    args = parser.parse_args()

    if args.dataset:
        import json

        with open(args.dataset, encoding="utf-8") as f:
            dataset = json.load(f)
        # TODO: 从 JSON 文件加载
        print("从文件加载数据集尚未实现，使用内置样本集。")

    dataset = SAMPLE_DATASET
    print(f"评测数据集: {dataset.name} (共 {len(dataset)} 条查询)\n")

    if args.remote:
        result = asyncio.run(run_remote(dataset, args.remote, args.kb_id))
    else:
        result = asyncio.run(run_local_baseline(dataset))

    print(result)
    print("\n提示：使用 --remote 参数连接实际服务进行评测。")
    print("示例：python tests/eval/runner.py --remote http://localhost:8000 --kb-id <uuid>")


if __name__ == "__main__":
    main()

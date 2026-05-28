"""评测数据集加载器。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalQuery:
    """评测查询条目。"""

    query_id: str
    query: str
    relevant_chunk_ids: set[str] = field(default_factory=set)
    relevance_scores: dict[str, float] = field(default_factory=dict)
    knowledge_base_id: str = ""


@dataclass
class EvalDataset:
    """评测数据集。"""

    name: str
    queries: list[EvalQuery] = field(default_factory=list)

    def __iter__(self):
        return iter(self.queries)

    def __len__(self) -> int:
        return len(self.queries)

    def get_retrieved_ids(self, per_query_results: list[list[str]]) -> list[list[str]]:
        return per_query_results

    def get_relevant_sets(self) -> list[set[str]]:
        return [q.relevant_chunk_ids for q in self.queries]

    def get_relevance_maps(self) -> list[dict[str, float]]:
        return [q.relevance_scores for q in self.queries]


def load_dataset_from_dict(name: str, data: list[dict]) -> EvalDataset:
    """从字典列表加载评测数据集。

    数据格式：
    [
        {
            "query_id": "q1",
            "query": "什么是 RAG？",
            "relevant_chunk_ids": ["chunk_1", "chunk_3"],
            "relevance_scores": {"chunk_1": 3, "chunk_3": 2},
            "knowledge_base_id": "kb_001"
        },
        ...
    ]
    """
    queries: list[EvalQuery] = []
    for item in data:
        queries.append(
            EvalQuery(
                query_id=item["query_id"],
                query=item["query"],
                relevant_chunk_ids=set(item.get("relevant_chunk_ids", [])),
                relevance_scores=item.get("relevance_scores", {}),
                knowledge_base_id=item.get("knowledge_base_id", ""),
            )
        )
    return EvalDataset(name=name, queries=queries)


# 内置示例评测数据集
SAMPLE_DATASET = EvalDataset(
    name="P2-基础评测集",
    queries=[
        EvalQuery(
            query_id="q1",
            query="什么是 RAG",
            relevant_chunk_ids={"c1"},
            relevance_scores={"c1": 3.0, "c2": 1.0},
        ),
        EvalQuery(
            query_id="q2",
            query="向量数据库的作用",
            relevant_chunk_ids={"c2", "c3"},
            relevance_scores={"c2": 3.0, "c3": 2.0, "c1": 1.0},
        ),
        EvalQuery(
            query_id="q3",
            query="如何提升检索精度",
            relevant_chunk_ids={"c3"},
            relevance_scores={"c3": 3.0, "c1": 1.0},
        ),
    ],
)

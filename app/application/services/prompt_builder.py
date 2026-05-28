"""Prompt 构建器——系统提示词 + 上下文格式化。"""

from app.application.services.retrieval_service import RetrievedChunk

SYSTEM_PROMPT = """你是一个严谨的知识库问答助手。
请只根据给定的上下文回答问题。
如果上下文不足以回答，请明确说明"根据当前知识库资料无法确定"。
回答时尽量简洁，并在关键结论后标注来源编号，例如 [1]、[2]。"""


def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[dict]:
    """构建 LLM 消息列表（system + user）。"""
    context_blocks: list[str] = []
    for i, c in enumerate(chunks):
        page = f"页码：{c.page_number}" if c.page_number else ""
        context_blocks.append(
            f"[{i + 1}] 文件：{c.filename}{'，' + page if page else ''}\n{c.content}"
        )

    context = "\n\n".join(context_blocks)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"问题：{question}\n\n上下文：\n{context}\n\n回答：",
        },
    ]

class RagService:
    """Application-level orchestrator for retrieval + generation."""

    async def query(self, knowledge_base_id: str, question: str) -> dict:
        # Placeholder implementation for scaffold stage.
        return {
            "knowledge_base_id": knowledge_base_id,
            "answer": "Not implemented yet.",
            "sources": [],
            "question": question,
        }

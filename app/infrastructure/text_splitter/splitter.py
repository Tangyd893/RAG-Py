"""层级文本切分器——段落 → 句子 → 字符窗口。"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChunkDraft:
    """切分后的片段草稿。"""
    content: str
    chunk_index: int
    token_count: int
    page_number: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TextSplitter:
    """层级文本切分器：段落 → 句子 → 字符窗口。"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[ChunkDraft]:
        if not text.strip():
            return []

        paragraphs = self._split_paragraphs(text)
        chunks: list[ChunkDraft] = []

        for para in paragraphs:
            if not para.strip():
                continue
            if self._estimate_tokens(para) <= self.chunk_size:
                chunks.append(para)
            else:
                chunks.extend(self._split_long_paragraph(para))

        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        raw = re.split(r"\n\s*\n", text)
        return [p.strip() for p in raw if p.strip()]

    def _split_long_paragraph(self, paragraph: str) -> list[ChunkDraft]:
        sentences = self._split_sentences(paragraph)
        chunks: list[ChunkDraft] = []
        current = ""
        current_tokens = 0

        for sent in sentences:
            sent_tokens = self._estimate_tokens(sent)
            if current_tokens + sent_tokens <= self.chunk_size:
                current = (current + sent) if current else sent
                current_tokens += sent_tokens
            else:
                if current:
                    chunks.append(self._make_draft(current))
                if sent_tokens > self.chunk_size:
                    chunks.extend(self._split_by_window(sent))
                    current = ""
                    current_tokens = 0
                else:
                    current = sent
                    current_tokens = sent_tokens

        if current:
            chunks.append(self._make_draft(current))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        pattern = r"(?<=[。！？\n])(?=[^。！？\n])"
        parts = re.split(pattern, text)
        return [s.strip() for s in parts if s.strip()]

    def _split_by_window(self, text: str) -> list[ChunkDraft]:
        chunks: list[ChunkDraft] = []
        step = self.chunk_size - self.chunk_overlap
        if step <= 0:
            step = self.chunk_size

        pos = 0
        while pos < len(text):
            end = min(pos + self.chunk_size, len(text))
            chunks.append(self._make_draft(text[pos:end]))
            pos += step
        return chunks

    @staticmethod
    def _make_draft(content: str) -> ChunkDraft:
        return ChunkDraft(
            content=content.strip(),
            chunk_index=0,
            token_count=len(content),
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return len(text)

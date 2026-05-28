"""Markdown 文档解析器。"""


class MdParser:
    """将 Markdown 文件字节内容解码为 UTF-8 文本。"""

    async def parse(self, content: bytes, filename: str) -> str:
        return content.decode("utf-8", errors="replace")

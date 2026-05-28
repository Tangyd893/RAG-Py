"""文档解析器协议。"""

from typing import Protocol


class DocumentParser(Protocol):
    """文档解析器抽象接口——将文件字节内容解析为纯文本。"""

    async def parse(self, content: bytes, filename: str) -> str:
        ...

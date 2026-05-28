"""对象存储抽象接口。"""

from typing import Optional, Protocol


class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes) -> str:
        """写入对象，返回存储路径。"""
        ...

    async def get(self, key: str) -> Optional[bytes]:
        """读取对象。"""
        ...

    async def delete(self, key: str) -> None:
        """删除对象。"""
        ...

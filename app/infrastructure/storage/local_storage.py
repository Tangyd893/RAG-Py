"""本地文件存储实现。"""

from pathlib import Path
from typing import Optional


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes) -> str:
        path = self.base_dir / key
        path.write_bytes(data)
        return str(path)

    async def get(self, key: str) -> Optional[bytes]:
        path = self.base_dir / key
        if path.exists():
            return path.read_bytes()
        return None

    async def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            path.unlink()

"""API 集成测试。"""

import uuid

import pytest


class TestHealthAPI:
    """健康检查接口测试。"""

    @pytest.mark.asyncio
    async def test_health_ok(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_readiness(self, client):
        resp = await client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ready"}


class TestKnowledgeBaseAPI:
    """知识库接口测试。"""

    @pytest.mark.asyncio
    async def test_create_kb_requires_name(self, client):
        resp = await client.post("/api/v1/knowledge-bases", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "HTTP_ERROR"

    @pytest.mark.asyncio
    async def test_create_kb_invalid_chunk_size(self, client):
        resp = await client.post(
            "/api/v1/knowledge-bases",
            json={"name": "测试", "chunk_size": 100},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "HTTP_ERROR"


class TestDocumentAPI:
    """文档接口测试。"""

    KB_ID = str(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_upload_without_kb_fails(self, client):
        resp = await client.post(
            f"/api/v1/knowledge-bases/{self.KB_ID}/documents",
        )
        assert resp.status_code == 422


class TestQueryAPI:
    """查询接口测试。"""

    KB_ID = str(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_query_requires_body(self, client):
        resp = await client.post("/api/v1/queries")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_query_missing_required_fields(self, client):
        resp = await client.post(
            "/api/v1/queries", json={"knowledge_base_id": self.KB_ID}
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["error"]["code"] == "HTTP_ERROR"


class TestErrorHandling:
    """异常处理测试。"""

    @pytest.mark.asyncio
    async def test_nonexistent_route_returns_404_response(self, client):
        resp = await client.get("/api/v1/nonexistent")
        assert resp.status_code == 200
        body = resp.json()
        assert body["error"] is not None
        assert "request_id" in body

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, client):
        resp = await client.get("/api/v1/knowledge-bases/not-a-uuid")
        assert resp.status_code == 422


class TestResponseStructure:
    """ApiResponse 统一格式验证。"""

    @pytest.mark.asyncio
    async def test_health_response_has_request_id(self, client):
        resp = await client.get("/api/v1/health")
        assert "status" in resp.json()
        assert resp.headers.get("x-request-id") is not None

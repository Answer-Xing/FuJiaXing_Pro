"""健康检查接口测试"""
class TestHealth:
    """测试 /health 系列接口"""

    def test_root_returns_info(self, client):
        """GET / —— 返回服务信息"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "health" in data

    def test_liveness(self, client):
        """GET /health/live —— 返回 alive"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness(self, client, mock_llm_client):
        """GET /health/ready —— 有可用模型时返回 ready"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    def test_health_returns_models_count(self, client, mock_llm_client):
        """GET /health —— 返回模型数量"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "models_available" in data
        assert "uptime_seconds" in data
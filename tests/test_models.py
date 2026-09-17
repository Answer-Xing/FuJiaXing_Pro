"""模型列表接口测试"""
class TestModels:
    """测试 GET /models 接口"""

    def test_list_models(self, client, mock_llm_client):
        """GET /models —— 返回模型列表"""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert len(data["models"]) > 0
        assert "total" in data
        assert data["total"] == len(data["models"])

        # 检查模型信息完整性
        model = data["models"][0]
        assert "id" in model
        assert "name" in model
        assert "provider" in model
        assert "description" in model
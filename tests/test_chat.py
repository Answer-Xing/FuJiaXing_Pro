"""聊天接口测试"""
class TestChat:
    """测试 /chat 和 /chat/stream 接口"""

    def test_chat_returns_response(self, client, sample_chat_request, mock_llm_client):
        """POST /chat —— 返回正确的聊天响应"""
        response = client.post("/chat", json=sample_chat_request)
        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["model"] == "deepseek-chat"
        assert "content" in data
        assert "usage" in data
        assert "total_tokens" in data["usage"]

    def test_chat_rejects_empty_messages(self, client):
        """POST /chat —— 空消息列表返回 422"""
        response = client.post("/chat", json={
            "model": "deepseek",
            "messages": [],
        })
        assert response.status_code == 422  # Pydantic 校验失败

    def test_chat_rejects_invalid_model(self, client):
        """POST /chat —— 无效模型名返回 400"""
        response = client.post("/chat", json={
            "model": "nonexistent-model",
            "messages": [{"role": "user", "content": "Hello"}],
        })
        assert response.status_code == 400

    def test_chat_rejects_invalid_temperature(self, client):
        """POST /chat —— temperature 超出范围返回 422"""
        response = client.post("/chat", json={
            "model": "deepseek",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 99.0,  # 超出 0-2 范围
        })
        assert response.status_code == 422

    def test_chat_stream_returns_sse(self, client, sample_chat_request, mock_llm_client):
        """POST /chat/stream —— 返回 SSE 格式的流式数据"""
        response = client.post("/chat/stream", json=sample_chat_request)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # 检查 SSE 格式
        content = response.text
        assert "data: " in content
        # 流式数据应该包含 token
        assert "token" in content
        # 应该有结束标记
        assert "[DONE]" in content

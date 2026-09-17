"""pytest 共享配置和 fixtures"""
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app


@pytest.fixture
def client():
    """创建测试用的 FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def sample_chat_request():
    """测试用的聊天请求数据"""
    return {
        "model": "deepseek",
        "messages": [
            {"role": "system", "content": "你是助手"},
            {"role": "user", "content": "你好"},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }


@pytest.fixture
def mock_llm_response():
    """模拟 LLM 返回的数据"""
    return {
        "content": "你好！有什么可以帮助你的？",
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 10,
            "total_tokens": 25,
        },
        "model": "deepseek-chat",
    }


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """模拟 LLMClient，避免测试时真的调用外部 API"""
    with patch("app.routers.chat.get_llm_client") as mock_get:
        mock_instance = Mock()
        mock_instance.chat.return_value = mock_llm_response
        mock_instance.get_available_models.return_value = [
            {"id": "deepseek", "name": "DeepSeek-V3", "provider": "DeepSeek", "description": "测试用"}
        ]
        # 流式——返回一个 Token 生成器
        mock_instance.chat_stream.return_value = iter(["你", "好", "！"])
        mock_get.return_value = mock_instance
        yield mock_instance
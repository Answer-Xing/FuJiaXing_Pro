"""LLM 调用客户端——统一封装多模型调用逻辑"""
from openai import OpenAI
from app.config import get_settings
import structlog

logger = structlog.get_logger()


class LLMClientError(Exception):
    """LLM 调用异常"""
    pass


class ModelNotFoundError(LLMClientError):
    """模型未配置"""
    pass


class LLMClient:
    """统一的 LLM 调用客户端

    支持:
    - 多模型切换（DeepSeek / OpenAI）
    - 普通调用 + 流式调用
    - 自动 Token 统计
    - 错误处理和重试
    """

    def __init__(self):
        self.settings = get_settings()
        # 创建各个 Provider 的客户端
        self._clients: dict[str, OpenAI] = {}

        if self.settings.deepseek_api_key:
            self._clients["deepseek"] = OpenAI(
                api_key=self.settings.deepseek_api_key,
                base_url=self.settings.deepseek_base_url,
            )

        if self.settings.openai_api_key:
            self._clients["openai"] = OpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
            )

        if not self._clients:
            raise LLMClientError(
                "未配置任何 LLM API Key。请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY"
            )

        logger.info(
            "llm_client.initialized",
            models=list(self._clients.keys()),
        )

    def get_client(self, model_id: str) -> tuple[OpenAI, str]:
        """根据 model_id 获取对应的客户端和实际模型名"""
        if model_id not in self._clients:
            raise ModelNotFoundError(
                f"模型 '{model_id}' 未配置。可用模型: {list(self._clients.keys())}"
            )

        client = self._clients[model_id]
        # 获取实际要传给 API 的模型名
        model_name = (
            self.settings.deepseek_model if model_id == "deepseek"
            else self.settings.openai_model
        )
        return client, model_name

    def chat(self, request) -> dict:
        """普通（非流式）聊天——一次调用返回完整结果"""
        client, model_name = self.get_client(request.model)

        # 把 Pydantic 模型转为 API 需要的 messages 格式
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        logger.info(
            "llm_client.chat.start",
            model=request.model,
            model_name=model_name,
            message_count=len(messages),
            temperature=request.temperature,
        )

        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            logger.info(
                "llm_client.chat.success",
                model=request.model,
                prompt_tokens=resp.usage.prompt_tokens,
                completion_tokens=resp.usage.completion_tokens,
            )

            return {
                "content": resp.choices[0].message.content,
                "usage": {
                    "prompt_tokens": resp.usage.prompt_tokens,
                    "completion_tokens": resp.usage.completion_tokens,
                    "total_tokens": resp.usage.total_tokens,
                },
                "model": model_name,
            }

        except Exception as e:
            logger.error(
                "llm_client.chat.failed",
                model=request.model,
                error=str(e),
            )
            raise LLMClientError(f"调用 LLM 失败 ({request.model}): {e}")

    def chat_stream(self, request):
        """流式聊天——逐 Token 返回（生成器）"""
        client, model_name = self.get_client(request.model)

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        logger.info(
            "llm_client.chat_stream.start",
            model=request.model,
        )

        try:
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,  # ← 关键参数！
            )

            total_content = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    total_content += delta
                    yield delta  # 逐 Token 产出

            logger.info(
                "llm_client.chat_stream.success",
                model=request.model,
                total_length=len(total_content),
            )

        except Exception as e:
            logger.error(
                "llm_client.chat_stream.failed",
                model=request.model,
                error=str(e),
            )
            raise LLMClientError(f"流式调用失败 ({request.model}): {e}")

    def get_available_models(self) -> list[dict]:
        """返回当前可用的模型列表"""
        return self.settings.available_models


# ===== 全局单例 =====
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取 LLM Client 的单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

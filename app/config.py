"""应用配置——所有环境相关的变量都在这里"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)


# ============================================================
# 项目根目录
#
# 假设当前文件：
# ~/ai-chat-api/app/config.py
#
# 那么 PROJECT_ROOT：
# ~/ai-chat-api
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """应用配置类"""

    # ===== 应用基础 =====
    app_name: str = "AI Chat API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # ===== 服务器 =====
    host: str = "0.0.0.0"
    port: int = 8000

    # ===== DeepSeek 配置 =====
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    # ===== OpenAI 配置 =====
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.6-luna"

    # ===== 服务限制 =====
    max_tokens_default: int = 4096
    request_timeout: int = 60

    # ============================================================
    # Pydantic Settings 配置
    # ============================================================
    model_config = SettingsConfigDict(
        # 使用绝对路径，避免切换目录后读取错 .env
        env_file=ENV_FILE,
        env_file_encoding="utf-8",

        # DEEPSEEK_API_KEY 可以映射 deepseek_api_key
        case_sensitive=False,

        # 忽略 .env 中未声明字段
        extra="ignore",
    )

    # ============================================================
    # 修改配置读取优先级
    #
    # 默认：
    # 系统环境变量 > .env
    #
    # 我们修改成：
    # .env > 系统环境变量
    #
    # 这样即使 Linux / PyCharm / shell 中还残留旧 Key，
    # 当前项目自己的 .env 也优先。
    # ============================================================
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:

        return (
            init_settings,
            dotenv_settings,      # .env 优先
            env_settings,         # 系统环境变量其次
            file_secret_settings,
        )

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"

    @property
    def available_models(self) -> list[dict]:
        """返回当前已配置的可用模型列表"""

        models = []

        if self.deepseek_api_key:
            models.append(
                {
                    "id": "deepseek",
                    "name": "DeepSeek-V4-flash",
                    "provider": "DeepSeek",
                    "description": "高性价比通用模型，中文能力强",
                }
            )

        if self.openai_api_key:
            models.append(
                {
                    "id": "openai",
                    "name": self.openai_model,
                    "provider": "OpenAI",
                    "description": "OpenAI 大语言模型",
                }
            )

        return models


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置单例"""

    settings = Settings()

    # 只打印后四位，方便确认实际读取的是哪个 Key
    if settings.deepseek_api_key:
        print(
            f"[CONFIG] .env={ENV_FILE} "
            f"DeepSeek Key=****{settings.deepseek_api_key[-4:]}"
        )
    else:
        print(
            f"[CONFIG] .env={ENV_FILE} "
            f"DeepSeek Key=NOT_CONFIGURED"
        )

    return settings
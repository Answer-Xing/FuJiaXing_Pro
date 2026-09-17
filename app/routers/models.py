from fastapi import APIRouter

from app.models.schemas import ModelInfo, ModelListResponse
from app.services.llm_client import get_llm_client

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=ModelListResponse)
async def list_models():
    """列出当前可用的模型

    返回所有已配置了 API Key 的模型。
    至少需要配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 中的一个。
    """
    llm = get_llm_client()
    available = llm.get_available_models()

    models = [
        ModelInfo(
            id=m["id"],
            name=m["name"],
            provider=m["provider"],
            description=m["description"],
        )
        for m in available
    ]

    return ModelListResponse(
        models=models,
        default=models[0].id if models else "none",
        total=len(models),
    )
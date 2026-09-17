"""健康检查路由"""
import time
from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.config import get_settings
from app.services.llm_client import get_llm_client

router = APIRouter(tags=["Health"])

# 记录服务启动时间
START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查——返回服务状态和基本信息

    K8s / Docker Compose 用这个接口判断服务是否正常。
    """
    settings = get_settings()
    llm = get_llm_client()
    models = llm.get_available_models()

    return HealthResponse(
        status="healthy" if models else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        models_available=len(models),
        uptime_seconds=int(time.time() - START_TIME),
    )


@router.get("/health/live")
async def liveness():
    """Liveness 检查——服务进程是否存活"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    """Readiness 检查——服务是否准备好接收请求"""
    llm = get_llm_client()
    models = llm.get_available_models()

    if not models:
        return {"status": "not_ready", "reason": "没有可用的模型"}
    return {"status": "ready", "models": len(models)}
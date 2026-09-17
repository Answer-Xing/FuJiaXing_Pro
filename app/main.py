"""AI Chat API —— FastAPI 入口文件"""
import uuid
import sys
from pathlib import Path
from pathlib import Path

from fastapi.responses import FileResponse

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import get_settings
from app.core.logging_config import setup_logging
from app.routers import chat, models, health
from app.services.llm_client import get_llm_client

# ─── 初始化和配置 ───

settings = get_settings()

# 配置日志
setup_logging(
    level=settings.log_level,
    is_development=settings.is_development,
)
logger = structlog.get_logger()

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="个人 AI 聊天 API 服务——支持 DeepSeek 和 OpenAI 多模型切换",
    # 生产环境关闭文档
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)


# ─── 中间件 ───

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """给每个请求添加唯一 ID，贯穿所有日志"""
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:8])
    structlog.contextvars.bind_contextvars(request_id=request_id)

    logger.info(
        "request.received",
        method=request.method,
        path=request.url.path,
    )

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.middleware("http")
async def log_response_time(request: Request, call_next):
    """记录每个请求的处理时间"""
    import time
    start = time.time()
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(
        "request.completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        elapsed_ms=int(elapsed * 1000),
    )
    return response


@app.get("/test_chat.html", include_in_schema=False)
async def demo_page():
    html_path = Path(__file__).parent / "test_chat.html"
    return FileResponse(html_path)


# CORS——允许前端跨域访问
if settings.is_development:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ─── 挂载路由 ───
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(health.router)


# ─── 启动和关闭事件 ───

@app.on_event("startup")
async def startup():
    """服务启动时的初始化工作"""
    logger.info(
        "app.startup",
        environment=settings.environment,
        version=settings.app_version,
    )

    # 初始化 LLM Client（提前发现配置错误）
    try:
        llm = get_llm_client()
        available = llm.get_available_models()
        logger.info(
            "app.models_ready",
            models=[m["id"] for m in available],
        )
    except Exception as e:
        logger.error("app.startup_failed", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown():
    """服务关闭时的清理工作"""
    logger.info("app.shutdown")


# ─── 全局异常处理 ───

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """捕获所有未处理的异常，返回统一的错误格式"""
    logger.error(
        "app.unhandled_error",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试",
        },
    )


# ─── 根路径 ───

@app.get("/")
async def root():
    """根路径——返回服务信息"""
    llm = get_llm_client()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "models_available": len(llm.get_available_models()),
        "docs": "/docs" if settings.is_development else "disabled",
        "health": "/health",
    }

"""聊天相关路由"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import uuid

from app.models.schemas import ChatRequest, ChatResponse, ChatError
from app.services.llm_client import (
    get_llm_client,
    LLMClientError,
    ModelNotFoundError,
)
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """普通聊天接口——一次返回完整结果

    请求示例:
    ```json
    {
      "model": "deepseek",
      "messages": [
        {"role": "system", "content": "你是 Python 助手"},
        {"role": "user", "content": "写一个快排"}
      ],
      "temperature": 0.7
    }
    ```
    """
    if request.stream:
        # 如果客户端传了 stream=true 但走了普通接口
        # → 引导他们用 /chat/stream
        raise HTTPException(
            status_code=400,
            detail="流式请求请使用 POST /chat/stream 接口",
        )

    try:
        llm = get_llm_client()
        result = llm.chat(request)

        return ChatResponse(
            id=f"chat-{uuid.uuid4().hex[:8]}",
            model=result["model"],
            content=result["content"],
            usage=result["usage"],
        )

    except ModelNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error("chat.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口——通过 SSE 逐 Token 推送

    响应格式: Server-Sent Events
    每条事件格式: data: {"token": "Hello", "model": "deepseek-chat"}\\n\\n

    最终事件:       data: [DONE]\\n\\n

    前端使用示例:
    ```javascript
    const response = await fetch('/chat/stream', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model:'deepseek', messages:[{role:'user',content:'Hello'}]})
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      // text 格式: "data: {"token":"hello"}\\n\\n"
      console.log(text);
    }
    ```
    """
    # 强制 stream 模式（忽略请求体中的 stream 字段）
    request.stream = True

    try:
        llm = get_llm_client()
        token_stream = llm.chat_stream(request)

        async def sse_generator():
            """SSE 事件生成器——把 Token 流包装成 SSE 格式"""
            # 第一条事件：元信息
            import json
            yield f"data: {json.dumps({'model': request.model, 'status': 'started'})}\n\n"

            token_count = 0
            try:
                for token in token_stream:
                    token_count += 1
                    # 每条 SSE 事件 = "data: <json>\n\n"
                    event_data = json.dumps({
                        "token": token,
                        "index": token_count,
                    })
                    yield f"data: {event_data}\n\n"

            except Exception as e:
                # 流中出错 → 发送错误事件
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"

            # 结束标记
            yield "data: [DONE]\n\n"

            logger.info(
                "chat_stream.completed",
                token_count=token_count,
                model=request.model,
            )

        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
            },
        )

    except ModelNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error("chat_stream.unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")
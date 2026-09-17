# AI Chat API 服务架构说明

## 1. 项目概述

AI Chat API 是一个基于 FastAPI 构建的大模型统一调用服务，对外提供标准化的聊天接口，并支持多模型接入、流式响应、模型列表查询以及服务健康检查。

当前计划支持：

- DeepSeek
- OpenAI
- 后续可继续扩展其他大模型服务

同时支持通过 Docker Compose 进行一键部署，并可按需集成 Redis 缓存。

## 2. 整体架构

```text
用户
 │
 │ POST /chat
 │
 │ {
 │   "model": "deepseek",
 │   "messages": [...]
 │ }
 │
 ▼

┌──────────────────────────────────┐
│          AI Chat API 服务        ｜
│                                  │
│  /chat                           │
│     └── 调用 LLM，返回普通响应   ｜
│                                  │
│  /chat/stream                    │
│     └── 流式 SSE 响应            ｜
│                                  │
│  /models                         │
│     └── 查询当前可用模型列表     ｜
│                                  │
│  /health                         │
│     └── 服务健康检查             ｜
│                                  │
│  ┌────────────┐  ┌────────────┐  │
│  │ DeepSeek   │  │ OpenAI     │  │
│  │ V3         │  │ GPT-4o     │  │
│  └────────────┘  └────────────┘  │
│                                  │
│          支持多模型统一调用      ｜
└──────────────────────────────────┘

                  │
                  ▼

        Docker Compose 一键部署

        ┌──────────────────┐
        │ FastAPI API 服务  │
        ├──────────────────┤
        │ Redis（可选）      │
        └──────────────────┘
```

## 3. 请求流程

```text
用户发送请求
      │
      ▼
POST /chat
      │
      ▼
解析请求参数
      │
      ├── model
      └── messages
      │
      ▼
根据 model 选择对应 LLM
      │
      ├── DeepSeek
      └── OpenAI
      │
      ▼
调用模型 API
      │
      ▼
获取模型响应
      │
      ▼
统一封装响应结果
      │
      ▼
返回给用户
```

## 4. 核心接口

### 4.1 普通聊天接口

```http
POST /chat
```

用于普通非流式大模型对话。

请求示例：

```json
{
  "model": "deepseek",
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下 FastAPI"
    }
  ]
}
```

### 4.2 流式聊天接口

```http
POST /chat/stream
```

用于流式返回大模型生成结果。

响应方式：

```text
Server-Sent Events
SSE
```

### 4.3 模型列表接口

```http
GET /models
```

用于查询当前系统支持的大模型。

示例响应：

```json
{
  "models": [
    {
      "id": "deepseek",
      "name": "DeepSeek V3"
    },
    {
      "id": "openai",
      "name": "OpenAI GPT-4o"
    }
  ]
}
```

### 4.4 健康检查接口

```http
GET /health
```

用于检查 AI Chat API 服务是否正常运行。

示例响应：

```json
{
  "status": "ok"
}
```

## 5. 多模型调用架构

系统采用统一 LLM Client 层封装不同模型服务。

```text
                  Chat Router
                      │
                      ▼
               LLM Client Layer
                      │
           ┌──────────┴──────────┐
           │                     │
           ▼                     ▼
    DeepSeek Client         OpenAI Client
           │                     │
           ▼                     ▼
     DeepSeek API            OpenAI API
```

## 6. 服务职责划分

```text
Router
  │
  ├── 接收 HTTP 请求
  ├── 参数校验
  └── 返回 HTTP 响应
        │
        ▼
Service
  │
  ├── 模型选择
  ├── 业务逻辑
  └── LLM 调用
        │
        ▼
LLM Client
  │
  ├── DeepSeek
  └── OpenAI
        │
        ▼
第三方大模型 API
```

## 7. Docker 部署架构

项目支持使用 Docker Compose 进行部署。

```text
Docker Compose
      │
      ├── ai-chat-api
      │      │
      │      └── FastAPI
      │
      └── redis
             │
             └── 可选缓存服务
```

## 8. Redis 可选能力

Redis 可以作为后续扩展能力使用。

典型用途：

```text
Redis
 │
 ├── 对话缓存
 ├── 模型响应缓存
 ├── Session 状态
 ├── Conversation Context
 ├── 限流计数
 └── 请求幂等控制
```

## 9. 项目目录结构

```text
ai-chat-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── models.py
│   │   └── health.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm_client.py
│   │
│   └── core/
│       ├── __init__.py
│       └── logging_config.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_chat.py
│   └── test_models.py
│
├── .env.example
├── .env
├── .gitignore
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 10. 模块职责

| 模块 | 职责 |
|---|---|
| `main.py` | FastAPI 应用入口、注册路由、中间件 |
| `config.py` | 环境变量和系统配置管理 |
| `models/schemas.py` | Pydantic 请求和响应模型 |
| `routers/chat.py` | `/chat`、`/chat/stream` 接口 |
| `routers/models.py` | `/models` 接口 |
| `routers/health.py` | `/health` 健康检查 |
| `services/llm_client.py` | 统一封装不同大模型调用 |
| `core/logging_config.py` | 系统日志配置 |
| `tests/` | 接口及业务自动化测试 |
| `.env` | 本地实际环境变量 |
| `.env.example` | 环境变量模板 |
| `Dockerfile` | AI Chat API 镜像构建 |
| `docker-compose.yml` | API、Redis 等服务编排 |

## 11. 当前核心能力

```text
AI Chat API
│
├── 普通对话
│   └── POST /chat
│
├── 流式对话
│   └── POST /chat/stream
│
├── 模型管理
│   └── GET /models
│
├── 健康检查
│   └── GET /health
│
├── 多模型支持
│   ├── DeepSeek V3
│   └── OpenAI GPT-4o
│
└── 部署
    ├── Docker
    ├── Docker Compose
    └── Redis（可选）
```

## 12. 后续扩展方向

```text
AI Chat API
    │
    ├── 多轮对话
    ├── Conversation ID
    ├── Redis Memory
    ├── Token Usage
    ├── 模型调用耗时
    ├── 模型降级
    ├── Retry
    ├── Timeout
    ├── Rate Limit
    ├── Function Calling
    ├── Tool Calling
    ├── MCP
    ├── RAG
    └── Agent
```

最终可以逐步演进为：

```text
统一 LLM Gateway
        +
Chat API
        +
Agent Runtime
        +
RAG
        +
Tool Calling
        +
MCP
```

使用方式：

```text
启动服务端：uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
接口文档查看：http://62.234.81.102:8000/docs
前端可视化展示：http://62.234.81.102:8000/test_chat.html
```

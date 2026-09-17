AI Chat API 项目 README
AI Chat API
基于 FastAPI 构建的大模型统一调用网关服务，提供标准化的通用对话接口，支持多模型接入、流式响应、模型列表查询、服务健康检查等核心能力。项目支持 Docker / Docker Compose 一键部署，可按需集成 Redis 实现缓存、限流、会话管理等扩展能力，可快速迭代为企业级 LLM Gateway 服务。
✨ 项目特性
- 多模型统一适配：内置 DeepSeek V3、OpenAI GPT-4o 模型客户端，统一请求/响应范式，极简扩展新模型
- 双模式对话能力：支持普通同步对话 + SSE 流式对话，适配前端实时输出场景
- 标准化接口体系：提供聊天、模型查询、服务健康检查三类核心接口，规范统一、开箱即用
- 容器化一键部署：支持 Docker Compose 快速部署，适配服务器、云平台等多环境
- 可扩展缓存架构：可选集成 Redis，支持对话缓存、限流、会话状态、请求幂等等能力
- 模块化分层设计：路由层、业务服务层、模型客户端层解耦，代码结构清晰，易维护、易扩展
🏗️ 整体架构
项目采用分层架构设计，通过统一客户端层屏蔽各大模型 API 差异，对外提供统一标准化服务。
用户请求
   │
   ▼
HTTP 路由层（Router）—— 参数校验、请求接收、响应返回
   │
   ▼
业务服务层（Service）—— 模型路由、业务逻辑调度
   │
   ▼
LLM 客户端层（Client）—— 统一封装各厂商模型接口
   ├─ DeepSeek Client
   └─ OpenAI Client
   │
   ▼
第三方大模型 API 服务
服务部署架构：FastAPI 主服务 + 可选 Redis 缓存服务，通过 Docker Compose 统一编排管理。
📡 核心接口文档
1. 普通对话接口（同步）
- 请求方式：POST
- 接口地址：/chat
- 功能描述：发起非流式大模型对话，一次性返回完整响应结果
请求示例：
{
  "model": "deepseek",
  "messages": [
    {
      "role": "user",
      "content": "你好，请介绍一下 FastAPI"
    }
  ]
}
2. 流式对话接口
- 请求方式：POST
- 接口地址：/chat/stream
- 功能描述：基于 SSE 协议实现流式输出，逐字返回大模型生成内容
- 响应类型：Server-Sent Events (SSE)
3. 模型列表查询接口
- 请求方式：GET
- 接口地址：/models
- 功能描述：查询当前服务支持的所有大模型列表
响应示例：
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
4. 服务健康检查接口
- 请求方式：GET
- 接口地址：/health
- 功能描述：检测 API 服务运行状态，用于服务监控、保活检测
响应示例：
{
  "status": "ok"
}
📁 项目目录结构
ai-chat-api/
├── app/                    # 项目核心业务目录
│   ├── main.py             # FastAPI 入口、路由注册、中间件配置
│   ├── config.py           # 全局环境变量、配置管理
│   ├── models/             # 数据模型层
│   │   └── schemas.py      # Pydantic 请求/响应参数模型
│   ├── routers/            # 路由接口层
│   │   ├── chat.py         # 对话相关接口
│   │   ├── models.py       # 模型列表接口
│   │   └── health.py       # 健康检查接口
│   ├── services/           # 业务服务层
│   │   └── llm_client.py   # 大模型统一调用客户端
│   └── core/               # 核心工具配置
│       └── logging_config.py # 日志全局配置
├── tests/                  # 自动化测试用例
├── .env                    # 本地真实环境变量（不提交仓库）
├── .env.example            # 环境变量模板（仅占位，无真实密钥）
├── .gitignore              # Git 忽略文件配置
├── requirements.txt        # 项目依赖清单
├── Dockerfile              # 服务镜像构建配置
└── docker-compose.yml      # 容器服务编排配置
⚙️ 模块职责说明
模块文件
核心职责
main.py
FastAPI 应用初始化、路由注册、全局中间件配置、服务入口
config.py
统一读取并管理环境变量、模型密钥、服务端口等全局配置
schemas.py
定义请求、响应数据结构，完成参数校验、数据格式化
routers/ 系列
接收 HTTP 请求、参数校验、调用业务服务、返回标准化响应
llm_client.py
封装 DeepSeek、OpenAI 模型调用逻辑，屏蔽厂商接口差异
logging_config.py
统一日志格式、日志级别、日志输出规则配置
🚀 快速启动
1. 本地开发启动
1）安装依赖
pip install -r requirements.txt
2）配置环境变量
复制 .env.example为 .env，填入自己的模型 API 密钥（严禁提交真实密钥到仓库）
3）启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
2. 容器化部署
通过 Docker Compose 一键部署 FastAPI 服务 + 可选 Redis 缓存服务
docker-compose up -d
3. 服务访问地址
- 接口文档：http://localhost:8000/docs
- 前端可视化聊天页面：http://localhost:8000/test_chat.html
💾 Redis 扩展能力
项目支持可选集成 Redis，可实现后续多项核心扩展能力：
- 对话上下文缓存、模型响应结果缓存
- Session 会话状态持久化、对话上下文管理
- 接口限流、请求计数、防刷控制
- 请求幂等性校验，避免重复请求
📈 后续迭代规划
项目可逐步迭代为企业级 LLM 统一网关平台，后续扩展方向：
- 多轮对话、Conversation ID 会话管理
- Token 用量统计、模型调用耗时监控
- 模型降级、重试、超时容错机制
- 接口限流、频率控制
- Function Calling、Tool Calling 工具调用
- RAG 知识库检索、Agent 智能体能力、MCP 协议适配
⚠️ 安全规范
- 禁止提交真实密钥：.env 文件已配置在.gitignore 中，仅使用 .env.example 作为模板
- 密钥泄露处理：若 API 密钥不慎提交，需立即在模型后台撤销旧密钥、生成新密钥，并清理 Git 历史记录
- 生产环境关闭热更新、配置日志持久化、开启接口鉴权
📄 许可证
本项目为开源学习项目，可自由学习、二次开发，禁止用于违规商业用途。

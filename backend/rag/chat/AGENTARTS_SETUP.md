# AgentArts 维修知识问答智能体搭建指南

> 本指南说明如何在华为云 AgentArts 控制台手动创建维修知识问答智能体，并接入本项目已完成的 RAG 检索工具。

## 前置条件

1. 已有华为云账号并能访问 AgentArts 控制台。
2. 本项目后端已部署且公网可达，RAG Tool 接口 `POST /api/rag-tool/search` 可被 AgentArts 调用。
3. 已配置环境变量 `RAG_TOOL_API_KEY`（后端启动时注入），AgentArts 调用工具时需携带 `X-API-Key`。

## 一、生成 RAG Tool 鉴权 Key

在后端服务器执行（PowerShell）：

```powershell
# 生成一个随机 Key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

把输出值设置为后端环境变量 `RAG_TOOL_API_KEY`，并记录下来，后续 AgentArts 工具配置要用：

```powershell
$env:RAG_TOOL_API_KEY = "上一步生成的值"
python -B main.py
```

验证工具健康检查：

```powershell
$headers = @{ "X-API-Key" = "上一步生成的值" }
Invoke-RestMethod -Uri "http://<后端公网地址>:8000/api/rag-tool/health" -Headers $headers
```

应返回 `status=ready`。

## 二、在 AgentArts 创建智能体

### 2.1 进入控制台

1. 登录华为云控制台，搜索并进入 **AgentArts** 服务。
2. 在智能体管理页面，点击 **创建智能体**。

### 2.2 基本信息

| 配置项 | 值 |
|---|---|
| 智能体名称 | 航枢维修知识问答智能体 |
| 智能体描述 | 航空发动机维修知识问答，基于本地维修手册检索证据生成处置建议 |
| 智能体类型 | 对话型智能体 |

### 2.3 大模型配置

| 配置项 | 推荐值 |
|---|---|
| 模型来源 | 华为云盘古大模型（首选）或接入 DeepSeek / OpenAI 兼容端点 |
| 模型 | 按平台可选模型选择，建议选对话能力较强的版本 |
| 温度（temperature） | 0.3 |
| 最大输出 tokens | 800 |
| Top P | 0.9 |

### 2.4 系统提示词

把 `backend/rag/chat/agentarts_system_prompt.txt` 的完整内容粘贴到智能体的 **系统提示词**（System Prompt）输入框。

### 2.5 注册自定义工具（关键步骤）

在智能体的 **工具管理 / 插件** 区域，新增一个 **自定义工具（HTTP 调用）**：

| 配置项 | 值 |
|---|---|
| 工具名称 | `maintenance_knowledge_retriever` |
| 工具描述 | 检索航空发动机维修知识库，返回带来源、分数和内容哈希的只读证据片段 |
| 调用方式 | HTTP POST |
| 请求 URL | `http://<后端公网地址>:8000/api/rag-tool/search` |
| 请求头 | `Content-Type: application/json` 和 `X-API-Key: <第一步生成的 RAG_TOOL_API_KEY>` |
| 工具参数 Schema | 导入 `backend/rag/chat/agentarts_tool_schema.json` 文件内容 |

**工具参数 Schema** 直接把 `agentarts_tool_schema.json` 的 JSON 内容粘贴到工具的 parameters 配置框。

### 2.6 测试工具调用

在 AgentArts 工具测试界面，输入测试参数：

```json
{
  "query": "动力涡轮振动持续升高需要检查哪些部件",
  "top_k": 4,
  "min_score": 0.05
}
```

应返回 `documents` 数组，其中包含 `engine_vibration.md` 的内容片段。

### 2.7 测试智能体对话

在 AgentArts 智能体调试界面，输入测试问题：

| 测试问题 | 期望行为 |
|---|---|
| 发动机振动持续升高需要检查哪些部件？ | 调用工具，命中 `engine_vibration.md`，回答带来源 |
| 液压系统压力下降疑似泄漏怎么处置？ | 调用工具，命中 `hydraulic_leak.md` |
| 发动机燃烧室第三方改装方案推荐 | 工具无匹配，智能体不编造，说明依据不足 |
| 发动机振动异常现在能否继续放行？ | 回答含"应由有资质维修人员复核"安全提示 |
| 今天天气怎么样？ | 礼貌说明只回答维修相关问题 |

## 三、发布智能体 API

1. 在智能体详情页，点击 **发布** 或 **部署**。
2. 选择 **API 调用** 方式发布。
3. 发布后获得：
   - **智能体 API 端点 URL**：类似 `https://<agentarts-domain>/v1/agents/<agent_id>/completions`
   - **智能体 API Key**：`AGENTARTS_API_KEY`

记录这两个值，后续配置后端代理层要用。

## 四、配置后端代理层环境变量

在后端服务器配置以下环境变量（PowerShell）：

```powershell
$env:AGENTARTS_API_URL = "https://<agentarts-domain>/v1/agents/<agent_id>/completions"
$env:AGENTARTS_API_KEY = "<智能体 API Key>"
$env:RAG_TOOL_API_KEY = "<第一步生成的值，保持不变>"
python -B main.py
```

后端启动后，前端调用 `POST /api/rag-chat` 即可使用智能体。

## 五、验证联调

```powershell
# 测试后端代理层
$body = @{ message = "发动机振动持续升高需要检查哪些部件？" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/rag-chat" -Method POST -Body $body -ContentType "application/json"
```

应返回：

```json
{
  "session_id": "chat-xxxx",
  "answer": "智能体生成的回答...",
  "sources": [{"source": "knowledge_base/engine_manual/engine_vibration.md", ...}],
  "status": "success",
  "llm": "agentarts",
  "warnings": []
}
```

## 六、安全注意事项

1. `AGENTARTS_API_KEY` 和 `RAG_TOOL_API_KEY` 不得提交到 Git，不得写入日志。
2. 生产环境通过密钥管理系统或环境变量注入，不硬编码。
3. AgentArts 调用后端 RAG Tool 时，确保后端公网地址使用 HTTPS。
4. 在网关层配置限流和审计存储。
5. RAG Tool 的 `X-API-Key` 只保护 `/api/rag-tool/*`，不影响前端其他接口。
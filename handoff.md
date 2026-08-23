# 维修知识问答智能体调用 RAG Tool 交接文档

> 更新时间：2026-08-11
> 交接对象：维修知识问答智能体开发者
> Tool 名称：`maintenance_knowledge_retriever`
> Tool 版本：`1.0.0`

## 1. 先明确双方职责

RAG Tool 已经开发完成，代码位于 `backend/rag/`。你不需要重新实现知识切片、索引、检索、输入校验和引用追踪。

双方职责如下：

| 模块 | 负责人 | 职责 |
|---|---|---|
| RAG Tool | 已完成 | 接收检索问题，返回相关知识片段、来源、哈希、分数和知识库版本 |
| 维修知识问答智能体 | 你 | 判断何时调用 Tool、构造查询、读取证据、生成回答、展示引用和处理无结果情况 |

这个 Tool 只负责“检索证据”，不会代替你的智能体生成最终回答，也不会给出具有法律效力的适航放行结论。

## 2. Tool 在哪里

核心文件：

| 路径 | 作用 |
|---|---|
| `backend/rag/tool.py` | Tool 对外入口、请求与响应模型、日志、健康检查 |
| `backend/rag/retriever.py` | TF-IDF 稀疏向量余弦检索 |
| `backend/rag/build_index.py` | Markdown 切片、内容哈希和本地 JSON 索引 |
| `backend/rag/knowledge_base/` | 当前维修知识库 |
| `backend/rag/test_tool.py` | Tool 合同测试和可执行调用示例 |
| `backend/rag/TOOL_CONTRACT.md` | 精简接口合同 |
| `backend/rag/TEAMMATE_HANDOFF.md` | 更完整的模块说明和验收清单 |

FastAPI 路由位于 `backend/main.py`：

```text
POST /api/rag-tool/search
GET  /api/rag-tool/health
```

不要把 `/api/rag-advice` 当作智能体的 RAG Tool。`/api/rag-advice` 是当前报告页面使用的结构化建议接口；智能体应调用 `/api/rag-tool/search` 或 Python 函数入口。

## 3. 推荐接入方式

### 3.1 智能体与项目后端在同一个 Python 进程

这种方式不经过 HTTP，调用链更短。智能体从 `backend` 目录启动时可直接导入：

```python
from rag.tool import (
    get_openai_function_definition,
    search_maintenance_knowledge,
)

rag_tool_definition = get_openai_function_definition()
```

注册给支持 OpenAI Function Calling 的模型：

```python
tools = [rag_tool_definition]
```

模型发起 Tool Call 后执行：

```python
import json


def execute_tool_call(tool_name: str, raw_arguments: str | dict) -> dict:
    if tool_name != "maintenance_knowledge_retriever":
        raise ValueError(f"Unsupported tool: {tool_name}")

    arguments = (
        json.loads(raw_arguments)
        if isinstance(raw_arguments, str)
        else raw_arguments
    )
    return search_maintenance_knowledge(arguments)
```

建议的智能体处理流程：

```text
用户提出维修问题
        ↓
模型判断需要查阅维修知识
        ↓
模型调用 maintenance_knowledge_retriever
        ↓
智能体执行 search_maintenance_knowledge
        ↓
将 Tool 返回的 documents 作为证据交回模型
        ↓
模型生成带来源、限制条件和安全提示的最终答案
```

### 3.2 智能体是独立服务

如果你的智能体不和本项目运行在同一个 Python 进程，通过 HTTP 调用：

```http
POST http://<backend-host>:8000/api/rag-tool/search
Content-Type: application/json
X-API-Key: <RAG_TOOL_API_KEY>
```

请求示例：

```json
{
  "request_id": "maintenance-chat-001",
  "query": "动力涡轮振动持续升高，需要检查哪些部件和安全边界？",
  "top_k": 4,
  "categories": ["engine_manual", "regulations"],
  "min_score": 0.1
}
```

本地启动后端：

```powershell
cd E:\huawei_xiangmu\huaweiyunmadaojingsai\backend
$env:RAG_TOOL_API_KEY = "your-local-test-key"
python -B main.py
```

健康检查：

```powershell
$headers = @{ "X-API-Key" = "your-local-test-key" }
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/rag-tool/health" `
  -Headers $headers
```

只有配置了 `RAG_TOOL_API_KEY` 时，HTTP 接口才强制校验 `X-API-Key`。未配置密钥只适合本地开发，生产环境必须配置。

## 4. 请求参数怎么传

| 字段 | 是否必填 | 约束 | 使用建议 |
|---|---|---|---|
| `query` | 是 | 2 到 500 个字符 | 不要只传“怎么修”，应包含部件、异常现象和需要查找的内容 |
| `request_id` | 否 | 8 到 64 个字符 | 推荐使用当前会话 ID 或链路 ID，方便排查问题 |
| `top_k` | 否 | 1 到 10，默认 4 | 一般使用 3 到 5，不要无条件取满 10 条 |
| `categories` | 否 | 最多 5 个分类 | 已知资料类型时再过滤；不确定时传空列表 |
| `min_score` | 否 | 0 到 1，默认 0 | 当前建议从 0.1 开始验证，不能把它当作故障概率阈值 |

当前分类：

| 分类 | 内容 |
|---|---|
| `engine_manual` | 发动机检查、参数超限和振动处置知识 |
| `airport_handbook` | 地面和航后处置流程 |
| `regulations` | 安全、合规和放行边界提醒 |

### 4.1 推荐的 query 结构

你的智能体应把用户问题和已有故障上下文合并成具体查询：

```text
部件：动力涡轮；异常：振动持续升高；风险等级：高；查询目标：检查部位、处置顺序和放行边界
```

不推荐：

```text
怎么修？
```

Tool 不会自动读取你的智能体会话历史。需要用于检索的部件、现象和风险上下文必须写进 `query`。

## 5. Tool 返回什么

关键响应结构：

```json
{
  "tool_name": "maintenance_knowledge_retriever",
  "tool_version": "1.0.0",
  "request_id": "maintenance-chat-001",
  "query": "动力涡轮振动持续升高，需要检查哪些部件和安全边界？",
  "read_only": true,
  "result_count": 1,
  "documents": [
    {
      "document_id": "engine_vibration-1",
      "title": "engine_vibration",
      "category": "engine_manual",
      "source": "knowledge_base/engine_manual/engine_vibration.md",
      "content": "检索到的知识片段",
      "content_hash": "64 位 SHA-256 哈希",
      "content_truncated": false,
      "score": 0.2379,
      "matched_terms": ["振动"]
    }
  ],
  "warnings": [],
  "metadata": {
    "retrieval_mode": "tfidf_cosine",
    "knowledge_base_version": "知识库版本",
    "index_mode": "in_memory",
    "records_scanned": 12,
    "eligible_records": 6,
    "matched_records": 1,
    "query_token_count": 4,
    "duration_ms": 4
  }
}
```

智能体必须重点使用以下字段：

- `documents[].content`：回答证据；
- `documents[].source`：最终答案中的资料来源；
- `documents[].content_hash`：审计时确认引用内容；
- `documents[].score`：只用于排序和过滤；
- `request_id`：关联一次智能体调用；
- `metadata.knowledge_base_version`：记录本次使用的知识库版本；
- `warnings`：决定是否拒答或调整参数重试。

## 6. 智能体如何使用返回结果

### 6.1 有检索结果

1. 将 `documents[].content` 作为独立的“检索证据”交给模型；
2. 明确要求模型不得超出证据内容补写手册条款；
3. 最终答案至少展示 `source`；
4. 涉及适航、放行和安全时，增加人工复核提示；
5. 内部调用记录保留 `request_id`、`document_id`、`content_hash` 和知识库版本。

建议放入系统提示词的约束：

```text
你必须先依据 maintenance_knowledge_retriever 返回的 documents 回答维修知识问题。
不得把 score 解释为故障概率或放行可信度。
没有检索证据时不得编造手册条款、维修步骤或适航结论。
最终答案应列出使用的 source。
涉及适航、放行和安全时，必须提示由有资质人员依据最新有效文件复核。
```

### 6.2 没有检索结果

当 `result_count=0` 或 `warnings` 包含 `NO_MATCHING_DOCUMENTS` 时：

- 告诉用户当前知识库没有足够依据；
- 可以把 query 补充得更具体后重试一次；
- 不要无限重试；
- 不要让模型转为无依据自由回答；
- 建议用户查阅最新有效维修手册或交由有资质人员处理。

### 6.3 分类错误

当出现 `UNKNOWN_CATEGORY:<category>` 时：

- 检查是否拼错分类；
- 可以移除错误分类后重试一次；
- 不要把未知分类静默映射成另一个分类。

## 7. Tool 使用注意事项

### 7.1 `score` 不是故障概率

当前 `score` 是 TF-IDF 文本余弦相似度，只表示问题与知识片段的文本相关程度。它不能用于表示：

- 故障发生概率；
- 风险等级；
- 维修方案正确率；
- 适航或放行可信度。

### 7.2 Tool 不能代替正式文件和人工判断

当前知识库用于比赛演示和辅助检索，不能替代：

- 最新有效维修手册；
- 厂家服务通告和适航指令；
- 运营人批准的维修程序；
- 有资质维修人员的检查和签署；
- 法定适航放行程序。

最终答案不得写成“系统已确认可以放行”。

### 7.3 无证据时必须拒绝编造

Tool 已显式提供 `NO_MATCHING_DOCUMENTS`。你的智能体必须消费这个信号，不能为了保持对话流畅而编造维修步骤。

### 7.4 必须保留引用

至少在面向用户的回答中保留 `source`。如果系统需要审计，还应保存 `document_id`、`content_hash` 和 `knowledge_base_version`。

### 7.5 不要记录敏感问题全文

Tool 自身的结构化日志不记录原始 `query`，但响应中会返回 `query`。你的智能体和网关也应避免把用户问题、设备编号或维修记录全文写入普通日志。

### 7.6 不要硬编码 API Key

- 本地测试密钥不能提交到 Git；
- 生产密钥必须由部署环境或密钥管理系统注入；
- 日志和错误响应中不得输出密钥；
- 生产环境应设置密钥轮换策略。

### 7.7 控制重复调用

同一个问题已有有效检索结果时不要再次无条件调用。建议限制一次回答中的 Tool 调用次数，避免模型形成调用循环。

### 7.8 处理超时和接口错误

建议智能体按以下方式处理：

| 情况 | 处理方式 |
|---|---|
| `401` | 密钥缺失或错误，停止重试并提示服务配置异常 |
| `422` | 参数不符合合同，修正参数；不要原样重复请求 |
| `5xx` 或超时 | 最多进行有限次数退避重试，然后返回检索服务暂不可用 |
| `NO_MATCHING_DOCUMENTS` | 属于正常业务结果，不按系统错误重试 |

### 7.9 当前检索能力边界

当前版本使用本地 TF-IDF 稀疏向量检索，不是语义 Embedding，也没有接入生产向量数据库。它适合当前小型知识库和可审计演示，不应对外宣称已经具备完整企业生产级向量检索基础设施。

未来替换为 Embedding 或向量数据库时，应保持现有请求和响应字段兼容。不兼容变更必须升级 `tool_version`。

## 8. 你接下来需要完成的工作

请按以下顺序接入：

1. 在智能体中注册 `get_openai_function_definition()` 返回的 Tool schema；
2. 实现 Tool Call 分发，只允许白名单名称 `maintenance_knowledge_retriever`；
3. 把模型生成的 arguments 解析成字典并调用 Python 函数或 HTTP 接口；
4. 将返回的 `documents` 作为证据交回模型；
5. 在最终回答中展示 `source`；
6. 实现 `NO_MATCHING_DOCUMENTS`、`401`、`422`、超时和 `5xx` 处理；
7. 为一次回答设置合理的 Tool 调用次数上限；
8. 添加智能体端集成测试；
9. 联调时记录 `request_id` 和知识库版本；
10. 上线前配置正式密钥、TLS、限流、审计和网络访问控制。

## 9. 智能体端必须覆盖的测试

至少测试以下场景：

1. “发动机振动异常”能调用 Tool 并引用 `engine_vibration.md`；
2. “液压系统泄漏”能检索机场处置知识；
3. 无关问题返回 `NO_MATCHING_DOCUMENTS` 后，智能体明确拒绝编造；
4. 放行问题包含人工复核和最新有效文件提示；
5. API Key 缺失或错误时能处理 `401`；
6. 非法参数导致 `422` 时不会无限重试；
7. Tool 超时或 `5xx` 时能降级回答；
8. 最终答案中的引用能够对应 `source` 和 `content_hash`；
9. 同一问题不会形成无限 Tool Call 循环。

RAG 模块自身测试命令：

```powershell
cd E:\huawei_xiangmu\huaweiyunmadaojingsai\backend
python -B -m unittest rag.test_rag rag.test_tool -v
```

当前基线为 14 项测试全部通过。

## 10. 接入完成标准

满足以下条件后，智能体与 RAG Tool 的联调才算完成：

- 智能体能够正确注册并调用 `maintenance_knowledge_retriever`；
- 请求参数符合 Tool 合同；
- 有证据的回答包含可追溯来源；
- 无证据时不会编造；
- `score` 没有被当作故障概率；
- 安全和放行问题保留人工复核边界；
- 鉴权失败、参数错误、超时和服务错误均有明确处理；
- 不在代码或日志中泄露 API Key；
- 智能体端集成测试全部通过；
- 现有 `/api/predict`、报告页面和其他 RAG 接口没有受到影响。

如需确认最精确的字段约束，以 `backend/rag/tool.py` 和 `backend/rag/test_tool.py` 为准。

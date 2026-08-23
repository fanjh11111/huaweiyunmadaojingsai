# 维修知识问答智能体 RAG 工具交接文档

> 交接日期：2026-08-11
> 工具名称：`maintenance_knowledge_retriever`
> 工具版本：`1.0.0`
> 交接对象：维修知识问答智能体开发者

## 1. 交接结论

我已经在现有项目中完成了一个独立、只读、可被智能体直接调用的 RAG 检索工具。RAG 的知识库、索引、检索、工具合同和测试均保存在当前 `backend/rag/` 目录下，没有修改故障预测算法。

你不需要重新实现检索模块。接下来只需要把本工具注册到你的维修知识问答智能体，在模型发起工具调用时传入检索参数，再基于返回的 `documents` 组织答案和引用。

工具只负责“检索证据”，不负责代替维修人员做适航放行判断。

## 2. 我已经完成的内容

### 2.1 独立 RAG 模块

| 文件 | 作用 |
|---|---|
| `tool.py` | 对外稳定工具合同、输入校验、响应封装、健康检查和结构化日志 |
| `retriever.py` | 本地 TF-IDF 稀疏向量与余弦相似度检索 |
| `build_index.py` | Markdown 切片、内容哈希、JSON 索引生成和知识库版本计算 |
| `knowledge_base/` | 维修手册、机场处置流程和安全边界知识 |
| `agent.py` | 当前项目已有的结构化维修建议和追问逻辑 |
| `test_tool.py` | 对外工具合同测试 |
| `test_rag.py` | 原有建议和追问能力回归测试 |
| `TOOL_CONTRACT.md` | 精简版调用合同 |

当前知识库包含 4 份文档、12 个知识片段，覆盖：

- 发动机排气温度超限；
- 发动机振动异常；
- 液压系统泄漏；
- 安全信息和放行边界提醒。

### 2.2 检索能力

- 支持中文单字、双字词元和英文词元；
- 支持英文下划线字段拆分；
- 使用 TF-IDF 余弦相似度排序；
- 支持 `top_k`、知识分类过滤和 `min_score`；
- 返回匹配词、分数、来源和内容哈希；
- 知识不足时显式返回警告，不生成虚假证据。

### 2.3 智能体调用入口

已经提供三种入口：

1. Python 函数：`search_maintenance_knowledge(payload)`；
2. Python 类：`MaintenanceKnowledgeRetriever().search(payload)`；
3. HTTP：`POST /api/rag-tool/search`。

如你的智能体支持 OpenAI Function Calling，可以使用：

```python
from rag.tool import get_openai_function_definition

tool_definition = get_openai_function_definition()
```

生成的函数名称固定为 `maintenance_knowledge_retriever`。

### 2.4 合同和安全控制

- 使用 Pydantic 严格校验输入，未知字段会被拒绝；
- 请求和响应带 `request_id`，便于贯通智能体调用日志；
- 响应包含 `tool_name`、`tool_version` 和知识库版本；
- 每个知识片段包含 SHA-256 `content_hash`；
- 返回内容长度有上限，并明确标记是否截断；
- 工具是只读的，不提供知识库写入或删除能力；
- 结构化日志只记录请求长度、分类数、结果数和耗时，不记录原始问题；
- 配置 `RAG_TOOL_API_KEY` 后，HTTP 端点必须携带 `X-API-Key`；
- API Key 鉴权只作用于 `/api/rag-tool/*`，不会影响原有预测和报告接口。

### 2.5 已完成验证

- RAG 自动化测试：14 项全部通过；
- 前端 Vite 生产构建通过；
- 无 API Key 访问受保护接口返回 `401`；
- 非法请求返回 `422`；
- 正确检索请求返回 `200`；
- 中英文查询和 UTF-8 响应正常；
- `/api/rag-advice` 和 `/api/rag-followup` 回归正常；
- `/api/predict` 完整数据回归保持 1090 个原始故障段、53 条故障详情、5 项排行和 8 个全局指标。

## 3. 工具调用合同

### 3.1 请求字段

| 字段 | 必填 | 约束 | 说明 |
|---|---|---|---|
| `query` | 是 | 2 到 500 个字符 | 用户问题或由智能体整理的故障检索描述 |
| `request_id` | 否 | 8 到 64 个字符 | 建议传入会话 ID 或链路 ID；不传时自动生成 |
| `top_k` | 否 | 1 到 10，默认 4 | 最多返回的知识片段数 |
| `categories` | 否 | 最多 5 项 | 可选：`engine_manual`、`airport_handbook`、`regulations` |
| `min_score` | 否 | 0 到 1，默认 0 | 最小 TF-IDF 余弦相似度 |

推荐请求：

```json
{
  "request_id": "maintenance-chat-001",
  "query": "动力涡轮振动持续升高，需要检查哪些部件和安全边界？",
  "top_k": 4,
  "categories": ["engine_manual", "regulations"],
  "min_score": 0.1
}
```

### 3.2 关键响应字段

```json
{
  "tool_name": "maintenance_knowledge_retriever",
  "tool_version": "1.0.0",
  "request_id": "maintenance-chat-001",
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

`score` 只是文本检索相似度，不是故障概率、风险概率或放行可信度。

### 3.3 警告处理

| 警告 | 你的智能体应该怎么处理 |
|---|---|
| `NO_MATCHING_DOCUMENTS` | 明确告诉用户当前知识库依据不足，不得编造维修步骤或手册条款 |
| `UNKNOWN_CATEGORY:<name>` | 检查分类参数；可以移除错误分类后再检索一次 |

## 4. 接下来你要做什么

### 第一步：在智能体中注册工具

如果智能体和后端运行在同一个 Python 进程，优先直接调用，减少一次 HTTP 开销：

```python
from rag.tool import get_openai_function_definition, search_maintenance_knowledge

tools = [get_openai_function_definition()]


def execute_tool(tool_name: str, arguments: dict) -> dict:
    if tool_name != "maintenance_knowledge_retriever":
        raise ValueError(f"Unsupported tool: {tool_name}")
    return search_maintenance_knowledge(arguments)
```

如果你的智能体是独立服务，则通过 HTTP 调用：

```http
POST http://<backend-host>:8000/api/rag-tool/search
Content-Type: application/json
X-API-Key: <由部署环境注入的密钥>
```

不要在代码、提示词或 Git 仓库中写死 API Key。

### 第二步：设计智能体的工具调用策略

你的系统提示词至少要包含以下规则：

1. 回答维修知识问题前优先调用本工具获取证据；
2. 只根据 `documents` 中的内容回答，并保留 `source`；
3. `result_count=0` 时必须拒绝编造；
4. 不把 `score` 描述成故障概率；
5. 涉及适航、放行和安全时，提示由有资质人员按最新有效文件复核；
6. 工具中的示例知识不能替代正式维修手册、适航指令或运营人批准程序。

建议把用户原始问题与已知故障上下文合并成具体查询，例如：

```text
部件：动力涡轮；现象：振动持续升高；风险：高；需要检查部位、处置顺序和放行边界
```

### 第三步：处理工具返回结果

- 将 `documents[].content` 放入模型的证据上下文；
- 在最终答案中展示 `documents[].source`；
- 在内部日志中关联 `request_id` 和 `knowledge_base_version`；
- 需要审计时保存 `document_id` 和 `content_hash`；
- 同一个用户问题不要无条件重复调用工具，避免循环调用；
- 工具失败时返回可解释的降级信息，不要转为无依据自由回答。

### 第四步：增加你的智能体端测试

至少覆盖以下场景：

1. 发动机振动问题能调用工具并引用 `engine_vibration.md`；
2. 液压泄漏问题能检索机场处置知识；
3. 无关问题得到 `NO_MATCHING_DOCUMENTS` 后不会编造；
4. 放行问题包含人工复核和最新有效文件提示；
5. API Key 缺失或错误时，智能体能识别 `401` 并返回服务不可用提示；
6. 非法参数导致 `422` 时，不应无限重试同一请求。

### 第五步：部署前补齐外围能力

当前工具提供企业式调用合同、校验、追踪、可选鉴权和审计字段，但下面这些属于部署平台或后续基础设施工作，不在当前本地工具内：

- 网关 TLS；
- 正式 IAM 或服务身份认证；
- 租户隔离；
- 限流、熔断和调用配额；
- 集中日志与审计存储；
- 密钥轮换；
- 正式语义 Embedding 和向量数据库；
- 经授权、版本受控的真实维修手册和适航文件。

生产上线前必须补齐这些能力，不能把当前本地测试密钥当作生产密钥。

## 5. 本地启动和验证

在项目 `backend` 目录执行：

```powershell
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

运行全部 RAG 测试：

```powershell
python -B -m unittest rag.test_rag rag.test_tool -v
```

当前健康检查应至少满足：

- `status` 为 `ready`；
- `document_count` 为 4；
- `chunk_count` 为 12；
- 分类包含 `engine_manual`、`airport_handbook` 和 `regulations`。

`index_mode` 可能是 `in_memory`；执行以下命令生成本地 JSON 索引后会变为 `persisted_json`：

```powershell
python -B -m rag.build_index
```

## 6. 不要改错的边界

- 不要为接入智能体而修改 `/api/predict` 的模型推理逻辑；
- 不要把 `/api/rag-advice` 当作智能体检索工具，它是当前报告页面的结构化建议接口；
- 不要删除 `source`、`content_hash`、`request_id` 和知识库版本字段；
- 不要在无证据时让大模型自行补全手册内容；
- 不要把本地 TF-IDF 描述成已接入生产向量数据库；
- 未来替换检索引擎时，应保持现有请求和响应字段兼容；不兼容变更必须升级 `tool_version`。

## 7. 你的完成标准

当下面各项都满足时，你的维修知识问答智能体接入才算完成：

- 智能体能注册并调用 `maintenance_knowledge_retriever`；
- 工具调用参数通过当前 Pydantic 合同；
- 正常回答包含真实知识来源；
- 无检索结果时不会编造；
- 安全和放行问题保留人工复核边界；
- 智能体端测试覆盖成功、无结果、鉴权失败和参数错误；
- 生产部署不使用仓库内硬编码密钥；
- 替换检索引擎后仍通过 `rag.test_tool` 合同测试。

如需了解字段的精简定义，继续阅读 `TOOL_CONTRACT.md`；如需查看可执行示例，以 `test_tool.py` 为准。

# 维修知识检索工具合同

## 用途

`maintenance_knowledge_retriever` 是一个只读 RAG 工具，供维修知识问答智能体检索已入库的维修、机场处置和安全边界资料。

工具只返回证据片段和可追溯引用，不生成维修结论、不执行放行判断、不写入知识库。

## Python 直接调用

```python
from rag.tool import search_maintenance_knowledge

result = search_maintenance_knowledge({
    "request_id": "chat-20260811-001",
    "query": "动力涡轮振动升高后需要检查哪些部件？",
    "top_k": 4,
    "categories": ["engine_manual"],
    "min_score": 0.1,
})
```

智能体框架如支持 OpenAI function calling，可注册：

```python
from rag.tool import get_openai_function_definition

tool_definition = get_openai_function_definition()
```

## HTTP 调用

```http
POST /api/rag-tool/search
Content-Type: application/json
X-API-Key: <RAG_TOOL_API_KEY，仅生产环境配置后必填>
```

```json
{
  "request_id": "chat-20260811-001",
  "query": "动力涡轮振动升高后需要检查哪些部件？",
  "top_k": 4,
  "categories": ["engine_manual"],
  "min_score": 0.1
}
```

健康检查：

```http
GET /api/rag-tool/health
```

## 稳定响应字段

| 字段 | 含义 |
|---|---|
| `tool_name` / `tool_version` | 工具标识和合同版本 |
| `request_id` | 调用链路标识；调用方未传时工具自动生成 |
| `documents` | 可用于回答的知识片段 |
| `documents[].source` | 知识文件相对路径 |
| `documents[].content_hash` | 片段内容哈希，用于引用审计 |
| `documents[].score` | 当前 TF-IDF 余弦相似度，范围 0 到 1 |
| `metadata.knowledge_base_version` | 本次检索所用知识库版本 |
| `warnings` | 例如 `NO_MATCHING_DOCUMENTS` |

## 智能体调用约束

1. 优先根据用户问题构造具体、可检索的 `query`。
2. 仅将 `documents` 作为回答依据，并在回答中保留来源信息。
3. `result_count=0` 或含 `NO_MATCHING_DOCUMENTS` 时，不得编造手册条款或维修步骤。
4. 涉及放行、适航、安全时，必须提示由有资质人员依据最新有效文件复核。
5. 不得把工具分数解释为故障概率或适航结论。

## 安全与运维约定

- 请求长度、分类数量、返回数量和最小分数均由 Pydantic 合同限制。
- 工具记录结构化调用事件，但不记录原始 `query`，避免维修数据进入普通日志。
- 配置 `RAG_TOOL_API_KEY` 后，HTTP 工具端点要求 `X-API-Key`；未配置时仅适合本地开发。
- 生产环境还应在网关层配置 TLS、身份认证、限流、审计存储和网络访问控制。
- 当前检索引擎为本地 TF-IDF 稀疏向量模式。接入语义 Embedding/向量数据库时必须保持本合同字段兼容，并升级 `tool_version`。

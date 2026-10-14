# RAG 维修建议模块

该目录是独立的本地 RAG 模块，不修改现有预测算法。第一版采用可审计的本地 TF-IDF 稀疏向量检索和固定结构生成，不依赖外部大模型或向量数据库。

面向其他智能体调用的只读检索工具见 [TOOL_CONTRACT.md](TOOL_CONTRACT.md)。

与维修知识问答智能体开发者协作时，完整接入步骤和验收清单见 [TEAMMATE_HANDOFF.md](TEAMMATE_HANDOFF.md)。

## API

`POST /api/rag-advice`

请求字段：`component`、`fault_type`、`risk_level`、`confidence`、`abnormal_features`、`description`。

响应字段：异常判断、风险等级、建议检查步骤、放行建议、参考依据和注意事项。所有参考依据均保留 `source`。

`POST /api/rag-followup`

第二阶段接口。请求包含一期建议 `context`，以及 `evidence`、`why`、`extra_checks`、`question` 四种 `action` 之一。自由追问只回答当前知识库覆盖的维修问题，依据不足时明确拒答。

## 本地验证

在 `backend` 目录执行：

```powershell
python -B -m unittest rag.test_rag
```

如需生成可持久化的 `index.json`，可在具备目录写权限的环境执行：

```powershell
python -B -m rag.build_index
```

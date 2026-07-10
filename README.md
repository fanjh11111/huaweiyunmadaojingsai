# 航空发动机健康监测与故障预测看板

本项目是一个面向航空发动机健康评估的演示系统，包含前端 3D 可视化看板、FastAPI 推理后端、LSTM 故障预测模型以及若干离线训练/数据检查脚本。

系统的基本流程是：用户在前端上传发动机传感器数据文件，后端调用已训练的 LSTM 模型进行故障预测，返回故障等级、部件排行、故障详情、关键指标等结果，前端将结果以驾驶舱看板、3D 发动机模型和报告页面展示。

## 项目结构

```text
hangkong_3D/
├─ backend/
│  ├─ main.py
│  ├─ engine_scaler.pkl
│  ├─ lstm_engine_traced.pt
│  └─ lstm_engine_weights.pth
├─ public/
│  └─ models/
│     └─ turbine__turbofan_engine__jet_engine.glb
├─ src/
│  ├─ main.ts
│  ├─ App.vue
│  ├─ HomeView.vue
│  ├─ PredictReport.vue
│  ├─ FaultAnalysisReport.vue
│  ├─ engineDataConfig.ts
│  ├─ vite-env.d.ts
│  └─ router/
│     └─ index.ts
├─ 1.py
├─ check_data.py
├─ save_columns.py
├─ save_features.py
├─ package.json
├─ package-lock.json
├─ index.html
├─ vite.config.ts
└─ RAG_IMPROVEMENT_PLAN.md
```

## 核心模块说明

### `backend`

后端推理服务目录。

- `main.py`：FastAPI 服务入口，提供 `/api/predict` 接口。接口接收前端上传的 CSV 文件，完成数据读取、归一化、LSTM 推理、连续故障段提取、部件映射和展示数据生成。
- `engine_scaler.pkl`：训练阶段保存的数据归一化器，推理时用于保证输入数据缩放方式一致。
- `lstm_engine_traced.pt`：TorchScript 格式的 LSTM 推理模型，后端实际加载该文件进行预测。
- `lstm_engine_weights.pth`：PyTorch 权重文件，可用于重新加载模型结构或后续训练维护。

### `src`

前端源码目录，基于 Vue 3、Vite、Three.js、ECharts 实现。

- `main.ts`：Vue 应用入口，注册路由并挂载应用。
- `App.vue`：根组件，负责渲染路由页面。
- `HomeView.vue`：主看板页面。包含文件上传、故障预测结果展示、发动机关键指标、故障等级统计、部件排行、部件详情、趋势图和 3D 发动机模型。
- `PredictReport.vue`：预测报告页面，用于展示发动机健康评分、风险等级、参数趋势、故障预测分布和维护建议。
- `FaultAnalysisReport.vue`：故障分析报告页面，用于进一步展示和导出故障分析结果。
- `engineDataConfig.ts`：前端默认演示数据和类型定义，在没有上传数据或后端结果时提供初始展示内容。
- `router/index.ts`：前端路由配置，包含主看板 `/`、预测报告 `/predict-report` 和故障分析 `/fault-analysis`。
- `vite-env.d.ts`：Vite TypeScript 类型声明文件。

### `public/models`

前端静态模型资源目录。

- `turbine__turbofan_engine__jet_engine.glb`：Three.js 加载的发动机 3D 模型。

### 根目录 Python 脚本

- `1.py`：离线 LSTM 训练与故障段分析脚本。用于读取带标签的发动机传感器数据，训练 LSTM 二分类模型，并输出连续故障段分析结果。
- `check_data.py`：数据文件检查脚本，用于尝试读取 CSV 或 Excel 文件并输出列名、行列数和数据预览。
- `save_columns.py`：读取 Excel 数据并将列名保存到 `columns_output.txt`，用于核对传感器字段。
- `save_features.py`：读取 Excel 数据并将字段列表保存为 `feature_names.json`，用于前后端字段映射和调试。

### 前端配置文件

- `package.json`：前端项目依赖和 npm 脚本配置。
- `package-lock.json`：npm 依赖锁定文件。
- `index.html`：Vite 应用入口 HTML。
- `vite.config.ts`：Vite 构建配置。

### `RAG_IMPROVEMENT_PLAN.md`

后续优化方案文档，说明如何在现有故障预测系统基础上引入基于 RAG 的智能体，用于根据维修手册、机场处理手册和民航安全规定生成发动机处置建议。

## 运行方式

### 1. 启动后端

进入项目根目录后执行：

```bash
cd backend
python main.py
```

后端默认启动在：

```text
http://localhost:8000
```

前端上传文件时会请求：

```text
http://localhost:8000/api/predict
```

### 2. 启动前端

另开一个终端，进入项目根目录：

```bash
npm install
npm run dev
```

启动后根据终端提示，在浏览器中打开本地地址访问看板。

## 主要页面

- `/`：发动机健康监测主看板。
- `/predict-report`：AI 预测报告页面。
- `/fault-analysis`：故障分析报告页面。

## 当前实现状态

当前项目已经具备以下能力：

- 上传传感器 CSV 文件；
- 调用后端 LSTM 模型进行故障预测；
- 统计故障严重、中等、轻微等级；
- 根据异常特征推断可能故障部件；
- 展示发动机关键指标、部件排行、故障详情和预测结果；
- 使用 Three.js 展示发动机 3D 模型；
- 提供预测报告和故障分析报告页面。

后续可继续按照 `RAG_IMPROVEMENT_PLAN.md` 中的方案，引入维修知识库和 RAG 智能体，生成更完整的维修处置建议。

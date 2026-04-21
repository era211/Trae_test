# 数据集生成与标注系统

一个完整的数据集生成和数据标注 Web 平台，支持多种 NLP 任务类型。

## 功能特性

### 数据集生成
- **文本分类** — 自动生成带标注提示的文本分类样本
- **命名实体识别 (NER)** — 生成含人名、地名、机构名等实体的文本
- **问答 (QA)** — 生成上下文 + 问题的问答对
- **指令微调** — 生成 instruction/input/output 三元组
- **文本生成** — 生成提示词与对应生成任务

### 数据标注
- 可视化标注界面，支持所有任务类型
- 文本分类：点击标签一键标注
- NER：选中文字后选择实体类型
- QA / 指令微调 / 文本生成：富文本填写输出
- 支持标注审核（通过 / 拒绝）
- 进度追踪与统计

### 数据管理
- 项目管理（CRUD）
- 数据集管理（CRUD）
- 数据导入 / 导出（JSON / JSONL）
- 标注统计面板

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# 访问
open http://localhost:8080
```

## 项目结构

```
.
├── main.py                        # FastAPI 入口
├── requirements.txt
├── backend/
│   ├── database.py                # SQLAlchemy 模型 + SQLite
│   ├── schemas.py                 # Pydantic 请求/响应模型
│   ├── routes/
│   │   ├── projects.py            # 项目 CRUD API
│   │   ├── datasets.py            # 数据集 & 条目 API
│   │   └── generation.py         # 数据生成 API
│   └── generators/
│       └── data_generator.py     # 各任务类型数据生成器
└── frontend/
    ├── index.html                 # SPA 入口
    ├── css/style.css
    └── js/app.js                  # 前端逻辑（Vanilla JS）
```

## API 文档

启动服务后访问 [http://localhost:8080/docs](http://localhost:8080/docs) 查看交互式 API 文档。

## 支持的任务类型

| 类型 | 说明 |
|------|------|
| `text_classification` | 文本分类 |
| `ner` | 命名实体识别 |
| `qa` | 问答 |
| `instruction_tuning` | 指令微调 |
| `text_generation` | 文本生成 |

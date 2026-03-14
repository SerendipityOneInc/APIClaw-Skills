# APIClaw Analysis Skill

> 面向 AI 智能体的亚马逊选品调研技能 — 基于 [APIClaw API](https://apiclaw.io)

## 功能概览

赋予 AI 智能体实时亚马逊选品调研能力：

- 🔍 **市场验证** — 品类规模、集中度、新品率
- 🎯 **产品选品** — 14 种内置筛选预设（新手、快速周转、新兴品类等）
- 📊 **竞品分析** — 品牌/卖家格局、中国卖家案例
- ⚠️ **风险评估** — 6 维风险矩阵 + 合规预警
- 💰 **定价策略** — 价格带分析、利润估算
- 📈 **日常运营** — 市场监控、异常预警

## 目录结构

```
apiclaw-analysis-skill/
├── SKILL.md                  # 主入口 — 意图路由、使用方法、评估标准
├── references/
│   ├── reference.md          # API 接口、字段、筛选条件、评分标准
│   └── scenarios.md          # 进阶场景（评估、定价、运营、拓品）
└── scripts/
    └── apiclaw.py            # CLI 脚本 — 8 个子命令、14 种预设模式
```

## 快速开始

### 1. 获取 API Key

前往 [apiclaw.io/api-keys](https://apiclaw.io/api-keys) 注册账号 → 创建 API Key（格式：`hms_live_xxx`）

### 2. 开始使用

将 API Key 告诉你的 AI 智能体，它会自动完成配置。

### 3. 验证

```bash
python3 scripts/apiclaw.py check
```

## 脚本命令

| 命令 | 说明 |
|------|------|
| `categories` | 查询亚马逊品类树 |
| `market` | 市场级聚合数据 |
| `products` | 带筛选条件的产品搜索（14 种预设模式） |
| `competitors` | 按关键词/品牌/ASIN 查询竞品 |
| `product` | 单个 ASIN 实时详情 |
| `report` | 完整市场报告（组合工作流） |
| `opportunity` | 产品机会发现（组合工作流） |
| `check` | API 连通性自检 |

## 选品模式

14 种内置预设，通过 `products --mode` 使用：

`beginner` · `fast-movers` · `emerging` · `high-demand-low-barrier` · `single-variant` · `long-tail` · `underserved` · `new-release` · `fbm-friendly` · `low-price` · `broad-catalog` · `selective-catalog` · `speculative` · `top-bsr`

## 环境要求

- Python 3.8+（仅使用标准库，无需 pip 安装依赖）
- APIClaw API Key（[点此获取](https://apiclaw.io/api-keys)）

> 📖 [English](README.md)

## API 覆盖范围

| 接口 | 说明 |
|------|------|
| `categories` | 亚马逊品类树导航 |
| `markets/search` | 市场级指标（集中度、品牌数等） |
| `products/search` | 产品搜索，支持 20+ 筛选参数 |
| `products/competitor-lookup` | 按关键词/品牌/ASIN 发现竞品 |
| `realtime/product` | 实时产品详情（评论、卖点、变体） |

## 许可证

MIT

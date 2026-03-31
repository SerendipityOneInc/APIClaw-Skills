<p align="right">
  <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <h1 align="center">APIClaw Skills</h1>
</p>

<p align="center">
  <b>面向 AI Agent 的亚马逊电商数据层技能包。</b><br/>
  200M+ 商品、1B+ 评论、实时信号 — 为 AI 结构化，而非为人类设计。
</p>

<p align="center">
  <a href="https://github.com/SerendipityOneInc/APIClaw-Skills/actions/workflows/ci.yml"><img src="https://github.com/SerendipityOneInc/APIClaw-Skills/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://apiclaw.io"><img src="https://img.shields.io/badge/API-apiclaw.io-orange" alt="API" /></a>
  <a href="https://discord.gg/YfDFU9BDp5"><img src="https://img.shields.io/badge/Discord-Join-7289da?logo=discord&logoColor=white" alt="Discord" /></a>
  <a href="https://github.com/SerendipityOneInc/APIClaw-Skills/stargazers"><img src="https://img.shields.io/github/stars/SerendipityOneInc/APIClaw-Skills?style=social" alt="Stars" /></a>
</p>

<p align="center">
  <a href="https://apiclaw.io">官网</a> •
  <a href="https://apiclaw.io/en/api-keys">获取 API Key</a> •
  <a href="https://discord.gg/YfDFU9BDp5">Discord</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#api-接口">API 参考</a>
</p>

---

## 什么是 APIClaw？

[APIClaw](https://apiclaw.io) 是专为 Agent 构建的数据基础设施。模型正在商品化，真正稀缺的是 Agent 能直接消费的结构化数据。APIClaw 提供实时电商信号，让你的 Agent 每天能分析 10,000+ 商品，而不是 100 个。

当前已接入亚马逊，提供 6 个 API 接口：产品搜索（14 种预设模式）、市场分析、竞品情报、实时追踪、AI 评论洞察、类目导航。干净 JSON，Agent 即用。

本仓库包含 **两个 Agent 技能**，让任何 AI 助手都能即插即用地调用 APIClaw：

| 技能 | 说明 | 适用场景 |
|------|------|----------|
| 📦 **[`apiclaw/`](apiclaw/)** | 数据层概览，6 个 API 接口，快速集成 | 快速上手，Agent tool-calling |
| 🎯 **[`amazon-analysis/`](amazon-analysis/)** | 14 种选品策略，市场验证，竞品情报，风险评估 | 深度选品调研，自主选品 Agent |

## 快速开始

### 1. 安装技能包

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

安装时会提示选择技能：
- **APIClaw — Commerce Data for AI Agents**（通用概览，6 个接口）
- **Amazon Product Research & Seller Analytics**（深度分析，14 种策略）

也可以手动克隆：
```bash
git clone https://github.com/SerendipityOneInc/APIClaw-Skills.git
```

### 2. 设置 API Key

```bash
export APICLAW_API_KEY='hms_live_xxx'   # 在 apiclaw.io/en/api-keys 免费获取
```

> 🎁 **免费额度**：注册即送 1,000 credits，1 credit = 1 次 API 调用，无需信用卡。

### 3. 试一试

让你的 AI Agent 试试：

> *"分析一下美国亚马逊上 50 美元以下无线耳机的竞争格局"*

或者直接用命令行：

```bash
python amazon-analysis/scripts/apiclaw.py products --keyword "wireless earbuds" --mode competitive_landscape
```

## 示例：商品搜索

```bash
curl -X POST 'https://api.apiclaw.io/openapi/v2/products/search' \
  -H 'Authorization: Bearer hms_live_xxx' \
  -H 'Content-Type: application/json' \
  -d '{
    "keyword": "wireless earbuds",
    "mode": "beginner",
    "priceMax": 50,
    "pageSize": 3
  }'
```

返回示例（精简版）：

```json
{
  "products": [
    {
      "asin": "B0D5CRV4KL",
      "title": "Wireless Earbuds Bluetooth 5.3 ...",
      "price": 29.99,
      "rating": 4.5,
      "ratingCount": 12847,
      "bsrRank": 15,
      "atLeastMonthlySales": 8500,
      "brand": "SoundCore",
      "profitMargin": 0.42
    }
  ]
}
```

> **注意：** 这是精简示例，实际返回包含更多字段。完整字段列表请参考 [API 参考文档](apiclaw/references/openapi-reference.md)。

## API 接口

| 接口 | 说明 | 使用场景 |
|------|------|----------|
| 🔍 `products/search` | 商品搜索，14 种预设模式，20+ 筛选条件 | *"找 80 美元以下、4 星以上的跑步鞋"* |
| 📊 `markets/search` | 市场维度指标——集中度、品牌份额、定价分布 | *"瑜伽垫市场竞争激烈吗？"* |
| 🏷️ `products/competitor-lookup` | 按关键词、品牌或 ASIN 发现竞品 | *"这个细分类目的头部卖家有哪些？"* |
| ⚡ `realtime/product` | 实时商品详情——评论、功能、变体 | *"查一下 ASIN B0D5CRV4KL 的最新信息"* |
| 💬 `reviews/analyze` | AI 驱动的评论洞察——情感分析、痛点提取 | *"消费者对这个产品的好评和差评分别集中在哪里？"* |
| 📁 `categories` | 亚马逊类目树导航 | *"看看 Electronics 下面有哪些子类目"* |

**Base URL：** `https://api.apiclaw.io/openapi/v2`
**认证方式：** `Authorization: Bearer $APICLAW_API_KEY`
**请求方法：** 所有接口均使用 `POST`，请求体为 JSON

## 14 种选品模式

`products/search` 接口支持 14 种预设模式，覆盖不同的选品策略：

| 模式 | 策略 | 适用人群 |
|------|------|----------|
| `beginner` | 低竞争，易入场 | 新手卖家 |
| `fast-movers` | 高销售速率 | 追求快速出单 |
| `emerging` | 上升趋势，低饱和度 | 抢占先机 |
| `long-tail` | 长尾关键词，稳定需求 | 追求持续收益 |
| `underserved` | 高需求，卖家少 | 市场空白 |
| `new-release` | 最近上架的商品 | 追踪趋势 |
| `fbm-friendly` | 适合自发货 | 低投入起步 |
| `low-price` | 低价商品 | 走量策略 |
| `single-variant` | 简单 Listing，无变体 | 方便管理 |
| `high-demand-low-barrier` | 高销量，低评论门槛 | 可规模化入场 |
| `broad-catalog` | 宽品类范围分析 | 类目全景 |
| `selective-catalog` | 精选高质量商品 | 精品路线 |
| `speculative` | 高风险高回报机会 | 激进策略 |
| `top-bsr` | BSR 排行榜头部 | 研究头部玩家 |

## 应用场景

- 🔎 **选品调研** — 发现低竞争、高利润的细分市场
- 📈 **竞品监控** — 追踪竞品的价格、评论和 BSR 变化
- ✍️ **Listing 优化** — 基于 AI 评论分析优化你的商品文案
- 🚀 **市场进入分析** — 评估市场规模、竞争格局和利润空间
- 📊 **趋势发现** — 捕捉正在起飞的商品和新兴类目

## 项目结构

```
├── apiclaw/                        # 通用技能（轻量版）
│   ├── SKILL.md                      # 能力概览，快速入门
│   └── references/
│       └── openapi-reference.md      # API 字段参考
│
├── amazon-analysis/                # 亚马逊深度分析技能
│   ├── SKILL.md                      # 意图路由，工作流，评估标准
│   ├── references/
│   │   ├── reference.md              # 完整 API 参考
│   │   ├── scenarios-composite.md    # 综合推荐
│   │   ├── scenarios-eval.md         # 商品评估、风险分析、评论
│   │   ├── scenarios-pricing.md      # 定价策略、利润估算
│   │   ├── scenarios-ops.md          # 市场监控、预警
│   │   ├── scenarios-expand.md       # 扩展、趋势
│   │   └── scenarios-listing.md      # Listing 撰写与优化
│   └── scripts/
│       └── apiclaw.py                # CLI 工具 — 8 个子命令，14 种预设模式
```

## 环境要求

- Python 3.8+（仅依赖标准库，零 pip 依赖）
- APIClaw API Key（[免费获取](https://apiclaw.io/en/api-keys)）

## 参与贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解贡献指南。

## 社区

- 💬 [Discord](https://discord.gg/YfDFU9BDp5) — 聊天、提问、分享你在做的东西
- 🐛 [Issues](https://github.com/SerendipityOneInc/APIClaw-Skills/issues) — Bug 反馈和功能建议
- 📖 [API 文档](https://apiclaw.io) — 完整 API 文档

## 开源协议

[MIT](LICENSE) © [SerendipityOne Inc.](https://apiclaw.io)

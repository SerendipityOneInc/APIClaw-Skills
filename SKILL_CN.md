---
name: apiclaw-analysis
version: 1.0.0
description: >
  亚马逊卖家数据分析工具。功能：市场调研、选品、竞品分析、ASIN 评估、定价参考、品类研究。
  通过 scripts/apiclaw.py 调用 APIClaw API，需要 APICLAW_API_KEY。
---

# APIClaw — 亚马逊卖家数据分析

> AI 驱动的亚马逊选品调研。从市场发现到日常运营。
>
> **语言规则**：始终使用用户的语言回复。用户用中文问就用中文答，用英文问就用英文答。本技能文档的语言不影响输出语言。
> 所有 API 调用通过 `scripts/apiclaw.py` 执行 — 一个脚本，5 个接口，内置错误处理。

## 凭证

- 必需：`APICLAW_API_KEY`
- 作用域：仅用于 `https://api.apiclaw.io`
- 存储位置：技能目录下的 `config.json`（与 SKILL.md 同级）

### API Key 配置机制

**配置文件位置：** 技能根目录下的 `config.json`，与 `SKILL.md` 同级。

```
apiclaw-analysis-skill/
├── config.json          ← API Key 存储在这里
├── SKILL.md
├── scripts/
│   └── apiclaw.py
└── references/
```
**配置文件格式：**
```json
{
  "api_key": "hms_live_xxxxxx"
}
```

### 初始配置（AI 操作指南）

当用户首次使用或提供新 Key 时，AI 应执行：

```python
import os, json
# config.json 存储在技能根目录（scripts/ 的上级目录）
skill_dir = os.path.dirname(os.path.abspath(__file__))  # 从 scripts/ 运行时
skill_dir = os.path.dirname(skill_dir)  # 返回技能根目录
config_path = os.path.join(skill_dir, "config.json")
with open(config_path, "w") as f:
    json.dump({"api_key": "hms_live_用户提供的key"}, f, indent=2)
print(f"API Key 已保存到 {config_path}")
```

### 获取 API Key

**新用户请先获取 API Key：**

1. 访问 [APIClaw 控制台](https://apiclaw.io/api-keys) 注册账号
2. 创建 API Key，复制（格式：`hms_live_xxxxxx`）
3. 在对话中将 Key 告诉 AI，AI 会自动保存到配置文件

**新 Key 首次使用提示：** 新配置的 API Key 可能需要 3-5 秒在后端完全激活。如果首次调用返回 403 错误，AI 应等待 3 秒后重试，最多重试 2 次。

## 文件索引

| 文件 | 何时使用 |
|------|----------|
| `SKILL.md`（本文件） | 从这里开始 — 覆盖 80% 的任务 |
| `scripts/apiclaw.py` | **执行**所有 API 调用（不要读入上下文） |
| `references/reference.md` | 需要确认字段名或筛选条件详情时加载 |
| `references/scenarios.md` | 定价、日常运营或拓品场景（5.x/6.x/7.x）时加载 |

### 参考文件使用指南（重要）

**以下场景必须加载参考文件**：

| 场景 | 加载文件 | 原因 |
|------|----------|------|
| 需要确认字段名 | `reference.md` | 避免字段名错误（如 ratingCount vs reviewCount）|
| 需要筛选参数详情 | `reference.md` | 获取完整的 Min/Max 参数列表 |
| 定价策略分析 | `scenarios.md` | 包含定价 SOP 和参考框架 |
| 日常运营分析 | `scenarios.md` | 包含监控和预警逻辑 |
| 拓品分析 | `scenarios.md` | 包含关联推荐逻辑 |

**不要猜字段名**：如果不确定某个接口的返回字段，先加载 `reference.md` 查看。

---

## 执行标准

**优先使用脚本执行 API 调用。** 脚本内置了：
- 参数格式转换（如 topN 自动转为字符串）
- 重试逻辑（429/超时自动重试）
- 标准化错误消息
- `_query` 元数据注入（用于查询条件溯源）

**兜底方案：** 如果脚本执行失败且无法快速修复，可使用 curl 直接调用 API 作为临时方案，但需在输出中注明"本次使用 curl 直接调用"。

---

## 脚本用法

所有命令输出 JSON。进度消息输出到 stderr。

### categories — 品类树查询

```bash
python3 scripts/apiclaw.py categories --keyword "pet supplies"
python3 scripts/apiclaw.py categories --parent "Pet Supplies"
python3 scripts/apiclaw.py categories                          # 根品类
```

常用字段：`categoryName`（非 `name`）、`categoryPath`、`productCount`、`hasChildren`

### market — 市场级聚合数据

```bash
python3 scripts/apiclaw.py market --category "Pet Supplies,Dogs" --topn 10
python3 scripts/apiclaw.py market --keyword "treadmill"
```

关键输出字段：`sampleAvgMonthlySales`、`sampleAvgPrice`、`topSalesRate`（集中度）、`topBrandSalesRate`、`sampleNewSkuRate`、`sampleFbaRate`、`sampleBrandCount`

### products — 带筛选条件的选品

```bash
# 使用预设模式（14 种内置模式）
python3 scripts/apiclaw.py products --keyword "yoga mat" --mode beginner
python3 scripts/apiclaw.py products --keyword "pet toys" --mode high-demand-low-barrier

# 或使用显式筛选条件
python3 scripts/apiclaw.py products --keyword "yoga mat" --sales-min 300 --reviews-max 50
python3 scripts/apiclaw.py products --keyword "yoga mat" --growth-min 0.1 --listing-age 180

# 模式 + 覆盖参数组合（覆盖参数优先）
python3 scripts/apiclaw.py products --keyword "yoga mat" --mode beginner --price-max 30
```

可用模式：`fast-movers`、`emerging`、`single-variant`、`high-demand-low-barrier`、`long-tail`、`underserved`、`new-release`、`fbm-friendly`、`low-price`、`broad-catalog`、`selective-catalog`、`speculative`、`beginner`、`top-bsr`

### competitors — 竞品查询

```bash
python3 scripts/apiclaw.py competitors --keyword "wireless earbuds"
python3 scripts/apiclaw.py competitors --brand "Anker"
python3 scripts/apiclaw.py competitors --asin B09V3KXJPB
```

**products/competitors 共用字段（易混淆）**：

| ❌ 常见错误 | ✅ 正确字段 | 说明 |
|------------|------------|------|
| `reviewCount` | `ratingCount` | 评论数 |
| `bsr` | `bsrRank` | BSR 排名 |
| `monthlySales` | `salesMonthly` | 月销量 |

常用字段：`salesMonthly`、`bsrRank`、`ratingCount`、`rating`、`salesGrowthRate`、`listingDate`、`price`、`brand`、`categories`

> 完整字段列表见 `reference.md` → Shared Product Object

### product — 单个 ASIN 实时详情

```bash
python3 scripts/apiclaw.py product --asin B09V3KXJPB
python3 scripts/apiclaw.py product --asin B09V3KXJPB --marketplace JP
```

返回：title、brand、rating、ratingBreakdown、features（卖点）、topReviews、specifications、variants、bestsellersRank、buyboxWinner

### report — 完整市场分析（组合命令）

```bash
python3 scripts/apiclaw.py report --keyword "pet supplies"
```

自动执行：categories → market → products（前 50）→ realtime detail（前 1）。返回组合 JSON。

### opportunity — 产品机会发现（组合命令）

```bash
python3 scripts/apiclaw.py opportunity --keyword "pet supplies"
python3 scripts/apiclaw.py opportunity --keyword "pet supplies" --mode fast-movers
```

执行：categories → market → products（筛选后）→ realtime detail（前 3）。返回组合 JSON。

---

## 返回数据结构

**重要**：所有接口返回的 `.data` 字段是**数组**，不是对象。解析时使用 `.data[0]` 获取第一条记录。

```bash
# 正确 ✅
jq '.data[0].topSalesRate'

# 错误 ❌ - 会报 "Cannot index array with string"
jq '.data.topSalesRate'
```

**批量处理示例**：
```bash
# 遍历所有记录
jq '.data[] | {name: .categoryName, sales: .sampleAvgMonthlySales}'

# 取前 5 条
jq '.data[:5] | .[] | .title'
```

---

## 意图路由

| 用户说 | 执行命令 | 需要额外文件？ |
|--------|----------|----------------|
| "哪个品类有机会" | `market`（+ `categories` 确认路径） | 否 |
| "帮我查 B09XXX" / "分析 ASIN" | `product --asin XXX` | 否 |
| "中国卖家案例" | `competitors --keyword XXX --page-size 50` | `scenarios.md` → 3.4 |
| **产品评估** | | |
| "痛点" / "差评分析" | `product --asin XXX` | `scenarios.md` → 4.2 |
| "对比产品" | `competitors` 或多次 `product` | `scenarios.md` → 4.3 |
| "风险评估" / "能不能做" / "风险" | `product` + `market` + `competitors` | `scenarios.md` → 4.4 |
| "月销量" / "销量估算" | `competitors --asin XXX` | `scenarios.md` → 4.5 |
| "帮我选品" / "找产品" | `products --mode XXX`（见下方模式表） | 否 |
| "综合推荐" / "帮我选" / "卖什么好" | `products`（多模式）+ `market` | `scenarios.md` → 2.10 |

**选品模式映射（14 种）**：

| 用户意图 | 模式 | 筛选条件 |
|----------|------|----------|
| "蓝海市场" / "有痛点" / "可以改进" | `--mode underserved` | 月销≥300，评分≤3.7，6 个月内 |
| "高需求低门槛" / "容易做" / "好入手" | `--mode high-demand-low-barrier` | 月销≥300，评论≤50，6 个月内 |
| "新手友好" / "适合新卖家" / "入门级" | `--mode beginner` | 月销≥300，$15-60，FBA |
| "快速周转" / "卖得好" / "热销" | `--mode fast-movers` | 月销≥300，增长≥10% |
| "新兴产品" / "上升期" | `--mode emerging` | 月销≤600，增长≥10%，6 个月内 |
| "小而美上升期单品" / "单变体" | `--mode single-variant` | 增长≥20%，变体=1，6 个月内 |
| "长尾产品" / "小众" / "细分" | `--mode long-tail` | BSR 10K-50K，≤$30，独家卖家 |
| "新品" / "刚上架" / "新发布" | `--mode new-release` | 月销≤500，New Release 标签 |
| "低价产品" / "便宜的" | `--mode low-price` | ≤$10 |
| "头部卖家" / "畅销品" / "Top seller" | `--mode top-bsr` | BSR≤1000 |
| "自发货友好" / "FBM" | `--mode fbm-friendly` | 月销≥300，FBM |
| "铺货模式" / "广撒网" | `--mode broad-catalog` | BSR 增长≥99%，评论≤10，90 天内 |
| "精铺模式" | `--mode selective-catalog` | BSR 增长≥99%，90 天内 |
| "投机" / "跟卖机会" | `--mode speculative` | 月销≥600，卖家≥3 |
| "完整报告" / "全面分析" | `report --keyword XXX` | 否 |
| "产品机会" / "找机会" | `opportunity --keyword XXX` | 否 |
| **定价与 Listing** | | |
| "定多少钱" / "定价策略" | `market` + `products` | `scenarios.md` → 5.1 |
| "利润估算" / "利润率" | `competitors` | `scenarios.md` → 5.2 |
| "怎么写 listing" / "listing 参考" | `product --asin XXX` | `scenarios.md` → 5.3 |
| **日常运营** | | |
| "最近变化" / "市场变动" | `market` + `products` | `scenarios.md` → 6.1 |
| "竞品最近在干嘛" / "竞品动态" | `competitors --brand XXX` | `scenarios.md` → 6.2 |
| "异常预警" / "警报" | `market` + `products` | `scenarios.md` → 6.4 |
| **拓品** | | |
| "还能卖什么" / "相关产品" | `categories` + `market` | `scenarios.md` → 7.1 |
| "趋势" | `products --growth-min 0.2` | `scenarios.md` → 7.3 |
| "要不要下架" / "停售" | `competitors --asin XXX` + `market` | `scenarios.md` → 7.4 |
| **参考** | | |
| 需要确认筛选条件或字段名 | — | 加载 `reference.md` |

---

## 快速评估标准

### 市场可行性（来自 `market` 输出）

| 指标 | 良好 | 中等 | 警告 |
|------|------|------|------|
| 市场规模（avgRevenue × skuCount） | > $10M | $5–10M | < $5M |
| 集中度（topSalesRate, topN=10） | < 40% | 40–60% | > 60% |
| 新品率（sampleNewSkuRate） | > 15% | 5–15% | < 5% |
| FBA 率（sampleFbaRate） | > 50% | 30–50% | < 30% |
| 品牌数（sampleBrandCount） | > 50 | 20–50 | < 20 |

### 产品潜力（来自 `product` 输出）

| 指标 | 高 | 中 | 低 |
|------|------|------|------|
| BSR | 前 1000 | 1000–5000 | > 5000 |
| 评论数 | < 200 | 200–1000 | > 1000 |
| 评分 | > 4.3 | 4.0–4.3 | < 4.0 |
| 差评占比（1-2 星 %） | < 10% | 10–20% | > 20% |

### 销量估算兜底

当 `salesMonthly` 为空时：**月销量 ≈ 300,000 / BSR^0.65**

---

## 输出标准（强制）

**每次分析完成后必须包含数据来源块**，否则输出视为不完整：

```markdown
---
**数据来源与条件**
| 项目 | 值 |
|------|------|
| 数据来源 | APIClaw API |
| 接口 | [列出本次使用的接口，如 categories, markets/search, products/search] |
| 品类 | [查询的品类路径] |
| 时间范围 | [dateRange，如 30d] |
| 抽样方式 | [sampleType，如 by_sale_100] |
| Top N | [topN 值，如 10] |
| 排序 | [sortBy + sortOrder，如 monthlySales desc] |
| 筛选条件 | [具体参数值，如 monthlySalesMin: 300, reviewCountMax: 50] |

**数据说明**
- 月销量为基于 BSR + 抽样模型的**估算值**，非亚马逊官方数据
- 数据库接口数据有约 T+1 延迟，realtime/product 为当前实时数据
- 集中度指标基于 Top N 样本计算，不同 topN 值会得到不同结果
```

**规则**：
1. 每次分析后必须包含此块
2. 筛选条件应具体到参数值（如 `monthlySalesMin: 300, reviewCountMax: 50`）
3. 如使用多个接口，逐一列出
4. 如数据存在局限性（如缺少历史趋势），主动说明

---

## 局限性

### 本技能无法做到的

- 关键词研究 / 反查 ASIN / ABA 数据
- 流量来源分析
- 历史销量趋势（14 个月曲线）
- 历史价格 / BSR 图表
- AI 评论情感分析（可手动使用 topReviews + ratingBreakdown）

### API 数据覆盖边界

| 场景 | 覆盖 | 建议 |
|------|------|------|
| 市场数据：热门关键词 | ✅ 通常有数据 | 直接用 `--keyword` 查询 |
| 市场数据：小众/长尾关键词 | ⚠️ 可能无数据 | 改用品类路径 `--category` 查询 |
| 产品数据：活跃 ASIN | ✅ 有数据 | - |
| 产品数据：下架/变体 ASIN | ❌ 无数据 | 尝试父 ASIN 或 realtime 接口 |
| 实时数据：美国站 | ✅ 完全支持 | - |
| 实时数据：非美国站 | ⚠️ 部分字段缺失 | 核心字段可用，销量估算可能为空 |

---

## 错误处理与自检

HTTP 错误（401/402/403/404/429）由脚本自动处理，返回结构化 JSON，包含 `error.message` 和 `error.action`，AI 可直接读取并处理。

遇到问题时，运行自检：

```bash
python3 scripts/apiclaw.py check
```

测试 5 个接口中的 4 个（跳过需要有效 ASIN 的 `realtime/product`），报告可用性。

**其他常见问题**：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Cannot index array with string` | `.data` 是数组 | 使用 `.data[0].fieldName` |
| 返回空 `data: []` | 关键词无匹配 | 先用 `categories` 确认品类存在 |
| `salesMonthly: null` | 部分产品缺少销量数据 | BSR 估算：月销量 ≈ 300,000 / BSR^0.65 |
| `realtime/product` 慢 | 实时爬取 | 正常 5-30 秒，耐心等待 |

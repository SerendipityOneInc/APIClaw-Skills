# Amazon Daily Market Radar — APIClaw Agent Skill

> Set it. Forget it. Get alerted when it matters.

## What This Skill Does

Automated daily monitoring and alert system for Amazon sellers. Tracks your ASINs and competitors, detects price changes, BSR movements, new entrants, review spikes, and stock-out signals. First run establishes a baseline; subsequent runs compare against it and fire tiered alerts. Designed for unattended agent automation.

### What Makes This Different

- **Set-and-forget**: First run = baseline, every run after = smart change detection
- **Three-tier alerts**: 🔴 RED (price crash, BSR collapse, 1-star spike), 🟡 YELLOW (new competitors, moderate shifts), 🟢 GREEN (opportunities like competitor stock-outs)
- **Signal validation**: Distinguishes sustained trends (📊 7+ days) from single-day spikes (💡)
- **Cron-ready**: Built for scheduled execution with auto-monitor setup

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Daily Market Radar** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Set up daily monitoring for my ASINs: B0XXXXXXXX, B0YYYYYYYY"*
- *"帮我建立每日市场监控，关键词 'yoga mat'，追踪这 3 个 ASIN"*
- *"What changed in my market since yesterday?"*
- *"Run a daily radar check on my tracked products"*
- *"我的竞品有什么动态？"*

## What You Get

| Section | Description |
|---------|-------------|
| 🚨 Alert Summary | RED / YELLOW / GREEN alert counts |
| 🔴 RED Alerts | Critical changes requiring immediate action |
| 🟡 YELLOW Alerts | Watch-worthy shifts in competitors or market |
| 🟢 GREEN Opportunities | Favorable changes to capitalize on |
| 📊 KPI Dashboard | Today vs yesterday comparison |
| 🏃 Competitor Movement | Price, BSR, listing changes per competitor |
| 🌊 Market Shifts | Brand share, new entrants, price band migration |
| ✅ Action Items | Prioritized next steps |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category resolution |
| `markets/search` | Market-level metrics |
| `products/search` | Product landscape |
| `products/competitor-lookup` | Competitor discovery |
| `realtime/product` | Live ASIN polling |
| `reviews/analyze` | Review spike detection |
| `products/price-band-overview` | Price band shifts |
| `products/price-band-detail` | Detailed price analysis |
| `products/brand-overview` | Brand share changes |
| `products/brand-detail` | Per-brand tracking |
| `products/product-history` | Trend validation |

## Credit Cost

~15-30 credits per run (depends on number of tracked ASINs).

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.

# Amazon Competitor Intelligence Monitor — APIClaw Agent Skill

> Know your enemy. Full Scan + Quick Check. Always watching.

## What This Skill Does

Deep competitor intelligence with two operational modes. **Full Scan** delivers a complete competitive landscape — competitor matrix, brand ranking, pricing map, review battle, and battle strategy. **Quick Check** polls tracked ASINs against a saved baseline and fires tiered alerts when something changes.

### What Makes This Different

- **Dual-mode**: Full Scan (~28-35 credits) for deep analysis, Quick Check (~5-10 credits) for lightweight monitoring
- **Three-tier alerts**: 🔴 Critical (price crash, Buy Box lost), 🟡 Watch (FBA switch, rating shift), 🟢 Opportunity (stock-out, listing changes)
- **Competitive Score**: Each competitor scored 1-100 across 5 dimensions (sales, brand, listing, satisfaction, trend)
- **Auto-Monitor**: Offers scheduled Quick Check setup after every run

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Competitor Intelligence Monitor** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Analyze my competitors for ASIN B0XXXXXXXX in the yoga mat market"*
- *"Run a full competitor scan for keyword 'silicone spatula'"*
- *"Quick check my tracked competitors"*
- *"Who are the top competitors for 'dog harness' and how do I beat them?"*
- *"Monitor competitor price changes and alert me on anomalies"*

## What You Get

| Section | Description |
|---------|-------------|
| ⚔️ Battlefield Overview | Market size, player count, concentration |
| 📊 Competitor Matrix | Side-by-side comparison of all key competitors |
| 🏅 Brand Power Ranking | Brand strength scores and market share |
| 💰 Price Map | Price positioning across competitors |
| 📈 30-Day Trends | BSR, price, and sales movement |
| 💬 Review Battle | Rating, sentiment, pain points per competitor |
| 📋 Listing Audit | Image, bullet, A+ content comparison |
| 🎯 Battle Strategy | Actionable recommendations to outperform |
| 🚨 Alerts (Quick Check) | Tiered change detection vs baseline |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category resolution |
| `markets/search` | Market context |
| `products/search` | Product landscape |
| `products/competitors` | Competitor discovery |
| `realtime/product` | Live competitor data |
| `reviews/analysis` | Sentiment & pain points |
| `products/price-band-overview` | Price band context |
| `products/price-band-detail` | Detailed price analysis |
| `products/brand-overview` | Brand concentration |
| `products/brand-detail` | Per-brand breakdown |
| `products/history` | Trend analysis |

## Credit Cost

Full Scan: ~28-35 credits. Quick Check: ~5-10 credits.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.

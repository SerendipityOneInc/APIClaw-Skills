# Amazon Market Trend Scanner — APIClaw Agent Skill

> Find rising categories before everyone else.

## What This Skill Does

Scans Amazon category landscapes to discover trending subcategories, emerging niches, and market shifts. Give it a parent category and it analyzes all subcategories for demand surges, brand consolidation, new entrant waves, price band migration, and margin changes. Complements Daily Market Radar (defensive monitoring) with offensive trend discovery for product selection and market entry timing.

### What Makes This Different

- **Category-level trends**: Analyzes across ALL subcategories under a parent, not just individual products
- **7 key metrics per subcategory**: Sales, new SKU rate, brand concentration, avg price, gross margin, total SKUs, FBA rate
- **Trend signals**: Demand surge 🔴, red ocean warning 🔴, new entrant wave 🟡, brand loosening 🟡, price/margin shifts 🟡
- **Dual mode**: Full Scan for discovery, Quick Check for scheduled monitoring with auto-alerts
- **Emerging product detection**: Scans hot subcategories for emerging and new-release products

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Market Trend Scanner** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Scan Pet Supplies for trending subcategories"*
- *"什么品类在涨？扫一下 Home & Kitchen"*
- *"Which subcategories under Sports & Outdoors are growing fastest?"*
- *"帮我做品类趋势扫描，看看哪些细分在起势"*
- *"Find emerging niches in Beauty & Personal Care"*

## What You Get

| Section | Description |
|---------|-------------|
| 📊 Trend Dashboard | All subcategories with 7 key metrics |
| 🔥 Hot Categories TOP 5 | Fastest-growing subcategories ranked |
| 🆕 New Entrants Scan | Emerging and new-release products in hot categories |
| ⚠️ Risk Alerts | Red ocean warnings, demand surges, margin compression |
| 📋 Subcategory Detail | Deep dive per hot category |
| 🎯 Next Steps | Market entry timing and strategy |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category tree resolution |
| `markets/search` | Subcategory-level market metrics (paginated) |
| `products/search` | Emerging and new-release product scanning |

## Credit Cost

Full Scan: ~40-60 credits (~2-3 per subcategory × 20). Quick Check: ~20-30 credits.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.

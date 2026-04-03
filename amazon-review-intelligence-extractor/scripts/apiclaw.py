#!/usr/bin/env python3
# ============================================================
# 唯一真源 — 请勿直接编辑各 amazon-* skill 目录下的副本
# 真源位置: apiclaw/scripts/apiclaw.py
# 同步方式: pre-commit hook 自动复制 或 bash scripts/sync-scripts.sh
# ============================================================
"""
APIClaw CLI — Amazon Product Research via APIClaw API

Single-script interface for all 5 APIClaw endpoints + composite workflows.
Handles authentication, retries, rate limits, parameter quirks, and output formatting.

Usage:
    python apiclaw.py categories --keyword "pet supplies"
    python apiclaw.py market --category "Pet Supplies" --topn 10
    python apiclaw.py products --keyword "yoga mat" --mode beginner
    python apiclaw.py competitors --keyword "wireless earbuds"
    python apiclaw.py product --asin B09V3KXJPB
    python apiclaw.py report --keyword "pet supplies"
    python apiclaw.py opportunity --keyword "pet supplies"

Environment:
    APICLAW_API_KEY — Required. Get one at https://apiclaw.io/en/api-keys
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_URL = "https://api.apiclaw.io/openapi/v2"  # APIClaw API base URL
API_DOCS = "https://api.apiclaw.io/api-docs"   # API documentation URL
MAX_RETRIES = 2       # Maximum number of retry attempts for failed requests
RETRY_DELAY = 2       # Initial retry delay in seconds; doubles on 429 (rate limit)
REQUEST_TIMEOUT = 60  # Request timeout in seconds; realtime/product can be slow (up to 30s)

# 14 built-in product selection modes
# Each maps to a set of products/search filter parameters
PRODUCT_MODES = {
    "fast-movers":              {"monthlySalesMin": 300, "salesGrowthRateMin": 0.1},
    "emerging":                 {"monthlySalesMax": 600, "salesGrowthRateMin": 0.1, "listingAge": "180"},
    "single-variant":           {"salesGrowthRateMin": 0.2, "variantCountMax": 1, "listingAge": "180"},
    "high-demand-low-barrier":  {"monthlySalesMin": 300, "ratingCountMax": 50, "listingAge": "180"},
    "long-tail":                {"bsrMin": 10000, "bsrMax": 50000, "priceMax": 30, "sellerCountMax": 1, "monthlySalesMax": 300},
    "underserved":              {"monthlySalesMin": 300, "ratingMax": 3.7, "listingAge": "180"},
    "new-release":              {"monthlySalesMax": 500, "badges": ["New Release"], "fulfillment": ["FBA", "FBM"]},
    "fbm-friendly":             {"monthlySalesMin": 300, "fulfillment": ["FBM"], "listingAge": "180"},
    "low-price":                {"priceMax": 10},
    "broad-catalog":            {"bsrGrowthRateMin": 0.99, "ratingCountMax": 10, "listingAge": "90"},
    "selective-catalog":        {"bsrGrowthRateMin": 0.99, "listingAge": "90"},
    "speculative":              {"monthlySalesMin": 600, "sellerCountMin": 3, "listingAge": "180"},
    "beginner":                 {"monthlySalesMin": 300, "priceMin": 15, "priceMax": 60, "fulfillment": ["FBA"],
                                 "salesGrowthRateMin": 0.03, "listingAge": "365",
                                 "excludeKeywords": "Brow,Air Fryer,Body Fragrance Mist,Ornament,Ivory,Bed Comforter,Biker Shorts,Mens Dress Shoe,Charms,Dumbbell,Gaming Chair,Skipping Rope,Hoops,Plus Hoola,Kids Bike Helmet,Socks,Cushion,Camping Hammock,Double Leggings,Yoga,Hand Warmers,Trail Camera,Water Bottle,Insulated Food,Pillow,Pillows,iPhone,Dog Bark Collar,Leg Covers,Leg Cover,Laptop Stand,Pet Briefs,Brief,Hangers,Hanger,Slip Rug Pad,rossbody,Fanny Pack,Bedding,Dog Harness,Sweet Water Decor,Eyeshadow,Cotton Sleepsack,Swaddle,Chocolate Bra,Wireless Bed Sheet Set,Car Windshield Curtain,Curtains,Wallet,Green Tea,Picture Frame,Womens,Women Fan,Bottle,Essential Oil,Tumbler,YETI,Vitamin,Vitamins,Face Mask,Led Strip,Pocket,Women's Watch,Waffle Case,Gloves,Shorts,Short Yoga,StrawExpert,Wrap Around Pillowcases,Cup,Bath Mats,Bedsure,Pillowcase,Bathroom,Shower,Milk Frother,Masks,Bug Zapper,Touchless Thermometer,Cat Litter Mat,Probiotics,Smart Plug,Natural Vitality Bottle,Christmas,Sleeveless,Shape Shifting Box,Refrigerator Organizer,Hydration Multiplier,Standard Mouth,Gift Box,USB C,Superhero,Digital Caliper,Massage Gun,Fidget Toys,Garden Hose,Cookie,Blanket,Protein Bars,Caramel Cashew,String Lights,Umbrella,Wearable Blanket,Diapers,Halloween,Flying Toys,Laundry Basket,Kitchen Faucet,Citrulline Malate,Onesie,Pajamas,Nail Polish Kit,fairy finder,Allergy,Immune Supplement,Frying Pan,Tablecloth,Electric Knife,Butter Dish,Dancing Cactus,Maya Mint,ice Cream,Christmas Tree,Liquid Motion Lamp,Stuffed Animal,Plush Bed Comforter,Journal,Women's,Sleeveless Wrap,Supplement,Screen Magnifier,Foot Massager,Machine,Santa,Anime Heroes,Air Mattress,Three Barrel Curling,3D Printer Filament,Power Strip,Rechargeable Toothbrush,Hooded Bathrobe,Sleepwear,Baby Einstein,Vinyl,Plastic Plates,Doorbell,Month Planner,Wooden Balls,Arceus,Wipes,Perfume,Rings,Bore Sight,Fishing Lures,Ear Protection,Firewood Rack,Sling Bag,Resistance Bands,Belt,Backpacks,Silver Slides,Whiteboard,Sports Bra,Cover,Jade Stud,Earrings,Necklace,Snow Shovel,Computer Desk,Dog Pee Pads,Turtleneck,Glasses,Spa,Up Balancer"},
    "top-bsr":                  {"subBsrMax": 1000},
}

# ─── API Client ──────────────────────────────────────────────────────────────

def get_api_key():
    """
    Get API key from environment variable or config file.

    Priority:
    1. Environment variable APICLAW_API_KEY
    2. Config file config.json in the skill directory (next to scripts/)
    """
    # Try environment variable first
    key = os.environ.get("APICLAW_API_KEY", "").strip()
    if key:
        return key

    # Try config file in skill directory (parent of scripts/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)  # go up from scripts/ to skill root
    config_path = os.path.join(skill_dir, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                key = config.get("api_key", "").strip()
                if key:
                    return key
        except (json.JSONDecodeError, IOError) as e:
            print(f"WARNING: Failed to read config file: {e}", file=sys.stderr)

    # No key found
    print("ERROR: API Key not found.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Please configure your API Key using one of these methods:", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Method 1: Config file (recommended)", file=sys.stderr)
    print(f"    Create config.json in the skill directory: {skill_dir}", file=sys.stderr)
    print('    Content: {"api_key": "hms_live_yourkey"}', file=sys.stderr)
    print("", file=sys.stderr)
    print("  Method 2: Environment variable", file=sys.stderr)
    print("    export APICLAW_API_KEY='hms_live_yourkey'", file=sys.stderr)
    print("", file=sys.stderr)
    print("Get a free key at https://apiclaw.io/en/api-keys", file=sys.stderr)
    sys.exit(1)


def api_call(endpoint: str, params: dict) -> dict:
    """
    Make a POST request to APIClaw API with retry and error handling.

    Returns the parsed JSON response on success, with _query metadata injected.
    Exits with a clear error message on failure.
    """
    url = f"{BASE_URL}/{endpoint}"
    api_key = get_api_key()

    # Clean params: remove None values
    params = {k: v for k, v in params.items() if v is not None}

    # Quirk: topN and newProductPeriod must be strings
    for str_field in ("topN", "newProductPeriod"):
        if str_field in params and not isinstance(params[str_field], str):
            params[str_field] = str(params[str_field])

    # Save the actual params sent to API (for _query metadata)
    actual_params = dict(params)

    body = json.dumps(params).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "APIClaw-CLI/1.0 (Python)",
    }

    delay = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("success"):
                    # Inject _query metadata so AI knows exactly what was sent
                    data["_query"] = {
                        "endpoint": endpoint,
                        "params": actual_params,
                    }
                    return data
                else:
                    err = data.get("error", {})
                    err_msg = err.get('message', json.dumps(err))
                    print(f"API error: {err.get('code', 'unknown')} — {err_msg}", file=sys.stderr)
                    # Return error as structured result instead of exiting
                    # This allows composite commands to continue with other steps
                    data["_query"] = {"endpoint": endpoint, "params": actual_params}
                    return data
        except urllib.error.HTTPError as e:
            status = e.code
            if status == 401:
                return _error_result(401, "API Key invalid or expired",
                    "Check your API Key or get a new one at https://apiclaw.io/en/api-keys",
                    endpoint, actual_params)
            elif status == 402:
                return _error_result(402, "API quota exhausted or subscription expired",
                    "Check your plan at https://apiclaw.io/en/api-keys or provide a new Key",
                    endpoint, actual_params)
            elif status == 429:
                if attempt < MAX_RETRIES:
                    print(f"Rate limited (429). Waiting {delay}s before retry {attempt}/{MAX_RETRIES}...", file=sys.stderr)
                    time.sleep(delay)
                    delay *= 2
                    continue
                else:
                    return _error_result(429, "Rate limit exceeded after retries",
                        "Try again later or reduce request frequency",
                        endpoint, actual_params)
            elif status == 404:
                return _error_result(404, f"Endpoint '{endpoint}' not found",
                    f"Check {API_DOCS} for current endpoints",
                    endpoint, actual_params)
            else:
                if attempt < MAX_RETRIES:
                    print(f"HTTP {status}. Retrying {attempt}/{MAX_RETRIES}...", file=sys.stderr)
                    time.sleep(delay)
                    continue
                else:
                    return _error_result(status, f"HTTP {status} after {MAX_RETRIES} attempts",
                        "Check network or try again later",
                        endpoint, actual_params)
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"Request failed: {e}. Retrying {attempt}/{MAX_RETRIES}...", file=sys.stderr)
                time.sleep(delay)
                continue
            else:
                return _error_result(0, f"Request failed: {e}",
                    "Check network connection",
                    endpoint, actual_params)

    return _error_result(0, "Unexpected retry loop exit", "This should not happen", endpoint, actual_params)


def _error_result(status: int, message: str, action: str, endpoint: str, params: dict) -> dict:
    """
    Build a structured error result instead of sys.exit().
    This lets AI read the error from JSON stdout and take appropriate action.
    """
    print(f"ERROR: {message}", file=sys.stderr)
    return {
        "success": False,
        "error": {
            "status": status,
            "message": message,
            "action": action,
        },
        "_query": {
            "endpoint": endpoint,
            "params": params,
        },
    }


def output(data, fmt="json"):
    """Print output in the requested format."""
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif fmt == "compact":
        print(json.dumps(data, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


# ─── Helper: parse category string ──────────────────────────────────────────

def parse_category(cat_str: str) -> list:
    """Parse category path string into a list.
    
    Supported formats:
      - 'Pet Supplies,Dogs,Toys'           (comma-separated)
      - 'Pet Supplies > Dogs > Toys'       (spaced arrow)
      - 'Pet Supplies>Dogs>Toys'           (bare arrow, no spaces)
    """
    if not cat_str:
        return []
    # Support comma, ' > ' (spaced), and '>' (bare) separators
    if " > " in cat_str:
        return [c.strip() for c in cat_str.split(" > ")]
    if ">" in cat_str:
        return [c.strip() for c in cat_str.split(">")]
    return [c.strip() for c in cat_str.split(",")]


# ─── Subcommands ─────────────────────────────────────────────────────────────

def cmd_categories(args):
    """Query the Amazon category tree."""
    params = {}
    if args.keyword:
        params["categoryKeyword"] = args.keyword
    elif args.category:
        params["categoryPath"] = parse_category(args.category)
    elif args.parent:
        params["parentCategoryPath"] = parse_category(args.parent)
    # else: no params → root categories

    result = api_call("categories", params)
    output(result, args.format)


def cmd_market(args):
    """Search market-level aggregate data for a category."""
    params = {}
    if args.category:
        params["categoryPath"] = parse_category(args.category)
    if args.keyword:
        params["categoryKeyword"] = args.keyword
    if args.topn:
        params["topN"] = str(args.topn)
    if args.page_size:
        params["pageSize"] = args.page_size
    if args.sort:
        params["sortBy"] = args.sort
    if args.order:
        params["sortOrder"] = args.order

    result = api_call("markets/search", params)
    output(result, args.format)


def cmd_products(args):
    """Search products with filters (product selection / 选品)."""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["categoryPath"] = parse_category(args.category)

    # Apply mode preset filters
    if args.mode:
        mode_key = args.mode.lower().replace(" ", "-").replace("_", "-")
        if mode_key in PRODUCT_MODES:
            params.update(PRODUCT_MODES[mode_key])
        else:
            print(f"ERROR: Unknown mode '{args.mode}'.", file=sys.stderr)
            print(f"Available modes: {', '.join(sorted(PRODUCT_MODES.keys()))}", file=sys.stderr)
            sys.exit(1)

    # Override with explicit filters
    for attr in ("monthlySalesMin", "monthlySalesMax", "ratingCountMin", "ratingCountMax",
                 "priceMin", "priceMax", "ratingMin", "ratingMax", "bsrMin", "bsrMax",
                 "salesGrowthRateMin", "salesGrowthRateMax", "sellerCountMin", "sellerCountMax",
                 "variantCountMin", "variantCountMax"):
        val = getattr(args, attr.replace("Min", "_min").replace("Max", "_max")
                      .replace("monthly", "monthly_").replace("review", "review_")
                      .replace("sales", "sales_").replace("Growth", "_growth_")
                      .replace("Rate", "rate_").replace("price", "price_")
                      .replace("rating", "rating_").replace("bsr", "bsr_")
                      .replace("seller", "seller_").replace("Count", "_count_")
                      .replace("variant", "variant_"), None)
        # Simplified: just use the argparse names directly

    if args.sales_min is not None:
        params["monthlySalesMin"] = args.sales_min
    if args.sales_max is not None:
        params["monthlySalesMax"] = args.sales_max
    if args.ratings_min is not None:
        params["ratingCountMin"] = args.ratings_min
    if args.ratings_max is not None:
        params["ratingCountMax"] = args.ratings_max
    if args.price_min is not None:
        params["priceMin"] = args.price_min
    if args.price_max is not None:
        params["priceMax"] = args.price_max
    if args.rating_min is not None:
        params["ratingMin"] = args.rating_min
    if args.rating_max is not None:
        params["ratingMax"] = args.rating_max
    if args.growth_min is not None:
        params["salesGrowthRateMin"] = args.growth_min
    if args.listing_age:
        params["listingAge"] = args.listing_age
    if args.badges:
        params["badges"] = args.badges
    if args.fulfillment:
        params["fulfillment"] = args.fulfillment
    if args.include_brands:
        params["includeBrands"] = args.include_brands
    if args.exclude_brands:
        params["excludeBrands"] = args.exclude_brands

    params["sortBy"] = args.sort or "atLeastMonthlySales"
    params["sortOrder"] = args.order or "desc"
    params["pageSize"] = args.page_size or 20

    result = api_call("products/search", params)

    # Client-side ratingCount filter
    # Apply filtering locally to ensure mode presets work correctly
    if result and result.get("success") and isinstance(result.get("data"), list):
        rc_min = params.get("ratingCountMin")
        rc_max = params.get("ratingCountMax")
        if rc_min is not None or rc_max is not None:
            original_count = len(result["data"])
            filtered = result["data"]
            if rc_max is not None:
                filtered = [p for p in filtered if (p.get("ratingCount") or 0) <= rc_max]
            if rc_min is not None:
                filtered = [p for p in filtered if (p.get("ratingCount") or 0) >= rc_min]
            result["data"] = filtered
            if len(filtered) < original_count:
                result["_clientFilter"] = {
                    "reason": "ratingCount filter applied client-side",
                    "before": original_count,
                    "after": len(filtered)
                }

    output(result, args.format)


def cmd_competitors(args):
    """Look up competitors by keyword, brand, ASIN, or category."""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.brand:
        params["brand"] = args.brand
    if args.asin:
        params["asin"] = args.asin
    if args.category:
        params["categoryPath"] = parse_category(args.category)

    params["dateRange"] = args.date_range or "30d"
    params["marketplace"] = args.marketplace or "US"
    params["page"] = args.page or 1
    params["sortBy"] = args.sort or "atLeastMonthlySales"
    params["sortOrder"] = args.order or "desc"
    params["pageSize"] = args.page_size or 20

    result = api_call("products/competitor-lookup", params)
    output(result, args.format)


def cmd_product(args):
    """Get real-time product details for a single ASIN."""
    if not args.asin:
        print("ERROR: --asin is required for product command.", file=sys.stderr)
        sys.exit(1)
    params = {"asin": args.asin}
    if args.marketplace:
        params["marketplace"] = args.marketplace

    result = api_call("realtime/product", params)
    output(result, args.format)


def cmd_report(args):
    """
    Composite workflow: Full Market Report.
    Runs categories → markets/search → products/search → realtime/product (top 1).
    Outputs combined JSON with all results.
    """
    keyword = args.keyword
    if not keyword:
        print("ERROR: --keyword is required for report command.", file=sys.stderr)
        sys.exit(1)

    topn = str(args.topn or 10)
    results = {}

    # Step 1: Confirm category
    print("Step 1/4: Confirming category...", file=sys.stderr)
    cat_result = api_call("categories", {"categoryKeyword": keyword})
    results["categories"] = cat_result
    cat_data = cat_result.get("data", [])

    # Use the first matching category path
    category_path = None
    if cat_data:
        category_path = cat_data[0].get("categoryPath")

    # Step 2: Market data
    print("Step 2/4: Pulling market data...", file=sys.stderr)
    market_params = {"topN": topn}
    if category_path:
        market_params["categoryPath"] = category_path
    else:
        market_params["categoryKeyword"] = keyword
    market_result = api_call("markets/search", market_params)
    results["market"] = market_result

    # Step 3: Top products
    print("Step 3/4: Searching top products...", file=sys.stderr)
    products_result = api_call("products/search", {
        "keyword": keyword,
        "sortBy": "monthlySales",
        "sortOrder": "desc",
        "pageSize": 50,
    })
    results["products"] = products_result

    # Step 4: Top 1 ASIN detail
    product_data = products_result.get("data", [])
    if product_data:
        top_asin = product_data[0].get("asin")
        if top_asin:
            print(f"Step 4/4: Getting details for top ASIN {top_asin}...", file=sys.stderr)
            detail_result = api_call("realtime/product", {"asin": top_asin, "marketplace": "US"})
            results["topProductDetail"] = detail_result
    else:
        print("Step 4/4: No products found, skipping detail.", file=sys.stderr)

    print("Done.", file=sys.stderr)
    output(results, args.format)


def cmd_opportunity(args):
    """
    Composite workflow: Product Opportunity Discovery.
    Runs categories → markets/search → products/search (filtered) → realtime/product (top 3).
    """
    keyword = args.keyword
    if not keyword:
        print("ERROR: --keyword is required for opportunity command.", file=sys.stderr)
        sys.exit(1)

    results = {}

    # Step 1: Confirm category
    print("Step 1/4: Confirming category...", file=sys.stderr)
    cat_result = api_call("categories", {"categoryKeyword": keyword})
    results["categories"] = cat_result
    cat_data = cat_result.get("data", [])
    category_path = cat_data[0].get("categoryPath") if cat_data else None

    # Step 2: Market validation
    print("Step 2/4: Validating market...", file=sys.stderr)
    market_params = {"topN": "10"}
    if category_path:
        market_params["categoryPath"] = category_path
    else:
        market_params["categoryKeyword"] = keyword
    results["market"] = api_call("markets/search", market_params)

    # Step 3: Product candidates (high demand, low barrier)
    print("Step 3/4: Discovering product candidates...", file=sys.stderr)
    search_params = {
        "keyword": keyword,
        "monthlySalesMin": 300,
        "ratingCountMax": 50,
        "sortBy": "monthlySales",
        "sortOrder": "desc",
        "pageSize": 20,
    }
    # Apply mode override if specified
    if args.mode and args.mode in PRODUCT_MODES:
        search_params.update(PRODUCT_MODES[args.mode])
    results["products"] = api_call("products/search", search_params)

    # Step 4: Detail for top 3 ASINs
    product_data = results["products"].get("data", [])
    details = []
    for p in product_data[:3]:
        asin = p.get("asin")
        if asin:
            print(f"Step 4/4: Getting details for {asin}...", file=sys.stderr)
            details.append(api_call("realtime/product", {"asin": asin, "marketplace": "US"}))
    results["topProductDetails"] = details

    print("Done.", file=sys.stderr)
    output(results, args.format)


def cmd_market_entry(args):
    """
    Composite workflow: Full Market Entry Analysis.
    Runs ALL 11 endpoints in the correct order with fallback logic.
    Outputs a single structured JSON with all data needed for the report.
    
    Steps:
      1. Market landscape: market + brand-overview + brand-detail
      2. Price structure: price-band-overview + price-band-detail
      3. Product supply: products/search (5 pages, 100 records)
      4. Competitors: competitor-lookup + realtime/product (Top 5)
      5. Trends: product-history (Top 3, with ASIN retry)
      6. Consumer insights: reviews/analyze (3x category mode, fallback to ASIN)
    """
    keyword = args.keyword
    category = args.category
    if not keyword and not category:
        print("ERROR: --keyword or --category is required.", file=sys.stderr)
        sys.exit(1)

    results = {"meta": {"keyword": keyword, "category": category, "steps_completed": []}}
    category_path = parse_category(category) if category else None

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        """Call API and return result. Never exit on error."""
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # ── Step 0.5: Category Resolution ──
    if not category_path and keyword:
        log("Step 0.5: Resolving category...")
        cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
        results["categories"] = cat_result
        cat_data = cat_result.get("data", [])
        if cat_data:
            category_path = cat_data[0].get("categoryPath")
            log(f"  → Locked category: {' > '.join(category_path)}")
        else:
            log("  ⚠️ No category match, will use keyword-only queries")

    results["meta"]["resolved_category"] = category_path

    # ── Step 1: Market Landscape (3 calls) ──
    log("Step 1/6: Market landscape...")
    
    # 1a. Market aggregate
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    # 1b. Brand overview (keyword + category, fallback to category-only)
    brand_ov_params = {"pageSize": 20}
    if category_path:
        brand_ov_params["categoryPath"] = category_path
    if keyword:
        brand_ov_params["keyword"] = keyword
    r = safe_call("products/brand-overview", brand_ov_params, "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            log("  → brand-overview empty with keyword+category, retrying category-only...")
            brand_ov_params.pop("keyword", None)
            r = safe_call("products/brand-overview", brand_ov_params, "brand-overview (category-only)")
    results["brand_overview"] = r

    # 1c. Brand detail
    brand_dt_params = {"pageSize": 20}
    if category_path:
        brand_dt_params["categoryPath"] = category_path
    if keyword:
        brand_dt_params["keyword"] = keyword
    r = safe_call("products/brand-detail", brand_dt_params, "brand-detail")
    if not r.get("data") or not r.get("data", {}).get("brands"):
        if keyword and category_path:
            log("  → brand-detail empty with keyword+category, retrying category-only...")
            brand_dt_params.pop("keyword", None)
            r = safe_call("products/brand-detail", brand_dt_params, "brand-detail (category-only)")
    results["brand_detail"] = r
    results["meta"]["steps_completed"].append("market_landscape")

    # ── Step 2: Price Structure (2 calls) ──
    log("Step 2/6: Price structure...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword

    r = safe_call("products/price-band-overview", dict(pb_params), "price-band-overview")
    if not r.get("data"):
        if keyword and category_path:
            pb_params_co = {k: v for k, v in pb_params.items() if k != "keyword"}
            r = safe_call("products/price-band-overview", pb_params_co, "price-band-overview (category-only)")
    results["price_band_overview"] = r

    r = safe_call("products/price-band-detail", dict(pb_params), "price-band-detail")
    if not r.get("data"):
        if keyword and category_path:
            pb_params_co = {k: v for k, v in pb_params.items() if k != "keyword"}
            r = safe_call("products/price-band-detail", pb_params_co, "price-band-detail (category-only)")
    results["price_band_detail"] = r
    results["meta"]["steps_completed"].append("price_structure")

    # ── Step 3: Product Supply (5 pages = 100 records) ──
    log("Step 3/6: Product supply (5 pages)...")
    all_products = []
    total_products = 0
    for page in range(1, 6):
        prod_params = {"pageSize": 20, "page": page, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
        if keyword:
            prod_params["keyword"] = keyword
        if category_path:
            prod_params["categoryPath"] = category_path
        r = safe_call("products/search", prod_params, f"products page {page}")
        page_data = r.get("data", [])
        if isinstance(page_data, list):
            all_products.extend(page_data)
        if page == 1:
            total_products = r.get("meta", {}).get("total", 0)
        if not page_data:
            log(f"  → Page {page} empty, stopping pagination")
            break
    results["products"] = {"items": all_products, "total": total_products, "pages_fetched": page}
    log(f"  → {len(all_products)} products fetched (total available: {total_products})")
    results["meta"]["steps_completed"].append("product_supply")

    # ── Step 4: Top Competitor Deep-Dive ──
    log("Step 4/6: Competitor deep-dive...")
    
    # 4a. Competitor lookup
    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitor-lookup", comp_params, "competitors")

    # 4b. Pick Top 5 ASINs for realtime (deduplicate by parentAsin)
    seen_parents = set()
    top_asins = []
    for p in all_products:
        parent = p.get("parentAsin") or p.get("asin")
        if parent not in seen_parents:
            seen_parents.add(parent)
            top_asins.append(p.get("asin"))
        if len(top_asins) >= 5:
            break

    realtime_details = []
    for asin in top_asins:
        log(f"  → Realtime: {asin}")
        r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"realtime {asin}")
        if r.get("success") is not False:
            realtime_details.append(r)
    results["realtime"] = realtime_details
    results["meta"]["steps_completed"].append("competitor_deepdive")

    # ── Step 5: Trend Analysis ──
    log("Step 5/6: Trend analysis...")
    today = time.strftime("%Y-%m-%d")
    thirty_days_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))

    # Try product-history with Top 3, fallback to older ASINs
    history_data = []
    tried_asins = set()
    
    # Sort products by listingDate (oldest first) for fallback
    products_by_age = sorted(
        [p for p in all_products if p.get("listingDate")],
        key=lambda x: x.get("listingDate", "9999")
    )

    # Round 1: Top 3 by sales
    round1_asins = top_asins[:3]
    if round1_asins:
        tried_asins.update(round1_asins)
        r = safe_call("products/product-history", {
            "asins": round1_asins,
            "startDate": thirty_days_ago,
            "endDate": today,
        }, "product-history round 1")
        history_data = r.get("data", [])

    # Round 2: Try oldest products if round 1 was empty
    if not history_data:
        round2_asins = [p.get("asin") for p in products_by_age if p.get("asin") not in tried_asins][:5]
        if round2_asins:
            log(f"  → Round 1 empty, trying older ASINs: {round2_asins}")
            tried_asins.update(round2_asins)
            r = safe_call("products/product-history", {
                "asins": round2_asins,
                "startDate": thirty_days_ago,
                "endDate": today,
            }, "product-history round 2")
            history_data = r.get("data", [])

    results["product_history"] = {"data": history_data, "asins_tried": list(tried_asins)}
    log(f"  → {len(history_data)} history records from {len(tried_asins)} ASINs tried")
    results["meta"]["steps_completed"].append("trend_analysis")

    # ── Step 6: Consumer Insights ──
    log("Step 6/6: Consumer insights...")
    review_results = {}
    label_types = ["painPoints", "buyingFactors", "improvements"]

    # Priority 1: Category mode
    category_mode_success = True
    if category_path:
        for lt in label_types:
            log(f"  → reviews/analyze category mode: {lt}")
            r = safe_call("reviews/analyze", {
                "categoryPath": category_path,
                "mode": "category",
                "labelType": lt,
                "period": "6m",
            }, f"reviews {lt}")
            if r.get("success") is False or not r.get("data", {}).get("consumerInsights"):
                category_mode_success = False
                log(f"  ⚠️ Category mode failed for {lt}")
                break
            review_results[lt] = r

    # Priority 2: ASIN mode (if category failed)
    if not category_mode_success or not category_path:
        log("  → Falling back to ASIN mode...")
        # Pick ASINs with ratingCount >= 50
        review_asins = [p.get("asin") for p in all_products if (p.get("ratingCount") or 0) >= 50][:3]
        if review_asins:
            for lt in label_types:
                if lt in review_results:
                    continue
                log(f"  → reviews/analyze ASIN mode: {lt} ({review_asins})")
                r = safe_call("reviews/analyze", {
                    "asins": review_asins,
                    "mode": "asin",
                    "labelType": lt,
                    "period": "6m",
                }, f"reviews ASIN {lt}")
                review_results[lt] = r

    results["reviews"] = review_results
    results["meta"]["review_mode"] = "category" if category_mode_success and category_path else "asin"
    results["meta"]["steps_completed"].append("consumer_insights")

    # ── Summary ──
    log(f"\n✅ Market entry analysis complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    log(f"   Products: {len(all_products)} | Realtime: {len(realtime_details)} | History: {len(history_data)}")
    log(f"   Reviews mode: {results['meta']['review_mode']}")
    
    output(results, args.format)


def cmd_competitor_analysis(args):
    """
    Composite workflow: Competitor War Room.
    Discovers and deeply analyzes competitors with battle-ready insights.
    """
    keyword = args.keyword
    my_asin = getattr(args, 'my_asin', None)
    category = args.category

    if not keyword and not my_asin:
        print("ERROR: --keyword or --my-asin is required.", file=sys.stderr)
        sys.exit(1)

    category_path = parse_category(category) if category else None
    results = {"meta": {"keyword": keyword, "my_asin": my_asin, "category": category, "steps_completed": []}}

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # Category Resolution
    if not category_path:
        if keyword:
            log("Step 0: Resolving category...")
            cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
            results["categories"] = cat_result
            cat_data = cat_result.get("data", [])
            if cat_data:
                category_path = cat_data[0].get("categoryPath")
    results["meta"]["resolved_category"] = category_path

    # Step 1: Competitor Discovery
    log("Step 1/7: Competitor discovery...")
    prod_params = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["products"] = safe_call("products/search", prod_params, "products")

    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitor-lookup", comp_params, "competitors")
    results["meta"]["steps_completed"].append("competitor_discovery")

    # Step 2: Market Context
    log("Step 2/7: Market context...")
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    brand_params = {"pageSize": 20}
    if category_path:
        brand_params["categoryPath"] = category_path
    if keyword:
        brand_params["keyword"] = keyword
    r = safe_call("products/brand-overview", dict(brand_params), "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            r = safe_call("products/brand-overview", {"categoryPath": category_path, "pageSize": 20}, "bo (cat-only)")
    results["brand_overview"] = r
    r = safe_call("products/brand-detail", dict(brand_params), "brand-detail")
    if not r.get("data") or not r.get("data", {}).get("brands"):
        if keyword and category_path:
            r = safe_call("products/brand-detail", {"categoryPath": category_path, "pageSize": 20}, "bd (cat-only)")
    results["brand_detail"] = r
    results["meta"]["steps_completed"].append("market_context")

    # Step 3: Price Landscape
    log("Step 3/7: Price landscape...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword
    r = safe_call("products/price-band-overview", dict(pb_params), "pbo")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-overview", {"categoryPath": category_path, "pageSize": 20}, "pbo (cat)")
    results["price_band_overview"] = r
    r = safe_call("products/price-band-detail", dict(pb_params), "pbd")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-detail", {"categoryPath": category_path, "pageSize": 20}, "pbd (cat)")
    results["price_band_detail"] = r
    results["meta"]["steps_completed"].append("price_landscape")

    # Step 4: Deep Realtime for Top 10
    log("Step 4/7: Realtime deep-dive (Top 10)...")
    all_products = results["products"].get("data", [])
    if not isinstance(all_products, list):
        all_products = []
    seen = set()
    top_asins = []
    for p in all_products:
        parent = p.get("parentAsin") or p.get("asin")
        asin = p.get("asin")
        if parent not in seen:
            seen.add(parent)
            if my_asin and asin == my_asin:
                continue
            top_asins.append(asin)
        if len(top_asins) >= 10:
            break

    realtime_details = []
    for asin in top_asins:
        log(f"  → {asin}")
        r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"rt {asin}")
        realtime_details.append({"asin": asin, "result": r})
    results["realtime"] = realtime_details
    results["meta"]["steps_completed"].append("realtime_deepdive")

    # Step 5: Historical Trends
    log("Step 5/7: Historical trends...")
    today = time.strftime("%Y-%m-%d")
    thirty_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    history_asins = ([my_asin] if my_asin else []) + top_asins[:5]
    r = safe_call("products/product-history", {
        "asins": history_asins[:8], "startDate": thirty_ago, "endDate": today
    }, "product-history")
    results["product_history"] = {"data": r.get("data", []), "asins_tried": history_asins[:8]}
    results["meta"]["steps_completed"].append("historical_trends")

    # Step 6: Review Intelligence
    log("Step 6/7: Review intelligence...")
    review_results = {}
    for asin in top_asins[:5]:
        r = safe_call("reviews/analyze", {
            "asins": [asin], "mode": "asin", "labelType": "painPoints", "period": "6m"
        }, f"reviews {asin}")
        if r.get("data") and r.get("data", {}).get("consumerInsights"):
            review_results[asin] = r
    if not review_results and category_path:
        log("  → Falling back to category mode...")
        for lt in ["painPoints", "buyingFactors"]:
            review_results[lt] = safe_call("reviews/analyze", {
                "categoryPath": category_path, "mode": "category", "labelType": lt, "period": "6m"
            }, f"reviews cat {lt}")
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_intelligence")

    # Step 7: Brand Drill-Down
    log("Step 7/7: Brand drill-down...")
    brands = results.get("brand_detail", {}).get("data", {}).get("brands", [])
    if brands:
        top_brand = brands[0].get("brandName")
        if top_brand:
            bp = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
            if keyword:
                bp["keyword"] = keyword
            if category_path:
                bp["categoryPath"] = category_path
            bp["includeBrands"] = top_brand
            results["top_brand_products"] = safe_call("products/search", bp, f"brand {top_brand}")
    results["meta"]["steps_completed"].append("brand_drilldown")

    log(f"\n✅ Competitor analysis complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    log(f"   Competitors: {len(realtime_details)} | Reviews: {len(review_results)}")
    output(results, args.format)


def cmd_pricing_analysis(args):
    """
    Composite workflow: Pricing Analysis.
    Runs: realtime(my_asin) → price-band → products/competitors → market/brand → history → realtime(top5) → reviews
    """
    my_asin = args.my_asin
    keyword = args.keyword
    category = args.category

    if not my_asin:
        print("ERROR: --my-asin is required.", file=sys.stderr)
        sys.exit(1)
    if not keyword and not category:
        print("ERROR: --keyword or --category is required.", file=sys.stderr)
        sys.exit(1)

    category_path = parse_category(category) if category else None
    results = {"meta": {"my_asin": my_asin, "keyword": keyword, "category": category, "steps_completed": []}}

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # Step 0.5: Category Resolution
    if not category_path and keyword:
        log("Step 0: Resolving category...")
        cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
        results["categories"] = cat_result
        cat_data = cat_result.get("data", [])
        if cat_data:
            category_path = cat_data[0].get("categoryPath")
            log(f"  → Locked: {' > '.join(category_path)}")
    results["meta"]["resolved_category"] = category_path

    # Step 1: Current Price Snapshot
    log("Step 1/8: Current price snapshot...")
    results["my_product"] = safe_call("realtime/product", {"asin": my_asin, "marketplace": "US"}, f"realtime {my_asin}")
    results["meta"]["steps_completed"].append("price_snapshot")

    # Step 2: Price Band Intelligence
    log("Step 2/8: Price band intelligence...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword
    r = safe_call("products/price-band-overview", dict(pb_params), "price-band-overview")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-overview", {"categoryPath": category_path, "pageSize": 20}, "pbo (cat-only)")
    results["price_band_overview"] = r
    r = safe_call("products/price-band-detail", dict(pb_params), "price-band-detail")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-detail", {"categoryPath": category_path, "pageSize": 20}, "pbd (cat-only)")
    results["price_band_detail"] = r
    results["meta"]["steps_completed"].append("price_bands")

    # Step 3: Competitor Price Landscape
    log("Step 3/8: Competitor price landscape...")
    prod_params = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["products"] = safe_call("products/search", prod_params, "products")

    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitor-lookup", comp_params, "competitors")
    results["meta"]["steps_completed"].append("competitor_landscape")

    # Step 4: Market Benchmarks
    log("Step 4/8: Market benchmarks...")
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    brand_params = {"pageSize": 20}
    if category_path:
        brand_params["categoryPath"] = category_path
    if keyword:
        brand_params["keyword"] = keyword
    r = safe_call("products/brand-overview", dict(brand_params), "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            r = safe_call("products/brand-overview", {"categoryPath": category_path, "pageSize": 20}, "bo (cat-only)")
    results["brand_overview"] = r
    r = safe_call("products/brand-detail", dict(brand_params), "brand-detail")
    if not r.get("data") or not r.get("data", {}).get("brands"):
        if keyword and category_path:
            r = safe_call("products/brand-detail", {"categoryPath": category_path, "pageSize": 20}, "bd (cat-only)")
    results["brand_detail"] = r
    results["meta"]["steps_completed"].append("market_benchmarks")

    # Step 5: Historical Price Trends
    log("Step 5/8: Historical price trends...")
    today = time.strftime("%Y-%m-%d")
    thirty_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    
    comp_data = results["products"].get("data", [])
    comp_asins = []
    seen = set()
    for p in (comp_data if isinstance(comp_data, list) else []):
        parent = p.get("parentAsin") or p.get("asin")
        asin = p.get("asin")
        if parent not in seen and asin != my_asin:
            seen.add(parent)
            comp_asins.append(asin)
        if len(comp_asins) >= 4:
            break

    history_asins = [my_asin] + comp_asins
    r = safe_call("products/product-history", {
        "asins": history_asins, "startDate": thirty_ago, "endDate": today
    }, "product-history")
    results["product_history"] = {"data": r.get("data", []), "asins_tried": history_asins}
    results["meta"]["steps_completed"].append("price_trends")

    # Step 6: Realtime Competitor Deep-Dive (Top 5)
    log("Step 6/8: Realtime competitor deep-dive...")
    comp_realtime = []
    for asin in comp_asins[:5]:
        log(f"  → Realtime: {asin}")
        r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"realtime {asin}")
        comp_realtime.append({"asin": asin, "result": r})
    results["comp_realtime"] = comp_realtime
    results["meta"]["steps_completed"].append("comp_deepdive")

    # Step 7: Review Context
    log("Step 7/8: Review context...")
    review_results = {}
    my_rc = results["my_product"].get("data", {}).get("ratingCount", 0)
    if my_rc and my_rc >= 50:
        review_results["my_asin"] = safe_call("reviews/analyze", {
            "asins": [my_asin], "mode": "asin", "labelType": "painPoints", "period": "6m"
        }, f"reviews {my_asin}")
    if comp_asins:
        review_results["top_comp"] = safe_call("reviews/analyze", {
            "asins": [comp_asins[0]], "mode": "asin", "labelType": "painPoints", "period": "6m"
        }, f"reviews {comp_asins[0]}")
    if not review_results and category_path:
        for lt in ["painPoints", "buyingFactors"]:
            review_results[lt] = safe_call("reviews/analyze", {
                "categoryPath": category_path, "mode": "category", "labelType": lt, "period": "6m"
            }, f"reviews cat {lt}")
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_context")

    # Step 8: Price Drill-Down (opportunity band)
    log("Step 8/8: Price drill-down...")
    pbo_data = results.get("price_band_overview", {}).get("data", {})
    best_band = pbo_data.get("bestOpportunityBand", {}) if pbo_data else {}
    if best_band and best_band.get("sampleBandMinPrice") and best_band.get("sampleBandMaxPrice"):
        drill_params = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc",
                        "priceMin": best_band["sampleBandMinPrice"], "priceMax": best_band["sampleBandMaxPrice"]}
        if keyword:
            drill_params["keyword"] = keyword
        if category_path:
            drill_params["categoryPath"] = category_path
        results["price_drilldown"] = safe_call("products/search", drill_params, "price drill-down")
    results["meta"]["steps_completed"].append("price_drilldown")

    log(f"\n✅ Pricing analysis complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    output(results, args.format)


def cmd_daily_radar(args):
    """
    Composite workflow: Daily Market Radar.
    Runs realtime snapshots → historical comparison → market pulse → 
    new competitor detection → price landscape → review pulse.
    Designed for unattended daily monitoring.
    """
    asins_str = args.asins
    keyword = args.keyword
    category = args.category

    if not asins_str:
        print("ERROR: --asins is required (comma-separated ASINs to track).", file=sys.stderr)
        sys.exit(1)
    if not keyword and not category:
        print("ERROR: --keyword or --category is required.", file=sys.stderr)
        sys.exit(1)

    tracked_asins = [a.strip() for a in asins_str.split(",") if a.strip()]
    category_path = parse_category(category) if category else None
    results = {"meta": {"asins": tracked_asins, "keyword": keyword, "category": category, "steps_completed": []}}

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # Step 0.5: Category Resolution
    if not category_path and keyword:
        log("Step 0: Resolving category...")
        cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
        results["categories"] = cat_result
        cat_data = cat_result.get("data", [])
        if cat_data:
            category_path = cat_data[0].get("categoryPath")
            log(f"  → Locked: {' > '.join(category_path)}")
    results["meta"]["resolved_category"] = category_path

    # Step 1: Realtime Snapshot for All Tracked ASINs
    log(f"Step 1/7: Realtime snapshot ({len(tracked_asins)} ASINs)...")
    realtime_snapshots = []
    for asin in tracked_asins:
        log(f"  → {asin}")
        r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"realtime {asin}")
        realtime_snapshots.append({"asin": asin, "result": r})
    results["realtime"] = realtime_snapshots
    results["meta"]["steps_completed"].append("realtime_snapshot")

    # Step 2: Historical Comparison (7-day)
    log("Step 2/7: Historical comparison (7 days)...")
    today = time.strftime("%Y-%m-%d")
    seven_days_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))
    
    history_data = []
    tried_asins = set()
    
    # Round 1: All tracked ASINs
    r = safe_call("products/product-history", {
        "asins": tracked_asins,
        "startDate": seven_days_ago,
        "endDate": today,
    }, "product-history round 1")
    history_data = r.get("data", [])
    tried_asins.update(tracked_asins)

    results["product_history"] = {"data": history_data, "asins_tried": list(tried_asins)}
    log(f"  → {len(history_data)} history records")
    results["meta"]["steps_completed"].append("historical_comparison")

    # Step 3: Market Pulse
    log("Step 3/7: Market pulse...")
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    # Brand overview + detail
    brand_params = {"pageSize": 20}
    if category_path:
        brand_params["categoryPath"] = category_path
    if keyword:
        brand_params["keyword"] = keyword
    
    r = safe_call("products/brand-overview", dict(brand_params), "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            brand_params_co = {k: v for k, v in brand_params.items() if k != "keyword"}
            r = safe_call("products/brand-overview", brand_params_co, "brand-overview (category-only)")
    results["brand_overview"] = r

    r = safe_call("products/brand-detail", dict(brand_params), "brand-detail")
    if not r.get("data") or not r.get("data", {}).get("brands"):
        if keyword and category_path:
            brand_params_co = {k: v for k, v in brand_params.items() if k != "keyword"}
            r = safe_call("products/brand-detail", brand_params_co, "brand-detail (category-only)")
    results["brand_detail"] = r
    results["meta"]["steps_completed"].append("market_pulse")

    # Step 4: New Competitor Detection
    log("Step 4/7: New competitor detection...")
    prod_params = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["top_products"] = safe_call("products/search", prod_params, "products top 20")
    results["meta"]["steps_completed"].append("competitor_detection")

    # Step 5: Price Landscape
    log("Step 5/7: Price landscape...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword

    r = safe_call("products/price-band-overview", dict(pb_params), "price-band-overview")
    if not r.get("data"):
        if keyword and category_path:
            pb_co = {k: v for k, v in pb_params.items() if k != "keyword"}
            r = safe_call("products/price-band-overview", pb_co, "price-band-overview (category-only)")
    results["price_band_overview"] = r

    r = safe_call("products/price-band-detail", dict(pb_params), "price-band-detail")
    if not r.get("data"):
        if keyword and category_path:
            pb_co = {k: v for k, v in pb_params.items() if k != "keyword"}
            r = safe_call("products/price-band-detail", pb_co, "price-band-detail (category-only)")
    results["price_band_detail"] = r
    results["meta"]["steps_completed"].append("price_landscape")

    # Step 6: Review Pulse (ASIN mode for tracked products)
    log("Step 7/7: Review pulse...")
    review_results = {}
    # Pick first tracked ASIN with enough reviews
    for snap in realtime_snapshots:
        rc = snap.get("result", {}).get("data", {}).get("ratingCount", 0)
        if rc and rc >= 50:
            review_asin = snap["asin"]
            log(f"  → Analyzing reviews for {review_asin} ({rc} reviews)")
            r = safe_call("reviews/analyze", {
                "asins": [review_asin],
                "mode": "asin",
                "labelType": "painPoints",
                "period": "6m",
            }, f"reviews {review_asin}")
            review_results["painPoints"] = r
            break
    
    if not review_results:
        log("  ⚠️ No tracked ASIN with ≥50 reviews, using ratingBreakdown from realtime")
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_pulse")

    # Summary
    log(f"\n✅ Daily radar scan complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    log(f"   ASINs tracked: {len(tracked_asins)} | History: {len(history_data)} records")

    output(results, args.format)


def cmd_listing_audit(args):
    """
    Composite workflow: Listing Audit.
    Audits a product listing against category leaders across all dimensions.
    Runs: realtime(target) → products(leaders) → realtime(top5) → market → brand → price-band → reviews → history
    """
    my_asin = args.my_asin
    keyword = args.keyword
    category = args.category

    if not my_asin:
        print("ERROR: --my-asin is required.", file=sys.stderr)
        sys.exit(1)
    if not keyword and not category:
        print("ERROR: --keyword or --category is required.", file=sys.stderr)
        sys.exit(1)

    category_path = parse_category(category) if category else None
    results = {"meta": {"my_asin": my_asin, "keyword": keyword, "category": category, "steps_completed": []}}

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # Step 0.5: Category Resolution
    if not category_path and keyword:
        log("Step 0: Resolving category...")
        cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
        results["categories"] = cat_result
        cat_data = cat_result.get("data", [])
        if cat_data:
            category_path = cat_data[0].get("categoryPath")
            log(f"  → Locked: {' > '.join(category_path)}")
    results["meta"]["resolved_category"] = category_path

    # Step 1: Audit Target
    log("Step 1/7: Auditing target listing...")
    results["target_realtime"] = safe_call("realtime/product", {"asin": my_asin, "marketplace": "US"}, f"realtime {my_asin}")
    results["meta"]["steps_completed"].append("audit_target")

    # Step 2: Category Leaders
    log("Step 2/7: Finding category leaders...")
    prod_params = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["leader_products"] = safe_call("products/search", prod_params, "products leaders")

    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitor-lookup", comp_params, "competitors")
    results["meta"]["steps_completed"].append("category_leaders")

    # Step 3: Benchmark Realtime (Top 5 leaders, deduplicated)
    log("Step 3/7: Realtime benchmark for Top 5 leaders...")
    leader_data = results["leader_products"].get("data", [])
    if isinstance(leader_data, list):
        seen_parents = set()
        leader_asins = []
        for p in leader_data:
            parent = p.get("parentAsin") or p.get("asin")
            asin = p.get("asin")
            if parent not in seen_parents and asin != my_asin:
                seen_parents.add(parent)
                leader_asins.append(asin)
            if len(leader_asins) >= 5:
                break
    else:
        leader_asins = []

    leader_realtime = []
    for asin in leader_asins:
        log(f"  → Realtime: {asin}")
        r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"realtime {asin}")
        leader_realtime.append({"asin": asin, "result": r})
    results["leader_realtime"] = leader_realtime
    results["meta"]["steps_completed"].append("benchmark_realtime")

    # Step 4: Market Context
    log("Step 4/7: Market context...")
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    brand_params = {"pageSize": 20}
    if category_path:
        brand_params["categoryPath"] = category_path
    if keyword:
        brand_params["keyword"] = keyword
    r = safe_call("products/brand-overview", dict(brand_params), "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            r = safe_call("products/brand-overview", {"categoryPath": category_path, "pageSize": 20}, "brand-overview (cat-only)")
    results["brand_overview"] = r

    r = safe_call("products/brand-detail", dict(brand_params), "brand-detail")
    if not r.get("data") or not r.get("data", {}).get("brands"):
        if keyword and category_path:
            r = safe_call("products/brand-detail", {"categoryPath": category_path, "pageSize": 20}, "brand-detail (cat-only)")
    results["brand_detail"] = r
    results["meta"]["steps_completed"].append("market_context")

    # Step 5: Price Context
    log("Step 5/7: Price context...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword
    r = safe_call("products/price-band-overview", dict(pb_params), "price-band-overview")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-overview", {"categoryPath": category_path, "pageSize": 20}, "pbo (cat-only)")
    results["price_band_overview"] = r
    r = safe_call("products/price-band-detail", dict(pb_params), "price-band-detail")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-detail", {"categoryPath": category_path, "pageSize": 20}, "pbd (cat-only)")
    results["price_band_detail"] = r
    results["meta"]["steps_completed"].append("price_context")

    # Step 6: Review Intelligence
    log("Step 6/7: Review intelligence...")
    review_results = {}
    # ASIN mode first (my_asin + top leader)
    target_rc = results["target_realtime"].get("data", {}).get("ratingCount", 0)
    if target_rc and target_rc >= 50:
        log(f"  → reviews/analyze ASIN mode: {my_asin}")
        review_results["my_asin"] = safe_call("reviews/analyze", {
            "asins": [my_asin], "mode": "asin", "labelType": "painPoints", "period": "6m"
        }, f"reviews {my_asin}")
    if leader_asins:
        top_leader = leader_asins[0]
        log(f"  → reviews/analyze ASIN mode: {top_leader}")
        review_results["top_leader"] = safe_call("reviews/analyze", {
            "asins": [top_leader], "mode": "asin", "labelType": "painPoints", "period": "6m"
        }, f"reviews {top_leader}")
    # Category fallback
    if not review_results and category_path:
        log("  → Falling back to category mode...")
        for lt in ["painPoints", "buyingFactors", "improvements"]:
            review_results[lt] = safe_call("reviews/analyze", {
                "categoryPath": category_path, "mode": "category", "labelType": lt, "period": "6m"
            }, f"reviews category {lt}")
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_intelligence")

    # Step 7: Trend Context
    log("Step 7/7: Trend context...")
    today = time.strftime("%Y-%m-%d")
    thirty_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    history_asins = [my_asin] + leader_asins[:2]
    r = safe_call("products/product-history", {
        "asins": history_asins, "startDate": thirty_ago, "endDate": today
    }, "product-history")
    results["product_history"] = {"data": r.get("data", []), "asins_tried": history_asins}
    results["meta"]["steps_completed"].append("trend_context")

    log(f"\n✅ Listing audit complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    log(f"   Target: {my_asin} | Leaders: {len(leader_asins)} | Reviews: {len(review_results)}")
    output(results, args.format)


def cmd_opportunity_scan(args):
    """
    Composite workflow: Opportunity Discovery.
    Supports TWO scanning approaches:
    1. Mode-based: uses 14 preset modes (beginner, emerging, underserved, etc.)
    2. Custom filters: user-defined criteria (sales-min, ratings-max, price-min/max, rating-max)
    Both can be combined — mode presets + custom overrides.
    """
    keyword = args.keyword
    category = args.category
    modes_str = getattr(args, 'modes', None)
    
    # Custom filter params
    sales_min = getattr(args, 'sales_min', None)
    sales_max = getattr(args, 'sales_max', None)
    ratings_max = getattr(args, 'ratings_max', None)
    price_min = getattr(args, 'price_min', None)
    price_max = getattr(args, 'price_max', None)
    rating_max = getattr(args, 'rating_max', None)
    rating_min = getattr(args, 'rating_min', None)

    if not keyword and not category:
        print("ERROR: --keyword or --category is required.", file=sys.stderr)
        sys.exit(1)

    # Determine scan strategy
    has_custom_filters = any(v is not None for v in [sales_min, sales_max, ratings_max, price_min, price_max, rating_max, rating_min])
    
    if modes_str:
        modes = [m.strip() for m in modes_str.split(",")]
    elif has_custom_filters:
        modes = ["custom"]  # Custom-only scan
    else:
        modes = ["beginner", "emerging", "underserved"]  # Default modes
    
    category_path = parse_category(category) if category else None
    results = {"meta": {"keyword": keyword, "category": category, "modes": modes, 
                        "custom_filters": {k: v for k, v in {"sales_min": sales_min, "sales_max": sales_max,
                            "ratings_max": ratings_max, "price_min": price_min, "price_max": price_max,
                            "rating_max": rating_max, "rating_min": rating_min}.items() if v is not None},
                        "steps_completed": []}}

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # Category Resolution
    if not category_path and keyword:
        log("Step 0: Resolving category...")
        cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
        results["categories"] = cat_result
        cat_data = cat_result.get("data", [])
        if cat_data:
            category_path = cat_data[0].get("categoryPath")
            log(f"  → Locked: {' > '.join(category_path)}")
    results["meta"]["resolved_category"] = category_path

    # Step 1: Product Scan (mode-based + custom filters)
    scan_label = f"{len(modes)} modes" if "custom" not in modes else "custom filters"
    log(f"Step 1/6: Product scan ({scan_label})...")
    all_candidates = {}  # asin → product data (deduplicated)
    mode_results = {}
    
    # Build custom filter params (applied to ALL scans)
    custom_params = {}
    if sales_min is not None:
        custom_params["monthlySalesMin"] = sales_min
    if sales_max is not None:
        custom_params["monthlySalesMax"] = sales_max
    if ratings_max is not None:
        custom_params["ratingCountMax"] = ratings_max
    if price_min is not None:
        custom_params["priceMin"] = price_min
    if price_max is not None:
        custom_params["priceMax"] = price_max
    if rating_max is not None:
        custom_params["ratingMax"] = rating_max
    if rating_min is not None:
        custom_params["ratingMin"] = rating_min
    
    for mode in modes:
        log(f"  → {'Custom filters' if mode == 'custom' else f'Mode: {mode}'}")
        mode_products = []
        for page in range(1, 6):  # 5 pages per mode (100 products max)
            prod_params = {"pageSize": 20, "page": page, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
            if keyword:
                prod_params["keyword"] = keyword
            if category_path:
                prod_params["categoryPath"] = category_path
            # Apply mode preset (skip for "custom" mode)
            if mode != "custom" and mode in PRODUCT_MODES:
                prod_params.update(PRODUCT_MODES[mode])
            # Apply custom filters ON TOP of mode (custom overrides mode defaults)
            prod_params.update(custom_params)
            r = safe_call("products/search", prod_params, f"products {mode} p{page}")
            items = r.get("data", [])
            if isinstance(items, list):
                mode_products.extend(items)
            if not items:
                break
        mode_results[mode] = mode_products
        for p in mode_products:
            asin = p.get("asin")
            if asin and asin not in all_candidates:
                all_candidates[asin] = p
        log(f"    → {len(mode_products)} products, {len(all_candidates)} unique total")
    
    # Log actual search parameters for transparency
    if custom_params:
        log(f"  → Custom filters applied: {custom_params}")
    
    results["scan_results"] = {m: len(ps) for m, ps in mode_results.items()}
    results["meta"]["total_candidates"] = len(all_candidates)
    results["meta"]["steps_completed"].append("product_scan")

    # Step 2: Market Context
    log("Step 2/6: Market context...")
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    brand_params = {"pageSize": 20}
    if category_path:
        brand_params["categoryPath"] = category_path
    if keyword:
        brand_params["keyword"] = keyword
    r = safe_call("products/brand-overview", dict(brand_params), "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            r = safe_call("products/brand-overview", {"categoryPath": category_path, "pageSize": 20}, "bo (cat)")
    results["brand_overview"] = r
    r = safe_call("products/brand-detail", dict(brand_params), "brand-detail")
    if not r.get("data") or not r.get("data", {}).get("brands"):
        if keyword and category_path:
            r = safe_call("products/brand-detail", {"categoryPath": category_path, "pageSize": 20}, "bd (cat)")
    results["brand_detail"] = r
    results["meta"]["steps_completed"].append("market_context")

    # Step 3: Price Opportunity
    log("Step 3/6: Price opportunity...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword
    r = safe_call("products/price-band-overview", dict(pb_params), "pbo")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-overview", {"categoryPath": category_path, "pageSize": 20}, "pbo (cat)")
    results["price_band_overview"] = r
    r = safe_call("products/price-band-detail", dict(pb_params), "pbd")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-detail", {"categoryPath": category_path, "pageSize": 20}, "pbd (cat)")
    results["price_band_detail"] = r
    results["meta"]["steps_completed"].append("price_opportunity")

    # Step 4: Realtime Validation for Top 10
    log("Step 4/6: Realtime validation (Top 10)...")
    sorted_candidates = sorted(all_candidates.values(), key=lambda x: x.get("atLeastMonthlySales") or 0, reverse=True)
    seen = set()
    top_asins = []
    for p in sorted_candidates:
        parent = p.get("parentAsin") or p.get("asin")
        if parent not in seen:
            seen.add(parent)
            top_asins.append(p.get("asin"))
        if len(top_asins) >= 10:
            break

    realtime_details = []
    for asin in top_asins:
        log(f"  → {asin}")
        r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"rt {asin}")
        realtime_details.append({"asin": asin, "result": r})
    results["realtime"] = realtime_details
    results["meta"]["steps_completed"].append("realtime_validation")

    # Step 5: Trend Check (Top 5)
    log("Step 5/6: Trend check...")
    today = time.strftime("%Y-%m-%d")
    thirty_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    r = safe_call("products/product-history", {
        "asins": top_asins[:5], "startDate": thirty_ago, "endDate": today
    }, "product-history")
    results["product_history"] = {"data": r.get("data", []), "asins_tried": top_asins[:5]}
    results["meta"]["steps_completed"].append("trend_check")

    # Step 6: Consumer Insights (Top 3, category mode first)
    log("Step 6/6: Consumer insights...")
    review_results = {}
    if category_path:
        for lt in ["painPoints", "buyingFactors", "improvements"]:
            log(f"  → category mode: {lt}")
            r = safe_call("reviews/analyze", {
                "categoryPath": category_path, "mode": "category", "labelType": lt, "period": "6m"
            }, f"reviews {lt}")
            if r.get("data") and r.get("data", {}).get("consumerInsights"):
                review_results[lt] = r
            else:
                break
    if not review_results:
        log("  → Falling back to ASIN mode...")
        review_asins = [a for a in top_asins[:3]]
        for lt in ["painPoints", "buyingFactors", "improvements"]:
            r = safe_call("reviews/analyze", {
                "asins": review_asins, "mode": "asin", "labelType": lt, "period": "6m"
            }, f"reviews ASIN {lt}")
            review_results[lt] = r
    results["reviews"] = review_results
    results["meta"]["review_mode"] = "category" if category_path and review_results.get("painPoints", {}).get("data", {}).get("consumerInsights") else "asin"
    results["meta"]["steps_completed"].append("consumer_insights")

    # All candidates as structured list
    results["all_candidates"] = sorted_candidates[:50]  # Top 50 for report

    log(f"\n✅ Opportunity scan complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    log(f"   Modes: {modes} | Candidates: {len(all_candidates)} | Realtime: {len(realtime_details)}")
    output(results, args.format)


def cmd_review_deepdive(args):
    """
    Composite workflow: Review Intelligence Deep Dive.
    Full 11-dimension review analysis with market context.
    """
    target_asin = args.target_asin
    keyword = args.keyword
    category = args.category
    comp_asins_str = getattr(args, 'comp_asins', None)

    if not target_asin and not keyword:
        print("ERROR: --target-asin or --keyword is required.", file=sys.stderr)
        sys.exit(1)

    comp_asins = [a.strip() for a in comp_asins_str.split(",") if a.strip()] if comp_asins_str else []
    category_path = parse_category(category) if category else None
    results = {"meta": {"target_asin": target_asin, "keyword": keyword, "comp_asins": comp_asins, "steps_completed": []}}

    def log(msg):
        print(msg, file=sys.stderr)

    def safe_call(endpoint, params, label=""):
        r = api_call(endpoint, params)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
        return r

    # Category Resolution
    if not category_path:
        if keyword:
            log("Step 0: Resolving category...")
            cat_result = safe_call("categories", {"categoryKeyword": keyword}, "categories")
            results["categories"] = cat_result
            cat_data = cat_result.get("data", [])
            if cat_data:
                category_path = cat_data[0].get("categoryPath")
    results["meta"]["resolved_category"] = category_path

    # Step 1: Target Identification
    log("Step 1/5: Target identification...")
    if target_asin:
        results["target_realtime"] = safe_call("realtime/product", {"asin": target_asin, "marketplace": "US"}, f"realtime {target_asin}")
    if not target_asin and keyword:
        prod_params = {"pageSize": 20, "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
        if keyword:
            prod_params["keyword"] = keyword
        if category_path:
            prod_params["categoryPath"] = category_path
        results["products"] = safe_call("products/search", prod_params, "products")
        # Pick top product as target
        items = results["products"].get("data", [])
        if isinstance(items, list) and items:
            target_asin = items[0].get("asin")
            results["target_realtime"] = safe_call("realtime/product", {"asin": target_asin, "marketplace": "US"}, f"realtime {target_asin}")
    results["meta"]["resolved_target"] = target_asin
    results["meta"]["steps_completed"].append("target_identification")

    # Step 2: Full Review Analysis (11 dimensions for target + comparison)
    log("Step 2/5: Full review analysis (11 dimensions)...")
    label_types = ["painPoints", "positives", "buyingFactors", "improvements", "userProfiles",
                   "scenarios", "issues", "keywords", "usageTimes", "usageLocations", "behaviors"]
    
    review_results = {}
    # Target ASIN reviews
    if target_asin:
        for lt in label_types:
            log(f"  → {target_asin}: {lt}")
            r = safe_call("reviews/analyze", {
                "asins": [target_asin], "mode": "asin", "labelType": lt, "period": "6m"
            }, f"reviews {lt}")
            review_results[f"target_{lt}"] = r
    
    # Competitor comparison (top 2)
    for comp_asin in comp_asins[:2]:
        log(f"  → Competitor {comp_asin}: painPoints + positives")
        review_results[f"comp_{comp_asin}_painPoints"] = safe_call("reviews/analyze", {
            "asins": [comp_asin], "mode": "asin", "labelType": "painPoints", "period": "6m"
        }, f"reviews comp {comp_asin}")
        review_results[f"comp_{comp_asin}_positives"] = safe_call("reviews/analyze", {
            "asins": [comp_asin], "mode": "asin", "labelType": "positives", "period": "6m"
        }, f"reviews comp+ {comp_asin}")
    
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_analysis")

    # Step 3: Realtime Product Detail
    log("Step 3/5: Realtime product detail...")
    if comp_asins:
        comp_realtime = []
        for asin in comp_asins[:3]:
            log(f"  → {asin}")
            r = safe_call("realtime/product", {"asin": asin, "marketplace": "US"}, f"realtime {asin}")
            comp_realtime.append({"asin": asin, "result": r})
        results["comp_realtime"] = comp_realtime
    results["meta"]["steps_completed"].append("realtime_detail")

    # Step 4: Market & Competitive Context
    log("Step 4/5: Market context...")
    market_params = {"topN": "10", "pageSize": 20}
    if category_path:
        market_params["categoryPath"] = category_path
    elif keyword:
        market_params["categoryKeyword"] = keyword
    results["market"] = safe_call("markets/search", market_params, "market")

    brand_params = {"pageSize": 20}
    if category_path:
        brand_params["categoryPath"] = category_path
    if keyword:
        brand_params["keyword"] = keyword
    r = safe_call("products/brand-overview", dict(brand_params), "brand-overview")
    if not r.get("data") or r.get("data", {}).get("sampleBrandCount", 0) == 0:
        if keyword and category_path:
            r = safe_call("products/brand-overview", {"categoryPath": category_path, "pageSize": 20}, "bo (cat)")
    results["brand_overview"] = r

    # Competitor lookup
    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "atLeastMonthlySales", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitor-lookup", comp_params, "competitors")
    results["meta"]["steps_completed"].append("market_context")

    # Step 5: Price & Trend Context
    log("Step 5/5: Price & trend context...")
    pb_params = {"pageSize": 20}
    if category_path:
        pb_params["categoryPath"] = category_path
    if keyword:
        pb_params["keyword"] = keyword
    r = safe_call("products/price-band-overview", dict(pb_params), "pbo")
    if not r.get("data") and keyword and category_path:
        r = safe_call("products/price-band-overview", {"categoryPath": category_path, "pageSize": 20}, "pbo (cat)")
    results["price_band_overview"] = r

    today = time.strftime("%Y-%m-%d")
    thirty_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    hist_asins = [target_asin] + comp_asins[:2] if target_asin else comp_asins[:3]
    if hist_asins:
        r = safe_call("products/product-history", {
            "asins": hist_asins, "startDate": thirty_ago, "endDate": today
        }, "product-history")
        results["product_history"] = {"data": r.get("data", []), "asins_tried": hist_asins}
    results["meta"]["steps_completed"].append("price_trend_context")

    log(f"\n✅ Review deep-dive complete!")
    log(f"   Steps: {', '.join(results['meta']['steps_completed'])}")
    log(f"   Review dimensions: {sum(1 for k in review_results if k.startswith('target_'))}")
    output(results, args.format)


def cmd_check(args):
    """
    API self-check: verify API connectivity and available endpoints.
    Tests each endpoint with a simple query.
    """
    print("APIClaw API Self-Check\n", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Check API key from environment variable
    api_key = os.environ.get("APICLAW_API_KEY", "").strip()
    key_source = "env"

    # If not in env, check config file
    if not api_key:
        config_path = os.path.expanduser("~/.apiclaw/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    api_key = config.get("api_key", "").strip()
                    key_source = "config"
            except (json.JSONDecodeError, IOError):
                pass

    if api_key:
        source_label = "~/.apiclaw/config.json" if key_source == "config" else "env"
        print(f"✅ API Key ({source_label}): configured", file=sys.stderr)
    else:
        print("❌ API Key: Not found", file=sys.stderr)
        print("   Checked: $APICLAW_API_KEY, ~/.apiclaw/config.json", file=sys.stderr)
        print("   Get one at: https://apiclaw.io/en/api-keys", file=sys.stderr)
        sys.exit(1)

    print(f"\nTesting endpoints on {BASE_URL}...\n", file=sys.stderr)

    endpoints = [
        ("categories", {}, "Category tree"),
        ("markets/search", {"categoryKeyword": "pet", "pageSize": 1}, "Market search"),
        ("products/search", {"keyword": "test", "pageSize": 1}, "Product search"),
        ("products/competitor-lookup", {"keyword": "test", "pageSize": 1}, "Competitor lookup"),
    ]

    results = {}
    all_ok = True

    for endpoint, params, desc in endpoints:
        try:
            result = api_call(endpoint, params)
            data_count = len(result.get("data", []))
            print(f"✅ {endpoint:30} OK (returned {data_count} items)", file=sys.stderr)
            results[endpoint] = {"status": "ok", "items": data_count}
        except SystemExit:
            print(f"❌ {endpoint:30} FAILED", file=sys.stderr)
            results[endpoint] = {"status": "failed"}
            all_ok = False
        except Exception as e:
            print(f"❌ {endpoint:30} ERROR: {e}", file=sys.stderr)
            results[endpoint] = {"status": "error", "message": str(e)}
            all_ok = False

    # Note: realtime/product requires a valid ASIN, skip in self-check
    print(f"⏭️  realtime/product            (skipped, requires valid ASIN)", file=sys.stderr)

    print("\n" + "=" * 50, file=sys.stderr)
    if all_ok:
        print("✅ All endpoints operational", file=sys.stderr)
    else:
        print("⚠️  Some endpoints failed. Check API key or network.", file=sys.stderr)

    print(f"\nAPI Docs: {API_DOCS}", file=sys.stderr)

    output({"check": "complete", "endpoints": results}, args.format)


# ─── Review Analysis Command ─────────────────────────────────────────────────

def cmd_analyze(args):
    """Analyze reviews for ASINs or category with AI-powered insights."""
    params = {}
    if args.asin:
        params["asins"] = [args.asin]
        params["mode"] = "asin"
    elif args.asins:
        params["asins"] = [a.strip() for a in args.asins.split(",")]
        params["mode"] = "asin"
    elif args.category:
        params["categoryPath"] = parse_category(args.category)
        params["mode"] = "category"
    else:
        print("ERROR: --asin, --asins, or --category is required.", file=sys.stderr)
        sys.exit(1)

    if args.label_type:
        params["labelType"] = args.label_type
    if args.period:
        params["period"] = args.period

    result = api_call("reviews/analyze", params)
    output(result, args.format)


# ─── New Endpoint Commands (price-band, brand, history) ──────────────────────

def cmd_price_band_overview(args):
    """Get price band overview — hottest and best opportunity bands."""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["categoryPath"] = parse_category(args.category)
    params["pageSize"] = args.page_size or 20
    result = api_call("products/price-band-overview", params)
    output(result, args.format)


def cmd_price_band_detail(args):
    """Get price band detailed breakdown — all bands with stats."""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["categoryPath"] = parse_category(args.category)
    params["pageSize"] = args.page_size or 20
    result = api_call("products/price-band-detail", params)
    output(result, args.format)


def cmd_brand_overview(args):
    """Get brand landscape overview — brand count, CR10, top brand stats."""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["categoryPath"] = parse_category(args.category)
    params["pageSize"] = args.page_size or 20
    result = api_call("products/brand-overview", params)
    output(result, args.format)


def cmd_brand_detail(args):
    """Get brand ranking with per-brand statistics."""
    params = {}
    if args.keyword:
        params["keyword"] = args.keyword
    if args.category:
        params["categoryPath"] = parse_category(args.category)
    params["pageSize"] = args.page_size or 20
    result = api_call("products/brand-detail", params)
    output(result, args.format)


def cmd_product_history(args):
    """Get historical data (price, BSR, sales) for ASINs over a date range."""
    asins = [a.strip() for a in args.asins.split(",")]
    params = {
        "asins": asins,
        "startDate": args.start_date,
        "endDate": args.end_date,
    }
    result = api_call("products/product-history", params)
    output(result, args.format)


# ─── CLI Setup ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="APIClaw CLI — Amazon Product Research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s categories --keyword "pet supplies"
  %(prog)s market --category "Pet Supplies,Dogs" --topn 10
  %(prog)s products --keyword "yoga mat" --mode beginner
  %(prog)s products --keyword "yoga mat" --sales-min 300 --ratings-max 50
  %(prog)s competitors --keyword "wireless earbuds" --brand Anker
  %(prog)s product --asin B09V3KXJPB
  %(prog)s report --keyword "pet supplies"
  %(prog)s opportunity --keyword "pet supplies" --mode high-demand-low-barrier
  %(prog)s check                                            # API self-check
        """,
    )

    # Common args
    parser.add_argument("--format", choices=["json", "compact"], default="json",
                        help="Output format (default: json)")

    sub = parser.add_subparsers(dest="command", required=True)

    # ── categories ──
    p_cat = sub.add_parser("categories", help="Query Amazon category tree")
    p_cat.add_argument("--keyword", help="Search categories by keyword")
    p_cat.add_argument("--category", help="Exact category path (comma-separated)")
    p_cat.add_argument("--parent", help="Get child categories (comma-separated parent path)")
    p_cat.set_defaults(func=cmd_categories)

    # ── market ──
    p_mkt = sub.add_parser("market", help="Search market-level data for a category")
    p_mkt.add_argument("--category", help="Category path (comma-separated)")
    p_mkt.add_argument("--keyword", help="Category keyword")
    p_mkt.add_argument("--topn", type=int, default=10, help="Top N for concentration analysis (default: 10)")
    p_mkt.add_argument("--page-size", type=int, default=20)
    p_mkt.add_argument("--sort", help="Sort field")
    p_mkt.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_mkt.set_defaults(func=cmd_market)

    # ── products ──
    p_prod = sub.add_parser("products", help="Search products with filters (product selection)")
    p_prod.add_argument("--keyword", help="Search keyword")
    p_prod.add_argument("--category", help="Category path (comma-separated)")
    p_prod.add_argument("--mode", help=f"Preset filter mode: {', '.join(sorted(PRODUCT_MODES.keys()))}")
    p_prod.add_argument("--sales-min", type=int, help="Min monthly sales")
    p_prod.add_argument("--sales-max", type=int, help="Max monthly sales")
    p_prod.add_argument("--ratings-min", type=int, help="Min rating count")
    p_prod.add_argument("--ratings-max", type=int, help="Max rating count")
    p_prod.add_argument("--price-min", type=float, help="Min price")
    p_prod.add_argument("--price-max", type=float, help="Max price")
    p_prod.add_argument("--rating-min", type=float, help="Min rating")
    p_prod.add_argument("--rating-max", type=float, help="Max rating")
    p_prod.add_argument("--growth-min", type=float, help="Min sales growth rate")
    p_prod.add_argument("--listing-age", help="Max listing age in days (string)")
    p_prod.add_argument("--badges", nargs="+", help="Badge filters (e.g. 'New Release')")
    p_prod.add_argument("--fulfillment", nargs="+", help="Fulfillment filter (FBA, FBM)")
    p_prod.add_argument("--include-brands", help="Include brands (comma-separated)")
    p_prod.add_argument("--exclude-brands", help="Exclude brands (comma-separated)")
    p_prod.add_argument("--page-size", type=int, default=20)
    p_prod.add_argument("--sort", help="Sort field (default: monthlySales)")
    p_prod.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_prod.set_defaults(func=cmd_products)

    # ── competitors ──
    p_comp = sub.add_parser("competitors", help="Look up competitors")
    p_comp.add_argument("--keyword", help="Search keyword")
    p_comp.add_argument("--brand", help="Brand filter")
    p_comp.add_argument("--asin", help="ASIN filter")
    p_comp.add_argument("--category", help="Category path (comma-separated)")
    p_comp.add_argument("--date-range", default="30d", help="Date range (default: 30d)")
    p_comp.add_argument("--marketplace", default="US", help="Marketplace (default: US)")
    p_comp.add_argument("--page", type=int, default=1, help="Page number")
    p_comp.add_argument("--page-size", type=int, default=20)
    p_comp.add_argument("--sort", help="Sort field (default: atLeastMonthlySales)")
    p_comp.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_comp.set_defaults(func=cmd_competitors)

    # ── product (single ASIN) ──
    p_single = sub.add_parser("product", help="Get real-time details for one ASIN")
    p_single.add_argument("--asin", required=True, help="ASIN (required)")
    p_single.add_argument("--marketplace", default="US",
                          help="Marketplace: US/UK/DE/FR/IT/ES/JP/CA/AU/IN/MX/BR (default: US)")
    p_single.set_defaults(func=cmd_product)

    # ── report (composite) ──
    p_report = sub.add_parser("report", help="Full market analysis report (composite workflow)")
    p_report.add_argument("--keyword", required=True, help="Category/niche keyword")
    p_report.add_argument("--topn", type=int, default=10, help="Top N (default: 10)")
    p_report.set_defaults(func=cmd_report)

    # ── opportunity (composite) ──
    p_opp = sub.add_parser("opportunity", help="Product opportunity discovery (composite workflow)")
    p_opp.add_argument("--keyword", required=True, help="Category/niche keyword")
    p_opp.add_argument("--mode", help="Product search mode preset")
    p_opp.set_defaults(func=cmd_opportunity)

    # ── market-entry (composite: full analysis) ──
    p_me = sub.add_parser("market-entry", help="Full market entry analysis (runs ALL endpoints automatically)")
    p_me.add_argument("--keyword", help="Product keyword or niche")
    p_me.add_argument("--category", help="Category path (e.g. 'Sports & Outdoors>Sports Sunglasses')")
    p_me.set_defaults(func=cmd_market_entry)

    # ── competitor-analysis (composite) ──
    p_ca = sub.add_parser("competitor-analysis", help="Full competitor war room analysis")
    p_ca.add_argument("--keyword", help="Product keyword to discover competitors")
    p_ca.add_argument("--my-asin", help="Your product ASIN (optional)")
    p_ca.add_argument("--category", help="Category path")
    p_ca.set_defaults(func=cmd_competitor_analysis)

    # ── pricing-analysis (composite) ──
    p_pa = sub.add_parser("pricing-analysis", help="Full pricing analysis with competitor benchmarking")
    p_pa.add_argument("--my-asin", required=True, help="Your product ASIN")
    p_pa.add_argument("--keyword", help="Product keyword for market context")
    p_pa.add_argument("--category", help="Category path")
    p_pa.set_defaults(func=cmd_pricing_analysis)

    # ── daily-radar (composite) ──
    p_dr = sub.add_parser("daily-radar", help="Daily market monitoring scan (runs all tracking endpoints)")
    p_dr.add_argument("--asins", required=True, help="Tracked ASINs (comma-separated, your products + competitors)")
    p_dr.add_argument("--keyword", help="Category keyword for market monitoring")
    p_dr.add_argument("--category", help="Category path")
    p_dr.set_defaults(func=cmd_daily_radar)

    # ── listing-audit (composite) ──
    p_la = sub.add_parser("listing-audit", help="Full listing audit against category leaders")
    p_la.add_argument("--my-asin", required=True, help="ASIN to audit")
    p_la.add_argument("--keyword", help="Primary keyword for benchmark context")
    p_la.add_argument("--category", help="Category path")
    p_la.set_defaults(func=cmd_listing_audit)

    # ── opportunity-scan (composite) ──
    p_os = sub.add_parser("opportunity-scan", help="Multi-mode product opportunity discovery")
    p_os.add_argument("--keyword", help="Category keyword to scan")
    p_os.add_argument("--category", help="Category path")
    p_os.add_argument("--modes", help="Scan modes (comma-separated, e.g. beginner,emerging,underserved). Omit to use custom filters only.")
    p_os.add_argument("--sales-min", type=int, help="Min monthly sales (e.g. 300)")
    p_os.add_argument("--sales-max", type=int, help="Max monthly sales")
    p_os.add_argument("--ratings-max", type=int, help="Max review count (e.g. 100 for blue ocean)")
    p_os.add_argument("--price-min", type=float, help="Min price (e.g. 15)")
    p_os.add_argument("--price-max", type=float, help="Max price (e.g. 35)")
    p_os.add_argument("--rating-max", type=float, help="Max rating (e.g. 4.3 for improvement opportunity)")
    p_os.add_argument("--rating-min", type=float, help="Min rating")
    p_os.set_defaults(func=cmd_opportunity_scan)

    # ── review-deepdive (composite) ──
    p_rd = sub.add_parser("review-deepdive", help="Full 11-dimension review intelligence analysis")
    p_rd.add_argument("--target-asin", help="ASIN to analyze in depth")
    p_rd.add_argument("--keyword", help="Keyword to find target (if no ASIN)")
    p_rd.add_argument("--comp-asins", help="Competitor ASINs for comparison (comma-separated)")
    p_rd.add_argument("--category", help="Category path")
    p_rd.set_defaults(func=cmd_review_deepdive)

    # ── analyze (reviews) ──
    p_analyze = sub.add_parser("analyze", help="AI-powered review analysis")
    p_analyze.add_argument("--asin", help="Single ASIN")
    p_analyze.add_argument("--asins", help="Multiple ASINs (comma-separated)")
    p_analyze.add_argument("--category", help="Category path")
    p_analyze.add_argument("--label-type", help="Filter dimensions (comma-separated)")
    p_analyze.add_argument("--period", help="Time period: 1m, 3m, 6m, 1y, 2y", default="6m")
    p_analyze.set_defaults(func=cmd_analyze)

    # ── price-band-overview ──
    p_pbo = sub.add_parser("price-band-overview", help="Price band overview (hottest & best opportunity)")
    p_pbo.add_argument("--keyword", help="Search keyword")
    p_pbo.add_argument("--category", help="Category path")
    p_pbo.add_argument("--page-size", type=int, default=20)
    p_pbo.set_defaults(func=cmd_price_band_overview)

    # ── price-band-detail ──
    p_pbd = sub.add_parser("price-band-detail", help="Price band detailed breakdown")
    p_pbd.add_argument("--keyword", help="Search keyword")
    p_pbd.add_argument("--category", help="Category path")
    p_pbd.add_argument("--page-size", type=int, default=20)
    p_pbd.set_defaults(func=cmd_price_band_detail)

    # ── brand-overview ──
    p_bo = sub.add_parser("brand-overview", help="Brand landscape overview")
    p_bo.add_argument("--keyword", help="Search keyword")
    p_bo.add_argument("--category", help="Category path")
    p_bo.add_argument("--page-size", type=int, default=20)
    p_bo.set_defaults(func=cmd_brand_overview)

    # ── brand-detail ──
    p_bd = sub.add_parser("brand-detail", help="Brand ranking with per-brand stats")
    p_bd.add_argument("--keyword", help="Search keyword")
    p_bd.add_argument("--category", help="Category path")
    p_bd.add_argument("--page-size", type=int, default=20)
    p_bd.set_defaults(func=cmd_brand_detail)

    # ── product-history ──
    p_ph = sub.add_parser("product-history", help="Historical data for ASINs")
    p_ph.add_argument("--asins", required=True, help="ASINs (comma-separated)")
    p_ph.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    p_ph.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    p_ph.set_defaults(func=cmd_product_history)

    # ── check (API self-check) ──
    p_check = sub.add_parser("check", help="Fetch latest OpenAPI spec to verify available endpoints")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# ============================================================
# Canonical source - do not edit copies under amazon-* skill directories directly
# Source location: apiclaw/scripts/apiclaw.py
# Sync method: pre-commit hook auto-copy or bash scripts/sync-scripts.sh
# ============================================================
"""
APIClaw CLI — Amazon Product Research via APIClaw API

Single-script interface for all 11 APIClaw endpoints + composite workflows.
Handles authentication, retries, rate limits, parameter quirks, and output formatting.

Usage:
    python apiclaw.py categories --keyword "pet supplies"
    python apiclaw.py market --category "Pet Supplies" --topn 10
    python apiclaw.py products --keyword "yoga mat" --mode emerging
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
import random
import time
import urllib.request
import urllib.error

# ─── Configuration ───────────────────────────────────────────────────────────

BASE_URL = "https://api.apiclaw.io/openapi/v2"  # APIClaw API base URL
API_DOCS = "https://api.apiclaw.io/api-docs"   # API documentation URL
MAX_RETRIES = 3       # Maximum number of retry attempts for failed requests
RETRY_DELAY = 2       # Initial retry delay in seconds; doubles on each retry
RATE_LIMIT_RETRIES = 4  # Extra retries specifically for 429 rate limits
RATE_LIMIT_DELAY = 5    # Initial delay for 429 retries (seconds); doubles each time
MIN_REQUEST_INTERVAL = 0.6  # Minimum seconds between requests (100 req/min = 0.6s)
REQUEST_TIMEOUT = 60  # Request timeout in seconds; realtime/product can be slow (up to 30s)

# Global request pacer — prevents burst rate limit violations
_last_request_time = 0.0

# 13 built-in product selection modes
# Each maps to a set of products/search filter parameters
PRODUCT_MODES = {
    "fast-movers":              {"monthlySalesMin": 300, "salesGrowthRateMin": 0.1},
    "emerging":                 {"monthlySalesMax": 600, "salesGrowthRateMin": 0.1, "listingAge": "180"},
    "single-variant":           {"salesGrowthRateMin": 0.2, "variantCountMax": 1, "listingAge": "180"},
    "high-demand-low-barrier":  {"monthlySalesMin": 300, "ratingCountMax": 50, "listingAge": "180"},
    "long-tail":                {"bsrMin": 10000, "bsrMax": 50000, "priceMax": 30, "sellerCountMax": 1, "monthlySalesMax": 300},
    "underserved":              {"monthlySalesMin": 300, "ratingMax": 3.7, "listingAge": "180"},
    "new-release":              {"monthlySalesMax": 500, "badges": ["New Release"], "fulfillments": ["FBA", "FBM"]},
    "fbm-friendly":             {"monthlySalesMin": 300, "fulfillments": ["FBM"], "listingAge": "180"},
    "low-price":                {"priceMax": 10},
    "broad-catalog":            {"bsrGrowthRateMin": 0.99, "ratingCountMax": 10, "listingAge": "90"},
    "selective-catalog":        {"bsrGrowthRateMin": 0.99, "listingAge": "90"},
    "speculative":              {"monthlySalesMin": 600, "sellerCountMin": 3, "listingAge": "180"},
    # "beginner" mode disabled — excludeKeywords filter not working
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
    global _last_request_time

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

    # Rate-limit pacing: enforce minimum interval between requests
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

    delay = RETRY_DELAY
    max_attempts = MAX_RETRIES
    for attempt in range(1, max_attempts + 1):
        _last_request_time = time.monotonic()
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
                # Switch to longer retry strategy for rate limits
                if attempt == 1:
                    max_attempts = RATE_LIMIT_RETRIES
                    delay = RATE_LIMIT_DELAY
                if attempt < max_attempts:
                    jitter = random.uniform(0, delay * 0.25)
                    wait = delay + jitter
                    print(f"Rate limited (429). Waiting {wait:.1f}s before retry {attempt}/{max_attempts}...", file=sys.stderr)
                    time.sleep(wait)
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
                if attempt < max_attempts:
                    print(f"HTTP {status}. Retrying {attempt}/{max_attempts}...", file=sys.stderr)
                    time.sleep(delay)
                    continue
                else:
                    return _error_result(status, f"HTTP {status} after {max_attempts} attempts",
                        "Check network or try again later",
                        endpoint, actual_params)
        except Exception as e:
            if attempt < max_attempts:
                print(f"Request failed: {e}. Retrying {attempt}/{max_attempts}...", file=sys.stderr)
                time.sleep(delay)
                continue
            else:
                return _error_result(0, f"Request failed: {e}",
                    "Check network connection",
                    endpoint, actual_params)

    return _error_result(0, "Unexpected retry loop exit", "This should not happen", endpoint, actual_params)


def _filter_review_insights(result, label_type):
    """Return a shallow copy of a reviews/analysis result filtered to one labelType."""
    if not result.get("data") or not result["data"].get("consumerInsights"):
        return result
    filtered = dict(result)
    filtered["data"] = dict(result["data"])
    filtered["data"]["consumerInsights"] = [
        i for i in result["data"]["consumerInsights"]
        if i.get("labelType") == label_type
    ]
    return filtered


def _fetch_all_history(api_caller, asins, start_date, end_date, log_fn=None):
    """Fetch products/history for multiple ASINs (one API call per ASIN)."""
    all_data = []
    last_response = None
    for asin in asins:
        r = api_caller("products/history", {
            "asin": asin, "startDate": start_date, "endDate": end_date,
        }, f"history {asin}")
        last_response = r
        if r.get("data"):
            all_data.append(r["data"])
        elif log_fn:
            log_fn(f"  ⚠️ No history data for {asin}")
    if last_response is None:
        return {"success": False, "data": [], "error": {"message": "No ASINs provided"}}
    last_response["data"] = all_data
    return last_response


def _resolve_category(api_caller, log_fn, keyword=None, asin=None, results=None):
    """
    Resolve categoryPath with multi-level fallback.
    Returns (category_path, category_source) tuple.

    Priority:
      1. keyword → categories API
      2. asin → realtime/product → categoryPath or bestsellersRank leaf
      3. keyword → products/search → first result → realtime/product
    """
    category_path = None
    category_source = "user"

    # Priority 1: keyword → categories
    if keyword:
        log_fn("Step 0: Resolving category...")
        cat_result = api_caller("categories", {"categoryKeyword": keyword}, "categories")
        if results is not None:
            results["categories"] = cat_result
        cat_data = cat_result.get("data", [])
        if cat_data:
            category_path = cat_data[0].get("categoryPath")
            category_source = "keyword"

    # Priority 2: asin → realtime/product
    if not category_path and asin:
        log_fn("  → Resolving category from ASIN...")
        rt = api_caller("realtime/product", {"asin": asin, "marketplace": "US"}, f"realtime {asin}")
        if results is not None:
            results.setdefault("_asin_realtime", rt)
        rt_data = rt.get("data", {}) or {}
        if rt_data.get("categoryPath"):
            category_path = rt_data["categoryPath"]
            category_source = "asin_realtime"
            log_fn(f"  → Auto-detected category: {' > '.join(category_path)}")
        elif rt_data.get("bestsellersRank"):
            leaf = rt_data["bestsellersRank"][-1].get("category", "")
            if leaf:
                log_fn(f"  → Resolving category from BSR leaf: {leaf}")
                cat_result = api_caller("categories", {"categoryKeyword": leaf}, "categories")
                cat_data = cat_result.get("data", [])
                if cat_data:
                    category_path = cat_data[0].get("categoryPath")
                    category_source = "asin_bsr"
                    log_fn(f"  → Auto-detected category: {' > '.join(category_path)}")

    # Priority 3: keyword → search → first product → realtime
    if not category_path and keyword:
        log_fn("  → Resolving category from top search result...")
        prod_result = api_caller("products/search", {
            "keyword": keyword, "sortBy": "monthlySalesFloor", "sortOrder": "desc", "pageSize": 5
        }, "products (category probe)")
        prod_data = prod_result.get("data", [])
        if isinstance(prod_data, list) and prod_data:
            probe_asin = prod_data[0].get("asin")
            if probe_asin:
                rt = api_caller("realtime/product", {"asin": probe_asin, "marketplace": "US"}, f"realtime {probe_asin}")
                rt_data = rt.get("data", {}) or {}
                if rt_data.get("categoryPath"):
                    category_path = rt_data["categoryPath"]
                    category_source = "inferred_from_search"
                    log_fn(f"  ⚠️ Auto-inferred category: {' > '.join(category_path)} — AI should confirm with user")
                elif rt_data.get("bestsellersRank"):
                    leaf = rt_data["bestsellersRank"][-1].get("category", "")
                    if leaf:
                        cat_result = api_caller("categories", {"categoryKeyword": leaf}, "categories")
                        cat_data = cat_result.get("data", [])
                        if cat_data:
                            category_path = cat_data[0].get("categoryPath")
                            category_source = "inferred_from_search"
                            log_fn(f"  ⚠️ Auto-inferred category: {' > '.join(category_path)} — AI should confirm with user")

    return category_path, category_source


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


# ─── Review Analysis: Prompt-as-Data Toolkit ───────────────────────────────
# Used when /reviews/analysis lacks aggregation (ASIN has <50 reviews or no
# daily snapshot). This module does NOT call any external LLM — it provides
# raw data, rendered prompts, and a final aggregator. The calling skill's own
# LLM performs the Map (per-review tagging) and Reduce (semantic clustering)
# steps, producing JSON that feeds back into `review-aggregate`.
#
# Caller flow:
#   1. apiclaw.py reviews-raw --asin X          → fetch raw reviews
#   2. For each review, render via:
#        apiclaw.py review-tag-prompt --review '<json>'
#      The caller's LLM produces JSON matching REVIEW_MAP_SCHEMA.
#   3. Collect per-dimension candidate phrases; for each dimension render:
#        apiclaw.py review-reduce-prompt --label-type <dim> --candidates '[...]'
#      The caller's LLM produces JSON matching REVIEW_REDUCE_SCHEMA.
#   4. apiclaw.py review-aggregate --reviews R --tagged T --clusters C
#      → emits consumerInsights compatible with /reviews/analysis.

REVIEW_MAP_CONCURRENCY = 20           # suggested map parallelism for caller
REVIEW_REDUCE_KEYWORDS_CHUNK = 150    # suggested chunk size when keywords dim is large
REALTIME_REVIEWS_MAX_PAGES = 10       # API hard cap = 100 reviews (10 pages × 10)

DIM_TO_LABELTYPE = {
    "mentioned_scenarios": "scenarios",
    "mentioned_issues": "issues",
    "mentioned_positives": "positives",
    "mentioned_improvements": "improvements",
    "mentioned_buying_factors": "buyingFactors",
    "mentioned_pain_points": "painPoints",
    "user_profiles": "userProfiles",
    "mentioned_usage_times": "usageTimes",
    "mentioned_usage_locations": "usageLocations",
    "mentioned_behaviors": "behaviors",
    "keywords": "keywords",
}

_MAP_ARRAY_FIELDS = list(DIM_TO_LABELTYPE.keys())

REVIEW_MAP_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "sentiment": {"type": "STRING", "enum": ["positive", "neutral", "negative"]},
        **{k: {"type": "ARRAY", "items": {"type": "STRING"}} for k in _MAP_ARRAY_FIELDS},
    },
    "required": ["sentiment"] + _MAP_ARRAY_FIELDS,
}

REVIEW_REDUCE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "clusters": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "canonical": {"type": "STRING"},
                    "members": {"type": "ARRAY", "items": {"type": "STRING"}},
                },
                "required": ["canonical", "members"],
            },
        },
    },
    "required": ["clusters"],
}


def render_review_map_prompt(review: dict, product_title: str = "", product_category: str = "") -> str:
    title = review.get("title") or ""
    body = review.get("body") or ""
    full = f"{title}. {body}" if title else body
    text = full[:500]
    rating = review.get("rating") or 3
    verified = bool(review.get("verifiedPurchase"))
    return f"""IMPORTANT: Respond ONLY with a JSON object matching the schema below. Output must be in English — translate non-English text before extracting.

You are an expert data extraction specialist analyzing product reviews. Extract only what is EXPLICITLY mentioned — do not infer.

JSON schema:
{{
  "sentiment": "positive" | "neutral" | "negative",
  "mentioned_scenarios": [string],      // max 5 noun phrases 1-3 words (Workouts, Gaming)
  "mentioned_issues": [string],         // max 5 Adjective+Noun for PRODUCT DEFECTS (Poor Sound Quality)
  "mentioned_positives": [string],      // max 5 Adjective+Noun for praised aspects (Comfortable Fit)
  "mentioned_improvements": [string],   // max 3 Verb+Noun explicit suggestions (Extend Battery Life)
  "mentioned_buying_factors": [string], // max 3 noun phrases for purchase reasons (Price Point)
  "mentioned_pain_points": [string],    // max 3 UX frustrations EXPERIENCED AFTER USE (see rule)
  "user_profiles": [string],            // max 3 identities stated EXPLICITLY (see rule)
  "mentioned_usage_times": [string],    // max 3 time/season phrases (Morning, Winter)
  "mentioned_usage_locations": [string],// max 3 location phrases (Gym, Home)
  "mentioned_behaviors": [string],      // max 5 Verb+Object (Taking Calls, Running)
  "keywords": [string]                  // 3-15 salient words from the review
}}

Rules:
- sentiment: positive (4-5 stars or praise), neutral (3 stars / mixed), negative (1-2 stars or complaint)
- pain_points = problems EXPERIENCED AFTER USE. NOT problems the product solves. If the reviewer says the product solved a prior problem (e.g. "cured my foot pain"), that belongs in positives, NOT pain_points.
- issues vs pain_points: issues = product defects (hardware/software fault); pain_points = UX frustrations
- user_profiles: include ONLY if the reviewer explicitly states an identity ("I'm a...", "As a..."). NEVER infer.
- consistent naming across reviews (e.g. always "Workouts", not "At the gym")
- use empty arrays [] for categories with no mentions, never null

INPUT:
Product Category: {product_category or '(unknown)'}
Product Title: {product_title or '(unknown)'}
Review Rating: {rating}/5 stars
Verified Purchase: {'Yes' if verified else 'No'}
Review Text:
\"\"\"{text}\"\"\"

Return ONLY the JSON object."""


def render_review_reduce_prompt(label_type: str, candidates: list) -> str:
    return f"""Normalize product-review tags. Group semantically equivalent phrases into clusters and pick a concise Title-Case canonical name (1-3 words) for each cluster.

Label type: {label_type}

Rules:
- A cluster contains phrases describing the SAME underlying concept.
- Every input phrase MUST appear in exactly one cluster's `members`. No drops, no duplicates across clusters.
- Phrases with no semantic neighbors go in their own single-member cluster (still Title-Case canonical).
- Case-insensitive matching. Preserve input phrase strings verbatim in `members`.

Return a JSON object matching:
{{"clusters": [{{"canonical": "Title Case", "members": ["phrase1", "phrase2"]}}]}}

Input phrases:
{json.dumps(candidates, ensure_ascii=False)}"""


def fetch_realtime_reviews_all(asin: str, marketplace: str = "US",
                                max_pages: int = REALTIME_REVIEWS_MAX_PAGES,
                                log_fn=None) -> dict:
    """Paginate /realtime/reviews with cursor; stop on null cursor or max_pages."""
    log = log_fn or (lambda m: None)
    reviews = []
    cursor = None
    pages = 0
    t0 = time.time()
    for i in range(1, max_pages + 1):
        params = {"asin": asin, "marketplace": marketplace}
        if cursor:
            params["cursor"] = cursor
        resp = api_call("realtime/reviews", params)
        if not resp.get("success"):
            break
        data = resp.get("data") or {}
        page_reviews = data.get("reviews") or []
        cursor = data.get("nextCursor")
        pages += 1
        reviews.extend(page_reviews)
        log(f"  page {i}: {len(page_reviews)} reviews, cursor={'yes' if cursor else 'end'}")
        if not cursor:
            break
    return {
        "reviews": reviews,
        "pages": pages,
        "capped": pages >= max_pages and cursor is not None,
        "fetchSeconds": round(time.time() - t0, 2),
    }


def aggregate_review_insights(reviews: list, tagged: list, clusters_per_dim: dict) -> dict:
    """Combine raw reviews + per-review Map tags + per-dimension Reduce clusters
    into a reviews/analysis-compatible aggregation. No LLM calls."""
    from collections import defaultdict

    if len(tagged) != len(reviews):
        raise ValueError(f"tagged length ({len(tagged)}) != reviews length ({len(reviews)})")

    total = len(reviews)
    ratings = [r.get("rating") or 0 for r in reviews]

    dim_phrase_reviews = {k: defaultdict(set) for k in DIM_TO_LABELTYPE}
    for i, tags in enumerate(tagged):
        if not isinstance(tags, dict):
            continue
        for dim in DIM_TO_LABELTYPE:
            for el in (tags.get(dim) or []):
                if not isinstance(el, str):
                    continue
                kl = el.strip().lower()
                if kl:
                    dim_phrase_reviews[dim][kl].add(i)

    insights = []
    for dim, phrases in dim_phrase_reviews.items():
        if not phrases:
            continue
        p2c = {}
        for cl in (clusters_per_dim.get(dim) or []):
            canon = (cl.get("canonical") or "").strip()
            if not canon:
                continue
            for m in (cl.get("members") or []):
                if not isinstance(m, str):
                    continue
                ml = m.strip().lower()
                if ml and ml not in p2c:
                    p2c[ml] = canon
        for ph in phrases:
            p2c.setdefault(ph, ph.title())

        canon_to_reviews = defaultdict(set)
        for phrase, rs in phrases.items():
            canon_to_reviews[p2c[phrase]].update(rs)

        lt = DIM_TO_LABELTYPE[dim]
        for canon, rs in canon_to_reviews.items():
            c = len(rs)
            avg = sum(ratings[i] for i in rs) / c if c else 0.0
            insights.append({
                "element": canon,
                "labelType": lt,
                "count": c,
                "reviewRate": round(c / total, 4),
                "avgRating": round(avg, 2),
            })
    insights.sort(key=lambda x: (x["labelType"], -x["count"]))

    sentiments = [(t or {}).get("sentiment") for t in tagged]
    sentiment_dist = {
        "positive": round(sum(1 for s in sentiments if s == "positive") / total, 4) if total else 0,
        "neutral": round(sum(1 for s in sentiments if s == "neutral") / total, 4) if total else 0,
        "negative": round(sum(1 for s in sentiments if s == "negative") / total, 4) if total else 0,
    }
    avg_rating = round(sum(ratings) / total, 2) if total else 0.0

    return {
        "success": True,
        "data": {
            "reviewCount": total,
            "avgRating": avg_rating,
            "sentimentDistribution": sentiment_dist,
            "consumerInsights": insights,
            "topKeywords": [
                {"element": it["element"], "count": it["count"]}
                for it in insights if it["labelType"] == "keywords"
            ][:20],
        },
        "_meta": {"source": "prompt-as-data-aggregation", "tagsApplied": total},
    }


def cmd_reviews_raw(args):
    log_fn = (lambda m: print(m, file=sys.stderr)) if args.verbose else None
    result = fetch_realtime_reviews_all(args.asin, args.marketplace, args.max_pages, log_fn=log_fn)
    output({
        "success": True,
        "data": result,
        "_query": {"endpoint": "realtime/reviews",
                   "params": {"asin": args.asin, "marketplace": args.marketplace,
                              "maxPages": args.max_pages}},
    })


def _load_json_arg(inline: str, path: str, name: str):
    """Load JSON from --<name> inline arg or --<name>-file path."""
    if inline and path:
        print(f"ERROR: provide either --{name} or --{name}-file, not both", file=sys.stderr)
        sys.exit(1)
    if inline:
        return json.loads(inline)
    if path:
        with open(path) as f:
            return json.load(f)
    print(f"ERROR: --{name} or --{name}-file is required", file=sys.stderr)
    sys.exit(1)


def cmd_review_tag_prompt(args):
    review = _load_json_arg(args.review, args.review_file, "review")
    prompt = render_review_map_prompt(
        review,
        product_title=args.product_title or "",
        product_category=args.product_category or "",
    )
    print(prompt)


def cmd_review_reduce_prompt(args):
    candidates = _load_json_arg(args.candidates, args.candidates_file, "candidates")
    if not isinstance(candidates, list):
        print("ERROR: candidates must be a JSON array of strings", file=sys.stderr)
        sys.exit(1)
    prompt = render_review_reduce_prompt(args.label_type, candidates)
    print(prompt)


def cmd_review_aggregate(args):
    with open(args.reviews) as f:
        reviews_data = json.load(f)
    if isinstance(reviews_data, dict):
        reviews = (reviews_data.get("data") or {}).get("reviews") or reviews_data.get("reviews") or []
    else:
        reviews = reviews_data

    with open(args.tagged) as f:
        tagged = json.load(f)
    with open(args.clusters) as f:
        clusters_per_dim = json.load(f)

    result = aggregate_review_insights(reviews, tagged, clusters_per_dim)
    result["_query"] = {"endpoint": "realtime/reviews+local-aggregate",
                        "params": {"reviews": args.reviews, "tagged": args.tagged,
                                    "clusters": args.clusters}}
    output(result)


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
    if args.page:
        params["page"] = args.page
    if args.sort:
        params["sortBy"] = args.sort
    if args.order:
        params["sortOrder"] = args.order

    result = api_call("markets/search", params)
    output(result, args.format)


def cmd_products(args):
    """Search products with filters (product selection)."""
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
        params["fulfillments"] = args.fulfillment
    if args.include_brands:
        params["includeBrands"] = [b.strip() for b in args.include_brands.split(",")]
    if args.exclude_brands:
        params["excludeBrands"] = [b.strip() for b in args.exclude_brands.split(",")]

    params["sortBy"] = args.sort or "monthlySalesFloor"
    params["sortOrder"] = args.order or "desc"
    params["pageSize"] = args.page_size or 20
    params["page"] = args.page or 1

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
        params["brandName"] = args.brand
    if args.asin:
        params["asin"] = args.asin
    if args.category:
        params["categoryPath"] = parse_category(args.category)

    params["dateRange"] = args.date_range or "30d"
    params["marketplace"] = args.marketplace or "US"
    params["page"] = args.page or 1
    params["sortBy"] = args.sort or "monthlySalesFloor"
    params["sortOrder"] = args.order or "desc"
    params["pageSize"] = args.page_size or 20

    result = api_call("products/competitors", params)
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
        "sortBy": "monthlySalesFloor",
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
        "sortBy": "monthlySalesFloor",
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
      4. Competitors: competitors + realtime/product (Top 5)
      5. Trends: history (Top 3, with ASIN retry)
      6. Consumer insights: reviews/analysis (3x category mode, fallback to ASIN)
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
    if not category_path:
        category_path, category_source = _resolve_category(safe_call, log, keyword=keyword, results=results)
        results["meta"]["category_source"] = category_source
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

    # 1a-fallback: deep-leaf categoryPath has no aggregation data on the
    # backend → downgrade to keyword-only mode so all subsequent steps use
    # categoryKeyword instead of categoryPath. Only applies when both keyword
    # and categoryPath were provided (otherwise we have nothing to fall back to).
    if category_path and keyword:
        m = results["market"] or {}
        m_data = m.get("data") or []
        m_total = (m.get("meta") or {}).get("total", 0)
        if m.get("success") is False or not m_data or m_total == 0:
            log(f"  → categoryPath {' > '.join(category_path)} returned empty; "
                f"downgrading to keyword-only mode for subsequent steps")
            results["meta"]["category_downgrade"] = {
                "from": category_path,
                "reason": "empty_aggregation",
            }
            category_path = None
            market_params = {"topN": "10", "pageSize": 20, "categoryKeyword": keyword}
            results["market"] = safe_call("markets/search", market_params,
                                          "market (keyword fallback)")

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
        prod_params = {"pageSize": 20, "page": page, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
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
                   "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitors", comp_params, "competitors")

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

    # Try history with Top 3, fallback to older ASINs
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
        r = _fetch_all_history(safe_call, round1_asins, thirty_days_ago, today, log_fn=log)
        history_data = r.get("data", [])

    # Round 2: Try oldest products if round 1 was empty
    if not history_data:
        round2_asins = [p.get("asin") for p in products_by_age if p.get("asin") not in tried_asins][:5]
        if round2_asins:
            log(f"  → Round 1 empty, trying older ASINs: {round2_asins}")
            tried_asins.update(round2_asins)
            r = _fetch_all_history(safe_call, round2_asins, thirty_days_ago, today, log_fn=log)
            history_data = r.get("data", [])

    results["product_history"] = {"data": history_data, "asins_tried": list(tried_asins)}
    log(f"  → {len(history_data)} history records from {len(tried_asins)} ASINs tried")
    results["meta"]["steps_completed"].append("trend_analysis")

    # ── Step 6: Consumer Insights ──
    log("Step 6/6: Consumer insights...")
    review_results = {}
    label_types = ["painPoints", "buyingFactors", "improvements"]

    # Priority 1: Category mode (single call, split client-side)
    category_mode_success = False
    if category_path:
        log("  → reviews/analysis category mode")
        r = safe_call("reviews/analysis", {
            "categoryPath": category_path,
            "mode": "category",
            "period": "6m",
        }, "reviews category")
        if r.get("success") and r.get("data", {}).get("consumerInsights"):
            category_mode_success = True
            for lt in label_types:
                review_results[lt] = _filter_review_insights(r, lt)

    # Priority 2: ASIN mode (if category failed)
    if not category_mode_success:
        log("  → Falling back to ASIN mode...")
        review_asins = [p.get("asin") for p in all_products if (p.get("ratingCount") or 0) >= 50][:3]
        if review_asins:
            log(f"  → reviews/analysis ASIN mode ({review_asins})")
            r = safe_call("reviews/analysis", {
                "asins": review_asins,
                "mode": "asin",
                "period": "6m",
            }, "reviews ASIN")
            for lt in label_types:
                review_results[lt] = _filter_review_insights(r, lt)

    results["reviews"] = review_results
    results["meta"]["review_mode"] = "category" if category_mode_success else "asin"
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
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=my_asin, results=results)
        results["meta"]["category_source"] = category_source

    # Step 1: Competitor Discovery
    log("Step 1/7: Competitor discovery...")
    prod_params = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["products"] = safe_call("products/search", prod_params, "products")

    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitors", comp_params, "competitors")
    results["meta"]["resolved_category"] = category_path
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
    r = _fetch_all_history(safe_call, history_asins[:8], thirty_ago, today, log_fn=log)
    results["product_history"] = {"data": r.get("data", []), "asins_tried": history_asins[:8]}
    results["meta"]["steps_completed"].append("historical_trends")

    # Step 6: Review Intelligence
    log("Step 6/7: Review intelligence...")
    review_results = {}
    for asin in top_asins[:5]:
        r = safe_call("reviews/analysis", {
            "asins": [asin], "mode": "asin", "period": "6m"
        }, f"reviews {asin}")
        if r.get("data") and r.get("data", {}).get("consumerInsights"):
            review_results[asin] = r
    if not review_results and category_path:
        log("  → Falling back to category mode...")
        r = safe_call("reviews/analysis", {
            "categoryPath": category_path, "mode": "category", "period": "6m"
        }, "reviews category")
        for lt in ["painPoints", "buyingFactors"]:
            review_results[lt] = _filter_review_insights(r, lt)
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_intelligence")

    # Step 7: Brand Drill-Down
    log("Step 7/7: Brand drill-down...")
    brands = results.get("brand_detail", {}).get("data", {}).get("brands", [])
    if brands:
        top_brand = brands[0].get("brandName")
        if top_brand:
            bp = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
            if keyword:
                bp["keyword"] = keyword
            if category_path:
                bp["categoryPath"] = category_path
            bp["includeBrands"] = [top_brand]
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
    Category is auto-detected from ASIN if not provided.
    """
    my_asin = args.my_asin
    keyword = args.keyword
    category = args.category

    if not my_asin:
        print("ERROR: --my-asin is required.", file=sys.stderr)
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

    # Step 1: Current Price Snapshot
    log("Step 1/8: Current price snapshot...")
    results["my_product"] = safe_call("realtime/product", {"asin": my_asin, "marketplace": "US"}, f"realtime {my_asin}")
    my_data = results["my_product"].get("data", {}) or {}
    if not my_data.get("title"):
        log(f"\n❌ ASIN '{my_asin}' not found or has no data. Please check the ASIN and try again.")
        results["error"] = {"code": "ASIN_NOT_FOUND", "message": f"ASIN '{my_asin}' not found or returned empty data"}
        output(results, args.format)
        return
    results["meta"]["steps_completed"].append("price_snapshot")

    # Step 1.5: Auto Category Detection
    if not category_path:
        # For pricing, we already have realtime data — extract directly first
        if my_data.get("categoryPath"):
            category_path = my_data["categoryPath"]
            results["meta"]["category_source"] = "asin_realtime"
            log(f"  → Auto-detected category: {' > '.join(category_path)}")
        elif my_data.get("bestsellersRank"):
            leaf = my_data["bestsellersRank"][-1].get("category", "")
            if leaf:
                log(f"  → Resolving category from BSR leaf: {leaf}")
                cat_result = safe_call("categories", {"categoryKeyword": leaf}, "categories")
                results["categories"] = cat_result
                cat_data = cat_result.get("data", [])
                if cat_data:
                    category_path = cat_data[0].get("categoryPath")
                    results["meta"]["category_source"] = "asin_bsr"
                    log(f"  → Auto-detected category: {' > '.join(category_path)}")
        # Fallback to keyword
        if not category_path and keyword:
            category_path, category_source = _resolve_category(safe_call, log, keyword=keyword, results=results)
            results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category"] = category_path

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
    prod_params = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["products"] = safe_call("products/search", prod_params, "products")

    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitors", comp_params, "competitors")
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
    r = _fetch_all_history(safe_call, history_asins, thirty_ago, today, log_fn=log)
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
        review_results["my_asin"] = safe_call("reviews/analysis", {
            "asins": [my_asin], "mode": "asin", "period": "6m"
        }, f"reviews {my_asin}")
    if comp_asins:
        review_results["top_comp"] = safe_call("reviews/analysis", {
            "asins": [comp_asins[0]], "mode": "asin", "period": "6m"
        }, f"reviews {comp_asins[0]}")
    if not review_results and category_path:
        r = safe_call("reviews/analysis", {
            "categoryPath": category_path, "mode": "category", "period": "6m"
        }, "reviews category")
        for lt in ["painPoints", "buyingFactors"]:
            review_results[lt] = _filter_review_insights(r, lt)
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_context")

    # Step 8: Price Drill-Down (opportunity band)
    log("Step 8/8: Price drill-down...")
    pbo_data = results.get("price_band_overview", {}).get("data", {})
    best_band = pbo_data.get("bestOpportunityBand", {}) if pbo_data else {}
    if best_band and best_band.get("sampleBandMinPrice") and best_band.get("sampleBandMaxPrice"):
        drill_params = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc",
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
    if not category_path:
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=tracked_asins[0] if tracked_asins else None, results=results)
        results["meta"]["category_source"] = category_source
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
    r = _fetch_all_history(safe_call, tracked_asins, seven_days_ago, today, log_fn=log)
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
    prod_params = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
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
            r = safe_call("reviews/analysis", {
                "asins": [review_asin],
                "mode": "asin",
                "period": "6m",
            }, f"reviews {review_asin}")
            review_results["painPoints"] = _filter_review_insights(r, "painPoints")
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
    if not category_path:
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=my_asin, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category"] = category_path

    # Step 1: Audit Target
    log("Step 1/7: Auditing target listing...")
    results["target_realtime"] = safe_call("realtime/product", {"asin": my_asin, "marketplace": "US"}, f"realtime {my_asin}")
    results["meta"]["steps_completed"].append("audit_target")

    # Step 2: Category Leaders
    log("Step 2/7: Finding category leaders...")
    prod_params = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        prod_params["keyword"] = keyword
    if category_path:
        prod_params["categoryPath"] = category_path
    results["leader_products"] = safe_call("products/search", prod_params, "products leaders")

    comp_params = {"pageSize": 20, "dateRange": "30d", "marketplace": "US", "page": 1,
                   "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitors", comp_params, "competitors")
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
        log(f"  → reviews/analysis ASIN mode: {my_asin}")
        review_results["my_asin"] = safe_call("reviews/analysis", {
            "asins": [my_asin], "mode": "asin", "period": "6m"
        }, f"reviews {my_asin}")
    if leader_asins:
        top_leader = leader_asins[0]
        log(f"  → reviews/analysis ASIN mode: {top_leader}")
        review_results["top_leader"] = safe_call("reviews/analysis", {
            "asins": [top_leader], "mode": "asin", "period": "6m"
        }, f"reviews {top_leader}")
    # Category fallback
    if not review_results and category_path:
        log("  → Falling back to category mode...")
        r = safe_call("reviews/analysis", {
            "categoryPath": category_path, "mode": "category", "period": "6m"
        }, "reviews category")
        for lt in ["painPoints", "buyingFactors", "improvements"]:
            review_results[lt] = _filter_review_insights(r, lt)
    results["reviews"] = review_results
    results["meta"]["steps_completed"].append("review_intelligence")

    # Step 7: Trend Context
    log("Step 7/7: Trend context...")
    today = time.strftime("%Y-%m-%d")
    thirty_ago = time.strftime("%Y-%m-%d", time.localtime(time.time() - 30 * 86400))
    history_asins = [my_asin] + leader_asins[:2]
    r = _fetch_all_history(safe_call, history_asins, thirty_ago, today, log_fn=log)
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
    1. Mode-based: uses 13 preset modes (emerging, underserved, etc.)
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
        modes = ["emerging", "underserved", "high-demand-low-barrier"]  # Default modes
    
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
    if not category_path:
        category_path, category_source = _resolve_category(safe_call, log, keyword=keyword, results=results)
        results["meta"]["category_source"] = category_source
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
            prod_params = {"pageSize": 20, "page": page, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
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
    sorted_candidates = sorted(all_candidates.values(), key=lambda x: x.get("monthlySalesFloor") or 0, reverse=True)
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
    r = _fetch_all_history(safe_call, top_asins[:5], thirty_ago, today, log_fn=log)
    results["product_history"] = {"data": r.get("data", []), "asins_tried": top_asins[:5]}
    results["meta"]["steps_completed"].append("trend_check")

    # Step 6: Consumer Insights (Top 3, category mode first)
    log("Step 6/6: Consumer insights...")
    review_results = {}
    if category_path:
        log("  → reviews/analysis category mode")
        r = safe_call("reviews/analysis", {
            "categoryPath": category_path, "mode": "category", "period": "6m"
        }, "reviews category")
        if r.get("data") and r.get("data", {}).get("consumerInsights"):
            for lt in ["painPoints", "buyingFactors", "improvements"]:
                review_results[lt] = _filter_review_insights(r, lt)
    if not review_results:
        log("  → Falling back to ASIN mode...")
        review_asins = [a for a in top_asins[:3]]
        if review_asins:
            r = safe_call("reviews/analysis", {
                "asins": review_asins, "mode": "asin", "period": "6m"
            }, "reviews ASIN")
            for lt in ["painPoints", "buyingFactors", "improvements"]:
                review_results[lt] = _filter_review_insights(r, lt)
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
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=target_asin, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category"] = category_path

    # Step 1: Target Identification
    log("Step 1/5: Target identification...")
    if target_asin:
        results["target_realtime"] = safe_call("realtime/product", {"asin": target_asin, "marketplace": "US"}, f"realtime {target_asin}")
    if not target_asin and keyword:
        prod_params = {"pageSize": 20, "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
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
    # Target ASIN reviews (single call, split client-side)
    if target_asin:
        log(f"  → {target_asin}: all dimensions")
        r = safe_call("reviews/analysis", {
            "asins": [target_asin], "mode": "asin", "period": "6m"
        }, "reviews target")
        for lt in label_types:
            review_results[f"target_{lt}"] = _filter_review_insights(r, lt)

    # Competitor comparison (top 2, single call each)
    for comp_asin in comp_asins[:2]:
        log(f"  → Competitor {comp_asin}: all dimensions")
        r = safe_call("reviews/analysis", {
            "asins": [comp_asin], "mode": "asin", "period": "6m"
        }, f"reviews comp {comp_asin}")
        review_results[f"comp_{comp_asin}_painPoints"] = _filter_review_insights(r, "painPoints")
        review_results[f"comp_{comp_asin}_positives"] = _filter_review_insights(r, "positives")
    
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
                   "sortBy": "monthlySalesFloor", "sortOrder": "desc"}
    if keyword:
        comp_params["keyword"] = keyword
    if category_path:
        comp_params["categoryPath"] = category_path
    results["competitors"] = safe_call("products/competitors", comp_params, "competitors")
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
        r = _fetch_all_history(safe_call, hist_asins, thirty_ago, today, log_fn=log)
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
        ("products/competitors", {"keyword": "test", "pageSize": 1}, "Competitor lookup"),
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

    if args.period:
        params["period"] = args.period

    result = api_call("reviews/analysis", params)

    # Client-side filtering by label type (v2 API returns all dimensions in one call)
    if args.label_type and result.get("data") and result["data"].get("consumerInsights"):
        requested = [t.strip() for t in args.label_type.split(",")]
        result["data"]["consumerInsights"] = [
            i for i in result["data"]["consumerInsights"]
            if i.get("labelType") in requested
        ]

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
    params["page"] = args.page or 1
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
    params["page"] = args.page or 1
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
    params["page"] = args.page or 1
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
    params["page"] = args.page or 1
    result = api_call("products/brand-detail", params)
    output(result, args.format)


def cmd_product_history(args):
    """Get historical data (price, BSR, sales) for ASINs over a date range."""
    asins = [a.strip() for a in args.asins.split(",")]

    def _api_caller(endpoint, p, label=""):
        return api_call(endpoint, p)

    result = _fetch_all_history(_api_caller, asins, args.start_date, args.end_date)
    output(result, args.format)


# ─── CLI Setup ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="APIClaw CLI — Amazon Product Research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog="""
Examples:
  %(prog)s categories --keyword "pet supplies"
  %(prog)s market --category "Pet Supplies,Dogs" --topn 10
  %(prog)s products --keyword "yoga mat" --mode emerging
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
    p_cat = sub.add_parser("categories", help="Query Amazon category tree", allow_abbrev=False)
    p_cat.add_argument("--keyword", help="Search categories by keyword")
    p_cat.add_argument("--category", help="Exact category path (comma-separated)")
    p_cat.add_argument("--parent", help="Get child categories (comma-separated parent path)")
    p_cat.set_defaults(func=cmd_categories)

    # ── market ──
    p_mkt = sub.add_parser("market", help="Search market-level data for a category", allow_abbrev=False)
    p_mkt.add_argument("--category", help="Category path (comma-separated)")
    p_mkt.add_argument("--keyword", help="Category keyword")
    p_mkt.add_argument("--topn", type=int, default=10, help="Top N for concentration analysis (default: 10)")
    p_mkt.add_argument("--page-size", type=int, default=20)
    p_mkt.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_mkt.add_argument("--sort", help="Sort field")
    p_mkt.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_mkt.set_defaults(func=cmd_market)

    # ── products ──
    p_prod = sub.add_parser("products", help="Search products with filters (product selection)", allow_abbrev=False)
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
    p_prod.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_prod.add_argument("--sort", help="Sort field (default: monthlySales)")
    p_prod.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_prod.set_defaults(func=cmd_products)

    # ── competitors ──
    p_comp = sub.add_parser("competitors", help="Look up competitors", allow_abbrev=False)
    p_comp.add_argument("--keyword", help="Search keyword")
    p_comp.add_argument("--brand", help="Brand filter")
    p_comp.add_argument("--asin", help="ASIN filter")
    p_comp.add_argument("--category", help="Category path (comma-separated)")
    p_comp.add_argument("--date-range", default="30d", help="Date range (default: 30d)")
    p_comp.add_argument("--marketplace", default="US", help="Marketplace (default: US)")
    p_comp.add_argument("--page", type=int, default=1, help="Page number")
    p_comp.add_argument("--page-size", type=int, default=20)
    p_comp.add_argument("--sort", help="Sort field (default: monthlySalesFloor)")
    p_comp.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_comp.set_defaults(func=cmd_competitors)

    # ── product (single ASIN) ──
    p_single = sub.add_parser("product", help="Get real-time details for one ASIN", allow_abbrev=False)
    p_single.add_argument("--asin", required=True, help="ASIN (required)")
    p_single.add_argument("--marketplace", default="US",
                          help="Marketplace: US/UK/DE/FR/IT/ES/JP/CA/AU/IN/MX/BR (default: US)")
    p_single.set_defaults(func=cmd_product)

    # ── report (composite) ──
    p_report = sub.add_parser("report", help="Full market analysis report (composite workflow)", allow_abbrev=False)
    p_report.add_argument("--keyword", required=True, help="Category/niche keyword")
    p_report.add_argument("--topn", type=int, default=10, help="Top N (default: 10)")
    p_report.set_defaults(func=cmd_report)

    # ── opportunity (composite) ──
    p_opp = sub.add_parser("opportunity", help="Product opportunity discovery (composite workflow)", allow_abbrev=False)
    p_opp.add_argument("--keyword", required=True, help="Category/niche keyword")
    p_opp.add_argument("--mode", help="Product search mode preset")
    p_opp.set_defaults(func=cmd_opportunity)

    # ── market-entry (composite: full analysis) ──
    p_me = sub.add_parser("market-entry", help="Full market entry analysis (runs ALL endpoints automatically)", allow_abbrev=False)
    p_me.add_argument("--keyword", help="Product keyword or niche")
    p_me.add_argument("--category", help="Category path (e.g. 'Sports & Outdoors>Sports Sunglasses')")
    p_me.set_defaults(func=cmd_market_entry)

    # ── competitor-analysis (composite) ──
    p_ca = sub.add_parser("competitor-analysis", help="Full competitor war room analysis", allow_abbrev=False)
    p_ca.add_argument("--keyword", help="Product keyword to discover competitors")
    p_ca.add_argument("--my-asin", help="Your product ASIN (optional)")
    p_ca.add_argument("--category", help="Category path")
    p_ca.set_defaults(func=cmd_competitor_analysis)

    # ── pricing-analysis (composite) ──
    p_pa = sub.add_parser("pricing-analysis", help="Full pricing analysis with competitor benchmarking", allow_abbrev=False)
    p_pa.add_argument("--my-asin", required=True, help="Your product ASIN")
    p_pa.add_argument("--keyword", help="Product keyword for market context")
    p_pa.add_argument("--category", help="Category path")
    p_pa.set_defaults(func=cmd_pricing_analysis)

    # ── daily-radar (composite) ──
    p_dr = sub.add_parser("daily-radar", help="Daily market monitoring scan (runs all tracking endpoints)", allow_abbrev=False)
    p_dr.add_argument("--asins", required=True, help="Tracked ASINs (comma-separated, your products + competitors)")
    p_dr.add_argument("--keyword", help="Category keyword for market monitoring")
    p_dr.add_argument("--category", help="Category path")
    p_dr.set_defaults(func=cmd_daily_radar)

    # ── listing-audit (composite) ──
    p_la = sub.add_parser("listing-audit", help="Full listing audit against category leaders", allow_abbrev=False)
    p_la.add_argument("--my-asin", required=True, help="ASIN to audit")
    p_la.add_argument("--keyword", help="Primary keyword for benchmark context")
    p_la.add_argument("--category", help="Category path")
    p_la.set_defaults(func=cmd_listing_audit)

    # ── opportunity-scan (composite) ──
    p_os = sub.add_parser("opportunity-scan", help="Multi-mode product opportunity discovery", allow_abbrev=False)
    p_os.add_argument("--keyword", help="Category keyword to scan")
    p_os.add_argument("--category", help="Category path")
    p_os.add_argument("--modes", help="Scan modes (comma-separated, e.g. emerging,underserved,high-demand-low-barrier). Omit to use custom filters only.")
    p_os.add_argument("--sales-min", type=int, help="Min monthly sales (e.g. 300)")
    p_os.add_argument("--sales-max", type=int, help="Max monthly sales")
    p_os.add_argument("--ratings-max", type=int, help="Max review count (e.g. 100 for blue ocean)")
    p_os.add_argument("--price-min", type=float, help="Min price (e.g. 15)")
    p_os.add_argument("--price-max", type=float, help="Max price (e.g. 35)")
    p_os.add_argument("--rating-max", type=float, help="Max rating (e.g. 4.3 for improvement opportunity)")
    p_os.add_argument("--rating-min", type=float, help="Min rating")
    p_os.set_defaults(func=cmd_opportunity_scan)

    # ── review-deepdive (composite) ──
    p_rd = sub.add_parser("review-deepdive", help="Full 11-dimension review intelligence analysis", allow_abbrev=False)
    p_rd.add_argument("--target-asin", help="ASIN to analyze in depth")
    p_rd.add_argument("--keyword", help="Keyword to find target (if no ASIN)")
    p_rd.add_argument("--comp-asins", help="Competitor ASINs for comparison (comma-separated)")
    p_rd.add_argument("--category", help="Category path")
    p_rd.set_defaults(func=cmd_review_deepdive)

    # ── reviews-raw (realtime/reviews with cursor pagination, up to 100 reviews) ──
    p_rr = sub.add_parser("reviews-raw", help="Fetch raw reviews from realtime/reviews (cap 100, early-exit on null cursor)", allow_abbrev=False)
    p_rr.add_argument("--asin", required=True)
    p_rr.add_argument("--marketplace", default="US", choices=["US", "UK"])
    p_rr.add_argument("--max-pages", type=int, default=REALTIME_REVIEWS_MAX_PAGES,
                      help=f"Max pages to fetch (10 reviews each, default {REALTIME_REVIEWS_MAX_PAGES})")
    p_rr.add_argument("--verbose", action="store_true")
    p_rr.set_defaults(func=cmd_reviews_raw)

    # ── review-tag-prompt (render Map prompt for one review — caller's LLM runs it) ──
    p_rtp = sub.add_parser("review-tag-prompt", help="Render the per-review Map prompt (caller's own LLM runs it)", allow_abbrev=False)
    p_rtp.add_argument("--review", help="Review object as JSON string")
    p_rtp.add_argument("--review-file", help="Path to JSON file containing a single review object")
    p_rtp.add_argument("--product-title", help="Optional product title context")
    p_rtp.add_argument("--product-category", help="Optional product category context")
    p_rtp.set_defaults(func=cmd_review_tag_prompt)

    # ── review-reduce-prompt (render Reduce prompt for one dimension — caller's LLM runs it) ──
    p_rrp = sub.add_parser("review-reduce-prompt", help="Render the per-dimension Reduce prompt (caller's own LLM runs it)", allow_abbrev=False)
    p_rrp.add_argument("--label-type", required=True,
                       help="Dimension to cluster (scenarios, issues, positives, improvements, buyingFactors, painPoints, userProfiles, usageTimes, usageLocations, behaviors, keywords)")
    p_rrp.add_argument("--candidates", help="Candidate phrases as JSON array string")
    p_rrp.add_argument("--candidates-file", help="Path to JSON file containing candidate phrases array")
    p_rrp.set_defaults(func=cmd_review_reduce_prompt)

    # ── review-aggregate (build reviews/analysis-compatible output from tags + clusters) ──
    p_rag = sub.add_parser("review-aggregate", help="Aggregate per-review tags + per-dim clusters into consumerInsights", allow_abbrev=False)
    p_rag.add_argument("--reviews", required=True, help="Path to JSON from reviews-raw (or raw reviews array)")
    p_rag.add_argument("--tagged", required=True, help="Path to JSON array of Map outputs (same order as reviews)")
    p_rag.add_argument("--clusters", required=True, help="Path to JSON {dim_key: [{canonical, members}]} from Reduce")
    p_rag.set_defaults(func=cmd_review_aggregate)

    # ── analyze (reviews) ──
    p_analyze = sub.add_parser("analyze", help="AI-powered review analysis", allow_abbrev=False)
    p_analyze.add_argument("--asin", help="Single ASIN")
    p_analyze.add_argument("--asins", help="Multiple ASINs (comma-separated)")
    p_analyze.add_argument("--category", help="Category path")
    p_analyze.add_argument("--label-type", help="Filter dimensions (comma-separated)")
    p_analyze.add_argument("--period", help="Time period: 1m, 3m, 6m, 1y, 2y", default="6m")
    p_analyze.set_defaults(func=cmd_analyze)

    # ── price-band-overview ──
    p_pbo = sub.add_parser("price-band-overview", help="Price band overview (hottest & best opportunity)", allow_abbrev=False)
    p_pbo.add_argument("--keyword", help="Search keyword")
    p_pbo.add_argument("--category", help="Category path")
    p_pbo.add_argument("--page-size", type=int, default=20)
    p_pbo.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_pbo.set_defaults(func=cmd_price_band_overview)

    # ── price-band-detail ──
    p_pbd = sub.add_parser("price-band-detail", help="Price band detailed breakdown", allow_abbrev=False)
    p_pbd.add_argument("--keyword", help="Search keyword")
    p_pbd.add_argument("--category", help="Category path")
    p_pbd.add_argument("--page-size", type=int, default=20)
    p_pbd.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_pbd.set_defaults(func=cmd_price_band_detail)

    # ── brand-overview ──
    p_bo = sub.add_parser("brand-overview", help="Brand landscape overview", allow_abbrev=False)
    p_bo.add_argument("--keyword", help="Search keyword")
    p_bo.add_argument("--category", help="Category path")
    p_bo.add_argument("--page-size", type=int, default=20)
    p_bo.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_bo.set_defaults(func=cmd_brand_overview)

    # ── brand-detail ──
    p_bd = sub.add_parser("brand-detail", help="Brand ranking with per-brand stats", allow_abbrev=False)
    p_bd.add_argument("--keyword", help="Search keyword")
    p_bd.add_argument("--category", help="Category path")
    p_bd.add_argument("--page-size", type=int, default=20)
    p_bd.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_bd.set_defaults(func=cmd_brand_detail)

    # ── history ──
    p_ph = sub.add_parser("history", help="Historical data for ASINs", allow_abbrev=False)
    p_ph.add_argument("--asins", required=True, help="ASINs (comma-separated)")
    p_ph.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    p_ph.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    p_ph.set_defaults(func=cmd_product_history)

    # ── check (API self-check) ──
    p_check = sub.add_parser("check", help="Fetch latest OpenAPI spec to verify available endpoints", allow_abbrev=False)
    p_check.set_defaults(func=cmd_check)

    args, unknown = parser.parse_known_args()
    if unknown:
        cmd = sys.argv[1] if len(sys.argv) > 1 else ""
        print(f"ERROR: Unrecognized argument(s): {' '.join(unknown)}", file=sys.stderr)
        print(f"Run 'apiclaw.py {cmd} --help' to see valid options.", file=sys.stderr)
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()

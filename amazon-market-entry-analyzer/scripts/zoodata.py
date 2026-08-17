#!/usr/bin/env python3
# ============================================================
# Canonical source - do not edit copies under amazon-* skill directories directly
# Source location: zoodata/scripts/zoodata.py
# Sync method: pre-commit hook auto-copy or bash scripts/sync-scripts.sh
# ============================================================
"""
ZooData CLI — Amazon Product Research via ZooData API

Single-script interface for all 11 ZooData endpoints + composite workflows.
Handles authentication, retries, rate limits, parameter quirks, and output formatting.

Usage:
    python zoodata.py categories --keyword "pet supplies"
    python zoodata.py market --category "Pet Supplies" --topn 10
    python zoodata.py products --keyword "yoga mat" --mode emerging
    python zoodata.py competitors --keyword "wireless earbuds"
    python zoodata.py product --asin B09V3KXJPB
    python zoodata.py report --keyword "pet supplies"
    python zoodata.py opportunity --keyword "pet supplies"
    python zoodata.py keyword-detail --keywords "yoga mat,pilates mat" --date 2026-07-12
    python zoodata.py keyword-market-profile --keywords "yoga mat,pilates mat" --date 2026-07-12
    python zoodata.py keyword-trend --keywords "yoga mat,pilates mat" --date-from 2026-06-01 --date-to 2026-07-12
    python zoodata.py keyword-extends --query "yoga mat"
    python zoodata.py keyword-search-results --keyword "yoga mat" --date 2025-06-01
    python zoodata.py keyword-competitor-product-keywords --asin B09V3KXJPB --date 2025-06-01
    python zoodata.py keyword-product-traffic-terms --asin B09V3KXJPB --date 2025-06-01
    python zoodata.py product-traffic-terms-profile --asins "B09V3KXJPB,B07FR2V8SH" --date 2025-06-01
    python zoodata.py product-traffic-terms-timeline --asin B09V3KXJPB --keywords "yoga mat,pilates mat" --date-from 2026-07-06 --date-to 2026-07-12

Environment:
    ZOODATA_API_KEY — Required. Get one at https://zoodata.ai/en/api-keys
"""

import argparse
import contextlib
import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
import re
from datetime import date

# ─── Configuration ───────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "https://api.zoodata.ai/openapi/v2"
API_BASE_PATH = "/openapi/v2"
KEYWORD_DATE_RANGE_MAX_DAYS = 93
KEYWORD_TIMELINE_MAX_DAYS = 61


def _host_of(url):
    try:
        from urllib.parse import urlparse
        return (urlparse(url if "://" in url else f"https://{url}").hostname or "").lower()
    except Exception:
        return ""


def _is_trusted_host(url):
    """True only for ZooData hosts and localhost — the sole destinations the API
    key (Bearer token) may be sent to. Any other host is untrusted and the key
    is withheld (see api_call), so credentials never reach an arbitrary host."""
    host = _host_of(url)
    return host == "zoodata.ai" or host.endswith(".zoodata.ai") or host in ("localhost", "127.0.0.1")


def _resolve_base_url():
    """Resolve API base URL, allowing zoodata.ai / localhost hosts via ZOODATA_BASE_URL."""
    configured = os.environ.get("ZOODATA_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    if configured.rstrip("/") != DEFAULT_BASE_URL.rstrip("/") and not _is_trusted_host(configured):
        print(f"WARNING: ZOODATA_BASE_URL points at untrusted host '{_host_of(configured)}'. "
              "Your API key (Bearer token) will NOT be sent there — requests to untrusted "
              "hosts are refused. Use a zoodata.ai host or localhost.",
              file=sys.stderr)
    if configured.endswith(API_BASE_PATH):
        return configured
    return f"{configured}{API_BASE_PATH}"


BASE_URL = _resolve_base_url()  # ZooData API base URL
BASE_URL_TRUSTED = _is_trusted_host(BASE_URL)  # gates Bearer-token transmission
API_DOCS = "https://api.zoodata.ai/api-docs"   # API documentation URL
MAX_RETRIES = 3       # Fixed attempt budget for HTTP and network failures
RETRY_DELAY = 2       # Initial retry delay in seconds; doubles on each retry
REALTIME_EMPTY_RETRIES = 3  # Total attempts when realtime/product returns a transient 200-empty (scrape miss)
MIN_REQUEST_INTERVAL = 0.6  # Minimum seconds between requests (100 req/min = 0.6s)
REQUEST_TIMEOUT = 60  # Request timeout in seconds; realtime/product can be slow (up to 30s)

# API calls return structured errors so composite commands can finish collecting
# partial results.  Track those errors separately so the CLI still exits non-zero
# after printing the complete machine-readable response for the calling agent.
_cli_had_error = False

# The agent-facing CLI exposes exactly one result channel per invocation.
# Commands that reach output() emit one final JSON document on stdout and any
# progress/retry diagnostics produced along the way are suppressed. Failures
# that occur before a structured result exists keep using stderr exclusively.
_cli_emitted_output = False

# Global request pacer — prevents burst rate limit violations
_last_request_time = 0.0


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 13 built-in product selection modes
# Each maps to a set of products/search filter parameters
PRODUCT_MODES = {
    "fast-movers":              {"monthlySalesMin": 300, "salesGrowthRateMin": 0.1},
    "emerging":                 {"monthlySalesMax": 600, "salesGrowthRateMin": 0.1, "listingAge": "180d"},
    "single-variant":           {"salesGrowthRateMin": 0.2, "variantCountMax": 1, "listingAge": "180d"},
    "high-demand-low-barrier":  {"monthlySalesMin": 300, "ratingCountMax": 50, "listingAge": "180d"},
    "long-tail":                {"bsrMin": 10000, "bsrMax": 50000, "priceMax": 30, "sellerCountMax": 1, "monthlySalesMax": 300},
    "underserved":              {"monthlySalesMin": 300, "ratingMax": 3.7, "listingAge": "180d"},
    "new-release":              {"monthlySalesMax": 500, "badges": ["newRelease"], "fulfillments": ["FBA", "FBM"]},
    "fbm-friendly":             {"monthlySalesMin": 300, "fulfillments": ["FBM"], "listingAge": "180d"},
    "low-price":                {"priceMax": 10},
    "broad-catalog":            {"bsrGrowthRateMin": 0.99, "ratingCountMax": 10, "listingAge": "90d"},
    "selective-catalog":        {"bsrGrowthRateMin": 0.99, "listingAge": "90d"},
    "speculative":              {"monthlySalesMin": 600, "sellerCountMin": 3, "listingAge": "180d"},
    # "beginner" mode disabled — excludeKeywords filter not working
    "top-bsr":                  {"subBsrMax": 1000},
}

# ─── API Client ──────────────────────────────────────────────────────────────

def _read_config_api_key(path):
    """Return the api_key from a JSON config file, or None if absent/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return (json.load(f).get("api_key") or "").strip() or None
    except (json.JSONDecodeError, IOError):
        return None


def _load_command_allowlist():
    """
    Per-skill command-allowlist manifest.

    The shared CLI ships byte-identical inside every skill bundle; the
    `allowed-commands.json` manifest next to this script scopes which
    subcommands the bundling skill may invoke. Returns a set of command
    names, or None when no manifest exists (canonical copy / the zoodata
    data-layer reference skill expose the full surface). A malformed
    manifest fails closed: exit 2 with a diagnostic, never a silent
    full-surface fallback.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "allowed-commands.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            commands = json.load(f)["allowedCommands"]
        if (not isinstance(commands, list) or not commands
                or not all(isinstance(c, str) and c for c in commands)):
            raise ValueError("allowedCommands must be a non-empty list of strings")
        return set(commands)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"ERROR: invalid command-allowlist manifest allowed-commands.json ({path}): {e}",
              file=sys.stderr)
        print("Refusing to run (fail-closed). Restore the manifest from the "
              "published skill bundle or reinstall the skill.", file=sys.stderr)
        sys.exit(2)


def _enforce_command_allowlist(command, fmt="json"):
    """Refuse subcommands outside the bundling skill's manifest.

    The refusal is emitted as valid structured JSON WITHOUT the terminal
    interface-failure action token: per the shared CLI contract, non-zero
    exit with valid JSON and no token is a documented non-terminal error,
    so the calling agent selects a documented command instead of stopping
    the turn. No API request is made and no credits are consumed.
    """
    allowed = _load_command_allowlist()
    if allowed is None or command in allowed:
        return
    refusal = {
        "success": False,
        "error": {
            "status": "COMMAND_NOT_ALLOWED",
            "message": (
                f"Subcommand '{command}' is outside this skill's documented "
                f"command set. Allowed commands: {', '.join(sorted(allowed))}. "
                "No API request was made and no credits were consumed. "
                "The full command surface remains available via the zoodata "
                "data-layer reference skill (ships no manifest)."
            ),
        },
        "_query": {"endpoint": None, "params": {"command": command}},
    }
    indent = None if fmt == "compact" else 2
    print(json.dumps(refusal, ensure_ascii=False, indent=indent))
    sys.exit(2)


def _resolve_credential():
    """
    Resolve the ZooData API key. Returns the key string or None.
    Used by BOTH get_api_key() and cmd_check() so the two stay in sync —
    a divergence here was a real bug (check said configured, real calls failed).

    Sources, in order:
      1. ZOODATA_API_KEY env var
      2. ~/.zoodata/config.json

    A selected key remains authoritative even if an API request later
    rejects it; request handling must not fall through here.

    The legacy fallbacks (APICLAW_API_KEY env var, ~/.apiclaw/config.json)
    were removed: the CLI reads no credential source beyond the two it
    declares. The former {skill_dir}/config.json fallback was removed for
    security: the skill directory ships inside the published bundle, so a
    key placed there would be published publicly.
    """
    key = os.environ.get("ZOODATA_API_KEY", "").strip()
    if key:
        return key

    return _read_config_api_key(os.path.expanduser("~/.zoodata/config.json"))


def get_api_key():
    """Get API key for API calls. Exits with guidance if no key is found."""
    key = _resolve_credential()
    if key:
        return key

    print("ERROR: API Key not found.", file=sys.stderr)
    print("", file=sys.stderr)
    if os.environ.get("APICLAW_API_KEY", "").strip():
        print("  NOTE: APICLAW_API_KEY is set but no longer read (legacy source removed).", file=sys.stderr)
        print("  Rename it: export ZOODATA_API_KEY=\"$APICLAW_API_KEY\"", file=sys.stderr)
        print("", file=sys.stderr)
    print("Please configure your API Key using one of these methods:", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Method 1: Environment variable (recommended — no file written)", file=sys.stderr)
    print("    export ZOODATA_API_KEY='hms_live_yourkey'", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Method 2: User-home config (persistent, shared across all skills)", file=sys.stderr)
    print("    mkdir -p ~/.zoodata && chmod 700 ~/.zoodata", file=sys.stderr)
    print('    (umask 077; echo \'{"api_key":"hms_live_yourkey"}\' > ~/.zoodata/config.json)', file=sys.stderr)
    print("    # keep the file private (0600) — it holds a bearer credential", file=sys.stderr)
    print("", file=sys.stderr)
    print("Get a free key at https://zoodata.ai/en/api-keys", file=sys.stderr)
    sys.exit(1)


class _CreditTracker:
    """Accumulates real API credit consumption across every api_call() in one
    CLI invocation. Composite commands fan out to many endpoints, so without a
    running total their output would surface only one internal call's figure
    (or none). Hooking every request here — the sole HTTP site — never misses
    an internal call, even review pages that the merged output drops."""

    def __init__(self):
        self.consumed = 0.0          # sum of display `creditsConsumed`
        self.consumed_exact = 0.0    # sum of `creditsConsumedExact`
        self.remaining = None        # last display `creditsRemaining`
        self.remaining_exact = None  # last `creditsRemainingExact`
        self.calls = 0

    def record(self, meta):
        if not isinstance(meta, dict):
            return
        d = meta.get("creditsConsumed")
        e = meta.get("creditsConsumedExact")
        d = d if isinstance(d, (int, float)) else None
        e = e if isinstance(e, (int, float)) else None
        # Keep display and exact tallies separate; fall each back to the other
        # when the API omits one, so neither total is understated.
        disp = d if d is not None else e
        exact = e if e is not None else d
        if disp is not None:
            self.consumed += disp
            self.consumed_exact += exact if exact is not None else disp
            self.calls += 1
        rd = meta.get("creditsRemaining")
        if isinstance(rd, (int, float)):
            self.remaining = rd
        re_ = meta.get("creditsRemainingExact")
        if isinstance(re_, (int, float)):
            self.remaining_exact = re_


_CREDITS = _CreditTracker()


def _annotate_credits(payload):
    """Stamp the invocation's total credit consumption onto a dict payload's
    top-level `meta` so every command that hits the API reports an accurate
    total. For a single-endpoint response the display/exact totals equal that
    call's own figures (no change in meaning); for a composite they sum every
    internal call. A `meta` block is synthesised when the payload has none
    (e.g. `reviews-raw`, which fans out over review pages)."""
    if not isinstance(payload, dict) or _CREDITS.calls == 0:
        return
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        meta = {}
        payload["meta"] = meta
    disp = _CREDITS.consumed
    meta["creditsConsumed"] = int(disp) if float(disp).is_integer() else disp
    meta["creditsConsumedExact"] = _CREDITS.consumed_exact
    if _CREDITS.remaining is not None:
        meta["creditsRemaining"] = _CREDITS.remaining
    if _CREDITS.remaining_exact is not None:
        meta["creditsRemainingExact"] = _CREDITS.remaining_exact
    meta["apiCalls"] = _CREDITS.calls


def api_call(endpoint: str, params: dict) -> dict:
    """
    Make a POST request to ZooData API with retry and error handling.

    Returns the parsed JSON response with _query and authoritative _transport
    metadata. Structured non-2xx response bodies are preserved for the caller.
    """
    global _last_request_time

    url = f"{BASE_URL}/{endpoint}"

    if not BASE_URL_TRUSTED:
        print(f"ERROR: refusing to send your API key to untrusted host '{_host_of(BASE_URL)}'. "
              "Set ZOODATA_BASE_URL to a zoodata.ai host or localhost, or unset it.",
              file=sys.stderr)
        sys.exit(1)

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
        "User-Agent": "ZooData-CLI/1.0 (Python)",
    }

    # Rate-limit pacing: enforce minimum interval between requests
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)

    delay = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        _last_request_time = time.monotonic()
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                transport_status = getattr(resp, "status", None)
                if not isinstance(transport_status, int):
                    transport_status = resp.getcode()
                response_body = resp.read()
        except urllib.error.HTTPError as e:
            status = e.code
            response_text = ""
            try:
                response_text = e.read().decode("utf-8", errors="replace")
            except Exception:
                response_text = ""
            if attempt < MAX_RETRIES:
                print(f"HTTP {status}. Retrying {attempt}/{MAX_RETRIES}...", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
                continue
            else:
                return _http_error_result(
                    status,
                    f"HTTP {status} after {MAX_RETRIES} attempts",
                    endpoint,
                    actual_params,
                    response_text,
                    retry_exhausted=True,
                )
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"Request failed: {e}. Retrying {attempt}/{MAX_RETRIES}...", file=sys.stderr)
                time.sleep(delay)
                delay *= 2
                continue
            else:
                result = _error_result(
                    0,
                    f"Request failed: {e}",
                    endpoint,
                    actual_params,
                )
                result["error"]["retryExhausted"] = True
                return result

        # Transport succeeded. Response parsing and schema handling happen
        # outside the retrying transport block so a paid response is never
        # requested again merely because local post-processing failed.
        try:
            data = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            return _malformed_response_result(
                endpoint,
                actual_params,
                transport_status,
                f"Response body is not valid UTF-8 JSON: {e}",
            )

        if not isinstance(data, dict):
            return _malformed_response_result(
                endpoint,
                actual_params,
                transport_status,
                f"Expected a JSON object, received {type(data).__name__}",
            )

        if isinstance(transport_status, int) and 100 <= transport_status <= 599:
            # The outer HTTP status is authoritative. Always overwrite any
            # response-body field with the same name before the calling agent
            # inspects success or nested error fields.
            data["_transport"] = {"status": transport_status}
        _CREDITS.record(data.get("meta"))
        success = data.get("success")
        if success is True:
            # Inject _query metadata so AI knows exactly what was sent
            data["_query"] = {
                "endpoint": endpoint,
                "params": actual_params,
            }
            return data

        if success is not False:
            return _malformed_response_result(
                endpoint,
                actual_params,
                transport_status,
                "Expected top-level success to be a JSON boolean",
            )

        err = data.get("error", {})
        if not isinstance(err, dict):
            return _malformed_response_result(
                endpoint,
                actual_params,
                transport_status,
                f"Expected error to be a JSON object, received {type(err).__name__}",
            )
        err_msg = err.get("message", json.dumps(err))
        print(f"API error: {err.get('code', 'unknown')} — {err_msg}", file=sys.stderr)
        # Return error as structured result instead of exiting. This allows
        # composite commands to continue with other steps.
        _mark_cli_error()
        data["_query"] = {"endpoint": endpoint, "params": actual_params}
        return data

    return _error_result(0, "Unexpected retry loop exit", endpoint, actual_params)


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
      3. keyword → products/search → top row's categoryPath (else its bsrCategory);
         no realtime call — the search row already carries the category.
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

    # Priority 3: keyword → search → read categoryPath straight from the top product.
    # products/search rows already carry categoryPath, so category resolution needs NO
    # realtime call here (realtime is a flaky scrape endpoint). Fall back to the
    # product's bsrCategory; if even that is absent (a data anomaly), leave the category
    # unresolved rather than gamble on a flaky realtime probe for one field we can't get.
    if not category_path and keyword:
        log_fn("  → Resolving category from top search result...")
        prod_result = api_caller("products/search", {
            "keyword": keyword, "sortBy": "monthlySalesFloor", "sortOrder": "desc", "pageSize": 5
        }, "products (category probe)")
        prod_data = prod_result.get("data", [])
        if isinstance(prod_data, list) and prod_data:
            top = prod_data[0]
            if top.get("categoryPath"):
                category_path = top["categoryPath"]
                category_source = "inferred_from_search"
                log_fn(f"  ⚠️ Auto-inferred category: {' > '.join(category_path)} — AI should confirm with user")
            elif top.get("bsrCategory"):
                cat_result = api_caller("categories", {"categoryKeyword": top["bsrCategory"]}, "categories")
                cat_data = cat_result.get("data", [])
                if cat_data:
                    category_path = cat_data[0].get("categoryPath")
                    category_source = "inferred_from_search"
                    log_fn(f"  ⚠️ Auto-inferred category: {' > '.join(category_path or [])} — AI should confirm with user")

    # Record the resolved category path in composite meta so an empty top-level
    # `categories` section (Priority-1 miss for a multi-word product phrase) is not
    # misread as missing data when a later priority resolved the category. Pairs
    # with `meta.category_source`, which callers set to record HOW it resolved.
    if results is not None:
        results.setdefault("meta", {})["resolved_category_path"] = category_path

    return category_path, category_source


def _has_scope(keyword, category_path):
    """A category-scoped discovery call (products/search, products/competitors,
    markets/search for leaders) needs at least one filter. With neither keyword
    nor categoryPath the API returns unfiltered global top-sellers — a real bug
    that benchmarks a listing against random products. Callers MUST gate such
    calls on this."""
    return bool(keyword or category_path)


def _is_terminal_failure(result):
    """True when a call returned an exhausted terminal interface failure
    (transport retries used up). Once one happens inside a composite, the
    remaining fan-out calls will almost certainly hit the same wall, so the
    composite should stop rather than stack retry x timeout for every endpoint."""
    if not isinstance(result, dict):
        return False
    err = result.get("error")
    return isinstance(err, dict) and bool(err.get("retryExhausted"))


def _skipped_after_abort():
    """Envelope a composite's safe_call returns once the command has aborted
    after a terminal failure — no network call, no credits consumed."""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": "ABORTED_AFTER_TERMINAL_FAILURE",
            "message": "skipped: an earlier call in this composite hit a terminal interface failure",
        },
    }


REALTIME_FALLBACK_HINT = (
    "Realtime data collection failed for one or more items after retries. Tell the "
    "user realtime lookup is temporarily unavailable, then continue the analysis "
    "using the offline snapshot data already gathered (products/search fields, "
    "history, price/BSR/rating) — do not stall or fabricate the missing realtime detail."
)


def _is_empty_realtime(result):
    """True when realtime/product returned a 200-success but empty payload
    (`data.asin` blank) — a transient scrape miss, not a hard error."""
    if not isinstance(result, dict):
        return False
    data = result.get("data")
    return isinstance(data, dict) and not data.get("asin")


def _fetch_realtime(caller, asin, marketplace="US", label=None, attempts=REALTIME_EMPTY_RETRIES):
    """Fetch realtime/product for a known-good ASIN (it came from a search result),
    retrying a transient 200-empty up to `attempts` total. `caller(endpoint, params,
    label)` is the composite's safe_call or an api_call adapter. If still empty after
    all attempts, stamps result['_realtimeStatus']='empty_after_retries' so callers
    can surface the offline-fallback hint. Does NOT retry a terminal failure."""
    params = {"asin": asin, "marketplace": marketplace}
    lbl = label or f"realtime {asin}"
    r = caller("realtime/product", params, lbl)
    n = 1
    while n < attempts and _is_empty_realtime(r) and not _is_terminal_failure(r):
        n += 1
        r = caller("realtime/product", params, lbl)
    if _is_empty_realtime(r):
        r["_realtimeStatus"] = "empty_after_retries"
    return r


def _note_realtime_fallback(results, result):
    """If a realtime result came back empty after retries, bump the composite-level
    counter and set the user-facing offline-fallback hint on results['meta']."""
    if isinstance(result, dict) and result.get("_realtimeStatus") == "empty_after_retries":
        m = results.setdefault("meta", {})
        m["realtimeUnavailable"] = m.get("realtimeUnavailable", 0) + 1
        m["realtimeFallbackHint"] = REALTIME_FALLBACK_HINT


def _mark_cli_error():
    """Remember an API failure without interrupting a composite command."""
    global _cli_had_error
    _cli_had_error = True


def _malformed_response_result(endpoint, params, transport_status, detail):
    """Return the technical facts for a local response-decoding failure."""
    result = _error_result(
        0,
        f"Malformed response from endpoint '{endpoint}'",
        endpoint,
        params,
    )
    result["error"]["code"] = "MALFORMED_RESPONSE"
    result["error"]["detail"] = detail
    if isinstance(transport_status, int) and 100 <= transport_status <= 599:
        result["_transport"] = {"status": transport_status}
    return result


def _http_error_result(
    status: int,
    fallback_message: str,
    endpoint: str,
    params: dict,
    response_text: str = "",
    *,
    retry_exhausted: bool = False,
) -> dict:
    """Preserve a non-2xx server response and add only CLI-owned metadata.

    Structured JSON objects with an ``error`` object remain the primary result.
    Other JSON values and non-JSON text are retained under explicit raw-response
    keys while the CLI supplies only a generic transport fallback.
    """
    stripped = (response_text or "").strip()
    parsed = None
    parsed_ok = False
    if stripped:
        try:
            parsed = json.loads(stripped)
            parsed_ok = True
        except json.JSONDecodeError:
            pass

    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        result = _error_result(
            status,
            fallback_message,
            endpoint,
            params,
            server_response=parsed,
        )
    else:
        result = _error_result(
            status,
            fallback_message,
            endpoint,
            params,
        )
        if parsed_ok:
            result["_serverResponse"] = parsed
        elif stripped:
            result["_serverResponseText"] = stripped

    error = result.get("error")
    if isinstance(error, dict):
        if retry_exhausted:
            error["retryExhausted"] = True
    _CREDITS.record(result.get("meta"))
    return result


def _error_result(
    status: int,
    message: str,
    endpoint: str,
    params: dict,
    server_response=None,
) -> dict:
    """
    Build a structured error result instead of sys.exit().
    This lets AI read the error from JSON stdout and take appropriate action.
    """
    _mark_cli_error()
    print(f"ERROR: {message}", file=sys.stderr)

    transport = None
    if isinstance(status, int) and 100 <= status <= 599:
        # Preserve the authoritative outer HTTP status separately from the
        # response body.  In particular, a structured 422 body may omit a
        # numeric status or contain nested status-like fields that must not
        # override the transport classification.
        transport = {"status": status}

    # Preserve a structured server error verbatim for the calling agent.  Only
    # add CLI metadata; do not flatten VALIDATION_ERROR details into a string.
    if isinstance(server_response, dict):
        result = dict(server_response)
        result["success"] = False
        if transport is not None:
            result["_transport"] = transport
        result["_query"] = {"endpoint": endpoint, "params": params}
        return result

    result = {
        "success": False,
        "error": {
            "status": status,
            "message": message,
        },
        "_query": {
            "endpoint": endpoint,
            "params": params,
        },
    }
    if transport is not None:
        result["_transport"] = transport
    return result


def output(data, fmt="json"):
    """Print output in the requested format."""
    global _cli_emitted_output
    _annotate_credits(data)
    if isinstance(data, dict) and data.get("success") is False:
        _mark_cli_error()
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif fmt == "compact":
        print(json.dumps(data, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    _cli_emitted_output = True


# ─── Helper: parse category string ──────────────────────────────────────────

def parse_category(cat_str: str) -> list:
    """Parse category path string into a list.

    Supported formats:
      - '["Pet Supplies", "Dogs"]'         (JSON array — unambiguous, safest)
      - 'Pet Supplies > Dogs > Toys'       (spaced arrow — recommended)
      - 'Pet Supplies>Dogs>Toys'           (bare arrow, no spaces)
      - 'Pet Supplies,Dogs,Toys'           (comma-separated — AVOID for names
        that contain commas, e.g. "Headphones, Earbuds & Accessories";
        use '>' or JSON array for those)
    """
    if not cat_str:
        return []
    # JSON array input — exact segments, no separator ambiguity
    stripped = cat_str.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(c).strip() for c in parsed if str(c).strip()]
        except (json.JSONDecodeError, ValueError):
            pass  # not valid JSON — fall through to separator parsing
    # Arrow separators take priority: category names never contain '>',
    # but they DO contain commas (e.g. "Headphones, Earbuds & Accessories")
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
#   1. zoodata.py reviews-raw --asin X          → fetch raw reviews
#   2. For each review, render via:
#        zoodata.py review-tag-prompt --review '<json>'
#      The caller's LLM produces JSON matching REVIEW_MAP_SCHEMA.
#   3. Collect per-dimension candidate phrases; for each dimension render:
#        zoodata.py review-reduce-prompt --label-type <dim> --candidates '[...]'
#      The caller's LLM produces JSON matching REVIEW_REDUCE_SCHEMA.
#   4. zoodata.py review-aggregate --reviews R --tagged T --clusters C
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
    failure = None
    t0 = time.time()
    for i in range(1, max_pages + 1):
        params = {"asin": asin, "marketplace": marketplace}
        if cursor:
            params["cursor"] = cursor
        resp = api_call("realtime/reviews", params)
        if not resp.get("success"):
            failure = resp
            break
        data = resp.get("data") or {}
        page_reviews = data.get("reviews") or []
        cursor = data.get("nextCursor")
        pages += 1
        reviews.extend(page_reviews)
        log(f"  page {i}: {len(page_reviews)} reviews, cursor={'yes' if cursor else 'end'}")
        if not cursor:
            break
    result = {
        "reviews": reviews,
        "pages": pages,
        "capped": pages >= max_pages and cursor is not None,
        "fetchSeconds": round(time.time() - t0, 2),
    }
    if failure is not None:
        result["_failure"] = failure
    return result


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
    failure = result.pop("_failure", None)
    payload = {
        "success": failure is None,
        "data": result,
        "_query": {"endpoint": "realtime/reviews",
                   "params": {"asin": args.asin, "marketplace": args.marketplace,
                              "maxPages": args.max_pages}},
    }
    if isinstance(failure, dict):
        payload["error"] = failure.get("error") or {
            "message": "realtime/reviews pagination failed"
        }
        if isinstance(failure.get("_transport"), dict):
            payload["_transport"] = failure["_transport"]
        if isinstance(failure.get("_query"), dict):
            payload["_failedQuery"] = failure["_query"]
        if isinstance(failure.get("meta"), dict):
            payload["meta"] = failure["meta"]
    output(payload)


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
    if args.marketplace:
        params["marketplace"] = args.marketplace

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
    marketplace = args.marketplace or "US"
    # realtime/product can return a transient 200-empty; retry like the composites do
    # and, if still empty, surface the offline-fallback hint on the result's own meta so
    # a per-ASIN poller (e.g. a Quick Check loop) gets the same signal to fall back to
    # offline snapshot data instead of treating the empty payload as a real answer.
    caller = lambda ep, p, label=None: api_call(ep, p)
    result = _fetch_realtime(caller, args.asin, marketplace=marketplace)
    if isinstance(result, dict) and result.get("_realtimeStatus") == "empty_after_retries":
        meta = result.setdefault("meta", {})
        meta["realtimeUnavailable"] = (meta.get("realtimeUnavailable") or 0) + 1
        meta["realtimeFallbackHint"] = REALTIME_FALLBACK_HINT
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

    # Step 1: Confirm category (self-healing: categories -> products/search row's
    # categoryPath, so a product keyword like "yoga mat" with no direct category match
    # still resolves a categoryPath — otherwise the market step below returns empty).
    print("Step 1/4: Confirming category...", file=sys.stderr)
    _caller = lambda ep, p, label=None: api_call(ep, p)
    _log = lambda m: print(m, file=sys.stderr)
    category_path, category_source = _resolve_category(_caller, _log, keyword=keyword, results=results)
    results.setdefault("meta", {})["category_source"] = category_source

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
            detail_result = _fetch_realtime(_caller, top_asin)
            _note_realtime_fallback(results, detail_result)
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

    # Step 1: Confirm category (self-healing: categories -> products/search row's
    # categoryPath, so a product keyword with no direct category match still resolves a
    # categoryPath — otherwise the market validation below returns empty).
    print("Step 1/4: Confirming category...", file=sys.stderr)
    _caller = lambda ep, p, label=None: api_call(ep, p)
    _log = lambda m: print(m, file=sys.stderr)
    category_path, category_source = _resolve_category(_caller, _log, keyword=keyword, results=results)
    results.setdefault("meta", {})["category_source"] = category_source

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
            r = _fetch_realtime(_caller, asin)
            _note_realtime_fallback(results, r)
            details.append(r)
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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
        return r

    # ── Step 0.5: Category Resolution ──
    if not category_path:
        category_path, category_source = _resolve_category(safe_call, log, keyword=keyword, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category_path"] = category_path

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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
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
    results["meta"]["resolved_category_path"] = category_path
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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
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
    results["meta"]["resolved_category_path"] = category_path

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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
        return r

    # Step 0.5: Category Resolution
    if not category_path:
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=tracked_asins[0] if tracked_asins else None, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category_path"] = category_path

    # Step 1: Realtime Snapshot for All Tracked ASINs
    log(f"Step 1/7: Realtime snapshot ({len(tracked_asins)} ASINs)...")
    # Note: unlike search-sourced composites, these ASINs are USER-SUPPLIED, so a
    # persistent 200-empty may be a dead/typo ASIN rather than a transient miss. The
    # empty-retry is still bounded (≤REALTIME_EMPTY_RETRIES fast calls per ASIN) and the
    # offline-fallback hint surfaces it — a wrong ASIN costs a few extra credits, not a hang.
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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
        return r

    # Step 0.5: Category Resolution
    if not category_path:
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=my_asin, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category_path"] = category_path

    # Step 1: Audit Target
    log("Step 1/7: Auditing target listing...")
    results["target_realtime"] = safe_call("realtime/product", {"asin": my_asin, "marketplace": "US"}, f"realtime {my_asin}")
    results["meta"]["steps_completed"].append("audit_target")

    # Step 1.5: Empty-target guard. If the target ASIN has no realtime data and no
    # category resolved, the leader search below would run UNFILTERED and benchmark
    # the listing against random global top-sellers. A missing target is not
    # auditable — stop here rather than fabricate an audit against garbage peers.
    _tgt = results["target_realtime"].get("data")
    _tgt = _tgt if isinstance(_tgt, dict) else {}
    if not _tgt.get("asin"):
        results["meta"]["target_status"] = "empty"
        results["meta"]["audit_status"] = "not_auditable"
        results["meta"]["reason"] = (
            "Target ASIN returned no realtime data (not indexed by ZooData or a "
            "transient upstream failure). A listing audit cannot benchmark a missing "
            "target; re-check the ASIN or retry later."
        )
        _mark_cli_error()
        output(results, args.format)
        return
    results["meta"]["target_status"] = "ok"

    # Step 2: Category Leaders — only with a scope, else the search is unfiltered.
    log("Step 2/7: Finding category leaders...")
    if _has_scope(keyword, category_path):
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
    else:
        _no_scope = {"success": False, "data": [], "error": {
            "code": "NO_CATEGORY_SCOPE",
            "message": "skipped: no keyword or category to scope discovery (would return unfiltered global results)"}}
        results["leader_products"] = _no_scope
        results["competitors"] = _no_scope
        results["meta"].setdefault("warnings", []).append(
            "leader/competitor discovery skipped — target had no category and no keyword to scope on")
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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
        return r

    # Category Resolution
    if not category_path:
        category_path, category_source = _resolve_category(safe_call, log, keyword=keyword, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category_path"] = category_path

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
        # Fail-fast: once a terminal interface failure trips this composite,
        # skip remaining fan-out calls instead of stacking retry x timeout.
        if results.get("meta", {}).get("aborted"):
            return _skipped_after_abort()
        r = api_call(endpoint, params)
        # realtime/product is a scrape endpoint that can return a transient 200-empty;
        # the ASIN is known-good in a composite, so retry, then hint offline fallback.
        if endpoint == "realtime/product":
            n = 1
            while n < REALTIME_EMPTY_RETRIES and _is_empty_realtime(r) and not _is_terminal_failure(r):
                n += 1
                r = api_call(endpoint, params)
            if _is_empty_realtime(r):
                r["_realtimeStatus"] = "empty_after_retries"
                _note_realtime_fallback(results, r)
        if r.get("success") is False:
            log(f"  ⚠️ {label or endpoint}: {r.get('error', {}).get('message', 'failed')}")
            if _is_terminal_failure(r):
                results.setdefault("meta", {})["aborted"] = True
                results["meta"]["abort_reason"] = f"terminal interface failure on {label or endpoint}"
        return r

    # Category Resolution
    if not category_path:
        category_path, category_source = _resolve_category(
            safe_call, log, keyword=keyword, asin=target_asin, results=results)
        results["meta"]["category_source"] = category_source
    results["meta"]["resolved_category_path"] = category_path

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
    API self-check: verify credentials by default.
    Endpoint probes are opt-in because each API call can consume credits.
    """
    print("ZooData API Self-Check\n", file=sys.stderr)
    print("=" * 50, file=sys.stderr)

    # Use the SAME lookup chain as real API calls — divergence here was a real bug.
    if _resolve_credential():
        print("✅ API Key: configured", file=sys.stderr)
    else:
        print("❌ API Key: Not found", file=sys.stderr)
        print("   Checked: env ZOODATA_API_KEY, ~/.zoodata/config.json", file=sys.stderr)
        if os.environ.get("APICLAW_API_KEY", "").strip():
            print("   NOTE: APICLAW_API_KEY is set but no longer read (legacy source removed); rename it to ZOODATA_API_KEY.", file=sys.stderr)
        print("   Get one at: https://zoodata.ai/en/api-keys", file=sys.stderr)
        sys.exit(1)

    if not args.endpoints and not args.keyword_endpoints:
        print("\nNo endpoint probes requested; skipping API calls to avoid credit usage.", file=sys.stderr)
        print("Use --endpoints for general endpoint probes or --keyword-endpoints for keyword endpoint probes.", file=sys.stderr)
        output({"check": "credentials_only", "api_key": "configured", "endpoint_probes": "skipped"}, args.format)
        return

    print(f"\nTesting endpoints on {BASE_URL}...\n", file=sys.stderr)

    endpoints = []
    if args.endpoints:
        endpoints.extend([
            ("categories", {}, "Category tree"),
            ("markets/search", {"categoryKeyword": "pet", "pageSize": 1}, "Market search"),
            ("products/search", {"keyword": "test", "pageSize": 1}, "Product search"),
            ("products/competitors", {"keyword": "test", "pageSize": 1}, "Competitor lookup"),
        ])
    if args.keyword_endpoints:
        keyword = (args.keyword or "").strip() or "yoga mat"
        date = args.date or time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
        keyword_probes = [
            ("keywords/detail", {"keyword": keyword, "date": date}, "Keyword snapshot"),
            ("keywords/market-profile", {"keyword": keyword, "date": date}, "Keyword market profile"),
            (
                "keywords/trend-profile",
                {"keyword": keyword, "date": date, "windowPeriods": [4], "granularity": "week"},
                "Keyword trend profile",
            ),
            ("keywords/extends", {"query": keyword, "date": date, "queryType": "phrase", "pageSize": 1}, "Keyword expansion"),
            ("keywords/search-results", {"keyword": keyword, "date": date, "pageSize": 1}, "Keyword SERP"),
        ]
        endpoints.extend(keyword_probes)
        if args.asin:
            endpoints.extend([
                ("keywords/product-traffic-terms", {"asin": args.asin, "date": date, "pageSize": 1}, "ASIN traffic terms"),
                ("keywords/competitor-product-keywords", {"asin": args.asin, "date": date, "pageSize": 1}, "ASIN keyword coverage"),
                (
                    "keywords/product-traffic-terms-profile",
                    {"asin": args.asin, "date": date, "granularity": "week"},
                    "ASIN traffic profile",
                ),
            ])
            if keyword:
                endpoints.append((
                    "keywords/product-traffic-terms-timeline",
                    {"asin": args.asin, "keyword": keyword, "dateFrom": date, "dateTo": date},
                    "ASIN + keyword timeline",
                ))
        else:
            print("⏭️  ASIN keyword endpoints      (skipped, pass --asin to probe)", file=sys.stderr)

    results = {}
    all_ok = True

    for endpoint, params, desc in endpoints:
        try:
            result = api_call(endpoint, params)
            if result.get("success"):
                data = result.get("data")
                data_count = len(data) if isinstance(data, list) else (1 if data else 0)
                print(f"✅ {endpoint:30} OK (returned {data_count} items)", file=sys.stderr)
                results[endpoint] = {"status": "ok", "items": data_count}
            else:
                err = result.get("error", {})
                message = err.get("message") or err.get("code") or "unknown error"
                print(f"❌ {endpoint:30} FAILED: {message}", file=sys.stderr)
                results[endpoint] = {"status": "failed", "message": message}
                all_ok = False
        except SystemExit:
            print(f"❌ {endpoint:30} FAILED", file=sys.stderr)
            results[endpoint] = {"status": "failed"}
            all_ok = False
        except Exception as e:
            print(f"❌ {endpoint:30} ERROR: {e}", file=sys.stderr)
            results[endpoint] = {"status": "error", "message": str(e)}
            all_ok = False

    if args.endpoints:
        print(f"⏭️  realtime/product            (skipped, requires valid ASIN)", file=sys.stderr)

    print("\n" + "=" * 50, file=sys.stderr)
    if all_ok:
        print("✅ Requested endpoint probes completed", file=sys.stderr)
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


def _split_csv(value):
    """Split a comma-separated CLI value into a list, preserving None."""
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _require_nonempty_text(value, name):
    """Return stripped required text or fail before sending an invalid request."""
    normalized = (value or "").strip()
    if not normalized:
        raise SystemExit(f"ERROR: {name} must contain a non-empty value")
    return normalized


def _keyword_subject(args, max_items=20):
    """Return the single or batch keyword request field after local validation."""
    keyword = getattr(args, "keyword", None)
    if keyword is not None:
        return "keyword", _require_nonempty_text(keyword, "--keyword")
    keywords = _split_csv(getattr(args, "keywords", None)) or []
    if not keywords:
        raise SystemExit("ERROR: --keywords must contain at least one non-empty keyword")
    if len(keywords) > max_items:
        raise SystemExit(f"ERROR: --keywords accepts at most {max_items} keywords, got {len(keywords)}")
    normalized = [keyword.casefold() for keyword in keywords]
    if len(set(normalized)) != len(normalized):
        raise SystemExit("ERROR: --keywords contains case-insensitive duplicates")
    return "keywords", keywords


def _asin_subject(args, max_items=20):
    """Return the single or batch ASIN request field after local validation."""
    asin = getattr(args, "asin", None)
    if asin is not None:
        return "asin", _require_nonempty_text(asin, "--asin")
    asins = _split_csv(getattr(args, "asins", None)) or []
    if not asins:
        raise SystemExit("ERROR: --asins must contain at least one non-empty ASIN")
    if len(asins) > max_items:
        raise SystemExit(f"ERROR: --asins accepts at most {max_items} ASINs, got {len(asins)}")
    normalized = [asin.casefold() for asin in asins]
    if len(set(normalized)) != len(normalized):
        raise SystemExit("ERROR: --asins contains case-insensitive duplicates")
    return "asins", asins


def _require_yyyy_mm_dd(value, name):
    """Fail fast on malformed dates before sending validation-bad requests."""
    if not DATE_RE.match(value or ""):
        raise SystemExit(f"ERROR: {name} must be a full date in YYYY-MM-DD format, got: {value!r}")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"ERROR: {name} must be a valid calendar date in YYYY-MM-DD format, got: {value!r}")
    return value


def _require_date_range_within(date_from, date_to, max_days, label):
    """Fail fast on validation-bad date ranges before sending API requests."""
    start = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    span = (end - start).days
    if span < 0:
        raise SystemExit(
            f"ERROR: --date-from must be on or before --date-to for {label}, got: {date_from} > {date_to}"
        )
    if span > max_days:
        raise SystemExit(
            f"ERROR: {label} date range cannot exceed {max_days} days, got {span} days "
            f"({date_from} to {date_to})"
        )


def cmd_keyword_detail(args):
    """Get weekly keyword snapshot metrics."""
    _require_yyyy_mm_dd(args.date, "--date")
    params = {
        "date": args.date,
        "marketplace": args.marketplace,
        "granularity": "week",
    }
    subject_field, subject_value = _keyword_subject(args)
    params[subject_field] = subject_value
    result = api_call("keywords/detail", params)
    output(result, args.format)


def cmd_keyword_market_profile(args):
    """Get server-calculated multidimensional keyword market profiles."""
    _require_yyyy_mm_dd(args.date, "--date")
    params = {
        "date": args.date,
        "marketplace": args.marketplace,
        "granularity": "week",
    }
    subject_field, subject_value = _keyword_subject(args)
    params[subject_field] = subject_value
    result = api_call("keywords/market-profile", params)
    output(result, args.format)


def cmd_keyword_trend_profile(args):
    """Get server-calculated keyword trend profiles for fixed weekly windows."""
    _require_yyyy_mm_dd(args.date, "--date")
    raw_periods = _split_csv(args.window_periods) or []
    try:
        window_periods = [int(period) for period in raw_periods]
    except ValueError:
        raise SystemExit("ERROR: --window-periods accepts only comma-separated values from 4,8,12,26")
    if not 1 <= len(window_periods) <= 4:
        raise SystemExit("ERROR: --window-periods requires 1 to 4 values")
    if any(period not in {4, 8, 12, 26} for period in window_periods):
        raise SystemExit("ERROR: --window-periods accepts only 4,8,12,26")
    if len(set(window_periods)) != len(window_periods):
        raise SystemExit("ERROR: --window-periods must not contain duplicates")
    params = {
        "date": args.date,
        "windowPeriods": window_periods,
        "marketplace": args.marketplace,
        "granularity": "week",
    }
    subject_field, subject_value = _keyword_subject(args)
    params[subject_field] = subject_value
    result = api_call("keywords/trend-profile", params)
    output(result, args.format)


def cmd_keyword_trend(args):
    """Get weekly keyword trend metrics."""
    _require_yyyy_mm_dd(args.date_from, "--date-from")
    _require_yyyy_mm_dd(args.date_to, "--date-to")
    _require_date_range_within(args.date_from, args.date_to, KEYWORD_DATE_RANGE_MAX_DAYS, "keyword-trend")
    params = {
        "dateFrom": args.date_from,
        "dateTo": args.date_to,
        "marketplace": args.marketplace,
        "granularity": "week",
    }
    subject_field, subject_value = _keyword_subject(args)
    params[subject_field] = subject_value
    result = api_call("keywords/trend", params)
    output(result, args.format)


def cmd_keyword_extends(args):
    """Get keyword expansion candidates."""
    if args.date:
        _require_yyyy_mm_dd(args.date, "--date")
    params = {
        "query": _require_nonempty_text(args.query, "--query"),
        "marketplace": args.marketplace,
        "page": args.page,
        "pageSize": args.page_size,
        "queryType": args.query_type,
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
    }
    if args.date:
        params["date"] = args.date
    result = api_call("keywords/extends", params)
    output(result, args.format)


def cmd_keyword_search_results(args):
    """Get observed keyword SERP rows."""
    _require_yyyy_mm_dd(args.date, "--date")
    params = {
        "keyword": _require_nonempty_text(args.keyword, "--keyword"),
        "date": args.date,
        "marketplace": args.marketplace,
        "granularity": "week",
        "page": args.page,
        "pageSize": args.page_size,
        "exploreTypes": _split_csv(args.explore_types),
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
    }
    result = api_call("keywords/search-results", params)
    output(result, args.format)


def _asin_keyword_params(args):
    _require_yyyy_mm_dd(args.date, "--date")
    return {
        "asin": _require_nonempty_text(args.asin, "--asin"),
        "date": args.date,
        "marketplace": args.marketplace,
        "granularity": "week",
        "page": args.page,
        "pageSize": args.page_size,
        "exploreTypes": _split_csv(args.explore_types),
        "keywordContains": args.keyword_contains,
        "sortBy": args.sort_by,
        "sortOrder": args.sort_order,
    }


def cmd_keyword_competitor_product_keywords(args):
    """Get competitor ASIN keyword rows."""
    result = api_call("keywords/competitor-product-keywords", _asin_keyword_params(args))
    output(result, args.format)


def cmd_keyword_product_traffic_terms(args):
    """Get traffic-driving keyword rows for one ASIN."""
    result = api_call("keywords/product-traffic-terms", _asin_keyword_params(args))
    output(result, args.format)


def cmd_product_traffic_terms_profile(args):
    """Get weekly product traffic-term profiles for one or more ASINs."""
    _require_yyyy_mm_dd(args.date, "--date")
    subject_field, subject_value = _asin_subject(args)
    params = {
        subject_field: subject_value,
        "date": args.date,
        "marketplace": args.marketplace,
        "granularity": "week",
    }
    result = api_call("keywords/product-traffic-terms-profile", params)
    output(result, args.format)


def cmd_product_traffic_terms_timeline(args):
    """Get product traffic-term timeline for one ASIN + one or more keywords."""
    _require_yyyy_mm_dd(args.date_from, "--date-from")
    _require_yyyy_mm_dd(args.date_to, "--date-to")
    _require_date_range_within(
        args.date_from,
        args.date_to,
        KEYWORD_TIMELINE_MAX_DAYS,
        "product-traffic-terms-timeline",
    )
    params = {
        "asin": _require_nonempty_text(args.asin, "--asin"),
        "dateFrom": args.date_from,
        "dateTo": args.date_to,
        "marketplace": args.marketplace,
        "granularity": "week",
    }
    subject_field, subject_value = _keyword_subject(args)
    params[subject_field] = subject_value
    result = api_call("keywords/product-traffic-terms-timeline", params)
    output(result, args.format)


# ─── CLI Setup ───────────────────────────────────────────────────────────────

def main():
    global _cli_had_error, _cli_emitted_output
    _cli_had_error = False
    _cli_emitted_output = False

    # Enforce the per-skill allowlist BEFORE argparse touches the command:
    # a disallowed subcommand must yield the structured refusal, not a
    # usage error about its arguments (allow_abbrev=False everywhere, so
    # argv[1] is the literal command name). Help is documentation, not
    # execution — `<cmd> --help` makes no API call and stays available for
    # the full surface in every bundle.
    if (len(sys.argv) > 1 and not sys.argv[1].startswith("-")
            and "-h" not in sys.argv and "--help" not in sys.argv):
        _enforce_command_allowlist(sys.argv[1])

    parser = argparse.ArgumentParser(
        description="ZooData CLI — Amazon Product Research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False,
        epilog="""
Examples:
  %(prog)s categories --keyword "pet supplies"
  %(prog)s market --category "Pet Supplies > Dogs" --topn 10
  %(prog)s products --keyword "yoga mat" --mode emerging
  %(prog)s products --keyword "yoga mat" --sales-min 300 --ratings-max 50
  %(prog)s competitors --keyword "wireless earbuds" --brand Anker
  %(prog)s product --asin B09V3KXJPB
  %(prog)s report --keyword "pet supplies"
  %(prog)s opportunity --keyword "pet supplies" --mode high-demand-low-barrier
  %(prog)s check                                            # Credential check, no endpoint calls
  %(prog)s check --keyword-endpoints --keyword "yoga mat"   # Optional keyword endpoint probes
        """,
    )

    # Common args
    parser.add_argument("--format", choices=["json", "compact"], default="json",
                        help="Output format (default: json). Global flag — must come BEFORE the subcommand")

    sub = parser.add_subparsers(dest="command", required=True)

    # ── categories ──
    p_cat = sub.add_parser("categories", help="Query Amazon category tree", allow_abbrev=False)
    p_cat.add_argument("--keyword", help="Search categories by keyword")
    p_cat.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_cat.add_argument("--parent", help="Get child categories (comma-separated parent path)")
    p_cat.add_argument("--marketplace", default="US", help="Marketplace (default: US)")
    p_cat.set_defaults(func=cmd_categories)

    # ── market ──
    p_mkt = sub.add_parser("market", help="Search market-level data for a category", allow_abbrev=False)
    p_mkt.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_mkt.add_argument("--keyword", help="Category keyword")
    p_mkt.add_argument("--topn", type=int, default=10, help="Top N for concentration analysis (default: 10)")
    p_mkt.add_argument("--page-size", type=int, default=20)
    p_mkt.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_mkt.add_argument("--sort", choices=['totalSkuCount', 'sampleSkuCount', 'sampleAvgPrice', 'sampleAvgMonthlySales', 'sampleAvgMonthlyRevenue', 'sampleTotalMonthlySales', 'sampleAvgBsr', 'sampleAvgRating', 'sampleAvgRatingCount', 'sampleBrandCount', 'sampleSellerCount', 'sampleFbaRate', 'sampleNewSkuRate', 'topAvgMonthlySales', 'topAvgMonthlyRevenue', 'topSalesRate', 'topBrandSalesRate', 'topSellerSalesRate'], metavar="FIELD", help="Sort field (markets enum), e.g. sampleAvgMonthlySales, topBrandSalesRate")
    p_mkt.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_mkt.set_defaults(func=cmd_market)

    # ── products ──
    p_prod = sub.add_parser("products", help="Search products with filters (product selection)", allow_abbrev=False)
    p_prod.add_argument("--keyword", help="Search keyword")
    p_prod.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
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
    p_prod.add_argument("--listing-age", help="Max listing age: 30d, 90d, 180d, 1y, or 2y")
    p_prod.add_argument("--badges", nargs="+", help="Badge filters: bestSeller, amazonChoice, newRelease, aPlus, video")
    p_prod.add_argument("--fulfillment", nargs="+", help="Fulfillment filter (FBA, FBM)")
    p_prod.add_argument("--include-brands", help="Include brands (comma-separated)")
    p_prod.add_argument("--exclude-brands", help="Exclude brands (comma-separated)")
    p_prod.add_argument("--page-size", type=int, default=20)
    p_prod.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_prod.add_argument("--sort", choices=['monthlySalesFloor', 'monthlyRevenueFloor', 'bsr', 'price', 'rating', 'ratingCount', 'listingDate'], metavar="FIELD", help="Sort field (default: monthlySalesFloor): monthlySalesFloor, monthlyRevenueFloor, bsr, price, rating, ratingCount, listingDate")
    p_prod.add_argument("--order", choices=["asc", "desc"], default="desc")
    p_prod.set_defaults(func=cmd_products)

    # ── competitors ──
    p_comp = sub.add_parser("competitors", help="Look up competitors", allow_abbrev=False)
    p_comp.add_argument("--keyword", help="Search keyword")
    p_comp.add_argument("--brand", help="Brand filter")
    p_comp.add_argument("--asin", help="ASIN filter")
    p_comp.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_comp.add_argument("--date-range", default="30d", help="Date range (default: 30d)")
    p_comp.add_argument("--marketplace", default="US", help="Marketplace (default: US)")
    p_comp.add_argument("--page", type=int, default=1, help="Page number")
    p_comp.add_argument("--page-size", type=int, default=20)
    p_comp.add_argument("--sort", choices=['monthlySalesFloor', 'monthlyRevenueFloor', 'bsr', 'price', 'rating', 'ratingCount', 'listingDate'], metavar="FIELD", help="Sort field (default: monthlySalesFloor): monthlySalesFloor, monthlyRevenueFloor, bsr, price, rating, ratingCount, listingDate")
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
    p_me.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_me.set_defaults(func=cmd_market_entry)

    # ── competitor-analysis (composite) ──
    p_ca = sub.add_parser("competitor-analysis", help="Full competitor war room analysis", allow_abbrev=False)
    p_ca.add_argument("--keyword", help="Product keyword to discover competitors")
    p_ca.add_argument("--my-asin", help="Your product ASIN (optional)")
    p_ca.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_ca.set_defaults(func=cmd_competitor_analysis)

    # ── pricing-analysis (composite) ──
    p_pa = sub.add_parser("pricing-analysis", help="Full pricing analysis with competitor benchmarking", allow_abbrev=False)
    p_pa.add_argument("--my-asin", required=True, help="Your product ASIN")
    p_pa.add_argument("--keyword", help="Product keyword for market context")
    p_pa.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_pa.set_defaults(func=cmd_pricing_analysis)

    # ── daily-radar (composite) ──
    p_dr = sub.add_parser("daily-radar", help="Daily market monitoring scan (runs all tracking endpoints)", allow_abbrev=False)
    p_dr.add_argument("--asins", required=True, help="Tracked ASINs (comma-separated, your products + competitors)")
    p_dr.add_argument("--keyword", help="Category keyword for market monitoring")
    p_dr.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_dr.set_defaults(func=cmd_daily_radar)

    # ── listing-audit (composite) ──
    p_la = sub.add_parser("listing-audit", help="Full listing audit against category leaders", allow_abbrev=False)
    p_la.add_argument("--my-asin", required=True, help="ASIN to audit")
    p_la.add_argument("--keyword", help="Primary keyword for benchmark context")
    p_la.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_la.set_defaults(func=cmd_listing_audit)

    # ── opportunity-scan (composite) ──
    p_os = sub.add_parser("opportunity-scan", help="Multi-mode product opportunity discovery", allow_abbrev=False)
    p_os.add_argument("--keyword", help="Category keyword to scan")
    p_os.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
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
    p_rd.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
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
    p_analyze.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_analyze.add_argument("--label-type", help="Filter dimensions (comma-separated)")
    p_analyze.add_argument("--period", help="Time period: 1m, 3m, 6m, 1y, 2y", default="6m")
    p_analyze.set_defaults(func=cmd_analyze)

    # ── price-band-overview ──
    p_pbo = sub.add_parser("price-band-overview", help="Price band overview (hottest & best opportunity)", allow_abbrev=False)
    p_pbo.add_argument("--keyword", help="Search keyword")
    p_pbo.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_pbo.add_argument("--page-size", type=int, default=20)
    p_pbo.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_pbo.set_defaults(func=cmd_price_band_overview)

    # ── price-band-detail ──
    p_pbd = sub.add_parser("price-band-detail", help="Price band detailed breakdown", allow_abbrev=False)
    p_pbd.add_argument("--keyword", help="Search keyword")
    p_pbd.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_pbd.add_argument("--page-size", type=int, default=20)
    p_pbd.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_pbd.set_defaults(func=cmd_price_band_detail)

    # ── brand-overview ──
    p_bo = sub.add_parser("brand-overview", help="Brand landscape overview", allow_abbrev=False)
    p_bo.add_argument("--keyword", help="Search keyword")
    p_bo.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_bo.add_argument("--page-size", type=int, default=20)
    p_bo.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_bo.set_defaults(func=cmd_brand_overview)

    # ── brand-detail ──
    p_bd = sub.add_parser("brand-detail", help="Brand ranking with per-brand stats", allow_abbrev=False)
    p_bd.add_argument("--keyword", help="Search keyword")
    p_bd.add_argument("--category", help="Category path, '>' separated (names may contain commas, e.g. \"Electronics > Headphones, Earbuds & Accessories\"); JSON array also accepted")
    p_bd.add_argument("--page-size", type=int, default=20)
    p_bd.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_bd.set_defaults(func=cmd_brand_detail)

    # ── history ──
    p_ph = sub.add_parser("history", help="Historical data for ASINs", allow_abbrev=False)
    p_ph.add_argument("--asins", required=True, help="ASINs (comma-separated)")
    p_ph.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    p_ph.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    p_ph.set_defaults(func=cmd_product_history)

    # ── keyword-detail ──
    p_kd = sub.add_parser("keyword-detail", help="Keyword weekly snapshot", allow_abbrev=False)
    kd_subject = p_kd.add_mutually_exclusive_group(required=True)
    kd_subject.add_argument("--keyword", help="One keyword")
    kd_subject.add_argument("--keywords", help="Keywords (comma-separated, max 20)")
    p_kd.add_argument("--date", required=True, help="Lookup date (YYYY-MM-DD)")
    p_kd.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_kd.set_defaults(func=cmd_keyword_detail)

    # ── keyword-market-profile ──
    p_kmp = sub.add_parser(
        "keyword-market-profile",
        help="Server-calculated multidimensional keyword market profile",
        allow_abbrev=False,
    )
    kmp_subject = p_kmp.add_mutually_exclusive_group(required=True)
    kmp_subject.add_argument("--keyword", help="One keyword")
    kmp_subject.add_argument("--keywords", help="Keywords (comma-separated, max 20)")
    p_kmp.add_argument("--date", required=True, help="Lookup date (YYYY-MM-DD)")
    p_kmp.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_kmp.set_defaults(func=cmd_keyword_market_profile)

    # ── keyword-trend-profile ──
    p_ktp = sub.add_parser(
        "keyword-trend-profile",
        help="Server-calculated keyword trend profile for fixed weekly windows",
        allow_abbrev=False,
    )
    ktp_subject = p_ktp.add_mutually_exclusive_group(required=True)
    ktp_subject.add_argument("--keyword", help="One keyword")
    ktp_subject.add_argument("--keywords", help="Keywords (comma-separated, max 20)")
    p_ktp.add_argument("--date", required=True, help="As-of date (YYYY-MM-DD)")
    p_ktp.add_argument(
        "--window-periods",
        required=True,
        help="Comma-separated weekly windows selected from 4,8,12,26",
    )
    p_ktp.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_ktp.set_defaults(func=cmd_keyword_trend_profile)

    # ── keyword-trend ──
    p_kt = sub.add_parser("keyword-trend", help="Keyword weekly trend", allow_abbrev=False)
    kt_subject = p_kt.add_mutually_exclusive_group(required=True)
    kt_subject.add_argument("--keyword", help="One keyword")
    kt_subject.add_argument("--keywords", help="Keywords (comma-separated, max 20)")
    p_kt.add_argument("--date-from", required=True, help="Start date (YYYY-MM-DD; max 93-day range)")
    p_kt.add_argument("--date-to", required=True, help="End date (YYYY-MM-DD; max 93-day range)")
    p_kt.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_kt.set_defaults(func=cmd_keyword_trend)

    # ── keyword-extends ──
    p_ke = sub.add_parser("keyword-extends", help="Keyword expansion", allow_abbrev=False)
    p_ke.add_argument("--query", required=True, help="Seed keyword (required)")
    p_ke.add_argument("--date", help="Legacy lookup date (optional; service uses latest snapshot)")
    p_ke.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_ke.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_ke.add_argument("--page-size", type=int, default=20, help="Page size (default: 20, max 100)")
    p_ke.add_argument("--query-type", choices=["phrase", "fuzzy"], default="phrase", help="Expansion mode (default: phrase)")
    p_ke.add_argument("--sort-by", choices=["relevanceScore", "estimateSearchCount", "abaRank", "keyword"], default="relevanceScore")
    p_ke.add_argument("--sort-order", choices=["asc", "desc"], default="desc")
    p_ke.set_defaults(func=cmd_keyword_extends)

    # ── keyword-search-results ──
    p_ksr = sub.add_parser("keyword-search-results", help="Keyword SERP snapshot", allow_abbrev=False)
    p_ksr.add_argument("--keyword", required=True, help="Keyword (required)")
    p_ksr.add_argument("--date", required=True, help="Lookup date (YYYY-MM-DD)")
    p_ksr.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_ksr.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_ksr.add_argument("--page-size", type=int, default=20, help="Page size (default: 20, max 100)")
    p_ksr.add_argument("--explore-types", help="Comma-separated placements: ORG,SP,SB,SBV,SPR")
    p_ksr.add_argument("--sort-by", choices=["absolutePosition", "estimateImpressionPoint", "latestObservedAt", "price", "rating", "ratingCount", "recentSales", "asin", "title"], default="absolutePosition")
    p_ksr.add_argument("--sort-order", choices=["asc", "desc"], default="asc")
    p_ksr.set_defaults(func=cmd_keyword_search_results)

    # ── keyword-competitor-product-keywords ──
    p_kcpk = sub.add_parser("keyword-competitor-product-keywords", help="Competitor ASIN keyword rows", allow_abbrev=False)
    p_kcpk.add_argument("--asin", required=True, help="ASIN (required)")
    p_kcpk.add_argument("--date", required=True, help="Lookup date (YYYY-MM-DD)")
    p_kcpk.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_kcpk.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_kcpk.add_argument("--page-size", type=int, default=20, help="Page size (default: 20, max 100)")
    p_kcpk.add_argument("--explore-types", help="Comma-separated placements: ORG,SP,SB,SBV,SPR")
    p_kcpk.add_argument("--keyword-contains", help="Optional substring filter")
    p_kcpk.add_argument("--sort-by", choices=["trafficShare", "estimateImpressionPoint", "absolutePosition", "avgPosition", "keywordEstimateSearchCount", "keywordAbaRank", "latestObservedAt", "keyword"], default="trafficShare")
    p_kcpk.add_argument("--sort-order", choices=["asc", "desc"], default="desc")
    p_kcpk.set_defaults(func=cmd_keyword_competitor_product_keywords)

    # ── keyword-product-traffic-terms ──
    p_kptt = sub.add_parser("keyword-product-traffic-terms", help="ASIN traffic-driving keyword rows", allow_abbrev=False)
    p_kptt.add_argument("--asin", required=True, help="ASIN (required)")
    p_kptt.add_argument("--date", required=True, help="Lookup date (YYYY-MM-DD)")
    p_kptt.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_kptt.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    p_kptt.add_argument("--page-size", type=int, default=20, help="Page size (default: 20, max 100)")
    p_kptt.add_argument("--explore-types", help="Comma-separated placements: ORG,SP,SB,SBV,SPR")
    p_kptt.add_argument("--keyword-contains", help="Optional substring filter")
    p_kptt.add_argument("--sort-by", choices=["trafficShare", "estimateImpressionPoint", "absolutePosition", "avgPosition", "keywordEstimateSearchCount", "keywordAbaRank", "latestObservedAt", "keyword"], default="trafficShare")
    p_kptt.add_argument("--sort-order", choices=["asc", "desc"], default="desc")
    p_kptt.set_defaults(func=cmd_keyword_product_traffic_terms)

    # ── product-traffic-terms-profile ──
    p_pttp = sub.add_parser("product-traffic-terms-profile", help="Weekly ASIN traffic-term profile", allow_abbrev=False)
    pttp_subject = p_pttp.add_mutually_exclusive_group(required=True)
    pttp_subject.add_argument("--asin", help="One ASIN")
    pttp_subject.add_argument("--asins", help="ASINs (comma-separated, max 20)")
    p_pttp.add_argument("--date", required=True, help="Lookup date (YYYY-MM-DD)")
    p_pttp.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_pttp.set_defaults(func=cmd_product_traffic_terms_profile)

    # ── product-traffic-terms-timeline ──
    p_pttt = sub.add_parser("product-traffic-terms-timeline", help="ASIN + keyword traffic-term timeline", allow_abbrev=False)
    p_pttt.add_argument("--asin", required=True, help="ASIN (required)")
    pttt_subject = p_pttt.add_mutually_exclusive_group(required=True)
    pttt_subject.add_argument("--keyword", help="One exact keyword")
    pttt_subject.add_argument("--keywords", help="Exact keywords (comma-separated, max 20)")
    p_pttt.add_argument("--date-from", required=True, help="Start date (YYYY-MM-DD; max 61-day range)")
    p_pttt.add_argument("--date-to", required=True, help="End date (YYYY-MM-DD; max 61-day range)")
    p_pttt.add_argument("--marketplace", choices=["US", "UK"], default="US", help="Marketplace (default: US)")
    p_pttt.set_defaults(func=cmd_product_traffic_terms_timeline)

    # ── check (API self-check) ──
    p_check = sub.add_parser("check", help="Check credentials; endpoint probes are opt-in", allow_abbrev=False)
    p_check.add_argument("--endpoints", action="store_true",
                         help="Probe general commerce endpoints; consumes API credits")
    p_check.add_argument("--keyword-endpoints", action="store_true",
                         help="Probe keyword endpoints; consumes API credits")
    p_check.add_argument("--keyword", help="Keyword/query to use for --keyword-endpoints probes")
    p_check.add_argument("--asin", help="ASIN to use for ASIN keyword endpoint probes")
    p_check.add_argument("--date", help="Optional YYYY-MM-DD snapshot date for keyword probes")
    p_check.set_defaults(func=cmd_check)

    args, unknown = parser.parse_known_args()
    # Post-parse backstop: global options may legitimately precede the
    # subcommand (cli-contract.md documents that form), in which case the
    # early argv[1] check above never fired. Enforce on the parsed command
    # BEFORE the unknown-args exit so a disallowed command always yields
    # the structured refusal, never a usage error for a command that could
    # not run here anyway.
    _enforce_command_allowlist(args.command, args.format)
    if unknown:
        print(f"ERROR: Unrecognized argument(s): {' '.join(unknown)}", file=sys.stderr)
        print(f"Run 'zoodata.py {args.command} --help' to see valid options.", file=sys.stderr)
        sys.exit(1)
    # Codex and other agent runtimes may merge stdout and stderr into one tool
    # result. Buffer stderr while the command runs so retry/progress messages
    # cannot corrupt the final machine-readable JSON. If the command exits
    # before output() creates a structured result, surface the buffered stderr
    # as the sole result channel instead.
    diagnostics = io.StringIO()
    try:
        with contextlib.redirect_stderr(diagnostics):
            args.func(args)
    except BaseException:
        if not _cli_emitted_output:
            sys.stderr.write(diagnostics.getvalue())
        raise
    if not _cli_emitted_output:
        sys.stderr.write(diagnostics.getvalue())
    if _cli_had_error:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

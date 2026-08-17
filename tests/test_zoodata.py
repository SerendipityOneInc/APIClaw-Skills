"""
Test suite for zoodata/scripts/zoodata.py

Coverage:
  - parse_category: all supported separators and edge cases
  - PRODUCT_MODES: all 13 modes accepted; enum values match backend contract
  - argparse: all subcommands have valid --help; allow_abbrev=False regression
  - param construction: each subcommand passes the right keys to api_call
  - output format: json and compact both produce valid JSON
  - page / page-size: not overwritten by prefix matching (regression for #48)

Run from repo root:
    python tests/test_zoodata.py
    python -m pytest tests/test_zoodata.py -v
"""

import importlib.util
import http.client
import io
import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import mock_open, patch

# ---------------------------------------------------------------------------
# Load module under test
# ---------------------------------------------------------------------------
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "zoodata", "scripts", "zoodata.py")

spec = importlib.util.spec_from_file_location("zoodata", SCRIPT_PATH)
zoodata = importlib.util.module_from_spec(spec)
with patch.dict("os.environ", {"ZOODATA_API_KEY": "test_key"}):
    spec.loader.exec_module(zoodata)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
MOCK_OK = {"success": True, "data": [], "_query": {"endpoint": "", "params": {}}}


class MockHttpResponse:
    """Minimal urllib response carrying an explicit outer HTTP status."""

    def __init__(self, status, payload=None, raw_body=None):
        self.status = status
        self._body = (
            raw_body
            if raw_body is not None
            else json.dumps(payload).encode("utf-8")
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def getcode(self):
        return self.status

    def read(self):
        return self._body


def http_error_side_effect(status, reason, *, payload=None, raw_body=None, url=None):
    """Return a side effect that raises a fresh HTTPError for every retry."""
    body = raw_body if raw_body is not None else json.dumps(payload).encode("utf-8")
    target = url or "https://api.zoodata.ai/openapi/v2/keywords/detail"

    def raise_error(*args, **kwargs):
        raise urllib.error.HTTPError(target, status, reason, {}, io.BytesIO(body))

    return raise_error


def run_cli(*argv):
    """Run zoodata.main() with mocked api_call; return (endpoint, params)."""
    captured = {}

    def fake_api_call(endpoint, params):
        captured["endpoint"] = endpoint
        captured["params"] = dict(params)
        return {**MOCK_OK, "_query": {"endpoint": endpoint, "params": params}}

    with patch.object(zoodata, "api_call", side_effect=fake_api_call), \
         patch.object(zoodata, "output"), \
         patch.object(sys, "argv", ["zoodata.py", *argv]):
        zoodata.main()

    return captured


def run_cli_stdout(fmt, subcmd, *args):
    """Run zoodata.main() with real output(); return stdout as string.

    --format must precede the subcommand (it's a root-level arg).
    """
    import io

    def fake_api_call(endpoint, params):
        return {**MOCK_OK, "_query": {"endpoint": endpoint, "params": params}}

    buf = io.StringIO()
    argv = ["zoodata.py", "--format", fmt, subcmd, *args]
    with patch.object(zoodata, "api_call", side_effect=fake_api_call), \
         patch.object(sys, "argv", argv), \
         patch("sys.stdout", buf):
        zoodata.main()

    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. parse_category
# ---------------------------------------------------------------------------
class TestParseCategory(unittest.TestCase):

    def test_comma_separated(self):
        self.assertEqual(zoodata.parse_category("Pet Supplies,Dogs,Toys"),
                         ["Pet Supplies", "Dogs", "Toys"])

    def test_spaced_arrow(self):
        self.assertEqual(zoodata.parse_category("Pet Supplies > Dogs > Toys"),
                         ["Pet Supplies", "Dogs", "Toys"])

    def test_bare_arrow(self):
        self.assertEqual(zoodata.parse_category("Pet Supplies>Dogs>Toys"),
                         ["Pet Supplies", "Dogs", "Toys"])

    def test_bare_arrow_with_spaces_in_name(self):
        self.assertEqual(zoodata.parse_category("Home & Kitchen>Storage & Organization"),
                         ["Home & Kitchen", "Storage & Organization"])

    def test_single_segment(self):
        self.assertEqual(zoodata.parse_category("Electronics"), ["Electronics"])

    def test_empty_string(self):
        self.assertEqual(zoodata.parse_category(""), [])

    def test_spaced_arrow_takes_priority_over_bare(self):
        # " > " is checked before ">", so "A > B>C" splits on " > " first
        result = zoodata.parse_category("A > B>C")
        self.assertEqual(result, ["A", "B>C"])

    def test_strips_whitespace(self):
        self.assertEqual(zoodata.parse_category("  Pet Supplies , Dogs "),
                         ["Pet Supplies", "Dogs"])

    def test_arrow_protects_comma_in_category_name(self):
        """Amazon category names can contain commas; '>' must not split them.
        Regression: comma-split broke 'Headphones, Earbuds & Accessories'."""
        self.assertEqual(
            zoodata.parse_category("Electronics > Headphones, Earbuds & Accessories > Earbud Headphones"),
            ["Electronics", "Headphones, Earbuds & Accessories", "Earbud Headphones"])

    def test_json_array_input(self):
        self.assertEqual(zoodata.parse_category('["Sports & Outdoors"]'),
                         ["Sports & Outdoors"])

    def test_json_array_with_comma_in_name(self):
        self.assertEqual(
            zoodata.parse_category('["Health & Household", "Vitamins, Minerals & Supplements", "Collagen"]'),
            ["Health & Household", "Vitamins, Minerals & Supplements", "Collagen"])

    def test_malformed_json_falls_through_to_separator_parsing(self):
        self.assertEqual(zoodata.parse_category("[not json"), ["[not json"])


# ---------------------------------------------------------------------------
# 2. PRODUCT_MODES completeness
# ---------------------------------------------------------------------------
class TestProductModes(unittest.TestCase):

    def test_all_13_modes_defined(self):
        self.assertEqual(len(zoodata.PRODUCT_MODES), 13)

    def test_all_modes_accepted_by_cli(self):
        """Every mode name must be accepted by 'products --mode <name>' without sys.exit."""
        for mode in zoodata.PRODUCT_MODES:
            with self.subTest(mode=mode):
                # Should not raise or call sys.exit
                result = run_cli("products", "--keyword", "test", "--mode", mode)
                self.assertIn("endpoint", result)

    def test_unknown_mode_exits(self):
        with patch.object(zoodata, "api_call", return_value=MOCK_OK), \
             patch.object(zoodata, "output"), \
             patch.object(sys, "argv", ["zoodata.py", "products", "--keyword", "test",
                                        "--mode", "nonexistent-mode"]), \
             self.assertRaises(SystemExit) as cm:
            zoodata.main()
        self.assertNotEqual(cm.exception.code, 0)

    # Backend enum contracts — mirror hermes-service
    # app/api/openapi/schemas/products.py (LISTING_AGE_VALUES / BADGE_VALUES / FULFILLMENT_VALUES).
    # These guard against the CLI emitting preset values the API rejects with 422.
    BACKEND_LISTING_AGE = {"30d", "90d", "180d", "1y", "2y"}
    BACKEND_BADGES = {"bestSeller", "amazonChoice", "newRelease", "aPlus", "video"}
    BACKEND_FULFILLMENTS = {"AMZ", "FBA", "FBM"}

    def test_mode_enum_values_match_backend_contract(self):
        """Every enum-constrained filter value in a preset must be one the backend accepts.
        Regression: modes once sent listingAge '180' and badges ['New Release'] → hard 422."""
        for mode, filters in zoodata.PRODUCT_MODES.items():
            with self.subTest(mode=mode):
                if "listingAge" in filters:
                    self.assertIn(filters["listingAge"], self.BACKEND_LISTING_AGE,
                                  f"{mode}: listingAge {filters['listingAge']!r} not a backend enum value")
                for badge in filters.get("badges", []):
                    self.assertIn(badge, self.BACKEND_BADGES,
                                  f"{mode}: badge {badge!r} not a backend enum value")
                for ful in filters.get("fulfillments", []):
                    self.assertIn(ful, self.BACKEND_FULFILLMENTS,
                                  f"{mode}: fulfillment {ful!r} not a backend enum value")


# ---------------------------------------------------------------------------
# 3. --help for every subcommand (argparse definition sanity)
# ---------------------------------------------------------------------------
SUBCOMMANDS = [
    "categories", "market", "products", "competitors", "product",
    "report", "opportunity", "market-entry", "competitor-analysis",
    "pricing-analysis", "daily-radar", "listing-audit", "opportunity-scan",
    "review-deepdive", "analyze", "price-band-overview", "price-band-detail",
    "brand-overview", "brand-detail", "history",
    "keyword-detail", "keyword-market-profile", "keyword-trend-profile", "keyword-trend", "keyword-extends",
    "keyword-search-results", "keyword-competitor-product-keywords",
    "keyword-product-traffic-terms",
    "product-traffic-terms-profile", "product-traffic-terms-timeline",
    "check",
]


class TestSubcommandHelp(unittest.TestCase):

    def _assert_help_exits_0(self, subcmd):
        with patch.object(sys, "argv", ["zoodata.py", subcmd, "--help"]), \
             self.assertRaises(SystemExit) as cm:
            zoodata.main()
        self.assertEqual(cm.exception.code, 0, f"'{subcmd} --help' should exit 0")

    def test_root_help(self):
        with patch.object(sys, "argv", ["zoodata.py", "--help"]), \
             self.assertRaises(SystemExit) as cm:
            zoodata.main()
        self.assertEqual(cm.exception.code, 0)

    def test_all_subcommand_help(self):
        for subcmd in SUBCOMMANDS:
            with self.subTest(subcmd=subcmd):
                self._assert_help_exits_0(subcmd)


# ---------------------------------------------------------------------------
# 4. allow_abbrev=False regression
# ---------------------------------------------------------------------------
class TestAllowAbbrevDisabled(unittest.TestCase):

    def _assert_parse_error(self, *argv):
        with patch.object(zoodata, "api_call", return_value=MOCK_OK), \
             patch.object(zoodata, "output"), \
             patch.object(sys, "argv", ["zoodata.py", *argv]), \
             self.assertRaises(SystemExit) as cm:
            zoodata.main()
        self.assertNotEqual(cm.exception.code, 0)

    def test_abbreviated_page_errors_on_market(self):
        self._assert_parse_error("market", "--category", "Sports", "--pag", "1")

    def test_abbreviated_page_size_errors_on_market(self):
        self._assert_parse_error("market", "--category", "Sports", "--page-s", "20")

    def test_abbreviated_keyword_errors(self):
        self._assert_parse_error("market", "--key", "yoga")

    def test_abbreviated_category_errors(self):
        self._assert_parse_error("market", "--cat", "Sports")


# ---------------------------------------------------------------------------
# 5. page / page-size param construction (regression for issue #48)
# ---------------------------------------------------------------------------
class TestPageParamConstruction(unittest.TestCase):

    def _check(self, subcmd, extra_args, expected_page, expected_page_size):
        result = run_cli(subcmd, *extra_args,
                         "--page-size", str(expected_page_size),
                         "--page", str(expected_page))
        self.assertEqual(result["params"].get("pageSize"), expected_page_size,
                         f"{subcmd}: pageSize should be {expected_page_size}")
        self.assertEqual(result["params"].get("page"), expected_page,
                         f"{subcmd}: page should be {expected_page}")

    def test_market(self):
        self._check("market", ["--keyword", "yoga"], 3, 50)

    def test_products(self):
        self._check("products", ["--keyword", "yoga"], 2, 30)

    def test_price_band_overview(self):
        self._check("price-band-overview", ["--keyword", "yoga"], 2, 40)

    def test_price_band_detail(self):
        self._check("price-band-detail", ["--keyword", "yoga"], 4, 10)

    def test_brand_overview(self):
        self._check("brand-overview", ["--keyword", "yoga"], 2, 15)

    def test_brand_detail(self):
        self._check("brand-detail", ["--keyword", "yoga"], 3, 25)

    def test_competitors(self):
        self._check("competitors", ["--keyword", "earbuds"], 2, 30)

    def test_market_page_default_is_1(self):
        result = run_cli("market", "--keyword", "yoga")
        self.assertEqual(result["params"].get("page"), 1)
        self.assertEqual(result["params"].get("pageSize"), 20)


# ---------------------------------------------------------------------------
# 6. API endpoint routing (each subcommand hits the right endpoint)
# ---------------------------------------------------------------------------
class TestEndpointRouting(unittest.TestCase):

    def test_categories(self):
        r = run_cli("categories", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "categories")

    def test_market(self):
        r = run_cli("market", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "markets/search")

    def test_products(self):
        r = run_cli("products", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/search")

    def test_competitors(self):
        r = run_cli("competitors", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/competitors")

    def test_product(self):
        r = run_cli("product", "--asin", "B09V3KXJPB")
        self.assertEqual(r["endpoint"], "realtime/product")

    def test_price_band_overview(self):
        r = run_cli("price-band-overview", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/price-band-overview")

    def test_price_band_detail(self):
        r = run_cli("price-band-detail", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/price-band-detail")


class TestCategoryResolutionMeta(unittest.TestCase):
    """Regression: an empty top-level `categories` section for a multi-word
    product phrase must not read as missing data. `_resolve_category` resolves
    via the products/search fallback and records the path in
    `meta.resolved_category_path` so composites and callers can tell fallback
    resolution apart from a genuine gap."""

    def _caller(self, responses):
        def api_caller(endpoint, params, label=None):
            return responses.get(endpoint, {"success": True, "data": []})
        return api_caller

    def test_keyword_fallback_records_resolved_path(self):
        path = ["Sports & Outdoors", "Exercise & Fitness", "Yoga", "Mats"]
        responses = {
            # Priority 1: categories/search misses on the product phrase.
            "categories": {"success": True, "data": []},
            # Priority 3: top product carries the real categoryPath.
            "products/search": {"success": True, "data": [{"categoryPath": path}]},
        }
        results = {}
        resolved, source = zoodata._resolve_category(
            self._caller(responses), lambda *a, **k: None,
            keyword="yoga mat", results=results,
        )
        self.assertEqual(resolved, path)
        self.assertEqual(source, "inferred_from_search")
        # The empty `categories` section is disambiguated by the resolved path.
        self.assertEqual(results["categories"]["data"], [])
        self.assertEqual(results["meta"]["resolved_category_path"], path)

    def test_meta_key_name_is_consistent(self):
        # Every composite records the resolved path under the single documented
        # key `resolved_category_path`. The legacy `resolved_category` name (set by
        # 7 composite bodies before standardization) must not reappear, or pricing
        # and other ASIN-first paths drift back to an undocumented key.
        src = open(SCRIPT_PATH).read()
        self.assertNotIn('["resolved_category"]', src)
        self.assertIn('["resolved_category_path"]', src)

    def test_unresolved_keyword_records_null_path(self):
        responses = {
            "categories": {"success": True, "data": []},
            "products/search": {"success": True, "data": []},
        }
        results = {}
        resolved, source = zoodata._resolve_category(
            self._caller(responses), lambda *a, **k: None,
            keyword="zzz nonexistent niche", results=results,
        )
        self.assertIsNone(resolved)
        # Path key is always present so consumers can branch on null vs a real path.
        self.assertIn("resolved_category_path", results["meta"])
        self.assertIsNone(results["meta"]["resolved_category_path"])

    def test_brand_overview(self):
        r = run_cli("brand-overview", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/brand-overview")

    def test_brand_detail(self):
        r = run_cli("brand-detail", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/brand-detail")

    def test_keyword_detail(self):
        r = run_cli("keyword-detail", "--keyword", "yoga mat", "--date", "2026-06-29")
        self.assertEqual(r["endpoint"], "keywords/detail")
        self.assertEqual(r["params"], {
            "keyword": "yoga mat",
            "date": "2026-06-29",
            "marketplace": "US",
            "granularity": "week",
        })

    def test_keyword_detail_batch(self):
        r = run_cli("keyword-detail", "--keywords", "yoga mat,pilates mat", "--date", "2026-06-29")
        self.assertEqual(r["params"]["keywords"], ["yoga mat", "pilates mat"])

    def test_keyword_detail_batch_rejects_duplicates(self):
        with self.assertRaises(SystemExit):
            run_cli("keyword-detail", "--keywords", "Yoga Mat,yoga mat", "--date", "2026-06-29")

    def test_keyword_detail_batch_rejects_more_than_20(self):
        with self.assertRaises(SystemExit):
            run_cli("keyword-detail", "--keywords", ",".join(f"term{i}" for i in range(21)), "--date", "2026-06-29")

    def test_keyword_market_profile(self):
        r = run_cli("keyword-market-profile", "--keyword", "yoga mat", "--date", "2026-06-29")
        self.assertEqual(r["endpoint"], "keywords/market-profile")
        self.assertEqual(r["params"], {
            "keyword": "yoga mat",
            "date": "2026-06-29",
            "marketplace": "US",
            "granularity": "week",
        })

    def test_keyword_market_profile_batch(self):
        r = run_cli(
            "keyword-market-profile",
            "--keywords", "yoga mat,pilates mat",
            "--date", "2026-06-29",
            "--marketplace", "UK",
        )
        self.assertEqual(r["params"]["keywords"], ["yoga mat", "pilates mat"])
        self.assertEqual(r["params"]["marketplace"], "UK")

    def test_keyword_market_profile_batch_rejects_duplicates(self):
        with self.assertRaises(SystemExit):
            run_cli("keyword-market-profile", "--keywords", "Yoga Mat,yoga mat", "--date", "2026-06-29")

    def test_keyword_trend(self):
        r = run_cli("keyword-trend",
                    "--keyword", "yoga mat",
                    "--date-from", "2026-06-01",
                    "--date-to", "2026-06-29")
        self.assertEqual(r["endpoint"], "keywords/trend")
        self.assertEqual(r["params"]["dateFrom"], "2026-06-01")
        self.assertEqual(r["params"]["dateTo"], "2026-06-29")
        self.assertEqual(r["params"]["granularity"], "week")

    def test_keyword_trend_profile(self):
        r = run_cli(
            "keyword-trend-profile",
            "--keywords", "yoga mat,pilates mat",
            "--date", "2026-07-15",
            "--window-periods", "4,12,26",
            "--marketplace", "UK",
        )
        self.assertEqual(r["endpoint"], "keywords/trend-profile")
        self.assertEqual(r["params"]["keywords"], ["yoga mat", "pilates mat"])
        self.assertEqual(r["params"]["windowPeriods"], [4, 12, 26])
        self.assertEqual(r["params"]["marketplace"], "UK")
        self.assertEqual(r["params"]["granularity"], "week")

    def test_keyword_trend_profile_rejects_duplicate_windows(self):
        with self.assertRaises(SystemExit):
            run_cli(
                "keyword-trend-profile", "--keyword", "yoga mat",
                "--date", "2026-07-15", "--window-periods", "4,4",
            )

    def test_keyword_trend_profile_rejects_invalid_window(self):
        with self.assertRaises(SystemExit):
            run_cli(
                "keyword-trend-profile", "--keyword", "yoga mat",
                "--date", "2026-07-15", "--window-periods", "6",
            )

    def test_keyword_extends(self):
        r = run_cli("keyword-extends",
                    "--query", "yoga mat",
                    "--date", "2026-06-29",
                    "--query-type", "fuzzy",
                    "--page-size", "50")
        self.assertEqual(r["endpoint"], "keywords/extends")
        self.assertEqual(r["params"]["query"], "yoga mat")
        self.assertEqual(r["params"]["queryType"], "fuzzy")
        self.assertEqual(r["params"]["pageSize"], 50)

    def test_keyword_extends_date_optional(self):
        r = run_cli("keyword-extends", "--query", "yoga mat")
        self.assertNotIn("date", r["params"])

    def test_keyword_search_results(self):
        r = run_cli("keyword-search-results",
                    "--keyword", "yoga mat",
                    "--date", "2026-06-29",
                    "--explore-types", "ORG,SP")
        self.assertEqual(r["endpoint"], "keywords/search-results")
        self.assertEqual(r["params"]["exploreTypes"], ["ORG", "SP"])
        self.assertEqual(r["params"]["granularity"], "week")
        self.assertNotIn("lookbackDays", r["params"])

    def test_keyword_competitor_product_keywords(self):
        r = run_cli("keyword-competitor-product-keywords",
                    "--asin", "B01CGLCGRA",
                    "--date", "2026-06-29",
                    "--keyword-contains", "yoga",
                    "--explore-types", "ORG")
        self.assertEqual(r["endpoint"], "keywords/competitor-product-keywords")
        self.assertEqual(r["params"]["keywordContains"], "yoga")
        self.assertEqual(r["params"]["exploreTypes"], ["ORG"])
        self.assertEqual(r["params"]["granularity"], "week")
        self.assertNotIn("lookbackDays", r["params"])

    def test_keyword_product_traffic_terms(self):
        r = run_cli("keyword-product-traffic-terms",
                    "--asin", "B01CGLCGRA",
                    "--date", "2026-06-29")
        self.assertEqual(r["endpoint"], "keywords/product-traffic-terms")
        self.assertEqual(r["params"]["asin"], "B01CGLCGRA")
        self.assertEqual(r["params"]["sortBy"], "trafficShare")
        self.assertEqual(r["params"]["granularity"], "week")
        self.assertNotIn("lookbackDays", r["params"])

    def test_product_traffic_terms_profile_single(self):
        r = run_cli("product-traffic-terms-profile",
                    "--asin", "B01CGLCGRA",
                    "--date", "2026-06-29")
        self.assertEqual(r["endpoint"], "keywords/product-traffic-terms-profile")
        self.assertEqual(r["params"], {
            "asin": "B01CGLCGRA",
            "date": "2026-06-29",
            "marketplace": "US",
            "granularity": "week",
        })

    def test_product_traffic_terms_profile_batch(self):
        r = run_cli(
            "product-traffic-terms-profile",
            "--asins", "B01CGLCGRA,B07FR2V8SH",
            "--date", "2026-06-29",
        )
        self.assertEqual(r["endpoint"], "keywords/product-traffic-terms-profile")
        self.assertEqual(r["params"]["asins"], ["B01CGLCGRA", "B07FR2V8SH"])
        self.assertEqual(r["params"]["granularity"], "week")

    def test_product_traffic_terms_profile_rejects_more_than_20_asins(self):
        with self.assertRaisesRegex(SystemExit, "at most 20 ASINs"):
            run_cli(
                "product-traffic-terms-profile",
                "--asins", ",".join(f"B{i:09d}" for i in range(21)),
                "--date", "2026-06-29",
            )

    def test_product_traffic_terms_profile_rejects_duplicate_asins(self):
        with self.assertRaisesRegex(SystemExit, "case-insensitive duplicates"):
            run_cli(
                "product-traffic-terms-profile",
                "--asins", "B01CGLCGRA,b01cglcgra",
                "--date", "2026-06-29",
            )

    def test_product_traffic_terms_timeline(self):
        r = run_cli("product-traffic-terms-timeline",
                    "--asin", "B01CGLCGRA",
                    "--keyword", "yoga mat",
                    "--date-from", "2026-06-23",
                    "--date-to", "2026-06-29")
        self.assertEqual(r["endpoint"], "keywords/product-traffic-terms-timeline")
        self.assertEqual(r["params"], {
            "asin": "B01CGLCGRA",
            "keyword": "yoga mat",
            "dateFrom": "2026-06-23",
            "dateTo": "2026-06-29",
            "marketplace": "US",
            "granularity": "week",
        })

    def test_product_traffic_terms_timeline_batch(self):
        r = run_cli("product-traffic-terms-timeline",
                    "--asin", "B01CGLCGRA",
                    "--keywords", "yoga mat,pilates mat",
                    "--date-from", "2026-06-23",
                    "--date-to", "2026-06-29")
        self.assertEqual(r["params"]["keywords"], ["yoga mat", "pilates mat"])


# ---------------------------------------------------------------------------
# 7. Output format produces valid JSON
# ---------------------------------------------------------------------------
class TestOutputFormat(unittest.TestCase):

    def test_json_format_is_valid(self):
        out = run_cli_stdout("json", "market", "--keyword", "yoga")
        parsed = json.loads(out)
        self.assertIsInstance(parsed, dict)

    def test_compact_format_is_valid_json(self):
        out = run_cli_stdout("compact", "market", "--keyword", "yoga")
        parsed = json.loads(out)
        self.assertIsInstance(parsed, dict)

    def test_compact_is_single_line(self):
        out = run_cli_stdout("compact", "market", "--keyword", "yoga")
        self.assertEqual(out.count("\n"), 1)  # only the trailing newline

    def test_json_is_indented(self):
        out = run_cli_stdout("json", "market", "--keyword", "yoga")
        self.assertGreater(out.count("\n"), 1)


class TestSingleChannelCliOutput(unittest.TestCase):

    def test_success_after_incomplete_read_emits_only_final_stdout_json(self):
        response = MockHttpResponse(200, {
            "success": True,
            "data": {"brands": []},
        })
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(
                 zoodata.urllib.request,
                 "urlopen",
                 side_effect=[http.client.IncompleteRead(b"partial", 10), response],
             ) as urlopen, \
             patch.object(zoodata.time, "sleep"), \
             patch.object(sys, "argv", [
                 "zoodata.py", "brand-detail", "--keyword", "storage bins",
             ]), \
             patch("sys.stdout", stdout), \
             patch("sys.stderr", stderr):
            zoodata.main()

        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(stderr.getvalue(), "")
        result = json.loads(stdout.getvalue())
        self.assertIs(result["success"], True)
        self.assertEqual(result["_query"]["endpoint"], "products/brand-detail")

    def test_exhausted_retry_emits_only_final_stdout_error_json(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(
                 zoodata.urllib.request,
                 "urlopen",
                 side_effect=http.client.IncompleteRead(b"partial", 10),
             ), \
             patch.object(zoodata.time, "sleep"), \
             patch.object(sys, "argv", [
                 "zoodata.py", "brand-detail", "--keyword", "storage bins",
             ]), \
             patch("sys.stdout", stdout), \
             patch("sys.stderr", stderr), \
             self.assertRaises(SystemExit) as raised:
            zoodata.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(stderr.getvalue(), "")
        result = json.loads(stdout.getvalue())
        self.assertIs(result["success"], False)
        self.assertIs(result["error"]["retryExhausted"], True)

    def test_pre_result_failure_emits_only_stderr(self):
        stdout = io.StringIO()
        stderr = io.StringIO()

        def missing_key():
            print("credential failure", file=sys.stderr)
            raise SystemExit(1)

        with patch.object(zoodata, "get_api_key", side_effect=missing_key), \
             patch.object(sys, "argv", [
                 "zoodata.py", "brand-detail", "--keyword", "storage bins",
             ]), \
             patch("sys.stdout", stdout), \
             patch("sys.stderr", stderr), \
             self.assertRaises(SystemExit):
            zoodata.main()

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "credential failure\n")


class TestApiErrorPropagation(unittest.TestCase):

    def test_successful_http_response_preserves_authoritative_transport_status(self):
        response = MockHttpResponse(201, {
            "success": True,
            "data": {"status": "ok"},
            "_transport": {"status": 599},
        })

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", return_value=response), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertIs(result["success"], True)
        self.assertEqual(result["_transport"], {"status": 201})

    def test_http_2xx_business_error_cannot_spoof_transport_status(self):
        response = MockHttpResponse(200, {
            "success": False,
            "error": {
                "code": "BUSINESS_ERROR",
                "status": 500,
                "message": "Request could not be completed",
            },
            "_transport": {"status": 500},
        })

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", return_value=response), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertIs(result["success"], False)
        self.assertEqual(result["error"]["status"], 500)
        self.assertEqual(result["_transport"], {"status": 200})

    def test_malformed_or_non_object_http_response_is_not_retried(self):
        cases = (
            (MockHttpResponse(200, payload=[]), "Expected a JSON object"),
            (MockHttpResponse(200, raw_body=b"{not-json"), "not valid UTF-8 JSON"),
            (
                MockHttpResponse(200, payload={"data": {}}),
                "Expected top-level success to be a JSON boolean",
            ),
        )

        for response, expected_detail in cases:
            with self.subTest(expected_detail=expected_detail), \
                 patch.object(zoodata, "get_api_key", return_value="test_key"), \
                 patch.object(zoodata.urllib.request, "urlopen", return_value=response) as urlopen, \
                 patch.object(zoodata.time, "sleep"):
                result = zoodata.api_call("keywords/detail", {
                    "keyword": "yoga mat",
                    "date": "2026-07-29",
                })

            self.assertEqual(urlopen.call_count, 1)
            self.assertIs(result["success"], False)
            self.assertEqual(result["error"]["code"], "MALFORMED_RESPONSE")
            self.assertIn(expected_detail, result["error"]["detail"])
            self.assertNotIn("action", result["error"])
            self.assertEqual(result["_transport"], {"status": 200})

    def test_http_500_stops_after_internal_retries_without_parameter_recovery(self):
        def service_error(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/product-traffic-terms",
                500,
                "Internal Server Error",
                {},
                io.BytesIO(b"{}"),
            )

        params = {
            "asin": "B0F8P9MQWY",
            "date": "2026-07-27",
            "marketplace": "US",
        }
        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=service_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/product-traffic-terms", params)

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["error"]["status"], 500)
        self.assertEqual(result["error"]["message"], "HTTP 500 after 3 attempts")
        self.assertEqual(result["_transport"], {"status": 500})
        self.assertNotIn("action", result["error"])
        self.assertIs(result["error"]["retryExhausted"], True)
        self.assertNotIn("workflowDisposition", result["error"])
        self.assertNotIn("retryPolicy", result["error"])
        self.assertNotIn("parameterMutationAllowed", result["error"])
        self.assertEqual(result["_query"]["params"], params)

    def test_non_keyword_http_500_uses_the_same_terminal_contract(self):
        def service_error(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/markets/search",
                500,
                "Internal Server Error",
                {},
                io.BytesIO(b"{}"),
            )

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=service_error), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("markets/search", {
                "categoryKeyword": "yoga mat",
                "pageSize": 20,
            })

        self.assertEqual(result["_transport"], {"status": 500})
        self.assertNotIn("action", result["error"])
        self.assertIs(result["error"]["retryExhausted"], True)

    def test_http_429_uses_fixed_blind_attempt_budget_and_preserves_status(self):
        def rate_limit_error(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/detail",
                429,
                "Too Many Requests",
                {},
                io.BytesIO(b"{}"),
            )

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=rate_limit_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["error"]["status"], 429)
        self.assertEqual(result["error"]["message"], "HTTP 429 after 3 attempts")
        self.assertNotIn("action", result["error"])
        self.assertIs(result["error"]["retryExhausted"], True)

    def test_http_404_uses_fixed_blind_attempt_budget(self):
        http_error = http_error_side_effect(404, "Not Found", payload={})

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["_transport"], {"status": 404})
        self.assertEqual(result["error"]["message"], "HTTP 404 after 3 attempts")
        self.assertNotIn("action", result["error"])
        self.assertIs(result["error"]["retryExhausted"], True)

    def test_http_410_preserves_final_replacement_contract_after_blind_retries(self):
        server_response = {
            "error": {
                "code": "endpoint_gone",
                "message": (
                    "product-traffic-terms-overview has been retired. "
                    "Use product-traffic-terms-profile instead."
                ),
                "details": {
                    "replacementMethod": "POST",
                    "replacementPath": "/openapi/v2/keywords/product-traffic-terms-profile",
                    "supportedGranularity": ["week"],
                    "maxAsins": 20,
                },
            },
        }
        http_error = http_error_side_effect(
            410,
            "Gone",
            payload=server_response,
            url="https://api.zoodata.ai/openapi/v2/keywords/product-traffic-terms-overview",
        )

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/product-traffic-terms-overview", {
                "asin": "B01CGLCGRA",
                "date": "2026-07-29",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertIs(result["success"], False)
        self.assertEqual(result["error"]["code"], server_response["error"]["code"])
        self.assertIs(result["error"]["retryExhausted"], True)
        self.assertEqual(result["_transport"], {"status": 410})
        self.assertEqual(
            result["error"]["details"]["replacementPath"],
            "/openapi/v2/keywords/product-traffic-terms-profile",
        )

    def test_account_http_errors_preserve_final_server_message_after_blind_retries(self):
        for status, code in ((401, "invalid_api_key"), (402, "quota_exhausted")):
            server_response = {
                "error": {
                    "code": code,
                    "message": f"server message for {status}",
                    "details": {"status": status},
                },
            }
            http_error = http_error_side_effect(status, "account error", payload=server_response)

            with self.subTest(status=status), \
                 patch.object(zoodata, "get_api_key", return_value="test_key"), \
                 patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error) as urlopen, \
                 patch.object(zoodata.time, "sleep"):
                result = zoodata.api_call("keywords/detail", {
                    "keyword": "yoga mat",
                    "date": "2026-07-29",
                })

            self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
            self.assertEqual(result["error"]["code"], server_response["error"]["code"])
            self.assertEqual(result["error"]["message"], server_response["error"]["message"])
            self.assertIs(result["error"]["retryExhausted"], True)
            self.assertEqual(result["_transport"], {"status": status})

    def test_other_http_4xx_preserves_final_structured_response_after_blind_retries(self):
        server_response = {
            "success": False,
            "error": {
                "code": "ACCESS_DENIED",
                "message": "This account cannot access the requested marketplace.",
                "details": {"marketplace": "UK"},
            },
            "meta": {"requestId": "req_denied"},
        }
        http_error = http_error_side_effect(403, "Forbidden", payload=server_response)

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
                "marketplace": "UK",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["error"]["code"], server_response["error"]["code"])
        self.assertIs(result["error"]["retryExhausted"], True)
        self.assertEqual(result["meta"], server_response["meta"])
        self.assertEqual(result["_transport"], {"status": 403})

    def test_http_error_credit_metadata_is_recorded(self):
        server_response = {
            "error": {"code": "FAILED", "message": "request failed after billing"},
            "meta": {
                "creditsConsumed": 1,
                "creditsConsumedExact": 0.5,
                "creditsRemaining": 99,
                "creditsRemainingExact": 99.5,
            },
        }
        http_error = http_error_side_effect(400, "Bad Request", payload=server_response)
        tracker = zoodata._CreditTracker()

        with patch.object(zoodata, "_CREDITS", tracker), \
             patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertEqual(result["meta"], server_response["meta"])
        self.assertEqual(tracker.calls, 1)
        self.assertEqual(tracker.consumed, 1)
        self.assertEqual(tracker.consumed_exact, 0.5)

    def test_non_json_http_error_body_is_retained(self):
        def gateway_error(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/detail",
                502,
                "Bad Gateway",
                {},
                io.BytesIO(b"upstream gateway unavailable"),
            )

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=gateway_error), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertEqual(result["_serverResponseText"], "upstream gateway unavailable")
        self.assertEqual(result["_transport"], {"status": 502})
        self.assertIs(result["error"]["retryExhausted"], True)

    def test_retryable_structured_error_preserves_server_fields(self):
        server_response = {
            "success": False,
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "profile calculator is warming up",
                "details": {"component": "profile-calculator"},
            },
            "meta": {"requestId": "req_service"},
        }

        def service_error(*args, **kwargs):
            raise urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/product-traffic-terms-profile",
                503,
                "Service Unavailable",
                {},
                io.BytesIO(json.dumps(server_response).encode("utf-8")),
            )

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=service_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/product-traffic-terms-profile", {
                "asin": "B01CGLCGRA",
                "date": "2026-07-29",
                "granularity": "week",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["error"]["code"], "SERVICE_UNAVAILABLE")
        self.assertEqual(result["error"]["message"], "profile calculator is warming up")
        self.assertEqual(result["error"]["details"], {"component": "profile-calculator"})
        self.assertIs(result["error"]["retryExhausted"], True)
        self.assertEqual(result["meta"], server_response["meta"])
        self.assertEqual(result["_transport"], {"status": 503})

    def test_retryable_http_error_keeps_only_final_attempt_body(self):
        first_response = {
            "error": {
                "code": "FIRST_ATTEMPT",
                "message": "stale response from the first attempt",
            },
        }
        errors = [
            urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/detail",
                500,
                "Internal Server Error",
                {},
                io.BytesIO(json.dumps(first_response).encode("utf-8")),
            ),
            urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/detail",
                502,
                "Bad Gateway",
                {},
                io.BytesIO(b"intermediate gateway response"),
            ),
            urllib.error.HTTPError(
                "https://api.zoodata.ai/openapi/v2/keywords/detail",
                503,
                "Service Unavailable",
                {},
                io.BytesIO(b""),
            ),
        ]

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=errors) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["_transport"], {"status": 503})
        self.assertEqual(result["error"]["message"], "HTTP 503 after 3 attempts")
        self.assertNotIn("code", result["error"])
        self.assertNotIn("_serverResponse", result)
        self.assertNotIn("_serverResponseText", result)

    def test_exhausted_network_failure_emits_terminal_interface_failure_signal(self):
        network_error = urllib.error.URLError("network unavailable")

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=network_error) as urlopen, \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertEqual(urlopen.call_count, zoodata.MAX_RETRIES)
        self.assertEqual(result["error"]["status"], 0)
        self.assertNotIn("action", result["error"])
        self.assertIs(result["error"]["retryExhausted"], True)

    def test_http_422_preserves_structured_server_response(self):
        server_response = {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Remove `lookbackDays` and set `granularity` to `week`.",
                "details": [{"field": "lookbackDays", "type": "extra_forbidden"}],
            },
            "meta": {"requestId": "req_test"},
        }
        http_error = http_error_side_effect(
            422,
            "Unprocessable Entity",
            payload=server_response,
            url="https://api.zoodata.ai/openapi/v2/keywords/search-results",
        )

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/search-results", {
                "keyword": "yoga mat",
                "date": "2026-07-23",
                "granularity": "lately_day",
                "lookbackDays": 7,
            })

        self.assertEqual(result["error"]["code"], server_response["error"]["code"])
        self.assertEqual(result["error"]["details"], server_response["error"]["details"])
        self.assertIs(result["error"]["retryExhausted"], True)
        self.assertEqual(result["meta"], server_response["meta"])
        self.assertIs(result["success"], False)
        self.assertEqual(result["_transport"], {"status": 422})
        self.assertEqual(result["_query"]["params"]["lookbackDays"], 7)

    def test_http_422_transport_status_cannot_be_overridden_by_response_body(self):
        server_response = {
            "success": True,
            "error": {
                "code": "VALIDATION_ERROR",
                "status": 500,
                "message": "Invalid request",
            },
        }
        http_error = http_error_side_effect(422, "Unprocessable Entity", payload=server_response)

        with patch.object(zoodata, "get_api_key", return_value="test_key"), \
             patch.object(zoodata.urllib.request, "urlopen", side_effect=http_error), \
             patch.object(zoodata.time, "sleep"):
            result = zoodata.api_call("keywords/detail", {
                "keyword": "yoga mat",
                "date": "2026-07-29",
            })

        self.assertIs(result["success"], False)
        self.assertEqual(result["error"]["status"], 500)
        self.assertEqual(result["_transport"], {"status": 422})

    def test_structured_api_error_prints_full_json_before_nonzero_exit(self):
        error = {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Remove `lookbackDays` and set `granularity` to `week`.",
                "details": [{"field": "lookbackDays", "type": "extra_forbidden"}],
            },
            "meta": {"requestId": "req_test"},
            "_query": {
                "endpoint": "keywords/search-results",
                "params": {
                    "keyword": "yoga mat",
                    "date": "2026-07-23",
                    "granularity": "week",
                },
            },
        }
        stdout = io.StringIO()

        with patch.object(zoodata, "api_call", return_value=error), \
             patch.object(sys, "argv", [
                 "zoodata.py", "keyword-search-results",
                 "--keyword", "yoga mat", "--date", "2026-07-23",
             ]), \
             patch("sys.stdout", stdout), \
             self.assertRaises(SystemExit) as raised:
            zoodata.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(json.loads(stdout.getvalue()), error)

    def test_future_http_410_prints_migration_body_before_nonzero_exit(self):
        error = {
            "success": False,
            "error": {
                "code": "endpoint_gone",
                "message": "This endpoint has been retired. Use its replacement.",
                "details": {
                    "replacementMethod": "POST",
                    "replacementPath": "/openapi/v2/keywords/replacement-profile",
                    "supportedGranularity": ["week"],
                    "maxSubjects": 20,
                },
            },
            "_transport": {"status": 410},
            "_query": {
                "endpoint": "keywords/detail",
                "params": {"keyword": "yoga mat", "date": "2026-07-29"},
            },
        }
        stdout = io.StringIO()

        with patch.object(zoodata, "api_call", return_value=error), \
             patch.object(sys, "argv", [
                 "zoodata.py", "keyword-detail",
                 "--keyword", "yoga mat", "--date", "2026-07-29",
             ]), \
             patch("sys.stdout", stdout), \
             self.assertRaises(SystemExit) as raised:
            zoodata.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(json.loads(stdout.getvalue()), error)

    def test_non_keyword_command_prints_structured_error_before_nonzero_exit(self):
        error = {
            "success": False,
            "error": {
                "status": 500,
                "message": "HTTP 500 after 3 attempts",
                "action": "STOP_CURRENT_TURN. APPLY_SKILL_INTERFACE_FAILURE_TEMPLATE. "
                          "DO_NOT_SELECT_ANOTHER_COMMAND.",
                "retryExhausted": True,
            },
            "_transport": {"status": 500},
            "_query": {
                "endpoint": "markets/search",
                "params": {"categoryKeyword": "yoga mat"},
            },
        }
        stdout = io.StringIO()

        with patch.object(zoodata, "api_call", return_value=error), \
             patch.object(sys, "argv", [
                 "zoodata.py", "market", "--keyword", "yoga mat",
             ]), \
             patch("sys.stdout", stdout), \
             self.assertRaises(SystemExit) as raised:
            zoodata.main()

        self.assertEqual(raised.exception.code, 1)
        self.assertEqual(json.loads(stdout.getvalue()), error)

    def test_reviews_raw_surfaces_partial_pagination_failure(self):
        page_one = {
            "success": True,
            "data": {
                "reviews": [{"id": "R1", "rating": 5}],
                "nextCursor": "cursor-2",
            },
        }
        failure = {
            "success": False,
            "error": {
                "status": 500,
                "message": "HTTP 500 after 3 attempts",
                "action": "STOP_CURRENT_TURN. APPLY_SKILL_INTERFACE_FAILURE_TEMPLATE. "
                          "DO_NOT_SELECT_ANOTHER_COMMAND.",
                "retryExhausted": True,
            },
            "_transport": {"status": 500},
            "_query": {
                "endpoint": "realtime/reviews",
                "params": {
                    "asin": "B01CGLCGRA",
                    "marketplace": "US",
                    "cursor": "cursor-2",
                },
            },
        }
        captured = {}
        args = type("Args", (), {
            "asin": "B01CGLCGRA",
            "marketplace": "US",
            "max_pages": 10,
            "verbose": False,
        })()

        with patch.object(zoodata, "api_call", side_effect=[page_one, failure]), \
             patch.object(zoodata, "output", side_effect=lambda data, fmt="json": captured.update(data)):
            zoodata.cmd_reviews_raw(args)

        self.assertIs(captured["success"], False)
        self.assertEqual(captured["data"]["pages"], 1)
        self.assertEqual(captured["data"]["reviews"], page_one["data"]["reviews"])
        self.assertEqual(captured["error"], failure["error"])
        self.assertEqual(captured["_transport"], {"status": 500})
        self.assertEqual(captured["_failedQuery"], failure["_query"])

    def test_keyword_commands_reject_whitespace_only_required_subjects(self):
        cases = (
            ("keyword-detail", "--keyword", "   ", "--date", "2026-07-29"),
            ("keyword-extends", "--query", "   "),
            ("keyword-search-results", "--keyword", "   ", "--date", "2026-07-29"),
            ("keyword-product-traffic-terms", "--asin", "   ", "--date", "2026-07-29"),
            ("product-traffic-terms-profile", "--asin", "   ", "--date", "2026-07-29"),
            (
                "product-traffic-terms-timeline",
                "--asin", "   ",
                "--keyword", "yoga mat",
                "--date-from", "2026-07-01",
                "--date-to", "2026-07-29",
            ),
        )

        for argv in cases:
            with self.subTest(command=argv[0]), \
                 self.assertRaisesRegex(SystemExit, "non-empty value"):
                run_cli(*argv)


# ---------------------------------------------------------------------------
# 8. category param passed correctly to API
# ---------------------------------------------------------------------------
class TestCategoryParamPassing(unittest.TestCase):

    def test_comma_format_parsed_to_list(self):
        r = run_cli("market", "--category", "Pet Supplies,Dogs")
        self.assertEqual(r["params"]["categoryPath"], ["Pet Supplies", "Dogs"])

    def test_arrow_format_parsed_to_list(self):
        r = run_cli("market", "--category", "Pet Supplies > Dogs > Toys")
        self.assertEqual(r["params"]["categoryPath"], ["Pet Supplies", "Dogs", "Toys"])

    def test_keyword_goes_to_correct_key(self):
        r = run_cli("market", "--keyword", "yoga")
        self.assertIn("categoryKeyword", r["params"])
        self.assertEqual(r["params"]["categoryKeyword"], "yoga")


# ---------------------------------------------------------------------------
# 9. cmd_market_entry: categoryPath → keyword fallback (regression for #XX)
# ---------------------------------------------------------------------------
class TestMarketEntryCategoryFallback(unittest.TestCase):
    """cmd_market_entry must downgrade to keyword-only mode when a deep-leaf
    categoryPath returns no aggregation data from markets/search.

    Without this fallback, all 11 downstream endpoints inherit the dead
    categoryPath and return empty/HTTP 500 — the symptom Kimi 2.5 reported when
    asked to analyze a 5-level leaf like
    'Electronics > … > Over-Ear Headphones'.
    """

    DEEP_LEAF = "Electronics,Headphones,Earbuds & Accessories,Headphones & Earbuds,Over-Ear Headphones"

    def _run(self, market_when_categoryPath, market_when_categoryKeyword):
        """Run market-entry, returning the ordered list of (endpoint, params) calls."""
        calls = []
        # Endpoints whose response.data is a dict (others use list)
        dict_data_endpoints = {
            "products/brand-overview", "products/brand-detail",
            "products/price-band-overview", "products/price-band-detail",
            "reviews/analysis", "realtime/product", "realtime/reviews",
            "products/history",
        }

        def fake_api_call(endpoint, params):
            calls.append((endpoint, dict(params)))
            if endpoint == "markets/search":
                if "categoryPath" in params:
                    return market_when_categoryPath
                return market_when_categoryKeyword
            empty_data = {} if endpoint in dict_data_endpoints else []
            return {"success": True, "data": empty_data, "meta": {"total": 0},
                    "_query": {"endpoint": endpoint, "params": params}}

        argv = ["zoodata.py", "market-entry",
                "--keyword", "Over-Ear Headphones",
                "--category", self.DEEP_LEAF]
        with patch.object(zoodata, "api_call", side_effect=fake_api_call), \
             patch.object(zoodata, "output"), \
             patch.object(sys, "argv", argv):
            zoodata.main()
        return calls

    @staticmethod
    def _market_resp(empty=False):
        if empty:
            return {"success": True, "data": [], "meta": {"total": 0},
                    "_query": {"endpoint": "markets/search", "params": {}}}
        return {"success": True, "data": [{"asin": "B0EXAMPLE"}],
                "meta": {"total": 1234},
                "_query": {"endpoint": "markets/search", "params": {}}}

    def test_empty_categoryPath_triggers_keyword_retry(self):
        calls = self._run(self._market_resp(empty=True), self._market_resp())
        market_calls = [p for ep, p in calls if ep == "markets/search"]
        self.assertGreaterEqual(len(market_calls), 2,
            "Expected an initial categoryPath call followed by a keyword fallback retry")
        self.assertIn("categoryPath", market_calls[0])
        self.assertIn("categoryKeyword", market_calls[1])
        self.assertNotIn("categoryPath", market_calls[1])

    def test_subsequent_endpoints_drop_categoryPath_after_downgrade(self):
        calls = self._run(self._market_resp(empty=True), self._market_resp())
        # Skip the very first markets/search (which legitimately uses
        # categoryPath); every call after the downgrade must not carry it.
        seen_first_market = False
        for ep, p in calls:
            if ep == "markets/search" and not seen_first_market:
                seen_first_market = True
                continue
            self.assertNotIn("categoryPath", p,
                f"{ep} should not carry categoryPath after downgrade, got {p}")

    def test_nonempty_categoryPath_does_not_retry(self):
        calls = self._run(self._market_resp(), self._market_resp())
        market_calls = [p for ep, p in calls if ep == "markets/search"]
        self.assertEqual(len(market_calls), 1,
            "No fallback retry should fire when categoryPath returns data")
        self.assertIn("categoryPath", market_calls[0])

    def test_failed_categoryPath_call_also_triggers_retry(self):
        # success=False (HTTP 500-equivalent) should also trigger downgrade
        failed = {"success": False, "error": {"status": 500, "message": "boom"},
                  "_query": {"endpoint": "markets/search", "params": {}}}
        calls = self._run(failed, self._market_resp())
        market_calls = [p for ep, p in calls if ep == "markets/search"]
        self.assertGreaterEqual(len(market_calls), 2)
        self.assertIn("categoryKeyword", market_calls[1])


class TestCommandAllowlist(unittest.TestCase):
    """Per-skill command-allowlist enforcement. The shared CLI ships
    identically inside every skill bundle; an `allowed-commands.json`
    manifest next to the script scopes which subcommands the bundling skill
    may invoke. No manifest → full surface (canonical copy / zoodata
    reference skill). Malformed manifest → fail closed. A refusal emits
    valid structured JSON (success=false, error.status=COMMAND_NOT_ALLOWED,
    no terminal interface-failure action token) and exits 2, so the shared
    CLI contract classifies it as a documented non-terminal error, not a
    terminal interface failure."""

    MANIFEST = os.path.join(os.path.dirname(os.path.abspath(SCRIPT_PATH)),
                            "allowed-commands.json")

    def _enforce_capturing(self, command):
        import contextlib
        import io
        out, err = io.StringIO(), io.StringIO()
        code = None
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                zoodata._enforce_command_allowlist(command)
            except SystemExit as e:
                code = e.code
        return code, out.getvalue(), err.getvalue()

    def test_no_manifest_allows_full_surface(self):
        with patch("os.path.exists", return_value=False):
            self.assertIsNone(zoodata._load_command_allowlist())
            code, out, _err = self._enforce_capturing("products")
        self.assertIsNone(code)
        self.assertEqual(out, "")

    def test_manifest_allows_declared_command(self):
        manifest = '{"allowedCommands": ["market", "check"]}'
        with patch("os.path.exists", side_effect=lambda p: p == self.MANIFEST), \
             patch("builtins.open", mock_open(read_data=manifest)):
            code, out, _err = self._enforce_capturing("market")
        self.assertIsNone(code)
        self.assertEqual(out, "")

    def test_manifest_refuses_undeclared_command_with_structured_json(self):
        manifest = '{"allowedCommands": ["market", "check"]}'
        with patch("os.path.exists", side_effect=lambda p: p == self.MANIFEST), \
             patch("builtins.open", mock_open(read_data=manifest)):
            code, out, _err = self._enforce_capturing("products")
        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["status"], "COMMAND_NOT_ALLOWED")
        self.assertIn("products", payload["error"]["message"])
        self.assertIn("market", payload["error"]["message"])
        # Must NOT carry the terminal interface-failure action token —
        # the agent should pick a documented command, not stop the turn.
        self.assertNotIn("action", payload["error"])

    def test_malformed_manifest_fails_closed(self):
        for bad in ('{not json', '{"allowedCommands": []}',
                    '{"allowedCommands": "market"}', '{"other": 1}'):
            with self.subTest(bad=bad), \
                 patch("os.path.exists", side_effect=lambda p: p == self.MANIFEST), \
                 patch("builtins.open", mock_open(read_data=bad)):
                code, _out, err = self._enforce_capturing("market")
                self.assertEqual(code, 2)
                self.assertIn("allowed-commands.json", err)

    def test_help_is_exempt_from_enforcement(self):
        """`<cmd> --help` is documentation, not execution: it makes no API
        call, so it must stay available for every subcommand in every
        bundled copy (parser wellformedness remains verifiable everywhere).
        Enforcement gates only actual execution."""
        import subprocess
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        restricted_copy = os.path.join(
            repo_root, "amazon-market-trend-scanner", "scripts", "zoodata.py")
        # 'history' is outside the trend-scanner allowlist
        r = subprocess.run([sys.executable, restricted_copy, "history", "--help"],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("--asins", r.stdout)
        # ...but actually executing it is refused. Hermetic env: if the
        # refusal ever regresses, this degrades to a credential error
        # instead of a live API call from a developer machine.
        r = subprocess.run([sys.executable, restricted_copy, "history",
                            "--asins", "B0X", "--start-date", "2026-01-01",
                            "--end-date", "2026-01-02"],
                           capture_output=True, text=True, timeout=30,
                           env={"PATH": os.environ.get("PATH", ""),
                                "HOME": "/nonexistent"})
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["error"]["status"], "COMMAND_NOT_ALLOWED")

    def test_global_options_before_subcommand_cannot_bypass_enforcement(self):
        """Regression: cli-contract.md instructs 'Place global options before
        the subcommand', so `--format json <disallowed> ...` must be refused
        exactly like the bare form. The original hook only inspected argv[1]
        and let this canonical form straight through to the API. Run with a
        credential-free env so a failed refusal surfaces as a credential
        error (exit 1), never a live API call."""
        import subprocess
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        restricted_copy = os.path.join(
            repo_root, "amazon-market-trend-scanner", "scripts", "zoodata.py")
        hermetic = {"PATH": os.environ.get("PATH", ""), "HOME": "/nonexistent"}
        r = subprocess.run(
            [sys.executable, restricted_copy, "--format", "json", "history",
             "--asins", "B0X", "--start-date", "2026-01-01",
             "--end-date", "2026-01-02"],
            capture_output=True, text=True, timeout=30, env=hermetic)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["error"]["status"],
                         "COMMAND_NOT_ALLOWED")
        # A stray unknown argument must not demote the refusal to a usage
        # error: the command can never run here, so the refusal wins.
        r = subprocess.run(
            [sys.executable, restricted_copy, "--format", "json", "history",
             "--asins", "B0X", "--start-date", "2026-01-01",
             "--end-date", "2026-01-02", "--bogus"],
            capture_output=True, text=True, timeout=30, env=hermetic)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["error"]["status"],
                         "COMMAND_NOT_ALLOWED")

    def test_every_amazon_skill_ships_a_valid_manifest(self):
        """Repo-state guard: each amazon-* skill bundles a manifest matching
        the CLI's real subcommand surface; the zoodata data-layer reference
        skill deliberately ships none (full surface, per its SKILL.md)."""
        import glob
        import re
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        src = open(SCRIPT_PATH, encoding="utf-8").read()
        real_commands = set(re.findall(r"add_parser\(\s*[\"']([a-z0-9-]+)[\"']", src))
        skill_dirs = sorted(glob.glob(os.path.join(repo_root, "amazon-*")))
        self.assertGreater(len(skill_dirs), 5)
        for d in skill_dirs:
            manifest_path = os.path.join(d, "scripts", "allowed-commands.json")
            with self.subTest(skill=os.path.basename(d)):
                self.assertTrue(os.path.exists(manifest_path),
                                f"missing manifest: {manifest_path}")
                with open(manifest_path, encoding="utf-8") as f:
                    commands = json.load(f)["allowedCommands"]
                self.assertTrue(commands)
                self.assertIn("check", commands)
                self.assertEqual(len(commands), len(set(commands)))
                unknown = set(commands) - real_commands
                self.assertFalse(unknown, f"unknown subcommands: {unknown}")
        self.assertFalse(os.path.exists(os.path.join(
            repo_root, "zoodata", "scripts", "allowed-commands.json")))

    def test_manifests_match_skill_md_declarations(self):
        """Drift guard: each manifest is the ENFORCED copy of the command
        policy its SKILL.md owns — the two must stay in exact agreement.
        A narrower manifest breaks documented workflows (real incident:
        market-entry's routing-table commands were missing from its first
        manifest); a wider one silently un-enforces the declaration.

        Every skill declares its command set on exactly ONE declaration
        line — "This skill allows ..." (9 skills) or "The bundled manifest
        allows exactly ..." (keyword-traffic-analysis). Only that line is
        scanned, so ordinary prose edits elsewhere can never fire this
        test; when a route is added or removed, update the declaration
        line and the manifest together. (market-entry's endpoint→CLI
        routing table is separately pinned by
        tests/test_non_keyword_cli_routing.py.)
        """
        import glob
        import re
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        src = open(SCRIPT_PATH, encoding="utf-8").read()
        real = set(re.findall(r"add_parser\(\s*[\"']([a-z0-9-]+)[\"']", src))
        MARKERS = ("This skill allows", "The bundled manifest allows exactly")

        for d in sorted(glob.glob(os.path.join(repo_root, "amazon-*"))):
            name = os.path.basename(d)
            with open(os.path.join(d, "scripts", "allowed-commands.json"),
                      encoding="utf-8") as f:
                manifest = set(json.load(f)["allowedCommands"])
            skill = open(os.path.join(d, "SKILL.md"), encoding="utf-8").read()
            declaration_lines = [l for l in skill.splitlines()
                                 if any(m in l for m in MARKERS)]
            with self.subTest(skill=name):
                self.assertEqual(
                    len(declaration_lines), 1,
                    f"{name}: expected exactly one declaration line "
                    f"(markers: {MARKERS}), found {len(declaration_lines)}")
                declared = {t for t in
                            re.findall(r"`([a-z0-9-]+)`", declaration_lines[0])
                            if t in real}
                self.assertEqual(declared, manifest,
                                 f"{name}: declared-only={sorted(declared - manifest)} "
                                 f"manifest-only={sorted(manifest - declared)}")


class TestCredentialResolution(unittest.TestCase):
    """`_resolve_credential()` resolves the ZooData key from exactly two
    sources, in order: ZOODATA_API_KEY env, ~/.zoodata/config.json. The legacy
    APICLAW sources (APICLAW_API_KEY env, ~/.apiclaw/config.json) were removed:
    the CLI must not read any credential source beyond the two it declares.
    The in-bundle {skill_dir}/config.json fallback was removed for good: the
    skill directory ships inside the published bundle, so a key placed there
    would leak."""

    def _resolve_capturing_stderr(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            key = zoodata._resolve_credential()
        return key, buf.getvalue()

    def test_env_zoodata_takes_precedence(self):
        with patch.dict("os.environ", {"ZOODATA_API_KEY": "z"}, clear=True):
            self.assertEqual(zoodata._resolve_credential(), "z")

    def test_zoodata_env_wins_even_when_legacy_apiclaw_env_is_set(self):
        with patch.dict("os.environ",
                        {"ZOODATA_API_KEY": "new", "APICLAW_API_KEY": "old"},
                        clear=True):
            self.assertEqual(zoodata._resolve_credential(), "new")

    def test_zoodata_home_config_wins_even_when_legacy_apiclaw_env_is_set(self):
        home_zoodata = os.path.expanduser("~/.zoodata/config.json")
        with patch.dict("os.environ", {"APICLAW_API_KEY": "old"}, clear=True), \
             patch("os.path.exists", side_effect=lambda p: p == home_zoodata), \
             patch("builtins.open", mock_open(read_data='{"api_key":"new_home"}')):
            self.assertEqual(zoodata._resolve_credential(), "new_home")

    def test_legacy_apiclaw_env_is_not_a_source(self):
        """Regression: the deprecated APICLAW_API_KEY fallback was removed.
        A key present ONLY in the legacy env var must not resolve — the CLI
        reads no credential source beyond the two it declares."""
        with patch.dict("os.environ", {"APICLAW_API_KEY": "legacy"}, clear=True), \
             patch("os.path.exists", return_value=False):
            key, stderr = self._resolve_capturing_stderr()
        self.assertIsNone(key)
        self.assertEqual(stderr, "")

    def test_legacy_apiclaw_home_config_is_not_a_source(self):
        """Regression: the deprecated ~/.apiclaw/config.json fallback was
        removed. A key present ONLY in the legacy config file must not
        resolve, and the file must not even be opened."""
        apiclaw_home = os.path.expanduser("~/.apiclaw/config.json")
        opened = mock_open(read_data='{"api_key":"legacy_home"}')
        with patch.dict("os.environ", {}, clear=True), \
             patch("os.path.exists", side_effect=lambda p: p == apiclaw_home), \
             patch("builtins.open", opened):
            key, stderr = self._resolve_capturing_stderr()
        self.assertIsNone(key)
        self.assertEqual(stderr, "")
        for call in opened.call_args_list:
            self.assertNotIn(".apiclaw", str(call))

    def test_missing_key_guidance_creates_config_with_restrictive_permissions(self):
        """The setup hint printed when no key is configured must create
        ~/.zoodata/config.json without group/other access (umask 077 subshell
        + chmod 700 on the directory) — the key is a bearer credential and a
        world-readable file was a ClawHub scan finding."""
        import contextlib
        import io
        buf = io.StringIO()
        with patch.dict("os.environ", {}, clear=True), \
             patch("os.path.exists", return_value=False), \
             contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit):
                zoodata.get_api_key()
        guidance = buf.getvalue()
        self.assertIn("umask 077", guidance)
        self.assertIn("chmod 700 ~/.zoodata", guidance)

    def test_missing_key_guidance_flags_ignored_legacy_env_var(self):
        """A user whose environment still sets APICLAW_API_KEY gets a hard
        'not found' after the legacy removal — the guidance must tell them,
        in-band, that the variable is set but no longer read, so they don't
        need the CHANGELOG to connect the dots. No hint when it isn't set."""
        import contextlib
        import io

        def _guidance(env):
            buf = io.StringIO()
            with patch.dict("os.environ", env, clear=True), \
                 patch("os.path.exists", return_value=False), \
                 contextlib.redirect_stderr(buf):
                with self.assertRaises(SystemExit):
                    zoodata.get_api_key()
            return buf.getvalue()

        with_legacy = _guidance({"APICLAW_API_KEY": "legacy"})
        self.assertIn("APICLAW_API_KEY is set but no longer read", with_legacy)
        self.assertIn("ZOODATA_API_KEY", with_legacy)
        without_legacy = _guidance({})
        self.assertNotIn("no longer read", without_legacy)

    def test_no_skill_doc_advertises_legacy_apiclaw_sources(self):
        """Doc-layer regression guard: the legacy APICLAW credential sources
        were removed from the CLIs, so no published skill document may
        advertise them again. Scans every SKILL.md and README.md in the repo
        (all ship inside published bundles); CHANGELOG history and CLI
        docstrings that explain the removal are intentionally out of scope."""
        repo_root = os.path.join(os.path.dirname(__file__), "..")
        scanned = []
        offenders = []
        for dirpath, dirnames, filenames in os.walk(repo_root):
            # Prune hidden dirs (.git, gitignored local snapshots like
            # .agents/) and tooling dirs — only tracked skill docs matter.
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".")
                           and d not in ("node_modules", "__pycache__")]
            for name in filenames:
                if name in ("SKILL.md", "README.md"):
                    path = os.path.join(dirpath, name)
                    scanned.append(path)
                    with open(path, "r", encoding="utf-8") as f:
                        if "apiclaw" in f.read().lower():
                            offenders.append(os.path.relpath(path, repo_root))
        self.assertGreater(len(scanned), 10)  # guard against vacuous pass
        self.assertEqual(offenders, [])

    def test_skill_dir_config_is_not_a_source(self):
        """The in-bundle {skill_dir}/config.json fallback was removed so a
        committed key can never ship inside the published skill. Only
        ~/.zoodata/config.json is consulted; a config.json anywhere else
        (e.g. next to scripts/) is ignored even when it exists."""
        home_zoodata = os.path.expanduser("~/.zoodata/config.json")
        apiclaw_home = os.path.expanduser("~/.apiclaw/config.json")
        # Neither home config exists; only a config.json sitting elsewhere
        # (e.g. next to scripts/, the removed fallback) would "exist".
        with patch.dict("os.environ", {}, clear=True), \
             patch("os.path.exists", side_effect=lambda p: p not in (home_zoodata, apiclaw_home)), \
             patch("builtins.open", mock_open(read_data='{"api_key":"bundled"}')):
            self.assertIsNone(zoodata._resolve_credential())

    def test_user_home_config_works_when_no_env(self):
        """The regression: before the fix, real API calls didn't look here
        even though `check` did, so a key written ONLY to ~/.zoodata/config.json
        produced false-green check + hard-fail calls."""
        home_zoodata = os.path.expanduser("~/.zoodata/config.json")
        with patch.dict("os.environ", {}, clear=True), \
             patch("os.path.exists", side_effect=lambda p: p == home_zoodata), \
             patch("builtins.open", mock_open(read_data='{"api_key":"home_key"}')):
            self.assertEqual(zoodata._resolve_credential(), "home_key")

    def test_returns_none_when_nothing_configured(self):
        with patch.dict("os.environ", {}, clear=True), \
             patch("os.path.exists", return_value=False):
            self.assertIsNone(zoodata._resolve_credential())

    def test_explicit_null_api_key_does_not_crash(self):
        """A config with `{"api_key": null}` must return None, not crash on
        None.strip()."""
        home_zoodata = os.path.expanduser("~/.zoodata/config.json")
        with patch.dict("os.environ", {}, clear=True), \
             patch("os.path.exists", side_effect=lambda p: p == home_zoodata), \
             patch("builtins.open", mock_open(read_data='{"api_key": null}')):
            self.assertIsNone(zoodata._resolve_credential())


class TestBaseUrlResolution(unittest.TestCase):
    def test_default_base_url_points_to_openapi_v2(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                zoodata._resolve_base_url(),
                "https://api.zoodata.ai/openapi/v2",
            )

    def test_env_base_url_appends_openapi_v2_for_bare_host(self):
        with patch.dict("os.environ", {"ZOODATA_BASE_URL": "http://localhost:8080"}, clear=True):
            self.assertEqual(
                zoodata._resolve_base_url(),
                "http://localhost:8080/openapi/v2",
            )

    def test_env_base_url_preserves_explicit_openapi_v2_path(self):
        with patch.dict(
            "os.environ",
            {"ZOODATA_BASE_URL": "http://localhost:8080/openapi/v2/"},
            clear=True,
        ):
            self.assertEqual(
                zoodata._resolve_base_url(),
                "http://localhost:8080/openapi/v2",
            )

    def _stderr_of_resolve(self, env):
        import contextlib
        import io
        buf = io.StringIO()
        with patch.dict("os.environ", env, clear=True), \
             contextlib.redirect_stderr(buf):
            zoodata._resolve_base_url()
        return buf.getvalue()

    def test_untrusted_host_warns_key_is_withheld(self):
        stderr = self._stderr_of_resolve({"ZOODATA_BASE_URL": "https://evil.example.com"})
        self.assertIn("WARNING", stderr)
        self.assertIn("evil.example.com", stderr)
        self.assertIn("Bearer", stderr)
        self.assertIn("NOT be sent", stderr)

    def test_default_host_is_silent(self):
        self.assertEqual(self._stderr_of_resolve({}), "")

    def test_zoodata_subdomain_is_trusted_and_silent(self):
        stderr = self._stderr_of_resolve({"ZOODATA_BASE_URL": "https://staging.zoodata.ai"})
        self.assertEqual(stderr, "")

    def test_localhost_is_trusted_and_silent(self):
        stderr = self._stderr_of_resolve({"ZOODATA_BASE_URL": "http://localhost:8080"})
        self.assertEqual(stderr, "")

    def test_is_trusted_host_accepts_zoodata_and_localhost(self):
        for url in ("https://api.zoodata.ai/openapi/v2",
                    "https://staging.zoodata.ai",
                    "https://zoodata.ai",
                    "http://localhost:8080",
                    "http://127.0.0.1:9000"):
            self.assertTrue(zoodata._is_trusted_host(url), url)

    def test_is_trusted_host_rejects_arbitrary_and_spoofed_hosts(self):
        # Bearer token must never go to these — note the subdomain-spoof cases.
        for url in ("https://evil.example.com",
                    "https://zoodata.ai.evil.com",
                    "https://notzoodata.ai"):
            self.assertFalse(zoodata._is_trusted_host(url), url)

    def test_api_call_refuses_untrusted_host_before_sending_key(self):
        """When the base URL is untrusted, api_call must sys.exit(1) BEFORE
        resolving/sending the key — the Bearer token is withheld, not just warned."""
        import contextlib
        import io
        buf = io.StringIO()
        with patch.object(zoodata, "BASE_URL_TRUSTED", False), \
             patch.object(zoodata, "get_api_key") as get_key, \
             contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit):
                zoodata.api_call("categories", {})
        get_key.assert_not_called()  # key resolution never reached
        self.assertIn("refusing", buf.getvalue())


class TestCheckCommand(unittest.TestCase):
    def test_check_defaults_to_credentials_only_without_api_call(self):
        captured = {}

        def fake_output(data, fmt="json"):
            captured.update(data)

        args = type("Args", (), {
            "format": "json",
            "endpoints": False,
            "keyword_endpoints": False,
        })()

        with patch.object(zoodata, "_resolve_credential", return_value="test_key"), \
             patch.object(zoodata, "api_call") as api_call, \
             patch.object(zoodata, "output", side_effect=fake_output):
            zoodata.cmd_check(args)

        api_call.assert_not_called()
        self.assertEqual(captured["check"], "credentials_only")
        self.assertEqual(captured["endpoint_probes"], "skipped")

    def test_check_marks_structured_api_failure_as_failed_when_probing_endpoints(self):
        error = {
            "success": False,
            "error": {"message": "Request failed"},
            "_query": {"endpoint": "categories", "params": {}},
        }
        captured = {}

        def fake_output(data, fmt="json"):
            captured.update(data)

        args = type("Args", (), {
            "format": "json",
            "endpoints": True,
            "keyword_endpoints": False,
        })()

        with patch.object(zoodata, "_resolve_credential", return_value="test_key"), \
             patch.object(zoodata, "api_call", return_value=error), \
             patch.object(zoodata, "output", side_effect=fake_output):
            zoodata.cmd_check(args)

        self.assertEqual(captured["endpoints"]["categories"]["status"], "failed")

    def test_keyword_check_does_not_interpret_account_statuses(self):
        captured = {}

        def fake_output(data, fmt="json"):
            captured.update(data)

        args = type("Args", (), {
            "format": "json",
            "endpoints": False,
            "keyword_endpoints": True,
            "keyword": "yoga mat",
            "date": "2026-06-29",
            "asin": "B01CGLCGRA",
        })()

        for status in (401, 402):
            error = {
                "success": False,
                "error": {"status": status, "message": "terminal account failure"},
                "_transport": {"status": status},
            }
            captured.clear()
            with self.subTest(status=status), \
                 patch.object(zoodata, "_resolve_credential", return_value="test_key"), \
                 patch.object(zoodata, "api_call", return_value=error) as api_call, \
                 patch.object(zoodata, "output", side_effect=fake_output):
                zoodata.cmd_check(args)

            self.assertGreater(api_call.call_count, 1)
            self.assertEqual(api_call.call_count, len(captured["endpoints"]))
            self.assertEqual(
                captured["endpoints"]["keywords/detail"]["status"],
                "failed",
            )
            self.assertTrue(all(
                result["status"] == "failed"
                for result in captured["endpoints"].values()
            ))

    def test_keyword_check_includes_published_profile_endpoints_on_all_hosts(self):
        args = type("Args", (), {
            "format": "json",
            "endpoints": False,
            "keyword_endpoints": True,
            "keyword": "yoga mat",
            "date": "2026-06-29",
            "asin": None,
        })()

        for base_url in [
            "http://localhost:8080/openapi/v2",
            "https://api.zoodata.ai/openapi/v2",
        ]:
            calls = []

            def fake_api_call(endpoint, params):
                calls.append(endpoint)
                return {"success": True, "data": [], "meta": {}}

            with patch.object(zoodata, "BASE_URL", base_url), \
                 patch.object(zoodata, "_resolve_credential", return_value="test_key"), \
                 patch.object(zoodata, "api_call", side_effect=fake_api_call), \
                 patch.object(zoodata, "output"):
                zoodata.cmd_check(args)

            self.assertIn("keywords/market-profile", calls)
            self.assertIn("keywords/trend-profile", calls)

    def test_keyword_check_uses_product_traffic_terms_profile_for_asin_probe(self):
        args = type("Args", (), {
            "format": "json",
            "endpoints": False,
            "keyword_endpoints": True,
            "keyword": "yoga mat",
            "date": "2026-06-29",
            "asin": "B01CGLCGRA",
        })()
        calls = []

        def fake_api_call(endpoint, params):
            calls.append((endpoint, params))
            return {"success": True, "data": [], "meta": {}}

        with patch.object(zoodata, "_resolve_credential", return_value="test_key"), \
             patch.object(zoodata, "api_call", side_effect=fake_api_call), \
             patch.object(zoodata, "output"):
            zoodata.cmd_check(args)

        endpoints = [endpoint for endpoint, _ in calls]
        self.assertIn("keywords/product-traffic-terms-profile", endpoints)
        profile_params = next(
            params for endpoint, params in calls
            if endpoint == "keywords/product-traffic-terms-profile"
        )
        self.assertEqual(profile_params["asin"], "B01CGLCGRA")
        self.assertEqual(profile_params["granularity"], "week")


class TestCategoriesMarketplace(unittest.TestCase):
    """The categories subcommand used to reject --marketplace even though every
    other marketplace-aware subcommand accepted it."""

    def test_categories_accepts_marketplace_flag(self):
        r = run_cli("categories", "--keyword", "x", "--marketplace", "UK")
        self.assertEqual(r["endpoint"], "categories")
        self.assertEqual(r["params"]["marketplace"], "UK")

    def test_categories_marketplace_defaults_to_us(self):
        r = run_cli("categories", "--keyword", "x")
        self.assertEqual(r["params"]["marketplace"], "US")


# ---------------------------------------------------------------------------
class TestCreditAggregation(unittest.TestCase):
    """Composite commands fan out to many endpoints; the run's total credit
    consumption must be summed and stamped onto the top-level meta."""

    def _reset(self):
        zoodata._CREDITS.consumed = 0.0
        zoodata._CREDITS.consumed_exact = 0.0
        zoodata._CREDITS.remaining = None
        zoodata._CREDITS.remaining_exact = None
        zoodata._CREDITS.calls = 0

    setUp = _reset
    tearDown = _reset  # avoid leaking accumulated state to other test classes

    def test_tracker_sums_display_and_exact_separately(self):
        t = zoodata._CreditTracker()
        t.record({"creditsConsumed": 1, "creditsRemaining": 100})
        t.record({"creditsConsumedExact": 2.0, "creditsRemainingExact": 98.0})
        self.assertEqual(t.consumed, 3.0)         # 1 + (fallback 2.0)
        self.assertEqual(t.consumed_exact, 3.0)   # (fallback 1) + 2.0
        self.assertEqual(t.remaining, 100)        # last display remaining
        self.assertEqual(t.remaining_exact, 98.0)
        self.assertEqual(t.calls, 2)

    def test_tracker_ignores_non_dict_and_missing_fields(self):
        t = zoodata._CreditTracker()
        t.record(None)
        t.record({})
        t.record({"foo": 1})
        self.assertEqual(t.calls, 0)
        self.assertEqual(t.consumed, 0.0)

    def test_annotate_stamps_composite_total_onto_meta(self):
        for rem in (500, 499, 498):  # three internal calls, 1 credit each
            zoodata._CREDITS.record({"creditsConsumed": 1, "creditsRemaining": rem})
        payload = {"meta": {"keyword": "x", "steps_completed": []}, "market": {}}
        zoodata._annotate_credits(payload)
        self.assertEqual(payload["meta"]["creditsConsumed"], 3)
        self.assertEqual(payload["meta"]["creditsRemaining"], 498)
        self.assertEqual(payload["meta"]["apiCalls"], 3)

    def test_annotate_preserves_single_call_display_value(self):
        # A single call whose display credit (1) differs from exact (0.5) must
        # keep BOTH — annotate must not overwrite the rounded display with exact.
        zoodata._CREDITS.record({"creditsConsumed": 1, "creditsConsumedExact": 0.5,
                                 "creditsRemaining": 9})
        payload = {"meta": {"foo": "bar"}}
        zoodata._annotate_credits(payload)
        self.assertEqual(payload["meta"]["creditsConsumed"], 1)
        self.assertEqual(payload["meta"]["creditsConsumedExact"], 0.5)

    def test_annotate_synthesises_meta_when_absent(self):
        # reviews-raw and similar emit no top-level meta; the total must still
        # be surfaced, not silently dropped.
        zoodata._CREDITS.record({"creditsConsumed": 1, "creditsRemaining": 9})
        zoodata._CREDITS.record({"creditsConsumed": 1, "creditsRemaining": 8})
        payload = {"success": True, "data": {}}  # no meta
        zoodata._annotate_credits(payload)
        self.assertIn("meta", payload)
        self.assertEqual(payload["meta"]["creditsConsumed"], 2)
        self.assertEqual(payload["meta"]["apiCalls"], 2)

    def test_annotate_is_noop_without_api_calls(self):
        payload = {"meta": {"keyword": "x"}}
        zoodata._annotate_credits(payload)  # calls == 0
        self.assertNotIn("creditsConsumed", payload["meta"])


class TestCompositeRobustness(unittest.TestCase):
    """Composite fail-fast + scope guards (fixes for keyword->category self-heal,
    terminal-failure abort, and listing-audit empty-target)."""

    def _run(self, argv, router):
        """Run a composite with a per-endpoint api_call router.
        Returns (calls, results) where calls is a list of (endpoint, params)
        actually sent to api_call, and results is what output() received."""
        calls = []
        captured = {}

        def fake_api_call(endpoint, params):
            calls.append((endpoint, dict(params)))
            resp = dict(router(endpoint, dict(params), calls))
            resp.setdefault("_query", {"endpoint": endpoint, "params": params})
            return resp

        def fake_output(data, fmt="json"):
            captured["results"] = data

        with patch.object(zoodata, "api_call", side_effect=fake_api_call), \
             patch.object(zoodata, "output", side_effect=fake_output), \
             patch.object(sys, "argv", ["zoodata.py", *argv]):
            try:
                zoodata.main()
            except SystemExit:
                pass
        return calls, captured.get("results", {})

    # --- Fix: listing-audit empty-target guard ---
    def test_listing_audit_empty_target_is_not_auditable(self):
        def router(endpoint, params, calls):
            if endpoint == "realtime/product":
                return {"success": True, "data": {"asin": ""}}   # empty target
            return {"success": True, "data": []}
        calls, results = self._run(["listing-audit", "--my-asin", "B00EMPTY000"], router)
        self.assertEqual(results.get("meta", {}).get("target_status"), "empty")
        self.assertEqual(results.get("meta", {}).get("audit_status"), "not_auditable")
        # must NOT have issued an unfiltered products/search (no keyword, no categoryPath)
        for ep, p in calls:
            if ep == "products/search":
                self.assertTrue(p.get("keyword") or p.get("categoryPath"),
                                f"unfiltered products/search issued: {p}")

    def test_listing_audit_valid_target_proceeds(self):
        def router(endpoint, params, calls):
            if endpoint == "realtime/product":
                return {"success": True, "data": {"asin": params.get("asin"),
                        "categoryPath": ["Sports & Outdoors", "Yoga", "Mats"]}}
            return {"success": True, "data": []}
        calls, results = self._run(["listing-audit", "--my-asin", "B08373YJTB"], router)
        self.assertEqual(results.get("meta", {}).get("target_status"), "ok")
        self.assertNotEqual(results.get("meta", {}).get("audit_status"), "not_auditable")

    def test_has_scope_helper(self):
        self.assertFalse(zoodata._has_scope(None, None))
        self.assertTrue(zoodata._has_scope("yoga mat", None))
        self.assertTrue(zoodata._has_scope(None, ["A", "B"]))

    # --- Fix: report/opportunity self-heal category for a product keyword ---
    def test_report_self_heals_category_for_product_keyword(self):
        def router(endpoint, params, calls):
            if endpoint == "categories":
                return {"success": True, "data": []}            # no direct category match
            if endpoint == "products/search":
                # real products/search rows carry categoryPath — resolution reads it directly
                return {"success": True, "data": [{"asin": "B0PROBE001",
                        "categoryPath": ["Sports & Outdoors", "Yoga", "Mats"]}]}
            if endpoint == "markets/search":
                return {"success": True, "data": [{"totalSkuCount": 100}]}
            return {"success": True, "data": []}
        calls, results = self._run(["report", "--keyword", "yoga mat"], router)
        market_calls = [p for ep, p in calls if ep == "markets/search"]
        self.assertTrue(market_calls, "markets/search was not called")
        # self-heal: market must be scoped by the resolved categoryPath, not categoryKeyword
        self.assertEqual(market_calls[0].get("categoryPath"),
                         ["Sports & Outdoors", "Yoga", "Mats"])
        self.assertNotIn("categoryKeyword", market_calls[0])

    # --- Fix: terminal failure aborts composite fan-out ---
    def test_is_terminal_failure_helper(self):
        self.assertTrue(zoodata._is_terminal_failure(
            {"success": False, "error": {"retryExhausted": True}}))
        self.assertFalse(zoodata._is_terminal_failure(
            {"success": False, "error": {"code": "EMPTY"}}))
        self.assertFalse(zoodata._is_terminal_failure({"success": True, "data": []}))

    def test_composite_aborts_after_terminal_failure(self):
        def router(endpoint, params, calls):
            # first call resolves category; the next real call is a terminal failure
            if len(calls) >= 2:
                return {"success": False, "error": {
                    "code": "HTTP_503", "message": "unavailable", "retryExhausted": True}}
            return {"success": True, "data": [{"categoryPath": ["Sports", "Yoga"]}]}
        calls, results = self._run(["market-entry", "--keyword", "yoga mat"], router)
        self.assertTrue(results.get("meta", {}).get("aborted"),
                        "composite did not set aborted flag after terminal failure")
        # a full market-entry issues 20+ calls; abort must bound real network calls
        self.assertLess(len(calls), 10,
                        f"composite kept calling after terminal failure: {len(calls)} calls")

    def test_composite_does_NOT_abort_on_business_failure(self):
        """Safety property: a per-endpoint business failure WITHOUT retryExhausted
        (404/422/empty-but-success) must NOT abort the whole composite."""
        def router(endpoint, params, calls):
            if endpoint == "categories":
                return {"success": True, "data": [{"categoryPath": ["Sports", "Yoga"]}]}
            if endpoint == "markets/search":
                # non-terminal business failure mid fan-out — must be tolerated, not abort
                return {"success": False, "error": {"code": "HTTP_422", "message": "validation"}}
            return {"success": True, "data": []}
        calls, results = self._run(["market-entry", "--keyword", "yoga mat"], router)
        self.assertFalse(results.get("meta", {}).get("aborted"),
                         "composite wrongly aborted on a non-terminal business failure")
        # composite must have continued PAST the failing markets/search to other endpoints
        endpoints = {ep for ep, _ in calls}
        self.assertTrue(endpoints - {"categories", "markets/search"},
                        f"composite stopped after the non-terminal failure; only hit {endpoints}")

    def test_listing_audit_empty_target_null_data(self):
        """Empty target detected regardless of realtime data shape (None / list)."""
        for empty in (None, []):
            def router(endpoint, params, calls, _e=empty):
                if endpoint == "realtime/product":
                    return {"success": True, "data": _e}
                return {"success": True, "data": []}
            calls, results = self._run(["listing-audit", "--my-asin", "B00X"], router)
            self.assertEqual(results.get("meta", {}).get("audit_status"),
                             "not_auditable", f"data={empty!r} not treated as empty target")

    # --- realtime empty-retry + offline fallback ---
    def test_is_empty_realtime_helper(self):
        self.assertTrue(zoodata._is_empty_realtime({"success": True, "data": {"asin": ""}}))
        self.assertTrue(zoodata._is_empty_realtime({"success": True, "data": {}}))
        self.assertFalse(zoodata._is_empty_realtime({"success": True, "data": {"asin": "B01"}}))
        self.assertFalse(zoodata._is_empty_realtime({"success": True, "data": []}))
        self.assertFalse(zoodata._is_empty_realtime({"success": False, "data": None}))

    def test_fetch_realtime_retries_transient_empty_then_succeeds(self):
        seq = [
            {"success": True, "data": {"asin": ""}},
            {"success": True, "data": {"asin": ""}},
            {"success": True, "data": {"asin": "B01", "categoryPath": ["A"]}},
        ]
        state = {"n": 0}
        def caller(ep, params, label=None):
            r = seq[state["n"]]; state["n"] += 1; return r
        r = zoodata._fetch_realtime(caller, "B01")
        self.assertEqual(state["n"], 3)               # retried until data arrived
        self.assertEqual(r["data"]["asin"], "B01")
        self.assertNotIn("_realtimeStatus", r)        # succeeded → no fallback mark

    def test_fetch_realtime_gives_up_after_attempts(self):
        state = {"n": 0}
        def caller(ep, params, label=None):
            state["n"] += 1
            return {"success": True, "data": {"asin": ""}}
        r = zoodata._fetch_realtime(caller, "B01")
        self.assertEqual(state["n"], zoodata.REALTIME_EMPTY_RETRIES)   # bounded, not infinite
        self.assertEqual(r.get("_realtimeStatus"), "empty_after_retries")

    def test_fetch_realtime_does_not_retry_terminal_failure(self):
        state = {"n": 0}
        def caller(ep, params, label=None):
            state["n"] += 1
            return {"success": False, "error": {"retryExhausted": True}}
        zoodata._fetch_realtime(caller, "B01")
        self.assertEqual(state["n"], 1)               # terminal → hand off to ②, no retry

    def test_report_category_resolves_from_products_not_realtime_probe(self):
        def router(endpoint, params, calls):
            if endpoint == "categories":
                return {"success": True, "data": []}
            if endpoint == "products/search":
                return {"success": True, "data": [{"asin": "B01",
                        "categoryPath": ["Sports & Outdoors", "Yoga", "Mats"]}]}
            if endpoint == "markets/search":
                return {"success": True, "data": [{"totalSkuCount": 1}]}
            return {"success": True, "data": []}   # realtime (Step 4 detail) returns no category
        calls, results = self._run(["report", "--keyword", "yoga mat"], router)
        self.assertEqual(results.get("meta", {}).get("category_source"), "inferred_from_search")
        market = [p for ep, p in calls if ep == "markets/search"]
        self.assertEqual(market[0].get("categoryPath"), ["Sports & Outdoors", "Yoga", "Mats"])

    def test_resolve_category_never_calls_realtime(self):
        """Category resolution reads categoryPath from the products/search row and
        must NOT fall back to a flaky realtime probe."""
        eps = []
        def caller(endpoint, params, label=None):
            eps.append(endpoint)
            if endpoint == "categories":
                return {"success": True, "data": []}
            if endpoint == "products/search":
                return {"success": True, "data": [{"asin": "B01", "categoryPath": ["A", "B", "C"]}]}
            return {"success": True, "data": []}
        cp, src = zoodata._resolve_category(caller, lambda m: None, keyword="yoga mat")
        self.assertEqual(cp, ["A", "B", "C"])
        self.assertEqual(src, "inferred_from_search")
        self.assertNotIn("realtime/product", eps)

    def test_resolve_category_bsr_fallback_still_no_realtime(self):
        """If categoryPath is absent, fall back to bsrCategory — still no realtime."""
        eps = []
        def caller(endpoint, params, label=None):
            eps.append(endpoint)
            if endpoint == "products/search":
                return {"success": True, "data": [{"asin": "B01", "bsrCategory": "Yoga Mats"}]}
            if endpoint == "categories":
                return {"success": True, "data": [{"categoryPath": ["Sports", "Yoga", "Mats"]}]}
            return {"success": True, "data": []}
        cp, src = zoodata._resolve_category(caller, lambda m: None, keyword="yoga mat")
        self.assertEqual(cp, ["Sports", "Yoga", "Mats"])
        self.assertNotIn("realtime/product", eps)

    def test_composite_sets_offline_fallback_hint_when_realtime_stays_empty(self):
        def router(endpoint, params, calls):
            if endpoint == "realtime/product":
                return {"success": True, "data": {"asin": ""}}      # always transient-empty
            if endpoint in ("categories", "products/search"):
                return {"success": True, "data": [{"asin": "B01", "categoryPath": ["A", "B"]}]}
            return {"success": True, "data": []}
        calls, results = self._run(["opportunity", "--keyword", "yoga mat"], router)
        meta = results.get("meta", {})
        self.assertIn("realtimeFallbackHint", meta)
        self.assertGreaterEqual(meta.get("realtimeUnavailable", 0), 1)
        rt_calls = [ep for ep, _ in calls if ep == "realtime/product"]
        self.assertGreaterEqual(len(rt_calls), zoodata.REALTIME_EMPTY_RETRIES)  # did retry

    def test_product_command_retries_and_sets_fallback(self):
        """Granular `product` retries transient-empty realtime and, if still empty,
        stamps the offline-fallback hint on meta (parity with composites / Quick Check)."""
        def router(endpoint, params, calls):
            return {"success": True, "data": {"asin": ""}, "meta": {"creditsConsumed": 1}}
        calls, result = self._run(["product", "--asin", "B0DEAD0000"], router)
        rt_calls = [ep for ep, _ in calls if ep == "realtime/product"]
        self.assertEqual(len(rt_calls), zoodata.REALTIME_EMPTY_RETRIES)   # retried, not single-shot
        self.assertEqual(result.get("_realtimeStatus"), "empty_after_retries")
        self.assertIn("realtimeFallbackHint", result.get("meta", {}))

    def test_product_command_success_no_retry_no_fallback(self):
        def router(endpoint, params, calls):
            return {"success": True, "data": {"asin": params["asin"], "title": "X"},
                    "meta": {"creditsConsumed": 1}}
        calls, result = self._run(["product", "--asin", "B01LP0U5X0"], router)
        rt_calls = [ep for ep, _ in calls if ep == "realtime/product"]
        self.assertEqual(len(rt_calls), 1)                    # data present → no retry
        self.assertNotIn("realtimeFallbackHint", result.get("meta", {}))


# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

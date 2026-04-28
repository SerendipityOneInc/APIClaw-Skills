"""
Test suite for apiclaw/scripts/apiclaw.py

Coverage:
  - parse_category: all supported separators and edge cases
  - PRODUCT_MODES: all 14 modes accepted without error
  - argparse: all subcommands have valid --help; allow_abbrev=False regression
  - param construction: each subcommand passes the right keys to api_call
  - output format: json and compact both produce valid JSON
  - page / page-size: not overwritten by prefix matching (regression for #48)

Run from repo root:
    python tests/test_apiclaw.py
    python -m pytest tests/test_apiclaw.py -v
"""

import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Load module under test
# ---------------------------------------------------------------------------
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "apiclaw", "scripts", "apiclaw.py")

spec = importlib.util.spec_from_file_location("apiclaw", SCRIPT_PATH)
apiclaw = importlib.util.module_from_spec(spec)
with patch.dict("os.environ", {"APICLAW_API_KEY": "test_key"}):
    spec.loader.exec_module(apiclaw)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
MOCK_OK = {"success": True, "data": [], "_query": {"endpoint": "", "params": {}}}


def run_cli(*argv):
    """Run apiclaw.main() with mocked api_call; return (endpoint, params)."""
    captured = {}

    def fake_api_call(endpoint, params):
        captured["endpoint"] = endpoint
        captured["params"] = dict(params)
        return {**MOCK_OK, "_query": {"endpoint": endpoint, "params": params}}

    with patch.object(apiclaw, "api_call", side_effect=fake_api_call), \
         patch.object(apiclaw, "output"), \
         patch.object(sys, "argv", ["apiclaw.py", *argv]):
        apiclaw.main()

    return captured


def run_cli_stdout(fmt, subcmd, *args):
    """Run apiclaw.main() with real output(); return stdout as string.

    --format must precede the subcommand (it's a root-level arg).
    """
    import io

    def fake_api_call(endpoint, params):
        return {**MOCK_OK, "_query": {"endpoint": endpoint, "params": params}}

    buf = io.StringIO()
    argv = ["apiclaw.py", "--format", fmt, subcmd, *args]
    with patch.object(apiclaw, "api_call", side_effect=fake_api_call), \
         patch.object(sys, "argv", argv), \
         patch("sys.stdout", buf):
        apiclaw.main()

    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. parse_category
# ---------------------------------------------------------------------------
class TestParseCategory(unittest.TestCase):

    def test_comma_separated(self):
        self.assertEqual(apiclaw.parse_category("Pet Supplies,Dogs,Toys"),
                         ["Pet Supplies", "Dogs", "Toys"])

    def test_spaced_arrow(self):
        self.assertEqual(apiclaw.parse_category("Pet Supplies > Dogs > Toys"),
                         ["Pet Supplies", "Dogs", "Toys"])

    def test_bare_arrow(self):
        self.assertEqual(apiclaw.parse_category("Pet Supplies>Dogs>Toys"),
                         ["Pet Supplies", "Dogs", "Toys"])

    def test_bare_arrow_with_spaces_in_name(self):
        self.assertEqual(apiclaw.parse_category("Home & Kitchen>Storage & Organization"),
                         ["Home & Kitchen", "Storage & Organization"])

    def test_single_segment(self):
        self.assertEqual(apiclaw.parse_category("Electronics"), ["Electronics"])

    def test_empty_string(self):
        self.assertEqual(apiclaw.parse_category(""), [])

    def test_spaced_arrow_takes_priority_over_bare(self):
        # " > " is checked before ">", so "A > B>C" splits on " > " first
        result = apiclaw.parse_category("A > B>C")
        self.assertEqual(result, ["A", "B>C"])

    def test_strips_whitespace(self):
        self.assertEqual(apiclaw.parse_category("  Pet Supplies , Dogs "),
                         ["Pet Supplies", "Dogs"])


# ---------------------------------------------------------------------------
# 2. PRODUCT_MODES completeness
# ---------------------------------------------------------------------------
class TestProductModes(unittest.TestCase):

    def test_all_13_modes_defined(self):
        self.assertEqual(len(apiclaw.PRODUCT_MODES), 13)

    def test_all_modes_accepted_by_cli(self):
        """Every mode name must be accepted by 'products --mode <name>' without sys.exit."""
        for mode in apiclaw.PRODUCT_MODES:
            with self.subTest(mode=mode):
                # Should not raise or call sys.exit
                result = run_cli("products", "--keyword", "test", "--mode", mode)
                self.assertIn("endpoint", result)

    def test_unknown_mode_exits(self):
        with patch.object(apiclaw, "api_call", return_value=MOCK_OK), \
             patch.object(apiclaw, "output"), \
             patch.object(sys, "argv", ["apiclaw.py", "products", "--keyword", "test",
                                        "--mode", "nonexistent-mode"]), \
             self.assertRaises(SystemExit) as cm:
            apiclaw.main()
        self.assertNotEqual(cm.exception.code, 0)


# ---------------------------------------------------------------------------
# 3. --help for every subcommand (argparse definition sanity)
# ---------------------------------------------------------------------------
SUBCOMMANDS = [
    "categories", "market", "products", "competitors", "product",
    "report", "opportunity", "market-entry", "competitor-analysis",
    "pricing-analysis", "daily-radar", "listing-audit", "opportunity-scan",
    "review-deepdive", "analyze", "price-band-overview", "price-band-detail",
    "brand-overview", "brand-detail", "history", "check",
]


class TestSubcommandHelp(unittest.TestCase):

    def _assert_help_exits_0(self, subcmd):
        with patch.object(sys, "argv", ["apiclaw.py", subcmd, "--help"]), \
             self.assertRaises(SystemExit) as cm:
            apiclaw.main()
        self.assertEqual(cm.exception.code, 0, f"'{subcmd} --help' should exit 0")

    def test_root_help(self):
        with patch.object(sys, "argv", ["apiclaw.py", "--help"]), \
             self.assertRaises(SystemExit) as cm:
            apiclaw.main()
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
        with patch.object(apiclaw, "api_call", return_value=MOCK_OK), \
             patch.object(apiclaw, "output"), \
             patch.object(sys, "argv", ["apiclaw.py", *argv]), \
             self.assertRaises(SystemExit) as cm:
            apiclaw.main()
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

    def test_brand_overview(self):
        r = run_cli("brand-overview", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/brand-overview")

    def test_brand_detail(self):
        r = run_cli("brand-detail", "--keyword", "yoga")
        self.assertEqual(r["endpoint"], "products/brand-detail")


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

        argv = ["apiclaw.py", "market-entry",
                "--keyword", "Over-Ear Headphones",
                "--category", self.DEEP_LEAF]
        with patch.object(apiclaw, "api_call", side_effect=fake_api_call), \
             patch.object(apiclaw, "output"), \
             patch.object(sys, "argv", argv):
            apiclaw.main()
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


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

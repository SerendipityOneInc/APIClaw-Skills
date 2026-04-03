"""
Tests for the argparse prefix-matching bug fix.

Verifies that:
1. --page and --page-size are passed to api_call independently and correctly
2. --page does NOT overwrite --page-size (the original bug)
3. allow_abbrev=False causes unknown abbreviations to error out
4. All 6 affected subcommands: market, products, price-band-overview,
   price-band-detail, brand-overview, brand-detail

Run from repo root:
    python -m pytest tests/test_apiclaw_page_arg.py -v
    # or without pytest:
    python tests/test_apiclaw_page_arg.py
"""

import importlib
import json
import os
import sys
import types
import unittest
from io import StringIO
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Load the module under test without executing main()
# ---------------------------------------------------------------------------
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "apiclaw", "scripts", "apiclaw.py")

spec = importlib.util.spec_from_file_location("apiclaw", SCRIPT_PATH)
apiclaw = importlib.util.module_from_spec(spec)
# Patch get_api_key before exec so the module doesn't fail at import time
with patch.dict("os.environ", {"APICLAW_API_KEY": "test_key"}):
    spec.loader.exec_module(apiclaw)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
MOCK_RESPONSE = {"success": True, "data": [], "_query": {"endpoint": "", "params": {}}}


def run_cli(*argv):
    """Run apiclaw.main() with the given argv, mocking api_call.

    Returns the params dict that was passed to api_call.
    """
    captured = {}

    def fake_api_call(endpoint, params):
        captured["endpoint"] = endpoint
        captured["params"] = dict(params)
        return {**MOCK_RESPONSE, "_query": {"endpoint": endpoint, "params": params}}

    with patch.object(apiclaw, "api_call", side_effect=fake_api_call), \
         patch.object(apiclaw, "output"), \
         patch.object(sys, "argv", ["apiclaw.py", *argv]):
        apiclaw.main()

    return captured


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestMarketPageArg(unittest.TestCase):

    def test_page_size_not_overwritten_by_page(self):
        """Original bug: --page 1 used to silently set page_size=1."""
        result = run_cli("market", "--category", "Sports", "--page-size", "20", "--page", "1")
        self.assertEqual(result["params"]["pageSize"], 20, "pageSize must remain 20")
        self.assertEqual(result["params"]["page"], 1, "page must be 1")

    def test_page_default_is_1(self):
        result = run_cli("market", "--category", "Sports")
        # page default=1 — but cmd_market only sets page if args.page is truthy
        # page=1 is truthy (non-zero), so it should be present
        self.assertEqual(result["params"]["page"], 1)

    def test_custom_page(self):
        result = run_cli("market", "--category", "Sports", "--page", "3")
        self.assertEqual(result["params"]["page"], 3)
        self.assertEqual(result["params"]["pageSize"], 20)  # default

    def test_page_and_page_size_independent(self):
        result = run_cli("market", "--page-size", "50", "--page", "2", "--keyword", "yoga")
        self.assertEqual(result["params"]["pageSize"], 50)
        self.assertEqual(result["params"]["page"], 2)


class TestProductsPageArg(unittest.TestCase):

    def test_page_size_not_overwritten_by_page(self):
        result = run_cli("products", "--keyword", "yoga mat", "--page-size", "20", "--page", "1")
        self.assertEqual(result["params"]["pageSize"], 20)
        self.assertEqual(result["params"]["page"], 1)

    def test_custom_page(self):
        result = run_cli("products", "--keyword", "yoga mat", "--page", "5")
        self.assertEqual(result["params"]["page"], 5)

    def test_page_size_default(self):
        result = run_cli("products", "--keyword", "yoga mat")
        self.assertEqual(result["params"]["pageSize"], 20)
        self.assertEqual(result["params"]["page"], 1)


class TestPriceBandOverviewPageArg(unittest.TestCase):

    def test_page_size_not_overwritten(self):
        result = run_cli("price-band-overview", "--keyword", "yoga", "--page-size", "30", "--page", "2")
        self.assertEqual(result["params"]["pageSize"], 30)
        self.assertEqual(result["params"]["page"], 2)

    def test_defaults(self):
        result = run_cli("price-band-overview", "--keyword", "yoga")
        self.assertEqual(result["params"]["pageSize"], 20)
        self.assertEqual(result["params"]["page"], 1)


class TestPriceBandDetailPageArg(unittest.TestCase):

    def test_page_size_not_overwritten(self):
        result = run_cli("price-band-detail", "--keyword", "yoga", "--page-size", "40", "--page", "3")
        self.assertEqual(result["params"]["pageSize"], 40)
        self.assertEqual(result["params"]["page"], 3)

    def test_defaults(self):
        result = run_cli("price-band-detail", "--keyword", "yoga")
        self.assertEqual(result["params"]["pageSize"], 20)
        self.assertEqual(result["params"]["page"], 1)


class TestBrandOverviewPageArg(unittest.TestCase):

    def test_page_size_not_overwritten(self):
        result = run_cli("brand-overview", "--keyword", "yoga", "--page-size", "15", "--page", "2")
        self.assertEqual(result["params"]["pageSize"], 15)
        self.assertEqual(result["params"]["page"], 2)

    def test_defaults(self):
        result = run_cli("brand-overview", "--keyword", "yoga")
        self.assertEqual(result["params"]["pageSize"], 20)
        self.assertEqual(result["params"]["page"], 1)


class TestBrandDetailPageArg(unittest.TestCase):

    def test_page_size_not_overwritten(self):
        result = run_cli("brand-detail", "--keyword", "yoga", "--page-size", "25", "--page", "4")
        self.assertEqual(result["params"]["pageSize"], 25)
        self.assertEqual(result["params"]["page"], 4)

    def test_defaults(self):
        result = run_cli("brand-detail", "--keyword", "yoga")
        self.assertEqual(result["params"]["pageSize"], 20)
        self.assertEqual(result["params"]["page"], 1)


class TestAllowAbbrevDisabled(unittest.TestCase):
    """allow_abbrev=False: abbreviated args should error, not silently match."""

    def _assert_parse_error(self, *argv):
        with patch.object(apiclaw, "api_call", return_value=MOCK_RESPONSE), \
             patch.object(apiclaw, "output"), \
             patch.object(sys, "argv", ["apiclaw.py", *argv]), \
             self.assertRaises(SystemExit) as cm:
            apiclaw.main()
        self.assertNotEqual(cm.exception.code, 0, "Should exit with error code")

    def test_abbreviated_page_errors_on_market(self):
        """--pag should NOT be silently matched to --page-size or --page."""
        self._assert_parse_error("market", "--category", "Sports", "--pag", "1")

    def test_abbreviated_page_size_errors(self):
        """--page-s should NOT silently match to --page-size."""
        self._assert_parse_error("market", "--category", "Sports", "--page-s", "20")


class TestCompetitorsUnchanged(unittest.TestCase):
    """competitors already had --page defined — verify it still works."""

    def test_competitors_page_and_page_size(self):
        result = run_cli("competitors", "--keyword", "earbuds", "--page-size", "30", "--page", "2")
        self.assertEqual(result["params"]["pageSize"], 30)
        self.assertEqual(result["params"]["page"], 2)


# ---------------------------------------------------------------------------
# Standalone runner (no pytest required)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

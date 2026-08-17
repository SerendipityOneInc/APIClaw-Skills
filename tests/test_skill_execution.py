"""Execution smoke tests for every skill's bundled CLI.

Goal: verify each of the 12 skills actually *executes* — the CLI imports and
builds its argparse tree, every subcommand the skill's SKILL.md declares it
uses really exists and its parser is well-formed, and `check` runs without a
Python traceback. All of this is **credit-free** (no API calls).

An optional live tier (one cheap real call per CLI) runs only when
`RUN_LIVE_SKILL_TESTS=1` and a `ZOODATA_API_KEY` is present.

Run: `python3 -m pytest tests/test_skill_execution.py -v`
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _discover_skills():
    """Return [(skill_name, cli_path)] for every skill that ships a CLI."""
    out = []
    for skill_md in sorted(REPO.glob("*/SKILL.md")):
        d = skill_md.parent
        for cli_name in ("zoodata.py", "webtools.py"):
            cli = d / "scripts" / cli_name
            if cli.exists():
                out.append((d.name, cli))
                break
    return out


SKILLS = _discover_skills()
NON_KEYWORD_ZOODATA_SKILLS = {
    name
    for name, cli in SKILLS
    if cli.name == "zoodata.py"
    and name not in {"zoodata", "amazon-keyword-traffic-analysis"}
}


def _declared_subcommands(skill_dir: Path):
    """Parse the "this skill's workflows use: a, b, ..." line from SKILL.md.

    Returns a set of subcommand tokens, or None if the skill declares the full
    surface ("all subcommands") or has no such line.
    """
    text = (skill_dir / "SKILL.md").read_text()
    # Match only to end of the declaration line — NOT across blank lines (re.S
    # would over-capture later bullets and could inject false subcommands).
    m = re.search(r"this skill's workflows use:\s*(.+)", text)
    if not m:
        return None
    frag = m.group(1)
    if "all subcommands" in frag.lower():
        return None
    return set(re.findall(r"`([a-z0-9\-]+)`", frag))


def _actual_subcommands(cli: Path):
    """Extract argparse subcommand names from the CLI source (add_parser calls)."""
    src = cli.read_text()
    return set(re.findall(r"add_parser\(\s*[\"']([a-z0-9\-]+)[\"']", src))


def _run(cli: Path, *args, timeout=30):
    return subprocess.run(
        [sys.executable, str(cli), *args],
        capture_output=True, text=True, timeout=timeout,
        cwd=str(cli.parent.parent),
        env={**os.environ, "ZOODATA_API_KEY": os.environ.get("ZOODATA_API_KEY", "")},
    )


class TestSkillCliExecutes(unittest.TestCase):
    def test_at_least_all_twelve_skills_discovered(self):
        # Guard: the suite must actually cover every skill, not silently skip.
        self.assertEqual(len(SKILLS), 12, f"discovered {len(SKILLS)}: {[s for s,_ in SKILLS]}")

    def test_cli_help_runs(self):
        """`<cli> --help` exits 0 with no Python traceback (CLI imports + builds)."""
        for name, cli in SKILLS:
            with self.subTest(skill=name):
                r = _run(cli, "--help")
                self.assertEqual(r.returncode, 0, f"{name} --help exit {r.returncode}\n{r.stderr}")
                self.assertNotIn("Traceback (most recent call last)", r.stderr, name)

    def test_declared_subcommands_exist_in_cli(self):
        """Every subcommand a SKILL.md claims to use must exist in its CLI."""
        for name, cli in SKILLS:
            declared = _declared_subcommands(cli.parent.parent)
            if declared is None:
                continue  # full-surface skill (zoodata) or no declaration
            actual = _actual_subcommands(cli)
            with self.subTest(skill=name):
                missing = declared - actual
                self.assertEqual(missing, set(),
                                 f"{name} declares subcommands not in its CLI: {sorted(missing)}")

    def test_declared_subcommand_parsers_are_wellformed(self):
        """`<cli> <subcmd> --help` exits 0 for each declared subcommand (parser builds)."""
        for name, cli in SKILLS:
            declared = _declared_subcommands(cli.parent.parent)
            subcmds = sorted(declared) if declared else sorted(_actual_subcommands(cli))
            for sub in subcmds:
                with self.subTest(skill=name, sub=sub):
                    r = _run(cli, sub, "--help")
                    self.assertEqual(r.returncode, 0,
                                     f"{name} {sub} --help exit {r.returncode}\n{r.stderr}")
                    self.assertNotIn("Traceback (most recent call last)", r.stderr)

    def test_check_runs_without_crash(self):
        """`<cli> check` must not crash with a traceback (exit code is env-dependent:
        0 when a key is configured, non-zero when not — both are 'normal')."""
        for name, cli in SKILLS:
            with self.subTest(skill=name):
                r = _run(cli, "check")
                self.assertNotIn("Traceback (most recent call last)", r.stderr,
                                 f"{name} check crashed:\n{r.stderr}")
                self.assertIn(r.returncode, (0, 1, 2), f"{name} check exit {r.returncode}")

    def test_shared_cli_contract_has_one_canonical_owner(self):
        contract = (
            REPO / "zoodata" / "references" / "cli-contract.md"
        ).read_text()
        self.assertIn(
            "# ZooData CLI Contract",
            contract,
        )
        for required in (
            "## Invocation interface",
            "## Command identity and composite reuse",
            "## Execution-environment permission gate",
            "Treat API endpoint identifiers and composite result keys as data identities",
            "Treat a successful composite command's structured output as the evidence bundle",
            "Use the execution tool's permission or escalation mechanism to request access",
            "rerun the exact unchanged CLI command",
            "Always inspect stdout, even when the process exits non-zero",
            "Treat `_transport.status` as the authoritative outer HTTP status",
            "one fixed blind retry budget to every HTTP non-2xx or network failure",
            "does not assign HTTP-status meaning",
            "A valid `status=empty` or a documented business/coverage error is not automatically terminal",
            "A partial pagination failure must return `success=false`",
        ):
            self.assertIn(required, contract)
        self.assertIn(
            "This shared contract intentionally defines no user-facing wording",
            contract,
        )
        self.assertNotIn("## Default interface failure output", contract)
        self.assertNotIn("Service is currently unavailable", contract)
        self.assertNotIn("STOP_CURRENT_TURN", contract)

    def test_all_non_keyword_zoodata_skills_route_to_shared_cli_contract(self):
        expected = {
            "amazon-analysis",
            "amazon-competitor-intelligence-monitor",
            "amazon-daily-market-radar",
            "amazon-listing-audit-pro",
            "amazon-market-entry-analyzer",
            "amazon-market-trend-scanner",
            "amazon-opportunity-discoverer",
            "amazon-pricing-command-center",
            "amazon-review-intelligence-extractor",
        }
        self.assertEqual(NON_KEYWORD_ZOODATA_SKILLS, expected)
        contract_ref = "Before selecting or invoking the first command, read and apply the local `references/cli-contract.md`"
        for name in sorted(NON_KEYWORD_ZOODATA_SKILLS):
            with self.subTest(skill=name):
                skill = (REPO / name / "SKILL.md").read_text()
                self.assertIn("## Shared CLI Contract", skill)
                self.assertIn(contract_ref, skill)
                self.assertIn("Reapply it after every granular or composite result", skill)
                self.assertNotIn("Always parse valid structured stdout even when the process exits non-zero", skill)
                self.assertIn("### Local Interface Failure Output", skill)
                self.assertNotIn("zoodata/SKILL.md", skill)
                self.assertIn("https://zoodata.ai/en/pricing", skill)

        zoodata_skill = (REPO / "zoodata" / "SKILL.md").read_text()
        self.assertIn("## Shared CLI contract", zoodata_skill)
        self.assertIn("### Local Interface Failure Output", zoodata_skill)

    def test_every_zoodata_skill_has_a_byte_identical_local_contract(self):
        canonical = (
            REPO / "zoodata" / "references" / "cli-contract.md"
        ).read_bytes()
        zoodata_skills = {
            name for name, cli in SKILLS if cli.name == "zoodata.py" and name != "zoodata"
        }
        self.assertEqual(len(zoodata_skills), 10)
        for name in sorted(zoodata_skills):
            with self.subTest(skill=name):
                copy = REPO / name / "references" / "cli-contract.md"
                self.assertTrue(copy.is_file(), f"missing shared contract copy: {copy}")
                self.assertEqual(
                    copy.read_bytes(),
                    canonical,
                    f"out-of-sync shared contract copy: {copy}",
                )

    def test_release_workflow_blocks_unsynced_shared_files(self):
        workflow = (REPO / ".github" / "workflows" / "shared-files-distribution.yml").read_text()
        sync_script = (REPO / "scripts" / "sync-scripts.sh").read_text()
        pre_commit = (REPO / "scripts" / "pre-commit").read_text()

        self.assertIn("pull_request:", workflow)
        self.assertNotIn("    paths:", workflow)
        self.assertIn("name: Sync Shared Files & Test", workflow)
        self.assertIn("run: bash scripts/sync-scripts.sh --check", workflow)
        self.assertIn("CHECK_ONLY=1", sync_script)
        self.assertIn("OUT-OF-SYNC", sync_script)
        self.assertIn("references/cli-contract.md", pre_commit)

    def test_keyword_skill_keeps_its_specialized_failure_gate(self):
        skill = (REPO / "amazon-keyword-traffic-analysis" / "SKILL.md").read_text()
        self.assertIn("Read the local `references/cli-contract.md`", skill)
        self.assertIn(
            "apply its `Interface Failure Stop Gate` before selecting any next capability or command",
            skill,
        )


@unittest.skipUnless(
    os.environ.get("RUN_LIVE_SKILL_TESTS") == "1" and os.environ.get("ZOODATA_API_KEY"),
    "live tier: set RUN_LIVE_SKILL_TESTS=1 and ZOODATA_API_KEY to run real API calls",
)
class TestSkillCliLive(unittest.TestCase):
    """One cheap real call per zoodata CLI: `categories --marketplace US` is a
    zero/low-cost endpoint. Confirms the end-to-end HTTP + auth path works."""

    def test_categories_call_succeeds(self):
        for name, cli in SKILLS:
            if cli.name != "zoodata.py":
                continue
            with self.subTest(skill=name):
                r = _run(cli, "categories", "--marketplace", "US", timeout=60)
                self.assertEqual(r.returncode, 0, f"{name} categories failed:\n{r.stderr}")
                self.assertNotIn("Traceback (most recent call last)", r.stderr)

    def test_composite_workflow_reports_aggregated_credits(self):
        """A real composite run (market-entry fans out over ~all endpoints) must
        execute end-to-end AND surface an aggregated credit total in its meta —
        the regression the _CreditTracker fix targets (was reported as 1)."""
        import json
        cli = REPO / "amazon-market-entry-analyzer" / "scripts" / "zoodata.py"
        r = _run(cli, "market-entry", "--keyword", "yoga mat", timeout=300)
        self.assertEqual(r.returncode, 0, f"market-entry failed:\n{r.stderr[:400]}")
        meta = json.loads(r.stdout).get("meta", {})
        self.assertGreater(meta.get("apiCalls", 0), 1, "composite should fan out to many calls")
        # The regression collapsed the total to a single internal call's figure (1).
        # Assert the surfaced total reflects the fan-out, without assuming a fixed
        # per-endpoint cost (some endpoints could be zero-cost).
        self.assertGreater(meta.get("creditsConsumed", 0), 1,
                           "aggregated credits must exceed a single call's figure")


if __name__ == "__main__":
    unittest.main()

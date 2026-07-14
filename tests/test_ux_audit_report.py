"""Structural tests for the UX audit deliverable (research artifact)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ux-audit" / "UX_TASK_MAP_AND_FLAWS.md"


class TestUxAuditReport(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REPORT.is_file(), "UX report must exist")
        self.text = REPORT.read_text(encoding="utf-8")

    def test_minimum_tasks_named(self):
        for needle in (
            "Product search",
            "price by supermarket",
            "Shopping lists",
            "Price history",
            "competitors",
            "EU",
            "categories",
        ):
            self.assertIn(needle, self.text)

    def test_has_measured_durations(self):
        # Rows like: | **Measured** | **~9.5 s** ... |  or **16.7–17.7 s**
        measured = re.findall(
            r"\*\*Measured\*\*[^|\n]{0,20}\|\s*\*+~?([0-9]+(?:\.[0-9]+)?)",
            self.text,
        )
        # Timing summary table numeric cells
        table = re.findall(
            r"\|\s*\*\*([0-9]+(?:\.[0-9]+)?)\*\*\s*\|",
            self.text,
        )
        # Any "duration_s=" style from embedded method notes not required
        total = len(measured) + len(table)
        self.assertGreaterEqual(
            total,
            3,
            f"measured={measured!r} table={table!r}",
        )

    def test_flaw_count_at_least_8(self):
        flaws = re.findall(r"\|\s*\*\*(F\d+)\*\*", self.text)
        self.assertGreaterEqual(len(set(flaws)), 8, flaws)

    def test_method_mentions_proxy_and_playwright(self):
        low = self.text.lower()
        self.assertIn("proxy", low)
        self.assertIn("playwright", low)

    def test_integrated_map_section(self):
        self.assertIn("Integrated map", self.text)

    def test_screens_dir_has_evidence(self):
        d = ROOT / "docs" / "ux-audit" / "screens"
        self.assertTrue(d.is_dir())
        self.assertGreaterEqual(len(list(d.glob("*.png"))), 5)

    def test_timings_log_present(self):
        # Prefer in-repo copy; allow method section as fallback proof
        log = ROOT / "docs" / "ux-audit" / "task-timings.log"
        if log.is_file():
            body = log.read_text(encoding="utf-8", errors="replace")
            self.assertIn("duration_s=", body)
        else:
            self.assertIn("Timing summary", self.text)


if __name__ == "__main__":
    unittest.main()

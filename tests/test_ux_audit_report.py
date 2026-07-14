"""Structural tests for the UX audit deliverable."""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ux-audit" / "UX_TASK_MAP_AND_FLAWS.md"
SCREENS = ROOT / "docs" / "ux-audit" / "screens"
TIMINGS = ROOT / "docs" / "ux-audit" / "timings.json"


class TestUxAuditReport(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REPORT.is_file())
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
        # Verified numeric durations in timing table
        nums = re.findall(r"\|\s*\*\*([0-9]+(?:\.[0-9]+)?)\*\*\s*\|", self.text)
        self.assertGreaterEqual(len(nums), 3, nums)

    def test_flaw_count_at_least_8(self):
        flaws = re.findall(r"\|\s*\*\*(F\d+)\*\*", self.text)
        self.assertGreaterEqual(len(set(flaws)), 8)

    def test_method_mentions_proxy_and_playwright(self):
        low = self.text.lower()
        self.assertIn("proxy", low)
        self.assertIn("playwright", low)

    def test_integrated_map_section(self):
        self.assertIn("Integrated map", self.text)

    def test_screens_unique_and_present(self):
        self.assertTrue(SCREENS.is_dir())
        pngs = list(SCREENS.glob("*.png"))
        self.assertGreaterEqual(len(pngs), 8)
        hashes = {}
        for p in pngs:
            h = hashlib.md5(p.read_bytes()).hexdigest()
            hashes.setdefault(h, []).append(p.name)
        dups = {h: ns for h, ns in hashes.items() if len(ns) > 1}
        self.assertEqual(dups, {}, f"duplicate screenshots: {dups}")

    def test_required_outcome_screens(self):
        names = {p.name for p in SCREENS.glob("*.png")}
        for required in (
            "T1_search_results_mobile.png",
            "T2_product_multi_chain_prices.png",
            "T7_lists_index.png",
        ):
            self.assertIn(required, names)

    def test_timings_json_marks_unobserved_honestly(self):
        import json

        data = json.loads(TIMINGS.read_text(encoding="utf-8"))
        by_id = {t["task_id"]: t for t in data}
        # Successful timed tasks must have evidence files that exist
        for tid in ("T1_search_product", "T2_product_price_by_chain", "T7_shopping_lists"):
            self.assertIn(tid, by_id)
            self.assertTrue(by_id[tid]["success"])
            ev = by_id[tid]["evidence"]
            self.assertTrue((SCREENS / Path(ev).name).is_file(), ev)
        # Unobserved must not claim success with fake duration
        for tid in ("T3_price_history", "T4_competitors"):
            if tid in by_id:
                self.assertFalse(by_id[tid].get("success", True))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for pure basket / availability helpers (no network)."""

from __future__ import annotations

import unittest

from posokanei.basket import (
    compare_basket,
    is_available,
    price_at_retailer,
    collect_retailer_ids,
)


def _product(pid, name, prices, country="GR"):
    """prices: dict retailer -> price."""
    retailer_prices = [
        {
            "retailer": rid,
            "retailer_display_name": rid,
            "price": price,
            "price_normalized": price,
            "is_discount": False,
            "country": country,
        }
        for rid, price in prices.items()
    ]
    return {
        "id": pid,
        "name": name,
        "retailers": list(prices.keys()),
        "retailer_prices": retailer_prices,
        "missing": False,
    }


class TestPriceAtRetailer(unittest.TestCase):
    def test_found(self):
        p = _product("a", "Milk", {"sklavenitis": 1.5, "lidl": 1.2})
        self.assertEqual(price_at_retailer(p, "lidl"), 1.2)
        self.assertIsNone(price_at_retailer(p, "masoutis"))


class TestAvailability(unittest.TestCase):
    def test_yes_no_unknown(self):
        p = _product("a", "Milk", {"sklavenitis": 1.5})
        yes = is_available(p, "sklavenitis")
        self.assertEqual(yes.status, "yes")
        self.assertTrue(yes.available)
        self.assertEqual(yes.price, 1.5)

        no = is_available(p, "lidl")
        self.assertEqual(no.status, "no")
        self.assertFalse(no.available)

        missing = {"id": None, "name": "X", "missing": True, "retailer_prices": []}
        unk = is_available(missing, "lidl")
        self.assertEqual(unk.status, "unknown")


class TestCompareBasket(unittest.TestCase):
    def test_totals_and_cheapest(self):
        products = [
            _product("1", "Milk", {"sklavenitis": 1.5, "lidl": 1.2, "masoutis": 1.4}),
            _product("2", "Bread", {"sklavenitis": 1.0, "lidl": 0.9}),
            _product("3", "Eggs", {"sklavenitis": 3.0, "masoutis": 2.5}),
        ]
        cmp_ = compare_basket(products, country="GR")
        by_r = {r.retailer: r for r in cmp_.retailers}

        self.assertAlmostEqual(by_r["sklavenitis"].total, 5.5)
        self.assertTrue(by_r["sklavenitis"].complete)

        self.assertFalse(by_r["lidl"].complete)
        self.assertAlmostEqual(by_r["lidl"].total, 2.1)  # partial sum
        self.assertIn("Eggs", by_r["lidl"].missing_items)

        self.assertEqual(cmp_.cheapest, "sklavenitis")
        self.assertAlmostEqual(cmp_.cheapest_total, 5.5)

    def test_require_complete(self):
        products = [
            _product("1", "Milk", {"sklavenitis": 1.5, "lidl": 1.2}),
            _product("2", "Bread", {"sklavenitis": 1.0}),
        ]
        cmp_ = compare_basket(products, require_complete=True)
        by_r = {r.retailer: r for r in cmp_.retailers}
        self.assertIsNone(by_r["lidl"].total)
        self.assertAlmostEqual(by_r["sklavenitis"].total, 2.5)

    def test_collect_retailers_country_filter(self):
        p = {
            "id": "1",
            "name": "X",
            "retailer_prices": [
                {"retailer": "lidl", "price": 1.0, "country": "GR"},
                {"retailer": "carrefour_es", "price": 1.1, "country": "ES"},
            ],
        }
        ids = collect_retailer_ids([p], country="GR")
        self.assertEqual(ids, ["lidl"])


if __name__ == "__main__":
    unittest.main()

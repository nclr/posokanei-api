"""Structural / pure unit tests for client helpers (no live network)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from posokanei.client import ProductPage, PosoKaneiClient, _looks_like_product_id


ROOT = Path(__file__).resolve().parents[1]


class TestProductPage(unittest.TestCase):
    def test_from_dict(self):
        raw = {
            "products": [{"id": "abc", "name": "N"}],
            "total": 10,
            "page": 2,
            "page_size": 5,
            "total_pages": 2,
            "has_next": False,
            "has_prev": True,
            "query_time_ms": 3,
        }
        page = ProductPage.from_dict(raw)
        self.assertEqual(page.total, 10)
        self.assertEqual(len(page.products), 1)
        self.assertFalse(page.has_next)


class TestLooksLikeId(unittest.TestCase):
    def test_hex32(self):
        self.assertTrue(_looks_like_product_id("a1d2bc0e1bce49d3ade7d6a403c43e80"))
        self.assertFalse(_looks_like_product_id("γάλα"))
        self.assertFalse(_looks_like_product_id("short"))


class TestApiMapArtifact(unittest.TestCase):
    def test_api_map_lists_core_endpoints(self):
        path = ROOT / "docs" / "api_map.json"
        self.assertTrue(path.is_file(), "docs/api_map.json must ship")
        data = json.loads(path.read_text(encoding="utf-8"))
        paths = {e["path"] for e in data["endpoints"]}
        for required in (
            "/products/search",
            "/products/{id}",
            "/meta/stats",
            "/meta/retailers",
            "/products/{id}/competitors",
        ):
            self.assertIn(required, paths)
        self.assertEqual(data["base_url"], "https://api.posokanei.gov.gr")


class TestClientRequestUsesProxyEnv(unittest.TestCase):
    def test_opener_reads_proxy_env(self):
        with mock.patch.dict(
            "os.environ",
            {
                "HTTPS_PROXY": "http://agent:secret@100.92.223.118:18888",
                "HTTP_PROXY": "http://agent:secret@100.92.223.118:18888",
            },
            clear=False,
        ):
            from posokanei import client as client_mod

            opener = client_mod._build_opener()
            # ProxyHandler is present
            handler_types = [type(h).__name__ for h in opener.handlers]
            self.assertIn("ProxyHandler", handler_types)


class TestClientGetProductPath(unittest.TestCase):
    def test_get_product_builds_path(self):
        c = PosoKaneiClient()
        captured = {}

        def fake_request(method, path, query=None, body=None, raw=False):
            captured["method"] = method
            captured["path"] = path
            captured["query"] = query
            return {"id": "x", "name": "y", "retailer_prices": []}

        c.request = fake_request  # type: ignore
        c.get_product("deadbeefdeadbeefdeadbeefdeadbeef", countries="GR")
        self.assertEqual(captured["method"], "GET")
        self.assertEqual(captured["path"], "/products/deadbeefdeadbeefdeadbeefdeadbeef")
        self.assertEqual(captured["query"]["countries"], "GR")


if __name__ == "__main__":
    unittest.main()

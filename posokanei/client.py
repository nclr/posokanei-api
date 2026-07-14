"""HTTP client for https://api.posokanei.gov.gr (respects HTTP(S)_PROXY)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional, Sequence

DEFAULT_BASE_URL = "https://api.posokanei.gov.gr"
DEFAULT_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 posokanei-api/0.1"
)


class PosoKaneiError(Exception):
    """API or transport error."""

    def __init__(self, message: str, status: Optional[int] = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


@dataclass
class ProductPage:
    products: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    query_time_ms: Optional[float] = None
    raw: Optional[dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProductPage":
        return cls(
            products=list(data.get("products") or []),
            total=int(data.get("total") or 0),
            page=int(data.get("page") or 1),
            page_size=int(data.get("page_size") or 0),
            total_pages=int(data.get("total_pages") or 0),
            has_next=bool(data.get("has_next")),
            has_prev=bool(data.get("has_prev")),
            query_time_ms=data.get("query_time_ms"),
            raw=dict(data),
        )


def _build_opener() -> urllib.request.OpenerDirector:
    """Build opener that honors HTTP_PROXY / HTTPS_PROXY from the environment."""
    # ProxyHandler(None) would disable; empty dict still lets env proxies work
    # via getproxies() when we pass nothing special — but we want explicit env.
    proxies: MutableMapping[str, str] = {}
    for key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        val = os.environ.get(key)
        if val:
            scheme = "https" if "https" in key.lower() else "http"
            proxies[scheme] = val
    # Prefer https_proxy for both if only one set
    if "https" in proxies and "http" not in proxies:
        proxies["http"] = proxies["https"]
    if "http" in proxies and "https" not in proxies:
        proxies["https"] = proxies["http"]
    if proxies:
        return urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
    return urllib.request.build_opener()


class PosoKaneiClient:
    """Thin client for the public PosoKanei API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        user_agent: str = DEFAULT_UA,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_agent = user_agent
        self._opener = _build_opener()

    def _headers(self, extra: Optional[Mapping[str, str]] = None) -> dict[str, str]:
        h = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "Origin": "https://posokanei.gov.gr",
            "Referer": "https://posokanei.gov.gr/",
        }
        if extra:
            h.update(extra)
        return h

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
        raw: bool = False,
    ) -> Any:
        if not path.startswith("/"):
            path = "/" + path
        url = self.base_url + path
        if query:
            q = {
                k: (str(v).lower() if isinstance(v, bool) else str(v))
                for k, v in query.items()
                if v is not None
            }
            url = url + "?" + urllib.parse.urlencode(q, doseq=True)

        data = None
        headers = self._headers()
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._opener.open(req, timeout=self.timeout) as resp:
                payload = resp.read()
                status = getattr(resp, "status", None) or resp.getcode()
                content_type = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            err_body = e.read()
            try:
                parsed = json.loads(err_body.decode("utf-8"))
            except Exception:
                parsed = err_body.decode("utf-8", errors="replace")
            raise PosoKaneiError(
                f"HTTP {e.code} for {method} {path}: {parsed}",
                status=e.code,
                body=parsed,
            ) from e
        except urllib.error.URLError as e:
            raise PosoKaneiError(f"Transport error for {method} {path}: {e}") from e

        if raw:
            return payload
        if not payload:
            return None
        if "application/json" in content_type or payload[:1] in (b"{", b"["):
            return json.loads(payload.decode("utf-8"))
        return payload

    def get(self, path: str, **query: Any) -> Any:
        return self.request("GET", path, query=query or None)

    def post(self, path: str, body: Any) -> Any:
        return self.request("POST", path, body=body)

    # --- Meta ---

    def stats(self) -> dict[str, Any]:
        return self.get("/meta/stats")

    def retailers(self, countries: str = "GR") -> list[dict[str, Any]]:
        data = self.get("/meta/retailers", countries=countries)
        return list(data.get("retailers") or [])

    def categories(self) -> list[dict[str, Any]]:
        data = self.get("/meta/categories")
        return list(data.get("categories") or [])

    def category_tree(
        self, include_counts: bool = True, include_hidden: bool = False
    ) -> dict[str, Any]:
        return self.get(
            "/meta/categories/tree",
            include_counts=include_counts,
            include_hidden=include_hidden,
        )

    # --- Products ---

    def list_products(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "name",
        sort_order: str = "asc",
        category: Optional[str] = None,
        countries: str = "GR",
        is_international: Optional[bool] = None,
    ) -> ProductPage:
        q: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "countries": countries,
        }
        if category:
            q["category"] = category
        if is_international is not None:
            q["is_international"] = is_international
        return ProductPage.from_dict(self.get("/products", **q))

    def search(
        self,
        title: Optional[str] = None,
        *,
        ids: Optional[Sequence[str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "name",
        sort_order: str = "asc",
    ) -> ProductPage:
        body: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if title is not None:
            body["title"] = title
        if ids is not None:
            body["ids"] = list(ids)
        return ProductPage.from_dict(self.post("/products/search", body))

    def get_product(
        self,
        product_id: str,
        *,
        countries: str = "GR",
        include_tax: bool = True,
        sort_retailers: str = "asc",
        include_history: bool = False,
        price_type: Optional[str] = None,
    ) -> dict[str, Any]:
        if not product_id:
            raise ValueError("product_id cannot be empty")
        q: dict[str, Any] = {
            "countries": countries,
            "include_tax": include_tax,
            "sort_retailers": sort_retailers,
        }
        if include_history:
            q["include_history"] = True
        if price_type:
            q["price_type"] = price_type
        return self.get(f"/products/{product_id}", **q)

    def by_barcode(
        self,
        barcode: str,
        *,
        countries: str = "GR",
        include_tax: bool = True,
    ) -> dict[str, Any]:
        if not barcode:
            raise ValueError("barcode cannot be empty")
        return self.get(
            f"/products/barcode/{barcode}",
            countries=countries,
            include_tax=include_tax,
        )

    def competitors(
        self,
        product_id: str,
        *,
        include_tax: bool = True,
        retailer: Optional[str] = None,
    ) -> dict[str, Any]:
        if not product_id:
            raise ValueError("product_id cannot be empty")
        q: dict[str, Any] = {"include_tax": include_tax}
        if retailer:
            q["retailer"] = retailer
        return self.get(f"/products/{product_id}/competitors", **q)

    def resolve_products(
        self,
        queries: Sequence[str],
        *,
        page_size: int = 5,
    ) -> list[dict[str, Any]]:
        """Resolve free-text or product-id queries to best-match products.

        - If a query looks like a 32-char hex product id, fetch by id (fallback search).
        - Otherwise POST /products/search with title=query and take the first hit.
        """
        resolved: list[dict[str, Any]] = []
        for q in queries:
            q = (q or "").strip()
            if not q:
                continue
            if _looks_like_product_id(q):
                try:
                    resolved.append(self.get_product(q))
                    continue
                except PosoKaneiError:
                    pass
            page = self.search(title=q, page=1, page_size=page_size)
            if not page.products:
                resolved.append(
                    {
                        "id": None,
                        "name": q,
                        "query": q,
                        "missing": True,
                        "retailers": [],
                        "retailer_prices": [],
                    }
                )
            else:
                hit = dict(page.products[0])
                hit["query"] = q
                hit["missing"] = False
                resolved.append(hit)
        return resolved


def _looks_like_product_id(value: str) -> bool:
    v = value.strip().lower()
    return len(v) == 32 and all(c in "0123456789abcdef" for c in v)

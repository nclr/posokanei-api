"""CLI entry points for PosoKanei API."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional, Sequence

from .basket import compare_basket, is_available
from .client import PosoKaneiClient, PosoKaneiError


def _client() -> PosoKaneiClient:
    return PosoKaneiClient()


def _print_json(data: Any) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def cmd_search(args: argparse.Namespace) -> int:
    client = _client()
    page = client.search(
        title=args.query,
        page=args.page,
        page_size=args.page_size,
        sort_by=args.sort_by,
        sort_order=args.sort_order,
    )
    if args.json:
        _print_json(page.raw or page.__dict__)
        return 0
    print(f"total={page.total} page={page.page}/{page.total_pages} showing={len(page.products)}")
    for p in page.products:
        stats = p.get("price_stats") or {}
        retailers = ",".join(p.get("retailers") or [])
        print(
            f"{p.get('id')}\t{stats.get('min_price')}-{stats.get('max_price')}\t"
            f"{(p.get('name') or '').strip()}\t[{retailers}]"
        )
    return 0


def cmd_product(args: argparse.Namespace) -> int:
    client = _client()
    product = client.get_product(
        args.product_id,
        countries=args.countries,
        include_tax=not args.no_tax,
        include_history=args.history,
    )
    if args.json:
        _print_json(product)
        return 0
    print(f"id={product.get('id')}")
    print(f"name={(product.get('name') or '').strip()}")
    print(f"brand={product.get('brand')}")
    print(f"unit={product.get('unit_quantity')} {product.get('unit')}")
    print("prices:")
    for rp in product.get("retailer_prices") or []:
        disc = " DISCOUNT" if rp.get("is_discount") else ""
        print(
            f"  {rp.get('retailer'):20} {rp.get('price'):8.2f} EUR "
            f"({rp.get('retailer_display_name')}){disc}"
        )
    return 0


def cmd_available(args: argparse.Namespace) -> int:
    client = _client()
    products = client.resolve_products([args.product])
    product = products[0]
    av = is_available(product, args.retailer)
    if args.json:
        _print_json(av.to_dict())
        return 0
    print(f"product_id={av.product_id}")
    print(f"product_name={av.product_name}")
    print(f"retailer={av.retailer}")
    print(f"status={av.status}")
    print(f"available={av.available}")
    print(f"price={av.price}")
    return 0


def cmd_basket(args: argparse.Namespace) -> int:
    client = _client()
    queries = list(args.products)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    queries.append(line)
    if not queries:
        print("No products specified", file=sys.stderr)
        return 2

    products = client.resolve_products(queries)
    only = args.retailers.split(",") if args.retailers else None
    comparison = compare_basket(
        products,
        retailers=only,
        country=args.countries if args.countries != "ALL" else None,
        require_complete=args.require_complete,
    )
    if args.json:
        _print_json(comparison.to_dict())
        return 0

    print("=== Basket items ===")
    for item in comparison.items:
        flag = "MISSING" if item.missing else "OK"
        print(f"  [{flag}] {item.product_name} (id={item.product_id})")

    print("\n=== Cost by supermarket ===")
    for r in comparison.retailers:
        if r.total is None:
            total_s = "n/a"
        else:
            total_s = f"{r.total:.2f} EUR"
        complete_s = "complete" if r.complete else f"incomplete missing={r.missing_count}"
        print(f"  {r.retailer:20} total={total_s:12} priced={r.priced_count} ({complete_s})")
        if args.verbose:
            for li in r.line_items:
                p = "—" if li["price"] is None else f"{li['price']:.2f}"
                print(f"      - {p:>8}  {li['name']}")

    if comparison.cheapest is not None:
        print(
            f"\nCheapest (best complete or fullest basket): "
            f"{comparison.cheapest} @ {comparison.cheapest_total:.2f} EUR"
        )
    return 0


def cmd_meta(args: argparse.Namespace) -> int:
    client = _client()
    if args.what == "stats":
        data = client.stats()
    elif args.what == "retailers":
        data = client.retailers(countries=args.countries)
    elif args.what == "categories":
        data = client.categories()
    elif args.what == "tree":
        data = client.category_tree()
    else:
        print(f"Unknown meta: {args.what}", file=sys.stderr)
        return 2
    _print_json(data)
    return 0


def cmd_competitors(args: argparse.Namespace) -> int:
    client = _client()
    data = client.competitors(args.product_id, retailer=args.retailer)
    if args.json:
        _print_json(data)
        return 0
    print(f"product={data.get('product_name')} total_competitors={data.get('total_competitors')}")
    for c in data.get("competitors") or []:
        stats = c.get("price_stats") or {}
        print(
            f"  {c.get('id')}  {stats.get('min_price')}-{stats.get('max_price')}  "
            f"{(c.get('name') or '').strip()}"
        )
    return 0


def cmd_barcode(args: argparse.Namespace) -> int:
    client = _client()
    product = client.by_barcode(args.barcode, countries=args.countries)
    if args.json:
        _print_json(product)
        return 0
    print(f"id={product.get('id')}")
    print(f"name={(product.get('name') or '').strip()}")
    for rp in product.get("retailer_prices") or []:
        print(f"  {rp.get('retailer'):20} {rp.get('price')}")
    return 0


def cmd_exercise(args: argparse.Namespace) -> int:
    """Hit multiple mapped endpoints; print summary for verification logs."""
    client = _client()
    report: dict[str, Any] = {"endpoints": []}

    def rec(name: str, path: str, fn):
        try:
            data = fn()
            keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
            sample = None
            if isinstance(data, dict):
                if "products" in data and data["products"]:
                    p0 = data["products"][0]
                    sample = {
                        "id": p0.get("id"),
                        "name": (p0.get("name") or "")[:60],
                        "retailers": p0.get("retailers"),
                    }
                elif "retailers" in data and isinstance(data["retailers"], list) and data["retailers"]:
                    r0 = data["retailers"][0]
                    sample = r0 if isinstance(r0, dict) else {"id": r0}
                elif "total_products" in data:
                    sample = {
                        "total_products": data.get("total_products"),
                        "retailer_count": data.get("retailer_count"),
                    }
            entry = {"name": name, "path": path, "status": "ok", "keys": keys, "sample": sample}
            report["endpoints"].append(entry)
            print(f"OK  {path} keys={keys} sample={sample}")
        except Exception as e:
            report["endpoints"].append(
                {"name": name, "path": path, "status": "error", "error": str(e)}
            )
            print(f"ERR {path}: {e}", file=sys.stderr)

    rec("meta_stats", "GET /meta/stats", client.stats)
    rec(
        "meta_retailers",
        "GET /meta/retailers",
        lambda: {"retailers": client.retailers(countries="GR"), "count": "n/a"},
    )
    rec(
        "products_search",
        "POST /products/search",
        lambda: client.search(title=args.query or "γάλα", page_size=3).raw,
    )
    page = client.search(title=args.query or "γάλα", page_size=1)
    pid = page.products[0]["id"] if page.products else None
    if pid:
        rec(
            "product_detail",
            f"GET /products/{pid}",
            lambda: client.get_product(pid),
        )
        rec(
            "product_competitors",
            f"GET /products/{pid}/competitors",
            lambda: client.competitors(pid),
        )
    rec(
        "products_list",
        "GET /products",
        lambda: client.list_products(page_size=2).raw,
    )
    if args.json:
        _print_json(report)
    return 0 if all(e.get("status") == "ok" for e in report["endpoints"]) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="posokanei",
        description="PosoKanei.gov.gr API client (use Greek egress proxy)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("search", help="Search products by title")
    s.add_argument("query")
    s.add_argument("--page", type=int, default=1)
    s.add_argument("--page-size", type=int, default=10)
    s.add_argument("--sort-by", default="name")
    s.add_argument("--sort-order", default="asc")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("product", help="Product detail + prices by store")
    s.add_argument("product_id")
    s.add_argument("--countries", default="GR")
    s.add_argument("--no-tax", action="store_true")
    s.add_argument("--history", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_product)

    s = sub.add_parser("available", help="Is product available at a supermarket chain?")
    s.add_argument("product", help="Product id or search text")
    s.add_argument("retailer", help="Retailer id e.g. sklavenitis")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_available)

    s = sub.add_parser("basket", help="Compare basket cost across supermarkets")
    s.add_argument("products", nargs="*", help="Product ids or search texts")
    s.add_argument("-f", "--file", help="File with one product query per line")
    s.add_argument("--retailers", help="Comma-separated retailer ids to include")
    s.add_argument("--countries", default="GR", help="GR or ALL")
    s.add_argument("--require-complete", action="store_true")
    s.add_argument("-v", "--verbose", action="store_true")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_basket)

    s = sub.add_parser("meta", help="Meta endpoints")
    s.add_argument("what", choices=["stats", "retailers", "categories", "tree"])
    s.add_argument("--countries", default="GR")
    s.set_defaults(func=cmd_meta)

    s = sub.add_parser("competitors", help="Competitor products")
    s.add_argument("product_id")
    s.add_argument("--retailer")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_competitors)

    s = sub.add_parser("barcode", help="Lookup by barcode (rate-limited)")
    s.add_argument("barcode")
    s.add_argument("--countries", default="GR")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_barcode)

    s = sub.add_parser("exercise", help="Exercise multiple mapped endpoints (live)")
    s.add_argument("--query", default="γάλα")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_exercise)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except PosoKaneiError as e:
        print(f"API error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

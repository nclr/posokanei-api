"""Pure helpers: availability + multi-product basket cost by supermarket."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class Availability:
    """Whether a product is stocked (has a price) at a retailer."""

    product_id: Optional[str]
    product_name: str
    retailer: str
    available: bool
    price: Optional[float] = None
    status: str = "unknown"  # yes | no | unknown
    country: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BasketItemResult:
    query: str
    product_id: Optional[str]
    product_name: str
    missing: bool
    prices_by_retailer: dict[str, Optional[float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetailerTotal:
    retailer: str
    total: Optional[float]
    complete: bool
    priced_count: int
    missing_count: int
    missing_items: list[str] = field(default_factory=list)
    line_items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BasketComparison:
    items: list[BasketItemResult]
    retailers: list[RetailerTotal]
    cheapest: Optional[str] = None
    cheapest_total: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "retailers": [r.to_dict() for r in self.retailers],
            "cheapest": self.cheapest,
            "cheapest_total": self.cheapest_total,
        }


def _retailer_prices_map(product: Mapping[str, Any]) -> dict[str, float]:
    """Extract retailer_id -> shelf price from a product payload."""
    out: dict[str, float] = {}
    for entry in product.get("retailer_prices") or []:
        rid = entry.get("retailer")
        price = entry.get("price")
        if rid is None or price is None:
            continue
        try:
            out[str(rid)] = float(price)
        except (TypeError, ValueError):
            continue
    # Fallback: listed in retailers without price → skip (unknown amount)
    return out


def price_at_retailer(product: Mapping[str, Any], retailer: str) -> Optional[float]:
    """Return shelf price for retailer, or None if not available."""
    return _retailer_prices_map(product).get(retailer)


def is_available(
    product: Mapping[str, Any],
    retailer: str,
    *,
    require_price: bool = True,
) -> Availability:
    """
    Report whether product is available at a supermarket chain.

    - yes: retailer appears with a numeric price (or in retailers[] if require_price=False)
    - no: product known but retailer absent
    - unknown: product missing / no id
    """
    pid = product.get("id")
    name = str(product.get("name") or product.get("query") or "")
    if product.get("missing") or not pid:
        return Availability(
            product_id=pid,
            product_name=name,
            retailer=retailer,
            available=False,
            price=None,
            status="unknown",
        )

    prices = _retailer_prices_map(product)
    if retailer in prices:
        return Availability(
            product_id=str(pid),
            product_name=name,
            retailer=retailer,
            available=True,
            price=prices[retailer],
            status="yes",
            country=_country_for(product, retailer),
        )

    retailers = {str(r) for r in (product.get("retailers") or [])}
    if not require_price and retailer in retailers:
        return Availability(
            product_id=str(pid),
            product_name=name,
            retailer=retailer,
            available=True,
            price=None,
            status="yes",
        )

    return Availability(
        product_id=str(pid),
        product_name=name,
        retailer=retailer,
        available=False,
        price=None,
        status="no",
    )


def _country_for(product: Mapping[str, Any], retailer: str) -> Optional[str]:
    for entry in product.get("retailer_prices") or []:
        if entry.get("retailer") == retailer:
            return entry.get("country")
    return None


def collect_retailer_ids(
    products: Sequence[Mapping[str, Any]],
    *,
    country: Optional[str] = "GR",
    only: Optional[Iterable[str]] = None,
) -> list[str]:
    """Union of retailer ids appearing on products, optionally filtered by country."""
    only_set = set(only) if only is not None else None
    found: set[str] = set()
    for product in products:
        for entry in product.get("retailer_prices") or []:
            rid = entry.get("retailer")
            if not rid:
                continue
            rid = str(rid)
            if only_set is not None and rid not in only_set:
                continue
            if country is not None:
                c = entry.get("country")
                if c is not None and c != country:
                    continue
            found.add(rid)
        if country is None:
            for r in product.get("retailers") or []:
                rid = str(r)
                if only_set is None or rid in only_set:
                    found.add(rid)
    return sorted(found)


def compare_basket(
    products: Sequence[Mapping[str, Any]],
    *,
    retailers: Optional[Sequence[str]] = None,
    country: Optional[str] = "GR",
    require_complete: bool = False,
) -> BasketComparison:
    """
    Total a basket of products across supermarket chains.

    For each retailer, sum prices of items that have a price there.
    Incomplete baskets (missing items) get complete=False and missing_items listed.
    If require_complete=True, total is None unless every item is priced.
    """
    items: list[BasketItemResult] = []
    price_maps: list[dict[str, float]] = []

    for product in products:
        q = str(product.get("query") or product.get("name") or product.get("id") or "")
        missing = bool(product.get("missing") or not product.get("id"))
        pmap = {} if missing else _retailer_prices_map(product)
        # filter country
        if country is not None and not missing:
            filtered: dict[str, float] = {}
            for entry in product.get("retailer_prices") or []:
                if entry.get("country") not in (None, country):
                    continue
                rid = entry.get("retailer")
                price = entry.get("price")
                if rid is not None and price is not None:
                    try:
                        filtered[str(rid)] = float(price)
                    except (TypeError, ValueError):
                        pass
            pmap = filtered
        price_maps.append(pmap)
        items.append(
            BasketItemResult(
                query=q,
                product_id=product.get("id"),
                product_name=str(product.get("name") or q),
                missing=missing,
                prices_by_retailer={k: v for k, v in pmap.items()},
            )
        )

    if retailers is None:
        retailer_ids = collect_retailer_ids(products, country=country)
    else:
        retailer_ids = list(retailers)

    totals: list[RetailerTotal] = []
    for rid in retailer_ids:
        line_items: list[dict[str, Any]] = []
        missing_names: list[str] = []
        total = 0.0
        priced = 0
        for item, pmap in zip(items, price_maps):
            price = pmap.get(rid)
            if price is None:
                missing_names.append(item.product_name)
                line_items.append(
                    {
                        "product_id": item.product_id,
                        "name": item.product_name,
                        "price": None,
                        "available": False,
                    }
                )
            else:
                priced += 1
                total += price
                line_items.append(
                    {
                        "product_id": item.product_id,
                        "name": item.product_name,
                        "price": price,
                        "available": True,
                    }
                )
        missing_count = len(missing_names)
        complete = missing_count == 0 and not any(i.missing for i in items)
        if require_complete and not complete:
            total_val: Optional[float] = None
        elif priced == 0:
            total_val = None
        else:
            total_val = round(total, 4)

        totals.append(
            RetailerTotal(
                retailer=rid,
                total=total_val,
                complete=complete,
                priced_count=priced,
                missing_count=missing_count,
                missing_items=missing_names,
                line_items=line_items,
            )
        )

    # Sort: complete baskets first, then by total ascending (None last)
    def sort_key(r: RetailerTotal) -> tuple:
        return (
            0 if r.complete else 1,
            r.total if r.total is not None else float("inf"),
            r.retailer,
        )

    totals.sort(key=sort_key)

    cheapest = None
    cheapest_total = None
    for r in totals:
        if r.complete and r.total is not None:
            cheapest = r.retailer
            cheapest_total = r.total
            break
    if cheapest is None:
        # fallback: best partial total by priced_count then total
        partial = [
            r for r in totals if r.total is not None and r.priced_count > 0
        ]
        if partial:
            partial.sort(key=lambda r: (-r.priced_count, r.total or float("inf")))
            cheapest = partial[0].retailer
            cheapest_total = partial[0].total

    return BasketComparison(
        items=items,
        retailers=totals,
        cheapest=cheapest,
        cheapest_total=cheapest_total,
    )

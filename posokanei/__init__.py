"""PosoKanei.gov.gr public API client and basket helpers."""

from .basket import (
    Availability,
    BasketComparison,
    BasketItemResult,
    RetailerTotal,
    compare_basket,
    is_available,
    price_at_retailer,
)
from .client import PosoKaneiClient, PosoKaneiError, ProductPage

__all__ = [
    "Availability",
    "BasketComparison",
    "BasketItemResult",
    "PosoKaneiClient",
    "PosoKaneiError",
    "ProductPage",
    "RetailerTotal",
    "compare_basket",
    "is_available",
    "price_at_retailer",
]

__version__ = "0.1.0"

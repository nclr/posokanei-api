# PosoKanei API Map

**Base URL:** `https://api.posokanei.gov.gr`  
**Frontend:** `https://posokanei.gov.gr` (Flutter web, package `PosoKanei` v1.1.10)  
**Discovery date:** 2026-07-14  
**Discovery method:** Loaded frontend via kepik egress proxy (Greek IP, Athens); reverse-engineered public routes from `main.dart.js` and live HTTP exercise. No OpenAPI/docs published (404 on `/docs`, `/openapi.json`).

## Geo / access

| Path | Result |
|------|--------|
| Direct (non-GR egress) to `posokanei.gov.gr` / `api.posokanei.gov.gr` | Often **403** |
| Via kepik egress proxy (GR IP) | **200** on site and API |

Always set `HTTP_PROXY` / `HTTPS_PROXY` from `~/.config/nomad/egress-proxy.env` (see egress-proxy skill).

## Auth

Public read APIs require **no API key**. Forms endpoints accept JSON POSTs (may involve reCAPTCHA on the web UI; not exercised as a write workflow).

Recommended browser-like headers:

- `Accept: application/json`
- `Origin: https://posokanei.gov.gr`
- `Referer: https://posokanei.gov.gr/`
- `User-Agent: <modern browser>`

## Endpoints

### Meta

| Method | Path | Query | Returns |
|--------|------|-------|---------|
| `GET` | `/meta/stats` | — | `total_products`, `active_products`, `retailers[]` (ids), `retailer_count`, `products_on_discount`, `timestamp` |
| `GET` | `/meta/retailers` | `countries` (e.g. `GR`, or multi) | `{ count, retailers: [{ id, name, country, logo_url, website }] }` |
| `GET` | `/meta/categories` | — | `{ count, categories: [{ category_id, category_name, name_en, depth, parent_id, image_url, product_count }] }` |
| `GET` | `/meta/categories/tree` | `include_counts` (bool str), `include_hidden` (bool str) | `{ total_categories, root_count, tree: [nested category nodes with children, vat_rates, …] }` |

### Products — list / search

| Method | Path | Params / body | Returns |
|--------|------|---------------|---------|
| `GET` | `/products` | Query: `page`, `page_size`, `sort_by` (`name`, `price_asc`, …), `sort_order` (`asc`/`desc`), `category` (category id), `countries` (e.g. `GR`), optional `is_international` | Paginated product list (see schema below) |
| `POST` | `/products/search` | JSON body: `page`, `page_size`, `sort_by`, `sort_order`, optional `title` (search text), optional `ids` (array of product ids) | Same pagination envelope |

**Pagination envelope** (list + search):

```json
{
  "products": [ /* ProductSummary */ ],
  "total": 268,
  "page": 1,
  "page_size": 5,
  "total_pages": 54,
  "has_next": true,
  "has_prev": false,
  "query_time_ms": 12
}
```

### Products — detail / barcode / competitors

| Method | Path | Query | Returns |
|--------|------|-------|---------|
| `GET` | `/products/{id}` | `countries` (e.g. `GR`), `include_tax` (`true`/`false`), `sort_retailers` (`asc`), optional `include_history` (`true`), optional `price_type` (`unit_price` when history) | Full product + `retailer_prices[]`; if history requested, `history.daily_prices` per retailer |
| `GET` | `/products/barcode/{barcode}` | `countries`, `include_tax` | Same as product detail. Barcode: 8/12/13 digits. **Rate-limited** (HTTP 429). |
| `GET` | `/products/{id}/competitors` | `include_tax`, optional `retailer` | `{ id, product_name, category_*, competitors: [products with prices], total_competitors }` |

### Static assets (on API host)

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/images/product/{id}` | Product image bytes (optional `?v=` version) |
| `GET` | `/images/category/{id}` | Category image |
| `GET` | `/images/retailer/{retailer_id}` | Retailer logo SVG/PNG |

### Forms (write; web UI)

| Method | Path | Body (from app) | Notes |
|--------|------|-----------------|-------|
| `POST` | `/forms/contact` | contact form fields | Not required for price comparison |
| `POST` | `/forms/suggest-link` | suggest-link fields | Not required for price comparison |

### Frontend-only routes (not API)

- `/` home, `/privacy-policy` — SPA routes on `posokanei.gov.gr`

## Product object (key fields)

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | Stable product id (hex) |
| `name` | string | Display name (el) |
| `brand` | string \| null | Brand |
| `category` / `subcategory` | string | Labels |
| `category_ids` | string[] | Category id path |
| `unit` / `unit_quantity` | string / number | e.g. `L`, `1.0` |
| `image_url` | string | Absolute or API-relative |
| `price_stats` | object | `min_price`, `max_price`, `avg_price`, `retailer_count`, `min_unit_price` |
| `retailers` | string[] | Retailer ids that carry the product |
| `retailer_prices` | array | See below |
| `available_countries` | string[] | e.g. `["GR"]` |
| `private_label` | bool | Private label flag |

**`retailer_prices[]` entry:**

| Field | Type |
|-------|------|
| `retailer` | string id (`sklavenitis`, `ab_vasilopoulos`, …) |
| `retailer_display_name` | string |
| `price` | number (EUR, shelf price) |
| `price_normalized` | number (often unit price) |
| `is_discount` | bool |
| `discount_percentage` | number \| null |
| `last_updated` | ISO date string |
| `country` | e.g. `GR` |

## Greek retailers (subset of `meta/stats` + `meta/retailers`)

Common GR chain ids: `ab_vasilopoulos`, `galaxias`, `sklavenitis`, `mymarket`, `masoutis`, `kritikos`, `halkiadakis`, `market_in`, `lidl`, `synka`.  
EU chains also present (CY/ES/IT/BE/…). Client helpers default to `country=GR`.

## Coverage limits

- Map covers **public client-facing** routes used by the official Flutter web app.
- Undocumented admin/internal routes may exist but were not observed in the web client.
- Barcode lookup is rate-limited; prefer product id / search for bulk work.
- No published OpenAPI; field names taken from live JSON + minified client.

## Client alignment

This map is the source of truth for package `posokanei` in this repo:

| Map operation | Client / CLI |
|---------------|--------------|
| Search / list | `PosoKaneiClient.search`, `list_products` / `posokanei search` |
| Product detail + prices | `get_product` / `posokanei product` |
| Availability at chain | `is_available` / `posokanei available` |
| Basket cost by supermarket | `compare_basket` / `posokanei basket` |
| Meta | `stats`, `retailers`, `categories` / `posokanei meta` |
| Competitors | `competitors` / `posokanei competitors` |
| Barcode | `by_barcode` / `posokanei barcode` |

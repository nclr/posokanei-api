# Discovery notes (2026-07-14)

## Method

1. Loaded `https://posokanei.gov.gr` **through kepik egress proxy** (direct non-GR egress returned **HTTP 403**).
2. Identified Flutter web app (`main.dart.js`, package version **1.1.10** / build 11 from `version.json`).
3. Extracted path string literals and request construction (`lc` = GET, `r_` = POST) from minified Dart JS.
4. Confirmed each route with live HTTP via proxy; recorded response shapes in `API_MAP.md` / `api_map.json`.

## Hosts

| Host | Role |
|------|------|
| `posokanei.gov.gr` | SPA frontend, CSP `connect-src` includes `https://api.posokanei.gov.gr` |
| `api.posokanei.gov.gr` | JSON API + product/category/retailer images |

## Endpoints observed in client (complete set from `main.dart.js`)

Public API paths found as string literals in the web client:

- `GET /meta/stats`
- `GET /meta/retailers`
- `GET /meta/categories`
- `GET /meta/categories/tree`
- `GET /products`
- `POST /products/search`
- `GET /products/{id}`
- `GET /products/{id}/competitors`
- `GET /products/barcode/{barcode}`
- `POST /forms/contact`
- `POST /forms/suggest-link`
- Image GETs: `/images/product/{id}`, `/images/category/{id}`, `/images/retailer/{id}`

SPA-only (frontend router, not API): `/`, `/privacy-policy`.

No OpenAPI/Swagger (`/docs`, `/openapi.json` → 404).

## Rate limits / quirks

- Barcode lookup returns **429** under burst load (“Too many barcode search requests”).
- Search/list return current shelf prices per retailer; history is opt-in via `include_history=true` on product detail.
- Some products appear on few Greek chains; basket “complete” totals require every item to have a price at that retailer.

## Coverage honesty

This inventory is **every public route referenced by the official web client** at discovery time. Server-only or mobile-only routes may exist outside this set and are out of scope unless observed in public traffic.

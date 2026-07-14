# posokanei-api

Python client, CLI, and API map for the public **[PosoKanei](https://posokanei.gov.gr)** supermarket price comparison API (`https://api.posokanei.gov.gr`).

Greek government price comparison across major supermarket chains (and some EU retailers). The public site is often **geo-restricted** (HTTP 403 from non-GR egress). This project is designed to run through the **kepik egress proxy** so traffic exits with a Greek IP.

## Remotes

| Host | URL |
|------|-----|
| Gitea | `https://gitea.cluster-kepik.nclr.eu/ai/posokanei-api` |
| GitHub | `https://github.com/nclr/posokanei-api` |
| Local path | `/home/giorgos/posokanei-api` |

## Quick start (with Greek egress)

```bash
set -a
source "$HOME/.config/nomad/agent-sandbox.env"   # optional nomad
source "$HOME/.config/nomad/egress-proxy.env"    # sets HTTP(S)_PROXY
set +a

cd /home/giorgos/posokanei-api
python3 -m pip install -e . --user   # or: PYTHONPATH=. 

# Search
python3 -m posokanei search "γάλα" --page-size 5

# Product detail + per-store prices
python3 -m posokanei product <product_id>

# Availability at a chain
python3 -m posokanei available "coca cola" sklavenitis

# Basket cost comparison across supermarkets
python3 -m posokanei basket "γάλα" "ψωμί" "αυγά" -v

# Meta
python3 -m posokanei meta stats
python3 -m posokanei meta retailers

# Exercise several mapped endpoints (verification)
python3 -m posokanei exercise
```

Environment: `HTTP_PROXY` / `HTTPS_PROXY` (and lowercase variants) are honored by the client.

## Library usage

```python
from posokanei import PosoKaneiClient, compare_basket, is_available

client = PosoKaneiClient()
page = client.search("ρύζι", page_size=5)
product = client.get_product(page.products[0]["id"])

print(is_available(product, "sklavenitis"))

products = client.resolve_products(["γάλα πλήρες 1lt", "ψωμί του τοστ"])
cmp = compare_basket(products, country="GR")
for r in cmp.retailers:
    print(r.retailer, r.total, "complete" if r.complete else "partial")
print("cheapest", cmp.cheapest, cmp.cheapest_total)
```

## API map

Full documentation of discovered endpoints:

- [docs/API_MAP.md](docs/API_MAP.md)
- [docs/api_map.json](docs/api_map.json) (machine-readable)
- [docs/DISCOVERY.md](docs/DISCOVERY.md) (how endpoints were found; coverage limits)

Example multi-product file: [examples/sample_basket.txt](examples/sample_basket.txt).

Core operations:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/meta/stats` | Catalog stats |
| GET | `/meta/retailers` | Chains |
| GET | `/meta/categories` | Categories |
| GET | `/meta/categories/tree` | Category tree |
| GET | `/products` | List / filter by category |
| POST | `/products/search` | Search by title or ids |
| GET | `/products/{id}` | Detail + prices (+ optional history) |
| GET | `/products/barcode/{code}` | Barcode lookup (rate-limited) |
| GET | `/products/{id}/competitors` | Similar products |

## Tests

```bash
# Pure unit tests (no network)
python3 -m unittest discover -s tests -v

# Live (requires egress proxy)
set -a; source "$HOME/.config/nomad/egress-proxy.env"; set +a
python3 -m posokanei exercise
python3 -m posokanei basket "COCA-COLA Original Taste 1lt" "γάλα" -v
```

## Skills

Grok skill for future agents: `~/.grok/skills/posokanei-api/SKILL.md` (mirrored under `.grok/skills/posokanei-api/` in this repo). Loads egress-proxy first, then points at this client.

## License

MIT — API data belongs to the Greek public PosoKanei service; use responsibly and respect rate limits.

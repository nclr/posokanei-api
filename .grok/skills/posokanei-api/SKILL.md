---
name: posokanei-api
description: >
  Call the public posokanei.gov.gr / api.posokanei.gov.gr supermarket price
  APIs via the kepik Greek egress proxy. Use when the user mentions PosoKanei,
  posokanei, πόσο κάνει, Greek supermarket price comparison, basket cost across
  chains, or product availability at sklavenitis/ab/masoutis/lidl/etc. Triggers:
  "posokanei", "compare supermarket prices Greece", "/posokanei".
metadata:
  short-description: "PosoKanei price API + basket compare"
---

# PosoKanei API (Greece supermarket prices)

## Facts

| Item | Value |
|------|--------|
| Frontend | `https://posokanei.gov.gr` |
| API | `https://api.posokanei.gov.gr` |
| Project | `/home/giorgos/posokanei-api` |
| Gitea | `https://gitea.cluster-kepik.nclr.eu/ai/posokanei-api` |
| GitHub | `https://github.com/nclr/posokanei-api` |
| API map | `docs/API_MAP.md`, `docs/api_map.json` |
| Geo | Direct egress often **403**; use **egress-proxy** (Greek IP) |

**Never** commit proxy passwords or tokens. Always compose with the existing **egress-proxy** skill.

## Step 1 — load Greek egress

```bash
set -a
source "$HOME/.config/nomad/agent-sandbox.env"   # if using nomad tools
source "$HOME/.config/nomad/egress-proxy.env"    # HTTP(S)_PROXY
set +a
```

Smoke: `curl -sS -x "$https_proxy" -I https://posokanei.gov.gr | head -5` → expect 200.  
If env missing: run `~/.grok/skills/egress-proxy/scripts/refresh-env.sh`.

## Step 2 — run the shipped client

```bash
cd /home/giorgos/posokanei-api
export PYTHONPATH=/home/giorgos/posokanei-api

# Search / list
python3 -m posokanei search "γάλα" --page-size 5

# Detail + prices by store
python3 -m posokanei product <product_id>

# Is it in this supermarket?
python3 -m posokanei available "coca cola 1lt" sklavenitis

# Basket: total cost at every chain that carries the items
python3 -m posokanei basket "γάλα" "ψωμί" "αυγά" -v
python3 -m posokanei basket -f basket.txt --json

# Meta + multi-endpoint exercise
python3 -m posokanei meta stats
python3 -m posokanei exercise
```

Library:

```python
from posokanei import PosoKaneiClient, compare_basket, is_available
client = PosoKaneiClient()
products = client.resolve_products(["γάλα", "ρύζι"])
print(compare_basket(products).to_dict())
```

## Step 3 — key endpoints (see full map in repo)

- `POST /products/search` body `{title, page, page_size, sort_by, sort_order}`
- `GET /products/{id}?countries=GR&include_tax=true`
- `GET /meta/retailers?countries=GR`
- `GET /products/{id}/competitors`

Retailer ids (GR): `sklavenitis`, `ab_vasilopoulos`, `mymarket`, `masoutis`, `galaxias`, `lidl`, `kritikos`, `halkiadakis`, `market_in`, `synka`.

## Related skills

- **egress-proxy** — mandatory for access from this host
- **gitea-login** — push/pull the Gitea mirror

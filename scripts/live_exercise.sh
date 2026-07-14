#!/usr/bin/env bash
# Live exercise of mapped APIs via kepik egress proxy. Writes logs for verification.
set -euo pipefail

SCRATCH="${SCRATCH:-/tmp/grok-goal-93a9412911f1/implementer}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$SCRATCH"

set -a
# shellcheck disable=SC1090
source "${HOME}/.config/nomad/egress-proxy.env"
set +a

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "=== exercise endpoints ===" | tee "$SCRATCH/api-map-exercise.log"
python3 -m posokanei exercise --json 2>&1 | tee -a "$SCRATCH/api-map-exercise.log"

echo "=== basket compare ===" | tee "$SCRATCH/basket-compare.out"
python3 -m posokanei basket \
  -f "$ROOT/examples/sample_basket.txt" \
  -v 2>&1 | tee -a "$SCRATCH/basket-compare.out"

echo "=== availability ===" | tee -a "$SCRATCH/basket-compare.out"
python3 -m posokanei available "COCA-COLA Original Taste 1lt" sklavenitis 2>&1 | tee -a "$SCRATCH/basket-compare.out"

echo "Done. Logs under $SCRATCH"

# ML-CHALLENGE — Term 3

Standalone mirror of the ML stages (1–3) from the main `dotin` repository. Stats-challenge content is intentionally excluded.

## Structure

- `stage-1-kiarash-akbari/` — Data Factory: NYC 311 noise-complaint pipeline (API ingestion, validation, quarantine, cleaning, outputs, manifest).
- `stage-2-kiarash-akbari/` — Database Performance: Olist PostgreSQL schema, analytical views, snapshots, and query optimization.
- `stage-3-kiarash-akbari/` — Machine Learning: cost-sensitive credit-default prediction with evidence-driven threshold selection.

All three stage folders are synced from `dotin` (branch `stage-3/setup` / merged to `main`).

## Stage 3 highlights

- Cost-sensitive threshold selection (12:1 FN:FP matrix), achieving a 54.1% cost reduction vs. the "flag nobody" baseline.
- Full missingness evidence (sentinel spikes, co-missingness, two-proportion test).
- Leakage audit for all engineered features.

## Setup

See each stage folder's own `README.md` / `requirements.txt` for stage-specific setup. A shared venv under `stage-1-kiarash-akbari/.venv` is recommended.

## Note

This repository is a read-only mirror of the ML work; active development happens in `dotin`.
# Research: Phase 2 — Logistics, Macro & Feedstock

## Decision

- Chosen: Extend the existing `agents/data_fetcher.py` and `agents/normalizer.py` ingestion pipeline to support logistics and macro feeds using established normalization and source health conventions.
- Rationale: The current repository already supports primary/fallback ingestion, USD conversion, quality flags, and source health updates. Reusing that infrastructure reduces risk and keeps new feed types aligned with existing contracts.
- Alternatives considered:
  - Create separate freight and macro ingestion pipelines: rejected because it would duplicate health, normalization, and persistence logic.
  - Store macro feed data in a dedicated table separate from `price_history`: rejected in Phase 2 to preserve a unified normalized repository contract and leverage existing `SourceType.MACRO` semantics.
  - Treat all logistics and macro inputs as raw payload archives only: rejected because downstream forecasting requires normalized USD values and confidence metadata.

## Rationale

- Existing product and technical conventions favor data contract consistency. New feeds should fit into the same health/fallback model rather than introduce ad hoc exceptions.
- Freight data is conceptually different from cotton price records, so it should remain logically separable as a logistics repository while still using the same ingestion health model.
- Macro feeds are best represented as normalized numeric records with `SourceType.MACRO` and commodity labels for values like `usd_inr`, `usd_cny`, `oil_spot`, and `electricity`.
- The 48-hour stale threshold was selected to allow daily sources some publication latency while still surfacing degraded signal quality promptly.

## Alternatives considered

1. **Dedicated macro feed table**
   - Pros: clear separation of macro inputs.
   - Cons: extra schema/tables, separate persistence logic, more consumer complexity.
   - Decision: keep macro feed persistence aligned with normalized price history in Phase 2.

2. **Separate freight ingestion service**
   - Pros: isolate logistics domain.
   - Cons: duplicates fallback logic and source health semantics.
   - Decision: extend the existing `DataFetcher` instead.

3. **Only persist live primary data, ignore fallback records**
   - Pros: simpler pipeline.
   - Cons: removes resilience and breaks the product requirement for fallback activation.
   - Decision: preserve fallback provenance and record quality flags explicitly.

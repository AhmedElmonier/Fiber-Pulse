<!--
Sync Impact Report:
Version change: none -> 1.0.0
Modified principles: placeholders -> defined operational, forecasting, transparency, interface, delivery principles
Added sections: Operational Constraints, Development Workflow
Removed sections: none
Templates requiring updates: ✅ .specify/templates/plan-template.md (generic alignment, no edit required), ✅ .specify/templates/spec-template.md (generic alignment, no edit required), ✅ .specify/templates/tasks-template.md (generic alignment, no edit required)
Follow-up TODOs: none
-->

# FiberPulse AI Constitution

## Core Principles

### I. Data Integrity as First-Class Product
All inputs are treated as contracts. Every source MUST be ingested with explicit health state, fallback behavior, and USD normalization before persistence. Stale or dead feeds MUST trigger a confidence decay path rather than allowing silent precision.

### II. Baseline-First Forecasting
The system MUST deploy a simple, explainable baseline forecast before promoting any complex model. Advanced models like TFT MUST be gated by an objective promotion rule and only enabled after measurable improvement.

### III. Transparency and Confidence
Every forecast MUST expose interval bounds, confidence status, and decay rationale. The system MUST avoid presenting raw point forecasts as definitive predictions and MUST communicate uncertainty to operational users.

### IV. Operationally Actionable Delivery
User-facing value MUST be delivered through clear operational workflows, not generic dashboards. The product MUST support explicit commands, alert summaries, manual data ingestion, and feedback-driven action.

### V. Incremental, Maintainable Delivery
Implementation MUST proceed in guarded phases: foundation, data ingestion, baseline AI, interface, and model upgrade. Code MUST remain modular, testable, documented, and changes to core contracts MUST be reviewed before acceptance.

## Operational Constraints

- Technology MUST align to Python 3.12, Poetry-managed dependencies, PostgreSQL with pgvector, async fetch pipelines, and environment-managed secrets.
- All commodity prices MUST be normalized to USD before storage; original local values MAY be retained for audit and traceability.
- Scheduling and market cadence MUST operate in Africa/Cairo timezone for all production jobs and alerts.
- The initial delivery scope MUST be constrained to Telegram-based operational reporting, chart generation, and alerting; no broad UI platform is required for v1.
- Model promotion MUST be governed by a defined performance gate and fallback behavior; no advanced model is production-active without passing the baseline improvement threshold.

## Development Workflow

- Every change MUST reference one or more constitution principles in the PR description.
- Phase boundaries MUST be validated before moving from data scaffolding to forecasting, from baseline forecast to interface, and from interface to model promotion.
- New data contracts, schema changes, and model gates MUST be documented in plan.md and traced to measurable outcomes in the PRD.
- All PRs MUST include tests for new behavior, especially around data ingestion, model evaluation, alert suppression, and Telegram command flows.
- Architectural changes that affect data health, model governance, or operational delivery MUST trigger a constitution review and update.

## Governance

This constitution is the authoritative guide for architecture, data quality, and delivery decisions in FiberPulse AI. All development work MUST comply with these principles.

- Amendments require updating this file, recording the rationale, and obtaining owner acknowledgment before acceptance.
- Compliance review MUST occur at each phase transition and before production deployment.
- Exceptions to this constitution are not permitted without explicit governance justification in the project plan.
- The constitution MUST be referenced by all task planning, code review, and deployment checklists.

**Version**: 1.0.0 | **Ratified**: 2026-03-28 | **Last Amended**: 2026-03-28

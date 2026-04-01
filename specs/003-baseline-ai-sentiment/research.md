# Research: Phase 3 — Baseline AI + Sentiment

## Decision

- **Sentiment Engine**: Use a hybrid approach combining a curated cotton-market keyword list with VADER/TextBlob for polarity.
- **Baseline Model**: XGBoost using a recursive (step-by-step) forecasting approach with a 30-day sliding window of features.
- **Confidence Intervals**: Implement Quantile Regression within XGBoost (multi-output or separate models for 0.05, 0.5, and 0.95 quantiles) to provide interval bounds.
- **CLI Framework**: Use `click` for the `fiberpulse` command-line interface.

## Rationale

- **Sentiment**: Keyword-based scoring is highly explainable and requires no GPU resources for inference, making it ideal for a Phase 3 baseline.
- **XGBoost**: It handles non-linear relationships and missing data well, which are common in market datasets. It is faster to train and iterate on than the Phase 5 TFT model.
- **Quantile Regression**: Unlike simple standard deviation assumptions, quantile regression provides non-symmetric intervals that better reflect market risk.
- **Click**: Industry standard for Python CLIs, providing easy subcommand nesting and parameter validation.

## Alternatives considered

- **Recursive vs Direct Forecast**: Direct forecast (predicting N days ahead in one jump) was rejected because it requires separate models for each horizon, increasing complexity. Recursive forecasting allows a single model to project forward.
- **Standard Deviation Intervals**: Rejected because market price distributions are often skewed; quantiles provide a more accurate representation of uncertainty.
- **FinBERT (Phase 3)**: Rejected for this phase to adhere to the "Baseline-First" principle. FinBERT will be evaluated in Phase 5.

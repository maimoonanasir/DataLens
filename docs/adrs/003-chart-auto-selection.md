# ADR-003: Chart Auto-Selection Algorithm

**Date:** 2026-05-04
**Status:** Accepted
**Deciders:** Haider Ahmad

---

## Context

DataLens must automatically select 4–6 "meaningful" chart types from any uploaded CSV without user configuration. The algorithm receives a list of `ColumnProfile` objects and must decide:

1. Which chart types to include
2. Which columns to use for each chart
3. What aggregation to apply
4. In what order to display them

The spec requires a mix of chart types appropriate to column types: bar for categoricals, line/area for time series, histograms for numeric distributions, scatter for correlations.

For the Online Retail II dataset (our primary test case), the expected output is:
- A line chart of revenue over time (InvoiceDate × Price/Quantity)
- A bar chart of top countries by revenue (Country × Price)
- A horizontal bar of top products (Description × Quantity)
- A histogram of quantity distribution
- A scatter plot of Price vs Quantity

---

## Options Considered

**Option A — Fixed rule-based selection (if datetime → line, if categorical → bar, etc.)**
Simple priority queue of rules. Predictable and testable. May produce redundant charts (two bar charts if there are two categoricals of similar cardinality). Does not account for column interest/variance.

**Option B — Statistical scoring (entropy, variance ratio, mutual information)**
Rank all column pairs by statistical interest and select the top-k. More sophisticated but requires loading the full dataset into memory for scoring, which is slow for 1M rows and adds complexity with no proportional gain for typical business datasets.

**Option C — Hybrid: fixed rules with tie-breaking heuristics**
Apply chart type rules by column dtype, use heuristics (column name keywords, cardinality ratios, coefficient of variation) to break ties between columns of the same type. The selection algorithm runs in O(n_columns) without reading the data — only the cached profile is needed.

---

## Decision

We chose **Option C — Hybrid rule-based selection with heuristics**, implemented in `backend/app/services/chart_selector.py`.

The algorithm runs in this priority order:

| Priority | Chart type | Trigger condition | Column selection |
|----------|-----------|-------------------|-----------------|
| 1 | Line | ≥1 datetime column | First datetime × revenue-keyword numeric (sum) |
| 2 | Bar | ≥1 categorical (5–50 unique), ≥1 numeric | Mid-cardinality categorical × revenue numeric (sum) |
| 3 | Horizontal bar | Second categorical, ≥1 numeric | Second categorical × numeric (sum, top-15) |
| 4 | Histogram | ≥1 numeric | Numeric with highest coefficient of variation |
| 5 | Scatter | ≥2 numerics | Price-keyword × Quantity-keyword pair |
| 6 | Count bar | Low-cardinality categorical (≤10 unique) | Count aggregation |

Key heuristics used:

- **Column name keywords** determine priority within each type: `price`, `amount`, `revenue`, `value` → preferred for Y-axis aggregation; `quantity`, `qty` → scatter pair partner.
- **Mid-cardinality preference** for bar charts: columns with 5–50 unique values produce readable axis labels. Columns with 1–4 values are reserved for slot 6 (count bars).
- **Coefficient of variation** (std/mean) determines histogram priority: highly variable columns (like Quantity, which ranges from -80 to 80,000 in Online Retail II) produce the most informative histograms.
- **Fallback histograms** are added if fewer than 4 charts were selected from the first 5 slots.

The algorithm caps output at 6 charts (`specs[:6]`).

---

## Trade-offs

**What we gave up:**
- Statistical optimality — a mutual-information scorer would find more interesting correlations
- User configurability — users cannot drag and re-order chart slots in the MVP
- Handling CSVs with only text columns (no numeric/datetime) — such datasets will generate only count-bar charts, which may be fewer than 4

**What we accepted:**
- The algorithm relies on English-language column name keywords. Non-English CSVs may not get optimal selections (e.g., a German CSV with `Menge` instead of `Quantity` will not trigger the scatter pair heuristic). Mitigation: the scatter pair falls back to `numerics[0], numerics[1]` if no keyword matches.
- The algorithm is column-type–deterministic: the same profile always produces the same chart set. This is a feature (predictability, testability) but means the user cannot "explore" different chart combinations without code changes.

**Future improvement:** Add a UI control on the Dashboard to let users swap one chart type for another, with the algorithm suggesting alternatives. This is deferred to post-MVP (see SPEC.md Section 9, Out of Scope).

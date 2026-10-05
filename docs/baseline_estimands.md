# Baseline estimands

This note was written before the cereals baseline was fit. It defines the objects in `configs/baseline_models.yaml`. It does not report a coefficient. Fitted numbers, once they exist, belong in `reports/results/baseline_models.json` and `reports/research_paper/baseline_findings.md`.

## Outcome and price

The outcome in the log-log models is `log(MOVE)`, the natural log of item movement. `MOVE` counts items. The transformation is defined only when movement is positive, so the log sample drops zero scans.

The price regressor is `log(PRICE / QTY)`, the natural log of the per-item bundle price, in log dollars per item. `PRICE` is the bundle total and `QTY` is the number of items in the bundle. It is not price per ounce.

In a log-log equation, β is the difference in log item movement associated with a one-unit difference in log unit price, after the controls and fixed effects included in that model. A one-unit log-price difference is a price ratio of e. The readable translation of a 10 percent price difference is

`exp(β × log(1.10)) − 1`,

the associated proportional difference in item movement. Under a constant-elasticity reading, β itself is an elasticity of movement with respect to unit price. In this project that reading is conditional on the specification. It is not a causal elasticity. Price is chosen by the chain, promotions move both price and movement, and the fixed effects do not block every demand shock that also moves the shelf price.

## Sample

The estimation sample is the cereals log sample: `OK = 1`, `PRICE > 0`, `QTY > 0`, and `MOVE > 0`. The fitter stops if the row count or the file hash disagrees with `reports/results/data_quality.json`. Absent UPC-store-weeks are not filled with zero. `SALE` codes `G` and `L` are not recoded.

The expected log sample at the time this note was written has 4,707,776 rows. That count is a check against the quality report, not a result of the regression.

## Controls, fixed effects, and clustering

| Model | What is held fixed | Variation that identifies the price coefficient |
| --- | --- | --- |
| M0 | an intercept | all price differences in the log sample |
| M1 | an intercept and `1{SALE in {B,C,S}}` | price differences among rows with the same promotion code |
| M2 product | a UPC effect | price differences for one UPC across stores and weeks |
| M2 product and store | additive UPC and store effects | price differences that are not a permanent product gap or a permanent store gap |
| M3 pair | a UPC-store effect | changes inside a store-product pair |
| M3 pair and week | a UPC-store effect and a week effect | within-pair changes that are not common to every cereal that week |
| M4 month | a UPC-store effect and a calendar-month effect | within-pair changes that are not a repeating month pattern |
| M4 year-month | a UPC-store effect and a year-month effect | within-pair changes that are not common inside that calendar month |
| M5 confirmatory | M3's fixed effects and the B/C/S indicator | the M3 variation that is not collinear with the coded promotion flag |

M5 is the confirmatory association in `configs/specifications.yaml`. The other rows are comparisons. A higher R-squared, or a more negative β, does not promote a comparison into the confirmatory model.

UPC-by-week effects are not estimated. They would absorb chainwide promotions of one UPC. Store-by-week effects are not estimated. They would absorb a category-wide store-week price shift. Week effects do not absorb a promotion that is specific to one UPC.

The promotion indicator equals 1 only for `SALE` in {B, C, S}. Blank weeks are not confirmed regular-price weeks. `G` and `L` stay in the reference group with the blanks. The promotion coefficient is the log movement difference associated with a coded promotion at a given unit price. It is not the total association of a promotion, because the price coefficient already holds the accompanying price difference.

Primary standard errors cluster by store. That allows arbitrary correlation across products and weeks inside a store, including serial correlation. It does not allow correlation across stores. With G store clusters, intervals use a Student t reference with G − 1 degrees of freedom. Week-clustered and two-way (store and week) standard errors are sensitivities. Two-way clustering can fail to be positive semidefinite; when it does, that standard error is not reported. Clustering is not an identification strategy.

The finite-sample factor is `G/(G−1) × (N−1)/(N−K)`. For two absorbed factors, K includes `n1 + n2 − 1` plus the slopes, which assumes the two-way graph is connected. That rank enters the standard error only.

## What is not claimed

- β is not the effect of an exogenous price change.
- No instrument is used. Average acquisition cost, lags, other-store prices, and price tier stay out.
- `log(1 + MOVE)` is not estimated. A coefficient on that transformation is not an exact elasticity.
- A level regression of `MOVE` on unit price, if reported, is in items per dollar. Translating it at the median price and median movement is a local reading, not the log-log estimand.
- PPML, if it converges, estimates an elasticity of the conditional mean. It answers the zero-sales problem only when a zero-movement row still has a positive unit price. If that count is zero, PPML on the log sample is a functional-form comparison, not a correction for selection.
- Restoring `OK = 0` rows is a sign check required by the analysis plan. It does not replace the log sample. Zero prices are not restored into a log-price regression, because the log is undefined.

## Hypotheses already on record

1. The confirmatory cereals coefficient is negative. A non-negative estimate is reported and is not searched away.
2. On the same rows, the pooled OLS coefficient differs from the confirmatory coefficient. The comparison is two-sided. It is not a Hausman test of exogeneity.
3. The oatmeal confirmatory coefficient has the same sign as cereals. Oatmeal is not part of this cereals baseline.

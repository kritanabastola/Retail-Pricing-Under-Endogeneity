# Analysis plan

Phase 1 profiled the three movement files and froze the specifications below. The cereals baseline was fit later from those specifications. Each later phase stops for permission. The fit does not reopen the confirmatory equation.

## When an estimator is rejected

These rules are fixed before coefficients are seen.

- The main specification is not an instrumental-variables estimator. IV is rejected unless a written assignment mechanism and exclusion argument exist before the second stage is computed. They do not.
- A fixed-effects price coefficient is not interpreted as a within-pair association if fewer than 20 percent of UPC-store pairs in the log sample have any truncated price change. The cereals screen is 85.5 percent, so this trigger is not met. It remains in force for every later sample.
- Do not add fixed effects, instruments, or sample cuts after seeing which coefficient is significant. The confirmatory equation is `configs/specifications.yaml`.
- Do not zero-fill the 32 missing cereal weeks or any other absent UPC-store-week.
- Do not recode `SALE` values `G` or `L` as promotions or as blanks. If reclassifying them flips the sign of β, report both versions and do not keep the significant one.
- If the sign of β flips when `OK = 0` rows are restored, or when zero-price rows are restored, report the flip. Do not select the version with the smaller p-value.
- The Phase 1 screen found no `PRICE` or `PROFIT` value in these three files that differs from its hexadecimal double by more than 0.0001. If a later extract disagrees, stop and reconcile. Do not choose the representation that changes significance.
- A counterfactual price outside the observed within-UPC-store range of unit prices is rejected.
- If store-clustered standard errors cannot be computed, say so. Do not substitute ordinary standard errors without labeling them.
- A first-stage F statistic is not evidence that an instrument is exogenous. A non-rejection of an overidentification test is not evidence that the instruments are valid, and that test is not used for a one-instrument model.

## Phase 2 — Cereals analysis file

The cereals UPC CSV and movement zip are already in gitignored `data/raw/` from the Phase 1 screen. Do not commit them. Phase 2 builds the analysis file. It does not refit the category choice and it does not estimate β.

1. Confirm the movement header against `MOVEMENT_COLUMNS`. Fail if it differs.
2. Decode `PRICE_HEX` and `PROFIT_HEX`. Tabulate absolute disagreements with the truncated fields. Do not choose a column because of a regression result.
3. Apply the accounting functions. Reconcile a sample of constructed revenue values to `PRICE * MOVE / QTY` and record any failures.
4. Merge UPC attributes. Write the unmatched-UPC audit. Do not drop unmatched rows silently.
5. Count duplicate UPC-store-week keys. Stop and document them if any exist.
6. Map weeks through `week_bounds`. Count weeks outside 1–399.
7. Build a store-tier file from a second reading of manual Part 6, and record stores with no zone.
8. Write an exclusion table: raw rows, `OK = 0`, nonpositive price, nonpositive quantity, zero movement, missing hex, duplicate keys. The log sample is the last row of that table.
9. Descriptive tables only: distributions of unit price and movement, share of rows with `SALE` in {B, C, S}, within-UPC-store price variation, and how much price variation sits within store, within UPC, and within week. No regression yet.

## Phase 3 — Pre-specified comparisons

The exploratory description in `docs/exploratory_analysis.md` was completed on 5 October 2026, before the estimators in this section. Those estimators were then fit on the cereals log sample. The results are `reports/results/baseline_models.json` and `reports/research_paper/baseline_findings.md`. The sample was not retuned after the coefficient was seen.

On the Phase 2 log sample, estimate the descriptive ladder and the confirmatory specification in `configs/specifications.yaml`. Cluster standard errors by store. Report economic magnitude (a 1 percent unit-price difference and the associated movement difference) beside statistical precision. Do not add fixed effects after seeing the coefficient.

## Phase 4 — Identification and falsification

The cereals baseline did not estimate 2SLS. The identification audit then chose Branch B: assignment and dates for the 1994 experiment were not established, every candidate instrument was rejected, and 2SLS was not estimated on scanner rows. The memo is `reports/research_paper/identification_audit.md`.

The pre-specified checks that do not require an instrument were run as observational sensitivities. The adjacent price lead is nonzero. The first and second halves of the sample, split at week 200 before the subsample coefficients were seen, do not share a common magnitude. The promotion-coded split is exploratory and is large. None of those checks replaces the confirmatory association, and none is a causal elasticity.

## Phase 5 — Heterogeneity and oatmeal

Exploratory tier splits on cereals. Then the same confirmatory specification on oatmeal, with its own exclusion table. Agreement is robustness. Disagreement is a result, not a reason to drop a category.

## Phase 6 — Accounting counterfactuals

The hypothetical accounting scenarios are in `reports/research_paper/pricing_scenarios.md`. They use the confirmatory coefficient only as a stated elasticity, hold promotion status fixed, restrict the decision table to prices inside each pair's historical range, and report revenue and accounting gross profit separately under the recorded margin and under a 10-point less favorable margin. Nothing was implemented in stores. No Bertrand price was computed.

## Phase 7 — Paper, memo, and dashboard

The paper is `reports/research_paper/paper.md`. The two-page memo is `reports/research_paper/executive_memo.md`. The Streamlit application is `src/pricing_research/dashboard/app.py`. It reads the saved result files and does not refit a model. No scenario is offered as a deployment.

## Phase 8 — Interview notes and resume lines

Draft those only from outputs that the test log and the result files support.

## Estimation stack

Declared in `pyproject.toml` and not imported in Phase 1: pandas, numpy, scipy, statsmodels, linearmodels, pyarrow, matplotlib, seaborn, streamlit. DuckDB, scikit-learn, pyfixest, econml, and pyblp are not dependencies. A differentiated-product demand system is out of scope unless a later decision log shows why the fixed-effects audit is not the right object.

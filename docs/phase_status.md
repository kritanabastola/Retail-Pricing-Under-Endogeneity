# Phase status

Current phase: **independent audit complete, with a documented data-download blocker.** A clean virtual environment rebuilt the cereals panel, estimates, diagnostics, scenarios, and tests from the local Kilts files and reprinted the confirmatory coefficient. A fresh download of `wcer.zip` timed out, so from-scratch acquisition of the movement file was not demonstrated. No causal elasticity is claimed, and no scenario is supported for deployment. Oatmeal has not been estimated. The audit is `docs/phase8_audit.md`.

## Phase map

| Phase | Scope | Status |
| --- | --- | --- |
| 1 | Availability, license, variables, cleaning risks, identification, pre-specified design | Complete |
| 2 | Ingest cereals, build the analysis file, descriptive variation | Complete |
| 3 | Exploratory description of the cereals panel | Exploratory memo complete. The OLS and fixed-effects comparison was fit afterward |
| 4 | Identification audit and falsification. The baseline requested earlier is a separate completed step and did not estimate 2SLS | Complete as Branch B. No causal elasticity |
| 5 | Tier and promotion splits; oatmeal robustness | Not started. The audit's High, CubFighter, and discontinued splits are exploratory robustness only |
| 6 | Accounting counterfactuals under uncertainty | Complete as hypothetical scenarios. No deployment recommendation |
| 7 | Paper, executive memo, Streamlit dashboard bound to result files | Complete. No deployment recommendation |
| 8 | Independent audit, interview notes, and resume lines from verified outputs | Complete as an audit of the cereals artifacts. Movement zip was not re-downloaded. No causal elasticity |

## Baseline result

Command, from `retail-pricing-econometrics`, after `scipy` 1.18.1 was installed into `.venv`:

```text
.venv/bin/ruff check src/pricing_research/estimation tests/unit/test_estimation.py
.venv/bin/python -m pytest tests/unit/test_estimation.py -q
.venv/bin/python -m pricing_research.estimation.run
```

The estimator tests passed (`11 passed`). A later full run of `pytest` passed `56 passed in 1.13s`, and `ruff check src tests` passed. The fit exited 0 and wrote `reports/results/baseline_models.json`.

The log sample hash matches the Phase 2 quality report. The fit uses 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks, and 36,443 pairs. The confirmatory price coefficient, model `M5_confirmatory`, is −2.128 with a store-clustered standard error of 0.026. The memo is `reports/research_paper/baseline_findings.md`. No instrumental-variables estimator was run. The sample was not retuned.

## Identification audit

Command, from `retail-pricing-econometrics`:

```text
.venv/bin/python -m pytest tests/unit/test_identification.py -q
.venv/bin/python -m pricing_research.estimation.identify
```

The identification unit tests passed (`7 passed`). A later full run of `pytest` passed `63 passed in 0.90s`, and `ruff check src tests` passed. The audit exited 0. Branch B: every candidate instrument is rejected, and 2SLS was not estimated on scanner rows. The retained observational model is still `M5_confirmatory`. The memo is `reports/research_paper/identification_audit.md`. A synthetic 2SLS file was written with `empirical` false and `kilts_rows` 0. That file is not a Dominick's result.

## Hypothetical price scenarios

```text
.venv/bin/python -m pytest tests/unit/test_counterfactual.py -q
.venv/bin/python -m pricing_research.economics.counterfactual
```

The scenario tests passed (`9 passed`). A later full run of `pytest` passed `72 passed in 0.92s`, and `ruff check src tests` passed. The command exited 0 and wrote `reports/results/pricing_scenarios.json`. No scenario is marked supported for deployment. The memo is `reports/research_paper/pricing_scenarios.md`.

## Research communication

The paper is `reports/research_paper/paper.md`. The executive memo is `reports/research_paper/executive_memo.md`. The dashboard is `src/pricing_research/dashboard/app.py`. Dashboard tests check artifact agreement, empty filters, scenario units, and that the Streamlit script loads. A later full run of `pytest` passed `80 passed in 2.10s`, and `ruff check src tests` passed. Launch:

```text
.venv/bin/python -m streamlit run src/pricing_research/dashboard/app.py
```

## Phase 8 result

Command, from `retail-pricing-econometrics`, using `/tmp/pricing-audit-venv` after `pip install -e ".[dev]"`:

```text
python -m pricing_research.data.build
python -m pricing_research.reporting.explore
python -m pricing_research.estimation.run
python -m pricing_research.estimation.identify
python -m pricing_research.economics.counterfactual
python -m pytest -q
python -m ruff check src tests
```

pytest: `83 passed, 1 warning in 2.14s`. ruff: `All checks passed!` The reprinted confirmatory coefficient is −2.127546339203591 with store-clustered standard error 0.026069776011552 on 4,707,776 rows. The audit is `docs/phase8_audit.md`. Interview notes are `docs/interview_preparation.md`. Resume bullets are `docs/resume_bullets.md`.

## Phase 3 result

Command, from `retail-pricing-econometrics`:

```text
.venv/bin/ruff check src/pricing_research/reporting
.venv/bin/python -m pricing_research.reporting.explore
.venv/bin/python -m pytest -q
```

ruff: `All checks passed!`

The explore command exited 0 and logged `Wrote 12 figures`.

pytest: `45 passed in 0.30s`.

The memo is `docs/exploratory_analysis.md`. Counts are `reports/results/exploratory_summary.json`. The log sample used for the price and movement descriptions has 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks, and 36,443 UPC-store pairs. The audited panel has 6,602,582 rows. No regression coefficient was estimated.

## Phase 2 result

Command, from `retail-pricing-econometrics`, after `numpy` 2.5.3, `pandas` 3.0.6, and `pyarrow` 25.0.1 were installed into `.venv`:

```text
.venv/bin/ruff check src tests
.venv/bin/python -m pricing_research.data.build
.venv/bin/python -m pytest -q
```

ruff: `All checks passed!`

The build exited 0 and logged `Audited 6602582 rows; log sample 4707776 rows`.

pytest: `38 passed in 0.35s`.

`reports/tables/cleaning_summary.csv` reconciles the file:

| Rule | Rows | Rows remaining |
| --- | --- | --- |
| Input movement rows | 6,602,582 | 6,602,582 |
| Duplicate UPC-store-week | 0 | 6,602,582 |
| `OK` not 1 | 141,285 | 6,461,297 |
| Price not positive | 1,753,521 | 4,707,776 |
| Quantity not positive | 0 | 4,707,776 |
| Movement not positive | 0 | 4,707,776 |
| Week outside 1–400 | 0 | 4,707,776 |
| Log sample | 4,707,776 | 4,707,776 |

141,285 + 1,753,521 + 4,707,776 = 6,602,582. The audited Parquet has 6,602,582 rows. Rows deleted: 0. The movement-not-positive waterfall count is 0 because all 1,850,703 nonpositive-movement rows also have a nonpositive price and were already classified. 677 rows have positive movement and a nonpositive price. They remain in the audited file.

Outputs, gitignored:

- `data/interim/cereals_movement_audited.parquet`, 6,602,582 rows, SHA-256 `d82de16ad1a0e2247b4a553af1f8f14237969c5ff2e923d777fdd7b6e484a013`
- `data/processed/cereals_log_sample.parquet`, 4,707,776 rows, SHA-256 `023bd0b03df848a782b8bfab3b2ddce418543b08202736047ea418f923b4b4fb`

Inputs:

- `data/raw/wcer.zip`, 42,402,094 bytes, SHA-256 `2d4a59f88e4b97257c566f7c62fcccfdf9d5971891a617316ab21ea61c8d24c2`
- `data/raw/upccer.csv`, 25,932 bytes, SHA-256 `affa589f080ab18a2edb2fa8f4cfb52b9212dec353bb49778e57f2b2403c5c6c`

Hexadecimal price and margin each disagreed with the truncated field on 0 rows. The revenue identity failed 0 of 5,991 decimal checks. UPC join failures: 0. Duplicate keys: 0. The research question was not changed.

## Phase 1 files

- `README.md`
- `pyproject.toml`, `Makefile`, `.gitignore`, `.env.example`
- `configs/project.yaml`, `configs/data_sources.yaml`, `configs/specifications.yaml`
- `src/pricing_research/reporting/feasibility.py`
- `reports/tables/category_feasibility.json`
- `src/pricing_research/economics/accounting.py`
- `src/pricing_research/data/calendar.py`
- `src/pricing_research/validation/schema.py`
- `tests/unit/test_accounting.py`, `test_calendar.py`, `test_schema.py`
- `docs/research_design.md`, `data_dictionary.md`, `identification.md`, `analysis_plan.md`, `limitations.md`, `reproducibility.md`, `model_card.md`, `decision_log.md`, this file
- `data/README.md`

## Phase 1 commands

Interpreter: `/usr/local/bin/python3.13` (Python 3.13.1). Working directory: `retail-pricing-econometrics`.

```text
/usr/local/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install -e . --no-deps
.venv/bin/python -m pip install "pytest>=8.3" "ruff>=0.6"
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
```

`pip install -e . --no-deps` was intentional at that point. Phase 2 later installed numpy, pandas, and pyarrow. scipy, statsmodels, linearmodels, matplotlib, seaborn, and streamlit are still declared and were not imported.

Resolved test tools: pytest 9.1.1, ruff 0.16.10.

Phase 1 final unit-test run, before the panel tests: `33 passed in 0.03s`. ruff: `All checks passed!`

Feasibility screen:

```text
.venv/bin/python -m pricing_research.reporting.feasibility \
  --raw-dir data/raw \
  --out reports/tables/category_feasibility.json
```

## Findings that constrain later phases

- Cereals is the primary category. The built log sample has 4,707,776 rows. Truncated unit price changes in 31,167 of 36,443 log-sample UPC-store pairs.
- Oatmeal is the robustness category. The same builder accepts `--category oatmeal` and does not replace the cereals quality report. That run was not required for this gate. Canned soup is deferred.
- The movement header is `STORE`, `UPC`, `WEEK`, `MOVE`, `QTY`, `PRICE`, `SALE`, `PROFIT`, `OK`, `PRICE_HEX`, `PROFIT_HEX`. There is no `DEAL` column. `SALE` also contains undocumented `G` and `L` (11,076 cereals rows).
- Truncated price and margin matched the hexadecimal doubles within 0.0001 on every cereals row in this build.
- Cereals is missing 32 week numbers: 262–265, 284–309, and 370–371. Those weeks were not filled.
- Causal IV is rejected for the main specification. The Hoch, Drèze, and Purk experiment included ready-to-eat cereals, and the assignment file is not in the downloaded bundle.
- The confirmatory object remains the fixed-effects association in `configs/specifications.yaml`.
- Movement store IDs 135, 140, 141, 142, 143, 144, and 146 are missing from the 96-row store transcription. Their tier fields are null.

## Unresolved after the identification audit

- Experiment assignment and dates are not established. The audit rejected every candidate and did not estimate 2SLS.
- Demographics and customer-count files were sized and not opened.
- `statsmodels`, `linearmodels`, seaborn, and streamlit are declared and were not imported. The baseline uses numpy, pandas, pyarrow, matplotlib, and scipy.
- The manual's cereals row total (6,417,055) does not match the CSV (6,602,582). The difference is unexplained. The panel uses the CSV count.
- The store transcription is spot-checked, not re-keyed from the manual PDF.
- Oatmeal has not been fit. The cereals price scenarios are hypothetical accounting arithmetic, not a deployment result.

## Permission requested

The identification audit is closed on Branch B. A later phase may not adopt an instrument without a written assignment and exclusion argument before the second stage. The confirmatory sample may not be retuned to change the coefficient that has now been seen. The price scenarios are hypothetical and do not authorize a deployment. The paper, memo, and dashboard do not change that conclusion. Oatmeal and interview notes have not been started.

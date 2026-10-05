# Reproducibility

## Phase 1 environment

Phase 1 tests use the Python standard library and pytest. They do not import pandas or statsmodels. Those libraries are declared in `pyproject.toml` for later phases. The Phase 1 virtual environment was created with `pip install -e . --no-deps` and then pytest 9.1.1 and ruff 0.16.10. The estimation libraries were not installed.

The commands that produced the Phase 1 gate, and their output, are in `docs/phase_status.md`. The same sequence is:

```bash
cd retail-pricing-econometrics
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -e . --no-deps
python -m pip install "pytest==9.1.1" "ruff==0.16.10"
python -m pytest
python -m ruff check src tests
```

`pip install -e ".[dev]"` would also install the estimation libraries named in `pyproject.toml`. That command was not the one used for this gate, and those libraries have not been import-tested.

`make test` and `make lint` call `python -m pytest` and `python -m ruff check` with whatever `python` is on the path. Use the project virtual environment so that interpreter is 3.11 or newer. The system `python3` on the machine used for Phase 1 was 3.9.6 and is not the project interpreter.

## What is not reproduced by the tests

The unit tests do not download Kilts files and do not estimate a regression. The feasibility counts in `reports/tables/category_feasibility.json` come from a separate command that reads gitignored files in `data/raw/`:

```bash
python -m pricing_research.reporting.feasibility \
  --raw-dir data/raw \
  --out reports/tables/category_feasibility.json
```

The unit tests check:

- the manual's revenue and margin identities, including the three-for-two-dollar bundle arithmetic
- rejection of nonpositive prices, nonpositive bundle sizes, negative movement, and binary floats
- week dates read from the manual for weeks 1, 7, 91, 115, 116, 399, and 400
- the movement header observed on the oatmeal CSV
- promotion-code handling, duplicate keys, and unmatched UPCs

## Data access

Catalog: https://www.chicagobooth.edu/research/kilts/research-data/dominicks

Acknowledge the James M. Kilts Center, University of Chicago Booth School of Business, in any paper that uses the data. Do not commit `data/raw/`.

`python -m pytest` and `python -m ruff check src tests` are the checks for the code. They use synthetic rows. They do not read `data/raw/` and they do not estimate a regression.

## Phase 2 panel

Install the libraries the builder imports, then construct the cereals panel:

```bash
cd retail-pricing-econometrics
source .venv/bin/activate
python -m pip install "numpy>=2.1" "pandas>=2.2" "pyarrow>=17" "matplotlib>=3.9"
python -m pricing_research.data.acquire --raw-dir data/raw
python -m pricing_research.data.build
python -m pytest
python -m ruff check src tests
```

`python -m pricing_research.data.build` reads `data/raw/wcer.zip` and `data/raw/upccer.csv`, keeps every movement row, and writes the log sample as a filter. The command that produced the committed quality report is recorded in `docs/phase_status.md` with the test output from that run.

`--max-rows` writes a development extract under a `_dev` suffix and does not replace `reports/results/data_quality.json`. Do not report that extract as the full sample.

The store list used in the join is `src/pricing_research/data/resources/store_codebook.csv`. It is a transcription of manual Part 6, not a Kilts microdata file. Provenance is in `docs/data_dictionary.md`.

`python -m pytest` and `python -m ruff check src tests` are the checks for the code. They use synthetic rows. They do not read `data/raw/` and they do not estimate a regression.

The exploratory figures and `reports/results/exploratory_summary.json` come from a separate command that reads the gitignored Parquet panel:

```bash
python -m pricing_research.reporting.explore
```

That command does not estimate the confirmatory regression. The memo written from its output is `docs/exploratory_analysis.md`.

## Baseline associations

The cereals slopes are a separate command. It reads the gitignored log sample, checks the row count and hash against `reports/results/data_quality.json`, and writes `reports/results/baseline_models.json`, `reports/tables/baseline_regression.csv`, and the `baseline_` figures.

```bash
python -m pip install "scipy>=1.14"
python -m pricing_research.estimation.run
```

`scipy` supplies the Student t reference for the store-clustered intervals. `statsmodels` and `linearmodels` are still declared and are not imported. The point estimates come from the within-transformed OLS in `pricing_research.estimation.ols`. Synthetic tests in `tests/unit/test_estimation.py` do not read the Kilts panel. The memo written from the Kilts fit is `reports/research_paper/baseline_findings.md`.

## Identification audit

The audit reads the same log sample and the baseline JSON. It does not estimate two-stage least squares on those rows. Instrument verdicts are fixed in `pricing_research.estimation.instruments` before correlations are computed. A separate synthetic 2SLS example is written with `empirical` false and `kilts_rows` 0.

```bash
python -m pricing_research.estimation.identify
```

The memo written from that command is `reports/research_paper/identification_audit.md`. Synthetic checks for the instrument list, the absorption of a week-level series, the constant-margin identity, and the synthetic 2SLS example are in `tests/unit/test_identification.py`. They do not read the Kilts panel.

## Hypothetical price scenarios

```bash
python -m pricing_research.economics.counterfactual
```

The command reads the log sample, the baseline coefficient table, and the identification robustness table. It does not refit a regression. Synthetic checks in `tests/unit/test_counterfactual.py` do not read the Kilts panel. The memo is `reports/research_paper/pricing_scenarios.md`.

## Paper, memo, and dashboard

`reports/research_paper/paper.md` and `reports/research_paper/executive_memo.md` quote the saved coefficients. `tests/unit/test_dashboard.py` checks that the rounded confirmatory coefficient in both documents matches `reports/tables/baseline_regression.csv`, and that the baseline, audit, and scenario files agree with one another.

```bash
python -m streamlit run src/pricing_research/dashboard/app.py
```

The app reads those result files. It does not fit a model. Set `PRICING_DASHBOARD_SKIP_PANEL=1` to open the pages that do not need the log-sample parquet. Product-week charts use `data/processed/cereals_log_sample.parquet` when that file is present.

## Seeds

Phase 1 has no stochastic estimator. When a later phase uses a bootstrap or a cross-validation split, the seed goes in `configs/project.yaml` and is read by the estimator rather than set inside a notebook.

## Clean-environment rerun (5 October 2026)

A virtual environment outside the project, `/tmp/pricing-audit-venv`, ran `pip install -e ".[dev]"` and then the build, explore, estimate, identify, scenario, pytest, and ruff commands. pytest reported `83 passed, 1 warning in 2.14s`. The confirmatory coefficient reprinted as −2.127546339203591 (store-clustered SE 0.026069776011552, n = 4,707,776). The transcript is `reports/results/phase8_reproduction.log`. The review is `docs/phase8_audit.md`.

That run checksummed the local cereals zip and UPC file. A fresh `upccer.csv` download matched the recorded hash. A fresh `wcer.zip` download timed out after 589,479 of 42,402,094 bytes (curl exit 28) and was not used. The movement microdata are therefore not shown to be re-downloadable from this network.

`pip install -e ".[dev]"` does install statsmodels, linearmodels, and seaborn. The Kilts estimators do not import them. The independent benchmark in `tests/unit/test_independent_benchmark.py` imports statsmodels when it is present and skips that one test when it is not. The synthetic two-stage least squares file remains `empirical: false` with `kilts_rows: 0`.

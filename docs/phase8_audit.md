# Phase 8 audit

Independent review of the cereals project as of 5 October 2026. This note records what was rerun, what the estimates are allowed to mean, and what is still missing. It does not upgrade the confirmatory coefficient to a causal elasticity.

## Verdict

The saved cereals results are internally consistent and were reproduced from a clean virtual environment using the local Kilts files. The confirmatory price coefficient remains **−2.127546339203591** (store-clustered standard error **0.026069776011552**) on **4,707,776** positive-sale rows. Identification is Branch B: no instrument is approved, two-stage least squares was not estimated on scanner rows, and `deployment_supported` is false on every scenario row.

Complete reproducibility from a machine that does not already hold `data/raw/wcer.zip` was **not** demonstrated. A fresh download of that zip timed out. At the time of the audit there was no git repository, no license file, and the GitHub Actions workflow had never run. The code and reports were published afterward at https://github.com/kritanabastola/Retail-Pricing-Under-Endogeneity. Raw Kilts files were not included.

## A. Clean reproduction

Interpreter: Python 3.13.1 in `/tmp/pricing-audit-venv`, created outside the project so the existing `.venv` was left in place. The system `python3` on this machine is 3.9.6 and was not used.

### Install

```bash
/tmp/pricing-audit-venv/bin/python -m pip install -U pip
/tmp/pricing-audit-venv/bin/python -m pip install -e ".[dev]"
```

Exit 0. The extra installs NumPy, pandas, SciPy, PyArrow, matplotlib, Streamlit, Altair, pytest, and ruff, and also statsmodels 0.15.0, linearmodels 7.0, and seaborn 0.13.2. A search of `src/` finds no estimator import of statsmodels, linearmodels, or seaborn. The independent-benchmark test does import statsmodels when it is installed.

### Data

Local cereals files, checksummed by `python -m pricing_research.data.acquire` without `--force`:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `data/raw/wcer.zip` | 42,402,094 | `2d4a59f88e4b97257c566f7c62fcccfdf9d5971891a617316ab21ea61c8d24c2` |
| `data/raw/upccer.csv` | 25,932 | `affa589f080ab18a2edb2fa8f4cfb52b9212dec353bb49778e57f2b2403c5c6c` |

A fresh UPC download completed and matched that hash:

```text
curl -fL --retry 1 --max-time 45  .../upc_csv-files/upccer.csv
```

25,932 bytes, exit 0, SHA-256 identical to the local file.

A fresh movement download did not complete:

```text
curl -fL --retry 1 --max-time 45  .../movement_csv-files/wcer.zip
```

Exit 28. The first attempt received 589,479 of 42,402,094 bytes and then timed out. The partial files were not used. Cleaning and estimation therefore used the already-checksummed local zip. That is a blocker for a from-scratch reproduction of the microdata.

### Pipeline

From `retail-pricing-econometrics`, with `/tmp/pricing-audit-venv/bin/python`. The full transcript is `reports/results/phase8_reproduction.log`.

| Step | Command | Outcome |
| --- | --- | --- |
| Clean | `python -m pricing_research.data.build` | Exit 0. Audited 6,602,582 rows. Log sample 4,707,776 rows. |
| Describe | `python -m pricing_research.reporting.explore` | Exit 0. Wrote 12 figures. |
| Estimate | `python -m pricing_research.estimation.run` | Exit 0. Wrote `reports/results/baseline_models.json`. |
| Diagnose / identify | `python -m pricing_research.estimation.identify` | Exit 0. Wrote `reports/results/identification_audit.json`. |
| Scenarios | `python -m pricing_research.economics.counterfactual` | Exit 0. Wrote `reports/results/pricing_scenarios.json`. |
| Tests | `python -m pytest -q` | **83 passed**, 1 warning, 2.14s. |
| Lint | `python -m ruff check src tests` | All checks passed. |
| Reprint | read `M5_confirmatory` / `log_unit_price` | −2.127546339203591, SE 0.026069776011552, n = 4,707,776. |

The warning is a statsmodels deprecation for passing a dict to a formula. It is confined to `tests/unit/test_independent_benchmark.py`.

### Dashboard

Port 8501 was already taken by the earlier project interpreter. The audit interpreter was started separately:

```bash
/tmp/pricing-audit-venv/bin/python -m streamlit run \
  src/pricing_research/dashboard/app.py \
  --server.port 8502 --server.headless true --server.address 127.0.0.1
```

The process reported `http://127.0.0.1:8502`. The overview page showed 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks, coefficient −2.128, store-clustered SE 0.026, and Branch B. The pricing-scenarios page opened with the elasticity control set to `central_confirmatory_association (-2.128)`. In a viewport about 760 pixels wide, the sidebar covers the left edge of the main heading. The numbers on the page were still readable.

### Flags after the rerun

- `causal_claim` is false on the identification audit and on the scenario file.
- `iv_estimated_on_kilts_rows` is false.
- Instrument verdicts: 10 `REJECTED`, 0 `APPROVED`.
- `deployment_supported`: 0 true, 320 false.
- `equilibrium_prices_computed` is false. Bertrand markup optimization is `not estimated`.
- Regenerated JSON under `reports/` contains no `/Users/` paths. Input paths are project-relative (`data/raw/wcer.zip`, and the store codebook under `src/`).

## B. Statistical review

**Outcome and price.** The outcome is log item movement (`MOVE`). Unit price is `PRICE / QTY` in dollars per item. Revenue in the scenario layer is price times movement. These are the Kilts identities. The coefficient is a log-log association, so a 10 percent price difference maps to a movement factor of `1.10^β − 1`, about −18.4 percent at the confirmatory point estimate. That translation is arithmetic. It is not an effect of changing price.

**Fixed effects.** M5 absorbs a UPC-by-store effect and a week effect by alternating projections. The reported rank, 36,808, equals 36,443 pairs plus 366 weeks minus one omitted dummy. Week effects do not absorb a promotion that is specific to one UPC. Store-by-week and UPC-by-week effects were excluded in the design and were not added after the coefficient was seen. The pooled slope (−0.346) and the confirmatory slope (−2.128) are different associations. The audit file states that the gap is not a measured sign of omitted-variable bias. A Hausman test was not computed, because no estimator was shown to be consistent for a causal parameter.

**Clustering.** The primary interval uses the store-cluster sandwich and a Student t reference with 92 degrees of freedom. Week-clustered and two-way (Cameron, Gelbach, and Miller) standard errors are stored as sensitivities. Applying the store critical value to those other standard errors is a disclosed choice. It is not a week-cluster interval, and clustering does not make price exogenous.

**Measurement and missing values.** The audited file keeps every input row. The log sample is a filter: `OK == 1`, positive price, positive `QTY`, and positive movement. Recorded zeros are not filled, and absent UPC-store-weeks are not created. Unconditional nonpositive prices and the sequential waterfall are different counts. They should not be added. Codes `G` and `L` stay unclassified. Blank `SALE` is not treated as a verified regular price. The confirmatory dummy is 1{`SALE` in {B, C, S}}, so unclassified and blank weeks sit in the reference group.

**Zero-sales selection.** Every nonpositive-movement row in the cereals file also has a nonpositive price, so the log sample does not contain a positive price with zero movement. The coefficient is still conditional on a positive scanned sale. It does not describe weeks the chain did not record, and it does not describe a demand curve through zero.

**Instruments.** Verdicts are set in code before correlations are computed. Margin-derived average acquisition cost is a function of shelf price when the margin is stable, so it fails exclusion. Lagged prices and other-store prices can share promotions and demand shocks. Price tier does not vary within a store. The promotion flag is an incomplete control. A national cost index would be absorbed by week effects. The Hoch, Drèze, and Purk assignment file is not in the raw directory (`hoch_assignment_filenames_in_raw` is empty). A first-stage F and an overidentification test are marked not applicable because no instrument was approved and two-stage least squares was not fit to Kilts rows.

**Elasticities, costs, and scenarios.** Using −2.128 as a hypothetical constant elasticity, revenue and accounting gross profit move in opposite directions on the menu of pairs whose own history contains every listed price. Both totals rise together only if the pooled association is treated as causal, which this audit rejects. `PROFIT` is a margin field. The unit cost in the scenarios is average acquisition cost held constant, not marginal cost, and gross profit is not operating profit. Baselines are each pair's own last log-sample week. They are not one calendar week of chain revenue. A 10 percent increase from the last price is outside that pair's observed range for about 68 percent of pairs. The store-clustered band around the M5 scenario is sampling uncertainty for the association. It is not a causal confidence interval. Specification uncertainty, from −0.346 to −2.128, is large enough to change the sign of the revenue calculation.

**Claim consistency.** The paper, memo, dashboard, and result files agree on Branch B, the rounded coefficient −2.128, and the refusal to deploy a price. The dashboard UPC count is read from the exploratory summary rather than typed as a constant. No result in this review was found that calls M5 a causal elasticity.

## C. Independent benchmark

These checks are not Dominick's findings.

1. `tests/unit/test_independent_benchmark.py` builds a 12-group synthetic panel with a known within slope of −1.25. A hand-written group demean plus `numpy.linalg.lstsq` recovers −1.25, and `fit_ols` matches that slope. The same design, fit with `statsmodels.formula.api.ols` and group dummies, also recovers −1.25. That test ran in the clean environment because statsmodels was installed. It would skip if statsmodels were absent.
2. `revenue_factor(1.10, -2.0)` matches `1.10 * 1.10**(-2)` and `1.10**(1-2)`.
3. `reports/results/synthetic_iv_demonstration.json` records a separate synthetic two-stage least squares example. `empirical` is false and `kilts_rows` is 0. On 20,000 synthetic rows, a valid excluded instrument has true slope −1.4 and estimate −1.4035153185273719 (first stage 0.8062276703357523) and is marked as recovering the slope. An instrument that also shifts demand by 0.9 has estimate −0.651772503637244 and does not recover the slope. That file is a software check. It is not a cereals elasticity.

No published Dominick's coefficient was reestimated from another author's code in this pass. The Hoch, Drèze, and Purk category sales and profit figures are their results and are not claimed here.

## D. Repository audit

| Item | Finding |
| --- | --- |
| License | No `LICENSE` file. A license was not chosen in this audit. |
| Attribution | README and the paper name the Kilts Center. The Hoch, Drèze, and Purk experiment is cited as their study. |
| Redistribution | `.gitignore` excludes `data/raw/`, `data/interim/`, and `data/processed/`. Raw Kilts files were not staged. There is no commit, because the directory is not a git repository. |
| Secrets and paths | No API keys or passwords were found in `src/`. Regenerated report JSON uses project-relative paths. |
| Dependencies | `pip install -e ".[dev]"` is the command that was demonstrated. It installs three libraries the estimators do not import. |
| Documentation | README, paper, memo, and this audit point at the same coefficient and the same Branch B conclusion. |
| Links | The Kilts catalog URL is the one used for acquisition. README links to figures and reports that exist, including this file. There is no GitHub URL to check. |
| Unused code | statsmodels, linearmodels, and seaborn are declared and unused by the Kilts estimators. The benchmark test is the only statsmodels use. |
| Generated files | Figures and result JSON are produced by the commands above. The reproduction log is kept. |
| Continuous integration | `.github/workflows/tests.yml` installs the package, runs ruff, and runs pytest on Ubuntu with Python 3.13. It has never been executed. Do not describe CI as passing. |

## E–G. Portfolio documents

- README: `README.md`
- Interview notes, 20 questions: `docs/interview_preparation.md`
- Resume bullets, three audiences: `docs/resume_bullets.md`

Those documents use the reproduced coefficient and the Branch B conclusion. They do not claim a deployed price, a revenue gain, or a causal elasticity.

## H. Scorecard

Scores are 1–10. A low identification score is the scientifically correct reading of this design, not a request to find an instrument after the fact.

| Dimension | Score | Reason | Remaining weakness |
| --- | ---: | --- | --- |
| Economic rigor | 8 | The equation, the sample filter, the promotion codes, and the clustering choice were written down before the fit and were not retuned. Units follow the Kilts identities. | Week effects miss UPC-specific promotions. There is no substitution system. Oatmeal was not estimated. |
| Identification validity | 2 | No instrument survives exclusion or has the required variation. Two-stage least squares was not fit to scanner rows. | The project cannot support a causal price elasticity until an assignment or another excludable shifter is in hand and checked against the prices that were charged. |
| Data quality | 7 | 6.6 million audited rows, a documented log-sample filter, checksums, and a store codebook with stated provenance. | Historical Chicago chain, incomplete `SALE` codes, missing weeks inside 1–399, and a margin field that is not marginal cost. The movement zip could not be re-downloaded in this audit. |
| Reproducibility | 6 | A clean environment rebuilt the panel, the estimates, the scenarios, and the tests, and reprinted the same coefficient. | Reproduction still depends on a local copy of `wcer.zip`. There is no git history, and CI has not run. |
| Engineering quality | 7 | Within OLS, cluster standard errors, scenario accounting, and the dashboard are tested. Report paths are portable. ruff passed. | Declared but unused libraries. No license. The dashboard sidebar covers the heading in a narrow window. |
| Original contribution | 4 | The contribution is a careful refusal: the within association is not a causal elasticity, and revenue and accounting gross profit need not move together. | The estimator is standard. The result is an application to one category of a public academic panel. |
| Business interpretability | 7 | The scenario page separates item movement, revenue, and accounting gross profit, and it marks every case unsupported for deployment. | The dollars are hypothetical, the baseline weeks are not contemporaneous, and average acquisition cost is not the cost a manager would use for a live price. |
| Communication | 8 | The paper, memo, README, and dashboard state Branch B in the same place as the coefficient. | No public repository URL. The narrow-viewport overlap makes the scenario heading hard to read. |
| Interview defensibility | 8 | The prepared answers match the artifacts, including the instrument failure, the confidence-interval interpretation, and the profit-versus-revenue conflict. | A reviewer can fairly ask why oatmeal was not estimated and why the Hoch assignment was not obtained. Those are open gaps, and the notes already say so. |

## Remaining limitations

- Causal identification was not established.
- The movement microdata were not freshly downloaded in this audit.
- The directory is not a git repository, has no license file, and has an unexecuted CI workflow.
- Oatmeal, a substitution system, and Bertrand pricing were not estimated.
- Scenario profit is accounting gross profit from average acquisition cost, on stacked last weeks, and a 10 percent increase is often outside the pair's own price history.

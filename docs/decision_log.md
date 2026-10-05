# Decision log

Decisions below were made before any demand regression. Dates are the research dates, not the historical dates in the scanner files.

## 2026-10-05 — Primary category is ready-to-eat cereals

The manual gives cereals weeks 1–399, 490 UPCs, and 6,417,055 movement rows. The public UPC CSV has 490 data rows, all commodity code 311. The movement CSV zip is public (42,402,094 bytes) and was not downloaded. Cereals are differentiated, separated from hot cereal by the manual, and included as Cereal-RTE in Hoch, Drèze, and Purk (1994, Table 1).

## 2026-10-05 — Oatmeal is the robustness category; canned soup waits

Oatmeal has 96 UPCs, starts at week 91, and its movement zip is 7,736,663 bytes. Canned soup has a full week window and 7,011,243 manual rows, and its zip is 43,140,921 bytes, similar to cereals. Soup is the better eventual test of multi-item `QTY`, because the manual's bundle example is tomato soup. That test is not required to choose the confirmatory specification.

## 2026-10-05 — Do not zero-fill, and do not treat blank `SALE` as a regular-price week

The manual does not define absent UPC-store-weeks as zero sales. It does say that an unset `SALE` code can still be a promotion. Both rules are in the specification file.

## 2026-10-05 — Confirmatory association uses UPC-by-store and week fixed effects

Chainwide promotions of a single UPC survive additive week effects and would be absorbed by UPC-by-week effects. Store-by-week effects would absorb a category-wide experimental price shift. Those richer effects are documented as excluded, not as a hierarchy to climb after seeing estimates. Store-clustered standard errors are the baseline inference choice and are not an identification strategy.

## 2026-10-05 — No instrument is adopted

The public files reviewed do not include experiment assignment. Average acquisition cost, lags, other-store prices, and price tier each fail a basic exclusion or exogeneity argument recorded in `docs/identification.md`. The project may later conclude that causal identification was not established.

## 2026-10-05 — Hexadecimal price and margin are compared with the truncated fields before use

The Kilts page says both representations are in the CSV and that the hexadecimal values match SAS. Mehrhoff suggests the truncated fields for ordinary use. Disagreements will be counted in Phase 2. The representation will not be chosen by the resulting t-statistic.

## 2026-10-05 — Raw data stay out of git

The license is academic-use with required Kilts acknowledgment. The repository stores code, the week rule, and documentation.

## 2026-10-05 — Three movement files were profiled, and cereals stays primary

`python -m pricing_research.reporting.feasibility` counted the cereals, oatmeal, and canned-soup CSVs. Results are in `reports/tables/category_feasibility.json`. Cereals has 4,707,776 log-sample rows, price changes in 85.5 percent of UPC-store pairs, bundle size other than 1 on only 5,034 rows, and milder seasonality than oatmeal or soup. Oatmeal remains the robustness category. Soup is feasible and is deferred because `QTY` changes in 24.3 percent of its pairs and November movement is about three times July movement.

The raw zips remain in gitignored `data/raw/`. They were not used to estimate a price coefficient.

## 2026-10-05 — Phase 2 does not change the research question

The confirmatory equation, the cereals log-sample rules, the oatmeal robustness role, and the rejection of a causal IV stay as written in `configs/specifications.yaml`. Phase 2 builds the panel those rules describe. It does not estimate β.

The log sample is a flagged subset of the audited movement file. Rows that fail a rule remain in `data/interim/cereals_movement_audited.parquet`. `reports/tables/cleaning_summary.csv` is a first-reason waterfall: input rows equal sequential exclusions plus the log sample. Unconditional flag counts can overlap and are not the waterfall.

A store codebook was added from the Eurostat `dff` transcription of manual Part 6, after spot checks of stores 2, 8, 12, 21, and 137 against the manual. It is a codebook, not scanner microdata. Store 102's ZIP is left as transcribed (`655`). Tiers are not invented for stores the transcription does not list.

## 2026-10-05 — `G` and `L` stay unclassified

The movement files contain `SALE` code `G` and, in cereals, one `L`. Manual Part 4, as read here, defines B, C, and S. The confirmatory indicator uses only those three codes.

## 2026-10-05 — Causal IV is rejected for the main specification

No assignment file for the 1994 experiment is in the downloaded bundle. Margin-derived cost is a function of retail price, and in cereals the margin changes while the truncated price is fixed in only 5.3 percent of UPC-store pairs. Lagged prices, other-store prices, tiers, promotion codes, traffic, and demographics fail the exclusion or exogeneity bar recorded in `docs/identification.md`. The main estimator is the pre-specified fixed-effects association and its sensitivity ladder.

## 2026-10-05 — Phase 3 describes the panel and does not estimate β

The confirmatory equation, the cereals log-sample rules, and the rejection of a causal IV are unchanged. The exploratory memo is `docs/exploratory_analysis.md`. Pooled and within-pair correlations are reported there as correlations. They are not elasticities. The pre-specified OLS and fixed-effects comparison has not been run.

No design revision came out of the description. Two facts constrain how a later coefficient would be read, and both were already in the specification. Unclassified `G` and `L` weeks are high-movement, low-price weeks that the B/C/S indicator leaves in the reference group. About 28 percent of multi-store price-change weeks move at least 80 percent of the comparable stores together, so week fixed effects do not absorb every chainwide UPC promotion. The 20 percent within-pair price-change rule is cleared: 85.5 percent of log-sample pairs have a unit-price range above $0.001.

## 2026-10-05 — The cereals baseline is fit, and the design is not revised

`python -m pricing_research.estimation.run` fit the ladder in `configs/baseline_models.yaml` on the cereals log sample. The confirmatory association is negative, and it differs from pooled OLS. Those are the two cereals hypotheses that were written down before the fit. Pair-effect PPML and a linear items-per-dollar model do not match the log-log magnitude. They are reported as different estimands. `log(1 + MOVE)` was not estimated. `OK = 0` rows with a usable price do not flip the sign. No fixed effect was added after the coefficient was seen. Causal IV stays rejected. The memo is `reports/research_paper/baseline_findings.md`.

## 2026-10-05 — Identification audit chooses Branch B

`python -m pricing_research.estimation.identify` measured the candidate instruments and the pre-specified observational sensitivities. Every candidate stays rejected. The verdicts were fixed before the correlations. Two-stage least squares was not estimated on scanner rows. The Hoch assignment file is still absent. The confirmatory association remains M5. Its magnitude moves across the week split and across blank versus coded promotion rows. The design equation was not retuned. Oatmeal was not estimated. Accounting counterfactuals were not run. The memo is `reports/research_paper/identification_audit.md`.

## 2026-10-05 — Price scenarios stay hypothetical

`python -m pricing_research.economics.counterfactual` applied stated elasticities to each UPC-store pair's last observed shelf. The confirmatory association enters only as a hypothetical elasticity. Revenue and accounting gross profit are reported separately. No Bertrand price was computed. No scenario is supported for deployment. The memo is `reports/research_paper/pricing_scenarios.md`.

## 2026-10-05 — Paper, memo, and dashboard read the saved files

The research paper is `reports/research_paper/paper.md`. The two-page memo is `reports/research_paper/executive_memo.md`. The Streamlit app in `src/pricing_research/dashboard/app.py` loads the baseline table, the identification audit, and the scenario file. It does not refit a coefficient and it does not offer two-stage least squares. No deployment recommendation was added.

## 2026-10-05 — Independent audit does not revise the design

A clean environment rebuilt the cereals artifacts from the local Kilts files and reprinted the same confirmatory coefficient. The fresh movement-zip download timed out, so that file was not replaced. Branch B stands: no instrument is approved, two-stage least squares stays off the scanner rows, and no scenario is supported for deployment. Interview notes and resume bullets were written from those artifacts. Oatmeal was not estimated. The review is `docs/phase8_audit.md`.

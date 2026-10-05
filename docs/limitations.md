# Limitations

These limits apply after the cereals identification audit. The coefficients are conditional associations. The audit did not sign the gap between pooled OLS and the confirmatory slope as omitted-variable bias. A store-clustered interval does not turn the price coefficient into an elasticity of demand.

## Data

- The series ends in 1997 and describes one defunct chain in metropolitan Chicago. It is not current national demand.
- Movement rows are scanned sales. Stockouts and items absent from the file are not observed as separate states. Missing UPC-store-weeks will not be coded as zero.
- `SALE` is an incomplete promotion flag. Blank is not a verified regular-price week.
- `QTY` is bundle size, not package size. `SIZE` is an irregular text field. Unit price and price per ounce are different objects.
- `NITEM` links across UPCs are not reliable enough to define the product in the confirmatory sample.
- `PROFIT` is an average-acquisition-cost margin in percent of sales. It is not marginal cost, not replacement cost, and not economic profit after operating cost.
- The manual's printed movement totals match the canned-soup CSV (7,011,243 rows) and do not match the cereals CSV (6,602,582 versus 6,417,055) or the oatmeal CSV (1,333,465 versus 1,301,870). Counted CSV rows are the ones this project uses. The difference is unexplained.
- In all three files, every truncated `PRICE` and `PROFIT` matched its hexadecimal double within 0.0001. That is a property of these three extracts on 5 October 2026, not a promise about other categories.
- Cereals is missing 32 week numbers inside weeks 1–399, including 16 February 1995 through 16 August 1995. Oatmeal is missing three weeks. Soup is missing 20. The holes are not the same across categories. They are not filled with zero sales.
- Nonpositive prices in these files are exact zeros. They mostly sit on zero-movement rows. Cereals also has 677 rows with positive movement and a zero price. Those rows are excluded from the log sample and are not imputed.
- `SALE` contains `G` and, once in cereals, `L`. The manual text that was read defines B, C, and S only. `G` and `L` stay unclassified.
- The movement files contain 93 store IDs, the same set in all three categories. The catalog's "100-store chain" and the 86 stores in Hoch, Drèze, and Purk (1994) are different counts. The Phase 2 join uses a 96-row transcription of manual Part 6. Cereals movement IDs 135, 140, 141, 142, 143, 144, and 146 are not in that transcription (49,304 rows), so their tier is null. Ten transcription IDs are absent from the cereals file. The transcription was spot-checked, not re-keyed row by row. Some stores have no zone because they opened after the 1992 zone snapshot.
- Demographics are a single 1990 cross-section.
- Customer counts are daily store traffic, not UPC demand, and they respond to promotions.
- The manual's special-event column is only partly checked. Week fixed effects do not require the labels; holiday charts do.
- Princeton's catalog start year (1987) disagrees with the manual's week-1 date (14 September 1989). This project follows the manual.

## Baseline estimates

- The confirmatory price coefficient is an association after UPC-store effects, week effects, and an incomplete promotion flag. The fitted value and its intervals are in `reports/research_paper/baseline_findings.md`. Magnitude is sensitive to product fixed effects and to the promotion flag. That sensitivity is not an identification proof.
- Eleven and a half percent of log-price variation remains after pair and week effects, and 9.2 percent remains after the coded promotion indicator is residualized as well. That is enough to estimate the slope. The price changes in that remainder are still chosen.
- There is no `OK = 1` row with a positive unit price and zero movement. PPML on the log sample does not restore zero sales. A coefficient on `log(1 + MOVE)` was not estimated and would not be an elasticity.
- Pair-effect PPML and the linear items-per-dollar model do not reproduce the log-log magnitude. The median translation of the linear slope is not β.
- Confirmatory residuals are serially correlated inside pairs (successive-week correlation about 0.31) and have a long left tail. Quantile bins of the residual against residualized log price are not flat, so a single slope is an average.
- Store clustering leaves cross-store dependence unaccounted for. Week and two-way standard errors are larger and still leave the confirmatory interval below −1. Ninety-three clusters make the t interval an approximation.
- Restoring 43,426 `OK = 0` rows with positive price and movement does not flip the sign. Those rows are not the confirmatory sample.

## Identification

- The Phase 5 audit chose Branch B. Causal identification is not established. The memo is `reports/research_paper/identification_audit.md`.
- Two-stage least squares was not estimated on Kilts rows. Weak-instrument diagnostics and an overidentification test are not applicable. A Hausman test was not computed, because it would need an estimator already known to be consistent for a causal parameter.
- The published everyday-price experiment included ready-to-eat cereals, but the public files reviewed here do not contain treatment assignment or timing. The raw directory listing in the audit contains no assignment filename.
- Reconstructed experiment labels from later research are not the randomization.
- Margin-derived cost, lagged price, other-store prices, price tier, the promotion flag, customer counts, 1990 demographics, a national cost index, and an exposure-weighted index are rejected. A wholesale cost index would not automatically satisfy exclusion. A pure weekly index is absorbed by week effects. The audit's week-number demonstration has remaining share 0 after week effects and is not a cost series.
- On the log sample, log average acquisition cost correlates 0.886 with log unit price. The leave-one-out other-store price correlates 0.990. Those correlations are not relevance proofs.
- A store-clustered standard error does not establish exogeneity. High-tier and CubFighter robustness intervals use 25 and 9 store clusters.
- The confirmatory association is −1.870 in weeks 1–200 and −2.428 in weeks 201–399. The magnitude is not stable across that pre-specified split.
- Blank `SALE` rows give −1.383 and coded B/C/S rows give −2.696. Blank is not a confirmed regular price.
- Adding the next calendar week's log price produces a lead coefficient of 0.459. That rejects a narrow contemporaneous-only story. It does not sign the bias in the confirmatory slope.
- Moving unclassified `G` and `L` into the promotion indicator changes the price coefficient from −2.128 to −2.046. The sign does not flip.
- Week fixed effects leave chainwide UPC promotions in the price variation. Those promotions are chosen. That remaining chosen price variation is the most serious unresolved threat.
- The log sample conditions on positive scanned movement.
- Scenario arithmetic in the audit uses assumed elasticities. It is not a causal revenue result.

## Counterfactual scenarios

- The scenarios in `reports/research_paper/pricing_scenarios.md` are hypothetical accounting arithmetic. They are not causal effects and were not implemented in stores.
- The decision table keeps prices inside each pair's historical unit-price range. A 10 percent increase from the last observed price is outside that range for 68 percent of pairs.
- Baselines are each pair's last log-sample week. Those weeks are not contemporaneous, so the stacked dollars are not one week's category revenue.
- The unit cost is an average-acquisition-cost proxy held constant. It is not marginal cost. Accounting gross profit is not operating profit.
- No Bertrand price was computed. Cross-product substitution and competitor responses are omitted, so a category total is a sum of own-price hypotheticals.
- Under the confirmatory association used as a hypothetical elasticity, revenue and accounting gross profit move in opposite directions. The sampling interval around that association does not flip the revenue sign. The pooled association does. Neither association is a causal elasticity.

## Integrity rules already in force

Unsupported claims stay in this file. Synthetic rows are allowed only in unit tests. The three oatmeal records used to test hexadecimal decoding are fixtures copied from an inspection, not population moments.

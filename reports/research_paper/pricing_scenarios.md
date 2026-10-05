# Hypothetical cereals price scenarios

Command: `python -m pricing_research.economics.counterfactual`.

These are accounting scenarios. They are not causal effects, not equilibrium prices, and not results that were implemented in stores. Phase 5 did not establish a causal elasticity. Bertrand markup optimization was not estimated: the files do not contain a substitution system, competitor prices, or a marginal cost.

The machine-readable file is `reports/results/pricing_scenarios.json`. The decision table is `reports/tables/pricing_scenarios.csv`. The figures are `reports/figures/scenario_01_revenue.png` and `reports/figures/scenario_02_gross_profit.png`.

## Decision problem

Under stated assumptions about the own-price response, a constant unit acquisition-cost proxy, and no competitor response, how would feasible percent changes in unit price move predicted item sales, revenue, and accounting gross profit for ready-to-eat cereals?

The calculation, for a common price ratio `P1 / P0` and a stated elasticity ε, is

`Q1 = Q0 × (P1 / P0)^ε`

`R1 = P1 × Q1`

`G1 = (P1 − c) × Q1`

ε is a constant own-price elasticity of item movement with respect to unit price. Unit price is dollars per item. Movement is items. Revenue and gross profit are dollars. When every pair receives the same percent price change, the percent changes in quantity and revenue equal the closed form and do not depend on which pairs are included. The percent change in gross profit does depend on the margin distribution.

What ε is in each row:

| Case | ε | Status |
| --- | --- | --- |
| Pooled association (low sensitivity) | −0.346 | Estimated association, used as a hypothetical elasticity |
| Confirmatory association (central) | −2.128 | Estimated M5 association, used as a hypothetical elasticity |
| Unit | −1 | Assumed benchmark. Revenue is unchanged |
| Steeper | −3 | Assumed round adverse case. Not the pair-PPML estimate |
| Blank `SALE` slice | −1.383 | Estimated association on blank rows. Blank is not a confirmed regular price |
| Coded B/C/S slice | −2.696 | Estimated association. Exploratory |
| Weeks 1–200 | −1.870 | Estimated association. Specification check |
| Weeks 201–399 | −2.428 | Estimated association. Specification check |

Held constant inside a scenario: the baseline week's promotion class, other products' prices, competitor prices, store traffic, assortment, and the baseline unit cost within a cost case. Cross-cereal substitution is not in the formula. A category total is a sum of own-price hypotheticals.

The M5 association holds the coded promotion flag fixed. These scenarios do not flip `SALE`. A price cut that would have been run as a promotion is a different intervention.

## Baseline and historical support

Each of 36,443 UPC-store pairs contributes its last week in the cereals log sample. That is 489 UPCs and 93 stores. The baseline weeks run from week 1 to week 399, with median week 361. They are not one calendar week. The stacked baseline revenue is $1,218,462. The revenue-weighted recorded margin is 20.5 percent. Accounting gross profit on that stack is not a year of profit and not operating profit.

`c` is the baseline unit price times `(1 − PROFIT/100)`. `PROFIT` is average acquisition cost as a percent of sales. It is not replacement cost and not marginal cost. The design notes already record that `PROFIT` changes while truncated `PRICE` is fixed in 5.3 percent of pairs. A less favorable case lowers the recorded margin by 10 percentage points, an assumption. On 10 pairs that shift would pass −100 percent and is capped there. On 10.2 percent of pairs the less favorable unit cost is at least the baseline price. On 2.6 percent of pairs the recorded margin is already nonpositive.

A candidate price is inside historical support when it lies between the minimum and maximum unit price that pair actually posted. Price increases are inside support less often than price cuts, because many last prices sit near the top of the pair's own range.

| Price change | Pairs inside that pair's history | Share of pairs | Share of stacked baseline revenue |
| --- | --- | --- | --- |
| −10% | 24,895 | 68.3% | 74.2% |
| −5% | 27,128 | 74.4% | 77.2% |
| −2% | 28,459 | 78.1% | 79.0% |
| −1% | 28,714 | 78.8% | 79.5% |
| +1% | 18,827 | 51.7% | 62.6% |
| +2% | 18,030 | 49.5% | 60.8% |
| +5% | 14,757 | 40.5% | 53.9% |
| +10% | 11,567 | 31.7% | 44.8% |

The comparable menu is the 9,326 pairs (25.6 percent of pairs, 38.8 percent of stacked baseline revenue) that can accommodate every move from −10 percent through +10 percent, including the 1, 2, and 5 percent steps. Their stacked baseline is $472,636 of revenue, 169,574 items, and $113,383 of accounting gross profit. The revenue-weighted margin on this subset is 24.0 percent. These pairs are selected by having a wide historical price range and a last price that is not at the edge of that range. The figures use this subset so the sample does not change from one price to the next.

A narrower menu, ±1 percent and ±2 percent only, is inside history for 15,737 pairs (43.2 percent of pairs, 54.1 percent of stacked revenue). The sign pattern below is the same on that larger set.

Moves outside a pair's own range are extrapolations. They are in the JSON under `all_pairs_including_extrapolations` and are not the decision sample.

## Accounting results on the comparable menu

Recorded acquisition-cost proxy. Quantity and revenue percents are the constant-elasticity formula. Gross-profit percents use this menu's margins.

| Price change | Case | Quantity | Revenue | Accounting gross profit |
| --- | --- | --- | --- | --- |
| −10% | Pooled −0.346 | +3.7% | −6.7% | −39.5% |
| −10% | Confirmatory −2.128 | +25.1% | +12.6% | −27.0% |
| −10% | Unit −1 | +11.1% | 0 | −35.2% |
| −10% | Assumed −3 | +37.2% | +23.5% | −20.0% |
| −5% | Pooled −0.346 | +1.8% | −3.3% | −19.4% |
| −5% | Confirmatory −2.128 | +11.5% | +6.0% | −11.7% |
| −5% | Unit −1 | +5.3% | 0 | −16.7% |
| −5% | Assumed −3 | +16.6% | +10.8% | −7.7% |
| −2% | Pooled −0.346 | +0.7% | −1.3% | −7.7% |
| −2% | Confirmatory −2.128 | +4.4% | +2.3% | −4.3% |
| −2% | Unit −1 | +2.0% | 0 | −6.5% |
| −2% | Assumed −3 | +6.2% | +4.1% | −2.6% |
| +2% | Pooled −0.346 | −0.7% | +1.3% | +7.6% |
| +2% | Confirmatory −2.128 | −4.1% | −2.2% | +3.9% |
| +2% | Unit −1 | −2.0% | 0 | +6.2% |
| +2% | Assumed −3 | −5.8% | −3.9% | +2.1% |
| +5% | Pooled −0.346 | −1.7% | +3.2% | +18.8% |
| +5% | Confirmatory −2.128 | −9.9% | −5.4% | +8.9% |
| +5% | Unit −1 | −4.8% | 0 | +15.1% |
| +5% | Assumed −3 | −13.6% | −9.3% | +4.4% |
| +10% | Pooled −0.346 | −3.2% | +6.4% | +37.1% |
| +10% | Confirmatory −2.128 | −18.4% | −10.2% | +15.7% |
| +10% | Unit −1 | −9.1% | 0 | +28.8% |
| +10% | Assumed −3 | −24.9% | −17.4% | +6.5% |

The ±1 percent rows are in the CSV. They have the same sign pattern as the ±2 percent rows.

On this menu, a 10 percent higher price under the confirmatory association used as ε would mean about $48,200 less revenue and about $17,800 more accounting gross profit, on a stacked baseline of $472,636. That sentence is arithmetic. It is not a forecast of what Dominick's would have received.

## Uncertainty

**Sampling uncertainty of M5.** The store-clustered interval for the confirmatory coefficient is [−2.179, −2.076]. Mapped through the revenue formula, a 10 percent price increase changes revenue by between −10.6 percent and −9.7 percent. The week-clustered and two-way standard errors, using the same 92-degree critical value as the baseline memo, widen that to about −11.1 percent to −9.3 percent and −11.2 percent to −9.2 percent. The promotion coefficient is not redrawn. Its covariance with the price coefficient is already inside the cluster-robust standard error of the price coefficient. Independent draws of the two coefficients were not used. This band is sampling uncertainty for the association. It is not a confidence set for a causal elasticity, and it does not flip the sign of the revenue change.

**Specification uncertainty.** The blank, coded, early-window, and late-window associations are all steeper than −1. On the same menu they keep the confirmatory pattern: a price cut raises revenue and lowers accounting gross profit; a price increase does the opposite. The pooled association is the case that flips the revenue sign. Treating −0.346 as the elasticity, a 10 percent price increase raises revenue by 6.4 percent. Treating −2.128 as the elasticity, the same increase lowers revenue by 10.2 percent.

**Cost.** Lowering the margin by 10 points cuts this menu's baseline accounting gross profit from $113,383 to $66,119. Price increases still raise accounting gross profit, and price cuts still lower it, under all four primary elasticities. The dollar gain from a price increase is larger when unit cost is higher, because the items no longer sold were carrying a higher assumed acquisition cost. That is an accounting identity under the constant-unit-cost assumption. It is not evidence that a higher cost makes a price increase more attractive as an operating decision. Costs that do not vary with the unit sold are omitted.

**Promotion status.** Among comparable-menu pairs whose baseline week is blank, 6,922 pairs, the blank-slice elasticity gives the same conflict: a 10 percent cut raises revenue 4.1 percent and lowers accounting gross profit 31.9 percent. Among 2,361 coded baseline weeks, the coded-slice elasticity gives a 19.6 percent revenue increase and a 23.4 percent gross-profit decrease for that cut. Holding the flag fixed does not remove the conflict between the two objectives.

**Recent shelves.** Pairs whose last week is 374 or later (the final contiguous stretch, beginning 7 November 1996) contribute 7,572 comparable-menu baselines and $436,408 of stacked revenue. Under the confirmatory association, a 10 percent price increase changes revenue by −10.2 percent and accounting gross profit by +14.8 percent. The sign pattern matches the full last-week menu.

**Product illustrations.** The three UPCs with the largest scanned item movement were selected before the profit comparison. Only a few of their stores can host the full ±10 percent menu.

| UPC | Description | Stores in the full menu | Baseline revenue | Baseline accounting gross profit |
| --- | --- | --- | --- | --- |
| 1600066610 | Cheerios, 15 oz | 12 of 93 | $1,406 | $217 |
| 3800000120 | Kellogg's Corn Flakes, 18 oz | 3 of 93 | $704 | $1.39 |
| 1600066510 | Cheerios, 10 oz | 4 of 93 | $289 | $13 |

Own-price revenue percents match the category formula. The corn-flakes gross-profit percent is not interpretable: the baseline accounting margin on those three stores is about a dollar, so a price move swings the percent by thousands. Report dollars there, or do not use the percent.

## Recommendation

No scenario is supported for deployment.

1. **What looks attractive only under an assumption the audit rejected.** If someone treats the pooled association (−0.346) as a causal elasticity, price increases of 1, 2, 5, and 10 percent raise both revenue and accounting gross profit on the comparable menu. Phase 5 did not adopt that coefficient as a causal elasticity. It is the association that mixes high-volume and high-price products in the cross-section.

2. **What is sensitive.** Under every steeper case — confirmatory, unit, assumed −3, blank, coded, and both week windows — revenue and accounting gross profit move in opposite directions at every nonzero price in the menu. A revenue objective points toward price cuts. An accounting-gross-profit objective points toward price increases. The sampling interval around M5 does not change that split. The split does change if the elasticity is the pooled association. Gross-profit percents also change with the margin assumption, and they break down when baseline gross profit is near zero.

3. **What the data cannot support.** A causal elasticity. A profit-maximizing markup. A competitor's response. Cross-cereal substitution. Operating profit. A uniform 10 percent increase for the pairs whose last price is already at the top of their history (about 68 percent of pairs). A claim that the stacked baselines are one week's category revenue.

4. **What to test before any price change.** Write the assignment and the weeks down before looking at the response. Hold the promotion calendar fixed. Measure substitution into other cereals and the change in store traffic. Record replacement cost rather than the average-acquisition-cost margin. Keep the tested prices inside the historical range of the tested UPC-store pairs.

## Guardrails

Prices in the decision table sit inside each included pair's observed unit-price range. Predicted quantities stay nonnegative because baseline movement is positive and the price ratio is positive. The less favorable margin is an explicit 10-point assumption, capped at −100 percent where the shift would leave the manual's scale. Retail gross profit is not operating profit. No Bertrand equilibrium was computed.

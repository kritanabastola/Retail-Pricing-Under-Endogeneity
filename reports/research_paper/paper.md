# Retail pricing under endogeneity: demand associations and conditional accounting scenarios for Dominick’s ready-to-eat cereals

Kritana Bastola  
University of South Florida, Econometrics and Quantitative Economics  
5 October 2026

## Abstract

This paper asks how item movement for ready-to-eat cereal at Dominick’s Finer Foods covaries with unit price, and which pricing statements survive once the endogeneity of shelf prices is taken seriously. The data are the Kilts Center scanner files for cereals, weeks 1–399 (14 September 1989 through 7 May 1997). The pre-specified confirmatory regression is a log-log association with UPC-by-store and week fixed effects and an incomplete promotion indicator. On 4,707,776 positive-sale rows the price coefficient is −2.128 (store-clustered standard error 0.026). A 10 percent higher unit price is associated with about an 18.4 percent lower item movement inside that specification. Pooled OLS on the same rows is −0.346. The gap is a difference between two associations. It is not a measured sign of omitted-variable bias, because the fixed-effects slope is not established as causal.

An identification audit rejects every candidate instrument, including the published Hoch, Drèze, and Purk (1994) everyday-price experiment, whose assignment and dates are not in the public files; a margin-derived acquisition cost, which is a function of the shelf price; lagged prices; other-store prices; price tiers; promotion flags; customer counts; demographics; and a national or exposure-weighted cost index, neither of which is in the files. Two-stage least squares is not estimated. Hypothetical accounting scenarios then apply stated elasticities only inside each pair’s historical price range. Under the confirmatory association used as a hypothetical elasticity, revenue and accounting gross profit move in opposite directions. No scenario is supported as a price to deploy. The practical implication is a designed price test with the promotion calendar held fixed, not a markup formula.

## 1. Research question and contribution

The question is how retail demand responds to product price changes, and under what assumptions that relationship can support a counterfactual pricing statement. The contribution is a closed empirical sequence on one category: a pre-specified association, an instrument audit that ends in “not identified,” and accounting scenarios that stay labeled as hypothetical. The sequence is designed so that a precise standard error cannot be mistaken for a causal elasticity.

Three boundaries are fixed before looking at coefficients. Oatmeal is reserved as a later robustness category and is not estimated here. Canned soup is deferred. A differentiated-products demand system in the sense of Nevo (2001) is out of scope: this paper does not estimate cross-price elasticities, recover marginal costs, or compute Bertrand markups.

## 2. Economic motivation

A grocery chain chooses regular prices, zone tiers, and promotions. A week the chain expects to be busy can be a week it cuts a price or runs a coupon. Scanned movement is then the quantity that clears at a chosen price, not an experiment. Chevalier, Kashyap, and Rossi (2003), using this same chain’s scanner data, document that retail prices tend to fall at seasonal demand peaks and that retail margins account for most of that movement. Their finding is a reason to expect shelf prices and demand shocks to move together. It is not a number imported into the regressions below.

The managerial object is also easy to overstate. Accounting gross profit on a scanned sale is not store operating profit. A price that raises one UPC’s revenue can steal movement from a neighboring cereal. Without substitution and without a competitor’s response, a category sum of own-price calculations is not a chain-wide optimum.

## 3. Related literature

Hoch, Drèze, and Purk (1994) report field experiments at Dominick’s on everyday low prices and high-low pricing. Their Table 1 includes ready-to-eat cereal at a 10 percent everyday price change. They describe category-by-category assignment of stores to EDLP, Hi-Lo, or control, with promotions continued in the ordinary way. The category volume and profit figures in that article are theirs. This paper does not reestimate them and does not treat them as UPC-store elasticities. Abrams, Gui, and Hortaçsu (2018) try to recover Study 1 labels from prices with a mixture model. A mixture label is an estimate, not the randomization file, and it is not used here.

Nevo (2001) estimates a random-coefficients discrete-choice system for ready-to-eat cereal and discusses brand-level market power. That design needs a substitution matrix and an equilibrium assumption this file does not support. The present paper stops at a single-product log-log association and says so.

Hausman (1996) is the usual citation for using a price in another market as an instrument, on the idea that a common cost shifts every price while demand shocks are independent across markets. Dominick’s is one chain in one metropolitan area, and the Kilts manual says promoted prices were supposed to be chainwide. That instrument is considered in Section 8 and rejected. Cameron, Gelbach, and Miller (2011) supply the two-way cluster variance used as a sensitivity. Clustering is an inference choice. It does not make price exogenous.

## 4. Institutional setting and data

Dominick’s Finer Foods was a Chicago-area grocer. The James M. Kilts Center for Marketing at the University of Chicago Booth School of Business distributes the scanner files for academic research. The Dominick’s Data Manual (created July 2013, updated October 2018) dates week 1 to 14 September 1989 and week 399, the last cereals week used here, to 7 May 1997. A Princeton catalog start year of 1987 disagrees with the manual and is not used. Any paper that uses the files must acknowledge the Kilts Center. The files describe a defunct chain. They are not current national demand.

The cereals movement extract has 6,602,582 rows. The manual’s printed total is 6,417,055. The counted CSV is the sample. No row is deleted to force the printed total. The header is `STORE`, `UPC`, `WEEK`, `MOVE`, `QTY`, `PRICE`, `SALE`, `PROFIT`, `OK`, `PRICE_HEX`, and `PROFIT_HEX`. There is no `DEAL` column. On every cereals row the truncated price and margin match the hexadecimal doubles within 0.0001, so the truncated fields are the ones used.

`MOVE` counts items. `QTY` is bundle size, not package size. Unit price is `PRICE / QTY`. Revenue is `PRICE × MOVE / QTY`. `PROFIT` of 25.3 means 25.3 cents of gross margin per dollar of sales. The manual identifies the underlying cost concept as average acquisition cost, not replacement cost. The implied unit cost, price times `(1 − PROFIT/100)`, is therefore an accounting proxy. It is not marginal cost, and because it is built from the shelf price it is not an instrument.

`SALE` codes B, C, and S are the manual’s bonus buy, coupon, and simple price reduction. Blank does not prove a regular-price week. The file also contains `G` and, once in cereals, `L`. Those letters are left unclassified. The confirmatory indicator is 1 when `SALE` is B, C, or S, so `G` and `L` sit in the reference group.

The log sample keeps `OK = 1`, positive price, positive bundle quantity, and positive movement: 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks, and 36,443 UPC-store pairs. Every nonpositive-movement row in this extract also has a nonpositive price, so there is no `OK = 1` row with a positive price and zero movement for a Poisson model to restore. Thirty-two week numbers inside 1–399 are absent, including 16 February 1995 through 16 August 1995. Week 219 (18–24 November 1993) is present and is entirely zero price and zero movement, which is why the audited file has 367 week numbers and the log sample has 366. Absent weeks are not filled with zero.

Seven movement store IDs are missing from the store-codebook transcription, so their price tier is null. The codebook is a 1992 zone snapshot, not a weekly price.

## 5. Descriptive evidence

The panel is unbalanced. The median UPC-store pair has 78 log-sample weeks. Most log-price variation is the identity of the product: after UPC means, 16.8 percent of the sum of squares remains, and after UPC-store means, 15.8 percent remains. After pair and week effects, 11.5 percent remains. That is enough to estimate a slope. It is not evidence that the remaining price changes are exogenous.

Unit price changes by more than $0.001 in 31,167 of 36,443 pairs (85.5 percent), which clears a pre-specified 20 percent screen for reading a within-pair slope. The median within-pair log-price range is a peak-to-trough factor, not a typical weekly change. About 16 percent of successive observed weeks inside a pair show a unit-price change above $0.001. Prices are often unchanged from the previous observed week and still move over the life of most pairs.

Mean movement in the audited file is 14.08 items per row, with movement equal to zero on 28.0 percent of rows. Mean movement in the log sample is higher because zeros are out. Gross sales in the log sample, from the manual’s revenue identity, are about $262 million over the whole window. Monthly mean movement varies, so seasonality is visible. Week fixed effects are in the confirmatory equation for that reason. They do not absorb a promotion that hits one UPC across the chain.

## 6. Model specification

The confirmatory equation, written before estimation, is

\[
\log Q_{ist} = \alpha_{is} + \gamma_t + \beta \log P_{ist} + \delta D_{ist} + \varepsilon_{ist},
\]

where \(Q\) is item movement, \(P\) is unit price, \(D\) is the B/C/S indicator, \(\alpha_{is}\) is a UPC-by-store effect, and \(\gamma_t\) is a week effect. \(\beta\) is the difference in log movement associated with a difference in log unit price after those controls. Under a constant-elasticity reading it would be an elasticity. In this paper that reading is conditional on the specification. It is not a causal elasticity.

The comparison ladder, also pre-specified, is pooled OLS (M0), pooled OLS with the promotion flag (M1), UPC effects (M2), UPC and store effects, pair effects (M3), pair and week effects, calendar-month and year-month alternatives (M4), and the confirmatory model (M5). UPC-by-week effects are excluded because they would absorb the chainwide UPC promotions the manual describes as the chain’s promoted-price policy. Store-by-week effects are excluded because they would absorb a category-wide experimental shift if one were later established. Standard errors cluster by store, with a Student t reference on 92 degrees of freedom. Week-clustered and Cameron-Gelbach-Miller two-way standard errors are sensitivities. Two-way variances are positive semidefinite for the linear models reported here.

A coefficient on \(\log(1 + Q)\) is not estimated. It would not be an elasticity. A level regression of items on dollars, and a Poisson pseudo-maximum-likelihood fit on the same positive rows, are reported as different estimands. They are not substituted for M5 after seeing the results.

## 7. Identification strategy and limitations

The causal parameter of interest is the effect of an exogenous unit-price change on item movement in a Dominick’s store-week. M5 equals that parameter only if the price changes left inside a UPC-store pair, after week effects and the coded promotion flag, are independent of the demand shocks left in the residual. The audit does not adopt that assumption.

Sources of possible dependence, without a claimed sign for the bias, are simultaneity between the shelf price and scanned movement; product attributes the chain observes and the file does not; promotions chosen in response to expected demand; expected store traffic; assortment and which rows exist; unobserved competitive pressure, including Cub Foods competition lined up with zone tiers; seasonality and UPC-specific demand shocks that survive week effects; and measurement error in price, movement, and `SALE`. Fixed effects change which variation remains. They do not, by themselves, make the remainder exogenous. Store clustering is not an exogeneity proof.

The published experiment is the most credible design in the literature on these files, and it is not usable here. The public movement, UPC, store, demographics, and customer-count files do not contain a store-category treatment arm or a cereal week window. A teaching-note date is not treated as a project fact. Until the assignment is in hand and checked against prices, no week is called experimental and M5 is not described as the Hoch–Drèze–Purk treatment effect.

Table 1 summarizes the instrument audit. Verdicts were fixed before correlations were computed. A correlation with price is descriptive. It is not a first stage, and an F statistic would not repair an exclusion failure.

| Candidate | Correlation with log price | Verdict |
| --- | ---: | --- |
| Hoch–Drèze–Purk assignment | Not in the files | Rejected |
| Log average acquisition cost | 0.886 | Rejected. Built from the shelf price |
| Lagged log unit price | 0.928 | Rejected. Promotions persist |
| Other stores’ leave-one-out price | 0.990 | Rejected. One chain, one city |
| Price tier | 0.087, and zero within the pair | Rejected. Time-invariant policy |
| Coded promotion flag | −0.210 | Rejected as an instrument. Kept as a control |
| Customer counts and 1990 demographics | Not constructed | Rejected |
| National or exposure-weighted cost index | Not in the files | Rejected |

A pure weekly cost index would be absorbed by the week effects already in M5. An exposure interaction would need its own exclusion argument. Package mix is a product attribute. Weak-instrument diagnostics, weak-instrument-robust confidence sets, and an overidentification test are not applicable, because no instrument was estimated. A Hausman test was not computed: it would require an estimator already known to be consistent for a causal parameter.

The most serious remaining threat is the variation M5 actually uses. Inside a UPC-store pair, after a common cereal-week shock and an incomplete promotion flag, the remaining price changes are still chosen. Chainwide promotions of one UPC survive week effects.

## 8. Estimation results

Table 2 reports the price coefficient from the comparison ladder. All figures are store-clustered. The associated movement column applies \(\exp(\hat\beta \log 1.10) - 1\) to the fitted association.

| Model | Controls | Coefficient | Store SE | 95 percent interval | Movement at +10% price |
| --- | --- | ---: | ---: | --- | ---: |
| M0 pooled | Intercept | −0.346 | 0.035 | [−0.415, −0.277] | −3.2% |
| M1 pooled | Promotion flag | −0.219 | 0.035 | — | −2.1% |
| M2 | UPC effects | −2.290 | 0.077 | — | −19.6% |
| M2 | UPC and store | −2.392 | 0.045 | — | — |
| M3 | Pair effects | −2.421 | 0.045 | — | — |
| M3 | Pair and week | −2.629 | 0.028 | — | −22.2% |
| M5 confirmatory | Pair, week, B/C/S flag | −2.128 | 0.026 | [−2.179, −2.076] | −18.4% |

Product fixed effects move the association from about −0.35 to about −2.29 because the cross-section mixes products whose volume and average price move together. Week effects steepen the pair slope to −2.629. The promotion flag brings it back to −2.128. The M5 promotion coefficient is 0.450 (SE 0.005): at a given price, a coded promotion week has about 57 percent higher movement. That partial gap is not the total promotion effect, and the flag is incomplete.

The M5 store-clustered interval lies below −1. Applying the same 92-degree critical value to the week-clustered standard error (0.052) and the two-way standard error (0.058) still leaves intervals below −1. That is a property of the association. It would support a revenue conclusion only if \(\beta\) were a constant causal elasticity, which Section 7 does not establish. Within \(R^2\) for M5 is 0.202. Overall \(R^2\) is 0.628. M5 was not chosen for having the largest \(R^2\).

Figure `baseline_01_coefficients.png` plots the ladder. The hypotheses written before the fit were that the confirmatory slope is negative and that it differs from pooled OLS. Both agree with the table. The difference is not a Hausman exogeneity test.

On the same positive rows, pooled PPML gives −0.783 and pair-effect PPML gives −3.279. A linear items-per-dollar model with pair and week effects gives −52.8 items per dollar. At the median unit price of $3.15 and median movement of 13, that slope translates to a much steeper ratio than \(\beta\). The translation is not \(\beta\). Restoring 43,426 `OK = 0` rows with positive price and movement changes M5 from −2.128 to −2.125. The sign does not flip. Those rows are not the confirmatory sample.

Confirmatory residuals have a successive-week correlation of about 0.31 inside pairs. Binned residual means are not flat, so a single log-log slope is an average. Dropping the 4,708 rows above the 99.9 percentile of Cook’s distance moves the coefficient from −2.128 to −2.118. The tail does not create the result.

## 9. Robustness and sensitivity

Table 3 keeps the observational reading. Every subsample clears the within-pair price-change screen. Moving `G` and `L` into the promotion indicator changes the price coefficient from −2.128 to −2.046. The sign does not flip. Both versions are reported.

| Check | Rows | Stores | Coefficient | Store SE |
| --- | ---: | ---: | ---: | ---: |
| Blank `SALE` only | 4,350,772 | 93 | −1.383 | 0.033 |
| Coded B/C/S only | 345,945 | 93 | −2.696 | 0.030 |
| Weeks 1–200 | 2,528,421 | 86 | −1.870 | 0.036 |
| Weeks 201–399 | 2,179,355 | 93 | −2.428 | 0.030 |
| High-tier stores | 1,357,188 | 25 | −2.082 | 0.059 |
| CubFighter stores | 517,634 | 9 | −2.145 | 0.059 |
| M5 plus next week’s log price | 4,509,599 | 93 | −2.389 | 0.025 |

Blank is still not a confirmed regular price. The blank and coded slopes are far enough apart that one elasticity is a poor summary of the two slices. Both store-clustered intervals lie below −1. The week split was fixed at week 200 before these coefficients were computed. The late window contains the 1995 gap. The two half-sample intervals exclude each other’s point estimates, so the magnitude is not stable. High-tier and CubFighter point estimates sit near M5, and their intervals are rough because the cluster counts are 25 and 9.

On the lead specification, next week’s log price has coefficient 0.459 (SE 0.010). A nonzero lead rejects the narrow claim that, after the confirmatory controls, movement is related only to the current price. A zero lead would not have proved exogeneity either. The lead does not sign the bias in M5.

Figure `identification_01_robustness.png` plots these coefficients against the M5 reference line.

## 10. Conditional counterfactuals

Scenarios use \(Q_1 = Q_0 (P_1/P_0)^\varepsilon\), \(R_1 = P_1 Q_1\), and \(G_1 = (P_1 - c) Q_1\), with \(c\) held at a baseline unit acquisition-cost proxy. \(\varepsilon\) is either an estimated association used hypothetically or a round assumption (−1, or −3). Promotion status is held at the baseline week. Other products’ prices and competitor prices are held constant because they are not in the design. Category totals are sums of own-price hypotheticals.

Each pair’s baseline is its last log-sample week. Those weeks are not contemporaneous, so stacked dollars are not one week’s category revenue. A candidate price is inside support when it lies between that pair’s own minimum and maximum unit price. A 10 percent increase from the last price is inside history for 31.7 percent of pairs. The comparable menu — pairs that can accommodate every step from −10 percent to +10 percent — contains 9,326 pairs, 25.6 percent of pairs and 38.8 percent of stacked baseline revenue. On that menu the stacked baseline is $472,636 of revenue and $113,383 of accounting gross profit. The revenue-weighted margin is 24.0 percent. These pairs are selected by having a wide historical range and a last price that is not at the edge.

| Price change | ε = −0.346 revenue / gross profit | ε = −2.128 revenue / gross profit | ε = −3 revenue / gross profit |
| --- | --- | --- | --- |
| −10% | −6.7% / −39.5% | +12.6% / −27.0% | +23.5% / −20.0% |
| +10% | +6.4% / +37.1% | −10.2% / +15.7% | −17.4% / +6.5% |

Under the confirmatory association, a 10 percent higher price on this menu corresponds to about $48,200 less revenue and about $17,800 more accounting gross profit. That sentence is arithmetic. The store-clustered interval for M5 maps the same price increase into a revenue change of −10.6 to −9.7 percent. The week and two-way standard errors widen that band only to about −11 percent. The band does not cross zero. Replacing −2.128 with the pooled association flips the revenue sign. The sampling interval and the specification range answer different questions, and neither is a causal confidence set. The promotion coefficient is not redrawn; its covariance with the price coefficient is already inside the cluster-robust standard error of the price coefficient.

A 10-point less favorable margin, an assumption, cuts baseline accounting gross profit on the menu from $113,383 to $66,119. Price increases still raise accounting gross profit and price cuts still lower it. The dollar gain from selling fewer units is larger when the assumed unit cost is higher, because the avoided units carry a larger acquisition-cost proxy. That identity is not an operating recommendation. Costs that do not vary with the unit are omitted.

Blank-baseline and coded-baseline slices, and shelves from 7 November 1996 onward, keep the same conflict between revenue and accounting gross profit whenever \(\varepsilon\) is steeper than −1. Figures `scenario_01_revenue.png` and `scenario_02_gross_profit.png` plot the menu. No Bertrand price is computed.

## 11. Practical implications

No price in this study is supported for deployment. If a manager treats the pooled association as causal, small price increases raise both revenue and accounting gross profit in the scenario arithmetic. That coefficient mixes products in the cross-section, and the identification audit does not adopt it. If a manager treats the confirmatory association as causal, revenue and accounting gross profit point in opposite directions: cuts raise hypothetical revenue and lower hypothetical gross profit. The data do not say which objective the chain would have maximized, and they do not establish the elasticity.

The action the evidence does support is a test, not a rollout. Write the stores, the products, and the weeks down before looking at the response. Hold the promotion calendar fixed, so the test is not a promotion under another name. Measure substitution into other cereals and the change in store traffic. Record replacement cost rather than the average-acquisition-cost margin. Keep tested prices inside the historical range of the tested pairs. A uniform 10 percent increase is already outside history for about two-thirds of pairs at their last observed price.

## 12. Limitations and future research

External validity stops at this chain, this category, and 1989–1997. The log sample conditions on positive scanned movement. Stockouts are not a separate state. The promotion flag is incomplete. The magnitude of the association is not stable across the pre-specified week split or across blank and coded weeks. Baselines in the scenarios are not one calendar week. Own-price arithmetic ignores cannibalization.

A later paper could use the Hoch–Drèze–Purk assignment if the original store-category arms and cereal weeks are obtained and checked against prices before any second stage. Oatmeal, specified as a robustness category, has not been estimated. A substitution system would be a different project and would still need a cost and a conduct assumption that these files do not provide. Interview claims and a deployed pricing tool are out of scope until those gaps are closed in the result files, not in prose.

## References

Abrams, Eliot, George Gui, and Ali Hortaçsu. 2018. “Finding Exogenous Variation in Data.” Working paper, 7 May 2018. SSRN 3176846.

Cameron, A. Colin, Jonah B. Gelbach, and Douglas L. Miller. 2011. “Robust Inference with Multiway Clustering.” *Journal of Business & Economic Statistics* 29 (2): 238–249.

Chevalier, Judith A., Anil K. Kashyap, and Peter E. Rossi. 2003. “Why Don’t Prices Rise During Periods of Peak Demand? Evidence from Scanner Data.” *American Economic Review* 93 (1): 15–37.

Hausman, Jerry A. 1996. “Valuation of New Goods under Perfect and Imperfect Competition.” In *The Economics of New Goods*, edited by Timothy F. Bresnahan and Robert J. Gordon. Chicago: University of Chicago Press.

Hoch, Stephen J., Xavier Drèze, and Mary E. Purk. 1994. “EDLP, Hi-Lo, and Margin Arithmetic.” *Journal of Marketing* 58 (4): 16–27.

Kilts Center for Marketing. 2018. *Dominick’s Data Manual*. University of Chicago Booth School of Business. Created July 2013, updated October 2018.

Kilts Center for Marketing. Dominick’s Dataset. University of Chicago Booth School of Business. https://www.chicagobooth.edu/research/kilts/research-data/dominicks. Consulted 5 October 2026.

Nevo, Aviv. 2001. “Measuring Market Power in the Ready-to-Eat Cereal Industry.” *Econometrica* 69 (2): 307–342.

## Appendix. Reproducibility

The working copy has no recorded git remote. Commands below use the project virtual environment and read gitignored Kilts files that are not part of the result tables. Synthetic unit tests do not read those files.

```text
python -m pricing_research.data.build
python -m pricing_research.reporting.explore
python -m pricing_research.estimation.run
python -m pricing_research.estimation.identify
python -m pricing_research.economics.counterfactual
streamlit run src/pricing_research/dashboard/app.py
```

The log-sample hash recorded with the baseline is `023bd0b03df848a782b8bfab3b2ddce418543b08202736047ea418f923b4b4fb`. Coefficients in this paper are rounded from `reports/tables/baseline_regression.csv`, `reports/tables/identification_robustness.csv`, and `reports/results/pricing_scenarios.json`. The dashboard reads those files. It does not contain a second copy of the estimator. `statsmodels` and `linearmodels` are declared and were not imported. The within estimator is the project’s OLS routine, checked on synthetic designs with a known slope. A full `pytest` run after the dashboard tests is recorded in `docs/phase_status.md`.

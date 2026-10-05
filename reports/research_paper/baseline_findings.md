# Baseline findings: cereals log-log associations

These numbers were computed by `python -m pricing_research.estimation.run` on 5 October 2026. The full-precision file is `reports/results/baseline_models.json`. The coefficient table is `reports/tables/baseline_regression.csv`. Figures are `reports/figures/baseline_01_coefficients.png` through `baseline_04_binned_residuals.png`. Definitions written before the fit are in `docs/baseline_estimands.md`.

Every slope below is a conditional association. None is a causal elasticity. The confirmatory model was not chosen because its R-squared is the largest or because the price coefficient is negative.

## Estimand and sample

The outcome is `log(MOVE)`, the natural log of item movement. The price regressor is `log(PRICE / QTY)`, the natural log of dollars per item. A coefficient β maps a 10 percent price difference into an associated movement difference of `exp(β × log(1.10)) − 1`.

The sample is the cereals log sample: `OK = 1`, positive price, positive bundle quantity, and positive movement. The file hash matches `reports/results/data_quality.json`. The regression uses 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks, and 36,443 UPC-store pairs. The audited panel still has all 6,602,582 movement rows. Absent UPC-store-weeks were not filled with zero.

Primary intervals are store-clustered and use a Student t reference with 92 degrees of freedom (critical value 1.986). Week-clustered and two-way standard errors are sensitivities. Two-way variances were positive semidefinite for every linear model reported here, so those standard errors are shown. Clustering does not make the slope exogenous.

The within-pair screen is cleared on this sample. Unit price changes by more than $0.001 in 31,167 of 36,443 pairs, which is 85.5 percent. The 20 percent floor in the analysis plan is about the share of pairs, not the share of variance.

## What variation the fixed effects leave

These shares were computed before the slopes were used.

| Specification | Share of log-price variance remaining |
| --- | ---: |
| Pooled (M0, M1) | 1.000 |
| UPC effects (M2) | 0.168 |
| UPC and store effects | 0.162 |
| UPC-store pair effects (M3) | 0.158 |
| Pair and week effects (M3, and M5 before the promotion regressor) | 0.115 |
| Pair and calendar month (M4) | 0.158 |
| Pair and year-month (M4) | 0.117 |

Product identity absorbs most of the price variation. Store effects, added to product effects, remove little more. Week effects remove some of what remains inside the pair. After pair and week effects, 11.5 percent of the log-price sum of squares is still there. Residualizing the coded promotion indicator as well leaves 9.2 percent. About four-fifths of the pair-and-week price variation is not a linear function of the B/C/S flag. The promotion dummy itself keeps 89.2 percent of its variance after pair and week effects, so the two regressors in the confirmatory model are not the same variable.

UPC-by-week and store-by-week effects were not fit. The first would absorb chainwide promotions of one UPC. The second would absorb a category-wide store-week price shift. The remaining variation is enough to estimate the pre-specified association. It is not evidence that the remaining price changes are exogenous. Chainwide promotions of a single UPC survive week effects, and those promotions are chosen.

## Coefficient ladder

Store-clustered standard errors are in parentheses. The sample for M0 through M5 and for the level and PPML rows is the same 4,707,776 log-sample rows, except the `OK = 0` sign check.

| Model | Price coefficient | 10% price, associated movement | Within R² |
| --- | ---: | ---: | ---: |
| M0 pooled OLS | −0.346 (0.035) | −3.2% | 0.012 |
| M1 pooled, promotion held fixed | −0.219 (0.035) | −2.1% | 0.049 |
| M2 UPC effects | −2.290 (0.077) | −19.6% | 0.131 |
| M2 UPC and store effects | −2.392 (0.045) | −20.4% | 0.161 |
| M3 pair effects | −2.421 (0.045) | −20.6% | 0.194 |
| M3 pair and week effects | −2.629 (0.028) | −22.2% | 0.177 |
| M4 pair and calendar month | −2.414 (0.045) | −20.6% | 0.193 |
| M4 pair and year-month | −2.605 (0.028) | −22.0% | 0.175 |
| M5 confirmatory: pair, week, and B/C/S | −2.128 (0.026) | −18.4% | 0.202 |

The pooled 95 percent interval for M0 is [−0.415, −0.277]. The confirmatory interval is [−2.179, −2.076]. Applying the same 92-degree critical value to the larger week-clustered and two-way standard errors gives [−2.231, −2.024] and [−2.242, −2.013]. Using the week-cluster degrees of freedom instead would change those bounds by about 0.001. All three exclude zero. All three also lie below −1. That is a statement about this association: a 10 percent higher unit price is associated with about an 18 percent lower item movement, and the store-clustered interval for that translation is tight. It is not a statement that raising a shelf price would cut revenue. The interval would support that revenue arithmetic only if β were a constant causal elasticity. That assumption is not established.

The ladder moves in one place, and then it settles. Going from pooled OLS to UPC effects changes the price coefficient from −0.35 to −2.29. Adding store effects, and then replacing additive product and store effects with a pair effect, moves it only from −2.29 to −2.42. Calendar-month effects do almost nothing beyond the pair effect (−2.41 versus −2.42). Week effects, and year-month effects, make the slope a bit steeper (−2.63 and −2.61). The coded promotion indicator then brings the pair-and-week slope from −2.63 back to −2.13.

That pattern matches the Phase 3 description without turning the correlations into slopes. Across products, higher volume and higher average log price moved together. Inside a UPC-store pair, higher log price and higher log movement moved in opposite directions. The pooled coefficient mixes those two relationships, so it is much closer to zero than the within-product coefficient. Product fixed effects are what separate them. The confirmatory specification was already the pair-and-week model with the promotion indicator. The estimates do not create a reason to replace it with the specification that has the largest R-squared. M5 does have the largest within R-squared in this table, 0.202, and its overall R-squared is 0.628 because the fixed effects themselves fit a great deal. Those figures describe fit. They are not the selection rule.

Hypothesis 1, stated before estimation, was that the confirmatory coefficient is negative. The estimate is −2.128. The store-cluster t statistic on 92 degrees of freedom is −81.6. The sign statement agrees with the estimate. A non-negative result would have been reported; it did not occur.

Hypothesis 2 was that the pooled coefficient differs from the confirmatory coefficient on the same rows. The gap, pooled minus confirmatory, is 1.782 with a store-clustered standard error of 0.026 (t = 69.0 on 92 degrees of freedom). The coefficients differ. This comparison uses the covariance of the two store-clustered estimators. It is not a Hausman test, and a rejection is not evidence that the fixed-effects slope is exogenous.

Hypothesis 3, the oatmeal sign check, was not estimated. Oatmeal remains the robustness category.

## Promotion

In M5 the coefficient on `1{SALE in {B, C, S}}` is 0.450 (store-clustered SE 0.005). At a given unit price, a coded promotion is associated with about 57 percent higher item movement (`exp(0.450) − 1`). That is a partial association. Promotions also change the price, and the price coefficient is holding that price difference fixed, so 0.450 is not the total gap between promoted and other weeks.

The pooled promotion coefficient is larger, 0.682 (SE 0.009), because it still compares different products and stores. Holding the promotion flag fixed moves the pooled price slope from −0.346 to −0.219. Holding it fixed inside the pair-and-week model moves the price slope from −2.629 to −2.128. The flag matters for magnitude in both cases. It does not flip the sign.

Blank weeks are still not confirmed regular-price weeks. `G` and `L` remain in the reference group with the blanks. If those unclassified weeks behave like promotions, the reference group contains some promoted weeks and the promotion coefficient is smaller than a complete promotion contrast. They were not recoded.

## Zeros, selection, and other functional forms

Log movement is undefined at zero sales. On the audited file, 1,850,703 rows have nonpositive movement, and every one of those rows also has a nonpositive price. Among `OK = 1` rows with a positive unit price, the count of zero-movement rows is 0. A log-price PPML cannot put those zero-sale rows back, because the log price is undefined when the recorded price is zero. `log(1 + MOVE)` was not estimated. Its coefficient would not be an elasticity.

PPML on the log sample is a comparison of functional form, not a correction for the zeros. It estimates the elasticity of the conditional mean of movement. Pooled PPML gives −0.783 (store-clustered SE 0.028). Pair-effect PPML gives −3.279 (SE 0.050). Both are negative. Both are steeper than the matching log-outcome OLS slopes (−0.346 and −2.421). The conditional mean and the mean of the log are different objects. The pair PPML is not the confirmatory estimate.

A linear model of item movement on the dollar unit price, with the same pair and week effects, gives −52.8 items per dollar (SE 1.93). At the log-sample median, $3.15 and 13 items, that slope translates to about −12.8. That translation is not β. A one-dollar price difference is large relative to typical cereal prices, and a slope of −53 items per dollar is large relative to median movement of 13 items. The linear form can be precisely estimated and still be a poor summary of a relationship that is closer to log-log. It is reported so the disagreement is visible. It does not replace M5.

Restoring the 43,426 `OK = 0` rows that still have positive price, positive bundle quantity, and positive movement produces a confirmatory-style price coefficient of −2.125 on 4,751,202 rows. The sign matches M5. The estimates differ by about 0.002. This check does not replace the log sample. The 677 rows with positive movement and a nonpositive price cannot enter a log-price regression.

## Inference, residuals, and influence

Store clustering allows arbitrary correlation across products and weeks inside a store. The within-pair correlation of successive confirmatory residuals, using the previous observed week rather than a filled calendar lag, is 0.31. Serial correlation is present, which is why the primary standard error is not an iid standard error. Store clustering does not cover a shock that hits the same UPC in many stores in one week. Week clustering covers that kind of common week shock and misses dependence across weeks. For M5 the week-clustered price standard error is 0.052 and the two-way standard error is 0.058, against 0.026 for the store cluster. Precision is worse under the sensitivities. The sign and the conclusion that the association is steeper than −1 are unchanged. Ninety-three stores is a moderate number of clusters. The t interval is an approximation, not an exact finite-sample result.

The confirmatory residual has standard deviation 0.56 log points and skewness −0.32. The median residual is 0.03. The 1st percentile is −1.63 and the 99th is 1.36. A thin left tail extends well beyond that. Absolute studentized residuals exceed 4 on 21,353 rows, 0.45 percent of the sample. Dropping the 4,708 rows above the 99.9 percentile of Cook's distance, as a diagnostic only, moves the price coefficient from −2.128 to −2.118. Those rows do not account for the result. The diagnostic sample is not a new specification.

Mean residuals in quantile bins of residualized log price are not a flat line. Across the bins they range from about −0.11 to about 0.11 log points, with the lowest bin mean near a residualized log price of −0.11 and higher means at both ends of the price range. The bend is small relative to the residual standard deviation of 0.56, and it is large enough to say that a single log-log slope is an average association. It is not the shape of every price bin. That limit matters for any later counterfactual that treats β as a constant elasticity. It is not a reason to search for a new confirmatory equation after seeing the bins.

## What is still unidentified

The association is not the effect of an exogenous price change. Demand shocks can still move the shelf price inside a pair and a week. Coded promotions are held fixed in M5; uncoded promotions, costs, and local demand shocks are not. Week effects do not absorb a promotion that is specific to one UPC. No instrument was used. Average acquisition cost, lagged prices, other-store prices, and price tier remain rejected as default instruments. The Hoch, Drèze, and Purk assignment file is still not in the estimated specification.

## Design revision

No revision. The confirmatory equation, the cereals log sample, the treatment of `G` and `L`, the refusal to zero-fill, and the rejection of a causal IV are unchanged. The estimates agree with the two cereals hypotheses that were written down before the fit. The level model, the PPML slopes, and the curved residual bins change the magnitude one would carry into a counterfactual. They do not change which equation is confirmatory.

# Model card

| Item | Status after the paper, memo, and dashboard |
| --- | --- |
| Model estimated | Conditional log-log associations. The confirmatory fit is UPC-by-store and week fixed effects plus the incomplete promotion indicator. It is not a causal elasticity. |
| Confirmatory price coefficient | −2.128 on the cereals log sample, store-clustered SE 0.026. Source: `reports/results/baseline_models.json`, model `M5_confirmatory`. |
| Dependent variable | `log(MOVE)`, positive scanned item movement |
| Price | `log(PRICE / QTY)` |
| Sample | Ready-to-eat cereals log sample: 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks. The audited file keeps all 6,602,582 movement rows. |
| Identification | Not established. Phase 5 Branch B. See `reports/research_paper/identification_audit.md` |
| Validation | Synthetic checks that the within estimator, cluster interval, PPML slope, and regression table recover known inputs or reject invalid ones. The Kilts fit is a separate command. |
| Metrics | Associations are in the baseline memo. Hypothetical revenue and accounting gross profit are in `reports/research_paper/pricing_scenarios.md`. No scenario is supported for deployment. |
| Intended use | Historical research, the paper and memo, and a dashboard that reads the saved files |
| Out of scope | A deployed pricing system, a credit-risk model, a claim about current shoppers, a structural Bertrand model |

Update this card only from a result file written by code that was run.

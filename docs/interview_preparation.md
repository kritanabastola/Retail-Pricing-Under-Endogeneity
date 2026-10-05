# Interview preparation

These answers describe the cereals project as it stands after the identification audit and the hypothetical price scenarios. The confirmatory coefficient is an association. It is not a causal elasticity. Numbers below are the saved estimates: −2.128 (store-clustered standard error 0.026) on 4,707,776 positive-sale rows.

## Why this economic question?

Retailers set shelf prices and then observe sales, so a regression of quantity on price mixes the demand curve with the chain's pricing rule. I wanted a question where that problem is the object of the study, not a footnote: how cereal movement at Dominick's covaries with unit price, and which pricing statements survive once that endogeneity is taken seriously.

## Why this dataset?

The Kilts Center Dominick's files are a public academic scanner panel with store, UPC, week, movement, price, a promotion code, and a margin field, for a chain that was also the site of a published pricing experiment. Ready-to-eat cereals are differentiated, separated from oatmeal in the manual, and were one of the categories in Hoch, Drèze, and Purk (1994). The cereals movement file is large enough for store-clustered inference: 6,602,582 audited rows and 4,707,776 positive-sale rows, 93 stores, 489 UPCs, and 366 weeks in the log sample. It is a historical Chicago chain from 1989 to 1997, not a current national panel.

## What is price endogeneity?

Price is endogenous for demand if it is correlated with the unobserved part of demand. A promotion, a local demand shock, or a manager responding to slow sales can move the shelf price and the error term together. Ordinary least squares then does not recover the slope of demand.

## What causes simultaneous price and quantity movements?

Quantity demanded depends on price. The chain also chooses price using information about demand, cost, and promotions. In one week those two relationships are both operating, so an observed pair (price, movement) is an equilibrium outcome, not an experiment. Chainwide promotions are a concrete version of the same problem: they shift many stores' prices and quantities at once.

## What does β estimate?

In the confirmatory equation, β is the partial association between log item movement and log unit price after UPC-by-store effects, week effects, and an incomplete promotion flag. A 10 percent higher unit price is associated with about an 18.4 percent lower movement inside that specification. β is not the effect of an exogenous price change. The audit did not establish that.

## Why fixed effects?

Pooled OLS compares expensive products and high-volume products as well as price changes for the same product. UPC-by-store effects use only the price variation within a product-store pair. Week effects absorb shocks that hit every cereal in a week. That is why the pooled slope (−0.346) and the confirmatory slope (−2.128) answer different questions. The gap is not, by itself, the sign of omitted-variable bias.

## Why this clustering scheme?

The same store is observed for many weeks, so residuals within a store are not independent. Store clustering allows arbitrary correlation inside a store and treats stores as the sampling units. The 95 percent interval uses a Student t reference with 92 degrees of freedom, one less than the 93 stores. Week-clustered and two-way standard errors are reported as sensitivities. Clustering changes the standard error. It does not make price exogenous.

## Why not ordinary OLS alone?

The pooled regression is in the paper, on the same 4,707,776 rows. It is much flatter because it uses cross-product differences. A pricing decision is about changing one product's price, so the within-product association is the relevant descriptive object. Even that object is not causal. Reporting only the pooled slope would hide the specification the design named in advance.

## What supports the instrument's exclusion restriction?

Nothing that I was willing to defend. The Hoch, Drèze, and Purk assignment file is not in the public bundle. Average acquisition cost constructed from the recorded margin is a function of shelf price. Lagged prices and other-store prices share promotions and demand shocks. Price tier does not vary within a store. The promotion flag is an incomplete control, not a random assignment. No instrument was marked approved, and two-stage least squares was not estimated on the scanner rows.

## How could the IV fail?

A valid instrument has to move price and be excludable from demand. A margin-derived cost fails exclusion because it is built from the price. A lagged price fails if promotions or demand shocks persist. Another store's price fails if the chain sets promotions centrally. A strong first stage does not repair any of those failures. A synthetic example in the repository recovers a known slope when the instrument is valid and misses it when the instrument also shifts demand. That example uses no Kilts rows.

## What is the economic meaning of the confidence interval?

The reported interval, about [−2.18, −2.08], is a store-clustered sampling interval for the confirmatory association. If the model were the data-generating process and stores were the independent draws, that interval would cover the association's sampling uncertainty. It is not an interval for a causal elasticity, and passing the scenario arithmetic through it does not create one. Specification uncertainty, from −0.346 in the pooled model to −2.128 in the confirmatory model, is much larger and does change the sign of a revenue calculation.

## How does the model deal with promotions?

The confirmatory specification includes a dummy equal to one when `SALE` is B, C, or S. Blank is not treated as a verified regular price. Codes G and L are unclassified and stay in the reference group. The slope is about −1.38 on blank weeks and about −2.70 on coded-promotion weeks, so the promotion control does not make the price association stable. A blank field can still hide merchandising the code does not record.

## What makes the model vulnerable to omitted variables?

Week effects absorb only shocks common to all cereals that week. A UPC-specific promotion, a local taste shift, or a competitor price can remain inside the pair and move both the shelf price and movement. The adjacent-week price lead is nonzero, which rejects a story in which only the current price matters, and it does not sign the bias. There is no competitor-price series and no substitution system.

## What limits external validity?

The estimates describe one defunct Chicago grocer from September 1989 through May 1997. Shoppers, wholesale costs, and private-label strategy have changed. The log sample conditions on a positive scanned sale, so weeks with zero movement are not in the regression. A result for cereals need not carry over to soup or to a current national chain. Oatmeal was named as a robustness category and was not estimated.

## Why might simulated profit differ from realized profit?

The scenarios apply a stated elasticity to each pair's last observed shelf and hold a unit acquisition-cost proxy fixed. That proxy is average acquisition cost from the recorded margin, not marginal cost and not operating profit. The baseline weeks are not one calendar week. A price outside the pair's own history is an extrapolation; a 10 percent increase is outside history for about 68 percent of pairs. Substitution across cereals and store traffic are not in the arithmetic. Nothing in the scenario file was implemented in stores.

## What would an actual randomized pricing experiment look like?

Write the stores, the UPCs, and the weeks before looking at sales. Change price, not the promotion calendar. Keep the tested prices inside the range each product already posted in that store. Measure substitution and store traffic, and record replacement cost rather than the historical margin. A 1 or 2 percent move is the relevant starting test. The original Hoch, Drèze, and Purk design is the closest published experiment, and this project cannot use it until the assignment and the cereal weeks are in hand.

## What did you personally implement?

The panel builder, the within-transformed OLS and the cluster-robust variance, the Poisson pseudo-maximum-likelihood checks, the instrument audit, the accounting scenarios, the tests against known synthetic slopes, the paper, the memo, and the Streamlit dashboard. The dashboard reads the saved files. It does not refit a coefficient. `statsmodels` and `linearmodels` are declared and are not used for the Kilts estimates.

## What failed?

Causal identification failed, and that is the result rather than a temporary gap. No candidate instrument met the exclusion rule. The confirmatory association is not stable across the first and second half of the calendar (−1.87 versus −2.43) or across blank and coded promotion weeks. Under the steep association, revenue and accounting gross profit move in opposite directions, so there is no scenario I would hand a manager as a price to deploy.

## What would you improve?

The next data object is the Hoch, Drèze, and Purk store-by-category assignment, checked against the prices actually charged, before any outcome regression. A replacement-cost series that is not computed from the shelf price would still need its own exclusion argument. A substitution system would be required before any markup or Bertrand calculation. Oatmeal was pre-specified as a robustness category and has not been estimated.

## What result changed your initial assumptions?

I expected a within-product slope to be more credible than pooled OLS, and it is a better description of within-product comovement. It did not become a causal elasticity. I also expected a price increase to be judged by whether revenue rose. On the historically supportable menu, treating −2.128 as a hypothetical elasticity makes a 10 percent price increase lower revenue by about 10 percent and raise accounting gross profit by about 16 percent. The commercially attractive case, in which both rise, uses the pooled association that the design had already set aside.

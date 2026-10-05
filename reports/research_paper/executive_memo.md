# Pricing memo: Dominick’s ready-to-eat cereals

To: pricing and strategy  
From: Kritana Bastola  
Date: 5 October 2026  
Subject: Do not deploy a cereal price change from these estimates

## Decision question

If Dominick’s had changed a cereal’s unit price, holding the promotion calendar fixed, what would have happened to item sales, revenue, and accounting gross profit? The evidence does not answer that question with a causal number. It does answer a narrower one: how movement and price covary in the historical file, and how the accounting arithmetic looks under stated assumptions.

## Evidence considered

The data are Kilts Center scanner records for ready-to-eat cereals at Dominick’s, 14 September 1989 through 7 May 1997. The estimation sample is 4,707,776 UPC-store-weeks with a positive scanned sale. Zeros and missing weeks were not filled in. The confirmatory summary is a log-log regression with a separate intercept for each product-store pair, a week effect, and an incomplete promotion flag. Standard errors are clustered by store.

A separate audit looked for a convincing source of price variation that does not itself shift demand. The published Hoch, Drèze, and Purk everyday-price experiment included cereal, but the public files do not contain the store assignments or the weeks. Acquisition cost constructed from the recorded margin is a function of the shelf price. Lagged prices, prices in other stores, zone tiers, and promotion flags fail the same test. No instrumental-variables model was estimated.

Accounting scenarios then take each pair’s last observed shelf and apply a stated elasticity only when the new price sits inside that pair’s own historical price range. A 10 percent increase fails that test for 68 percent of pairs. Revenue and accounting gross profit are reported separately. Accounting gross profit uses average acquisition cost. It is not store operating profit, and it is not marginal cost. Competitor prices and substitution across cereals are not in the calculation.

## Main empirical findings

Inside the confirmatory specification, the price coefficient is −2.128 (store-clustered standard error 0.026). A 10 percent higher unit price is associated with about an 18.4 percent lower item movement. The 95 percent interval is about [−2.18, −2.08]. A simple regression that ignores product and week differences gives −0.346 on the same rows. Those are two different associations. The gap is not a measured bias correction.

The steep association is not a single stable number. It is about −1.87 in the first half of the calendar and about −2.43 in the second. Weeks with no coded promotion and weeks with a coded promotion also disagree (−1.38 versus −2.70). A blank promotion field is not a verified regular price.

If the −2.128 association is treated only as a hypothetical elasticity, a 10 percent price cut on the pairs that historically could absorb it raises revenue by about 13 percent and lowers accounting gross profit by about 27 percent. A 10 percent price increase does the reverse: revenue down about 10 percent, accounting gross profit up about 16 percent. The two objectives conflict. They conflict in the same direction if the elasticity is −1 or −3, and on shelves from late 1996. They do not conflict in that way if someone uses the flat −0.346 association: price increases then raise both revenue and accounting gross profit. That flat number mixes expensive and high-volume products. It is not a within-product effect, and it is not established as causal.

Sampling error around −2.128 is small next to that specification gap. It does not flip the sign of the revenue calculation. Changing which association is treated as the elasticity does.

## Recommended next action

Do not change cereal prices from this study. Do not treat −2.128 as a markup input.

If a price test is still worth running, write the stores, the UPCs, and the weeks down before anyone looks at the sales response. Hold the promotion calendar fixed, so the test is not a deal under another name. Keep the tested prices inside the range each product already posted in that store. Measure whether other cereals pick up the lost movement, and whether store traffic changes. Record replacement cost rather than the historical acquisition-cost margin. Start with a 1 or 2 percent move. A uniform 10 percent increase is already outside the last observed price for most pairs.

## Risks and uncertainty

The estimates describe one defunct Chicago chain from 1989 to 1997. They are not current demand. The promotion code misses some merchandising, and a blank code is not proof of a regular price. The steep association changes across the sample window, so a single elasticity is a strong extra assumption. Scenario dollars stack each pair’s own last week. They are not one week of chain revenue. A price cut that looks good for one UPC can be paid for by a neighboring UPC. That substitution was not estimated. Nothing in the scenario file was implemented in stores.

## Additional data or experiment required

The missing piece for a causal cereal elasticity is the original Hoch, Drèze, and Purk store-by-category assignment and the cereal weeks, checked against the prices actually charged, before any outcome regression. A wholesale cost that is not computed from the shelf price would still need its own argument that it does not shift demand, and a national weekly index would be absorbed by the week effects already in the model. Until one of those designs is in hand, the honest product of this file is the conditional association and the conflict between revenue and accounting gross profit under stated assumptions.

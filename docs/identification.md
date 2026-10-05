# Identification audit

Phase 5 status: **Branch B. No causal price elasticity is adopted.** The audit is `reports/research_paper/identification_audit.md`. Two-stage least squares was not estimated on the scanner rows. The retained result is the confirmatory association.

The parameter we would like, and do not yet claim, is the effect of an exogenous change in a UPC's unit price on that UPC's item movement in a Dominick's store-week, holding the chain's other contemporaneous demand shifters fixed. The confirmatory regression in `configs/specifications.yaml` is a conditional association. It is the object that later counterfactuals may use only with that label.

## Why price is endogenous here

Dominick's chose shelf prices, promotions, and zone tiers. A week with high expected demand can be a week with a deal. Zone regular prices were a chain policy lined up with location and local competition. The manual says promoted prices were supposed to be the same chainwide, and regular prices were supposed to be uniform inside a zone. Observed movement is scanned sales, not a structural quantity demanded at a posted price when the item is unavailable.

Fixed effects change which price variation remains. They do not, by themselves, make the remaining variation exogenous.

- Pooled OLS uses cross-store tier differences, cross-UPC assortment differences, and within-series price changes together.
- UPC fixed effects remove permanent product differences, including package size when size does not change within the UPC.
- Store fixed effects remove permanent store differences, including the 1990 demographic profile and the store's usual tier.
- UPC-by-store fixed effects use only price changes inside a UPC-store pair.
- Additive week fixed effects remove shocks common to all cereals in that week. They do **not** remove a chainwide promotion of one UPC, because that promotion is not common to every UPC.
- UPC-by-week fixed effects would remove chainwide UPC promotions. The manual says those promotions are how the chain set promoted prices. That specification is not confirmatory, because it would discard the chain's main within-UPC price changes and leave a thin, selected remainder.
- Store-by-week fixed effects would remove a common log-price shift across cereals in a store-week. That is the shape of the category-level everyday-price experiment discussed below. Those fixed effects are excluded from the confirmatory specification so that an experiment, if it is later established, is not differenced out by accident.

Store-clustered standard errors allow residuals to be correlated within a store over time. Clustering is an inference choice. It is not evidence that price is exogenous.

## Candidates that were considered and not adopted

### 1. The Hoch, Drèze, and Purk everyday-price experiments

Hoch, Drèze, and Purk (1994, *Journal of Marketing* 58(4): 16–27) report two field experiments at Dominick's.

Study 1 used 19 categories and all 86 stores in the chain. Stores were randomly assigned to everyday low price (EDLP), high-low (Hi-Lo), or control **on a category-by-category basis**. Control stores kept existing everyday nonpromotional prices. EDLP stores decreased category prices by a constant factor, and Hi-Lo stores increased them by the same factor, so relative brand prices inside the category stayed in place. The tests ran a minimum of 16 weeks. Promotions continued in the ordinary way, and promotional prices were the same dollar price point across the three conditions. The authors say retail competitors did not match the everyday price changes during the test. Their Table 1 lists Cereal-RTE with a 10 percent category price change. Reported category outcomes in that table are theirs, not results of this project, and they are category aggregates rather than UPC-store elasticities.

Study 2, about eight months later, assigned each store one everyday-price condition across 26 categories. Rollout was staggered. The analysis window they describe is 16 weeks after prices had changed in all of those categories. A third manipulation increased the frequency of shallow bonus-buy deals.

What is **not** established for this project:

- The public movement, UPC, demographics, customer-count, store, and week files reviewed in Phase 1 do not contain a store-category treatment arm or an experiment week window.
- The journal article, in the text reviewed here, does not give the cereals start week. A secondary teaching note mentions 2 July 1992. That date is not treated as a project fact.
- Abrams, Gui, and Hortaçsu (2018) try to recover Study 1 labels from prices, using background documentation they obtained from Montgomery and Rossi. They report that documented labels and observed prices disagree for some store-categories, and that their mixture labels sometimes track prices more closely than the surviving documentation. Cereals is one of the categories they consider. Their labels are an estimate under a mixture model, not the randomization file.

Until a store-by-week assignment for ready-to-eat cereals is in hand and checked against prices, this project will not call a week "experimental," will not use a mined experiment indicator as an instrument, and will not describe the fixed-effects coefficient as the Hoch–Drèze–Purk treatment effect. A credible later phase can still audit that design. The audit has to state the endogenous variable, the assignment mechanism, the weeks, the exclusion restriction, and the interference created by chainwide promotions and a shared media market. Failure to find a clean assignment will be reported as failure to establish identification.

The published experiment is still useful as design context. It says everyday category price changes of about 10 percent moved category unit volume only a little in their analysis, while promotional prices were held to a common deal price. That is a reason to separate promotion-coded weeks from other price changes, not a number to import.

### 2. Margin-derived average acquisition cost

`PROFIT` implies an accounting cost share of sales. The manual says this cost is average acquisition cost and explains why it is not replacement cost. Because retail price and the margin are recorded on the same row, a cost constructed as price times one minus the margin share is a function of price. Wholesale deals were also timed with retail promotions through forward buying. Relevance of a mechanical function of price is not exogeneity. This candidate is not a default instrument. A first-stage F statistic, were one later computed, would not overturn that.

### 3. Lagged price

A lag is predetermined only if the relevant demand shock is not itself persistent. Promotions and zone policy are persistent. A lagged price is not adopted as an instrument.

### 4. Prices in other stores or other zones

A Hausman-style instrument needs a common cost shock and demand shocks that are independent across markets. Dominick's is one chain in one metropolitan area. The manual says promoted prices were chainwide. Weather, holidays, sports, and local media hit many stores in the same week. Other-zone regular prices also differ because tiers differ, and tiers are related to who lives near the store and to Cub Foods competition. This candidate is not adopted.

### 5. Price tier

High, medium, low, and Cub-Fighter are the manual's collapse of 16 zones. They are a pricing policy. Interactions of the price coefficient with tier are exploratory descriptions of heterogeneity. The tier dummy is not an instrument for price.

### Overidentification

No exactly identified or overidentified IV specification is confirmatory. An overidentification test will not be reported for a one-instrument model. A failure to reject an overidentification test, if a later overidentified model is estimated as a sensitivity, will not be described as proof that the instruments are valid.

## Feasibility ratings

Ratings use the files that were actually opened. "Joinable" means the field is on the movement row or can be merged on store, UPC, or week from a file that is in the Kilts catalog. None of these candidates is adopted as an instrument.

| Candidate | Provenance | How it varies | Joinable now | Mechanism and exclusion | Rating |
| --- | --- | --- | --- | --- | --- |
| Hoch, Drèze, and Purk Study 1 arm | Journal article. Cereal-RTE is in their Table 1 at a 10 percent everyday price change. Assignment and weeks are not in the movement, UPC, store, week, demographics, or customer-count files. | Store by category, for a limited run of weeks, if the design was implemented | No | Random assignment within elasticity strata would be the mechanism. Chainwide deal prices and a shared media market are the threats. A reconstructed mixture label is not the assignment. | Not feasible for this design. Separate experimental paper only if a primary assignment file is obtained before estimation. |
| `PROFIT`-implied average acquisition cost | Movement file. Cost share `1 - PROFIT/100`, then scaled by price. | In cereals, `PROFIT` changes while truncated `PRICE` stays fixed in 5.3 percent of log-sample UPC-store pairs. In the other pairs, margin movement is tied to the price movement. | Yes, same row | The constructed cost is a function of retail price. The manual says the underlying concept is average acquisition cost, moved by forward buying. A first-stage F statistic would not fix that. Store and week fixed effects do not remove a mechanical function of price. | Rejected. |
| Lagged unit price | Built from the same movement series | Within UPC-store, one week earlier | Yes | Predetermined on the calendar. Not exogenous if promotions and demand shocks persist. Collinear with the fixed-effects price variation the regression already uses. | Rejected. |
| Another store's price | Other rows of the same movement file. All three categories contain the same 93 store IDs. | Across stores, often little if the manual's chainwide promotion rule holds | Yes | Common wholesale shocks could move every store. Common Chicago demand shocks, and chainwide deal prices, violate exclusion. After week effects, a chainwide price has no cross-store contrast left. | Rejected for the main specification. |
| Price tier | Manual Part 6, a 1992 snapshot. Not yet a clean store table in this repository. | Across stores, not over weeks in the manual's account | Not yet built | A chain policy correlated with location and Cub Foods competition. Store fixed effects absorb a time-invariant tier. | Rejected as an instrument. Exploratory heterogeneity only, after the store file is built. |
| `SALE` in {B, C, S} | Movement file. Cereals also has 11,075 `G` codes and one `L`, which are unclassified. | 7.3 percent of cereals log-sample rows and 20.8 percent of that sample's movement | Yes | Merchandising chosen by the chain. The manual does not describe it as randomized. It is a confounder and an incomplete control. | Not an instrument. |
| Customer counts | Separate daily file. Zip size was 42,337,187 bytes. Not opened in this pass. | Store-day traffic | Joinable to store-week after aggregation | Traffic responds to deals. It is an outcome of price as well as a shifter of movement. | Rejected as an instrument. |
| 1990 demographics | Store cross-section. Stata zip was 168,854 bytes. Not opened. | Across stores, once | Joinable on store | Absorbed by store fixed effects. Not a price shifter over time. | Not an instrument. |

**Main specification after the Phase 5 audit:** the confirmatory fixed-effects association. No causal instrumental-variables claim. Every candidate in the audit, including a national cost index and an exposure-weighted index, is rejected. Correlations with price were computed after the verdicts were fixed and did not change them. Oatmeal has not been estimated.

## What the confirmatory coefficient can support

The fitted confirmatory association can support a statement of this form: inside ready-to-eat cereals at Dominick's, item movement and unit price covary by about −2.13 after UPC-by-store and week fixed effects and an incomplete promotion flag, with store-clustered uncertainty. The week split and the blank-versus-coded split show that this magnitude is not a single stable number. The association cannot support a statement that an arbitrary price change would move quantity by that coefficient, or that a simulated gross-profit change would have been realized.

Counterfactual rules are in `configs/specifications.yaml`. The scenarios that follow those rules are hypothetical accounting arithmetic in `reports/research_paper/pricing_scenarios.md`. Prices in the decision table lie inside the historical within-UPC-store range of unit prices. Accounting revenue and accounting gross profit are separate objectives. The margin input is a scenario, including a 10-point less favorable margin, not a measured marginal cost. Competitor response is not modeled because competitor prices are not in the files. The scenarios are not business results.

# Exploratory memo: Dominick's cereals

This memo describes the Phase 2 cereals panel. It does not estimate the confirmatory regression, and it does not read a correlation as a causal elasticity. The machine-readable counts are `reports/results/exploratory_summary.json`. Figure denominators are `reports/figures/figure_metadata.json`. The command was `python -m pricing_research.reporting.explore`.

The research question and the confirmatory equation are unchanged.

## Samples

Two samples are used, and they are not interchangeable.

The audited panel has every movement row: 6,602,582 rows, 93 stores, 490 UPCs, and 367 week numbers. Recorded zeros stay in this file. Mean movement is 14.08 items per row. Movement is zero on 28.03 percent of rows, and price is zero on 28.04 percent.

The log sample is the pre-specified subset: `OK = 1`, positive price, positive bundle quantity, and positive movement. It has 4,707,776 rows, 93 stores, 489 UPCs, 366 weeks, and 36,443 UPC-store pairs. Mean movement in this sample is 19.28 items. Log price and log movement are defined on every one of these rows. Gross sales in the log sample total $262,008,582, from `PRICE × MOVE / QTY`.

## What the panel looks like

The panel is not balanced. Among the 36,443 pairs, the median pair has 78 log-sample weeks, the 10th percentile has 7, and the 90th has 349. Five hundred sixty-five pairs appear in only one week, so a within-pair price range is undefined for them.

Product histories are incomplete in a different way. Conditional on the weeks a UPC is observed, coverage is high: the median UPC is present in 99.3 percent of the category weeks inside its own first-to-last span, after the 32 category-wide missing weeks are removed from that denominator. Of the 489 log-sample UPCs, 254 span at least 100 week indexes, and their median coverage is 99.4 percent. Only 128 UPCs are observed both in weeks 1–52 and in weeks 348–399. Thirty-six descriptions begin with `~`. Those discontinued labels account for 3.7 percent of log-sample item movement. Entry and exit, not week-to-week holes inside a product's life, are the main product-availability fact.

One audited UPC never enters the log sample: UPC 3000043316, Quaker club pack, 116 rows, all with zero movement. The file's 490th UPC is a recorded zero, not a dropped positive-sale history.

## Missing rows, recorded zeros, and week 219

Thirty-two week numbers inside 1–399 are absent from the file: 262–265, 284–309, and 370–371. Figure 09 shows those weeks as zero rows. They were not filled.

Week 219 is a different object. It is in the file, dated 18–24 November 1993, with 16,971 rows, and every one of those rows has price 0 and movement 0. None of them enter the log sample. That is why the audited file has 367 weeks and the log sample has 366. Treating week 219 as a missing week would be wrong. Treating its zeros as a normal demand observation would pull a level regression toward zero and would make log movement undefined.

A further 677 audited rows have positive movement and a nonpositive price. They stay in the audited file and out of the log sample. Another 43,426 rows have positive movement and a positive price but are still outside the log sample; given the Phase 2 waterfall, those are `OK = 0` rows. Putting either group back into a log-price regression would change the sample the design froze. This memo does not do that.

## Price variation, and whether fixed effects have anything to use

Most of the variation in log unit price is the identity of the product. After UPC means are removed, 16.8 percent of the sum of squares remains. After UPC-store means are removed, 15.8 percent remains. Store means alone remove almost none of it: 99.3 percent of the sum of squares is within stores, because a store's assortment spans cheap and expensive cereals.

The Phase 1 rule still applies: a later fixed-effects coefficient is not read as a within-pair association if fewer than 20 percent of log-sample pairs have any truncated price change. That bar is cleared. Of all 36,443 pairs, 31,167 (85.5 percent) have a unit-price range above $0.001. Of the 35,878 pairs with at least two weeks, 86.9 percent do. The median log-price range among those multi-week pairs is 0.410, a peak-to-trough factor of 1.51. That is the range over the pair's observed life, not a typical weekly change. Among the 4,671,333 log-sample rows that have a previous observed week for the same UPC and store, 16.4 percent show a unit-price change above $0.001. Prices are often unchanged from the previous observed week, and they still move over the life of most pairs.

Week fixed effects do not exhaust the price variation. Within a week, 92.6 percent of the log-price sum of squares remains.

## Aggregate correlations are not within-pair associations

On the log sample, the Pearson correlation of log unit price and log item movement is −0.111. That is the pooled, cross-sectional cloud in the left panel of figure 03. The hex density is a draw of 200,000 rows with seed 20261005. The connected means use all 4,707,776 rows.

Inside UPC-store pairs the correlation is −0.441. The right panel of figure 03 is the mean of demeaned log movement in quantile bins of demeaned log price. The bin means fall as the within-pair price rises. This is a description of comovement after pair means are removed. It is not the confirmatory coefficient: week effects and the promotion indicator are still in the variation, and no standard error is reported.

Removing only week means, and not pair means, leaves a correlation of −0.087. In a given week, higher-priced cereal rows are only weakly associated with lower movement, because different products are being compared. Alternating removal of UPC-store means and week means, eight rounds, leaves a correlation of −0.421. Week means do not account for the within-pair association. None of these numbers is β.

Across the 489 UPCs, the correlation between the log of total item movement and the UPC's mean log unit price is +0.163. Higher-volume products do not, in this cross section, carry lower average prices. Package size and brand are still inside that comparison. It answers a different question from the within-pair plot.

## Promotions

`SALE` blank is 4,350,772 log-sample rows (92.4 percent). Bonus buy (`B`) is 251,546 rows (5.3 percent). Simple price reduction (`S`) is 91,077 rows (1.9 percent). Coupon (`C`) is 3,322 rows (0.07 percent). Unclassified `G` and `L` codes are 11,059 log-sample rows. They are not in figure 06.

Pooled mean log movement is higher on coded weeks than on blank weeks, and mean unit prices are lower on `B` ($2.57) and `S` ($2.44) than on blank weeks ($3.16). Coupon rows are too few to carry a category conclusion; their pooled mean log movement is high, and their mean price ($3.06) is close to the blank-week mean.

The within-pair contrast is the one that matches the fixed-effects design. After UPC-store means are removed, blank weeks sit 0.059 log points below the pair's mean movement, and 0.013 log points above its mean log price. `S` weeks sit 1.259 log points above the pair's mean movement and 0.282 log points below its mean log price. The `S`-minus-blank gaps are about 1.32 log points of movement and −0.30 log points of price. `B` weeks are milder: +0.47 log points of movement and −0.11 log points of price. These are associations. The chain chooses the promotion and the price together.

Unclassified codes are not promotions under the manual's B/C/S list, and the confirmatory indicator still excludes them. In this sample they look like deep promotions: within-pair log movement is +1.63 and within-pair log price is −0.39. Because the confirmatory dummy is 1{`SALE` in {B, C, S}}, those 11,059 weeks sit in the reference group with the blanks. That is a consequence for the later coefficient, not a reason found here to recode `G` or `L`.

Coded weeks are also where a large share of movement sits relative to their row share. `B` and `S` together are 7.3 percent of log-sample rows and 20.3 percent of log-sample item movement (9,643,666 + 8,743,302 items, out of 90,766,941).

## Stores and chainwide price changes

A store's price position is the mean of log unit price minus the UPC mean, on the log sample. It holds the product fixed in a simple way. It is not a cost index. High-tier stores (25 stores, 1,357,188 rows) have a median position of +0.027 log points. Cub-Fighter stores (9 stores, 517,634 rows) have a median of −0.036. The gap between those two medians is about 6.5 percent in the price level. The store ranges overlap: the lowest high-tier store is below the highest Cub-Fighter store. Medium (42 stores) and low (9 stores) sit near zero and slightly below. Store 139, Bloomingdale, is in the codebook with a blank tier and a blank zone; its position is +0.041 on 33,987 log-sample rows, and one store is not a tier. Seven movement stores are absent from the codebook (135, 140, 141, 142, 143, 144, 146), covering 42,846 log-sample rows. Their tier is missing, not imputed.

Prices are usually not the same across stores in a given UPC-week. Among 65,152 UPC-weeks with at least 10 log-sample stores, 7.8 percent have a cross-store unit-price range of at most $0.001. The median range is $0.31, and the 90th percentile is $0.72. That fits zone pricing better than a single chainwide shelf price.

Changes are a mixture. The previous week means the preceding observed log-sample week for that pair, which can skip a hole. Among UPC-weeks with at least 10 stores that have such a previous observation and at least one price change (27,725 UPC-weeks), the median share of those stores changing together is 8.5 percent. In 28.3 percent of those UPC-weeks, at least 80 percent of the comparable stores change together. Most price changes are not chainwide. A substantial minority are. Week fixed effects do not absorb a UPC-specific promotion that hits many stores in the same week. That was already the reason the design refused UPC-by-week effects. This count is the empirical content of that choice. It is not evidence that the remaining within-store price changes are exogenous.

## Seasonality

Figure 08 is the mean of recorded movement, zeros included, by the month of the week-start date. Each observed row has equal weight. January averages 14.84 items and June averages 14.11, a ratio of 1.05. November is the low month on this measure, at 12.90 items. There is no large holiday spike in movement per observed row.

The total-item ratio of January to June is 1.43 (9,178,217 versus 6,415,188). That matches the Phase 1 screen and is mostly a difference in how many rows those months contain (618,295 versus 454,571, a ratio of 1.36), including the 1995 gap that removes weeks from February through August. A total that ignores the denominator overstates seasonality. The log-sample means, which drop zero-movement rows, run from 20.06 items in January to 17.25 in December. Category demand per observed store-UPC-week moves modestly across the year.

## Concentration

Sales are not a one-product market, and they are not equal across UPCs. The movement Herfindahl index is 0.0070 and the revenue index is 0.0069, on the order of 140 equal-sized products. The ten largest UPCs by movement account for 15.5 percent of log-sample items; the ten largest by revenue account for 14.1 percent of gross sales. The top 48 UPCs, one tenth of 489 by integer division, account for 47.7 percent of items and 47.6 percent of gross sales.

The single largest UPC by total log-sample movement is Cheerios, UPC 1600066610, chosen by that rule before the chart was drawn. It has 2,011,819 items (2.2 percent of log-sample movement), 29,679 rows, and all 93 stores, from week 1 through week 399, with 366 observed weeks. Figure 04 shows its weekly item total and its median unit price. The price series steps and then sits flat for long stretches, while movement spikes in particular weeks. Those spikes are not a demand curve.

## What this leaves unidentified

Price, promotion, and movement are chosen together inside the UPC-store pair. The within-pair correlation is more negative than the pooled correlation, which is the usual reason to prefer pair fixed effects to pooled OLS, and it is also the pattern one expects if the chain cuts price when it wants to sell more. Week fixed effects remove a common week shock and leave the within-pair association almost intact. They do not remove the UPC-specific promotions that hit many stores at once, and about 28 percent of multi-store price-change weeks have that shape. Store tiers shift the average price by only a few percent and are a chain policy, not a randomly assigned instrument.

Nothing in these plots identifies a causal price elasticity. The confirmatory specification remains the pre-specified association with UPC-by-store and week fixed effects and the incomplete B/C/S indicator. Average acquisition cost, lags, other-store prices, and tiers are still not instruments. The within-pair price variation is large enough that the 20 percent rule does not block a later within-pair reading. That is a statement about variation, not about exogeneity.

## Design revision

No revision. The category, the log-sample rules, the confirmatory equation, and the rejection of a causal IV are unchanged. The exploratory results above are the evidence that was asked for before any pricing model is estimated.

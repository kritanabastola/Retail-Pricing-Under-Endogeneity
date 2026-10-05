# Data dictionary

Sources read for this dictionary:

- Kilts Center Dominick's catalog page, consulted 5 October 2026.
- Dominick's Data Manual, created July 2013 and updated October 2018.
- The cereals movement and UPC files processed by `python -m pricing_research.data.build` on 5 October 2026. Hashes and row counts are in `reports/results/data_quality.json`.

Variable definitions below are unchanged by estimation. Fitted associations are in `reports/results/baseline_models.json`, not in this dictionary.

## What the archive is

The archive is store-level scanner data from Dominick's Finer Foods, a Chicago-area supermarket chain that no longer operates. The Kilts page describes a 1989–1994 research partnership and says randomized shelf and pricing experiments were run in more than 25 categories. The scanner files are a by-product of that cooperation and cover a longer window than the partnership sentence. Week 1 in the manual starts 14 September 1989. The decode table continues through week 400, ending 14 May 1997. A Princeton library catalog dates the series from 14 September 1987; that start year conflicts with the manual's week table and is not used.

The files record scanned sales. They do not record a complete shelf-availability census, and a missing UPC-store-week is not documented as a zero-sale week.

These are historical prices and quantities. They are not estimates of current demand.

## License and citation

The manual says the data are for academic research purposes only. Any working paper or publication that uses any portion of the data must acknowledge the James M. Kilts Center, University of Chicago Booth School of Business. Raw files are not committed here. A Zenodo deposit of derived profit series (DOI 10.5281/zenodo.4004172) is a different object and is not a source for this project.

## File map for the categories under consideration

| Role | Category | UPC file | Movement file | Manual window | Manual UPCs | Manual movement rows | File used |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Primary | Ready-to-eat cereals (`cer`) | `upccer.csv` | `wcer.zip` (`wcer.csv`) | Weeks 1–399 | 490 | 6,417,055 | Local, gitignored. The build reads the full CSV. |
| Robustness | Oatmeal (`oat`) | `upcoat.csv` | `woat.zip` | Weeks 91–399 | 96 | 1,301,870 | Local, gitignored. Same pipeline, not the confirmatory sample. |
| Deferred | Canned soup (`cso`) | `upccso.csv` | `wcso.zip` | Weeks 1–399 | 445 | 7,011,243 | Profiled in Phase 1 and not ingested by the Phase 2 build. |

Manual file sizes are the manual's own SAS-file figures (cereals 300 MB, oatmeal 61 MB, canned soup 338 MB). They are not the CSV zip sizes above. The manual's row counts are file inventories, not the regression sample.

The manual says the cereals category is ready-to-eat breakfast cereal and that hot cereals are in the oatmeal category. All 490 rows in the cereals UPC CSV have commodity code 311. Thirty-six descriptions begin with `~`, which the manual defines as discontinued. Six begin with `$`, which the manual says does not mean anything. No description in that file began with `#` or `<`.

## UPC attribute file

One row per UPC. Columns read from `upccer.csv` and `upcoat.csv`:

| Column | Manual meaning | Project use |
| --- | --- | --- |
| `COM_CODE` | Dominick's commodity code. A file may contain more than one code. A code does not appear in more than one UPC file. | Cereals attribute file is entirely code 311. Not a regressor in the confirmatory specification. |
| `UPC` | Item code. The manual says the last five digits identify the product and the remaining digits identify the manufacturer. | Merge key to movement. |
| `DESCRIP` | Product name, up to the manual's character layout. Leading `~` marks a discontinued item. Leading `<` is an unreliable trial-size flag. Leading `#` means on sale in Combo stores only. `$` and `*` mean nothing. | Descriptive label. The `#` flag is a product attribute, not the weekly `SALE` field. |
| `SIZE` | Package size as text (`10 OZ`, `23.45O`, `ASST`, `1 CT`). | Not the bundle quantity. Parsing it into ounces is exploratory because the strings are irregular. |
| `CASE` | Items per manufacturer case. Consumers do not see this. | Not a price or quantity. |
| `NITEM` | Dominick's attempt to link a reformulated UPC to an older one. The manual says the scheme is not foolproof, and that the last digit often marks drop-ship (0) versus warehoused (1). Products sharing the other digits are the same product. | Do not collapse UPCs on `NITEM` in the confirmatory sample. |

## There is no `DEAL` column

The promotion field on the movement file is `SALE`. Manual Part 4 defines `B` (bonus buy), `C` (coupon), and `S` (simple price reduction). A blank is not proof of a regular-price week. The cereals, oatmeal, and soup CSVs also contain `G`, and cereals contains one `L`. Those codes are unclassified. They are not promotions and not blanks.

## Counts from the cereals build on 5 October 2026

The machine-readable report is `reports/results/data_quality.json`. The waterfall is `reports/tables/cleaning_summary.csv`.

| Stage | Rows |
| --- | --- |
| Movement data rows read | 6,602,582 |
| Audited panel | 6,602,582 |
| Rows deleted | 0 |
| First-reason exclusion: `OK` not 1 | 141,285 |
| First-reason exclusion: price not positive | 1,753,521 |
| First-reason exclusion: quantity, movement, week, or duplicate key | 0 |
| Log sample | 4,707,776 |

141,285 + 1,753,521 + 4,707,776 = 6,602,582.

The unconditional flags are larger where rules overlap. Nonpositive movement occurs on 1,850,703 rows, and every one of those rows also has a nonpositive price, so the waterfall counts them under price or under `OK` rather than under movement. Nonpositive price occurs on 1,851,380 rows. The 677-row difference is positive movement with a nonpositive price. Those 677 rows stay in the audited panel, are out of the log sample, and are not imputed. `OK` not equal to 1 occurs on 141,285 rows, of which 97,859 also have a nonpositive price.

Duplicate UPC-store-week keys: 0. UPC join failures: 0. Margin outside [−100, 100]: 0. Negative movement: 0. Weeks outside 1–400: 0. Hexadecimal price and margin disagreements above 0.0001: 0 on all 6,602,582 rows. Decimal revenue checks: 5,991 comparisons, 0 failures. The input file was already ordered by UPC, store, and week.

`SALE`: blank 6,242,568; coded B, C, or S 348,938; unclassified 11,076. Package size stayed unparsed for 23 of 490 UPC rows. Those movement rows are kept. Product and store coverage tables have 490 and 93 rows.

Weeks present inside 1–399: 367. Missing week numbers: 262–265, 284–309, and 370–371. They are not in the panel.

Log-sample UPC-store pairs: 36,443. Pairs whose truncated unit price is not constant: 31,167. That is a descriptive count, not an elasticity.

`data/raw/wcer.zip` is 42,402,094 bytes, SHA-256 `2d4a59f88e4b97257c566f7c62fcccfdf9d5971891a617316ab21ea61c8d24c2`. `data/raw/upccer.csv` is 25,932 bytes, SHA-256 `affa589f080ab18a2edb2fa8f4cfb52b9212dec353bb49778e57f2b2403c5c6c`. The store codebook is 4,454 bytes, SHA-256 `e210d79ca63c3b6951701a0c695dc2d1ed7bbd907d0e5861df229e8af3176ab4`.

## Counts from the Phase 1 three-category screen

The profile is `reports/tables/category_feasibility.json`. The cereals build reproduced the cereals row count of 6,602,582. Oatmeal has 1,333,465, not the manual's 1,301,870. Canned soup has 7,011,243, matching the manual. All three files use the same 93 store IDs, have no duplicate UPC-store-week keys, and have no negative prices. Zero prices are common and usually accompany zero movement. Every truncated `PRICE` and `PROFIT` in these three files matched its hexadecimal double within 0.0001. Cereals is missing 32 week numbers inside the manual window, including 16 February 1995 through 16 August 1995.

## Movement file

Weekly store-UPC sales. The oatmeal CSV header, which matches the manual's movement layout, is:

`STORE`, `UPC`, `WEEK`, `MOVE`, `QTY`, `PRICE`, `SALE`, `PROFIT`, `OK`, `PRICE_HEX`, `PROFIT_HEX`

The manual says files are sorted by UPC, store, and week. Three inspected oatmeal rows were store 2, UPC 1112600301, weeks 91–93, with `QTY` 1, `PRICE` 1.89, blank `SALE`, `OK` 1, and `PROFIT` 31.48, 31.48, and 30.26. Those rows only document the schema. They are not a sample.

| Column | Meaning and rule |
| --- | --- |
| `STORE` | Store number. Join to the manual's store list and, separately, to the demographics file. |
| `UPC` | Merge key to the UPC file. |
| `WEEK` | Index into the Part 8 decode table. See `pricing_research.data.calendar`. |
| `MOVE` | Number of units sold. In a bundle week the manual says this is the count of items, not the count of bundles. |
| `QTY` | Number of items bundled together. It is not package size and it is not movement. |
| `PRICE` | Retail price of the bundle. It is not always a per-item price. Truncated in the CSV. |
| `PRICE_HEX` | Full-precision SAS value of price, as a hexadecimal IEEE-754 double. |
| `SALE` | `B` bonus buy, `C` coupon, `S` simple price reduction. If the code is set, the manual says the week is a promotion. If it is blank, a promotion may still have occurred. |
| `PROFIT` | Gross margin in percent of sales. A value of 25.3 means 25.3 cents per dollar, and the manual's cost-of-goods example is 74.7 cents per dollar. Truncated in the CSV. |
| `PROFIT_HEX` | Full-precision SAS value of the margin field. |
| `OK` | `1` valid, `0` trash. The manual says flagged weeks are suspect and are not used in Kilts analysis. |

Jens Mehrhoff's CSV conversion, as described on the Kilts page, says the hexadecimal fields reproduce the SAS values and suggests using the truncated fields for ordinary work. This project decodes the hexadecimal values, compares them with the truncated fields, and reports the discrepancy count before choosing a representation. The choice will not be made by which one produces a larger or more significant price coefficient.

### Identities

Implemented in `pricing_research.economics.accounting` and covered by unit tests:

- Unit price = `PRICE / QTY`.
- Revenue = `PRICE * MOVE / QTY`.
- Accounting gross profit = revenue × `PROFIT / 100`.
- Average-acquisition-cost share of sales = `1 - PROFIT / 100`.

The manual says the wholesale cost behind `PROFIT` is the average acquisition cost of inventory, not replacement cost and not the last transaction price. It cites Sam Peltzman, "Prices Rise Faster Than They Fall," University of Chicago Working Paper No. 142, for two reasons the accounting cost and replacement cost diverge: sluggish sell-off of older inventory, and manufacturer advance notice that lets the chain empty inventory and forward-buy. The project therefore does not call `PROFIT` a marginal cost.

## Analysis panel

`python -m pricing_research.data.build` writes two Parquet files. `data/interim/cereals_movement_audited.parquet` has every cereals movement row. `data/processed/cereals_log_sample.parquet` keeps the rows whose `in_log_sample` flag is true. Nothing is deleted from the audited file. The cleaning summary is a first-reason waterfall, so a row with both `OK = 0` and `PRICE = 0` is counted once, under `ok_not_one`. The same row still increments both unconditional flags in `reports/results/data_quality.json`.

The log-sample rules, in order, are: duplicate UPC-store-week, `OK` not equal to 1, `PRICE` not positive, `QTY` not positive, `MOVE` not positive, and week outside 1–400. Unmatched UPC, unmatched store, unclassified `SALE`, and a margin outside [−100, 100] are flags. They are not extra log-sample drops. Negative margins inside that interval stay in the log sample when the other rules pass. They are loss-leader records, not trash.

A recorded `MOVE` of zero stays in the audited file with `unit_volume_items` equal to zero. A UPC-store-week that is absent from the CSV is not a row. Those two states are not coded as the same thing, and neither is filled in.

Returns and negative movement: the cereals file had no negative `MOVE` in the Phase 1 screen. If a negative value appears, `move_negative` is true, `unit_volume_items` and `gross_sales` are null, and the row is out of the log sample because movement is not positive. The recorded `MOVE` is kept.

`PRICE` of zero with positive `MOVE` stays in the audited file, is out of the log sample, and is not imputed.

Unparsed `SIZE` strings do not drop the row. Ounces are parsed from `N OZ`, `N O`, and a trailing `Z` (`19.25Z`, `17.4 Z`). Bare numbers, `CT`, `ASST`, `2/20 O`, and `end` stay unparsed. `CASE` and `NITEM` are not the product key.

Promotion: `promo_coded` is true only for `SALE` in {B, C, S}. Blank is `sale_class = blank`. `G` and `L` are `unclassified`. Unusual promotion weeks are labeled, not removed.

Incomplete product histories stay incomplete. The product summary reports weeks observed inside each UPC's own min and max. It does not add the missing cereal weeks (the Phase 1 screen found 262–265, 284–309, and 370–371).

### Observed fields

These are the recorded values, renamed to lowercase. Invalid text becomes null and is flagged. The original text is not overwritten in the source CSV.

| Field | Source |
| --- | --- |
| `store`, `upc`, `week` | Movement keys. |
| `move`, `qty`, `price`, `profit` | Movement numerics. |
| `sale`, `ok`, `price_hex`, `profit_hex` | Movement text. |
| `com_code`, `descrip`, `size`, `nitem` | Left join to the UPC file. Null if the UPC does not match. |
| `price_tier`, `zone`, `city` | Left join to the store codebook. Null if the store does not match. |

### Derived fields

| Field | Rule |
| --- | --- |
| `unit_price` | `price / qty` when both are positive. Otherwise null. |
| `unit_volume_items` | `move` when `move >= 0`, including zero. Null when `move` is negative or not numeric. |
| `gross_sales` | `price * move / qty` when `qty > 0`, `move >= 0`, and `price` is numeric. This is the manual's sales identity. A zero price and zero movement produce zero. |
| `margin_rate` | `profit / 100` when `profit` is inside [−100, 100]. Otherwise null. |
| `gross_profit_proxy` | `gross_sales * margin_rate` when both exist. This is an accounting product of the recorded margin. It is not economic profit and not a marginal-cost residual. |
| `size_oz`, `size_parse` | Parsed package size. `price_per_oz` is `unit_price / size_oz` when both are positive. |
| `sale_class`, `promo_coded` | Promotion classification above. |
| `week_start`, `week_end`, `year`, `month`, `quarter` | From `week_bounds`. Year, month, and quarter use the Thursday that opens the week. Invalid week numbers get a null date. |
| `log_move`, `log_unit_price` | Natural logs on the log sample only. Null elsewhere. |
| `in_log_sample`, `log_sample_exclusion` | The waterfall flag and the first reason, if any. |

The float `gross_sales` is checked against `pricing_research.economics.accounting.revenue`, which uses `Decimal`, on every 5,000th input row and on every row with `QTY` other than 1. A gap above `1e-6` fails the build after the quality file is written. Estimation uses the truncated `PRICE` and `PROFIT`. The hexadecimal doubles are compared, and the disagreement count is stored in the quality file. The comparison does not choose the representation that would change a coefficient, because no coefficient is estimated here.

For cereals, `QTY` other than 1 is uncommon. The same `PRICE / QTY` definition is still the unit price on those rows, because `PRICE` is the bundle total and `MOVE` counts items. Oatmeal uses the same identities when that category is built. Soup is not in this build.

### Store codebook

`src/pricing_research/data/resources/store_codebook.csv` has columns `store_id`, `city`, `price_tier`, `zone`, `zip_code`, `address`. It was copied from the Eurostat `dff` repository's headerless transcription of manual Part 6 (`https://raw.githubusercontent.com/eurostat/dff/master/CSV/stores.csv`) and given a header. Stores 2, 8, 12, 21, and 137 were checked against the manual: River Forest High zone 1 ZIP 60305; Oak Lawn Low zone 5; Chicago High zone 7; Hanover Park CubFighter zone 6; Evanston High zone 1. Store 69's city text is "Now known as Store 137". Store 102's ZIP is the transcribed `655` and was not corrected. The other rows were not re-keyed from the PDF. A blank tier stays blank.

## Store list, zones, and demographics

Part 6 of the manual lists stores with city, price tier, zone, ZIP code, and address. The manual states:

> When the Dominick's data was collected, DFF priced products by 16 zones. Within each zone, there was supposed to be a uniform regular price (promoted prices are the same, chainwide). However, these 16 zones amounted to four price tiers: Cub-Fighter, low, medium, and high. Some stores in the database do not have a zone assignment as these stores came on-line after 1992 when the zone information was obtained.

The four tiers are a chain policy, not a randomized store treatment. Cub-Fighter is a competitive designation, not a demographic bin. The join uses `src/pricing_research/data/resources/store_codebook.csv` (96 stores). Cereals movement uses 93 store IDs. Seven of those IDs are absent from the transcription, so their tier, zone, and city are null: 135, 140, 141, 142, 143, 144, and 146 (49,304 movement rows). Ten transcription IDs do not appear in the cereals movement file: 4, 19, 25, 39, 46, 55, 60, 65, 69, and 108. The catalog's "about 100 stores" and the 86 stores in Hoch, Drèze, and Purk (1994) remain different counts. Some stores have no zone because they opened after the 1992 zone snapshot; a blank zone in the transcription is left blank.

The demographics file is a 1990 census profile of each store's trading area, processed by Market Metrics. Variables include age, ethnicity, education, income, household size, housing, employment, and shopper-type shares. They do not vary by week. Store fixed effects absorb them. The public Stata zip was 168,854 bytes on 5 October 2026 and was not opened.

## Customer counts

The customer-count file is daily and store-specific. `CUSTCOUN` is the number of customers who visited and bought something. Department dollar sales and coupon redemptions are also recorded. The public Stata zip was 42,337,187 bytes and was not opened. Store traffic is affected by prices and promotions, so it is not an instrument for price. It is also a poor confirmatory control if traffic is itself a consequence of the price change.

## Week calendar

`week_bounds` maps a week index to dates using the manual's week-1 start, 14 September 1989, and consecutive seven-day blocks. Unit tests check dates read from the manual, including week 1, week 91 (the oatmeal file's first week), weeks 115–116, week 399, and week 400. The cereals manual window ends at week 399 even though the decode table includes week 400.

The manual's special-event column was not fully transcribed in Phase 1. Week fixed effects absorb a common holiday week without that column. A complete event list is needed only for descriptive plots.

## Fields that are not in the public files reviewed

The catalog and manual contents reviewed in Phase 1 do not include a store-by-category treatment-assignment file, an experiment calendar, competitor prices, wholesale invoices, or a replacement-cost series. Those absences are identification facts, not cleaning details. See `docs/identification.md`.

"""Instrument candidates for the cereals price audit.

Verdicts are fixed here, before any correlation is computed. A large
correlation with price cannot change a verdict. Nothing in this module is an
approval to estimate two-stage least squares on the Kilts sample.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentCandidate:
    """One proposed instrument and the verdict that keeps it out of 2SLS."""

    variable: str
    source: str
    construction: str
    rationale: str
    exclusion: str
    direct_demand_effects: str
    common_shocks: str
    required_controls: str
    verdict: str
    verdict_reason: str


def _candidate(**fields: str) -> InstrumentCandidate:
    return InstrumentCandidate(**fields)


CANDIDATES: tuple[InstrumentCandidate, ...] = (
    _candidate(
        variable="hoch_dreze_purk_study1_assignment",
        source="Hoch, Drèze, and Purk 1994. Not a movement-file column.",
        construction="Not built. No store-category arm or cereal week window is on file.",
        rationale="Study 1 assigned stores, by category, to EDLP, Hi-Lo, or control.",
        exclusion="Usable only if the arm and the weeks are known and checked against prices.",
        direct_demand_effects="Chainwide deals and a shared media market can move control stores.",
        common_shocks="Holidays, competitors, and chain advertising are citywide.",
        required_controls="Assignment and weeks, written down before any second stage.",
        verdict="REJECTED",
        verdict_reason="The assignment file is absent. A mined price pattern is not the trial.",
    ),
    _candidate(
        variable="log_average_acquisition_cost",
        source="Same movement row: PRICE, QTY, and PROFIT.",
        construction="log(unit price times (1 - PROFIT/100)) when that product is positive.",
        rationale="A wholesale cost could shift price if it were not built from that price.",
        exclusion="PROFIT is a sales margin, so this product puts the shelf price back in.",
        direct_demand_effects="Forward buying ties wholesale deals to retail promotions.",
        common_shocks="Manufacturer deals are often chainwide.",
        required_controls="A cost that is not computed from the shelf price.",
        verdict="REJECTED",
        verdict_reason=(
            "This series is a function of retail price. An F statistic does not fix that."
        ),
    ),
    _candidate(
        variable="lagged_log_unit_price",
        source="Same UPC-store series, previous calendar week only.",
        construction="Log unit price in week t-1 when that adjacent log-sample week exists.",
        rationale="A lag is predetermined on the calendar.",
        exclusion="Predetermined is not exogenous when promotions and demand shocks persist.",
        direct_demand_effects="A multi-week deal enters both the lag and current movement.",
        common_shocks="Chainwide promotions last more than one week.",
        required_controls="Pair and week effects do not create an exclusion restriction.",
        verdict="REJECTED",
        verdict_reason="Persistent promotions and demand shocks violate exclusion.",
    ),
    _candidate(
        variable="other_store_leave_one_out_log_unit_price",
        source="Other stores in the same UPC-week.",
        construction="Leave-one-out mean log unit price. At least two stores.",
        rationale="A Hausman instrument needs independent demand shocks across markets.",
        exclusion="One chain in one city. Promoted prices were supposed to be chainwide.",
        direct_demand_effects="Another store's price is often the same promotion.",
        common_shocks="Weather, holidays, and local media hit many stores in one week.",
        required_controls="Separate markets. These files do not have them.",
        verdict="REJECTED",
        verdict_reason="Other-store prices share chainwide promotions and citywide demand.",
    ),
    _candidate(
        variable="price_tier",
        source="Store codebook, a 1992 snapshot of manual Part 6.",
        construction="Store price tier joined on store id. Not a weekly price.",
        rationale="Tiers summarize the chain's zone pricing.",
        exclusion="Tiers are pricing policy, lined up with location and Cub Foods competition.",
        direct_demand_effects="Who lives near the store affects the tier and demand.",
        common_shocks="The tier does not vary over weeks.",
        required_controls="Pair effects absorb a time-invariant tier.",
        verdict="REJECTED",
        verdict_reason="A time-invariant pricing policy is not an instrument.",
    ),
    _candidate(
        variable="promo_coded",
        source="Movement column SALE.",
        construction="1{SALE in {B, C, S}}. G and L stay unclassified.",
        rationale="None as an instrument. The flag is a merchandising choice.",
        exclusion="The manual does not describe SALE as randomized.",
        direct_demand_effects="Features and coupons can raise movement at a given shelf price.",
        common_shocks="Many promotions are chainwide for one UPC.",
        required_controls="The confirmatory equation already uses the flag as a control.",
        verdict="REJECTED",
        verdict_reason="The promotion flag is an incomplete control, not an instrument.",
    ),
    _candidate(
        variable="customer_counts",
        source="Kilts daily customer-count file. Sized in Phase 1 and not opened.",
        construction="Not constructed.",
        rationale="Store traffic could shift movement.",
        exclusion="Traffic is an outcome of prices and promotions.",
        direct_demand_effects="Deals bring shoppers into the store.",
        common_shocks="Holidays and weather move traffic and demand together.",
        required_controls="Opening the file would not supply an exclusion restriction.",
        verdict="REJECTED",
        verdict_reason="Customer counts respond to price. They are not used.",
    ),
    _candidate(
        variable="demographics_1990",
        source="Kilts 1990 store demographics. Sized in Phase 1 and not opened.",
        construction="Not constructed.",
        rationale="Neighborhood composition differs across stores.",
        exclusion="One cross-section is absorbed by pair effects and does not shift weekly price.",
        direct_demand_effects="Income and household composition shift demand directly.",
        common_shocks="None over time. The file is one cross-section.",
        required_controls="Store or pair fixed effects remove it.",
        verdict="REJECTED",
        verdict_reason="Demographics do not vary over the panel.",
    ),
    _candidate(
        variable="national_cost_index",
        source="Not in the Kilts files used here.",
        construction="Not built. A pure weekly series is absorbed by week effects.",
        rationale="A national input cost could shift retail price.",
        exclusion="Wholesale does not imply exclusion. Week effects absorb a common weekly series.",
        direct_demand_effects="Inflation and commodity news can move demand and costs together.",
        common_shocks="A national weekly index is a common shock.",
        required_controls="An exposure measure, if the index is to survive week effects.",
        verdict="REJECTED",
        verdict_reason="No cost index was joined. Week effects would absorb a pure time series.",
    ),
    _candidate(
        variable="exposure_weighted_cost_index",
        source="Not in the Kilts files used here.",
        construction="Not built. No product exposure share is in the confirmatory design.",
        rationale="An input share can leave within-week contrast.",
        exclusion="Exposure must be excluded from demand. Package mix is a product attribute.",
        direct_demand_effects="Ingredient mix and package size enter demand directly.",
        common_shocks="The national factor is still common.",
        required_controls=(
            "No time-varying exposure is on file. Pair effects absorb a fixed share."
        ),
        verdict="REJECTED",
        verdict_reason="No defensible exposure measure is in the files.",
    ),
)


def approved_candidates() -> tuple[InstrumentCandidate, ...]:
    """Candidates with verdict APPROVED. Empty unless the audit changes."""
    return tuple(item for item in CANDIDATES if item.verdict == "APPROVED")

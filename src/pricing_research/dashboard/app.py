"""Cereals research dashboard. Run with ``streamlit run`` on this file.

Every coefficient is read from ``reports/``. The app does not fit a model.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# Community Cloud runs this file without installing the src package.
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from pricing_research.dashboard.artifacts import (  # noqa: E402
    ArtifactError,
    confirmatory_price,
    consistency_checks,
    filter_panel,
    instrument_table,
    load_audit,
    load_exploratory,
    load_quality,
    load_scenarios,
    one_shelf_scenario,
    price_rows,
    product_table,
    project_root,
    read_panel,
    regression_table,
    robustness_table,
    sampling_revenue_band,
    shelf_snapshot,
    specification_band,
    store_table,
    weekly_summary,
)

ROOT = project_root()
PAGES = (
    "Executive overview",
    "Market data",
    "Econometric results",
    "Identification and robustness",
    "Pricing scenarios",
    "Documentation",
)


def main() -> None:
    st.set_page_config(
        page_title="Cereals pricing research",
        page_icon=None,
        layout="wide",
    )
    st.sidebar.title("Cereals pricing research")
    st.sidebar.caption(
        "Dominick’s ready-to-eat cereals, 14 September 1989 to 7 May 1997. "
        "Conditional associations. Not causal elasticities."
    )
    page = st.sidebar.radio("Section", PAGES, label_visibility="collapsed")
    try:
        _route(page)
    except ArtifactError as exc:
        st.error(str(exc))


def _route(page: str) -> None:
    if page == "Executive overview":
        page_overview()
    elif page == "Market data":
        page_market()
    elif page == "Econometric results":
        page_results()
    elif page == "Identification and robustness":
        page_identification()
    elif page == "Pricing scenarios":
        page_scenarios()
    else:
        page_docs()


def page_overview() -> None:
    quality = load_quality(ROOT)
    audit = load_audit(ROOT)
    scenarios = load_scenarios(ROOT)
    exploratory = load_exploratory(ROOT)
    price = confirmatory_price(regression_table(ROOT))
    rows = int(quality["row_reconciliation"]["log_sample_rows"])
    upcs = int(exploratory["log_sample"]["upcs"])
    st.title("Executive overview")
    st.markdown(
        "How does ready-to-eat cereal movement at Dominick’s covary with unit "
        "price, and which pricing statements survive once price endogeneity is "
        "taken seriously?"
    )
    _disclaimer()
    left, right = st.columns(2)
    with left:
        st.subheader("Dataset")
        st.markdown(
            f"Log sample: **{rows:,}** UPC-store-weeks, "
            f"**{int(price['store_clusters'])}** stores, "
            f"**{upcs:,}** UPCs, **{int(price['week_clusters'])}** weeks. "
            "The audited movement file keeps every row, including zeros. "
            "Missing weeks are not filled."
        )
        st.markdown(
            "Source: James M. Kilts Center for Marketing, University of Chicago "
            "Booth School of Business. Academic use. Historical chain. Not a "
            "description of current shoppers."
        )
    with right:
        st.subheader("Primary association")
        st.markdown(
            f"Confirmatory model M5: log items on log unit price, with UPC-by-store "
            f"effects, week effects, and an incomplete promotion flag. "
            f"Coefficient **{float(price['estimate']):.3f}** "
            f"(store-clustered SE {float(price['se_cluster_store']):.3f}). "
            f"A 10 percent higher unit price is associated with "
            f"**{100 * float(price['associated_movement_change_for_10_percent_price']):.1f} "
            "percent** lower item movement inside that specification."
        )
        st.markdown(
            "That number is a conditional association. Identification branch "
            f"**{audit['branch']}**: no causal elasticity was established, and "
            "two-stage least squares was not estimated."
        )
    st.subheader("Credibility")
    st.markdown(
        "- The confirmatory equation was written before the coefficient was seen.\n"
        "- Pooled OLS on the same rows is much flatter. The gap is a difference "
        "between two associations, not a measured bias sign.\n"
        "- Every proposed instrument was rejected, including margin-derived cost, "
        "lags, other-store prices, and the Hoch–Drèze–Purk assignment, which is "
        "not in the public files.\n"
        "- The slope is about −1.87 in the first half of the calendar and about "
        "−2.43 in the second. Blank and coded promotion weeks also disagree."
    )
    st.subheader("Decision implication")
    st.markdown(scenarios["decision"]["reason"])
    st.markdown(
        "Under the confirmatory association used only as a hypothetical elasticity, "
        "revenue and accounting gross profit move in opposite directions. "
        "No scenario in the saved file is supported for deployment."
    )
    _consistency_panel()


def page_market() -> None:
    st.title("Market data")
    _disclaimer()
    quality = load_quality(ROOT)
    exploratory = load_exploratory(ROOT)
    recon = quality["row_reconciliation"]
    zero_week = exploratory["audited"]["weeks_recorded_as_all_zero_price_and_movement"][0]
    st.subheader("What is and is not in the file")
    st.markdown(
        f"Audited movement rows: **{recon['audited_panel_rows']:,}**. "
        f"Rows deleted from that file: **{recon['rows_deleted']:,}**. "
        f"Log sample, a filter of positive scanned sales: "
        f"**{recon['log_sample_rows']:,}**. "
        f"Unclassified `SALE` codes: "
        f"**{quality['unconditional_flag_rows']['sale_unclassified']:,}**. "
        "Blank `SALE` is not a confirmed regular price. "
        f"Week 219 is in the file and is entirely zero price and zero movement "
        f"({zero_week['week_start']} to {zero_week['week_end']}). "
        "Thirty-two week numbers inside 1–399 are absent and were not filled."
    )
    products = product_table(ROOT).sort_values("log_sample_rows", ascending=False)
    stores = store_table(ROOT)
    panel = _panel()
    if panel is None:
        st.info(
            "The log-sample file is not loaded, so product-week charts are hidden. "
            "The counts above come from the saved quality report."
        )
        return
    labels = {
        int(row.upc): f"{row.descrip} · {row.size} · UPC {int(row.upc)}"
        for row in products.itertuples(index=False)
    }
    choice = st.selectbox("Product", list(labels), format_func=lambda upc: labels[upc])
    store_ids = ["All stores"] + [int(store) for store in stores["store"].tolist()]
    store_choice = st.selectbox("Store", store_ids)
    week_min, week_max = st.slider("Week index", 1, 399, (1, 399))
    store = None if store_choice == "All stores" else int(store_choice)
    selected = filter_panel(
        panel,
        upc=int(choice),
        store=store,
        week_min=int(week_min),
        week_max=int(week_max),
    )
    if selected.empty:
        st.warning(
            "No log-sample rows match this product, store, and week window. "
            "Zeros were not added for the missing weeks."
        )
        return
    snapshot = shelf_snapshot(selected)
    st.markdown(
        f"Selected log-sample rows: **{snapshot['rows']:,}**. "
        f"Stores: **{snapshot['stores']}**. Weeks: **{snapshot['weeks']}**. "
        f"Median unit price: **{snapshot['median_unit_price']:.2f} dollars** per item. "
        f"Observed unit-price range: **{snapshot['min_unit_price']:.2f}** to "
        f"**{snapshot['max_unit_price']:.2f} dollars**."
    )
    weekly = weekly_summary(selected)
    _line(weekly, "week", "items", "Week index", "Items sold", "Scanned items by week")
    _line(
        weekly,
        "week",
        "mean_unit_price",
        "Week index",
        "Mean unit price (dollars per item)",
        "Mean unit price by week",
    )
    counts = (
        selected["sale_class"]
        .astype(str)
        .value_counts()
        .rename_axis("sale_class")
        .reset_index(name="rows")
    )
    _bar(
        counts,
        "sale_class",
        "rows",
        "SALE class",
        "Log-sample rows",
        "Promotion codes in the selection",
    )
    st.caption(
        "Coded means B, C, or S. Blank is not a verified regular-price week. "
        "Unclassified covers G and L, which the manual sections used here do not define."
    )


def page_results() -> None:
    st.title("Econometric results")
    _disclaimer()
    table = price_rows(regression_table(ROOT))
    st.markdown(
        "Outcome: log item movement. Price: log dollars per item. "
        "Standard errors are clustered by store, with a Student t interval on "
        "G − 1 degrees of freedom. Week and two-way standard errors are sensitivities. "
        "Two-stage least squares is omitted because no instrument was approved."
    )
    st.latex(
        r"\log Q_{ist}=\alpha_{is}+\gamma_t+\beta \log P_{ist}+\delta D_{ist}+\varepsilon_{ist}"
    )
    st.caption(
        "i product, s store, t week. D is 1 when SALE is B, C, or S. "
        "G and L stay in the reference group in the confirmatory fit."
    )
    show = table[
        [
            "model_id",
            "role",
            "n",
            "store_clusters",
            "estimate",
            "se_cluster_store",
            "ci95_low",
            "ci95_high",
            "associated_movement_change_for_10_percent_price",
            "within_r_squared",
            "causal_claim",
        ]
    ].copy()
    show.columns = [
        "Model",
        "Role",
        "Rows",
        "Store clusters",
        "Price coefficient",
        "Store SE",
        "95% low",
        "95% high",
        "Associated movement at +10% price",
        "Within R²",
        "Causal claim",
    ]
    st.dataframe(show, hide_index=True, use_container_width=True)
    chart = table.loc[
        table["model_id"].isin(
            [
                "M0_pooled_ols",
                "M1_pooled_promotion",
                "M2_upc",
                "M2_upc_and_store",
                "M3_pair",
                "M3_pair_week",
                "M5_confirmatory",
            ]
        )
    ]
    _bar(
        chart,
        "model_id",
        "estimate",
        "Specification",
        "Price coefficient (log items per log dollar)",
        "Price coefficient by specification",
    )
    st.caption(
        "M5 is the pre-specified confirmatory association. It was not chosen "
        "because its R² is the largest. Intervals that lie below −1 describe "
        "this association. They do not establish that a price increase would cut revenue."
    )
    image = ROOT / "reports" / "figures" / "baseline_01_coefficients.png"
    if image.is_file():
        st.image(str(image), caption="Saved baseline figure. Same coefficients as the table.")


def page_identification() -> None:
    st.title("Identification and robustness")
    _disclaimer()
    audit = load_audit(ROOT)
    st.subheader("What the slope does and does not identify")
    st.markdown(
        "M5 identifies a partial association after UPC-store effects, week effects, "
        "and the B/C/S flag, with store-clustered sampling uncertainty. "
        "It does not identify the effect of an exogenous price change. "
        f"Audit branch: **{audit['branch']}**. "
        f"{audit['branch_label']}"
    )
    st.markdown(
        "Price can move with demand because the chain sets the shelf price, "
        "because promotions are chosen, because unobserved quality and local "
        "competition differ, and because a demand shock can be specific to one "
        "UPC. Week effects remove only what is common to every cereal that week. "
        "Pair effects remove only what is constant inside the UPC-store pair."
    )
    st.subheader("Instruments")
    st.markdown(
        "No instrument was approved. Correlations below were computed after the "
        "verdicts were fixed. A large correlation is not a first stage. "
        "Weak-instrument diagnostics were not computed, because two-stage least "
        "squares was not estimated."
    )
    instruments = instrument_table(ROOT)
    st.dataframe(
        instruments[
            [
                "variable",
                "verdict",
                "correlation_with_log_unit_price",
                "verdict_reason",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
    st.subheader("Observational sensitivities")
    robust = robustness_table(ROOT)
    st.dataframe(
        robust[
            [
                "model_id",
                "n",
                "stores",
                "estimate",
                "se_cluster_store",
                "ci95_low",
                "ci95_high",
                "few_store_clusters",
                "role",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
    _bar(
        robust,
        "model_id",
        "estimate",
        "Specification",
        "Price coefficient",
        "Observational price coefficient under pre-specified checks",
    )
    st.caption(
        "High-tier and CubFighter intervals use 25 and 9 store clusters. "
        "None of these rows replaces M5, and none is a causal elasticity. "
        "The adjacent price lead is nonzero, which rejects a narrow "
        "contemporaneous-only story and does not sign the bias."
    )
    _consistency_panel()


def page_scenarios() -> None:
    st.title("Pricing scenarios")
    st.warning(
        "Simulation disclaimer. These calculations apply a stated elasticity to "
        "a historical shelf. They are not forecasts of what a price change would "
        "have done. Competitor response and substitution across cereals are omitted. "
        "Accounting gross profit is not operating profit. Nothing here was implemented "
        "in stores, and no scenario is supported for deployment."
    )
    scenarios = load_scenarios(ROOT)
    price = confirmatory_price(regression_table(ROOT))
    st.latex(r"Q_1 = Q_0 \times (P_1 / P_0)^{\varepsilon}")
    st.latex(r"R_1 = P_1 \times Q_1, \qquad G_1 = (P_1 - c) \times Q_1")
    st.caption(
        "c is a unit acquisition-cost proxy held constant. "
        "ε is either an estimated association used hypothetically or a round assumption."
    )
    panel = _panel()
    if panel is None:
        st.info(
            "Product-level controls need the log-sample file. "
            "The category scenario table from the saved result file is below."
        )
    else:
        _interactive_scenario(panel, scenarios, price)
    st.subheader("Saved category scenarios")
    st.markdown(
        "The comparable menu is the set of UPC-store pairs whose own price history "
        "contains every move from −10 percent to +10 percent. "
        "Percent revenue changes follow the elasticity formula. "
        "Gross-profit percents use those pairs’ recorded margins."
    )
    rows = [
        row
        for row in scenarios["grids"]["full_menu_historical_support"]
        if row["cost_case"] == "recorded_average_acquisition_cost"
        and row["elasticity_case"]
        in {
            "low_sensitivity_pooled_association",
            "central_confirmatory_association",
            "assumed_unit",
            "high_sensitivity_assumed",
        }
        and row["price_ratio"] in {0.90, 0.95, 0.98, 1.02, 1.05, 1.10}
    ]
    show = pd.DataFrame(rows)[
        [
            "elasticity_case",
            "elasticity",
            "price_change",
            "quantity_change",
            "revenue_change",
            "gross_profit_change",
            "pairs",
            "deployment_supported",
        ]
    ]
    st.dataframe(show, hide_index=True, use_container_width=True)
    st.caption(scenarios["decision"]["reason"])


def _interactive_scenario(panel: pd.DataFrame, scenarios: dict, price_row: pd.Series) -> None:
    products = product_table(ROOT).sort_values("log_sample_rows", ascending=False)
    labels = {
        int(row.upc): f"{row.descrip} · {row.size} · UPC {int(row.upc)}"
        for row in products.itertuples(index=False)
    }
    upc = st.selectbox(
        "Product",
        list(labels),
        format_func=lambda key: labels[key],
        key="scenario_upc",
    )
    selected = filter_panel(panel, upc=int(upc))
    if selected.empty:
        st.warning("This UPC has no log-sample rows. No scenario is shown.")
        return
    shelf = shelf_snapshot(selected)
    st.markdown(
        f"Baseline is the median log-sample store-week for this UPC: "
        f"**{shelf['median_unit_price']:.2f} dollars** per item, "
        f"**{shelf['median_items']:.1f}** items, "
        f"median recorded margin **{shelf['median_profit_percent']:.1f}** percent. "
        f"Observed unit prices run from {shelf['min_unit_price']:.2f} "
        f"to {shelf['max_unit_price']:.2f} dollars. "
        "Dollars below are for that median store-week, not for the chain."
    )
    percent = st.slider("Hypothetical price change (percent)", -10, 10, 0, step=1)
    cases = scenarios["elasticity_cases"]
    case_labels = {
        row["case_id"]: f"{row['case_id']} ({row['elasticity']:.3f})" for row in cases
    }
    case_ids = list(case_labels)
    default_index = (
        case_ids.index("central_confirmatory_association")
        if "central_confirmatory_association" in case_ids
        else 0
    )
    case_id = st.selectbox(
        "Elasticity assumption",
        case_ids,
        index=default_index,
        format_func=lambda key: case_labels[key],
    )
    less_favorable = st.radio(
        "Cost assumption",
        ["Recorded median margin", "10 points less favorable"],
        horizontal=True,
    ) == "10 points less favorable"
    elasticity = float(next(row["elasticity"] for row in cases if row["case_id"] == case_id))
    ratio = 1.0 + percent / 100.0
    result = one_shelf_scenario(
        quantity=float(shelf["median_items"]),
        unit_price=float(shelf["median_unit_price"]),
        profit_percent=float(shelf["median_profit_percent"]),
        price_ratio=ratio,
        elasticity=elasticity,
        less_favorable=less_favorable,
        price_min=float(shelf["min_unit_price"]),
        price_max=float(shelf["max_unit_price"]),
    )
    if not result["inside_history"]:
        st.warning(
            "This candidate price is outside the observed unit-price range for this "
            "product. The calculation is an extrapolation."
        )
    quantity_change = result["quantity_change"]
    revenue_change = result["revenue_change"]
    profit_change = result["gross_profit_change"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Item movement", _pct(quantity_change))
    c2.metric("Revenue", _pct(revenue_change))
    c3.metric("Accounting gross profit", _pct(profit_change))
    st.caption(
        f"Unit cost proxy: {result['unit_cost']:.2f} dollars per item "
        f"({result['cost_label']}). "
        f"Candidate price: {result['candidate_price']:.2f} dollars. "
        "Movement, revenue, and gross profit are changes from the median store-week."
    )
    spec = specification_band(scenarios, ratio)
    sampling = sampling_revenue_band(price_row, ratio)
    st.markdown(
        f"Across the four primary stated elasticities, the revenue change ranges from "
        f"**{_pct(spec['low'])}** to **{_pct(spec['high'])}**. {spec['note']} "
        f"The store-clustered interval for the confirmatory association maps this "
        f"price ratio into a revenue change from **{_pct(sampling['revenue_change_at_low'])}** "
        f"to **{_pct(sampling['revenue_change_at_high'])}**. {sampling['note']}"
    )


def page_docs() -> None:
    st.title("Documentation")
    _disclaimer()
    st.markdown(
        "Data: James M. Kilts Center for Marketing, University of Chicago Booth "
        "School of Business, Dominick’s scanner files. Manual created July 2013 "
        "and updated October 2018. Catalog: "
        "https://www.chicagobooth.edu/research/kilts/research-data/dominicks"
    )
    st.markdown(
        "This working copy has no recorded git remote, so there is no GitHub "
        "repository URL to offer. Raw Kilts files are local and are not part of "
        "the result tables."
    )
    st.subheader("Confirmatory specification")
    st.latex(
        r"\log Q_{ist}=\alpha_{is}+\gamma_t+\beta \log P_{ist}+\delta D_{ist}+\varepsilon_{ist}"
    )
    st.markdown(
        "Unit price is `PRICE / QTY`. Revenue is `PRICE × MOVE / QTY`. "
        "Accounting gross profit is sales times `PROFIT / 100`. "
        "`PROFIT` is average acquisition cost in percent of sales, not marginal cost."
    )
    st.subheader("Result files")
    for path in (
        "reports/results/baseline_models.json",
        "reports/results/identification_audit.json",
        "reports/results/pricing_scenarios.json",
        "reports/research_paper/paper.md",
        "reports/research_paper/executive_memo.md",
    ):
        st.markdown(f"- `{path}`")
    paper = ROOT / "reports" / "research_paper" / "paper.md"
    memo = ROOT / "reports" / "research_paper" / "executive_memo.md"
    if paper.is_file():
        with st.expander("Research paper"):
            st.markdown(paper.read_text())
    if memo.is_file():
        with st.expander("Executive memo"):
            st.markdown(memo.read_text())
    limitations = ROOT / "docs" / "limitations.md"
    if limitations.is_file():
        with st.expander("Limitations"):
            st.markdown(limitations.read_text())


def _panel() -> pd.DataFrame | None:
    if os.environ.get("PRICING_DASHBOARD_SKIP_PANEL") == "1":
        return None
    return _cached_panel(str(ROOT))


@st.cache_data(show_spinner="Loading the cereals log sample")
def _cached_panel(root_str: str) -> pd.DataFrame | None:
    os.environ["PRICING_RESEARCH_ROOT"] = root_str
    return read_panel(Path(root_str))


def _disclaimer() -> None:
    st.info(
        "Method status: the confirmatory price coefficient is a conditional "
        "association. It is not a causal elasticity. No price recommendation "
        "in this dashboard is supported for deployment."
    )


def _consistency_panel() -> None:
    checks = consistency_checks(ROOT)
    failed = [row for row in checks if not row["passed"]]
    if failed:
        st.error("Result files disagree: " + "; ".join(row["check"] for row in failed))
    else:
        st.caption(
            f"Artifact check: {len(checks)} comparisons across the baseline, "
            "audit, and scenario files passed."
        )


def _pct(value: object) -> str:
    if value is None:
        return "undefined"
    return f"{100 * float(value):+.1f}%"


def _line(frame: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, title: str) -> None:
    chart = (
        alt.Chart(frame)
        .mark_line()
        .encode(
            x=alt.X(f"{x}:Q", title=x_title),
            y=alt.Y(f"{y}:Q", title=y_title),
        )
        .properties(
            title=title,
            height=280,
            padding={"left": 12, "right": 16, "top": 8, "bottom": 8},
        )
    )
    st.altair_chart(chart, use_container_width=True)


def _bar(frame: pd.DataFrame, x: str, y: str, x_title: str, y_title: str, title: str) -> None:
    chart = (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            x=alt.X(f"{x}:N", title=x_title, sort=None),
            y=alt.Y(f"{y}:Q", title=y_title),
        )
        .properties(
            title=title,
            height=320,
            padding={"left": 12, "right": 16, "top": 8, "bottom": 8},
        )
    )
    st.altair_chart(chart, use_container_width=True)


main()

"""Dashboard artifact checks. The log-sample parquet is not required."""

import os

import pandas as pd
import pytest

from pricing_research.dashboard.artifacts import (
    confirmatory_price,
    consistency_checks,
    filter_panel,
    load_scenarios,
    one_shelf_scenario,
    project_root,
    regression_table,
    sampling_revenue_band,
    shelf_snapshot,
    specification_band,
    weekly_summary,
)


def test_saved_artifacts_agree() -> None:
    checks = consistency_checks(project_root())
    failed = [row["check"] for row in checks if not row["passed"]]
    assert failed == []


def test_confirmatory_units_and_sample_size() -> None:
    row = confirmatory_price(regression_table(project_root()))
    assert int(row["n"]) == 4_707_776
    assert float(row["estimate"]) == pytest.approx(-2.127546339203591)
    assert str(row["causal_claim"]) == "False"
    assert row["associated_movement_change_for_10_percent_price"] == pytest.approx(
        -0.18353956463905607,
        rel=1e-6,
    )


def test_empty_selection_is_empty_and_not_filled() -> None:
    frame = pd.DataFrame(
        {
            "upc": [1, 1],
            "store": [2, 2],
            "week": [10, 11],
            "move": [4.0, 6.0],
            "unit_price": [2.0, 2.5],
            "profit": [20.0, 20.0],
            "promo_coded": [0, 1],
        }
    )
    empty = filter_panel(frame, upc=99, week_min=1, week_max=5)
    assert empty.empty
    assert shelf_snapshot(empty) is None
    assert list(weekly_summary(empty).columns) == [
        "week",
        "items",
        "mean_unit_price",
        "rows",
        "coded_share",
    ]


def test_one_shelf_scenario_matches_the_constant_elasticity_formula() -> None:
    result = one_shelf_scenario(
        quantity=10.0,
        unit_price=2.0,
        profit_percent=25.0,
        price_ratio=1.10,
        elasticity=-1.0,
        less_favorable=False,
        price_min=1.5,
        price_max=2.05,
    )
    assert result["causal"] is False
    assert result["revenue_change"] == pytest.approx(0.0, abs=1e-12)
    assert result["quantity_change"] == pytest.approx(1.0 / 1.10 - 1.0)
    assert result["quantity_unit"] == "items per median store-week"
    assert result["money_unit"] == "dollars per median store-week"
    assert result["inside_history"] is False
    assert result["unit_cost"] == pytest.approx(1.5)
    assert result["gross_profit_1"] > result["gross_profit_0"]


def test_sampling_band_is_not_labeled_as_causal() -> None:
    row = confirmatory_price(regression_table(project_root()))
    band = sampling_revenue_band(row, 1.10)
    assert "not a confidence interval for a causal elasticity" in band["note"].lower()
    assert band["revenue_change_at_low"] < band["revenue_change_at_high"] < 0


def test_specification_band_covers_pooled_and_steep_cases() -> None:
    scenarios = load_scenarios(project_root())
    band = specification_band(scenarios, 1.10)
    assert band["low"] < 0 < band["high"]
    assert "not a confidence interval" in band["note"].lower()


def test_paper_and_memo_use_the_saved_coefficient() -> None:
    root = project_root()
    estimate = float(confirmatory_price(regression_table(root))["estimate"])
    token = f"{abs(estimate):.3f}"
    paper = (root / "reports" / "research_paper" / "paper.md").read_text()
    memo = (root / "reports" / "research_paper" / "executive_memo.md").read_text()
    assert token in paper
    assert token in memo
    assert "4,707,776" in paper
    assert "deploy" in memo.lower()
    assert "causal elasticity" not in paper.lower() or "not a causal elasticity" in paper.lower()


def test_app_script_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    streamlit = pytest.importorskip("streamlit")
    monkeypatch.setenv("PRICING_DASHBOARD_SKIP_PANEL", "1")
    monkeypatch.setenv("PRICING_RESEARCH_ROOT", str(project_root()))
    app_test = pytest.importorskip("streamlit.testing.v1")
    path = project_root() / "src" / "pricing_research" / "dashboard" / "app.py"
    at = app_test.AppTest.from_file(str(path), default_timeout=60)
    at.run()
    assert not at.exception
    chunks = []
    for block in (at.markdown, at.info, at.caption, at.warning):
        chunks.extend(getattr(item, "value", "") for item in block)
    text = " ".join(chunks).lower()
    assert "not a causal elasticity" in text
    # Keep the import used so a missing streamlit install fails clearly.
    assert streamlit.__name__ == "streamlit"
    assert os.environ["PRICING_DASHBOARD_SKIP_PANEL"] == "1"
    at.sidebar.radio[0].set_value("Pricing scenarios").run()
    assert not at.exception
    at.sidebar.radio[0].set_value("Market data").run()
    assert not at.exception
    market = " ".join(getattr(item, "value", "") for item in at.info).lower()
    assert "not loaded" in market

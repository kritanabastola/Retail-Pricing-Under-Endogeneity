"""Checks for the exploratory summary functions. They use synthetic arrays only."""

import numpy as np
import pytest

from pricing_research.reporting.descriptives import (
    coverage_ratio,
    herfindahl,
    largest_share,
    pearson_correlation,
    price_changed,
    quantile_bin_means,
    within_sum_of_squares_share,
)


def test_pearson_correlation_is_signed() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert pearson_correlation(x, x) == pytest.approx(1)
    assert pearson_correlation(x, -x) == pytest.approx(-1)


def test_within_share_is_zero_when_groups_are_constant() -> None:
    values = np.array([1.0, 1.0, 5.0, 5.0])
    means = np.array([1.0, 1.0, 5.0, 5.0])
    assert within_sum_of_squares_share(values, means) == pytest.approx(0)


def test_within_share_is_one_when_group_means_equal_the_grand_mean() -> None:
    values = np.array([1.0, 3.0])
    means = np.array([2.0, 2.0])
    assert within_sum_of_squares_share(values, means) == pytest.approx(1)


def test_concentration_of_equal_and_single_products() -> None:
    assert herfindahl(np.array([1.0, 1.0])) == pytest.approx(0.5)
    assert herfindahl(np.array([4.0])) == pytest.approx(1)
    amounts = np.array([1.0, 2.0, 7.0])
    assert largest_share(amounts, 1) == pytest.approx(0.7)


def test_coverage_excludes_category_missing_weeks() -> None:
    assert coverage_ratio(3, 1, 5, {3, 4}) == pytest.approx(1)
    assert coverage_ratio(2, 1, 5, {3}) == pytest.approx(0.5)


def test_price_change_uses_a_dollar_tolerance() -> None:
    assert price_changed(1.0, 1.0004) is False
    assert price_changed(1.0, 1.01) is True


def test_quantile_bin_means_cover_every_row() -> None:
    x = np.arange(20, dtype=float)
    rows = quantile_bin_means(x, x * 2, n_bins=4)
    assert sum(row["n"] for row in rows) == 20
    assert rows[0]["y_mean"] < rows[-1]["y_mean"]

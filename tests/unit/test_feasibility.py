"""Synthetic movement rows for the feasibility screen. No Kilts extract is loaded."""

from pricing_research.reporting.feasibility import profile_rows


def _row(
    store: str = "2",
    upc: str = "111",
    week: str = "1",
    move: str = "4",
    qty: str = "1",
    price: str = "2.00",
    sale: str = "",
    profit: str = "25.3",
    ok: str = "1",
    price_hex: str = "4000000000000000",
    profit_hex: str = "40394CCCCCCCCCCD",
) -> dict[str, str]:
    return {
        "STORE": store,
        "UPC": upc,
        "WEEK": week,
        "MOVE": move,
        "QTY": qty,
        "PRICE": price,
        "SALE": sale,
        "PROFIT": profit,
        "OK": ok,
        "PRICE_HEX": price_hex,
        "PROFIT_HEX": profit_hex,
    }


def test_screen_counts_price_variation_and_exclusions() -> None:
    rows = [
        _row(week="1", price="2.00", move="4", sale=""),
        _row(week="2", price="1.50", move="6", sale="B"),
        _row(week="2", price="1.50", move="6", sale="B"),
        _row(week="3", price="2.00", move="0", ok="1"),
        _row(week="4", price="2.00", move="3", ok="0"),
        _row(store="8", upc="222", week="1", qty="3", price="2.00", move="6", profit="10"),
        _row(store="8", upc="222", week="2", qty="3", price="2.00", move="3", profit="12"),
    ]
    profile = profile_rows(rows)
    assert profile.n_rows == 7
    assert profile.duplicate_keys == 1
    assert profile.log_sample_rows == 5
    assert profile.ok_counts["0"] == 1
    assert profile.move_zero == 1
    cereal = profile.pairs[("111", "2")]
    assert cereal.price_varies is True
    bundle = profile.pairs[("222", "8")]
    assert bundle.price_varies is False
    assert bundle.profit_varies is True
    assert bundle.qty_varies is False

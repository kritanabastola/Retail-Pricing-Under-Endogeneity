"""Public Kilts URLs for the categories selected in Phase 1.

Cereals is the analysis panel. Oatmeal is the robustness category.
Canned soup is not part of this build.
"""

from __future__ import annotations

from dataclasses import dataclass

KILTS_MEDIA = (
    "https://www.chicagobooth.edu/research/kilts/research-data/-/media/"
    "enterprise/centers/kilts/datasets/dominicks-dataset"
)


@dataclass(frozen=True)
class CategoryFiles:
    """Local names and remote paths for one category."""

    name: str
    movement_zip: str
    movement_csv: str
    upc_csv: str
    movement_url: str
    upc_url: str
    manual_week_min: int
    manual_week_max: int
    role: str


def _files(name: str, acronym: str, week_min: int, week_max: int, role: str) -> CategoryFiles:
    movement_zip = f"w{acronym}.zip"
    upc_csv = f"upc{acronym}.csv"
    return CategoryFiles(
        name=name,
        movement_zip=movement_zip,
        movement_csv=f"w{acronym}.csv",
        upc_csv=upc_csv,
        movement_url=f"{KILTS_MEDIA}/movement_csv-files/{movement_zip}",
        upc_url=f"{KILTS_MEDIA}/upc_csv-files/{upc_csv}",
        manual_week_min=week_min,
        manual_week_max=week_max,
        role=role,
    )


CATEGORIES: dict[str, CategoryFiles] = {
    "cereals": _files("cereals", "cer", 1, 399, "primary analysis panel"),
    "oatmeal": _files("oatmeal", "oat", 91, 399, "robustness panel, not the confirmatory sample"),
}


def category_files(name: str) -> CategoryFiles:
    """Return the file description for a selected category."""
    try:
        return CATEGORIES[name]
    except KeyError as exc:
        known = ", ".join(sorted(CATEGORIES))
        raise KeyError(f"Unknown category {name!r}. Expected one of: {known}.") from exc

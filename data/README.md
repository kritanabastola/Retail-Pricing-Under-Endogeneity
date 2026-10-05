# Data directories

`raw/`, `interim/`, and `processed/` are gitignored. Dominick's files are released for academic research and are not redistributed from this repository.

## Obtain the files

Automatic download uses `curl`, because the Python SSL store on the machine used for this project rejected the Booth certificate. If `curl` fails, the command prints the URL and the path to save by hand.

```bash
python -m pricing_research.data.acquire --raw-dir data/raw
```

That fetches cereals (`wcer.zip`, `upccer.csv`) and oatmeal (`woat.zip`, `upcoat.csv`). Canned soup is not part of this build. Do not commit the zips or the UPC CSVs.

## Build the panel

```bash
python -m pricing_research.data.build
```

The default category is cereals and the default is the full file. The command writes:

- `data/interim/cereals_movement_audited.parquet` — every movement row, with flags and derived fields
- `data/processed/cereals_log_sample.parquet` — the pre-specified log sample only
- `reports/results/data_quality.json`
- `reports/tables/cleaning_summary.csv`
- `reports/tables/cereals_product_summary.csv`
- `reports/tables/cereals_store_summary.csv`

`--max-rows N` writes `*_dev` files and `data_quality_cereals.json`. That extract is a development sample. Do not report its counts as the full-sample panel.

Oatmeal uses the same definitions:

```bash
python -m pricing_research.data.build --category oatmeal
```

That run writes `data_quality_oatmeal.json` and does not replace the cereals quality report.

Missing UPC-store-weeks are not added. A recorded zero `MOVE` stays in the audited panel and is a different object from an absent record.

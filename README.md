# Decomposing Racial Gaps in Mortgage Denial Rates: HMDA 2024

Big Data Analysis, Group 3, National Economics University.

## Data

FFIEC/CFPB 2024 national loan-level HMDA file (reporting year 2024 only).
Page: https://ffiec.cfpb.gov/data-publication/one-year-national-loan-level-dataset/2024
Not stored in this repo. Run `python scripts/download_data.py` (writes `data/raw/` and `data/DOWNLOAD_MANIFEST.json`).

## Environment

Python 3.13, Java <version> (PySpark). `pip install -r requirements.txt`.
Windows + PySpark also needs `hadoop/bin/winutils.exe` and `hadoop.dll` (not included; see B07).
Optional: set `HMDA_ROOT` to the project root; otherwise notebooks locate the folder containing `origin/`.

## Run order

| Step | Folder | Purpose | Output (not in repo unless CSV/PNG) |
|---|---|---|---|
| 0 | `scripts/` | download raw CSV | `data/raw/` |
| 1 | `B04 - 30 Oct` | stream CSV to bucketed Parquet | `B04_raw_with_buckets.parquet` |
| 2 | `B05 - 30 Oct` | DuckDB data-quality audit | `B05_*.csv`, figures |
| 3 | `B06 - Clean` | Pandas cleaning (`clean_all`, analytic S0) | `B06_*.parquet`, `B06_*.csv` |
| 4 | `B07 - Spark Clean` | PySpark cleaning; needs B06 outputs | `B07_*.parquet`, `B07_*.csv` |
| 5 | `B14 - EDA` | descriptive and diagnostic analysis | `B14_*.csv`, figures |
| 6 | `B15 - EDA Pyspark` | PySpark EDA; needs B14 CSV outputs | `B15_*.csv`, figures |
| 7 | `B16 - Pandas Spark Compare` | Pandas vs. PySpark comparison | comparison outputs/tables |
| 8 | `B17 - Predictive` | predictive modeling | model metrics/outputs/figures |

## Not in the repo

Parquet files, model files, scratch folders, and `B06_lender_sizes.csv` / `B05_census_tract_anomaly.csv` (contain lender identifiers). Regenerate by running the notebooks in order.

## Scope

Descriptive and diagnostic analysis. No remaining gap is interpreted as proof of discrimination.
Lenders are anonymised (Decision D-O).

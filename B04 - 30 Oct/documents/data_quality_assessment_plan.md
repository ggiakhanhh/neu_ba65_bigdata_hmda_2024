# Data Quality Assessment Plan: HMDA 2024 Public LAR

**Project:** Decomposing Racial Gaps in Mortgage Denial Rates (Group 3, Big Data Analysis)
**Scope:** Week 2 (Data Engineering). This plan feeds directly into the cleaning rulebook (`data_cleaning_rules.md`) and the Pandas vs. PySpark equivalence checks.

Items marked **[decide after profiling]** are proposals whose thresholds or choices should be confirmed against the real data. Everything else follows from the project proposal, the assignment brief, or the group's Data Dictionary.

---

## 1. Principles

1. **Inspect before changing.** Every step first measures a problem, then a rule decides what to do about it.
2. **Flag, do not delete.** Unusual values get a flag column. Rows are removed only by explicit filter rules (F-rules) that are logged in the row-flow waterfall.
3. **Distinguish kinds of "missing".** Empty, `NA`, `Exempt`, `1111`, `8888`, `9999` and structurally absent values mean different things and are counted separately.
4. **Never replace missing values with zero.** Missing stays NULL and carries a status or flag column.
5. **Everything is reproducible and identical in Pandas and PySpark.** Each decision is written to the rule ledger with the number of affected rows.
6. **The analysis is descriptive and diagnostic, not causal.** Missing underwriting variables (credit score, assets, AUS results) limit any interpretation of racial gaps.

---

## 2. Data layers and ingest specification

| Layer | File | Content | Rows |
|---|---|---|---|
| Raw | `raw_with_buckets.parquet` | All 99 original columns as **string**, unmodified, plus `row_id` (int64) and `bucket` (int8) | = CSV rows |
| Clean (all rows) | `clean_all.parquet` | Typed columns, special codes converted to NULL with status flags, validity flags, engineered features. **No rows removed** | = CSV rows |
| Analytic | `analytic.parquet` | `clean_all` filtered by the sample rules (F-rules) | fewer |

**Why read everything as string at ingest.** `pd.read_csv` guesses types and silently turns strings such as `NA` into NaN, drops leading zeros (`census_tract`, `county_code`), converts integers to floats when NULLs are present, and guesses types per internal block or per chunk. Types are therefore applied explicitly, once, when building `clean_all`.

**Recommended `read_csv` settings for raw ingest**

```python
pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""],  # or [] to keep empty strings
            encoding="utf-8", chunksize=500_000, low_memory=False)
```

- `keep_default_na=False` preserves the literal text `NA`.
- The group's ingest converts empty cells to NULL (`na_values=[""]`). Record this in the rule ledger as part of rule T01. If `na_values=[]` is used instead, rule T01 performs the conversion later.

**Added technical columns (metadata, not data changes)**

- `row_id`: 0-based position of the row in the source CSV. Used for traceability and row-level Pandas/Spark comparison.
- `bucket`: pseudo-random integer 0 to 99, a deterministic Knuth multiplicative hash of `row_id`. Used to create **nested samples** for the benchmark (25% = `bucket < 25`, 50% = `bucket < 50`, 100% = all). Both engines read the same column, so no random seeds need to be synchronized.
- `bucket` is **not** a deduplication tool. See Step 5.

**Storage decisions to document**

- Parquet with ZSTD compression, typed columns in `clean_all`/`analytic`.
- Multiple part files (roughly 8 to 20, a few hundred MB each) are acceptable. Pandas and Spark both read a directory of Parquet files as one table.
- No partitioning by column. The main workload (group by race x loan type) does not benefit from state partitioning, and partitioning would create many small, unevenly sized files.
- Benchmarks run on `analytic.parquet` (typed), not on the all-string raw layer.

---

## 3. The eight assessment steps

### Step 0: Source profile

Record in the report appendix (required by assignment section 2.3):

- Download URL, download date, file name, file size, checksum (SHA-256)
- File format, delimiter, encoding
- Row count (counted with a CSV parser such as DuckDB, **not** `wc -l`, because quoted fields may contain line breaks) and column count (expected 99)
- Unit of observation: **one row = one loan application record**, not necessarily an originated loan
- Reporting year (must be 2024) and the data dictionary version used

### Step 1: Column catalog

Run `build_column_catalog.py`. For every column the catalog records:

- Name, position, in CSV or technical, dictionary type, target dtype, unit
- Which research questions use it (`used_in`), and its tier (1 = core, 2 = supporting/filter/QA, 3 = auxiliary)
- Allowed values (full text), parsed allowed codes, detected special codes
- Expected string length (for identifiers), applicable cleaning rule IDs
- Predictor status (target, leakage, sensitive, check) and known dictionary issues

Checks in this step: CSV header equals the dictionary field list (set and order), no duplicate column names, all proposal core variables are tier 1.

### Step 2: Completeness

For each column, count each category **separately**:

| Category | Example |
|---|---|
| Empty (NULL after ingest) | blank cell |
| `NA` | `income = NA` |
| `Exempt` | `debt_to_income_ratio = Exempt` |
| `1111` | `reverse_mortgage = 1111` |
| `8888`, `9999` | `applicant_age = 8888`, `co_applicant_age = 9999` |

Look up the meaning of each special code per column in the dictionary, because the same code can mean different things in different columns.

**Separate structural missingness from concerning missingness.**

- Structural (expected): `denial_reason_*` only when denied; `interest_rate`, `rate_spread`, `total_loan_costs`, points/fees only when a loan is originated; repeated race/ethnicity/AUS fields blank when no extra option is reported; co-applicant fields when there is no co-applicant.
- Concerning: DTI, CLTV, income missing where they should be reported.

**How to tell them apart:** compute the missing rate by `action_taken`, `loan_purpose`, `loan_type`, `lei` (lender) and `state_code`. Lenders that rely heavily on exemptions will stand out.

**Project-specific and most important:** compute the missing/exempt rate of DTI, CLTV and income **by race group**. If missingness differs between groups, the way missing values are treated can itself shift the gap being measured.

Also decide, for `derived_race`, which groups are kept as comparison groups, which are reported separately, and why (White, Black or African American, Asian as main groups; American Indian or Alaska Native, Native Hawaiian or Other Pacific Islander, 2 or more minority races, Joint, Race Not Available, Free Form Text Only reported separately, not dropped). **[decide after profiling group sizes]**

### Step 3: Validity

- **Categorical columns:** list every distinct value (`value_counts(dropna=False)`) and compare with `allowed_codes`. Unknown values are errors or undocumented codes.
- **Numeric columns:** check ranges (proposals, **[decide after profiling]**):
  - `loan_amount > 0`
  - `income > 0` (income is in **thousands of USD**)
  - CLTV between 0 and 200
  - `interest_rate` between 0 and 25
  - `loan_term` between 1 and 480 months
  - `tract_minority_population_percent` between 0 and 100
- **Formats:** `lei` = 20 characters, `census_tract` = 11 digits, `county_code` = 5 digits, `state_code` = 2 letters, `derived_msa_md` = 5 digits.
- **Rounding and binning in the public file:** several values are rounded or binned (for example `property_value`, DTI bins, age bins). Read the dictionary notes before calling anything "abnormal".
- **Type-conversion audit** for every numeric column: `NULL after cast = empty + known special codes + unparseable values (expected 0)`. If the equation does not balance, unknown values exist.

### Step 4: Cross-field consistency

Each check produces a violation count (expected 0 unless explained):

| Check | Condition |
|---|---|
| Denial reason vs. outcome | `denial_reason_1` is a real reason only when `action_taken = 3` (and code 10 "not applicable" otherwise) |
| Pricing fields vs. outcome | `interest_rate`, `rate_spread`, `total_loan_costs` present mostly for originated loans |
| Geography | `state_code` agrees with the first 2 digits of `county_code` and `census_tract` |
| CLTV recomputation | reported CLTV vs. `loan_amount / property_value x 100` (large gaps flagged; `property_value` is rounded, so small gaps are normal) |
| Derived vs. source demographics | `derived_race`, `derived_ethnicity`, `derived_sex` agree with the applicant/co-applicant source fields |
| Product type | `derived_loan_product_type` agrees with `loan_type` + `lien_status` |
| Plausibility | extreme `loan_amount / (income x 1000)` ratios |
| Year | `activity_year = 2024` for every row |

### Step 5: Duplicates

HMDA public data has **no unique loan identifier**, so duplicates require care.

1. Count rows identical on **all 99 original columns** (exclude `row_id` and `bucket` from the comparison key, otherwise no duplicates will ever be found).
2. Count rows identical on a core subset (for example `lei`, `census_tract`, `loan_amount`, `income`, `action_taken`, ...).
3. Check whether duplicate groups concentrate in a few lenders (possible filing issue) or are spread out (likely coincidence, especially because amounts and income are rounded).
4. **Do not delete automatically.** Main sample keeps duplicates and reports them (`dup_group_size`, `flag_dup_extra`). A version without duplicates is run as a robustness check (RQ4).
5. Tie-breaking rule for any removal: **keep the row with the smallest `row_id`** in each duplicate group, in both Pandas and Spark. (Spark's `dropDuplicates` does not guarantee which row it keeps.)
6. Compute duplicate flags on the **full** dataset before drawing any bucket-based sample.

```python
key = [c for c in df.columns if c not in ("row_id", "bucket")]
# Pandas (df sorted by row_id)
dup_extra = df.duplicated(subset=key, keep="first")
# Spark
w = Window.partitionBy(*key).orderBy("row_id")
sdf = sdf.withColumn("dup_rank", F.row_number().over(w))   # dup_rank > 1 = extra copy
```

### Step 6: Outliers

Separate genuine extremes from data errors using **business reasoning**, not only statistics.

- Describe `loan_amount`, `income`, CLTV, interest rate with percentiles (p1, p50, p99, p99.9) and log-scale plots, because amounts and income are right-skewed.
- Large loans and high incomes are often genuine (jumbo loans). Income of 1 (thousand USD) with a very large loan, or CLTV in the thousands, more likely indicates an error or special convention.
- Do not remove values because they look unusual. Flag them. Winsorizing (p1/p99) is used only as a robustness variant.
- Percentile cut-offs must be computed once, exactly, and stored as constants shared by Pandas and Spark (Spark's approximate percentile functions can differ).

### Step 7: Coverage and representativeness

- Row counts by state; number of lenders (LEI); concentration (share of applications held by the top 10 lenders)
- Sample size of **each race group after every filtering step**
- For small groups, report confidence intervals or merge groups, because their denial rates are unstable

### Step 8: Row-flow waterfall and rule ledger

**Waterfall table:** raw rows, then each filter step.

| Step | Rows kept | Rows removed | Denial rate: White | Black | Asian | Other groups |
|---|---|---|---|---|---|---|
| Raw (all rows) | | | n/a | n/a | n/a | n/a |
| F01 `action_taken` in {1,2,3} | | | | | | |
| F02 exclude business/commercial purpose | | | | | | |
| F03 exclude reverse mortgages | | | | | | |
| Final analytic sample | | | | | | |

If a filter changes a group's denial rate or the gap materially, that is a finding and must be discussed.

**Rule ledger** (one row per rule; see `data_cleaning_rules.md`): ID, description, reason, rows affected, percentage, how it is implemented in Pandas, how it is implemented in Spark, date and owner.

---

## 4. Post-ingest verification checklist

Run once after creating `raw_with_buckets.parquet`, and keep as an automated `validate_raw()` function:

1. Row count equals the DuckDB `count(*)` on the CSV; file checksum recorded.
2. 99 original columns plus `row_id` and `bucket` (101 total), names match the dictionary.
3. All original columns are strings; `row_id` is unique and runs from 0 to N-1; `bucket` is in 0 to 99.
4. No unintended NaN: only empty cells are NULL; literal `NA` strings are still present.
5. No repeated header rows inside the data (for example `loan_type == "loan_type"` count is 0).
6. Identifier lengths: `lei` 20, `census_tract` 11, `county_code` 5.
7. Special-token counts per column recorded (`NA`, `Exempt`, `1111`, `8888`, `9999`).
8. Head, middle and tail of the file inspected (truncation shows at the end).
9. Bucket check: each bucket is about 1% of rows, and the 25% sample has a denial rate and race mix close to the full data.
10. Re-read the written Parquet and compare row counts and a sample of values with the source.

---

## 5. Pandas and Spark equivalence notes for this phase

- Both engines read the same Parquet and apply the same rules in the same order.
- Pandas `groupby` drops NaN keys by default; use `dropna=False`. Spark keeps NULL groups.
- Spark reads empty CSV strings as NULL; Pandas with `keep_default_na=False` keeps `""`. Reading from the shared Parquet avoids this difference.
- Trim whitespace before casting; compare NULL counts after casting in both engines.
- Compare integers exactly and floats with a tolerance (for example 1e-9).
- Never rely on row order; sort or compare by key.
- Use DuckDB as an independent third reference when Pandas and Spark disagree.

---

## 6. Known issues in the group's Data Dictionary

- `aus_1`: the Allowed Values were copied from `initially_payable_to_institution`; use the values from `aus_2` instead.
- `debt_to_income_ratio`: the dictionary lists `36%`, `37%`, ...; real data may store `36`. Check with `value_counts`.
- `applicant_age` (`8888`) and `co_applicant_age` (`8888`, `9999`): meanings not yet verified against the official source.
- `purchaser_type`: max length 1 in the schema but codes 71 and 72 exist. Do not validate by length.
- `derived_msa_md`: the dictionary does not state the value used for areas outside an MSA. Check with `value_counts`.

---

## 7. Suggested execution order

1. Step 0 and ingest to `raw_with_buckets.parquet`, plus the post-ingest checklist (Section 4).
2. Step 1 column catalog.
3. Steps 2 and 3 (completeness and validity), the foundation for every later step.
4. Steps 4, 5 and 6 (consistency, duplicates, outliers).
5. Step 7, then finalize Step 8. Write rule ledger entries as decisions are made rather than at the end.

Code organization: `01_ingest.py`, `02_catalog.py`, `03_profile.py`, `04_rules_clean.py`, so that the PySpark implementation can follow the same structure.

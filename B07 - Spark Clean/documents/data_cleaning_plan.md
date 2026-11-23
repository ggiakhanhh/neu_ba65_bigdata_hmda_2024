# Stage B Plan: Data Cleaning & Preparation (HMDA 2024)

**Inputs:** `B04_raw_with_buckets.parquet` (12,259,199 rows, 101 columns), `data_cleaning_rules.md` (v1), B04 profile tables in `output/`.
**Outputs:** `clean_all.parquet` (same rows as raw), `analytic.parquet` (F rules applied), waterfall + rule ledger, Pandas vs PySpark equivalence report.

How the documents relate: **B04 notebook = evidence**, **rulebook = policy**, **this plan = order of work + what to change in the rulebook because of the evidence**.

---

## 1. Rulebook changes required by B04 evidence (v1 -> v2)

| Rule | Issue found | Proposed change |
|---|---|---|
| T01 | Says empty strings are "already NULL at ingest". Ingest used `na_values=[]`, so blanks are still `""` in raw | State that raw keeps `""`; T01 converts `""` to NULL in `clean_all` |
| T02 | Evidence: `income` has 0 `Exempt`; values 1111 / 8888 / 9999 (77 / 11 / 27 rows) are ordinary numbers | Keep T02 as is (only `NA`/`Exempt` -> NULL). Add note: `1111/8888/9999` are NOT sentinels in numeric columns [Hypothesis, verify in HMDA docs] |
| T06 | Column list for `1111` was assumed, not profiled | Replace with the list produced by the full 99-column profile (Step B-2) |
| T08 | Age codes: `applicant_age` has 1,463,684 `8888`; `co_applicant_age` has 1,178,955 `8888` and 6,666,402 `9999` | Keep rule; add cross-tab of these codes by `action_taken` (Step B-2) before finalizing |
| V02 | 165,254 rows: 157,494 exactly 0 and 7,760 negative | Flag only. Add two sub-flags (`income_zero`, `income_negative`). X06 stays NULL when income <= 0 |
| V04 | 83,442 rows have rate <= 0 (58,720 originated, 21,737 purchased) + 1 row > 25 | Flag only; `interest_rate` is descriptive only (not an RQ variable). Check `lien_status` of zero-rate rows |
| V06 | Rule ignores sentinels: `census_tract = 'NA'` (349,023 rows) would be flagged | Apply length test only when value is not `NA`/`Exempt`; store `geo_status` (`value`/`na`) instead. Inspect the 1 real `census_tract` violation |
| V07 | Rulebook tests 2-digit prefix only; B04 also tested 5-digit county prefix (0 mismatches on both) | Define V07 as both tests; expected flagged = 0 |
| V08 | Written as "real reason but action != 3". Evidence: `action_taken = 7` (preapproval denied) legitimately has real reasons (46,161 rows) | Redefine: real reason (1-9) with `action_taken` not in {3, 7}, OR action in {3, 7} with code `10`/blank. Expected flagged = 0. Treat `1111` as Exempt, never as a real reason |
| V10 | 20,229 clusters, 26,755 extra copies (0.22%) | Keep. First copy = smallest `row_id`; use MD5 key over 99 columns (`chr(31)` separator) |
| X03 | Group sizes (decision sample): White 5,550,877; Race Not Available 1,526,078; Black 762,461; Asian 524,984; Joint 189,064; AIAN 63,158; 2+ races 21,855; NHPI 21,118; Free Form 2,184 | Main gap groups White/Black/Asian; others reported separately. Free Form (n=2,184) is too small for stable rates: report with caution |
| X09 | ~287-288k rows (~2.3%) carry `Exempt`/`1111` in many fields | Add `is_exempt_filer` (e.g. `n_exempt_fields >= k`, choose k after profiling) to analyse them separately |
| X11 / Section 6 | `fin_complete` will remove many "Race Not Available" rows (24.40% DTI missing vs 3.75-8.95% elsewhere) | Waterfall must show **race composition and denial rate before/after** `fin_complete` (selection effect) |
| S4 | Percentiles in `B04_financial_percentiles.csv` were computed on all 12.26M rows | Recompute p1/p99 on S0 once, store as constants, apply in both engines (rulebook 8.2) |

## 2. Decisions to lock before coding (record in `decisions.md`)

| ID | Decision | Recommended default |
|---|---|---|
| D-A | Confirm F02 (business purpose) and F03 (reverse mortgage) | Keep both; report waterfall effect (~525k rows, ~6% in the 29 Oct run) as a deviation from the proposal |
| D-B | `income = 0` / negative in models | Keep rows; flag V02; excluded in S5; `loan_to_income` NULL |
| D-C | Zero interest rate | Flag only; descriptive use only |
| D-D | Group handling for X03 | As in table above |
| D-E | Partitioning of Parquet | `clean_all`: unpartitioned (same rows as raw, `bucket` kept for 25/50/100% benchmark); `analytic`: optionally partition by `bucket` is NOT needed; keep single file and explain why |
| D-F | Third engine | DuckDB (used in B04) may be used as an independent audit, but T/V/X/F must be implemented in **Pandas and PySpark** |

## 3. Steps (in order)

**B-1. Lock rules.** Update rulebook to v2 using Section 1; fill Section 2 decisions. *Done when:* `decisions.md` has no "Open" rows for D-A to D-F.

**B-2. Close the profiling gap (DuckDB, one notebook section).**
- B04 profiled only 10 columns. Profile **all 99**: blank / `NA` / `Exempt` / `1111` / `8888` / `9999` counts per column (this fixes the T06 list and T09).
- Cross-tab `applicant_age` / `co_applicant_age` special codes by `action_taken`.
- Count V01-V05 flags **inside the F01-F03 sample** (what matters for the analysis).
- Inspect the 1 `census_tract` violation and the zero-rate rows by `lien_status`.

**B-3. Global computations first (full data, before any filter).** Duplicate key + `dup_group_size`, `flag_dup_extra`, lender sizes (X10), S4 percentiles. In Pandas compute the MD5 key per chunk, then one global group-by on the key column only (never per-chunk dedup).

**B-4. Pandas implementation (chunked) -> `clean_all.parquet`.** Apply T, V, X in rule order; log rows affected per rule; row count must stay 12,259,199.

**B-5. PySpark implementation -> `clean_all_spark.parquet`.** Same rules, same flag names, same casts (trim first, then cast).

**B-6. Equivalence report (>= 3 outputs, requirement of the assignment).** Compare: row count after each rule; NULL counts after cast for `income`, `dti_point`, `cltv`; overall denial rate; denial rate by race; counts of every V flag. Integers exactly, floats with tolerance (1e-9). Any discrepancy: investigate (types, special codes, duplicates), do not edit results.

**B-7. Apply F rules -> `analytic.parquet`.** Waterfall table per rule: rows kept/removed and denial rate by race before and after. Then `fin_complete` subsample waterfall (race composition shift). Verify F01 = 8,661,779 rows.

**B-8. Rule ledger + documentation.** Fill the ledger template (rulebook Section 9) with rows affected, % and the Pandas/Spark implementation of each rule. Export to `output/`.

## 4. Suggested notebooks
`B05` profiling gap + rule lock evidence (DuckDB) -> `B06` Pandas cleaning -> `B07` PySpark cleaning -> `B08` equivalence + waterfall. Each follows the conventions (md cell per code cell, English, cells <= ~40 lines, no hard-coded numbers).

## 5. Definition of done for Stage B
- [ ] `clean_all` has exactly 12,259,199 rows in both engines, identical column names and flags.
- [ ] Every T/V/X/F rule has a ledger row with counts and both implementations.
- [ ] Pandas and PySpark agree on all comparison outputs (or every discrepancy is explained).
- [ ] F01 yields 8,661,779 rows; F02/F03 effect and race-level denial rates are in the waterfall.
- [ ] `decisions.md` is up to date and the rulebook is v2.

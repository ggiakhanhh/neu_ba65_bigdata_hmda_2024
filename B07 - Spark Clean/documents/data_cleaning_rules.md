# Data Cleaning Rulebook: HMDA 2024 Public LAR (v2.3 Final Reconciled)

**Project:** Decomposing Racial Gaps in Mortgage Denial Rates: A Large-Scale Analysis of the 2024 U.S. HMDA Market  
**Course:** Big Data Analysis (Final Project) — Group 3  
**Version:** 2.3 Final Reconciled (Verified against `B05 - 31 Oct.ipynb` outputs and `HMDA_Public_LAR_Data_Dictionary.xlsx`)  
**Companion documents:** `data_cleaning_plan.md`, `decisions.md` (Locked D-A through D-I)

**Evidence key (`B05 - 31 Oct.ipynb`, 1-based cell index → artifact):** 7 sentinel profile · 9 T03 23-col cast audit · 11 T06 / dr1 co-occurrence · 13 X09 · 15 age codes · 17 X05 undocumented blanks · 19 X05 4-state agreement · 21 waterfall & F02/F03 domain · 23 V01–V05 · 25 V02 by action · 27 V04 / zero-rate · 29 geo T05/V06/V07 · 31 DTI · 33 T12 7-field zero audit · 35 pre-RQ3 tract disparity · 37 V09 by lien · 39 V09 by loan type · 41 X11 race waterfall · 43 S5 dual robustness · 45 milestone summary.

---

## 1. Principles

1. Rules fall into four types:
   - **T** (column transforms, row count unchanged: 12,259,199 rows)
   - **V** (validity flags / diagnostics, row count unchanged: 12,259,199 rows)
   - **X** (feature engineering, row count unchanged: 12,259,199 rows)
   - **F** (row filters; the only type that reduces rows, logged in waterfall)
2. Unusual or extreme values are **flagged, not deleted**.
3. **No imputation and no replacing missing values with zero.** Missing values (including hidden Census zeros / `-1` where the evidence in T12 shows they encode missing tract/geography) stay `NULL` with a `<col>_status` column.
4. Every rule records the **number of rows affected** and percentage of dataset.
5. Every rule is implemented identically in Pandas and PySpark, with DuckDB used as an independent audit engine. All row filters use **positive set membership** (`.isin`) so NULL/NaN behave identically in both engines.

Output layers:
$$\text{raw (all strings, 101 cols)} \longrightarrow \text{clean\_all (T, V, X; 12,259,199 rows)} \longrightarrow \text{analytic (F rules applied; 8,136,664 rows)}$$

---

## 2. T rules: column transforms (`clean_all`)

| ID | Columns | Rule | Reason / evidence |
|---|---|---|---|
| T01 | All string columns | Trim leading/trailing whitespace. Raw layer keeps `""` (ingest `na_values=[]`); T01 converts `""` to NULL in `clean_all`. | Engine equivalence. B05 (cell 7) found 0 padded cells in all 99 columns, so trim is a safety no-op today. |
| T02 | `income`, `property_value`, `combined_loan_to_value_ratio`, `interest_rate`, `rate_spread`, `total_loan_costs`, `total_points_and_fees`, `origination_charges`, `discount_points`, `lender_credits`, `loan_term`, `prepayment_penalty_term`, `intro_rate_period`, `multifamily_affordable_units` | Case-insensitively convert `"NA"` and `"Exempt"` to NULL. Create `<col>_status` ∈ {`value`, `na`, `exempt`, `blank`}. `1111`, `8888`, `9999` are treated as ordinary numbers `[Hypothesis: Number schema type in Data Dictionary and no Exempt token in income; counts are small, e.g. income 1111 = 77 rows]`. | Preserves type of missingness. |
| T03 | All 23 Dictionary `Number` columns: T02 (14 cols) + `activity_year`, `loan_amount`, `tract_population`, `tract_minority_population_percent`, `ffiec_msa_md_median_family_income`, `tract_to_msa_income_percentage`, `tract_owner_occupied_units`, `tract_one_to_four_family_homes`, `tract_median_age_of_housing_units` | Explicit cast (`Int64`/`Float64`) **after T01/T02/T12**. Audit: `valid + missing_total + unparseable = 12,259,199` and `unparseable = 0`. `[Verified: B05 cell 9 — 0 unparseable in all 23 numeric columns]`. | Detect silent coercion errors across engines. |
| T04 | Categorical code columns (`loan_type`, `loan_purpose`, `action_taken`, `occupancy_type`, `*_ethnicity_*`, `*_race_*`, `*_sex*`, `aus_*`, `denial_reason_*`, ...) | Keep as **string**. | Codes are labels. |
| T05 | `lei`, `state_code`, `county_code`, `census_tract`, `derived_msa_md` | Keep as string. Case-insensitively convert `'NA'` (incl. the 1 lowercase `'na'` in `census_tract`, `row_id=1486879`) and `'Exempt'` to NULL, with `<col>_status` ∈ {`value`, `na`, `exempt`, `blank`}. Raw `'NA'` counts: `state_code` 215,946; `county_code` 296,190; `census_tract` 349,023 + 1 `'na'`. **`derived_msa_md = '99999'` (1,781,406 rows) is kept as a code with status `non_msa`** `[Hypothesis: non-metropolitan; '99999' is not documented in the Data Dictionary]`. Check length (20/2/5/11/5) on non-NULL values; **no zero padding**. | `<col>_status` preserves the reason for V06/V07. |
| T06 | Categorical columns with exemption code `'1111'` | **Keep `1111` as category "Exempt".** Whitelist = 15 columns in `output/B05_t06_exempt_columns_whitelist.csv`: 14 `[Verified: HMDA Data Dictionary (1111 = Exempt)]` + `denial_reason_1` `[Hypothesis: code 1111 is not in the dictionary's allowed values 1–10; 78.04% co-occurrence with the 28 documented exempt fields, while 22,885 rows carry it with none — B05 cell 11]`. | Valid regulatory category. |
| T07 | `debt_to_income_ratio` | Strip `%`; map with an **explicit lookup (no pass-through)** to `dti_bin_fine` (`<20`, `20-<30`, `30-<36`, `36`..`49`, `50-60`, `>60`), `dti_bin_coarse` (`<20`, `20-<30`, `30-<36`, `36-40`, `41-45`, `46-49`, `50-60`, `>60`), `dti_point` (36–49 only). `NA`/`Exempt` → NULL bins + `dti_status`. `[Verified: B05 cell 31 — 21 distinct values, all map; strict isin asserts pass]`. | Preserves fine and coarse DTI structure. |
| T08 | `applicant_age`, `co_applicant_age` | `8888` ("Not applicable", per HMDA Filing Instructions note in the dictionary) → NULL with `<col>_status='na'`: applicant 80.98% in purchased loans (1,185,349 rows); co-applicant 91.30% (1,076,382 of 1,178,955, B05 cell 15). `co_applicant_age='9999'` ("No co-applicant") → NULL with `co_applicant_age_status='no_coapp'`. **`has_coapplicant` is NOT set here — see X05.** | Special codes are absence, not age brackets. |
| T09 | Repeated fields (`*_ethnicity_2..5`, `*_race_2..5`, `aus_2..5`, `denial_reason_2..4`) | `""` → NULL (structural absence). | Standardizes sparse repeated fields. |
| T10 | `denial_reason_1` | Keep code `10` as a valid category. Descriptive only; excluded from predictive models. | Outcome-revealing (leakage). |
| T11 | `applicant_age_above_62`, `co_applicant_age_above_62` | Keep `Yes`/`No`/`NA` as strings. | Avoid `NA`→`False`. |
| T12 | `tract_*`, `tract_to_msa_income_percentage`, `ffiec_msa_md_median_family_income` | **Per-field** (evidence: B05 cell 33; locked in D-G & D-H). Status values: `value`, `no_tract`, `no_geo`, `na_code`.<br>1. **`census_tract` is NULL (349,024 raw; 96,065 in S0):** `tract_population`, `tract_minority_population_percent`, `tract_owner_occupied_units`, `tract_one_to_four_family_homes`, `tract_median_age_of_housing_units`, `tract_to_msa_income_percentage` are **`0` in raw on all 349,024 rows** (not NULL) → set NULL, status `no_tract`.<br>2. `ffiec_msa_md_median_family_income`: positive values **preserved** on the 55,343 tract-NA rows. Value `0` occurs on exactly 293,681 rows (63,462 in S0), all tract-NA → NULL, status `no_geo`. That count equals the number of rows where both `county_code` and `census_tract` are NA `[Hypothesis: no geocode at all; valid-tract rows with code 99999 have 0 zeros]`.<br>3. `tract_median_age_of_housing_units`: `-1` (204 rows) → NULL, status `na_code`. Zeros on **valid tracts** are kept: 502,156 on populated tracts (+220 on zero-population tracts = 502,376) `[Hypothesis: newly developed tracts; not verified]`.<br>4. `tract_to_msa_income_percentage`: 57,954 zeros on valid populated tracts (+220 on zero-pop tracts = 58,174) are **kept as 0** with flag `flag_tract_income_zero`; run RQ3 with and without them `[Hypothesis: unavailable/suppressed tract income]`.<br>5. Zeros in minority %, owner-occupied units, 1–4 family homes on valid tracts (212 / 2,995 / 3,361) are legitimate. Validate `tract_minority_population_percent` ∈ [0,100] `[Verified: min 0, max 100]`. | Raw encodes "no tract" as 0, which would otherwise enter RQ3 as a 0% income tract. |

---

## 3. V rules: validity flags & diagnostics (`clean_all`, row count unchanged)

| ID | Condition | Flag | Raw (12.26M) | S0 (8.14M) |
|---|---|---|---|---|
| V01 | `loan_amount <= 0` | `flag_loan_amount_invalid` | 0 | 0 |
| V02 | `income <= 0` (USD thousands) | `flag_income_nonpositive` (+ `flag_income_zero`, `flag_income_negative`) | 165,254 (157,494 zero; 7,760 negative) | 91,261 (84,356 zero; 6,905 negative); **60.49% denied** (negative 95.51% = 6,595/6,905; zero 57.63% = 48,612/84,356); 55,207 denials (B05 cell 43). `loan_to_income` = NULL. |
| V03 | CLTV `<= 0` or `> 200` | `flag_cltv_range` | 5,323 | 4,026; 96.77% denied (3,896) |
| V04 | `interest_rate <= 0` or `> 25` | `flag_rate_range` (+ `flag_rate_le0`, `flag_rate_gt25`) | 83,443 (83,442 ≤ 0; 1 > 25). By action: originated 58,720; approved-not-accepted 2,426 (+1 > 25); purchased 21,737; preapproval-approved 559; **denied 0** | 60,717; **0 denied**. 95.34% of zero-rate loans are lien 2 (5.220% of reported lien-2 rates, B05 cell 27) `[Hypothesis: down-payment-assistance seconds]` |
| V05 | `loan_term` outside [1, 480] | `flag_term_range` | 2,893 | 18; 72.22% denied (13) |
| V06 | Non-NULL `census_tract` fails `^[0-9]{11}$` **after T05** | `flag_id_format` | 0 invalid (349,024 NULL = 349,023 `'NA'` + 1 `'na'`) | 0 |
| V07 | **Guarded:** `county_code.notna() & census_tract.notna() & ~flag_id_format & (county_code[:5] != census_tract[:5])` | `flag_geo_mismatch` | 0 true mismatches. Unguarded Pandas-vs-Spark divergence: 57,852 rows = 55,343 (county valid / tract NA) + 2,509 (county NA / tract valid); 293,681 rows are NA in both (B05 cell 29). | 0 |
| V08 | Real reason (1–9) with `action_taken` ∉ {3,7}, OR `action_taken` ∈ {3,7} with `10`/blank. `1111` = Exempt. | `flag_denial_inconsistent` | 0 (from B04) | 0 |
| V09 | **Diagnostic profile only** (`profile_cltv_discrepancy`), no exclusion rule. First liens (S0, 5,033,106 valid): median \|CLTV−LTV\| 0.755 pp, p95 4.710 pp; 59.03% fall inside ±$5,000 property-rounding bounds and 8.80% (442,881) lie > 1 pp below lower bound (B05 cell 37). Below-bound share by loan type: FHA 19.75%, VA 14.97%, USDA 8.91%, Conventional 4.74% (B05 cell 39). Subordinate liens: median 49.276 pp. | `profile_cltv_discrepancy` | — | Candidate causes, all `[Hypothesis]`: financed FHA UFMIP / VA funding fee in `loan_amount`; midpoint rounding of `property_value`. |
| V10 | Duplicates across all 99 raw columns | `dup_group_size`, `flag_dup_extra` | 20,229 clusters; 26,755 extra copies (0.22%). First = smallest `row_id` (MD5, `chr(31)`) | Stage B-3 |

---

## 4. X rules: feature engineering (`clean_all`)

| ID | Feature | Definition |
|---|---|---|
| X01 | `is_denied` | `1` if `action_taken == '3'`; `0` if `action_taken` ∈ `('1','2')`; else NULL. |
| X02 | `in_decision_sample` | `action_taken` ∈ `('1','2','3')` (8,661,779). |
| X03 | `race_group` | From `derived_race`; all 9 groups kept. Primary: White, Black or African American, Asian. Others reported separately. Free Form Text Only (n = 2,184 in F01; 2,098 in S0) has unstable rates. |
| X04 | `ethnicity_group` | From `derived_ethnicity`. |
| X05 | `has_coapplicant`, `flag_coapp_discordant` | Each of `co_applicant_age`, `_sex`, `_race_1`, `_ethnicity_1` is mapped with **explicit valid sets** to `Present` / `No_Coapp` (`9999`,`5`,`8`,`5`) / `NA` (`8888`,`4`,`7`,`4`; **blank/NULL on race_1 and ethnicity_1 also = NA**) / `Invalid` (0 rows `[Verified: B05 cell 19]`). Precedence **Present > No_Coapp > NA**: `1` if any field is Present; else `0` if any No_Coapp; else NULL. `flag_coapp_discordant` = the four states are not all equal. Raw: 79,088 discordant (0.65%; 4-field concordance 99.35%), 1,134,611 all-NA (9.26%; 1,042,595 in purchased loans). S0: 18,230 discordant (0.22%), 3,625 all-NA (0.045%). `age = 8888` with three No_Coapp: 14,099 raw (1,771 S0). Blank `race_1` 1,014 and `ethnicity_1` 1,463 rows `[Hypothesis: unclassified or free-form text co-applicant]`. After T01 these are NULL, so the rule tests NULL explicitly in both engines. |
| X06 | `loan_to_income` | `loan_amount / (income * 1000)`; NULL if `income` is NULL or ≤ 0. |
| X07 | `ltv_calc` | `loan_amount / property_value * 100`; NULL if `property_value` is NULL or ≤ 0. |
| X08 | `log_loan_amount`, `log_income` | `log1p`; NULL if the input is NULL or ≤ 0. |
| X09 | `n_exempt_28`, `is_exempt_filer`, `is_partial_exempt`, `flag_dr1_is_1111` | `n_exempt_28` counts the **28 documented fields** (14 literal `Exempt` numeric/DTI columns + 14 dictionary-documented `1111` categorical columns; range 0–28, asserted in B05 cell 11). `is_exempt_filer = (n_exempt_28 == 28)`: 276,755 raw (2.26%), 241,108 S0. `is_partial_exempt = (1 ≤ n_exempt_28 ≤ 27)`: 23,164 raw (0.19%), **15,292 S0** (B05 cell 13: 7,880,264 + 241,108 + 15,292 = 8,136,664). `flag_dr1_is_1111`: 247,789 raw; 215,992 in the full-exempt group (78.04% of 276,755), 8,912 partial, 22,885 with n = 0. |
| X10 | `lender_n_apps`, `lender_size_bucket` | Computed on the full 12.26M before any filter. |
| X11 | `fin_complete` | `dti_bin_fine`, `combined_loan_to_value_ratio`, `income`, `loan_amount` all non-NULL. Retention in S0 by race: 80.57–94.28% (B05 cell 41). |

---

## 5. F rules: row filters (`analytic.parquet`) — NULL-safe positive membership

| ID | Rule | Status |
|---|---|---|
| F01 | `action_taken.isin(['1','2','3'])` | 8,661,779 rows. |
| F02 | `business_or_commercial_purpose.isin(['2','1111'])` | **Locked (D-A).** Domain verified as `{'1','2','1111'}` (B05 cell 21). Excludes code 1. Keeps 250,691 code-1111 rows in S0 `[Hypothesis: consumer loans]`. |
| F03 | `reverse_mortgage.isin(['2','1111'])` | **Locked (D-A).** Domain verified as `{'1','2','1111'}` (B05 cell 21). Excludes code 1. Keeps 250,889 code-1111 rows in S0 `[Hypothesis: non-reverse loans]`. |

**Sequential waterfall `[Verified: B05 cell 21]`:** Raw 12,259,199 → F01 8,661,779 (−3,597,420) → F02 8,170,177 (−491,602) → F03 **S0 8,136,664 (−33,513)**. Memo (not sequential): F03 alone on F01 = 33,569; overlap = 56; combined = 525,115 (6.06% of F01; 4.28% of raw). S0 = 93.94% of F01, 66.37% of raw. S0 denial rate 24.62% (2,003,276 / 8,136,664).

---

## 6. Sample definitions per step

| Stage | Sample | Description |
|---|---|---|
| Step 1 RQ1 raw gap | S0 | 8,136,664 rows. |
| Step 2 RQ1 product | S0 | + `loan_type`, `loan_purpose`, `lien_status`, `occupancy_type`. |
| Step 3 RQ2 financial | S0 ∩ `fin_complete` | **Steps 1–2 recomputed on this subsample.** Denial rates fall 1.09–4.29 pp across groups (selection effect, B05 cell 41). |
| Step 4 RQ3 geo/lender | Step-3 sample ∩ valid `census_tract` (Locked in D-I) | **Steps 1–3 recomputed on this subsample.** Pre-RQ3 evidence (B05 cell 35): 96,065 S0 rows (1.18%) lack a tract; 76.53% of them are denied vs 24.00% on valid tracts. Missing-tract share is highest for AIAN (2.83%, 86.47% denied) and Black (2.14%, 87.14% denied). |
| Step 5 RQ4 | S1–S6 | See §7. |

---

## 7. Robustness samples (RQ4)

| Code | Definition | Purpose |
|---|---|---|
| S0 | F01+F02+F03: 8,136,664 rows, denial 24.62% (2,003,276 denied) | Benchmark. |
| S1 | S0 without `flag_dup_extra` | Duplicates. |
| S2 | S0 with `fin_complete` | Financial controls. |
| S3 | S0 with missing-indicator variables | Missingness. |
| S4 | S0 winsorized at p1/p99 (thresholds computed on S0 once) | Outliers. |
| S5 | **Two variants. V04 is never excluded (Locked in D-B & D-C).** `S5_all` (exclude V01, V02, V03, V05; keep V04): **8,041,498 rows, denial 24.18%** (1,944,293 denied). `S5_keep_v02` (exclude V01, V03, V05; keep V02 & V04): **8,132,620 rows, denial 24.58%** (1,999,367 denied) `[Verified: B05 cell 43]`. | `interest_rate` is NULL on every denied application (0 denied among V04 rows), so excluding V04 removes 60,717 approved loans and artificially inflates the denial rate by **+0.18 pp** (`24.18%` → `24.36%` on 7,981,245 rows). Conversely, removing V02 drops 55,207 denials and compresses the denial rate by **−0.40 pp** (`24.58%` → `24.18%`). |
| S6 | S0 restricted to principal-residence, home-purchase, conventional, first-lien loans | Homogeneous sample. |

---

## 8. Dual-engine equivalence & storage (planned for B06–B08)

1. `clean_all.parquet`: unpartitioned, target 12,259,199 rows, keeps `bucket` (25/50/100% benchmarks). `analytic.parquet`: single file, target 8,136,664 rows. Sizes are logged when created (raw input: 432.33 MB, B04 cell 4).
2. DuckDB = audit/profiling engine; production pipeline in Pandas (B06) and PySpark (B07); equivalence audited in B08.
3. Standards: group-by with NULL keys (`dropna=False` in Pandas); trim before cast; exact equality for integer counts and flag tallies; tolerance 1e-9 for floats.

---

## 9. Record of decisions (see `decisions.md`)

* **D-A (Agreed):** F02/F03 via `.isin(['2','1111'])`; −525,115 rows; S0 = 8,136,664; retains 250,691 (F02) and 250,889 (F03) code-1111 rows in S0.
* **D-B (Agreed):** Income ≤ 0 retained, flagged V02, `loan_to_income` NULL; strongly outcome-related (60.49% denied); evaluated via dual S5 (`S5_all` 24.18% vs. `S5_keep_v02` 24.58%).
* **D-C (Agreed):** Zero rate retained, flagged V04; **not** excluded from gap models or S5 (0 denied; prevents +0.18 pp artificial inflation).
* **D-D (Agreed):** 9 race groups; X05 4-state precedence with discordance flag (`79,088` raw / `18,230` S0 discordant; `1,134,611` raw / `3,625` S0 all-NA).
* **D-E / D-F (Agreed):** Storage and dual-engine parity targets for B06–B08.
* **D-G (Agreed):** Per-field T12, zero housing ages kept on valid tracts, FFIEC kept on 55,343 tract-NA rows, `non_msa` status, V09 diagnostic profile, X09 strictly on 28 documented fields.
* **D-H (Agreed):** Tract-NA zeros (349,024 rows across 6 fields) → NULL (`no_tract`) and FFIEC zero (293,681 rows) → NULL (`no_geo`); 58,174 valid-tract zeros in `tract_to_msa_income_percentage` kept as `0` with `flag_tract_income_zero`.
* **D-I (Agreed):** RQ3 sample requires a valid `census_tract` (excludes 96,065 tract-NA S0 rows with 76.53% denial rate); recompute Steps 1–3 on the valid-tract subsample to isolate selection bias.

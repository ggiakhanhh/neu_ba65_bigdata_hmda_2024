# Data Cleaning Rulebook: HMDA 2024 Public LAR

**Project:** Decomposing Racial Gaps in Mortgage Denial Rates (Group 3, Big Data Analysis)
**Companion document:** `data_quality_assessment_plan.md`

Items marked **[decide after profiling]** are proposals pending evidence from the real data.

---

## 1. Principles

1. Rules fall into four types:
   - **T** (column transforms, row count unchanged)
   - **V** (validity flags, row count unchanged)
   - **X** (feature engineering, row count unchanged)
   - **F** (row filters; the only type that reduces rows, each logged in the waterfall)
2. Unusual values are **flagged, not deleted**.
3. **No imputation and no replacing missing values with zero.** Missing values stay NULL with a status column.
4. Every rule records the **number of rows affected**.
5. Every rule is implemented identically in Pandas and PySpark.

Output layers: `raw` (all strings, unmodified) to `clean_all` (T, V, X rules; same rows) to `analytic` (F rules applied).

---

## 2. T rules: column transforms (`clean_all`)

| ID | Columns | Rule | Reason |
|---|---|---|---|
| T01 | All string columns | Trim leading/trailing whitespace; empty string becomes NULL (already applied at ingest if `na_values=[""]`) | Avoid `"36 "` vs `"36"` mismatches and engine differences |
| T02 | Alphanumeric numeric columns: `income`, `property_value`, `combined_loan_to_value_ratio`, `interest_rate`, `rate_spread`, `total_loan_costs`, `total_points_and_fees`, `origination_charges`, `discount_points`, `lender_credits`, `loan_term`, `prepayment_penalty_term`, `intro_rate_period`, `multifamily_affordable_units` | `"NA"` and `"Exempt"` become NULL. Create `<col>_status` with values `value`, `na`, `exempt`, `blank` | These columns can contain text; the type of missingness must be preserved |
| T03 | Numeric columns: the T02 columns plus `loan_amount`, `activity_year`, `tract_*`, `ffiec_msa_md_median_family_income`, `tract_to_msa_income_percentage` | Explicit cast (Int64 or Float64). Audit: `NULL after cast = empty + NA/Exempt + unparseable (expected 0)` | Detect silent coercion errors |
| T04 | Categorical code columns (`loan_type`, `loan_purpose`, `action_taken`, `occupancy_type`, `*_ethnicity_*`, `*_race_*`, `*_sex*`, `aus_*`, `denial_reason_*`, ...) | Keep as **string**; do not cast to numbers. Codes such as `31`, `32`, `71`, `72` are labels, not quantities | Codes are categories |
| T05 | `lei`, `state_code`, `county_code`, `census_tract`, `derived_msa_md` | Keep as string. Check length only (20 / 2 / 5 / 11 / 5). **Do not pad zeros automatically**; violations are flagged (V06) | Leading zeros; padding could create false identifiers |
| T06 | Categorical columns where `1111` is a documented "Exempt" code: `reverse_mortgage`, `open_end_line_of_credit`, `business_or_commercial_purpose`, `manufactured_home_*`, `submission_of_application`, `initially_payable_to_institution`, `*_credit_score_type`, `negative_amortization`, `interest_only_payment`, `balloon_payment`, `other_nonamortizing_features`, `aus_1` | **Keep `1111` as the category "Exempt"**, do not convert to NULL. Apply only to the listed columns | It is a valid value of a categorical variable. Replacing `1111` across the whole table would corrupt other columns |
| T07 | `debt_to_income_ratio` | Remove `%`, standardize, and split into `dti_bin_fine` (published bins: `<20`, `20-<30`, `30-<36`, `36`..`49`, `50-60`, `>60`), `dti_bin_coarse` (`<20`, `20-<30`, `30-<36`, `36-40`, `41-45`, `46-49`, `50-60`, `>60`) and `dti_point` (numeric only when value is 36 to 49, otherwise NULL). `NA`/`Exempt` become NULL bins with `dti_status` | Mixed numbers and ranges; the dictionary shows `36%` but real data may show `36` (verify with `value_counts`) |
| T08 | `applicant_age`, `co_applicant_age` | `8888` becomes NULL with `age_status = na`. For co-applicant, `9999` (no co-applicant, to be verified) becomes NULL with `has_coapplicant = 0` | Special codes are not ages |
| T09 | Repeated fields (`*_ethnicity_2..5`, `*_race_2..5`, `aus_2..5`, `denial_reason_2..4`) | Empty becomes NULL; treated as structural missingness, not an error | Only populated when extra options are reported |
| T10 | `denial_reason_1` | Keep code `10` ("not applicable") as a category. Used for description only, never as a predictor | Outcome-revealing variable |
| T11 | `applicant_age_above_62`, `co_applicant_age_above_62` | Keep `Yes`/`No`/`NA` as categories; do not convert to boolean | Prevents `NA` becoming `False` |
| T12 | `tract_*` fields | Missing stays NULL. Check `tract_minority_population_percent` is in [0, 100] | Out-of-range values are flagged, not fixed |

---

## 3. V rules: validity flags (flag only, do not delete) **[decide thresholds after profiling]**

| ID | Condition | Flag column |
|---|---|---|
| V01 | `loan_amount <= 0` | `flag_loan_amount_invalid` |
| V02 | `income <= 0` (income is in **thousands of USD**) | `flag_income_nonpositive` |
| V03 | CLTV `<= 0` or `> 200` | `flag_cltv_range` |
| V04 | `interest_rate <= 0` or `> 25` | `flag_rate_range` |
| V05 | `loan_term` outside 1 to 480 months | `flag_term_range` |
| V06 | Wrong length: `lei` not 20, `census_tract` not 11, `county_code` not 5 | `flag_id_format` |
| V07 | `county_code[:2]` differs from `census_tract[:2]` | `flag_geo_mismatch` |
| V08 | `denial_reason_1` is a real reason but `action_taken` is not 3 (or the reverse) | `flag_denial_inconsistent` |
| V09 | Large gap between reported CLTV and `loan_amount / property_value x 100` (threshold chosen after viewing the distribution) | `flag_cltv_mismatch` |
| V10 | Row identical to an earlier row on all 99 original columns | `dup_group_size`, `flag_dup_extra` (second and later copies; the first is the one with the smallest `row_id`) |

By default the original values are kept and only flagged. Setting flagged values to NULL happens only in robustness variants. Genuine extremes (jumbo loans, high incomes) are never altered.

---

## 4. X rules: engineered features

| ID | Feature | Definition |
|---|---|---|
| X01 | `is_denied` | 1 if `action_taken = 3`; 0 if `action_taken` is 1 or 2; NULL otherwise |
| X02 | `in_decision_sample` | True if `action_taken` is in {1, 2, 3} (the denominator in the proposal) |
| X03 | `race_group` | From `derived_race`, nine groups kept as published. Main gap groups: White, Black or African American, Asian. Other groups are reported separately, never dropped **[decide after group sizes]** |
| X04 | `ethnicity_group` | From `derived_ethnicity`. Optionally `race_ethnicity_group` with Hispanic taking priority |
| X05 | `has_coapplicant` | Derived from `co_applicant_age`, `co_applicant_sex`, `co_applicant_race_1` (check they agree; the "no co-applicant" codes must be verified in the dictionary) |
| X06 | `loan_to_income` | `loan_amount / (income x 1000)`; NULL if income is NULL or not positive |
| X07 | `ltv_calc` | `loan_amount / property_value x 100` (`property_value` is rounded, so small differences from reported CLTV are expected) |
| X08 | `log_loan_amount`, `log_income` | `log1p` transforms for plots and models |
| X09 | `n_exempt_fields` | Count of Exempt/`1111` values in the row |
| X10 | `lender_n_apps`, `lender_size_bucket` | Computed on the **full** raw data before any filter, so both engines agree |
| X11 | `fin_complete` | True if DTI bin, CLTV, income and loan amount are all non-NULL |

---

## 5. F rules: row filters (`analytic.parquet`)

| ID | Keep rows where | Note |
|---|---|---|
| F01 | `action_taken` in {1, 2, 3} | Required by the proposal. Removes 4 (withdrawn), 5 (incomplete), 6 (purchased), 7 and 8 (preapproval) |
| F02 | `business_or_commercial_purpose != 1` (keep 2 and 1111) | **Proposal, to confirm.** Business loans are not standard consumer mortgages |
| F03 | `reverse_mortgage != 1` (keep 2 and 1111) | **Proposal, to confirm.** Structurally different product |

Not filtered: `occupancy_type`, `lien_status`, `open_end_line_of_credit` (they are controls in the proposal), race groups, and rows with missing values. "Race Not Available" stays in the sample but is not part of the main gap comparison.

For every F rule, log in the waterfall: rows kept, rows removed, and the denial rate of each race group before and after.

---

## 6. Sample definitions per step of the analytical framework

| Framework step | Sample |
|---|---|
| 1. Raw gap | `analytic` |
| 2. Product controls | `analytic` |
| 3. Financial controls | `analytic` where `fin_complete = True`. **Recompute the gaps of steps 1 and 2 on this same subsample**, otherwise changes in the gap may come from the sample change rather than from the added controls |
| 4. Geography and lender | Same subsample as step 3 |
| 5. Robustness | Variants below |

---

## 7. Robustness variants (RQ4)

| Code | Variant |
|---|---|
| S0 | Main sample (F01 to F03) |
| S1 | S0 without duplicate extras (`flag_dup_extra`) |
| S2 | S0 keeping only rows with no NA/Exempt in DTI, CLTV, income |
| S3 | S0 keeping missing rows, using missing-indicator variables instead of dropping |
| S4 | S0 with income and loan amount winsorized at p1/p99 |
| S5 | S0 excluding rows flagged by V01 to V05 |
| S6 | S0 restricted to principal-residence home-purchase loans (the "standard" fair-lending sample) |

---

## 8. Rules to keep Pandas and PySpark equivalent

1. `groupby` with NULL keys: Pandas needs `dropna=False`; Spark keeps NULL groups.
2. Percentiles for winsorizing: compute once exactly, store as constants, apply in both engines.
3. Casting: trim first, then cast; compare NULL counts after casting in both engines.
4. Compare integers exactly; floats with a tolerance (for example 1e-9). Round only for display.
5. Never rely on row order; sort or compare by key (`row_id`).
6. Aggregations that need global information (duplicates, lender sizes, percentiles) are computed on the full data first, then applied; do not compute them per chunk and combine.
7. For rates, sum numerators and denominators across chunks and divide at the end; never average rates.
8. Each rule in the ledger records how it is implemented in Pandas and in Spark.

---

## 9. Rule ledger template

| ID | Description | Reason | Rows affected | % | Pandas implementation | Spark implementation | Date / owner |
|---|---|---|---|---|---|---|---|
| T02 | `income`: NA/Exempt to NULL | Text codes in a numeric column | (fill) | (fill) | `s.str.strip().replace({"NA": pd.NA, "Exempt": pd.NA})` then `pd.to_numeric` | `when(col.isin("NA","Exempt"), None)` then `cast("double")` | |

---

## 10. Open decisions to confirm

- Final scope: confirm F02 and F03, and whether to additionally restrict to a standard fair-lending sample (S6) for the main results.
- Race group handling: which groups join the main gap comparison after seeing sample sizes.
- Thresholds for V02 to V05 and V09 after viewing distributions.
- Whether to run the out-of-time prediction with 2025 data (ask the instructor; the brief fixes the reporting year at 2024).
- Verify in the official source: meaning of `8888`/`9999` for age fields, "no co-applicant" codes, and the value used for areas outside an MSA.

# EDA Plan — Task B14 (Descriptive & Diagnostic Analysis of HMDA 2024)

**Project:** Decomposing Racial Gaps in Mortgage Denial Rates: A Large-Scale Analysis of the 2024 U.S. HMDA Market
**Folder:** `B14 - EDA/` (`input/`, `output/`, `documents/eda_plan.md`)
**Notebook:** `B14 - <date>.ipynb` (new version = new file, never overwrite; Convention 2.4)
**Status:** APPROVED (Decisions D-J … D-S confirmed by Human on 2026-11-09)
**Companion documents:** `data_cleaning_rules.md` (v2.3), `decisions.md` (D-A … D-S), `Coding and documenting conventions.md`, Proposal, Assignment PDF
**Numbers in this plan** are cited only as "as of run <date>, <notebook/cell>" (Convention 4.3). The notebook must recompute every number.

---

## 1. Task restatement, scope and assumptions

### 1.1 Task (2 sentences)
B14 profiles and explores the cleaned data produced by B06 (`B06_analytic.parquet` = sample S0, and `B06_clean_all.parquet` for selection checks) to (a) answer the descriptive/diagnostic part of RQ1–RQ4 and the Assignment Part 3 (A–E), and (b) produce the evidence that fixes the design of the sequential decomposition (which controls, which samples, which reference groups). EDA is **descriptive and diagnostic, not causal**; no remaining gap is interpreted as discrimination.

### 1.2 In scope / out of scope
| In scope | Out of scope (later tasks) |
|---|---|
| Univariate, bivariate, cross-tab, correlation, missingness and selection diagnostics on S0 | Final sequential models / regressions (Step 3–4 of the Proposal) |
| Raw gap, product-mix effect, financial-profile effect (**exploratory** direct standardization only) | Logistic Regression / Random Forest extension |
| Geography & lender heterogeneity (descriptive) | PySpark re-implementation (B07/B15) — but EDA defines the tables that must be reproduced |
| Robustness **preview** across samples and data-handling choices | Final RQ4 robustness suite and report text |
| Figures, tables, interpretation cells | Technical report writing |

### 1.3 Assumptions (labelled per Convention 4.4)
| # | Assumption | Label |
|---|---|---|
| A1 | `B06_analytic.parquet` equals S0 (F01–F03) and passed all golden checks vs B05 (48/48, as of run 2026-10-31, B06 cell 27). | [Verified: B06] |
| A2 | Denial rate = `is_denied` mean on S0; denominator is `action_taken IN (1,2,3)` (all S0 rows have non-NULL `is_denied`). | [Verified: Proposal §3, rule X01] |
| A3 | `derived_race` has 9 categories (incl. `Joint`, `Race Not Available`, `Free Form Text Only`); `derived_ethnicity` and `derived_sex` are separate CFPB-derived fields. | [Verified: Data Dictionary] |
| A4 | Hispanic ethnicity is **not** a `derived_race` value; a combined race-ethnicity variable must be built if wanted. | [Verified: Data Dictionary] |
| A5 | Public HMDA has no credit score value, assets, AUS result, or application dates; `applicant_credit_score_type` and `aus_1..5` give only model / system **type**. | [Verified: Data Dictionary + Proposal §3] |
| A6 | `interest_rate`, `rate_spread`, `total_loan_costs`, `origination_charges`, `discount_points`, `lender_credits`, `purchaser_type`, `hoepa_status` and loan-feature fields are **post-decision / outcome-dependent**: missing (or not applicable) for denied applications. B05 showed 0 reported interest rates for `action_taken = 3`. | [Verified: B05 cell 25] for `interest_rate`; [Hypothesis] for the others → tested in E-A3 |
| A7 | DTI is reported in bins plus integer points 36–49; CLTV and income are numeric; `income` is in thousands of USD. | [Verified: B05 cell 31, rules T07/X06] |
| A8 | Missingness of DTI / income / CLTV / property_value is **informative** (differs by outcome and race; fin_complete retention differs by race, as of run 2026-10-31, B05 cell 39 / B06 cell 29). | [Hypothesis] → tested in E-B4 |
| A9 | Chunking is not needed for EDA: S0 with ~40 selected columns (category dtypes) fits in memory; heavy computations use a seeded stratified sample. | [Hypothesis] → check peak memory in config cell |
| A10 | Standard FFIEC census-tract income levels (low < 50%, moderate 50–<80%, middle 80–<120%, upper ≥ 120% of MSA median) apply to `tract_to_msa_income_percentage`. | [Hypothesis: confirm against FFIEC documentation] |

---

## 2. Decisions needed from Human (proposed defaults)

Proposed IDs continue after D-I; renumber if `decisions.md` already has newer rows.

| ID | Decision | Proposed default | Why it matters | Status |
|---|---|---|---|---|
| D-J | **Reference group** for gaps | `White` (derived_race); gaps reported in percentage points (pp), ratio and odds ratio | All gap numbers depend on it | Agreed |
| D-K | **Race-ethnicity coding** | Primary = `derived_race` (per Proposal). Supplementary = 5-group `race_ethnicity` (Non-Hispanic White / Black / Asian, Hispanic any race, Other-or-Not-available) built in B14 | Hispanic applicants are spread across race categories; ignoring ethnicity hides a major group | Agreed |
| D-L | **Treatment of `Race Not Available` and `Free Form Text Only`** in EDA | Always shown as separate rows; never merged into White or minority; excluded from "headline gap" tables but kept in sample-size accounting | Large share of S0 with different denial profile (as of run 2026-10-31, B05 cell 39) | Agreed |
| D-M | **Minimum cell size** for any rate, gap, state, MSA or lender cell | `N_MIN_APPS = 1,000` and `N_MIN_DENIED = 100`; smaller cells are shown greyed / suppressed in plots and flagged `low_n` in tables | Avoids noise-driven rankings | Agreed |
| D-N | **Primary analysis sample for EDA** | Show S0 as baseline everywhere; show `fin_complete` and RQ3 sample (D-I) side by side in selection/gap tables; all other sections use S0 with missing categories made explicit. `clean_all` queried strictly for selection audits | Keeps selection effects visible instead of hidden; avoids conflating non-consumer loans | Agreed |
| D-O | **Lender anonymity** | Lenders appear only as hashed/ranked IDs (`L001…`), never by LEI or name in figures and report | Assignment §5: avoid unsupported claims about individual institutions | Agreed |
| D-P | **Exploratory decomposition preview** (Kitagawa / direct standardization of the Black–White gap by product mix and by financial strata) | Include in B14 as *exploratory*, clearly labelled; formal sequential models stay in the next task. Code accompanied by clear markdown explanations | Gives a first answer to the Main RQ and tests whether the planned stages are informative | Agreed |
| D-Q | **Inference style** | Wilson CIs for rates; log-odds-ratio CIs for gaps; headline gaps also get a **lender-cluster bootstrap** (resample lenders on pre-aggregated lender×race counts, B = 1,000, seed 42). No p-value tables (N is in the millions). Code accompanied by clear markdown explanations | Naive CIs ignore within-lender correlation | Agreed |
| D-R | **Input location** | Notebook reads B06 parquet from a single `B06_DIR` path declared once in the config cell (fallback to `input/`). Parquet files are not copied (≈1.3 GB) | Convention 2.2–2.3 | Agreed |
| D-S | **One notebook or several** | One notebook with Parts A–F; split into B14a–B14c only if Restart & Run All exceeds ~30 min | Convention 3.9 | Agreed |

---

## 3. Notebook layout and conventions applied

- Every code cell has an md cell above with **Input / Process / Output**; code ≤ ~40 lines; `# Step n:` comments; English only (Conventions 3.2–3.6).
- Config cell once: paths (`Path`), constants (`SEED = 42`, `N_MIN_APPS`, `N_MIN_DENIED`, `SAMPLE_N`, `B06_DIR`), reference group, palette, column groups. No paths elsewhere.
- Every artifact goes to `output/` with prefix `B14_` and is logged with path, size, shape (`save_and_log`, `save_fig_and_log`). Figures in `output/figures/B14_fig_<nn>_<slug>.png` (dpi 150).
- Each major figure: title, axis labels, units, n shown, **interpretation md cell** (4 questions in Section 11). Interpretation text is written **after** the first full run and cites numbers as "as of run <date>, cell <n>".
- Each important computation has a quick check (rows add up, rates within 0–100, no category lost to NULL, groupby with `dropna=False`).
- Any non-trivial library or technique (Wilson interval, Kitagawa decomposition, bootstrap, Cramér's V, mutual information, funnel plot) gets an md explanation "what it is and why we use it".
- Any rule/decision change found during EDA → proposed row for `decisions.md` / `data_cleaning_rules.md`, never silently coded (Convention 5.3, 6).

### Data loading pattern
1. Read only needed columns from `B06_analytic.parquet` with `pyarrow`; convert low-cardinality strings to `category`.
2. `df_s0` = analytic file (assert row count equals the B06 waterfall CSV, not a typed number).
3. `df_all_min` = a few columns from `B06_clean_all.parquet` (`row_id`, `action_taken`, race, status columns, `in_s0`, flags) for selection checks that need rows outside S0 (e.g., what F01 drops).
4. `df_samp` = seeded stratified sample of S0 (stratified by race × outcome, `SAMPLE_N ≈ 500k`) used only for scatter/hexbin, correlation, mutual information, VIF. All tables of counts and rates use the **full** S0.

### Variable roles registry (first deliverable, reused by later tasks)
`output/B14_variable_roles.csv`: one row per used column with `role ∈ {outcome, group, product_control, financial_control, geo_control, lender_control, diagnostic_only, post_decision_exclude}`, dictionary type, coverage in S0, availability by outcome (E-A3), and a rationale. This is the single place where leakage decisions are documented.

---

## 4. Part A — Data profile of the analytic frame

| ID | Step | Process | Output / check |
|---|---|---|---|
| A1 | Frame description | Rows, columns, dtypes, memory, column families (dictionary "axis"). Confirm S0 equals B06 numbers (golden values read from B06 CSVs). | `B14_frame_profile.csv`; asserts |
| A2 | Outcome overview | Counts and share by `action_taken` (1, 2, 3) and overall denial rate; by `in_s5_all`, `in_s5_keep_v02`, `fin_complete`; reconcile with B06 waterfall | `B14_outcome_overview.csv`; fig: stacked bar by action |
| A3 | **Availability by outcome** (leakage audit) | For every candidate column: non-missing share among denied vs not-denied (`is_denied` 1 vs 0). Flag columns with availability gap > 50 pp or 100% missing for denied | `B14_availability_by_outcome.csv` → feeds `post_decision_exclude` roles |
| A4 | Coverage matrix | Non-missing / "Exempt" / "NA" share per key variable overall and by race (uses `*_status` columns from B06) | `B14_coverage_by_race.csv`; heatmap |
| A5 | Population composition | Share of S0 by race, ethnicity, sex, age bracket, co-applicant presence (`has_coapplicant`), `Joint` race, application channel (`submission_of_application`) | `B14_composition.csv`; bar charts |

Notes: A3 uses the same status columns defined by T02/T05/T12; exempt filers (`is_exempt_filer`) are tabulated as a separate row because they have systematic `1111`/`Exempt` patterns.

---

## 5. Part B — Univariate distributions (Assignment 3.3 A)

| ID | Variables | Statistics (chosen per type) | Figures |
|---|---|---|---|
| B1 | `loan_amount`, `property_value`, `income`, `loan_to_income` | n, missing, mean, SD, p1/p5/p25/p50/p75/p95/p99, skewness; log scale views; S4 winsor thresholds from `B06_s4_winsor_thresholds.json` shown as vertical lines (display only, no data change) | Histogram (log x) and boxplot, overall and by outcome |
| B2 | `combined_loan_to_value_ratio`, `ltv_calc`, `profile_cltv_discrepancy` | Same; heaping at 80 / 95 / 97 / 100; by `lien_status` (first vs subordinate behave differently per B05 cell 37) | Histogram by lien; discrepancy plot |
| B3 | `debt_to_income_ratio` (`dti_bin_fine`, `dti_bin_coarse`, `dti_point`) | Treated as **ordinal bins**, not continuous; counts and shares per bin; share NA/Exempt | Bar chart in bin order |
| B4 | `interest_rate`, `rate_spread`, `loan_term`, `total_loan_costs` (**originated loans only**, `action_taken = 1`) | Same stats; explicit note that these exist only after origination (selection) | Histograms; boxplots by `loan_type` |
| B5 | Categorical: `loan_type`, `loan_purpose`, `lien_status`, `occupancy_type`, `construction_method`, `total_units`, `derived_dwelling_category`, `conforming_loan_limit`, `open_end_line_of_credit`, `preapproval`, `submission_of_application`, `aus_1`, `applicant_credit_score_type`, `lender_size_bucket` | Counts, shares, denial rate per level (table-first, chart only where informative) | Horizontal bars with denial-rate overlay |
| B6 | Outliers vs errors | Join V-flags (V01–V05, V09) to distributions: which extremes are rule violations, which are genuine large loans/incomes. Report denial rate of flagged rows (V02, V03 are > 50% denied per B05 cell 43) | `B14_outlier_flag_profile.csv` |
| B7 | Duplicates | `flag_dup_extra` / `dup_group_size`: share of S0, denial rate of extras vs originals, race mix of duplicates | `B14_duplicate_profile.csv` |

Output tables: `B14_numeric_summary.csv`, `B14_categorical_summary.csv`.

---

## 6. Part C — RQ1: raw gap and product mix

| ID | Analysis | Method | Output |
|---|---|---|---|
| C1 | **Raw denial gap by race** (all 9 groups) | Denial rate, Wilson CI, gap vs reference (pp), risk ratio, odds ratio; low-N flags (D-M); lender-cluster bootstrap CI for headline groups (D-Q) | `B14_rq1_raw_gap.csv`; forest-style plot |
| C2 | Gap by ethnicity, sex, age bracket, co-applicant presence, and 5-group `race_ethnicity` (D-K) | Same table template | `B14_rq1_gap_other_dims.csv` |
| C3 | **Product mix by race** | Row-normalised shares of race over `loan_type`, `loan_purpose`, `lien_status`, `occupancy_type`, `derived_dwelling_category`, loan-amount buckets, `conforming_loan_limit` | `B14_rq1_mix_by_race.csv`; heatmap |
| C4 | **Denial rate by product** and **stratified gaps** | For each product stratum (e.g., loan_purpose × loan_type), gap vs reference with CI; check whether the sign or size of the gap changes across strata (Simpson-type check) | `B14_rq1_stratified_gap.csv`; small-multiples plot |
| C5 | **Mix vs rate decomposition** (exploratory, D-P) | Kitagawa decomposition of (group − reference) denial gap into a *composition* part (different product mix) and a *rate* part (different denial rate within same product); product strata = loan_type × loan_purpose × lien_status × occupancy_type; strata with `low_n` pooled to "other" and counted | `B14_rq1_kitagawa.csv`; waterfall-style bar |
| C6 | `Race Not Available` profile (D-L) | Share and denial rate by lender, channel (`submission_of_application`), loan product; lender-level concentration of "Not Available" | `B14_rq1_race_na_profile.csv` |

Method note (md cell): Kitagawa decomposition splits a difference between two group-level rates into the part due to different population composition and the part due to different rates within each stratum; it is descriptive arithmetic, not a causal model.

---

## 7. Part D — RQ2: financial profile

| ID | Analysis | Method | Output |
|---|---|---|---|
| D1 | **Financial profile by race** | Medians / quartiles of `income`, `loan_amount`, `loan_to_income`, `property_value`; distribution of `dti_bin_coarse` and CLTV bins by race | `B14_rq2_profile_by_race.csv`; ridge/box plots |
| D2 | **Denial vs financial variables** | Denial rate curves by DTI (fine bins incl. points 36–49), CLTV bins (include heaping thresholds), income deciles (computed on S0), loan-to-income bins; with Wilson CI | `B14_rq2_denial_curves.csv`; line plots |
| D3 | **Joint surface** | Heatmap of denial rate over DTI bin × CLTV bin (cells above D-M only), separately for first lien purchase and refinance | `B14_rq2_dti_cltv_heatmap.csv` |
| D4 | **Gap within financial strata** | Gap vs reference within DTI × CLTV × income-decile strata; stratified Kitagawa (composition vs rate), same template as C5 | `B14_rq2_stratified_gap.csv` |
| D5 | **Common support / overlap** | For each minority group vs reference: share of group applicants located in strata where the reference group has ≥ `N_MIN_APPS`; flag regions of financial space without comparable applicants | `B14_rq2_common_support.csv` |
| D6 | **Missing financial data as selection (A8)** | For income, DTI, CLTV, property_value: missing share by race and by outcome; denial rate of rows with missing vs present; retention S0 → `fin_complete` by race and its effect on the gap (replicates and extends B05/B06 race waterfall); is missingness driven by exempt filers, loan purpose, or lender? | `B14_rq2_missingness_selection.csv`; plots |
| D7 | **Denial reasons** (denied only; descriptive, **never a predictor**) | Share of each `denial_reason_1..4` code by race; code `10` / `1111` handled per rules T06/T10; reasons "DTI" and "Collateral" vs financial strata | `B14_rq2_denial_reasons.csv`; stacked bars |
| D8 | **Pricing among originated loans** (conditional on origination) | `interest_rate`, `rate_spread`, `total_loan_costs` by race × loan_type; flagged as conditional (selection) | `B14_rq2_pricing_by_race.csv` |

---

## 8. Part E — Relationship analysis (Assignment 3.3 C)

| ID | Relationship | Method |
|---|---|---|
| E1 | Numeric–numeric: `loan_amount` vs `income`, `loan_amount` vs `property_value`, CLTV vs `ltv_calc`, rate vs CLTV / term (originated only) | Hexbin on `df_samp` (log axes), Spearman correlation matrix (heatmap), annotate heaping |
| E2 | Categorical vs outcome | Cramér's V (bias-corrected) and denial-rate spread for each categorical variable; mutual information with `is_denied` on `df_samp` |
| E3 | Collinearity preview for later models | Correlation among candidate controls; VIF on numeric block (`df_samp`, complete cases flagged as such); identify redundant pairs (e.g., CLTV vs ltv_calc, tract fields) |
| E4 | Race association with controls | Standardised mean differences of each control between each minority group and the reference (love-plot style) — shows which controls could plausibly narrow the gap |
| E5 | Importance preview (optional) | Simple univariate AUC of each control vs `is_denied`, no model fitting beyond a single-variable score; supports ordering of controls in the sequential framework |

Outputs: `B14_rel_spearman.csv`, `B14_rel_cramers_v.csv`, `B14_rel_vif.csv`, `B14_rel_smd_by_race.csv`.

---

## 9. Part F — RQ3 geography and lender

### Geography
| ID | Analysis | Notes |
|---|---|---|
| F1 | State-level denial rate and gap (Black–White, Asian–White, etc.) with CIs and `low_n` suppression | Forest plot sorted by gap; **map** via `plotly` choropleth (`locationmode="USA-states"`) with matplotlib tile-grid fallback if offline |
| F2 | MSA-level: top MSAs by volume, `non_msa` (code 99999, [Hypothesis]) vs MSA; denial and gap | Table + dot plot |
| F3 | Tract context: `tract_minority_population_percent` bins and FFIEC income-level of tract (A10) × applicant race; own-race vs neighbourhood-composition view | Heatmap; checks the "applicant vs neighbourhood" confounding |
| F4 | Missing census tract (D-I): selection of RQ3 sample by race; denial rate of tract-NA rows (very high per B05 cell 35) and what dropping them does to each gap | `B14_rq3_tract_na_selection.csv` |
| F5 | Heterogeneity across states: variance of gap across states, share of states with gap sign reversed, correlation of state gap with state average denial rate | Table + scatter |

### Lender
| ID | Analysis | Notes |
|---|---|---|
| F6 | Lender size and concentration: distribution of applications per lender, top-N share, HHI by market (state), `lender_size_bucket` mix by race | Lorenz-type curve |
| F7 | Dispersion of lender denial rates: **funnel plot** (denial rate vs volume with binomial control limits) to separate noise from true dispersion | Lenders anonymised (D-O) |
| F8 | Race mix sorting: do minority applicants concentrate in higher-denial lenders? Between- vs within-lender decomposition: lender-standardised gap (compare each group to the reference **within the same lender**, then aggregate with fixed weights) | `B14_rq3_lender_standardised_gap.csv` |
| F9 | Lender-level gap distribution among lenders with enough applicants in both groups (D-M); share of lenders with positive / negative gap | Histogram + table |
| F10 | Exempt filers and lender size: `is_exempt_filer` / `is_partial_exempt` by lender size; denial rate and missing-data pattern | Links to RQ4 |

Limitation to document: public HMDA has no lender type (bank / credit union / independent mortgage company) or lender name; an external LEI mapping is **out of scope** unless Human decides otherwise.

---

## 10. Part G — RQ4 robustness preview and missing variables

| ID | Analysis | Output |
|---|---|---|
| G1 | **Sample sensitivity matrix**: raw gap (pp and OR) for each group under: S0; `in_s5_all`; `in_s5_keep_v02`; `fin_complete`; RQ3 sample; S0 without `flag_dup_extra`; S0 without exempt filers; S0 without partial-exempt; originated-vs-denied only (exclude action 2); S0 with `Race Not Available` removed | `B14_rq4_sample_sensitivity.csv`; dot plot of gap by sample |
| G2 | **Special-code handling sensitivity**: DTI/income/CLTV missing → (a) drop, (b) explicit "missing" category, (c) missing indicator + median fill (preview only); effect on stratified gap | `B14_rq4_missing_handling.csv` |
| G3 | **Outcome definition sensitivity**: denial among {1,3} only vs {1,2,3}; "approved but not accepted" treated as approved vs excluded | Included in G1 |
| G4 | **Missing variables inventory**: credit score value, assets / reserves, AUS result, application date, employment / income documentation, loan officer / channel detail → what proxy exists in public HMDA (`applicant_credit_score_type`, `aus_1..5`, `submission_of_application`, lender FE) and how that limits interpretation | `B14_rq4_missing_variables.csv` (table written from the dictionary, each row tagged [Verified: dictionary]) |
| G5 | **Stability of the gap across subgroups**: sign and size of the Black–White gap across loan purpose, loan type, lien, DTI band, income quartile, state size; list of subgroups where it flips | `B14_rq4_gap_stability.csv` |

---

## 11. Financial interpretation template (Assignment 3.3 E)

For every major finding, the interpretation md cell must answer: (1) What pattern is observed? (2) What evidence (table / figure / cell number)? (3) Why might it matter in mortgage lending (underwriting, pricing, access, fair-lending screening)? (4) Which alternative explanations or limitations apply (unobserved credit score, assets, AUS, lender policy, selection from missing data, `Race Not Available`, pooling of heterogeneous groups)? Wording stays descriptive: "gap", "association", never "discrimination" or "bias" as a conclusion.

---

## 12. Dual-implementation hooks (Pandas now, PySpark later)

EDA is Pandas. To keep Part 4 of the Assignment cheap, B14 defines **named, version-fixed table functions** whose PySpark twins will be written in the next task. Proposed equivalence targets (≥ 3 required, 6 proposed):

| Target | B14 table | Tolerance |
|---|---|---|
| E1 | S0 row count and overall denial rate | exact |
| E2 | Denial rate by `derived_race` (C1) | exact counts, rate ±1e-9 |
| E3 | Race × `loan_type` counts / denied / rate (**the benchmark workload in the Proposal**) | exact |
| E4 | Missing-share per key variable (A4) | exact counts |
| E5 | Median / quantiles of `loan_amount`, `income` (B1) | PySpark `percentile_approx` vs exact → document difference; use exact `approxQuantile` with relativeError 0 on a check run |
| E6 | Lender × race aggregated counts (F7–F9 input) | exact |

Each function is documented in the ledger-style table `output/B14_pyspark_equivalents.csv` with columns `table_id`, `pandas_impl`, `pyspark_equiv`, `known_semantic_differences` (NULL handling, quantile method, `groupby(dropna=False)` vs Spark default). Convention 4.6.

---

## 13. Deliverables

| Type | Items |
|---|---|
| Notebook | `B14 - <date>.ipynb` (Restart & Run All clean) |
| Registry | `B14_variable_roles.csv`, `B14_pyspark_equivalents.csv` |
| Tables | All `B14_*.csv` listed in Parts A–G |
| Figures | `output/figures/B14_fig_*.png` (≈ 25–35; every figure answers a research question) |
| Findings log | `output/B14_eda_findings.csv` (`finding_id`, RQ, pattern, evidence artifact, caveat, [Verified]/[Hypothesis]) built from computed variables, not typed numbers |
| Documents | Updated `decisions.md` (D-J … D-S), proposed edits to `data_cleaning_rules.md` if EDA reveals rule gaps, `B14_hand_off.md` (design recommendation for the sequential decomposition: controls per stage, samples, reference groups, variables excluded) |
| Summary | `B14_summary.csv` (dynamic, like B05/B06 section 8/9) |

---

## 14. Execution order and checkpoints

| Order | Block | Gate before moving on |
|---|---|---|
| 1 | Config, loading, variable roles skeleton, A1–A2 | Row counts equal B06; peak memory logged |
| 2 | A3–A5, B1–B7 | Leakage audit reviewed by Human (roles table) |
| 3 | C1–C6 | Headline gap table reviewed; D-J / D-K / D-L / D-P confirmed |
| 4 | D1–D8 | Missingness and selection findings reviewed |
| 5 | Part E (relationships) | Collinear pairs listed |
| 6 | F1–F10 | Lender anonymisation (D-O) confirmed |
| 7 | G1–G5, findings log, hand-off, summary | Restart & Run All passes; checklist below |

Estimated runtime budget: loading + tables on full S0 should stay in minutes; sample-based steps (E, hexbin) use `df_samp`. If total runtime exceeds ~30 min, apply D-S.

---

## 15. Risks and open points

1. **Informative missingness** (DTI, income, CLTV) can make `fin_complete` results look like the gap narrows when it is partly selection. Mitigation: always show S0 and `fin_complete` side by side (D-N), plus G2.
2. **Large `Race Not Available` share** can hide or distort group gaps; handled by D-L and C6.
3. **Pooling heterogeneous lenders / markets**: simple CIs are too narrow; mitigated by lender-cluster bootstrap (D-Q) and F7–F9.
4. **Small groups** (`Free Form Text Only`, `2 or more minority races`, `Native Hawaiian or Other Pacific Islander` in some states) produce unstable rates; handled by D-M.
5. **Leakage-looking variables** (pricing, purchaser, HOEPA, denial reasons) must stay out of denial controls; enforced via `B14_variable_roles.csv`.
6. **Sample-based statistics** (VIF, MI, Spearman) are approximations; seed and `SAMPLE_N` are logged, and one full-data check is run for the headline correlation.
7. **Map rendering offline**: `plotly` choropleth may need bundled resources; fallback tile-grid map prepared.
8. **Tract-income-level cut-offs (A10)** are unverified until checked against FFIEC documentation.
9. **Performance of group-bys** with `category` dtype and `observed=True/False` — a known Pandas pitfall that silently drops or adds empty groups; every groupby uses explicit `observed=True, dropna=False` and a row-sum check.

---

## 16. Quick acceptance checklist (Convention 7)

- [ ] Notebook runs top to bottom without error.
- [ ] Every code cell has an English md cell (Input / Process / Output).
- [ ] All outputs in `output/`, named `B14_*`, logged with path, size, shape.
- [ ] No number typed into md or tables without "as of run <date>, cell <n>".
- [ ] Row counts reconcile (S0 total, by-race sums, strata sums).
- [ ] Every figure has title, axis labels, units, n, interpretation.
- [ ] Leakage audit (A3) and variable roles reviewed.
- [ ] Decisions D-J … D-S recorded in `decisions.md`.
- [ ] PySpark equivalents table complete (≥ 3 targets implemented in the next task).

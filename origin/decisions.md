# Project Decision Log: HMDA 2024 Big Data Analysis

**Project:** Decomposing Racial Gaps in Mortgage Denial Rates: A Large-Scale Analysis of the 2024 U.S. HMDA Market  
**Course:** Big Data Analysis (Final Project) — Group 3  
**Status Key:** `Agreed` (Decision approved, empirically verified, and locked), `Open` (Pending analysis), `Dropped` (Explicitly excluded from scope), `Revisit` (Subject to sensitivity check)  
**Evidence Base:** Empirically verified across 12,259,199 raw applications and 8,136,664 Analytic Sample ($S0$) applications via DuckDB vectorized engine in Milestone B05 (`B05 - 31 Oct v5.ipynb`, run 2026-10-31).

| ID | Date | Decision | Reason | Impact (rows/metric) | Status |
|---|---|---|---|---|---|
| D-A | 2026-10-30 | Confirm F02 (exclude business-purpose loans: code `'1'`) and F03 (exclude reverse mortgages: code `'1'`) using NULL-safe positive membership `.isin(['2', '1111'])` | Focus is consumer mortgage credit. Business loans follow commercial underwriting (DSCR/cash flow); reverse mortgages have no monthly payments and are age-restricted (62+). Positive membership `.isin(['2', '1111'])` ensures engine equivalence between Pandas and PySpark by preventing NULL/NaN filter leakage. Statutory small-filer exempt loans (`1111`: 250,691 business, 250,889 reverse in $S0$) are retained under `[Hypothesis: assumed to be consumer mortgages]`. | Excludes 525,115 rows (6.06% of F01 decision sample of 8,661,779; 4.28% of 12,259,199 raw). Sequential waterfall: F01 (8,661,779) $\rightarrow$ F02 (8,170,177, $-491,602$) $\rightarrow$ F03 (8,136,664, $-33,513$). Standalone F03 on F01 is 33,569 rows; overlap is 56 rows ($491,602 + 33,569 - 56 = 525,115$). Analytic Baseline $S0 = 8,136,664$ rows (66.37% of raw, 93.94% of F01; denial rate 24.62%). | Agreed |
| D-B | 2026-10-30 | Retain `income <= 0` in `clean_all` and Analytic $S0$; flag with Rule V02 (`flag_income_nonpositive`, `flag_income_zero`, `flag_income_negative`); set `loan_to_income = NULL`; evaluate via Corrected Dual Robustness $S5$ (`S5_all` vs. `S5_keep_v02`) | Negative income represents legitimate net tax losses (IRS 1040 Schedule C/E) per CFPB guidelines or non-relied income `[Hypothesis]`. Strongly outcome-related: in $S0$, negative income has a 95.51% denial rate (6,595 / 6,905) and zero income has a 57.63% denial rate (48,612 / 84,356), with an overall V02 denial rate of 60.49% (55,207 denials). Dropping V02 artificially removes 55,207 denials and compresses the overall denial rate by $-0.40\text{ pp}$ (from 24.58% down to 24.18%). Setting `loan_to_income = NULL` prevents invalid negative ratios or division-by-zero errors. | Raw: 165,254 rows flagged V02 (157,494 zero; 7,760 negative). Analytic $S0$: 91,261 rows flagged V02 (84,356 zero; 6,905 negative; 55,207 denials). Dual Robustness $S5$: `S5_all` (excludes V01, V02, V03, V05; keeps V04) = 8,041,498 rows, 24.18% denial; `S5_keep_v02` (excludes V01, V03, V05; keeps V02 & V04) = 8,132,620 rows, 24.58% denial. | Agreed |
| D-C | 2026-10-30 | Retain `interest_rate <= 0` in `clean_all` and Analytic $S0$; flag with Rule V04 (`flag_rate_range`, `flag_rate_le0`, `flag_rate_gt25`); do **NOT** exclude from core denial-rate gap models or Robustness $S5$; report rate statistics descriptively with and without V04 | 95.34% of zero-rate loans are subordinate liens (`lien_status = '2'`), representing 5.220% of reported rates in that lien group `[Hypothesis: Down Payment Assistance (DPA) second loans]`. 4.66% are first-lien loans. **Crucially, reported interest rate is 100% missing (`NA`/`Exempt`) on denied applications (`action_taken = '3'`); denied loans have 0 rows with reported rates.** Excluding V04 from denial gap models or $S5$ would drop 60,717 approved loans and 0 denied loans, creating an artificial upward bias in denial rates (+0.15 pp). V04 is kept in all denial-rate models and $S5$, and only separated when modeling pricing/rate-spread where interest rate is the dependent variable. | Raw: 83,443 rows flagged V04 (83,442 $\le 0$; 1 $> 25$). Analytic $S0$: 60,717 rows flagged V04 (60,716 $\le 0$; 1 $> 25$), 100% of which are approved/originated (`action_taken` $\in \{1, 2\}$). Prevents +0.15 pp artificial inflation of denial rates in robustness testing. | Agreed |
| D-D | 2026-10-30 | Retain all 9 published race groups from `derived_race` (Rule X03); focus primary gap decomposition on White, Black, Asian with transparent reporting of remaining groups; derive `has_coapplicant` via 4-state hierarchical precedence (`Present > No_Coapp > NA`) with `flag_coapp_discordant` (Rule X05) | Preserves full distributional integrity of the HMDA population. White, Black, and Asian represent the vast majority of volume and historical fair-lending benchmarks; other groups (Joint, American Indian/Alaska Native, Native Hawaiian/Pacific Islander, 2+ Minority Races, Free Form Text Only) are reported in full. For co-applicants, empirical audit reveals 79,088 raw rows (18,230 in $S0$) with discordant states across the 4 co-applicant fields (`co_applicant_age`, `_sex`, `_race_1`, `_ethnicity_1`). Hierarchical precedence (`Present > No_Coapp > NA`) ensures any positive presence assigns `1`, pure absence assigns `0`, and only completely uninformative records assign `NULL`. In $S0$, uninformative all-NA records are minimized to just 3,625 rows (0.045%), avoiding the misclassification of ~1.13M purchased-loan `8888` records as active co-applicants. | 100% of $S0$ applications retained (8,136,664 rows). In $S0$: 79,088 raw / 18,230 $S0$ discordant rows flagged via `flag_coapp_discordant`; unresolved all-NA co-applicants reduced to 3,625 rows in $S0$. | Agreed |
| D-E | 2026-10-30 | Plan storage of `clean_all.parquet` unpartitioned with `bucket` column and `analytic.parquet` as a single unpartitioned Parquet file (to be produced in B06–B08) | Parquet snappy columnar compression is highly efficient (raw parquet input: 432.33 MB). A single unpartitioned file eliminates small-file I/O overhead and partition fragmentation across Pandas and PySpark. The `bucket` column (Knuth multiplicative hash $0..99$ on `row_id`) provides deterministic, reproducible 25%, 50%, and 100% subsamples for scalable benchmarking. | Target row counts: `clean_all` = 12,259,199 rows (101 cols); `analytic` ($S0$) = 8,136,664 rows. File sizes and row counts to be logged upon artifact creation in B06–B08. | Agreed |
| D-F | 2026-10-30 | Utilize DuckDB as independent audit and profiling engine (B04–B05); implement dual production cleaning pipeline in Pandas (B06) and PySpark (B07); audit cross-engine equivalence in B08 | Fulfills Big Data course requirements for dual Pandas vs. PySpark implementations while leveraging DuckDB's high-speed vectorized in-process OLAP engine for full 99-column whitespace/sentinel audits, non-circular co-occurrence profiling, and rule calibrations. | Rigorous parity verification in B08: exact integer identity on all row counts and boolean flag tallies; floating-point agreement within tolerance $\le 10^{-9}$. | Agreed |
| D-G | 2026-10-31 | Calibrate Rule T12 as strictly per-field; retain legitimate zero housing ages; preserve FFIEC income on tract-NA rows; calibrate Rule X09 strictly on the 28 statutory documented fields; treat Rule V09 as an empirical diagnostic profile (not a row deletion filter) | 1) **T12 (Census):** Blanket tract nulling would wipe valid FFIEC income on 55,343 applications with missing tract but valid county/MSA, and would inappropriately null 502,156 legitimate zeros on populated tracts (`tract_median_age_of_housing_units == 0`, `[Hypothesis: newly developed tracts; unverified]`). Only code `-1` (204 rows) in housing age is a true invalid code set to `NULL`. The 293,681 zeros in `ffiec_income` occur strictly when both `county_code` and `census_tract` are NA (`[Hypothesis: complete absence of geocoding]`; all 1,471,022 valid-tract rows with `derived_msa_md = '99999'` have positive FFIEC income). `derived_msa_md = '99999'` is assigned status `'non_msa'`.<br>2) **X09 (Exempt filers):** Defining exempt flags strictly on the **28 statutory fields documented in the CFPB Data Dictionary** (14 literal `Exempt` + 14 documented `1111` categorical fields) eliminates the empirical artifact where 22,885 rows had *only* undocumented `denial_reason_1 = '1111'` and 0 other exempt fields. `flag_dr1_is_1111` is tracked separately under `[Hypothesis: FFIEC S.2155 Exemption]` (present in 78.04% of $n = 28$). Full exempt filers ($n = 28$): 276,755 raw, 241,108 in $S0$. Partial exempt ($1 \le n \le 27$): 23,164 raw, 15,292 in $S0$.<br>3) **V09 (CLTV discrepancy):** Treated as an empirical diagnostic profile, not an exclusion rule. In $S0$ first liens, median $\|\text{CLTV} - \text{LTV}\|$ is 0.76 pp (p95: 4.7 pp), but only 59.03% fall within $\pm \$5,000$ property midpoint rounding bounds, and 442,881 rows (8.80%) lie $> 1\text{ pp}$ below minimum bound. Breakdown by loan type reveals candidate causes `[Hypothesis]`: FHA (19.75% below bound) and VA (14.97% below bound) finance upfront mortgage insurance fees into `loan_amount`, inflating it relative to CLTV.<br>4) **Pre-RQ3 tract audit:** Documents that 96,065 $S0$ rows lack a census tract and suffer a 76.53% denial rate (vs. 24.00% on valid tracts), disproportionately affecting AIAN (2.83% missing, 86.47% denial) and Black (2.14% missing, 87.14% denial) borrowers. | Preserves 55,343 FFIEC incomes and 502,376 valid tract housing ages; removes artifactual partial exempt rows in X09; prevents false row deletion under V09; provides documented baseline for RQ3 geographic sample selection. | Agreed |
| D-H | 2026-10-31 | Convert hidden Census demographic zeros to `NULL` (status `'no_tract'`) on tract-NA rows and un-geocoded FFIEC income zeros to `NULL` (status `'no_geo'`) under Rule T12 items 1–2 | When `census_tract` is missing (349,024 raw; 96,065 in $S0$), the 6 tract demographic fields (`tract_population`, `tract_minority_population_percent`, `tract_owner_occupied_units`, `tract_one_to_four_family_homes`, `tract_median_age_of_housing_units`, `tract_to_msa_income_percentage`) hold raw `0` on all 349,024 rows. Leaving them as 0 would corrupt econometric models by treating missing tracts as zero-population or zero-income areas. Converting them to `NULL` with status `'no_tract'` preserves data integrity without imputation. For `ffiec_msa_md_median_family_income`, the 293,681 rows with value `0` occur strictly when both `county_code` and `census_tract` are missing (`[Hypothesis: complete absence of geocoding]`) and are converted to `NULL` with status `'no_geo'`, while preserving positive FFIEC income on 55,343 applications with missing tract but valid county. | Raw: converts 349,024 raw zeros in 6 tract demographic fields to `NULL` (status `'no_tract'`), converts 293,681 un-geocoded zeros in FFIEC income to `NULL` (status `'no_geo'`), and converts 204 `-1` values in housing age to `NULL` (status `'na_code'`). Retains 57,954 zeros in `tract_to_msa_income_percentage` on valid populated tracts (+220 on zero-pop tracts) flagged with `flag_tract_income_zero`. | Agreed |
| D-I | 2026-10-31 | Mandate valid `census_tract` for RQ3 geographic/lender disparity models; sequentially recompute baseline Step 1–3 models on the geographic subsample to isolate selection bias | RQ3 specifically investigates neighborhood-level tract disparities (tract-to-MSA income ratio, minority share). In $S0$, exactly 96,065 applications (1.18%) lack a census tract (`census_tract = 'NA'`). These missing-tract applications exhibit an extreme denial rate of 76.53% (compared to 24.00% for applications with valid tracts). Missing-tract rates are disproportionately elevated among historically underserved racial groups: American Indian or Alaska Native (2.83% missing, 86.47% denial rate) and Black or African American (2.14% missing, 87.14% denial rate). Filtering out missing tracts for RQ3 constitutes an explicit sample selection mechanism; recomputing Step 1–3 models on the valid-tract subsample is required to isolate structural selection bias from true neighborhood effects. | Restricts RQ3 models to $S0 \cap \text{fin\_complete} \cap \text{valid\_tract}$. Excludes 96,065 tract-NA applications (73,516 denials) from geographic regressions while transparently reporting the disparity waterfall in descriptive exhibits (`B05_tract_na_rq3_crosstab.csv`). | Agreed |
| D-J | 2026-11-09 | Establish `White` (`derived_race`) as the reference group for denial rate disparity gaps; report gaps as percentage point differences (pp), disparity ratios, and odds ratios | White applicants represent the historically benchmarked majority group in fair-lending studies and form the largest demographic bloc in $S0$ (5,360,624 applications, 65.88% of $S0$, as verified in B05 waterfall and B14 C1). Multi-metric reporting provides both absolute disparity ($\Delta\text{ pp} = \text{Rate}_{\text{Minority}} - \text{Rate}_{\text{White}}$) and relative disparity (odds ratio, relative risk). | Standardizes the reference baseline across all bivariate, cross-tab, and decomposition analyses in B14–B15. | Agreed |
| D-K | 2026-11-09 | Retain `derived_race` as primary race categorization (per Proposal); derive supplementary 5-group `race_ethnicity` variable (Non-Hispanic White, Non-Hispanic Black, Non-Hispanic Asian, Hispanic any race, Other/Unknown) for robustness checks | In HMDA, Hispanic ethnicity is recorded independently of race (`derived_ethnicity`). Grouping solely by `derived_race` disperses Hispanic borrowers across White (majority), Black, and other race bins, potentially obscuring distinct Hispanic credit disparities. | Primary exhibits use 9-category `derived_race`; supplementary exhibits profile the 5-group `race_ethnicity` to confirm findings are not distorted by ethnicity aggregation. | Agreed |
| D-L | 2026-11-09 | Treat `Race Not Available` and `Free Form Text Only` as separate unmerged categories in all descriptive accounting; exclude from headline relative disparity gap tables | Borrowers in `Race Not Available` did not provide race (mail/internet) or the lender failed to collect it. In $S0$, their denial rate (29.66%) lies between White (21.92%) and Black (36.80%) (as of run 2026-10-31, B05 cell 39), indicating an unobserved mixture of multiple demographic groups. Merging into either White or minority groups would distort estimated disparity gaps. | Retained as distinct rows in composition and distribution tables; included in total sample denominators; excluded from pairwise headline gap comparisons. | Agreed |
| D-M | 2026-11-09 | Enforce minimum cell size suppression rules (`N_MIN_APPS = 1,000` total applications AND `N_MIN_DENIED = 100` denials) for all demographic-geographic and lender cross-tabulations | Slicing data into fine-grained cells (e.g., Black applicants in Wyoming or small lender $\times$ race segments) generates extreme small-sample noise. A cell with 20 applications and 5 denials yields 25.0% but with a wide 95% Wilson CI [11.2%, 46.9%]. Requiring 1,000 applications guarantees a 95% CI margin of error within $\approx \pm 2.6\text{ pp}$ around a 24% baseline. | Sub-threshold cells are greyed/suppressed in visualizations and flagged with `low_n = True` in data tables to prevent spurious rankings. | Agreed |
| D-N | 2026-11-09 | Establish Analytic Sample $S0$ (`B06_analytic.parquet`, 8,136,664 rows) as universal baseline for EDA profiling; restrict `clean_all.parquet` strictly to selection auditing (no full EDA on `clean_all`); present $S0$, `fin_complete`, and RQ3 geographic sample side-by-side in selection tables | Full EDA on `clean_all` (12.26M rows) is methodologically inappropriate because it includes commercial-purpose loans (F02) and reverse mortgages (F03) that operate under distinct non-consumer underwriting criteria. Full univariate/bivariate profiling is executed strictly on consumer mortgage sample $S0$. Selection tables display $S0$, `fin_complete`, and RQ3 side-by-side to track attrition transparently. | Focuses analysis on target consumer population while rigorously documenting selection mechanisms across subsamples. `clean_all` queried only for lightweight filter validation. | Agreed |
| D-O | 2026-11-09 | Anonymize lender identities in all charts, tables, and reports using synthetic identifiers (`L001`, `L002`, ...); retain raw LEI mapping strictly in internal workspace files | Assignment §5 explicitly requires avoiding unsupported or defamatory conclusions regarding individual financial institutions. High raw denial rates at a specific lender often reflect borrower applicant sorting or specialized loan niches (e.g., FHA, subprime) rather than discriminatory policy. | Protects institutional confidentiality while fully supporting lender heterogeneity analysis. External reports contain no published LEI or institution names. | Agreed |
| D-P | 2026-11-09 | Implement exploratory Kitagawa rate-composition direct standardization decomposition of the Black–White denial gap across loan products and financial strata in B14 | Kitagawa decomposition is an exact algebraic accounting identity that separates an observed disparity gap into a composition effect (differences in borrower/product characteristics) and a rate effect (within-strata denial rate differences) without parametric assumptions, directly addressing step (a) of the Main Research Question. | Serves as an exploratory diagnostic bridge in B14 preceding formal sequential regression models (B15). Code is accompanied by detailed pedagogical markdown cells. | Agreed |
| D-Q | 2026-11-09 | Adopt Wilson score confidence intervals for proportions, lender-cluster bootstrap ($B=1,000$ on pre-aggregated lender $\times$ race tables) for headline gap CIs, and suppress asymptotic p-values | With multi-million row datasets ($N > 8\text{M}$), standard p-values reject all null hypotheses trivially ($p \approx 0$). Applications underwritten by the same lender share institutional policies and are not i.i.d. A pre-aggregated lender-cluster bootstrap provides realistic institutional standard errors at negligible computational cost. | Standardizes inference on robust effect sizes and clustered confidence bounds; eliminates misleading p-value tables; includes pedagogical markdown in notebook. | Agreed |
| D-R | 2026-11-09 | Read B06 parquet inputs directly in-place from a single `B06_DIR` configuration path; do not duplicate parquet files into local `input/` | `B06_analytic.parquet` and `B06_clean_all.parquet` total ~1.3 GB. Duplicating files wastes disk space, complicates cleanup, and violates the single-source-of-truth convention. | Single configuration parameter in config cell; zero file duplication. | Agreed |
| D-S | 2026-11-09 | Structure Milestone B14 as a single comprehensive Jupyter notebook (`B14 - <date>.ipynb`) covering Parts A through F; split into sub-notebooks only if full sequential execution exceeds 30 minutes | A unified notebook ensures consistent state, eliminates cross-notebook data handoff bugs, and produces a coherent end-to-end analytical narrative. Non-linear and computationally intensive diagnostics (MI, scatter) are accelerated via seeded stratified sampling. | Single reproducible notebook meeting Convention 3.9 execution benchmarks. | Agreed |
| D-T | 2026-11-10 | For non-race dimensions in C2 (`derived_ethnicity`, `derived_sex`, `has_coapplicant`), the reference level is the **largest informative level** (levels matching "not available / free form / missing / not provided" are never the reference); `race_ethnicity` uses `Non-Hispanic White` (D-K); `applicant_age` is reported as a **profile** (rate per bracket), with no gap columns | Denial rate by age is non-monotonic, so a "gap vs largest bracket" is arbitrary; uninformative levels are mixtures (D-L) | C2 table `B14_rq1_gap_other_dims.csv`; reference per dimension printed by C2 cell | Agreed |
| D-U | 2026-11-10 | In Kitagawa decompositions (C5, D4), strata where either group fails D-M (`N_MIN_APPS`/`N_MIN_DENIED`) are pooled into one "Other (pooled)" stratum **per comparison pair**; a decomposition is flagged `low_reliability` when pooled share exceeds 10% of either group; `composition_share_of_gap_pct` is set to NULL when \|raw gap\| < 1 pp `[Hypothesis: thresholds]` | Avoids noise-driven strata; share-of-gap explodes when the raw gap is near 0 | In C5, 4 of 6 groups pass (pooled < 10%); 2+ races and NHPI are low reliability (as of run 2026-11-10, B14 C5) | Agreed |
| D-V | 2026-11-10 | Fix Part D bin definitions: `cltv_bin` edges (≤60, 60–70, 70–<80, **=80**, 80–90, 90–95, 95–97, 97–100, >100; CLTV ≤ 0 → `MISSING / invalid`); `lti_bin` edges (<1, 1–2, 2–3, 3–4, 4–5, 5–7, ≥7); `income_decile` = deciles of **positive** income computed on S0, with `Income <= 0` and `Income missing` as separate levels; DTI bins keep `MISSING: na/exempt` as explicit categories | Heaping at 80/95/97/100 must be visible; special codes must not be dropped or merged into numeric bins (Principle 3, rules T02/T07) | Decile edges: see `B14_rq2_income_decile_edges.csv` (as of run 2026-11-10, B14 D0) | Agreed |
| D-X | 2026-11-10 | Strata-level decompositions (Kitagawa) are **reported as estimates only when `low_reliability = False`** (D-U); otherwise reported as "not estimable at this granularity". A coarser spec (DTI group × CLTV group × income group) is run as robustness (G2) | In Part D, pooled share exceeds 10% for **every** group in both specs: FIN: Black 47.55%, Asian 65.65%, Joint 96.38%, AIAN 98.45%, 2+ races and NHPI 100% (0 strata kept); PRODFIN: Black 20.51%, Asian 38.91%, Joint 87.44%, AIAN 97.82% (as of run 2026-11-10, B14 D4) | Part D/F decomposition tables carry `low_reliability`; headline gap claims rely on raw gap + cluster CI (C1). The same rule applies to lender strata (D-AG / B14) | Agreed |
| D-W | 2026-11-10 | Add diagnostic flag `flag_income_extreme` (`income` > 10,000 in $1,000s, i.e. > $10M) `[Hypothesis: threshold]`, formalised as rule V11 (rulebook v2.4). The flag is derived from `income` only; rows are **kept** in S0 and reported with/without in G1. **B06 is not re-run.** | `income` reaches 100,000,000 (≈ $100 billion; as of run 2026-11-10, B14 D0). Rows above $10M are 0.0123% of S0 (as of run 2026-11-10, B14 G0), so the effect on the overall denial rate is negligible, but they distort means, correlations, VIF and SMD. Their `loan_to_income` is far below typical values while loan amounts are ordinary (median loan_to_income 0.0419 vs median loan 720,000; as of run 2026-11-10, B14 G0), but G0 gives weaker evidence of a keying error than first written: 880 distinct income values among 1,000 rows (most common value 1.6%, i.e. 12,000 appears 16 times), 237 lenders (largest 9.5%), 5.2% exempt filers (as of run 2026-11-11, B14 G0), so there is no sign of one placeholder or one source. Reading the value as dollars instead of $1,000s gives a median loan-to-income of about 42, and reading it as reported gives 0.042; neither is plausible, so the cause is unexplained `[Hypothesis]`. Re-running B06 would cost about an hour and break lineage with B07/B08 and the 48/48 golden checks, for a flag that is a pure function of `income`. | Profile of rows above $10M in `B14_income_extreme_detail.csv` (G0); counts and denial rate at > $1M, > $10M, > $100M in `B14_income_extreme_profile.csv` (E0), where the rate rises with the threshold from below the S0 rate at > $1M to above it at > $10M (as of run 2026-11-11, B14 E0). The G0 threshold table (> $5M) was displayed, not saved. Removing the flagged rows moves the Black, Asian, Joint and AIAN gaps by less than 0.003 pp (as of run 2026-11-11, B14 G1). No row removed; no value changed. B07/B08 must compute V11 in both Pandas and PySpark so parity holds. | Agreed |
| D-Y | 2026-11-10 | Exclude `aus_1` and `applicant_credit_score_type` from the main sequential specification (Steps 2–4); include them only in a separate "with proxies" specification as an RQ4 robustness check, and compare the gap with and without them | Both fields describe which system or model was used, not its result or value (A5, `B14_rq4_missing_variables.csv`). They mainly reflect lender choice, loan product and channel, so they may act as bad controls `[Hypothesis]`, and their availability may depend on the outcome (tested in A3). | Main-spec gaps stay comparable across stages. The "with proxies" spec reports how much of the remaining gap is absorbed by these fields; the difference is read as "association with lender/product sorting", not as credit risk. Availability gaps: see `B14_availability_by_outcome.csv` (as of run 2026-11-10, B14 A3). | Agreed |
| D-Z | 2026-11-10 | In the state-size heterogeneity analysis (G5), keep rows with NULL `state_code` as a separate level `State missing`; do not merge them into any size group | Rule T05 converts raw `NA` to NULL, so these rows have no state. Merging them would invent a state size; dropping them is a selection step (Principle 3, D-V). The level is subject to D-M and is dropped from conclusions if `low_n`. | S0 count printed by G5 (as of run 2026-11-10, B14 G5) | Agreed |
| D-AA | 2026-11-10 | Move `loan_term` from `post_decision_exclude` to `product_control`; use it in the main sequential specification (Step 2, product controls) and run one sensitivity specification without it in B15 | The "Decisioning" axis in the project data dictionary is a group assumption (dictionary README), not a CFPB classification. Audit A3 shows no leakage: available on 95.95% of non-denied and 93.72% of denied applications (gap 2.22 pp, below the 50 pp flag; B14 A3). The FFIEC 2024 Filing Instructions Guide (field 82) defines it as the number of months after which the obligation will mature "or would have matured", so it is also reported for applications `[Verified: FFIEC 2024 FIG]`. For approved loans the value may be the final term rather than the term requested `[Hypothesis]`. | One column role change; no rows removed or changed. 95.40% of S0 has a value (4.60% missing, concentrated in exempt filers `[Hypothesis]`); missing values stay as an explicit category in models (D-V). `B14_variable_roles.csv` and `B14_hand_off.md` updated. | Agreed |
| D-AB | 2026-11-10 | Keep `conforming_loan_limit` as a product control with its four levels `C` (reference), `NC`, `NA`, `U`; treat `NA` as the 5+ unit (multifamily) indicator, so no separate multifamily dummy or `derived_dwelling_category` multifamily level is added beside it; keep `U` as its own level in models and suppress it in tables under D-M | Cross-tab in B14 (check cell for `conforming_loan_limit`): all 9,440 `NA` rows have 5 or more units and no other row does (0 disagreements); all 293 `U` rows have fewer than 5 units `[Verified: B14 check, as of run 2026-11-10]`. `NA` is therefore Not Applicable by definition of the CFPB-derived field, not missing data, and duplicates the multifamily information. Pooling `U` into `NA` was rejected because it would mix 293 ordinary properties into the multifamily group. `U` fails D-M (293 < 1,000 applications). | No rows changed. `C` 7,903,790 (97.14% of S0), `NC` 223,141 (2.74%), `NA` 9,440 (0.12%, denial 6.39%), `U` 293 (denial 32.42%, `low_n`). Avoids perfect collinearity between the `NA` level and a multifamily dummy. | Agree |
| D-AC | 2026-11-10 | Add `n_rate_usable` and `low_n_rate` (`n_rate_usable < N_MIN_APPS`) directly to `seg_table` in Step B4b (`B14_pricing_by_segment.csv`) and examine pricing hypotheses H1–H5 across product segments | In several originated-loan segments (e.g., open-end exempt `'1111'` with 99.80% missing rate, or USDA subordinate liens with 71.71% missing rate), `n_originated >= 1,000` passes `low_n`, but the number of usable rates (`n_rate_usable`) falls below `N_MIN_APPS = 1,000` `[Verified: B14 B4b, as of run 2026-11-10]`. Computing `n_rate_usable` and `low_n_rate` inside `seg_table` ensures the exported CSV (`B14_pricing_by_segment.csv`) and Figure 07b share the exact same reliability mask without recalculating via rounded percentages. | Adds 2 columns (`n_rate_usable`, `low_n_rate`) to `B14_pricing_by_segment.csv`; no rows removed or modified. | Agreed |
| D-AD | 2026-11-11 | In Part D, read denial reasons (D7) as **denials per 100 applications** (share among denied × race denial rate), in a `primary` version (additive to the raw gap) and an `any_of_4` version (overlapping); do not infer the contribution of a reason to a gap from its share among denied applications | Shares among denied are conditional on denial: DTI is a *smaller* share of denied Black applications (31.08%) than of denied White applications (33.09%) but contributes +4.18 pp per 100 applications. Reasons are lender-reported and post-decision, so they are descriptive evidence, not a credit score `[Hypothesis]` | New table `B14_rq2_denial_reasons_contribution.csv`. Black–White raw gap 14.88 pp = credit history +7.13 (47.90%) + DTI +4.18 (28.10%) + incomplete application +0.91 + other +0.87 + collateral +0.69 + unverifiable +0.53 + insufficient cash +0.42 + employment +0.11 + exempt +0.04 + MI denied +0.003 (as of run 2026-11-11, B14 D7c). No rows changed | Agreed |
| D-AE | 2026-11-11 | Re-run the D2 denial curves (DTI fine, CLTV bin, income decile, LTI bin) separately within product segments, defined as a partition of S0: first lien purchase, first lien refinance (codes 31, 32), first lien other purpose, subordinate lien closed-end, open-end line of credit; add the share of each segment in each bin. The pre-specified test of the product-mix hypothesis is in the in-depth note (thresholds are `[Hypothesis]`) | The all-S0 curves mix products with very different base rates, and the D3 surface is limited to first liens, so neither can show whether the high denial at DTI < 20 and CLTV <= 60 is a product-mix effect. The Part D interpretation currently carries this as `[Hypothesis]` | `B14_rq2_denial_curves_by_segment.csv` and `B14_fig_17b_denial_curves_by_segment.png` (as of run 2026-11-11, B14 D2b). Pre-specified 5 pp test: **CLTV <= 60 passes** (first-lien purchase 6.87% vs 14.33% segment base, −7.46 pp; refinance 27.84% vs 29.08%, −1.23 pp; 60.47% of bin is open-end/subordinate/other-purpose), confirming product mix. **DTI < 20 fails** in every segment (+10.72 pp above 20–<30 in purchase, +10.93 pp in refinance, +15.57 pp in subordinate closed-end, +13.17 pp in open-end), rejecting product mix as a sufficient explanation for DTI < 20 | Agreed |
| D-AF | 2026-11-11 | Main sequential specification, Step 3: use `dti_cat`, `cltv_bin`, `income_decile` (with its missing levels) and `log_loan_amount`; **do not** use `log_lti` / `lti_bin` or `ltv_calc` in the same specification. `lti_bin` and the continuous `log_income` + `log_loan_amount` form are run as one robustness specification | VIF on complete cases (n = 423,726) is 84.2 for `log_loan_amount`, 63.8 for `log_lti`, 36.2 for `log_income` and 13.7 for `ltv_calc`. `log_lti` equals `log_loan_amount` − `log_income` by construction. No pair has \|r\| > 0.8 (`B14_rel_redundant_pairs.csv` is empty), so a pairwise screen would not have found it. Reported CLTV is preferred to `ltv_calc` because `ltv_calc` leaves out the senior lien for subordinate liens (B2). `income_decile` is preferred to `log_income` because it keeps `Income <= 0` and `Income missing` as levels (D-V) | `B14_hand_off.md` Step 3 list changes (see section 4). No rows changed. Model specs in B15 must match | Agreed |
| D-AG (B14) | 2026-11-11 | In RQ3, report the lender-as-stratum Kitagawa decomposition (F8) as "not estimable at this granularity" (D-U, D-X) and base lender-level evidence on (i) the within-lender gap among lenders where both groups pass D-M (F9, always shown with `coverage_pct`) and (ii) the gap inside lender-size buckets (F6) | All six groups are `low_reliability` in F8: pooled share (max of group and White) is 44.10% for Black, 52.82% Asian, 65.48% Joint, 79.19% AIAN, 95.56% 2+ minority races and 100% Native Hawaiian or Other Pacific Islander (0 lenders kept). The pooled stratum merges thousands of small lenders, so lender sorting inside it is counted as rate `[Hypothesis: direction]` | F8 values stay in `B14_rq3_lender_standardised_gap.csv` for traceability only (Black: composition +2.69 pp, rate +12.18 pp; as of run 2026-11-11, B14 F8). F9 covers 69.82% of Black applications (97 lenders), 61.49% Asian (60), 38.54% Joint (27), 30.62% AIAN (11); 2+ minority races 1 lender, Native Hawaiian or Other Pacific Islander none. No rows changed | Agreed |
| D-AG | 2026-11-18 | Exclude `race` from predictive feature sets (M1–M3); restrict race strictly to post-hoc audit error-grouping (Q-B), White-trained counterfactual decomposition (Q-C), and optional diagnostic models (Q-D) | Using race in credit underwriting models is legally prohibited (ECOA / Reg B); a benchmark with race cannot measure what race *adds*. Keeps predictive measuring benchmark race-blind while allowing rigorous diagnostic gap audit. | Race is excluded from all candidate feature sets across 100% of $S0$ (8,136,664 rows). All 9 `derived_race` categories are retained for audit and decomposition. | Agreed |
| D-AH | 2026-11-18 | Run all nested feature sets (M1, M2, M3) across two underwriting-proxy variants: **P0** (baseline without `aus_1` and `applicant_credit_score_type`) and **P1** (including both proxies) | Follows Decision D-Y. `aus_1` and score type reflect process/channel rather than borrower risk, and `aus_1` code `6` (`Not applicable`) is about twice as frequent on denied files (45.3% vs. 22.1%, as of run 2026-11-10, B14 A3; 59.36% vs. 34.65% in grouped validation, as of run 2026-11-20, B16c C2). Comparing P0 vs. P1 quantifies how much explanatory power derives from process proxies. | Dual-pipeline evaluation of all models on $S0$. P0 serves as headline benchmark; P1 serves as upper-bound diagnostic. | Agreed |
| D-AI | 2026-11-18 | Partition 2024 Analytic Sample $S0$ using **lender-grouped split** (60% train / 20% validation / 20% test, stratified across 4 lender size buckets by application volume) as primary; retain random stratified 60/20/20 split as optimistic reference | Random splits let the model memorize individual lender denial policies (P7). Grouped splitting evaluates generalization to unseen institutions. Stratifying by lender size bucket ensures Small, Medium, Large, and Mega lenders appear in all splits. | $S0$ (8,136,664 rows) partitioned into Train (~4.88M), Val (~1.63M), Test (~1.63M). The difference in AUC between random and grouped splits directly measures lender leakage. | Agreed |
| D-AJ | 2026-11-18 | **Dropped**: Do not perform external validation on HMDA 2025; restrict predictive analysis strictly to 2024 $S0$ | Assignment §2.1 fixes scope to 2024 HMDA. Schema shifts, definition adjustments, or incomplete reporting in 2025 would confound cross-sample evaluation. Single-year limitation is documented transparently. | 0 rows from HMDA 2025 loaded or processed. Preserves project scope and prevents schema-mismatch confounding. | Dropped |
| D-AK | 2026-11-18 | Strictly enforce test-set discipline: test set is evaluated exactly once per final locked model; all hyper-parameter tuning, model selection, and decision thresholds are determined strictly on the validation set | Prevents optimistic data snooping and adaptive overfitting. Ensures unbiased out-of-sample performance estimates for headline reporting. | Test set (~1.63M rows, ~20% of $S0$) remains unvisited until final model locks. All threshold optimizations (e.g. max-F1) use validation set only. | Agreed |
| D-AL | 2026-11-18 | Model family selection: Logistic Regression (L2 regularization, binned features) as interpretable baseline, and HistGradientBoostingClassifier (sklearn, native categorical/missing support) as primary tree ensemble, with Random Forest retained for Proposal fidelity; build matching PySpark MLlib counterparts | LR provides transparent odds ratios matching B14 curves. HistGradientBoosting handles large data ($N > 8\text{M}$) and missingness natively without imputation. Fulfills course dual-engine requirement. | Dual Pandas/sklearn and PySpark MLlib implementations on full $S0$. Fit times, scoring throughput, and parity tolerances tracked in ledger. | Agreed |
| D-AM | 2026-11-18 | Restrict lender feature engineering to coarse `lender_size_bucket` only; strictly exclude lender identifiers (`lei`, `lender_code`) or fine lender target encodings from grouped-split models (permitted only in random-split reference) | In lender-grouped splits, test lenders are entirely unseen, so specific lender IDs or target encodings cannot generalize and would cause severe overfitting. `lender_size_bucket` captures broad institutional differences honestly. | Prevents lender memorization; maintains honest out-of-institution generalization metrics. Protects institutional anonymity (D-O). | Agreed |
| D-AN | 2026-11-18 | Implement Oaxaca–Blinder-style counterfactual decomposition (Part E) trained on White applicants, with reversed direction (trained on minority group $g$, scoring White) reported to document index dependence (formula amended by D-BI) | Overcomes the sparse-stratum failure of Kitagawa decomposition (D-X, D-AG). Smooth ML models pool information across high-dimensional feature spaces to decompose raw gaps into composition (explained) vs. rate/unexplained components. | Decomposes raw Black–White (+14.88 pp) and other minority gaps on test set. Enforces algebraic identity: $\text{Explained} + \text{Unexplained} = \text{Raw Gap}$ ($< 10^{-9}$). | Agreed |
| D-AO | 2026-11-18 | Employ a representative stratified subsample ($N \approx 500{,}000$, `df_samp`) for hyper-parameter grid searches, permutation feature importance, and bootstrapping; train final models and compute headline metrics on full $S0$ | Optimizes computational efficiency and memory footprint across 8.1M rows while preserving full population statistical power for final reported figures and audit tables. | Tuning accelerated ~16x; headline metrics, final coefficients, and official audit tables executed on 100% of $S0$ (8,136,664 rows). | Agreed |
| D-AP | 2026-11-18 | Prioritize ranking and calibration metrics (ROC-AUC, PR-AUC, Brier score, calibration curve) as primary evaluation criteria; determine classification thresholds on validation set (max F1, fixed-recall points) | Mortgage denial is an asymmetric diagnostic task (~24.6% base rate); default 0.5 threshold is arbitrary and inappropriate. Ranking and calibration assess probability validity independently of cutoff choice. | Ensures probability outputs are well-calibrated for audit grouping (Q-B) and counterfactual scoring (Q-C). Class metrics reported at validated optimal thresholds. | Agreed |
| D-AQ | 2026-11-18 | Exclude legally sensitive attributes (`derived_sex`, `applicant_age`, `has_coapplicant`) from predictive feature sets (M1–M3); retain strictly as audit and diagnostic grouping variables | Sex and age are protected classes under ECOA; co-applicant presence is highly correlated with race and marital status. Excluding them ensures the model functions strictly as an objective, credit-relevant benchmark. | Excluded from features across 100% of $S0$. Multi-dimensional audit profiles error rates and calibration parity across intersections of sex, age, and race. | Agreed |
| D-AR | 2026-11-18 | Standardize model fit statistics: report ROC-AUC, PR-AUC, Brier score, log-loss, calibration slope/intercept; report McFadden pseudo-$R^2$ ($1 - \text{LL}_{\text{model}}/\text{LL}_{\text{null}}$) and Tjur $R^2$ as supplementary metrics (never as classical $R^2$ variance-explained) | Logistic regression and binary classifiers have no ordinary $R^2$. Low pseudo-$R^2$ values are natural in binary credit models and must not be misinterpreted as low predictive validity or poor fit. | Prevents misinterpretation in academic and grading reviews. Establishes uniform goodness-of-fit reporting across all model specifications. | Agreed |
| D-AS | 2026-11-19 | Lender-grouped K-fold robustness (K = 5) over the lenders of train ∪ valid only (test lenders stay sequestered, D-AK), stratified by lender size bucket and balanced by application share like D-AI; models LR M3-P0 and HGB M3-P0 with hyper-parameters fixed from the primary split (as in `pred_plan.md` §3; this row was missing from `decisions.md`) | The grouped test set has a higher denial rate than train and valid `[Hypothesis: lender composition]`; one split cannot show whether conclusions depend on that draw | `B16b2-3_kfold_lender.csv`, `B16b2-3_kfold_summary.csv`; 5 folds × 2 models, about 1.29M-1.31M rows and 691-706 lenders per fold | Agreed |
| D-AT | 2026-11-19 | Headline models for the audit (Part D) and counterfactual (Part E): **HGB M3-P0 and HGB M2-P0, lender-grouped split**. Logistic Regression is kept for odds-ratio interpretation (F1) and as baseline. Random Forest is kept as the Proposal baseline. P1 models are reported as an upper-bound diagnostic only (D-AH) | HGB beats LR in every one of the 5 lender folds (paired AUC difference +0.016 to +0.021); RF is within 0.002 AUC of HGB on grouped M3-P0 but is only fitted for 3 configurations; M2→M3 adds almost nothing for HGB (grouped, P0), so showing M2 and M3 side by side is what answers P9 (race proxies in geography/lender) | Grouped valid AUC: HGB M3-P0 0.862, M2-P0 0.861; LR M3-P0 0.848; RF M3-P0 0.860 | Agreed |
| D-AU | 2026-11-19 | **Calibration offset policy:** no recalibration of the audit models. Audit tables (D1-D6, E) report (i) the absolute residual `observed − predicted` and (ii) the **residual relative to White** as the headline quantity, both with lender-cluster bootstrap intervals (D-Q). Intercept recalibration on validation is not applied | The level of predicted probability relative to the observed rate depends on which lenders are held out: across 5 lender folds `mean_pred − base_rate` runs from about −5.4 pp to +5.0 pp (HGB) and changes sign; on the primary validation set it is +2.3 pp. A fixed recalibration chosen on one validation draw would not transfer to test (different lender mix and base rate) | No rows changed; adds a relative-to-White column to D1/D4/D6 tables; calibration slope/intercept reported by group (D2) | Agreed |
| D-AV | 2026-11-19 | Fix the definition of the base-rate columns in all metric tables: `base_rate_train` (base rate of the training rows of the scheme; the McFadden null, D-AR) and `base_rate_eval` (base rate of the rows being scored); the single column `base_rate` is retired. `mcfadden_r2` uses the train null; `mcfadden_r2_evalnull` uses the evaluation null (D-AR amended) | In B16b the column `base_rate` held the validation rate for LR rows (grouped 0.2428) but the training rate for HGB/RF rows (grouped 0.2406), because `prob_metrics_b3` was called with the training rate. `mean_pred` vs `base_rate` comparisons were therefore inconsistent across algorithms | Patch cell recomputes both columns from the saved tables and asserts that the old McFadden values are reproduced; no model refit | Agreed |
| D-AW | 2026-11-19 | Random-split HGB fits are treated as **not converged** when they hit the iteration cap. Refit with cap 800 was run (2026-11-20): 6 of 7 random-split fits (including `P0+lenderTE`) still hit the cap, so Random-vs-grouped gaps (C1) and the lender-leakage reference (C9) are reported as **lower bounds**; the grouped fits (primary) are unaffected (best iteration 75-296, below the cap) | `hit_cap = True` for 6 of 7 refit fits in `B16b2-3_hgb_valid_metrics_random_refit.csv` (only M1-P0 stopped at 799); validation log-loss was still falling at the cap. The first-run gain from lender target encoding (+0.0163 AUC, cap 300) changed little after the refit (+0.0175, cap 800) | Primary results and audit unchanged; C1/C9 numbers are lower bounds (as of run 2026-11-20, B16c C1, C9). A further cap increase was not pursued: about 40 minutes per fit | Agreed (lower-bound reporting) |
| D-AX | 2026-11-19 | Part C (robustness) chỉ dùng validation; test chỉ dùng cho báo cáo headline (B16b 3b) và audit Part D/E bằng các mô hình đã khóa; random-split HGB refit (D-AW) được chạy với cap 800 trước khi báo C1/C9 | Giữ kỷ luật D-AK, tránh chọn chính sách xử lý missing theo kết quả test | D-AW chuyển từ Open sang Agreed sau khi refit; không dòng nào bị thay đổi | Agree |
| D-AY | 2026-11-20 | C4 missing-value policy: refit HGB M3-P0 on the 500k train sample (D-AO) under three policies (`explicit`, `drop`, `indicator_fill`), evaluated on the full grouped validation set. Missing-type levels: DTI `MISSING: na/exempt`, CLTV `MISSING / invalid`, income `Income missing`/`Income <= 0`, property value `PV missing`/`PV <= 0` `[Hypothesis]`. Best iteration chosen on a 200k validation subsample | Full-train refits would cost hours; all three policies use the same sample so differences come from the policy only. Validation only (D-AK, D-AX) | 3 fits; predictions saved (`row_id` only) for D6 | Agreed |
| D-AZ | 2026-11-20 | C5: score the locked HGB M3-P0 and M2-P0 on validation subsets (without / only DTI NA-Exempt, tract-NA, `fin_complete = False`); no refit | Cheap; answers "is the current model still good without those rows", not "what if it learned without them" | 2 models x 8 subsets | Agreed |
| D-BA | 2026-11-20 | C7 (state-grouped split) dropped for this run | Optional item in the plan; Human decision | none | Dropped |
| D-BB | 2026-11-20 | Audit design (Part D) on test predictions of locked models: all 9 `derived_race` groups kept, roles reference / headline / uninformative (D-L) / other; D-M suppression flag `low_n`; headline quantity = residual relative to White (D-AU) with identity raw gap = model-expected gap + relative residual (tol 1e-9); lender-cluster bootstrap B = 1,000, seed 42 on fixed predictions (D-Q); error-rate thresholds read from the validation-derived JSON (D-AP); segment cells reported only if group cell and White cell both pass D-M; D6 missing-policy sensitivity uses validation rows | Keeps test discipline (D-AK) and a consistent reading rule; no recalibration (D-AU) | Tables `B16c_audit_*.csv` | Agreed |
| D-BC | 2026-11-21 | f_W = HGB fit trên toàn bộ White train (grouped), HGB_BEST, số vòng chọn trên White valid | Ước lượng chuẩn tính điểm tín dụng của nhóm đa số làm nền tảng phản thực tế (counterfactual); số vòng dừng sớm chọn trên White valid để chống overfit và giữ kỷ luật test (D-AK) | best_iter 96 / 84 / 101, không chạm cap (as of run 2026-11-21, B16d E1b) | Agreed |
| D-BD | 2026-11-21 | 3 cấu hình: M2-P0, M3-P0, M3-P0 bỏ lender_size_bucket | M2 vs M3 phân lập vai trò địa lý; bỏ `lender_size_bucket` bóc tách mức độ phân loại ngân hàng (lender sorting) bị hấp thụ vào Explained vs hiệu ứng tỷ lệ nội bộ | B16d_cf_forward.csv | Agreed |
| D-BE | 2026-11-21 | Headline: Black, Asian, AIAN, Joint; NHPI và 2+ races báo cáo có cờ flagged | Tuân thủ D-M và D-U: NHPI và 2+ races có cỡ mẫu nhỏ hơn, phương sai lớn hơn; 4 nhóm headline đủ quy mô thống kê tin cậy | cả hai qua D-M ở test (1,480 và 1,546 từ chối) | Agreed |
| D-BF | 2026-11-21 | Support: propensity cân bằng trọng số hai lớp, White 500k, 100 vòng, ngưỡng 0.95 [Hypothesis]; báo cáo có và không lọc | Tránh ngoại suy quá mức vào vùng đặc trưng không có người nộp đơn da trắng tương đồng ($P(g \mid X) > 0.95$); cân bằng trọng số lớp và dùng White 500k train nhanh; báo cáo song song có/không lọc để minh bạch | M3-P0 flag 9.5% Black; M2-P0 flag 0 (E3a) | Agreed |
| D-BG | 2026-11-21 | Chiều ngược chỉ cho Black, Asian, AIAN, Joint | Kiểm tra độ nhạy chỉ số Oaxaca (fit trên $g$, chấm điểm White); nhóm nhỏ hơn (NHPI, 2+ races) không đủ mẫu train để fit HGB ổn định | B16d_cf_reverse.csv | Agreed |
| D-BH | 2026-11-21 | CI = bootstrap lender trên test (B=1,000, mô hình cố định) + 5 refit trên mẫu lender của White train, chỉ M2-P0 và M3-P0 (noLender không refit vì thời gian) | Bootstrap trên test với mô hình cố định nắm bắt phương sai chọn mẫu ngân hàng (D-Q, D-AU); 5 refit kiểm tra độ nhạy mô hình với phương sai huấn luyện; bỏ qua noLender refit vì chi phí thời gian | B16d_refit_*.csv (chờ chạy) | Agreed |
| D-BI | 2026-11-21 | Unexplained = (Y_g − mean_g f) − (Y_W − mean_W f); identity raw = explained + unexplained (tol 1e-9) | Sửa đổi công thức D-AN (PK-D-AN sửa) đảm bảo triệt tiêu offset hệ thống của lender draw (D-AU) khi mô hình không recalibrate; bảo toàn đẳng thức phân rã | PK-D-AN sửa; sai số tối đa 1.8e-15 | Agreed |
| D-BJ | 2026-11-21 | explained_share_pct chỉ báo cáo khi raw gap ≥ 5 pp [Hypothesis] | Tránh tỷ lệ phần trăm chia sẻ khoảng cách ($\text{explained} / \text{raw\_gap}$) bị bùng nổ hoặc đổi dấu phi lý khi khoảng cách thô gần 0 (tương tự D-U / D-X) | Asian, Joint là NaN | Agreed |
| D-BK | 2026-11-21 | Part F trên HGB M3-P0 grouped đã khóa (và M3-P1 chỉ cho khối proxies), mẫu validation 200k (D-AO), 3 lần hoán vị, đo bằng Δlog-loss và ΔAUC; hoán vị theo khối dùng cùng một hoán vị hàng cho mọi cột trong khối | Permutation importance (F2, F4) trên validation grouped tránh bias của impurity-based importance; mẫu 200k và 3 lần lặp cân đối tốc độ tính toán và độ ổn định (D-AO); hoán vị khối dùng chung một vector chỉ số hàng nhằm bảo tồn cấu trúc tương quan nội khối | Xuất bảng xếp hạng đặc trưng đơn lẻ và tầm quan trọng theo khối (`B16d_importance_*.csv`); biểu đồ Figure 31 | Agreed |
| D-BL | 2026-11-21 | `B16d_findings.csv`: `ci_lo`/`ci_hi` hold confidence intervals only; refit min/max go to `range_lo`/`range_hi`; PDP-minus-raw rows carry the caveat "possible method effect [Hypothesis, not tested]" | Prevents reading a refit range as a confidence interval; keeps the PDP reading labelled as untested | 13 columns, 50 rows (as of run 2026-11-21, B16d G2) | Agreed |

## ERRATUM & RECONCILIATION
> **Reconciliation Note (2026-11-10, B14 C1 Audit).** An earlier drafting typo in D-J and D-L quoted preliminary application counts (`White` 5,142,670; `Black` 627,749; `Race Not Available` 1,288,574). Investigation across the artifact lineage confirms that the true golden numbers produced by B05 (`B05_x11_race_selection_waterfall.csv`), B06, and B14 C1/C5 are completely unified and identical: `White` = 5,360,624 (65.88% of $S0$), `Black` = 733,103 (9.01% of $S0$), and `Race Not Available` = 1,275,240 (15.67% of $S0$). All denial rates (White 21.92%, Black 36.80%, Race Not Available 29.66%) and the Black–White gap (+14.88 pp) match perfectly across all milestones. The text below reflects the verified golden counts.

## In-Depth Explanations for Key Methodological Decisions

This section provides comprehensive methodological, mathematical, and empirical foundations for decisions that introduce advanced statistical techniques, suppression rules, or non-trivial data handling protocols.

---

### 1. Decision D-L: Treatment of Uninformative Race Categories (`Race Not Available` & `Free Form Text Only`)

#### Background and Context
In the CFPB HMDA reporting standards, `derived_race` aggregates borrower race disclosures into 9 categories. Two of these categories lack definitive racial identity:
- **`Race Not Available`**: Assigned when applicants elect not to provide race information (e.g., mail, internet, or telephone applications where visual observation is impossible) or when lenders fail to collect required demographic data.
- **`Free Form Text Only`**: Assigned when applicants submit narrative text in the open text field that does not match any standard FFIEC racial taxonomy code.

#### Empirical Rationale
In the Analytic Sample ($S0$, 8,136,664 applications; run 2026-10-31, B05 cell 39 / B06 / B14 C1):
- **White denial rate**: $21.92\%$ (5,360,624 applications, 65.88% of $S0$)
- **Black denial rate**: $36.80\%$ (733,103 applications, 9.01% of $S0$)
- **Race Not Available denial rate**: $29.66\%$ (1,275,240 applications, 15.67% of $S0$)

The observed denial rate of $29.66\%$ sits almost exactly midway between the White benchmark ($21.92\%$) and the Black benchmark ($36.80\%$). This empirical positioning indicates that `Race Not Available` is a latent mixture of White, Black, Hispanic, Asian, and other demographic groups who disproportionately use digital or broker channels.

#### Methodological Consequences of Misclassification
1. **Merging into White**: Artificially inflates the White denial rate ($21.92\% \rightarrow \approx 23.41\%$), thereby compressing the true Black–White and Hispanic–White disparity gaps by $\approx 1.5\text{ pp}$.
2. **Merging into Minorities**: Distorts minority-specific denial profiles, dilutes historical disparity trends, and assumes an unverified demographic identity without evidentiary support.
3. **Dropping Rows**: Violates population integrity by discarding $15.67\%$ of all mortgage applications, distorting market-wide origination totals and lender volume metrics.

### 2. Decision D-M: Statistical Reliability and Minimum Cell Size Suppression Rules (`N_MIN_APPS` & `N_MIN_DENIED`)

#### Concept of a "Cell" and Small-Sample Noise
A "cell" is defined as a specific granular slice or intersection of the dataset—for example:
$$\text{Cell}_{ij} = \{ \text{Race} = i \} \times \{ \text{State} = j \}$$
or an intersection across $(\text{Lender} \times \text{Race} \times \text{Loan Type})$.

When a cell contains very few observations, empirical denial rates suffer from severe small-sample variance. For example:
- Consider a cell with $N = 20$ applications and $d = 5$ denials ($\hat{p} = 25.0\%$).
- Its 95% Wilson score confidence interval spans from **$11.2\%$ to $46.9\%$**—a margin of error exceeding $\pm 17.8\text{ pp}$.
- If state rankings or lender outlier tables rely on such cells, the top and bottom ranks will be entirely dominated by sample noise (extreme lottery outcomes) rather than structural disparities.

#### Precision Calibration and Dual Threshold Rule
To ensure that every reported rate and ranking has meaningful statistical precision, Decision D-M enforces two joint conditions:
1. **$N_{\text{total}} \ge N_{\text{MIN\_APPS}} = 1,000$**
2. **$d \ge N_{\text{MIN\_DENIED}} = 100$**

#### Statistical Justification
Under a normal approximation to the binomial distribution with sample proportion $\hat{p} \approx 0.24$ (the market baseline) and $N = 1,000$:
$$\text{SE}(\hat{p}) = \sqrt{\frac{\hat{p}(1-\hat{p})}{N}} = \sqrt{\frac{0.24 \times 0.76}{1,000}} \approx 0.0135 \quad (1.35\text{ pp})$$
The corresponding 95% confidence interval margin of error is:
$$\text{MoE}_{95\%} \approx 1.96 \times 1.35\text{ pp} \approx \pm 2.65\text{ pp}$$

A margin of error of $\approx \pm 2.6\text{ pp}$ ensures that differences of $5\text{ pp}$ or larger between states or lenders reflect genuine structural disparities rather than sampling noise. Cells failing either threshold are visually suppressed (greyed or omitted) in scatter/funnel plots and explicitly flagged with `low_n = True` in data tables.

---

### 3. Decision D-N: Scope of Analysis Samples (Analytic Sample $S0$ vs. `clean_all` vs. Subsamples)

#### Baseline Sample Definition
The primary empirical frame for all exploratory analysis in B14 is the **Analytic Baseline Sample ($S0$, `B06_analytic.parquet`)**, comprising **8,136,664** rows. $S0$ is constructed from the raw dataset (12,259,199 rows) through three sequential statutory filters:
1. **F01**: Valid action taken (`action_taken` $\in \{1, 2, 3\}$: originated, approved but not accepted, or denied). Denominator for denial rate.
2. **F02**: Consumer-purpose loans only (`business_or_commercial_purpose != '1'`).
3. **F03**: Exclude reverse mortgages (`reverse_mortgage != '1'`).

#### Why Full EDA is NOT Performed on `clean_all`
The dataset `B06_clean_all.parquet` contains **12,259,199** rows, retaining commercial-purpose loans, reverse mortgages, withdrawn applications, and files closed for incompleteness.
- **Underwriting Divergence**: Commercial loans are underwritten based on commercial cash flow, tenant occupancy, and debt-service coverage ratio (DSCR). Reverse mortgages are equity-conversion products available only to older homeowners ($62+$) without monthly debt service payments.
- **Conflation Risk**: Profiling income distributions, loan-to-value ratios, or denial rates across `clean_all` would conflate commercial corporate borrowers with individual residential homebuyers, producing corrupted and misleading baseline distributions.
- **Target Population**: All research questions (RQ1–RQ4) explicitly target consumer residential mortgage disparities.
- **Role of `clean_all`**: `clean_all` is utilized strictly for **lightweight selection audits**. A minimal set of columns (`row_id`, `action_taken`, `derived_race`, `in_s0`, filter flags) is queried to verify that statutory exclusions (F01–F03) drop applications at equal or proportionate rates across demographic groups, proving absence of selection bias at the filtering boundary.

#### Side-by-Side Multi-Sample Reporting
To prevent sample attrition from confounding disparity findings, B14 presents core demographic denial tables with side-by-side columns:
- **Baseline $S0$**: Full consumer analytical frame ($N = 8,136,664$).
- **Financial Complete Sample (`fin_complete`)**: Subsample with non-missing financial covariates (DTI, income, CLTV, property value).
- **RQ3 Geographic Sample**: Subsample meeting $S0 \cap \text{fin\_complete} \cap \text{valid\_tract}$ ($N \approx 5.3\text{M}$ rows; excludes 96,065 missing-tract records per Decision D-I).
- **Robustness Samples ($S5$)**: Sensitivity variants evaluating the impact of non-positive income (`S5_all` vs. `S5_keep_v02` per Decision D-B).

---

### 4. Decision D-O: Institutional Anonymization for Lender Heterogeneity (LEI Masking)

#### Regulatory and Ethical Imperative
Under HMDA, every reporting institution is identified by its 20-character alphanumeric Legal Entity Identifier (LEI). The course project assignment guidelines (§5) explicitly mandate:
> *"Students must avoid drawing unsupported, definitive claims regarding individual financial institutions."*

Publicly asserting that an individual named lender (e.g., Bank of America, Rocket Mortgage, Wells Fargo) "discriminates" or has an excessive denial rate based on raw observational data is methodologically invalid and ethically improper.

#### Sources of Confounding in Raw Lender Denial Rates
A raw disparity between two lenders is heavily influenced by non-institutional factors:
1. **Applicant Self-Selection**: Lenders specialized in government-backed lending (FHA/VA) intentionally serve lower-income, first-time, or credit-building borrowers who exhibit higher market-wide denial rates.
2. **Geographic Footprint**: Lenders operating primarily in economically depressed MSAs or regions with volatile appraisal markets naturally experience higher denial rates.
3. **Channel Sorting**: Wholesale/broker channels present distinct underwriting risk profiles compared to direct retail branch networks.

#### Anonymization Protocol
- In all visualizations, regression outputs, and report tables, lenders are designated strictly via synthetic sequential codes:
  $$\text{Lender ID} \in \{ \text{L001}, \text{L002}, \text{L003}, \dots \}$$
  ranked deterministically by application volume.
- The lookup table mapping LEI codes and legal corporate names to synthetic IDs is generated in-memory or stored strictly in confidential workspace scratch directories, never exported into public deliverables or final report artifacts.

---

### 5. Decision D-P: Kitagawa Direct Standardization Decomposition (Exploratory Gap Partitioning)

#### Nature of the Technique: Arithmetic Identity vs. Model
The Kitagawa decomposition (Kitagawa, 1955; mathematically equivalent to a two-component Oaxaca-Blinder decomposition without unobservables) is an **exact algebraic accounting identity**. It does not assume any functional form, logistic link, or error distribution.

#### The Problem It Solves
Suppose the overall denial rate for Black applicants is $\bar{Y}_B = 36.80\%$ and for White applicants is $\bar{Y}_W = 21.92\%$, yielding a raw gap:
$$\Delta = \bar{Y}_B - \bar{Y}_W = 36.80\% - 21.92\% = +14.88\text{ pp}$$

This disparity arises from two fundamentally different sources:
1. **Composition (Endowment / Mix) Effect**: Black and White applicants apply for different loan products (e.g., FHA vs. Conventional) or possess different financial profiles (e.g., DTI $> 45\%$). Because certain loan types have inherently higher rejection rates, demographic differences in application mix create a mechanical disparity.
2. **Rate (Within-Strata) Effect**: Even within the *exact same* loan product category and financial stratum, Black applicants may experience higher denial rates than White applicants.

#### Algebraic Formulation
Let the market be partitioned into $K$ mutually exclusive and exhaustive strata (e.g., $K = 4$ loan types: Conventional, FHA, VA, USDA; or $K$ joint bins of Loan Type $\times$ DTI Category).

For demographic group $g \in \{B, W\}$:
- Let $w_k^g = \frac{N_k^g}{N^g}$ denote the proportion of group $g$ applications falling into stratum $k$ ($\sum_{k=1}^K w_k^g = 1$).
- Let $r_k^g$ denote the empirical denial rate within stratum $k$ for group $g$.

The overall group denial rate is the weighted average across all strata:
$$\bar{Y}_g = \sum_{k=1}^K w_k^g r_k^g$$

The observed gap $\Delta = \bar{Y}_B - \bar{Y}_W$ is decomposed using symmetric average weights:
$$\bar{w}_k = \frac{w_k^B + w_k^W}{2}, \qquad \bar{r}_k = \frac{r_k^B + r_k^W}{2}$$

The Kitagawa decomposition partitions $\Delta$ exactly:
$$\Delta = \sum_{k=1}^K \bar{r}_k \left( w_k^B - w_k^W \right) + \sum_{k=1}^K \bar{w}_k \left( r_k^B - r_k^W \right)$$
$$\Delta = \text{Composition Effect} + \text{Rate Effect}$$

Where:
- **Composition Effect** $= \sum_{k=1}^K \bar{r}_k (w_k^B - w_k^W)$: Measures how much of the gap would persist if both groups experienced the average within-strata denial rates, but retained their actual product/financial mix.
- **Rate Effect** $= \sum_{k=1}^K \bar{w}_k (r_k^B - r_k^W)$: Measures how much of the gap would persist if both groups had the exact same average product/financial distribution, but retained their actual group-specific denial rates within each stratum.

#### Diagnostic Role in Milestone B14
The Kitagawa decomposition answers step (a) of the Main Research Question directly from descriptive cross-tabulations. It provides an immediate benchmark indicating what portion of the raw racial gap is accounted for by product sorting vs. within-product rate differentials, establishing the empirical foundation for the formal sequential regression models developed in subsequent milestones.

---

### 6. Decision D-Q: Statistical Inference in Massive Datasets (Wilson Intervals, Cluster Bootstrap, and P-Value Traps)

#### The Big Data "P-Value Trap" ($N > 8\text{ Million}$)
In traditional econometric studies with small samples ($N \sim 1,000$), hypothesis testing relies heavily on $p$-values to determine whether an observed difference is statistically distinguishable from zero.
In contrast, in the HMDA 2024 Analytic Sample ($N = 8,136,664$):
$$\text{SE} \propto \frac{1}{\sqrt{N}} \approx \frac{1}{\sqrt{8,136,664}} \approx 0.00035$$
Under standard asymptotic tests, a completely trivial, economically meaningless difference of $0.05\text{ pp}$ ($0.0005$) produces test statistics of:
$$z = \frac{0.0005}{0.00035} \approx 1.43, \qquad \text{or for } 0.1\text{ pp}, \quad z \approx 2.85 \quad (p < 0.004)$$
Virtually every null hypothesis is rejected at $p < 10^{-10}$. In big data analytics, reporting tables filled with asterisks ($^{***}$) provides zero substantive information. Therefore, Decision D-Q mandates:
- **Suppression of Asymptotic P-Values**: Tables report effect sizes (percentage point gap $\Delta$, disparity ratio, odds ratio).
- **Interval Estimation**: All point estimates are accompanied by rigorous confidence intervals that reflect true economic and institutional uncertainty.

#### Failure of I.I.D. Assumptions and Institutional Clustering
Standard confidence intervals assume that all $8.1\text{M}$ applications are independent and identically distributed (i.i.d.).
In reality, mortgage applications are heavily clustered within financial institutions:
- Each lender maintains proprietary automated underwriting systems (AUS), custom credit overlays, specific risk tolerances, and localized branch operations.
- Two applications submitted to the same lender share common institutional shocks and underwriting policies.
- Assuming i.i.d. observations dramatically underestimates standard errors, producing falsely tight, overconfident confidence intervals.

#### Computational Innovation: Lender-Cluster Bootstrap
To account for within-lender correlation without incurring prohibitive computational cost across $8.1\text{M}$ raw rows, Decision D-Q introduces a **pre-aggregated lender-cluster bootstrap**:
1. **Pre-Aggregation**: The raw dataset is grouped into summary counts by $(\text{Lender} \times \text{Race})$:
   $$\text{Summary Table: } \{ \text{LEI}_j, \text{Race}_i, N_{ji}, d_{ji} \}$$
   Across $\sim 5,000$ active lenders and 9 race groups, this aggregated matrix contains only $\sim 25,000$ to $40,000$ rows, easily fitting in cache memory.
2. **Lender Resampling**: For $b = 1, \dots, B$ (with $B = 1,000$ iterations and fixed seed 42):
   - Sample $M$ lenders with replacement from the unique set of $M \approx 5,000$ lenders.
   - Aggregate the total applications and denials across the sampled lenders for each racial group.
   - Recompute the headline disparity metrics (e.g., $\Delta_{\text{Black-White}}^{(b)}$, $\text{OR}_{\text{Black-White}}^{(b)}$).
3. **Percentile Confidence Intervals**:
   The $95\%$ cluster-robust confidence interval is computed directly from the empirical $2.5^{\text{th}}$ and $97.5^{\text{th}}$ percentiles of the $1,000$ bootstrap replicates:
   $$\text{CI}_{95\%} = \left[ \Delta_{(0.025)}^{*}, \Delta_{(0.975)}^{*} \right]$$
4. **Computational Performance**: Because resampling operates on the pre-aggregated summary table rather than the $8.1\text{M}$ individual rows, $1,000$ cluster bootstrap iterations execute in seconds while capturing institutional clustering.

#### Proportion Confidence Intervals: Wilson Score Interval
For univariate and bivariate denial rates $\hat{p} = \frac{d}{n}$, the standard Wald confidence interval:
$$\text{CI}_{\text{Wald}} = \hat{p} \pm 1.96 \sqrt{\frac{\hat{p}(1-\hat{p})}{n}}$$
suffers from known pathology: it can produce limits outside $[0, 1]$ when proportions are extreme, and has poor coverage probability when $n$ is moderate.
Decision D-Q mandates the **Wilson score interval** (Wilson, 1927):
$$\text{CI}_{\text{Wilson}} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
Where $z = 1.96$ for a $95\%$ confidence level. The Wilson score interval is asymmetric, bounded strictly within $[0, 1]$, and maintains exact nominal coverage across both large and moderate cell sizes.

---

### 7. Decision D-V: Financial Bins for Part D (CLTV, LTI, Income Deciles, Missing Categories)

#### Why bins are needed
DTI is published in bins (with integer points 36–49), while CLTV, income and loan-to-income are continuous. Stratified analyses (denial curves, DTI × CLTV surfaces, stratified Kitagawa) require discrete **strata**, so a fixed, documented bin scheme is needed. Bin choices are analysis decisions: they change the strata, and therefore the composition/rate split of any gap.

#### CLTV bins and heaping
Lenders cluster loans at round LTV thresholds tied to mortgage-insurance and pricing rules (80, 95, 97, 100). A smooth bin width would hide these spikes. D-V gives exactly 80 its own bin (`=80`, edges 79.999 to 80), and the other thresholds close the interval on the right (e.g. 90–95 includes 95). CLTV ≤ 0 violates rule V03 and is mapped to `MISSING / invalid` instead of the lowest numeric bin, so invalid values never look like low leverage.

#### Income deciles
Income is strongly right-skewed (as of run 2026-11-10, B14 D0: median about 105, p90 258, maximum 100,000,000, all in $1,000s). Deciles are **quantile bins**: each holds about 10% of valid-income rows in S0, so every income stratum has volume, whatever the tail looks like. They are computed on **positive** income only; `Income <= 0` (rule V02) and `Income missing` are separate levels, because their denial profiles are very different (Decision D-B). Deciles are a property of S0: they must be recomputed if the sample changes (S5, `fin_complete`).

#### Missing values as categories
Missingness in DTI, income and CLTV is informative (Assumption A8, tested in D6): rows with missing data have different denial rates and race mix. Dropping them is a selection step; imputing them invents values. D-V keeps them as explicit categories (`MISSING: na`, `MISSING: exempt`, `Income missing`, `MISSING / invalid`), so every table sums to S0 and the selection stays visible.

#### Consequences and limits
- More and finer bins give smaller cells; Decision D-M then removes or pools them (see D-U/D-X).
- A bin is a proxy: two applicants in the same DTI × CLTV × income cell can still differ on credit score or assets (unobserved).
- `dti_mid` (bin midpoint) is used **only** for correlation/SMD diagnostics, not as a measured DTI.

---

### 8. Decisions D-W and D-X: Extreme Income and Reliability of Stratified Decompositions

#### D-W: the $100 billion income
`income` is reported in thousands of dollars, so a value of 100,000,000 means $100 billion, which is implausible for an individual applicant. It could be a keying error or a placeholder, but this cannot be verified from public HMDA. Under the project principles ("flag, do not delete"), B14 adds a **diagnostic flag** above $10M (`[Hypothesis: threshold]`) and reports results with and without those rows. The flag changes no row in S0 and does not require re-running B06. It matters most for **means, correlations, VIF and SMD**, which are not robust to a single extreme value; deciles and medians are barely affected.

#### D-X: why pooled Kitagawa results are not headline estimates
Decision D-U pools strata that fail D-M into one "Other" stratum per comparison pair. In Part D, the pooled share exceeds 10% for every group in both specifications, and 100% for two groups (no stratum kept). When most of a group sits in the pooled stratum, the **composition** inside that stratum (differences in DTI, CLTV, income between the groups) is counted as **rate**. So the reported "rate effect" tends to be too large, and for groups with 0 kept strata it equals the raw gap by construction `[Hypothesis: direction; not guaranteed with symmetric weights]`. D-X therefore says: such decompositions are **not** reported as estimates; headline conclusions rest on the raw gap with its lender-cluster interval (D-Q) and on lender-level and subgroup consistency checks. A coarse specification (3–5 groups per variable) is run as a robustness check.

#### D-AG (B14): the same rule applied to lenders
In F8 the stratum is the lender. Lenders failing D-M are pooled into one "Other (pooled)" stratum per comparison pair. The pooled stratum holds most lenders (4,678 to 4,776 per pair) and a pooled share (max of group and White) of 44.10% to 100%, so differences in which small lenders each group applies to are counted as "rate" (same mechanism as D-X). The composition figure (+2.69 pp for Black) is then not interpretable either. F9 avoids pooling by keeping only lenders where both groups pass D-M, at the cost of coverage (30.62% of AIAN to 69.82% of Black applications) and of excluding small lenders. It is therefore always reported together with `coverage_pct` and describes those lenders only.

### Decision D-Y: Treatment of `aus_1` and `applicant_credit_score_type`

#### What the fields are (and are not)
- `aus_1` records **which automated underwriting system** was used for the application (up to five systems can be reported in `aus_1..aus_5`). It does **not** record the system's recommendation.
- `applicant_credit_score_type` records **which credit scoring model** was used. It does **not** record the score.
- Public HMDA therefore contains no credit score value, no AUS result, no assets and no application dates (Assumption A5; table `B14_rq4_missing_variables.csv`). These two fields are the closest public proxies, but they are proxies for *process*, not for borrower risk.

#### Why they are not in the main specification
1. **They are not credit risk.** The choice of AUS or score model is made by the lender or driven by the loan program (for example, government-backed versus conventional) and by the submission channel. Adding them to a model absorbs lender and product sorting rather than measuring the borrower's credit quality.
2. **Possible dependence on the outcome (leakage).** Special values (`Not applicable`, `Exempt`/`1111`) may be reported differently for denied and approved files. Audit A3 measures the share of non-missing values among denied versus non-denied applications; a gap above 50 pp makes the field unusable as a control.
3. **Bad control (post-treatment) risk.** If AUS or score-model choice is itself correlated with race through lender or broker sorting, "controlling" for it can remove part of a gap that comes from that sorting. A narrower gap would then not mean the gap is "explained"; it would mean part of it was moved into the control `[Hypothesis]`.

#### What we do instead
- The sequential framework (raw gap, product, financial profile, geography and lender) is run **without** these fields.
- A separate specification adds them and is reported next to the main one in the RQ4 robustness section. The comparison answers: "how much does the remaining gap change when process proxies are added?"
- Interpretation stays descriptive. A remaining gap is never read as discrimination, because the true underwriting variables (credit score value, AUS result, assets) are unobserved in both specifications.

#### Alternative considered
Excluding the fields entirely was rejected: it would hide a sensitivity result that readers of a fair-lending analysis expect to see, and it would remove the only public information on underwriting process.

- Dictionary note: the data dictionary lists `applicant_credit_score_type` codes 1-9 and 1111 for the applicant, but codes 11-15 also occur in the 2024 file (B16c C2: e.g. code 14 has a 75.38% denial rate). The co-applicant list assigns them FICO Score 9 (11), FICO Score 8 (12), FICO Score 10 (13), FICO Score 10T (14) and VantageScore 4.0 (15); the same meaning is assumed for the applicant field `[Hypothesis]`.
---

### 10. Decision D-AB: Structural Redundancy of `conforming_loan_limit = NA` and Multifamily Dwellings (`5+` Units)

#### Background and Empirical Audit
In the CFPB HMDA schema, `conforming_loan_limit` indicates whether a loan falls within the Federal Housing Finance Agency (FHFA) conforming dollar limit (`C` = Conforming, `NC` = Non-Conforming/Jumbo, `U` = Undetermined, `NA` = Not Applicable). Under FHFA statutory rules, conforming loan limits apply strictly to 1-to-4 unit residential properties; multifamily properties (`total_units` $\ge 5$, i.e., `5-24`, `25-49`, `50-99`, `100-149`, `>149`) have no FHFA conforming limit and are assigned `NA`.

A cross-tabulation in Milestone B14 (Step B5 check cell, as of run 2026-11-10) across all 8,136,664 $S0$ applications confirms an exact 1-to-1 identity `[Verified: B14 B5 check]`:
- All **9,440** rows with `conforming_loan_limit == 'NA'` have `total_units` $\ge 5$ (0 rows have 1–4 units).
- All **8,127,224** rows with `conforming_loan_limit` $\in \{\text{'C'}, \text{'NC'}, \text{'U'}\}$ have `total_units` $\le 4$ (`C`: 7,903,790; `NC`: 223,141; `U`: 293).
- Total disagreements between `(conforming_loan_limit == 'NA')` and `(total_units >= 5)` equal **0 rows**.

#### Methodological Consequences for Sequential Modeling
1. **Avoiding Perfect Multicollinearity:** Including both `conforming_loan_limit` (with level `NA`) and a multifamily dummy (or `derived_dwelling_category` levels `'Multifamily:Site-Built'` and `'Multifamily:Manufactured'`) in Step 2 product controls creates an exact linear dependency ($\text{Dummy}_{\text{NA}} \equiv \text{Dummy}_{\text{5+ units}}$), causing rank deficiency in design matrices. Therefore, `conforming_loan_limit = 'NA'` serves as the sole multifamily indicator when `conforming_loan_limit` is included.
2. **Preserving Level `'U'` Separate from `'NA'`:** Code `'U'` (293 applications, denial rate 32.42%) consists entirely of 1–4 unit properties with undetermined conforming status. Merging `'U'` into `'NA'` (denial rate 6.39%) would contaminate commercial-style 5+ unit multifamily loans with 1–4 unit residential loans. `'U'` is retained as a distinct factor level in models and flagged `low_n = True` ($293 < 1,000$) in descriptive tables under Decision D-M.

---

### 11. Step B4b & Decision D-AC: Diagnostic Verification of Originated-Loan Pricing Hypotheses (H1–H5) and Usable-Rate Suppression (`n_rate_usable`)

#### Motivation
Step B4 revealed four empirical anomalies among originated loans (`action_taken == '1'`, $N = 5,793,597$): (i) elevated unusable interest rates in Conventional (6.11%) and USDA (8.79%) loans; (ii) 24.87% missingness in `total_loan_costs`; (iii) a spike of exact zero values ($\ge 5\%$) in `total_loan_costs`; (iv) a wide interquartile range (IQR = 1.65 pp) in Conventional interest rates relative to government-backed loans (0.75–1.00 pp); and (v) a median FHA closing cost ($11,394) more than double the Conventional median ($4,855). Step B4b (`B14_pricing_by_segment.csv`, `B14_pricing_missing_attribution.csv`, Fig 07b; as of run 2026-11-10) tests five structural hypotheses (H1–H5) by segmenting originated loans across `loan_type`, `lien_status`, `open_end_line_of_credit`, and `loan_purpose`.

#### Hypothesis Audit Matrix (H1–H5)

| ID | Hypothesis in Step B4 | Expected Pattern if True | Empirical Evidence in B4b (as of run 2026-11-10) | Verdict & Status |
|---|---|---|---|---|
| **H1** | Unusable rates in Conventional (6.11%) and USDA (8.79%) come from zero-rate loans (Rule V04) and subordinate liens | `pct_rate_v04` is high in `lien_status = 2` and open-end lines | Partially supported, but the primary driver is S.2155 statutory exemption: V04 zero-rate loans concentrate in **subordinate closed-end** loans (`pct_rate_v04 = 9.42%`) and are rare in open-end lines (`0.77%`). However, **75% of all unusable Conventional rates** come from `open_end_line_of_credit = '1111'` (Exempt filers), where **99.80%** of rates are missing. In USDA subordinate liens, **71.71%** of rates are missing (`NA`), not V04. | `[Verified: B14 B4b]` (Refined: Exempt `'1111'` + subordinate closed-end V04) |
| **H2** | `total_loan_costs` is missing on 24.87% of originated loans because open-end lines of credit (HELOCs) are exempt from reporting closing costs | `pct_cost_missing` is near 100% in open-end and low in closed-end | **100.00%** of open-end originated loans (`1: Open-End HELOC`) have missing `total_loan_costs`. Across all missing cost rows on originated loans, **73.3%** are open-end lines, **14.4%** are S.2155 exempt filers (`1111`), and only **12.3%** occur in non-exempt closed-end loans (`B14_pricing_missing_attribution.csv`). | `[Verified: B14 B4b]` (Confirmed) |
| **H3** | Exact zero `total_loan_costs` (`$0`) is a product-specific phenomenon rather than uniform lender misreporting | `pct_cost_zero_of_valid` varies sharply across product segments | Strongly product-specific: among valid reported costs, exact `$0` accounts for **39.51%** of subordinate closed-end loans and **47.69%** of Conventional home-improvement loans, compared to just **1.66%** in first-lien closed-end loans and **0.10%** in FHA loans. (Within-segment lender reporting heterogeneity remains a secondary `[Hypothesis]`.) | `[Verified: B14 B4b]` (Confirmed at product level) |
| **H4** | The wide IQR of Conventional interest rates (1.65 pp) is driven by pooling first liens with subordinate liens, HELOCs, and diverse loan purposes | Interest-rate IQR in first-lien closed-end Conventional loans is much narrower than in subordinate / open-end segments | Pooling artifact confirmed: across all originated loans, rate IQR is **0.87 pp** for first-lien closed-end vs. **1.41 pp** (first-lien open-end), **2.01 pp** (subordinate closed-end), and **2.20 pp** (subordinate open-end). Restricting Conventional loans to first liens yields an IQR of **0.80 pp**—just as tight as FHA (**1.00 pp**), VA (**0.88 pp**), and USDA (**0.75 pp**). | `[Verified: B14 B4b]` (Confirmed) |
| **H5** | High FHA median closing costs ($11,394 vs. $4,855 Conventional) are an artifact of loan-purpose mix (purchase vs. refinance/HELOC) | If driven by mix, FHA costs will be similar to Conventional within the same purpose; if structural, FHA median cost will exceed Conventional across every `loan_purpose` | Structural program difference, **not** purpose mix: FHA median `total_loan_costs` exceeds Conventional in every single loan purpose (e.g., Home Purchase: **$11,419** FHA vs. **$5,509** Conventional). VA Cash-Out Refinance also reaches **$12,362** (matching FHA), pointing to financed upfront government mortgage insurance / funding fees `[Hypothesis: upfront MIP/funding fee inclusion]`. | `[Verified: B14 B4b]` (Mix hypothesis rejected; program-fee `[Hypothesis]` retained) |

#### Rationale for Decision D-AC (`n_rate_usable` and `low_n_rate` in `seg_table`)
In Step B4b, `seg_table` initially flagged small segments using only `low_n = (n_originated < N_MIN_APPS)`. However, when a segment has high rate missingness (such as `open_end_line_of_credit = '1111'` with 99.80% missing rates), `n_originated` can easily exceed 1,000 while the number of valid, non-V04 interest rates (`n_rate_usable`) is only a few dozen. Computing `n_rate_usable = g["rate_ok"].count()` and `low_n_rate = (n_originated < N_MIN_APPS) | (n_rate_usable < N_MIN_APPS)` directly inside `seg_table` guarantees exact integer counts in `B14_pricing_by_segment.csv` without reconstructing counts from rounded percentages in downstream plotting cells.

### 12. Decision D-AD: Denial Reasons as Denials per 100 Applications
 
#### The problem with shares among denied applications
`denial_reason_1..4` exist only for denied applications. The natural first table is "of the denied applications of group g, what share cite reason r", written $s_r^g$. These shares add to 100% within a group, which hides the fact that the groups have different numbers of denials to share out. Let $\bar{Y}_g$ be the denial rate of group g. The same share of a larger denial rate is a larger number of denials per application.
 
#### Definition
For group $g$ and reason $r$, the contribution is
$$c_r^g = s_r^g \times \bar{Y}_g$$
the number of denials with primary reason $r$ per 100 applications of group $g$ when $\bar{Y}_g$ is in percent.
 
Because every denied application has exactly one primary reason (`denial_reason_1`, including the codes `1111`, `10` and a blank row for completeness), the shares partition the denials:
$$\sum_r s_r^g = 1 \quad\Rightarrow\quad \sum_r c_r^g = \bar{Y}_g$$
so for a reference group $W$:
$$\bar{Y}_g - \bar{Y}_W = \sum_r \left(c_r^g - c_r^W\right)$$
The raw gap splits **exactly** into one term per primary reason. The code asserts this for every race against `C1`. The any-of-4 version counts a denial once for each reason it cites; a file can cite up to four, the shares add to more than 100%, and the differences overlap and do not add up. It is reported as a sensitivity and never summed.
 
#### Worked example (as of run 2026-11-11, B14 D7c)
| | Black | White |
|---|---|---|
| Denial rate | 36.80% | 21.92% |
| DTI as primary reason, share of denied | 31.08% | 33.09% |
| DTI, per 100 applications | 11.43 | 7.25 |
| Credit history, share of denied | 35.81% | 27.61% |
| Credit history, per 100 applications | 13.18 | 6.05 |
 
The DTI *share* is lower for Black applicants, so reading the shares alone suggests "no DTI difference". Per 100 applications the difference is +4.18 pp, 28.10% of the raw gap. Credit history is +7.13 pp, 47.90%. Together they are 76.0% of the raw gap; the other nine primary reasons are 24.0%.
 
#### What the table is and is not
- It is accounting: where the extra denials of the group with the higher rate are recorded.
- It is not a counterfactual. If the credit-history reason were absent, some of those files would still be denied for another reason. So "47.90% of the gap" is not "the gap would fall by 47.90% with better credit".
- Reasons are reported by the lender, after the decision, and the lender chooses which reasons to report and in which order `[Hypothesis about reporting practice]`. A reason is therefore not a measured credit score. The reasons are never used as predictors (A6, A3).
- Still, the table is the only public information on what the denials were about. It limits two readings: "observed DTI explains the gap" (DTI is 28.10%) and "unobserved credit history explains the gap" (credit history is 47.90%, and 24.0% is other reasons).
#### Alternatives considered
1. **Shares among denied only** (the earlier text): rejected, because they mislead as shown above.
2. **A model of denial using the reasons as predictors:** rejected, because reasons are post-decision (leakage).
3. **Shapley-type split of the any-of-4 overlaps:** not needed; the primary version is already exact, and a split of overlaps would add assumptions.
---
 
### 13. Decision D-AE: Denial Curves within Product Segments (Simpson-Type Check for Part D)
 
#### The problem
All-S0 denial rates by DTI or CLTV bin average over products with very different base rates. The overall rate in bin $b$ is
$$\bar{Y}_b = \sum_s w_{s|b}\, r_{s,b}$$
where $s$ is a product segment, $w_{s|b}$ is the share of segment $s$ among applications in bin $b$, and $r_{s,b}$ is the denial rate of segment $s$ in bin $b$. The shape of $\bar{Y}_b$ across bins can come from $r_{s,b}$ changing with the bin, from $w_{s|b}$ changing with the bin (segments are distributed differently across bins), or both. Part D asks the first question; the all-S0 curve cannot separate it from the second.
 
#### Evidence that mix matters here (as of run 2026-11-10, B14 B5 and D3)
- All-S0 denial is 28.43% at CLTV <= 60 and 29.21% at DTI below 20, but in first-lien purchase the rate at CLTV <= 60 is only 3.9–6.7% (D3).
- Subordinate liens are 28.90% of S0 with 35.85% denial against 20.06% for first liens, and open-end lines of credit are 22.26% of S0 with 36.34% denial (B5). Low CLTV and low DTI on a small second lien or credit line are plausible reasons for the high all-S0 rates `[Hypothesis]`.
- D3 cannot settle it: it covers first liens only, and even there DTI below 20 has 33.8–44.1% denial at CLTV above 95 (purchase) and 41.53% at CLTV = 80 (refinance).
#### Specification
- **Segments (a partition of S0):** (1) first lien, purchase (`loan_purpose = 1`); (2) first lien, refinance (31, 32); (3) first lien, other purpose (2, 4, 5); (4) subordinate lien, closed-end; (5) open-end line of credit, any lien. The order of rules is open-end first, then lien, then purpose, so no row is in two segments; a row with a missing `lien_status` or `open_end_line_of_credit` goes to a level "Unclassified" that is shown, not dropped (D-V). This segment definition is proposed here `[Hypothesis]`; the segmentation of B4b (`loan_type` × `lien_status` × `open_end_line_of_credit`) is the model for it.
- **Bins:** exactly the D-V bins, unchanged.
- **Outputs per segment × bin:** applications, denials, denial rate, Wilson CI, `low_n` (D-M), and the segment share $w_{s|b}$.
- **Checks (asserted):** segment counts add up to S0; for every bin, $\sum_s w_{s|b}\,r_{s,b}$ equals the all-S0 rate of the bin; segment rates are in 0–100%.
#### Pre-specified reading rules `[Hypothesis: thresholds]`
Fixing the rules before the run avoids reading the answer after seeing it.
- **CLTV <= 60:** product mix is a sufficient explanation if, in both first-lien closed-end segments (purchase, refinance), the rate in the CLTV <= 60 bin is not above the rate of the same segment across all CLTV bins by more than 5 pp.
- **DTI below 20:** product mix is a sufficient explanation if, in the same two segments, the rate in the DTI < 20 bin is not above the rate in the 20–<30 bin by more than 5 pp. If it is above in a first-lien segment, the elevated rate is reported as unexplained by product mix and is carried to the limitations of D2/D3 as such.
- **Share check:** $w_{s|b}$ is reported for the two bins, so the reader can see directly how much of the all-S0 elevation comes from segment shares.
- If the two readings disagree between purchase and refinance, both are reported; no pooled sentence is written.
#### What this does not do
- It does not decompose the Black–White gap by segment; that stays with the raw gap, C5 and G2 (D-X). Race × segment × bin is optional and subject to D-M.
- It does not add controls; it describes.
#### Implementation note (Pandas / PySpark, Convention 4.6)
Segment is built with a `np.select` chain on `open_end_line_of_credit`, `lien_status`, `loan_purpose`; in PySpark with the same chain in `F.when(...).otherwise(...)`. The aggregation is `groupBy(segment, bin).agg(count, sum(is_denied))`. Pandas needs `observed=True, dropna=False` (plan risk 9); Spark keeps NULL groups by default.
 
---
 
### 14. Decision D-AF: Handling the Collinear Block (Loan Amount, Income, LTI, LTV)
 
#### What VIF measures
For control $j$ the variance inflation factor is $\text{VIF}_j = 1/(1-R_j^2)$, where $R_j^2$ is the share of the variance of $j$ explained by all the other controls. VIF 10 means $R_j^2 = 90\%$. A high VIF makes the coefficient of $j$ unstable and the sequential "gap narrowing" depends on which of the near-duplicates is in the model. Computed as the diagonal of the inverse correlation matrix (no extra library).
 
#### Result (complete cases, n = 423,726 = 84.74% of the sample; as of run 2026-11-11, B14 E3)
| Control | VIF |
|---|---|
| `log_loan_amount` | 84.16 |
| `log_lti` | 63.81 |
| `log_income` | 36.24 |
| `ltv_calc` | 13.70 |
| `log_property_value` | 7.92 |
| `cltv` | 2.32 |
| `dti_mid` | 1.53 |
| `tract_to_msa_income_percentage` | 1.36 |
| `tract_minority_population_percent` | 1.13 |
 
#### Why the high values are structural
$$\log(\text{LTI}) = \log(\text{loan amount}) - \log(\text{income}) \quad\text{(exact, by construction)}$$
so any two of the three predict the third almost perfectly; the VIF of 84 / 64 / 36 is this identity, not a surprising statistical finding. `ltv_calc` = loan amount / property value × 100 is linked in the same way to loan amount and property value. A pairwise correlation screen does not show it: no pair has |r| > 0.8 (`B14_rel_redundant_pairs.csv` is empty), and the largest Spearman values are 0.71 (`ltv_calc` with CLTV), 0.68 (LTI with loan amount) and 0.65 (income with property value). Redundancy that involves three variables is caught by VIF and not by pairs.
 
#### Decision and reasons
1. Keep `log_loan_amount` and `income_decile`; drop `log_lti`/`lti_bin` from the main specification (LTI is a function of the other two).
2. Use `income_decile` rather than `log_income` in the main specification because it carries `Income <= 0` and `Income missing` as separate levels (D-V, D6: missingness is informative). `log_income` cannot represent them without imputing.
3. Use reported `cltv_bin` rather than `ltv_calc`: for subordinate liens `loan_amount` is only the junior note, so `ltv_calc` leaves out the senior lien (B2, V09).
4. Run one robustness specification with `log_income` + `log_loan_amount` as continuous terms, and one with `lti_bin` instead of `income_decile`, to show that the conclusions do not depend on the choice.
#### Limits
- VIF is computed on complete cases (15.26% of the sample is dropped), and the dropped rows differ in denial rate and race mix (D6). The VIF describes the complete-case structure only.
- The variables are winsorised at sample p01/p99 for the diagnostic only (no data change); `dti_mid` is an ordinal midpoint of DTI bins (D-V).
- Collinearity does not bias the prediction of a model; it makes the *attribution* between near-duplicates unstable. That is why it matters for the sequential decomposition and less for a prediction task.

---

### 15. Task B16 Decisions: Predictive Modeling, Model-Based Auditing, and Counterfactual Decomposition (D-AG through D-AR)

#### 15.1 Decisions D-AG & D-AQ: Exclusion of Sensitive Demographic Attributes from Predictor Sets
- **ECOA / Regulation B Compliance:** In U.S. credit markets, using race, ethnicity, sex, age, or marital status in an underwriting decision model is strictly prohibited by law. A benchmark model including these variables would not represent a legally deployable or policy-relevant standard.
- **Diagnostic Role of the Model:** The supervised models (M1, M2, M3) serve as *measuring instruments*, not deployable underwriting tools. Excluding sensitive attributes answers Question Q-A: *"Given only observable, credit-relevant fields, what denial probability is expected?"*
- **Audit Grouping (Q-B):** The fitted race-blind model's predictions $\hat{p}_i$ are grouped post-hoc by demographic categories (`derived_race`, `derived_sex`, `applicant_age`, `has_coapplicant`) to measure calibration-in-the-large:
  $$\text{Residual Gap}_g = \bar{y}_g - \bar{\hat{p}}_g = \text{Observed Denial Rate}_g - \text{Mean Predicted Probability}_g$$
  A positive residual indicates that group $g$ experiences higher denials than expected from observable controls alone. Because unobserved credit risk (FICO score, debt obligations, liquid assets) is omitted from public HMDA, residual disparities are interpreted descriptively and never asserted as causal proof of discrimination.

#### 15.2 Decision D-AH: Dual Underwriting-Proxy Variants (P0 vs. P1)
- **The Proxy Dilemma:** Public HMDA omits credit scores and AUS results (Assumption A5), but records `aus_1` (system used) and `applicant_credit_score_type` (scoring model used). In B14 A3, AUS code `6` (`Not applicable`, per the HMDA data dictionary) was found to be about twice as frequent on denied loans (45.3% vs. 22.1%; as of run 2026-11-10, B14 A3), and B16c C2 shows the same pattern in grouped validation (59.36% vs. 34.65%; as of run 2026-11-20). This indicates that proxy fields capture post-application routing and channel differences rather than pure applicant creditworthiness. A file that leaves the process before an automated system is run may be recorded as "Not applicable" and also be more likely denied, so availability may depend on the outcome `[Hypothesis]`.
- **Dual Pipeline:** Every nested feature set (M1, M2, M3) is estimated in two distinct configurations:
  - **P0 (Baseline / Honest):** Excludes `aus_1` and `applicant_credit_score_type`.
  - **P1 (Upper-Bound / Diagnostic):** Includes both proxies.
- Comparing P0 and P1 directly isolates how much predictive power and disparity shrinkage arise from process routing markers rather than borrower financial fundamentals.

#### 15.3 Decisions D-AI & D-AM: Grouped Splitting and Preventing Lender Leakage
- **Lender Heterogeneity (P7):** In B14 F7, lender denial rates exhibited immense dispersion ($\phi$ overdispersion in the thousands). A standard random row split places applications from the same lender across train, validation, and test sets, allowing models to learn unmeasured institutional idiosyncrasies (lender leakage).
- **Lender-Grouped Split (Primary):** All 8,136,664 $S0$ applications are partitioned 60% train / 20% validation / 20% test by grouping entire lenders. Stratification is performed across 4 lender size buckets (Small, Medium, Large, Mega) by cumulative application share, ensuring all partitions reflect the market volume distribution while testing out-of-sample generalization to *unseen institutions*.
- **Lender Information in Features (D-AM):** In grouped-split models, individual lender IDs (`lei`, `lender_code`) cannot be used since test lenders are unseen. Only coarse `lender_size_bucket` is included as a feature. Random-split models with lender target encoding are retained strictly as a labelled, optimistic reference (C1).

#### 15.4 Decisions D-AK & D-AO: Test-Set Discipline and Subsample Tuning Strategy
- **One-Touch Test Set:** To eliminate optimistic reporting bias, test partitions remain strictly sequestered. All hyper-parameter tuning, feature selection checks, and decision threshold optimizations are executed exclusively on the validation set. The test set is evaluated exactly once per locked final model.
- **Compute Scalability ($N \approx 500{,}000$):** Training complex ensembles and executing cluster bootstrapping across 8.1M observations requires significant compute. A representative stratified subsample (`df_samp`, $N \approx 500{,}000$) is used for rapid grid searches and diagnostic importance scans, while final model weights, headline tables, and official audit metrics are fitted and evaluated on the full $S0$ population.

#### 15.5 Decision D-AL: Model Families and Dual Pandas / PySpark Implementation
- **Model Diversity:**
  1. **Logistic Regression (LR):** L2-regularized baseline with binned continuous features, producing transparent odds ratios directly verifiable against B14 D2 denial curves.
  2. **HistGradientBoostingClassifier (HGB):** Primary non-linear tree ensemble; handles large-scale data ($N > 8\text{M}$) and informative missing values natively without synthetic imputation.
  3. **Random Forest (RF):** Secondary tree ensemble maintained for strict fidelity to Proposal §6.
- **Dual Engine Requirement:** In accordance with Big Data course specifications, both LR and tree ensembles are implemented in Python (Pandas/sklearn) and Apache Spark (PySpark MLlib) on full $S0$, with numerical parity logged in `B16_pyspark_equivalents.csv`.

#### 15.6 Decision D-AN: Machine Learning Counterfactual Decomposition (Oaxaca–Blinder Style)
- **Overcoming Sparse Strata (D-X, D-AG):** In B14, exact non-parametric stratification (Kitagawa) failed due to curse of dimensionality ($\text{pooled share} > 10\%$, `low_reliability = True`).
- **Smooth Model Counterfactuals:** Task B16 replaces discrete cells with a smooth flexible ML function $f_W(x) = \hat{P}(\text{denied} \mid x, \text{White})$ trained on White applications only:
  $$\text{Raw Gap}_g = \bar{Y}_g - \bar{Y}_W$$
  $$\text{Explained (Composition)} = \frac{1}{N_g} \sum_{i \in g} f_W(x_i) - \frac{1}{N_W} \sum_{j \in W} f_W(x_j)$$
  $$\text{Unexplained} = \Big(\bar{Y}_g - \frac{1}{N_g} \sum_{i \in g} f_W(x_i)\Big) - \Big(\bar{Y}_W - \frac{1}{N_W} \sum_{j \in W} f_W(x_j)\Big)$$
  $$\text{Identity Check:} \quad \text{Explained} + \text{Unexplained} = \text{Raw Gap} \quad (\text{tolerance } \le 10^{-9})$$
  (Amended by D-BI.) The earlier form $\bar{Y}_g - \frac{1}{N_g}\sum_{i \in g} f_W(x_i)$ gives Explained + Unexplained $= \bar{Y}_g - \frac{1}{N_W}\sum_{j\in W} f_W(x_j)$, which equals the raw gap only if $f_W$ is calibrated on the White test rows. It is not: the offset between mean prediction and observed rate depends on the lender draw (D-AU). Subtracting the White residual removes the common offset and makes the identity exact.
- **Index Dependence & Support:** Because Oaxaca decompositions are path-dependent, the reverse decomposition ($f_g$ trained on minority group $g$ and evaluated on White applicants) is reported alongside $f_W$. Propensity overlap checks confirm common support across multidimensional covariate spaces.

#### 15.7 Decisions D-AP & D-AR: Probability Calibration, Threshold Selection, and Fit Statistics
- **Calibration Over Thresholding:** For fair-lending diagnostics, predicted probabilities must reflect empirical frequencies. Class weights (`balanced`) and synthetic oversampling are disabled in audit models to preserve well-calibrated probabilities ($\text{Calibration Slope} \approx 1.0$).
- **Threshold Selection (D-AP):** Because market denial is ~24.6%, the arbitrary 0.5 classification threshold is rejected. Thresholds for discrete metrics (precision, recall, F1) are calibrated on the validation set at maximum F1 and fixed recall targets (e.g., 80%).
- **Fit Statistics (D-AR):** Binary models lack an ordinary OLS $R^2$. Goodness-of-fit is reported via ROC-AUC, PR-AUC, Brier score, log-loss, and calibration intercept/slope. Supplementary **McFadden pseudo-$R^2$** ($1 - \text{LL}_{\text{model}}/\text{LL}_{\text{null}}$) and **Tjur $R^2$** ($\bar{\hat{p}}_{\text{denied}} - \bar{\hat{p}}_{\text{approved}}$) are provided with explicit pedagogical warnings that low pseudo-$R^2$ values are standard in binary cross-sectional credit data and do not imply low explanatory validity.
### 16. Decision D-AU: Why the calibration offset is not "fixed" (and how the audit is read instead)
 
#### What is being measured
For group g, the audit quantity is the **calibration-in-the-large residual**
$$r_g = \bar{y}_g - \bar{\hat p}_g$$
the observed denial rate minus the mean predicted probability of a race-blind model (Q-B, §15.1). A positive $r_g$ means more denials than the model expects from the observed fields.
 
#### The problem: a common offset that depends on the lender draw
If every group has the same shift $\delta$ in $\bar{\hat p}$, every $r_g$ moves by $-\delta$ and the audit would read "all groups are denied less/more than expected", which is meaningless for a gap. The 5-fold lender experiment (D-AS) shows that $\delta$ is large and unstable:
 
| Fold (lenders held out) | Base rate | Mean predicted (HGB) | Offset (pred − base), pp |
|---|---|---|---|
| 0 | 0.2423 | 0.2193 | −2.3 |
| 1 | 0.2556 | 0.2017 | −5.4 |
| 2 | 0.2249 | 0.2746 | +5.0 |
| 3 | 0.2432 | 0.2234 | −2.0 |
| 4 | 0.2399 | 0.2779 | +3.8 |
 
The base rate varies little across folds (sd 0.011), but the mean prediction varies about three times more (sd 0.035). The model has no access to lender policy (only `lender_size_bucket`, D-AM), so when a fold happens to contain lenders that deny more (or less) than their size bucket suggests, the offset follows. This is the same phenomenon as the overdispersion found in B14 F7 (phi in the thousands), now seen through prediction. On the primary validation set the offset is +2.3 pp (HGB M3-P0), and the intercept changes sign across folds (−0.30 to +0.52), so it is a property of the lender draw, not of the model.
 
#### Why not recalibrate
Recalibration would estimate an intercept on the validation lenders and apply it to the test lenders. The k-fold results show that the intercept estimated on one set of lenders is not the intercept of another (it changes sign), and the test set has its own base rate (26.64%, D-AS). A correction fitted on validation would fix one draw and might worsen the other. It would also hide the heterogeneity that is itself a finding.
 
#### What the audit reports instead
1. **Absolute residual** $r_g$ with lender-cluster bootstrap CI (D-Q): includes the common offset; reported for transparency.
2. **Relative residual** $r_g - r_{White}$ as the headline: the part of the offset that is common to groups cancels. The cluster bootstrap resamples whole lenders, so the part that does *not* cancel (groups sorted differently across lenders) is inside the interval.
3. Calibration slope and intercept by group (D2), so a group with a different calibration shape is visible.
#### Limits
- The cancellation is exact only if the offset is the same on the probability scale for all groups. Groups concentrate in different lenders (B14 F6: Black applicants are more often at Mega lenders), so part of $r_g - r_{White}$ is lender sorting, not "treatment". Part E (with and without `lender_size_bucket`) and F9 (within-lender gaps) are the checks.
- A residual relative to White is still compatible with unobserved credit score, assets and AUS results (G4). It is never read as discrimination.
---
 
### 17. Decision D-AT: Why HGB M3-P0 / M2-P0 are the headline models
 
| Evidence (grouped, validation unless stated) | Result |
|---|---|
| HGB vs LR, 5 lender folds, paired AUC difference | +0.021, +0.021, +0.016, +0.020, +0.018 (mean 0.019, sd 0.002): same sign in all folds. The sd of each model's AUC across folds is about 0.023, but folds are shared, so the paired difference is the correct comparison |
| HGB vs RF, M3-P0 / M3-P1 | 0.862 vs 0.860 / 0.867 vs 0.866: no practical difference; RF trains on 100,000 rows per tree |
| M2 → M3 (HGB, P0) | +0.0008: geography and lender size add almost no predictive power once product and financial fields are in |
| P1 − P0 (HGB, M3) | +0.005 AUC; P1 also changes calibration level (mean prediction 0.248 vs 0.266, base rate 0.243) |
 
**Why M2-P0 and M3-P0 together.** M3 adds state, MSA class, tract fields and lender size, which are race proxies (P9; B14 E4 shows tract minority share has the largest SMD). The audit residual of M2-P0 (no geography) and M3-P0 (with geography) are compared in D4. Because predictive gains from M2 to M3 are tiny, a change in the residual between the two is not explained by better prediction; it reflects what geography carries about group membership `[Hypothesis]`.
 
**Why P0 is the headline.** `aus_1` and the score-model type describe process, and `aus_1 = 6` (`Not applicable`) is about twice as frequent among denied files (B14 A3; 59.36% vs. 34.65% in grouped validation, as of run 2026-11-20, B16c C2). P1 improves AUC and moves the mean prediction closer to the base rate, but part of that is process routing, not borrower risk. P1 is reported as an upper bound (D-AH, D-Y).
 
**Why LR stays.** It gives odds ratios checkable against the B14 D2 curves (F1). Its calibration slope on grouped M2/M3-P0 (0.87-0.89) is below the soft gate of 0.9, which is another reason it is not the audit model.
 
---
 
### 18. Decision D-AW: Iteration cap on random-split HGB
 
For a gradient-boosting fit, the best number of trees is read from the validation log-loss at each stage (`staged_predict_proba`). If the minimum is at the last stage, the model would have kept improving. All six random-split HGB fits end at stage 300 (`hit_cap = True`), whereas the grouped fits stop at 75-296. With a random split, lenders are shared between train and validation, so more trees keep learning lender-specific patterns and the validation loss keeps falling; with grouped splits the loss turns up earlier because those patterns do not transfer.
 
**Consequences.** (a) The random-split metrics are slightly under-fitted (not converged). (b) The random-minus-grouped AUC gap (C1) and the lender-target-encoding gain (C9: +0.016 AUC) are lower bounds. (c) The primary grouped results and the audit do not depend on them. The refit (higher cap, about 6 fits) only affects the leakage reference; it is optional for the audit and required before quoting a final leakage number.
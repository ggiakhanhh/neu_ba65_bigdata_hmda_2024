# Project Decision Log: HMDA 2024 Big Data Analysis

**Project:** Decomposing Racial Gaps in Mortgage Denial Rates: A Large-Scale Analysis of the 2024 U.S. HMDA Market  
**Course:** Big Data Analysis (Final Project) — Group 3  
**Status Key:** `Agreed` (Decision approved, empirically verified, and locked), `Open` (Pending analysis), `Revisit` (Subject to sensitivity check)  
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


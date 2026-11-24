# B14 Hand-off: Design for the Sequential Decomposition (run 2026-11-24)

## Reference groups and metrics
- Reference: White (D-J). Headline groups: Black or African American, Asian, Joint, American Indian or Alaska Native, 2 or more minority races, Native Hawaiian or Other Pacific Islander. `Race Not Available` / `Free Form Text Only` kept in accounting, excluded from headline gaps (D-L).
- Report gap (pp), risk ratio, odds ratio; inference = lender-cluster bootstrap (B = 1,000, seed 42), Wilson CIs, no p-value tables (D-Q).

## Samples (rows)
- S0: 8,136,664 | S5_all: 8,041,498 | fin_complete: 7,037,363 | RQ3 (fin_complete & valid tract): 7,002,807.
- Always show S0 next to `fin_complete` (selection, D6B) and run the G1 variants as robustness.

## Controls by stage (observed, pre-decision only)
1. Raw gap: none.
2. Product: loan_type, loan_purpose, lien_status, occupancy_type, construction_method, derived_dwelling_category, conforming_loan_limit, open_end_line_of_credit.
3. Financial (D-AF): dti_cat, cltv_bin, income_decile (with its missing levels), log_loan_amount; missing values as explicit categories (D-V).
   Not in the main spec: log_lti / lti_bin and ltv_calc (collinear block, VIF; reported CLTV is used).
   Robustness specs: (i) log_income + log_loan_amount as continuous terms; (ii) lti_bin instead of income_decile.
4. Geography and lender: state_code, msa_class, tract_minority_bin, tract_income_level (tract-NA excluded for RQ3, D-I); lender size bucket or lender fixed effects (lenders anonymous, D-O).

## Excluded variables (leakage or diagnostic)
- Post-decision / outcome-revealing (12): denial_reason_1, denial_reason_2, denial_reason_3, denial_reason_4, discount_points, hoepa_status, interest_rate, lender_credits, origination_charges, purchaser_type, rate_spread, total_loan_costs.
- Process proxies `aus_1`, `applicant_credit_score_type`: not in the main specification; used only in the "with proxies" robustness spec (D-Y).
- loan_term: product control (D-AA)
- Denial reasons are descriptive only (D7). `flag_*`, `in_*`, `*_status` columns are diagnostics.

## Cautions
- Stratified decompositions are not estimates when `low_reliability` (D-U/D-X); use the coarse spec (G2) and the raw gap with cluster CI.
- Income > $10M flagged (1000 rows; D-W): run with and without.
- Unobserved: Credit score value, Assets and reserves, AUS recommendation/result, Application and decision dates, Employment history / income documentation, Lender identity details (type, name), Loan officer / broker detail (G4). No remaining gap is interpreted as discrimination.

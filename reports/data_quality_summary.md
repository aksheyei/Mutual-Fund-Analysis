# Data Quality Summary - Day 1

## Files Reviewed
10 CSV files loaded from data/raw/

## Anomalies Found

| File | Column | Issue |
|---|---|---|
| fund_master.csv | launch_date | Stored as text, not date |
| nav_history.csv | date | Stored as text, not date |
| aum_by_fund_house.csv | date | Stored as text, not date |
| monthly_sip_inflows.csv | month | Stored as text, not date |
| monthly_sip_inflows.csv | yoy_growth_pct | 12 missing values |
| category_inflows.csv | month | Stored as text, not date |
| industry_folio_count.csv | month | Stored as text, not date |
| investor_transactions.csv | transaction_date | Stored as text, not date |
| portfolio_holdings.csv | portfolio_date | Stored as text, not date |
| benchmark_indices.csv | date | Stored as text, not date |

## Notes
- scheme_performance.csv had no issues found.
- Date columns being stored as text will need conversion using pd.to_datetime()
  before any time-based analysis (sorting, aggregation, joins) is done. This
  will be handled during the data processing stage, not Day 1.
- The 12 missing values in yoy_growth_pct may correspond to funds without a
  full prior year of data to compare against - needs verification.

## No Missing Values Found In
- fund_master.csv

## AMFI Code Validation (Task 7)

All 40 AMFI codes in fund_master were checked against nav_history.
Result: every code has matching NAV data present - no missing schemes found.
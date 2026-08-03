# Data Dictionary — Bluestock Mutual Fund Analysis

This document describes every table and column in `bluestock_mf.db`, including
data types, business meaning, and source references.

---

## dim_fund

One row per mutual fund scheme. Source: `01_fund_master.csv`.

| Column | Type | Description |
|---|---|---|
| amfi_code | INTEGER (PK) | Unique AMFI scheme code identifying this specific fund + plan + option combination |
| fund_house | TEXT | Name of the mutual fund company (AMC) managing this fund |
| scheme_name | TEXT | Official name of the fund scheme |
| category | TEXT | Broad fund category — Equity or Debt |
| sub_category | TEXT | Specific fund type, e.g. Large Cap, Small Cap, Liquid, ELSS |
| plan | TEXT | Direct or Regular plan |
| launch_date | TEXT | Date the fund was launched (stored as text, format YYYY-MM-DD) |
| benchmark | TEXT | Index this fund is benchmarked against |
| expense_ratio_pct | REAL | Annual fee charged by the fund, as a percentage of assets |
| exit_load_pct | REAL | Fee charged for early withdrawal, as a percentage |
| min_sip_amount | INTEGER | Minimum SIP investment amount (INR) |
| min_lumpsum_amount | INTEGER | Minimum lump sum investment amount (INR) |
| fund_manager | TEXT | Name of the fund's manager |
| risk_category | TEXT | SEBI risk-o-meter grade (Low, Moderate, High, Very High, etc.) |
| sebi_category_code | TEXT | SEBI's official category code for this fund |

**Data quality note:** 5 of the "Bluechip"-named funds in this dataset's related
scheme codes were found to have been renamed to "Large Cap" following SEBI's
2018 mutual fund recategorization. See reports/data_quality_summary.md for
full details.

---

## dim_date

One row per calendar date from 2022-01-01 to 2026-12-31. Generated
programmatically (not sourced from a CSV) to support time-based analysis.

| Column | Type | Description |
|---|---|---|
| date_id | INTEGER (PK) | Unique sequential ID for this date |
| full_date | TEXT | The calendar date, format YYYY-MM-DD |
| year | INTEGER | Calendar year |
| month | INTEGER | Month number (1-12) |
| month_name | TEXT | Full month name (e.g. "January") |
| quarter | INTEGER | Calendar quarter (1-4) |
| day_of_week | TEXT | Full weekday name (e.g. "Monday") |
| is_weekend | INTEGER | 1 if Saturday/Sunday, 0 otherwise |

---

## fact_nav

One row per fund per date, recording the fund's NAV (price). Source:
`02_nav_history.csv` (cleaned).

| Column | Type | Description |
|---|---|---|
| nav_id | INTEGER (PK) | Unique sequential ID for this record |
| amfi_code | INTEGER (FK -> dim_fund) | Which fund this NAV belongs to |
| date_id | INTEGER (FK -> dim_date) | Which date this NAV was recorded on |
| nav | REAL | Net Asset Value (price per unit) on this date |

**Cleaning applied:** dates parsed to datetime, sorted by amfi_code + date,
duplicates removed, validated NAV > 0.

---

## fact_transactions

One row per investor transaction. Source: `08_investor_transactions.csv`
(cleaned).

| Column | Type | Description |
|---|---|---|
| transaction_id | INTEGER (PK) | Unique sequential ID for this transaction |
| investor_id | TEXT | Unique ID identifying the investor |
| amfi_code | INTEGER (FK -> dim_fund) | Which fund this transaction was for |
| date_id | INTEGER (FK -> dim_date) | Date the transaction occurred |
| transaction_type | TEXT | SIP, Lumpsum, or Redemption |
| amount_inr | INTEGER | Transaction amount in INR |
| state | TEXT | Investor's state |
| city | TEXT | Investor's city |
| city_tier | TEXT | City tier classification (T30/B30) |
| age_group | TEXT | Investor's age bracket |
| gender | TEXT | Investor's gender |
| annual_income_lakh | REAL | Investor's annual income, in lakhs of INR |
| payment_mode | TEXT | Method of payment (UPI, Cheque, Mandate, Net Banking, etc.) |
| kyc_status | TEXT | KYC compliance status (Verified/Pending) |

**Cleaning applied:** transaction_type standardised (e.g. "Sip" -> "SIP"),
amount validated > 0, dates parsed to datetime, KYC status values checked.

---

## fact_performance

One row per fund, giving a current snapshot of performance metrics. Source:
`07_scheme_performance.csv` (cleaned).

| Column | Type | Description |
|---|---|---|
| performance_id | INTEGER (PK) | Unique sequential ID for this record |
| amfi_code | INTEGER (FK -> dim_fund) | Which fund this performance data belongs to |
| return_1yr_pct | REAL | 1-year trailing return, % |
| return_3yr_pct | REAL | 3-year annualised return, % |
| return_5yr_pct | REAL | 5-year annualised return, % |
| benchmark_3yr_pct | REAL | Benchmark's 3-year annualised return, % |
| alpha | REAL | Excess return vs benchmark, risk-adjusted |
| beta | REAL | Fund's volatility relative to the market |
| sharpe_ratio | REAL | Risk-adjusted return metric (higher = better) |
| sortino_ratio | REAL | Downside-risk-adjusted return metric |
| std_dev_ann_pct | REAL | Annualised standard deviation of returns, % |
| max_drawdown_pct | REAL | Largest peak-to-trough decline, % |
| aum_crore | INTEGER | Assets under management, in crores of INR |
| expense_ratio_pct | REAL | Annual fee, % of assets |
| morningstar_rating | INTEGER | Star rating (1-5) |
| risk_grade | TEXT | Risk classification label |

**Cleaning applied:** validated all return values are numeric, checked
expense_ratio_pct falls within 0.1%-2.5% range, flagged anomalies.

**Note:** scheme_name, fund_house, category, and plan were intentionally
excluded from this table since they already exist in dim_fund — join on
amfi_code to retrieve them.

---

## fact_aum

One row per fund house per date, tracking AUM over time. Source:
`03_aum_by_fund_house.csv`.

| Column | Type | Description |
|---|---|---|
| aum_id | INTEGER (PK) | Unique sequential ID for this record |
| date_id | INTEGER (FK -> dim_date) | Date this AUM figure applies to |
| fund_house | TEXT | Name of the fund house |
| aum_lakh_crore | REAL | AUM in units of lakh crore INR |
| aum_crore | INTEGER | AUM in units of crore INR |
| num_schemes | INTEGER | Number of schemes under this fund house on this date |

---

## Relationships (Star Schema)

- fact_nav, fact_transactions -> dim_fund (via amfi_code) and dim_date (via date_id)
- fact_performance -> dim_fund (via amfi_code) only (no date dimension needed - snapshot data)
- fact_aum -> dim_date (via date_id) only (no fund dimension - tracked at fund house level)
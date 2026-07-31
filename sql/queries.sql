-- Query 1: Top 5 funds by AUM
SELECT d.fund_house, SUM(p.aum_crore) AS AUM
FROM dim_fund d LEFT JOIN fact_performance p ON d.amfi_code = p.amfi_code
GROUP BY d.fund_house
ORDER BY SUM(p.aum_crore) DESC
LIMIT 5;

-- Query 2: Average NAV per month
SELECT d.year, d.month, AVG(n.nav) AS avg_nav
FROM dim_date d LEFT JOIN fact_nav n ON d.date_id = n.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Query 3: SIP Year-over-Year growth
WITH SIP AS (
    SELECT d.year as year, SUM(t.amount_inr) AS SIP_TOTAL
    FROM dim_date d LEFT JOIN fact_transactions t ON d.date_id = t.date_id
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
    ORDER BY d.year
)
SELECT year, SIP_TOTAL,
(SIP_TOTAL - LAG(SIP_TOTAL, 1) OVER (ORDER BY year)) * 100.0 / LAG(SIP_TOTAL, 1) OVER (ORDER BY year) AS YOY_GROWTH
FROM SIP;

-- Query 4: Total transactions by state
SELECT state, COUNT(*) AS transactions
FROM fact_transactions
GROUP BY state;

-- Query 5: Funds with expense_ratio < 1%
SELECT f.scheme_name, f.fund_house, p.expense_ratio_pct
FROM fact_performance p
LEFT JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio_pct < 1
ORDER BY p.expense_ratio_pct;

-- Query 6: Top 5 fund houses by total AUM
SELECT fund_house, SUM(aum_crore) AS AUM
FROM fact_aum
GROUP BY fund_house
ORDER BY AUM DESC
LIMIT 5;

-- Query 7: Number of transactions by KYC status
SELECT kyc_status, COUNT(*) AS transactions
FROM fact_transactions
GROUP BY kyc_status;

-- Query 8: Average 1-year return by category
SELECT f.category, AVG(p.return_1yr_pct) AS avg_1yr_return
FROM fact_performance p
LEFT JOIN dim_fund f ON p.amfi_code = f.amfi_code
GROUP BY f.category;

-- Query 9: Funds with highest Sharpe ratio
SELECT f.scheme_name, f.fund_house, p.sharpe_ratio
FROM fact_performance p
LEFT JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- Query 10: Monthly transaction volume trend
SELECT d.year, d.month, COUNT(t.transaction_id) AS transactions
FROM dim_date d LEFT JOIN fact_transactions t ON d.date_id = t.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
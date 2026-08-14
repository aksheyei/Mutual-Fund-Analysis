"""
etl_pipeline.py

End-to-end ETL for the Bluestock Mutual Fund capstone.

What this does, in order:
1. Loads the 10 raw CSVs from data/raw/
2. Cleans dtypes, validates ranges, checks duplicates
3. Saves all cleaned CSVs to data/processed/
4. Builds the SQLite star schema in data/db/bluestock_mf.db
   (skips schema build + load if the DB file already exists)

Run from anywhere:
    python scripts/etl_pipeline.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# PATHS — resolved relative to this script's own location, not the current
# working directory, so it runs the same whether you call it from the repo
# root, from scripts/, or anywhere else.
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DB_DIR = os.path.join(PROJECT_ROOT, "data", "db")
DB_PATH = os.path.join(DB_DIR, "bluestock_mf.db")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

print("=" * 60)
print("STEP 1: Loading raw CSVs")
print("=" * 60)

fund_master = pd.read_csv(os.path.join(RAW_DIR, "01_fund_master.csv"))
nav_history = pd.read_csv(os.path.join(RAW_DIR, "02_nav_history.csv"))
aum_by_fund_house = pd.read_csv(os.path.join(RAW_DIR, "03_aum_by_fund_house.csv"))
monthly_sip_inflows = pd.read_csv(os.path.join(RAW_DIR, "04_monthly_sip_inflows.csv"))
category_inflows = pd.read_csv(os.path.join(RAW_DIR, "05_category_inflows.csv"))
industry_folio_counts = pd.read_csv(os.path.join(RAW_DIR, "06_industry_folio_count.csv"))
scheme_performance = pd.read_csv(os.path.join(RAW_DIR, "07_scheme_performance.csv"))
investor_transactions = pd.read_csv(os.path.join(RAW_DIR, "08_investor_transactions.csv"))
portfolio_holding = pd.read_csv(os.path.join(RAW_DIR, "09_portfolio_holdings.csv"))
benchmark_indices = pd.read_csv(os.path.join(RAW_DIR, "10_benchmark_indices.csv"))

print("Loaded 10 raw CSVs from", RAW_DIR)

print()
print("=" * 60)
print("STEP 2: Cleaning + validating")
print("=" * 60)

# --- fund_master ---
fund_master["launch_date"] = pd.to_datetime(fund_master["launch_date"])
print("fund_master duplicates:", fund_master.duplicated().sum())

# --- nav_history ---
nav_history["date"] = pd.to_datetime(nav_history["date"])
nav_history = nav_history.sort_values(by=["amfi_code", "date"], ascending=True)
print("nav_history duplicates:", nav_history.duplicated().sum())
print("nav_history rows with nav <= 0:", (nav_history["nav"] <= 0).sum())

# --- investor_transactions ---
investor_transactions["transaction_date"] = pd.to_datetime(investor_transactions["transaction_date"])
investor_transactions["transaction_type"] = investor_transactions["transaction_type"].replace("Sip", "SIP")
print("investor_transactions rows with amount <= 0:", (investor_transactions["amount_inr"] <= 0).sum())

# --- scheme_performance ---
print("scheme_performance rows with expense_ratio_pct <= 0.1:", (scheme_performance["expense_ratio_pct"] <= 0.1).sum())

# --- aum_by_fund_house ---
aum_by_fund_house["date"] = pd.to_datetime(aum_by_fund_house["date"])

# --- monthly_sip_inflows ---
monthly_sip_inflows["month"] = pd.to_datetime(monthly_sip_inflows["month"]).dt.strftime("%Y-%m")
# 2022 rows contain null yoy_growth_pct — no 2021 data to calculate YoY change against; expected, not an error

# --- category_inflows ---
print("category_inflows rows with negative net_inflow_crore:", (category_inflows["net_inflow_crore"] < 0).sum())

# --- industry_folio_counts ---
for col in ["total_folios_crore", "equity_folios_crore", "debt_folios_crore",
            "hybrid_folios_crore", "others_folios_crore"]:
    negative_count = (industry_folio_counts[col] < 0).sum()
    print(f"industry_folio_counts rows with negative {col}:", negative_count)

# --- portfolio_holding ---
portfolio_holding["portfolio_date"] = pd.to_datetime(portfolio_holding["portfolio_date"])
print("portfolio_holding rows with negative market_value_cr:", (portfolio_holding["market_value_cr"] < 0).sum())
print("portfolio_holding rows with negative current_price_inr:", (portfolio_holding["current_price_inr"] < 0).sum())

# --- benchmark_indices ---
benchmark_indices["date"] = pd.to_datetime(benchmark_indices["date"])
print("benchmark_indices duplicates:", benchmark_indices.duplicated().sum())
print("benchmark_indices rows with negative close_value:", (benchmark_indices["close_value"] < 0).sum())

print()
print("=" * 60)
print("STEP 3: Saving cleaned CSVs to data/processed/")
print("=" * 60)

fund_master.to_csv(os.path.join(PROCESSED_DIR, "fund_master_cleaned.csv"), index=False)
nav_history.to_csv(os.path.join(PROCESSED_DIR, "nav_history_cleaned.csv"), index=False)
investor_transactions.to_csv(os.path.join(PROCESSED_DIR, "investor_transactions_cleaned.csv"), index=False)
scheme_performance.to_csv(os.path.join(PROCESSED_DIR, "scheme_performance_cleaned.csv"), index=False)
aum_by_fund_house.to_csv(os.path.join(PROCESSED_DIR, "aum_by_fund_house_cleaned.csv"), index=False)
monthly_sip_inflows.to_csv(os.path.join(PROCESSED_DIR, "monthly_sip_inflows_cleaned.csv"), index=False)
category_inflows.to_csv(os.path.join(PROCESSED_DIR, "category_inflows_cleaned.csv"), index=False)
industry_folio_counts.to_csv(os.path.join(PROCESSED_DIR, "industry_folio_counts_cleaned.csv"), index=False)
portfolio_holding.to_csv(os.path.join(PROCESSED_DIR, "portfolio_holding_cleaned.csv"), index=False)
benchmark_indices.to_csv(os.path.join(PROCESSED_DIR, "benchmark_indices_cleaned.csv"), index=False)

print("Saved 10 cleaned CSVs to", PROCESSED_DIR)
print("(includes nav_history_cleaned.csv, investor_transactions_cleaned.csv,")
print(" scheme_performance_cleaned.csv — previously missing from the notebook)")

print()
print("=" * 60)
print("STEP 4: Building SQLite star schema")
print("=" * 60)

if os.path.exists(DB_PATH):
    print(f"{DB_PATH} already exists — skipping schema build and load.")
    print("Delete the file manually if you want a full rebuild.")
else:
    engine = create_engine(f"sqlite:///{DB_PATH}")

    with engine.connect() as conn:
        conn.exec_driver_sql("""
        CREATE TABLE dim_fund(
        amfi_code INTEGER PRIMARY KEY,
        fund_house TEXT,
        scheme_name TEXT,
        category TEXT,
        sub_category TEXT,
        plan TEXT,
        launch_date TEXT,
        benchmark TEXT,
        expense_ratio_pct REAL,
        exit_load_pct REAL,
        min_sip_amount INTEGER,
        min_lumpsum_amount INTEGER,
        fund_manager TEXT,
        risk_category TEXT,
        sebi_category_code TEXT
        )""")

        conn.exec_driver_sql("""
        CREATE TABLE dim_date(
        date_id INTEGER PRIMARY KEY,
        full_date TEXT,
        year INTEGER,
        month INTEGER,
        month_name TEXT,
        quarter INTEGER,
        day_of_week TEXT,
        is_weekend INTEGER
        )""")

        conn.exec_driver_sql("""
        CREATE TABLE fact_nav(
        nav_id INTEGER PRIMARY KEY,
        amfi_code INTEGER,
        date_id INTEGER,
        nav REAL,
        FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
        FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
        )""")

        conn.exec_driver_sql("""
        CREATE TABLE fact_transactions (
        transaction_id INTEGER PRIMARY KEY,
        investor_id TEXT,
        amfi_code INTEGER,
        date_id INTEGER,
        transaction_type TEXT,
        amount_inr INTEGER,
        state TEXT,
        city TEXT,
        city_tier TEXT,
        age_group TEXT,
        gender TEXT,
        annual_income_lakh REAL,
        payment_mode TEXT,
        kyc_status TEXT,
        FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
        FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
        )""")

        conn.exec_driver_sql("""
        CREATE TABLE fact_performance (
        performance_id INTEGER PRIMARY KEY,
        amfi_code INTEGER,
        return_1yr_pct REAL,
        return_3yr_pct REAL,
        return_5yr_pct REAL,
        benchmark_3yr_pct REAL,
        alpha REAL,
        beta REAL,
        sharpe_ratio REAL,
        sortino_ratio REAL,
        std_dev_ann_pct REAL,
        max_drawdown_pct REAL,
        aum_crore INTEGER,
        expense_ratio_pct REAL,
        morningstar_rating INTEGER,
        risk_grade TEXT,
        FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
        )""")

        conn.exec_driver_sql("""
        CREATE TABLE fact_aum (
        aum_id INTEGER PRIMARY KEY,
        date_id INTEGER,
        fund_house TEXT,
        aum_lakh_crore REAL,
        aum_crore INTEGER,
        num_schemes INTEGER,
        FOREIGN KEY (date_id) REFERENCES dim_date(date_id)
        )""")

        conn.commit()

    print("Created 6 tables: dim_fund, dim_date, fact_nav, fact_transactions, fact_performance, fact_aum")

    # --- dim_fund ---
    fund_master.to_sql("dim_fund", engine, if_exists="append", index=False)

    # --- dim_date (spans the full raw NAV history date range) ---
    date_range = pd.date_range(start="2022-01-01", end="2026-12-31", freq="D")
    dim_date = pd.DataFrame({
        "full_date": date_range.strftime("%Y-%m-%d"),
        "year": date_range.year,
        "month": date_range.month,
        "month_name": date_range.strftime("%B"),
        "quarter": date_range.quarter,
        "day_of_week": date_range.strftime("%A"),
        "is_weekend": date_range.dayofweek.isin([5, 6]).astype(int)
    })
    dim_date.insert(0, "date_id", range(1, len(dim_date) + 1))
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)

    dim_date_lookup = pd.read_sql("SELECT date_id, full_date FROM dim_date;", engine)
    dim_date_lookup["full_date"] = pd.to_datetime(dim_date_lookup["full_date"])

    # --- fact_nav ---
    fact_nav = nav_history.merge(dim_date_lookup, left_on="date", right_on="full_date", how="left")
    fact_nav = fact_nav[["amfi_code", "date_id", "nav"]]
    fact_nav.to_sql("fact_nav", engine, if_exists="append", index=False)

    # --- fact_transactions ---
    fact_transactions = investor_transactions.merge(dim_date_lookup, left_on="transaction_date", right_on="full_date", how="left")
    fact_transactions = fact_transactions[[
        "investor_id", "amfi_code", "date_id", "transaction_type", "amount_inr",
        "state", "city", "city_tier", "age_group", "gender",
        "annual_income_lakh", "payment_mode", "kyc_status"
    ]]
    fact_transactions.to_sql("fact_transactions", engine, if_exists="append", index=False)

    # --- fact_performance (drop columns already covered by dim_fund) ---
    fact_performance = scheme_performance.drop(columns=["scheme_name", "fund_house", "category", "plan"])
    fact_performance.to_sql("fact_performance", engine, if_exists="append", index=False)

    # --- fact_aum ---
    fact_aum = aum_by_fund_house.merge(dim_date_lookup, left_on="date", right_on="full_date", how="left")
    fact_aum = fact_aum[["date_id", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"]]
    fact_aum.to_sql("fact_aum", engine, if_exists="append", index=False)

    print()
    print("Row count checks:")
    print("dim_fund:", pd.read_sql("SELECT COUNT(*) FROM dim_fund;", engine).iloc[0, 0], "vs fund_master:", fund_master.shape[0])
    print("fact_nav:", pd.read_sql("SELECT COUNT(*) FROM fact_nav;", engine).iloc[0, 0], "vs nav_history:", nav_history.shape[0])
    print("fact_transactions:", pd.read_sql("SELECT COUNT(*) FROM fact_transactions;", engine).iloc[0, 0], "vs investor_transactions:", investor_transactions.shape[0])
    print("fact_performance:", pd.read_sql("SELECT COUNT(*) FROM fact_performance;", engine).iloc[0, 0], "vs scheme_performance:", scheme_performance.shape[0])
    print("fact_aum:", pd.read_sql("SELECT COUNT(*) FROM fact_aum;", engine).iloc[0, 0], "vs aum_by_fund_house:", aum_by_fund_house.shape[0])

    print()
    print(f"Database built at {DB_PATH}")

print()
print("=" * 60)
print("ETL PIPELINE COMPLETE")
print("=" * 60)

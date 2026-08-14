"""
compute_metrics.py

Performance + Advanced Analytics for the Bluestock Mutual Fund capstone.
Combines 04_performance_analytics.ipynb and 05_advanced_analytics.ipynb
into one runnable script.

Reads from data/processed/ (cleaned CSVs — run etl_pipeline.py first).

Produces:
  data/processed/alpha_beta.csv
  data/processed/max_drawdown.csv
  data/processed/fund_scorecard.csv
  data/processed/cohort_summary.csv
  data/processed/sip_continuity.csv
  data/processed/sector_hhi_equity.csv
  reports/var_cvar_report.csv
  reports/charts/benchmark_comparison_top5.png
  reports/charts/rolling_sharpe_chart.png
  scripts/recommender.py

NOTE: tracking_error_top5.csv is NOT produced here — that metric doesn't
exist in either source notebook, so there was nothing to extract. It's a
new calculation we still need to design and add.

Run from anywhere:
    python scripts/compute_metrics.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
CHARTS_DIR = os.path.join(REPORTS_DIR, "charts")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

ANNUAL_RF = 0.065
DAILY_RF = (1 + ANNUAL_RF) ** (1 / 252) - 1

print("=" * 60)
print("Loading cleaned data")
print("=" * 60)

fund_master = pd.read_csv(os.path.join(PROCESSED_DIR, "fund_master_cleaned.csv"))
nav_history = pd.read_csv(os.path.join(PROCESSED_DIR, "nav_history_cleaned.csv"))
benchmark_df = pd.read_csv(os.path.join(PROCESSED_DIR, "benchmark_indices_cleaned.csv"))
investor_txn = pd.read_csv(os.path.join(PROCESSED_DIR, "investor_transactions_cleaned.csv"))
portfolio_holdings = pd.read_csv(os.path.join(PROCESSED_DIR, "portfolio_holding_cleaned.csv"))

fund_master["launch_date"] = pd.to_datetime(fund_master["launch_date"])
nav_history["date"] = pd.to_datetime(nav_history["date"])
benchmark_df["date"] = pd.to_datetime(benchmark_df["date"])
investor_txn["transaction_date"] = pd.to_datetime(investor_txn["transaction_date"])

# Merged NAV + fund_master, sorted, with daily return
nav_df = pd.merge(fund_master, nav_history, on="amfi_code", how="left")
nav_df = nav_df.sort_values(["amfi_code", "date"]).reset_index(drop=True)
nav_df["daily_return"] = nav_df.groupby("amfi_code")["nav"].pct_change()

print("nav_df shape:", nav_df.shape)

# ===========================================================================
# PERFORMANCE ANALYTICS
# ===========================================================================

print()
print("=" * 60)
print("CAGR (1yr, 3yr — 5yr not computable, only ~4.4yrs of data)")
print("=" * 60)

end_date = nav_df["date"].max()
target_date_1yr = end_date - pd.DateOffset(years=1)
target_date_3yr = end_date - pd.DateOffset(years=3)

end_navs = nav_df[nav_df["date"] == end_date].set_index("amfi_code")["nav"]

nav_after_1yr_target = nav_df[nav_df["date"] >= target_date_1yr].sort_values("date")
nav_after_3yr_target = nav_df[nav_df["date"] >= target_date_3yr].sort_values("date")

start_1yr_navs = nav_after_1yr_target.groupby("amfi_code").first()["nav"]
start_3yr_navs = nav_after_3yr_target.groupby("amfi_code").first()["nav"]

cagr_1yr_all = (end_navs / start_1yr_navs) ** (1 / 1) - 1
cagr_3yr_all = (end_navs / start_3yr_navs) ** (1 / 3) - 1

cagr_table = pd.DataFrame({
    "cagr_1yr": cagr_1yr_all,
    "cagr_3yr": cagr_3yr_all,
    "cagr_5yr": pd.NA  # not computable — data only spans 4.4 years
})
cagr_table = cagr_table.reset_index()
cagr_table = cagr_table.merge(fund_master[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
cagr_table = cagr_table[["amfi_code", "scheme_name", "category", "cagr_1yr", "cagr_3yr", "cagr_5yr"]]

print("CAGR computed for", len(cagr_table), "funds")

print()
print("=" * 60)
print("Sharpe Ratio")
print("=" * 60)

mean_returns_all = nav_df.groupby("amfi_code")["daily_return"].mean()
std_returns_all = nav_df.groupby("amfi_code")["daily_return"].std()
sharpe_all = (mean_returns_all - DAILY_RF) / std_returns_all * (252 ** 0.5)

sharpe_table = pd.DataFrame({"sharpe_ratio": sharpe_all}).reset_index()
sharpe_table = sharpe_table.merge(fund_master[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
sharpe_table["sharpe_rank"] = sharpe_table["sharpe_ratio"].rank(ascending=False)
sharpe_table = sharpe_table.sort_values("sharpe_rank")

print("Sharpe ratio computed for", len(sharpe_table), "funds")

print()
print("=" * 60)
print("Sortino Ratio")
print("=" * 60)

negative_returns_all = nav_df[nav_df["daily_return"] < 0]
downside_std_all = negative_returns_all.groupby("amfi_code")["daily_return"].std()
sortino_all = (mean_returns_all - DAILY_RF) / downside_std_all * (252 ** 0.5)

sortino_table = pd.DataFrame({"sortino_ratio": sortino_all}).reset_index()
sortino_table = sortino_table.merge(fund_master[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
sortino_table["sortino_rank"] = sortino_table["sortino_ratio"].rank(ascending=False)
sortino_table = sortino_table.sort_values("sortino_rank")

print("Sortino ratio computed for", len(sortino_table), "funds")

print()
print("=" * 60)
print("Alpha / Beta vs NIFTY 100 (per-fund regression)")
print("=" * 60)

nifty100 = benchmark_df[benchmark_df["index_name"] == "NIFTY100"].copy()
nifty100 = nifty100.sort_values("date")
nifty100["benchmark_return"] = nifty100["close_value"].pct_change()

alpha_beta_results = []
for code in nav_df["amfi_code"].unique():
    fund_data = nav_df[nav_df["amfi_code"] == code]
    merged = fund_data[["date", "daily_return"]].merge(
        nifty100[["date", "benchmark_return"]], on="date", how="inner"
    ).dropna()
    result = stats.linregress(merged["benchmark_return"], merged["daily_return"])
    alpha_beta_results.append({
        "amfi_code": code,
        "beta": result.slope,
        "alpha": result.intercept * 252,
        "r_squared": result.rvalue ** 2
    })

alpha_beta_df = pd.DataFrame(alpha_beta_results)
alpha_beta_df = alpha_beta_df.merge(fund_master[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
alpha_beta_df = alpha_beta_df[["amfi_code", "scheme_name", "category", "beta", "alpha", "r_squared"]]
alpha_beta_df = alpha_beta_df.sort_values("alpha", ascending=False)

alpha_beta_df.to_csv(os.path.join(PROCESSED_DIR, "alpha_beta.csv"), index=False)
print("Saved alpha_beta.csv (" + str(len(alpha_beta_df)) + " funds)")

print()
print("=" * 60)
print("Maximum Drawdown")
print("=" * 60)

nav_df["running_max"] = nav_df.groupby("amfi_code")["nav"].cummax()
nav_df["drawdown"] = nav_df["nav"] / nav_df["running_max"] - 1

trough_rows = nav_df[nav_df["drawdown"] == nav_df.groupby("amfi_code")["drawdown"].transform("min")]
trough_rows = trough_rows[["amfi_code", "date", "nav", "drawdown"]].rename(
    columns={"date": "trough_date", "nav": "trough_nav"}
)

drawdown_table = trough_rows.merge(fund_master[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
drawdown_table = drawdown_table[["amfi_code", "scheme_name", "category", "trough_date", "trough_nav", "drawdown"]]
drawdown_table = drawdown_table.rename(columns={"drawdown": "max_drawdown"})
drawdown_table = drawdown_table.sort_values("max_drawdown")
# de-dupe in case a fund hit its exact min drawdown value on more than one date
drawdown_table = drawdown_table.drop_duplicates(subset="amfi_code")

drawdown_table.to_csv(os.path.join(PROCESSED_DIR, "max_drawdown.csv"), index=False)
print("Saved max_drawdown.csv (" + str(len(drawdown_table)) + " funds)")

print()
print("=" * 60)
print("Fund Scorecard")
print("=" * 60)

scorecard = cagr_table[["amfi_code", "scheme_name", "category", "cagr_3yr"]].copy()
scorecard = scorecard.merge(sharpe_table[["amfi_code", "sharpe_ratio"]], on="amfi_code", how="left")
scorecard = scorecard.merge(alpha_beta_df[["amfi_code", "alpha"]], on="amfi_code", how="left")
scorecard = scorecard.merge(fund_master[["amfi_code", "expense_ratio_pct"]], on="amfi_code", how="left")
scorecard = scorecard.merge(drawdown_table[["amfi_code", "max_drawdown"]], on="amfi_code", how="left")

scorecard["cagr_3yr_rank"] = scorecard["cagr_3yr"].rank(ascending=False)
scorecard["sharpe_rank"] = scorecard["sharpe_ratio"].rank(ascending=False)
scorecard["alpha_rank"] = scorecard["alpha"].rank(ascending=False)
scorecard["expense_rank"] = scorecard["expense_ratio_pct"].rank(ascending=True)
scorecard["max_dd_rank"] = scorecard["max_drawdown"].rank(ascending=False)

n = len(scorecard)
scorecard["cagr_3yr_score"] = (n - scorecard["cagr_3yr_rank"] + 1) / n * 100
scorecard["sharpe_score"] = (n - scorecard["sharpe_rank"] + 1) / n * 100
scorecard["alpha_score"] = (n - scorecard["alpha_rank"] + 1) / n * 100
scorecard["expense_score"] = (n - scorecard["expense_rank"] + 1) / n * 100
scorecard["max_dd_score"] = (n - scorecard["max_dd_rank"] + 1) / n * 100

scorecard["fund_score"] = (
    0.30 * scorecard["cagr_3yr_score"] +
    0.25 * scorecard["sharpe_score"] +
    0.20 * scorecard["alpha_score"] +
    0.15 * scorecard["expense_score"] +
    0.10 * scorecard["max_dd_score"]
)

fund_scorecard = scorecard[[
    "amfi_code", "scheme_name", "category", "cagr_3yr", "sharpe_ratio",
    "alpha", "expense_ratio_pct", "max_drawdown", "fund_score"
]].copy()
fund_scorecard = fund_scorecard.sort_values("fund_score", ascending=False).reset_index(drop=True)
fund_scorecard["overall_rank"] = fund_scorecard.index + 1

fund_scorecard.to_csv(os.path.join(PROCESSED_DIR, "fund_scorecard.csv"), index=False)
print("Saved fund_scorecard.csv — #1:", fund_scorecard.iloc[0]["scheme_name"],
      f"({fund_scorecard.iloc[0]['fund_score']:.2f}/100)")

print()
print("=" * 60)
print("Benchmark comparison chart (Top 5 vs NIFTY 50 / NIFTY 100)")
print("=" * 60)

top5 = fund_scorecard.head(5)
top5_codes = top5["amfi_code"].tolist()

nifty50 = benchmark_df[benchmark_df["index_name"] == "NIFTY50"].copy()
nifty50 = nifty50.sort_values("date")
nifty50["benchmark_return"] = nifty50["close_value"].pct_change()

chart_start = target_date_3yr

nav_3yr = nav_df[(nav_df["amfi_code"].isin(top5_codes)) & (nav_df["date"] >= chart_start)].copy()
nav_3yr = nav_3yr.sort_values(["amfi_code", "date"])
start_navs_3yr = nav_3yr.groupby("amfi_code")["nav"].transform("first")
nav_3yr["growth_index"] = 100 * (nav_3yr["nav"] / start_navs_3yr)

nifty50_3yr = nifty50[nifty50["date"] >= chart_start].copy()
nifty50_3yr["growth_index"] = 100 * (nifty50_3yr["close_value"] / nifty50_3yr["close_value"].iloc[0])

nifty100_3yr = nifty100[nifty100["date"] >= chart_start].copy()
nifty100_3yr["growth_index"] = 100 * (nifty100_3yr["close_value"] / nifty100_3yr["close_value"].iloc[0])

plt.figure(figsize=(12, 7))
for code in top5_codes:
    fund_data = nav_3yr[nav_3yr["amfi_code"] == code]
    fund_name = fund_master[fund_master["amfi_code"] == code]["scheme_name"].values[0]
    plt.plot(fund_data["date"], fund_data["growth_index"], label=fund_name)

plt.plot(nifty50_3yr["date"], nifty50_3yr["growth_index"], label="NIFTY 50", color="black", linestyle="--", linewidth=2)
plt.plot(nifty100_3yr["date"], nifty100_3yr["growth_index"], label="NIFTY 100", color="gray", linestyle="--", linewidth=2)

plt.title("Top 5 Funds vs Nifty 50 / Nifty 100 — Growth of ₹100 (3yr)")
plt.xlabel("Date")
plt.ylabel("Growth of ₹100 Invested")
plt.legend(loc="upper left", fontsize=8)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "benchmark_comparison_top5.png"), dpi=150)
plt.close()

print("Saved benchmark_comparison_top5.png")

# ===========================================================================
# ADVANCED ANALYTICS
# ===========================================================================

print()
print("=" * 60)
print("VaR (95%) and CVaR")
print("=" * 60)

var_cvar = nav_df.groupby("amfi_code")["daily_return"].quantile(0.05).reset_index()
var_cvar.columns = ["amfi_code", "var_95"]

cvar_list = []
for code in var_cvar["amfi_code"]:
    threshold = var_cvar.loc[var_cvar["amfi_code"] == code, "var_95"].values[0]
    fund_returns = nav_df.loc[nav_df["amfi_code"] == code, "daily_return"]
    cvar_value = fund_returns[fund_returns <= threshold].mean()
    cvar_list.append(cvar_value)
var_cvar["cvar_95"] = cvar_list

var_cvar_report = var_cvar.merge(
    fund_master[["amfi_code", "scheme_name", "category", "risk_category"]], on="amfi_code", how="left"
)
var_cvar_report = var_cvar_report[["amfi_code", "scheme_name", "category", "risk_category", "var_95", "cvar_95"]]

var_cvar_report.to_csv(os.path.join(REPORTS_DIR, "var_cvar_report.csv"), index=False)
print("Saved var_cvar_report.csv")

print()
print("=" * 60)
print("Rolling 90-day Sharpe Ratio (Top 5 by Sharpe)")
print("=" * 60)

nav_df["rolling_mean"] = nav_df.groupby("amfi_code")["daily_return"].transform(lambda x: x.rolling(90).mean())
nav_df["rolling_std"] = nav_df.groupby("amfi_code")["daily_return"].transform(lambda x: x.rolling(90).std())
nav_df["rolling_sharpe"] = (nav_df["rolling_mean"] / nav_df["rolling_std"]) * np.sqrt(252)

top5_sharpe_funds = fund_scorecard.nlargest(5, "sharpe_ratio")
top5_sharpe_codes = top5_sharpe_funds["amfi_code"].tolist()

plt.figure(figsize=(14, 7))
for code in top5_sharpe_codes:
    fund_data = nav_df[nav_df["amfi_code"] == code]
    fund_name = fund_master.loc[fund_master["amfi_code"] == code, "scheme_name"].values[0]
    plt.plot(fund_data["date"], fund_data["rolling_sharpe"], label=fund_name)

plt.xlabel("Date")
plt.ylabel("Rolling 90-Day Sharpe Ratio")
plt.title("Rolling 90-Day Sharpe Ratio — Top 5 Funds")
plt.legend(loc="best", fontsize=8)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(CHARTS_DIR, "rolling_sharpe_chart.png"), dpi=150)
plt.close()

print("Saved rolling_sharpe_chart.png")

print()
print("=" * 60)
print("Investor Cohort Analysis")
print("=" * 60)

first_txn_year = investor_txn.groupby("investor_id")["transaction_date"].min().dt.year.reset_index()
first_txn_year.columns = ["investor_id", "cohort_year"]
investor_txn = investor_txn.merge(first_txn_year, on="investor_id", how="left")

avg_sip_by_cohort = investor_txn[investor_txn["transaction_type"] == "SIP"].groupby("cohort_year")["amount_inr"].mean().reset_index()
avg_sip_by_cohort.columns = ["cohort_year", "avg_sip_amount"]

invested_only = investor_txn[investor_txn["transaction_type"].isin(["SIP", "Lumpsum"])]
total_invested_by_cohort = invested_only.groupby("cohort_year")["amount_inr"].sum().reset_index()
total_invested_by_cohort.columns = ["cohort_year", "total_invested"]

fund_counts = investor_txn.groupby(["cohort_year", "amfi_code"]).size().reset_index(name="txn_count")
top_fund_per_cohort = fund_counts.sort_values("txn_count", ascending=False).groupby("cohort_year").head(1)
top_fund_per_cohort = top_fund_per_cohort.merge(fund_master[["amfi_code", "scheme_name"]], on="amfi_code", how="left")
top_fund_per_cohort = top_fund_per_cohort[["cohort_year", "scheme_name", "txn_count"]]
top_fund_per_cohort.columns = ["cohort_year", "top_fund", "top_fund_txn_count"]

cohort_summary = avg_sip_by_cohort.merge(total_invested_by_cohort, on="cohort_year")
cohort_summary = cohort_summary.merge(top_fund_per_cohort, on="cohort_year")

cohort_summary.to_csv(os.path.join(PROCESSED_DIR, "cohort_summary.csv"), index=False)
print("Saved cohort_summary.csv (previously not saved by the notebook)")

print()
print("=" * 60)
print("SIP Continuity Analysis")
print("=" * 60)

sip_txns = investor_txn[investor_txn["transaction_type"] == "SIP"].copy()
sip_txns = sip_txns.sort_values(["investor_id", "transaction_date"])
sip_txns["gap_days"] = sip_txns.groupby("investor_id")["transaction_date"].diff().dt.days

sip_investor_stats = sip_txns.groupby("investor_id").agg(
    sip_count=("transaction_date", "count"),
    avg_gap_days=("gap_days", "mean")
).reset_index()

sip_continuity = sip_investor_stats[sip_investor_stats["sip_count"] >= 6].copy()
sip_continuity["at_risk"] = sip_continuity["avg_gap_days"] > 35

sip_continuity.to_csv(os.path.join(PROCESSED_DIR, "sip_continuity.csv"), index=False)
print("Saved sip_continuity.csv (previously not saved by the notebook) —",
      sip_continuity["at_risk"].sum(), "of", len(sip_continuity), "investors flagged at-risk")

print()
print("=" * 60)
print("Sector HHI Concentration (Equity funds)")
print("=" * 60)

sector_weights = portfolio_holdings.groupby(["amfi_code", "sector"])["weight_pct"].sum().reset_index()
sector_weights["weight_frac"] = sector_weights["weight_pct"] / 100
sector_weights["weight_sq"] = sector_weights["weight_frac"] ** 2

hhi_by_fund = sector_weights.groupby("amfi_code")["weight_sq"].sum().reset_index()
hhi_by_fund.columns = ["amfi_code", "hhi"]

hhi_report = hhi_by_fund.merge(fund_master[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
hhi_equity = hhi_report[hhi_report["category"] == "Equity"].sort_values("hhi", ascending=False)

hhi_equity.to_csv(os.path.join(PROCESSED_DIR, "sector_hhi_equity.csv"), index=False)
print("Saved sector_hhi_equity.csv (previously not saved by the notebook)")

print()
print("=" * 60)
print("Regenerating recommender.py")
print("=" * 60)

recommender_code = '''
import pandas as pd

# Load the data
fund_scorecard = pd.read_csv('data/processed/fund_scorecard.csv')
fund_master = pd.read_csv('data/processed/fund_master_cleaned.csv')

recommender_data = fund_scorecard.merge(fund_master[['amfi_code', 'risk_category']], on='amfi_code', how='left')

# Get user input
print("Enter your risk appetite: Low / Moderate / High")
risk_input = input("> ").strip().title()

# Filter and rank
matched_funds = recommender_data[recommender_data['risk_category'] == risk_input]

if matched_funds.empty:
    print("No funds found for risk category:", risk_input)
    print("Valid options are: Low, Moderate, High")
else:
    top3 = matched_funds.nlargest(3, 'sharpe_ratio')[['scheme_name', 'risk_category', 'sharpe_ratio']]
    print("\\nTop 3 Recommended Funds for", risk_input, "Risk Appetite:")
    print(top3.to_string(index=False))
'''

with open(os.path.join(SCRIPT_DIR, "recommender.py"), "w") as f:
    f.write(recommender_code)

print("Saved recommender.py to", SCRIPT_DIR)

print()
print("=" * 60)
print("COMPUTE METRICS COMPLETE")
print("=" * 60)
print("NOTE: tracking_error_top5.csv was NOT generated — no source logic")
print("exists for it in either notebook. Needs to be designed separately.")

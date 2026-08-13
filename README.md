# Bluestock Mutual Fund Analysis — Capstone Project

End-to-end analysis of the Indian mutual fund industry: ETL, exploratory data
analysis, performance & risk analytics, and a four-page Power BI dashboard —
built during a data analyst internship at **Bluestock Fintech**.


📄 **Full report:** [`Final_Report.pdf`](./reports/Final_Report.pdf)
📊 **Presentation:** [`Bluestock_MF_Presentation.pptx`](./reports/Bluestock_MF_Presentation.pptx)

---

## Project Overview

The project analyses 40 mutual fund schemes across India's 10 largest fund
houses, using a synthetic dataset calibrated against real AMFI industry
benchmarks (SIP inflows, folio counts). The pipeline covers:

- **ETL** — 10 raw CSVs cleaned and loaded into a star-schema SQLite database
  (`bluestock_mf.db`), validated with 10 SQL queries.
- **EDA** — NAV trends, AUM growth, SIP inflows, investor demographics,
  geography, and sector allocation (`EDA_analysis.ipynb`).
- **Performance & Risk Analytics** — CAGR, Sharpe, Sortino, Alpha/Beta (OLS),
  max drawdown, and a composite 0–100 Fund Scorecard
  (`Performance_Analytics.ipynb`).
- **Advanced Analytics** — VaR/CVaR, rolling Sharpe ratio, investor cohort
  behaviour, SIP continuity risk, a simple fund recommender, and sector
  concentration (HHI) (`Advanced_Analytics.ipynb`).
- **Power BI Dashboard** — a 4-page interactive report (Industry Overview,
  Fund Performance, Investor Analytics, SIP & Market Trends) on a cleaned
  star-schema data model.

See  [`Final_Report.pdf`](./reports/Final_Report.pdf) for full findings, methodology,
known data gaps, and recommendations.

---

## Repository Structure

```
Mutual-Fund-Analysis/
├── data/
│   ├── raw/                  # 10 original source CSVs
│   └── processed/            # Cleaned CSVs + deliverables (fund_scorecard.csv,
│                              # alpha_beta.csv, max_drawdown.csv, etc.)
├── notebooks/
│   ├── ETL_pipeline.ipynb        # raw CSVs -> cleaned data -> SQLite DB
│   ├── EDA_analysis.ipynb        # 9 exploratory findings
│   ├── Performance_Analytics.ipynb
│   └── Advanced_Analytics.ipynb
├── reports/
│   ├── charts/                # exported PNG charts
│   └── *.csv                  # analysis output tables
├── dashboard/
│   └── bluestock_mf_dashboard.pbix
├── bluestock_mf.db            # star-schema SQLite database (committed deliverable)
├── recommender.py             # standalone fund recommender CLI
├── run_pipeline.py            # master script — runs the full pipeline in order
├── requirements.txt
└── README.md
```

> **Note:** paths above reflect the project's intended layout. If your local
> checkout differs (e.g. the ETL notebook has a different filename), update
> the `NOTEBOOKS` dict at the top of `run_pipeline.py` to match.

---

## Setup Instructions

**Requirements:** Python 3.10+, Git, Power BI Desktop (Windows, for the
dashboard only).

```bash
# 1. Clone the repository
git clone https://github.com/aksheyei/Mutual-Fund-Analysis.git
cd Mutual-Fund-Analysis

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

`requirements.txt` should include, at minimum:

```
pandas
numpy
matplotlib
seaborn
plotly
kaleido
scipy
sqlalchemy
jupyter
```

---

## How to Run the ETL Pipeline

**Option A — run everything in order:**

```bash
python run_pipeline.py
```

**Option B — run a single stage** (e.g. just re-run EDA after a data fix):

```bash
python run_pipeline.py --stage eda
```

**Option C — run a stage and everything after it:**

```bash
python run_pipeline.py --from performance
```

**Option D — step through manually in Jupyter:**

```bash
jupyter notebook notebooks/ETL_pipeline.ipynb
```

Each notebook writes its outputs (cleaned CSVs, charts, deliverable tables)
to `data/processed/` and `reports/`. Notebooks execute from inside
`notebooks/`, so all relative paths reference `../data/processed/` and
`../reports/` — keep this in mind if you run cells manually outside of
`run_pipeline.py`.

---

## How to Open the Dashboard

1. Install [Power BI Desktop](https://www.microsoft.com/power-bi/desktop) (free, Windows only).
2. Open `dashboard/bluestock_mf_dashboard.pbix`.
3. If prompted, update the data source path to point at your local
   `bluestock_mf.db` / `data/processed/` files, then **Refresh**.
4. Use the page navigator on the left to move between **Industry Overview**,
   **Fund Performance**, **Investor Analytics**, and **SIP & Market Trends**.

*(Optional) Published dashboard:* if published to Power BI Service or
Tableau Public, the live link will be added here.

**🔗 Live dashboard:** _[add Power BI Service / Tableau Public URL here]_

---

## Dataset Descriptions

| File | Description |
|---|---|
| `dim_fund` | One row per scheme — AMFI code, scheme name, fund house, category, plan (Direct/Regular), risk classification |
| `dim_date` | Shared calendar dimension (date, year, month, quarter, weekday) used by every fact table |
| `fact_nav` | Daily NAV per scheme |
| `fact_transactions` | Investor-level SIP / lumpsum / redemption transactions |
| `fact_industry_metrics` | Monthly industry AUM, SIP inflow, and folio count series |
| `fund_scorecard.csv` | Composite 0–100 Fund Score per scheme (CAGR, Sharpe, Alpha, expense ratio, max drawdown) |
| `alpha_beta.csv` | OLS-estimated Alpha and Beta per scheme vs. its benchmark index |
| `max_drawdown.csv` | Largest peak-to-trough NAV decline per scheme, with trough date |
| `var_cvar_report.csv` | 95% daily Value-at-Risk and Conditional VaR per scheme |

Full column-level definitions and known data-quality caveats (unmatched
benchmarks, pre-2018 fund naming, synthetic-data artifacts in Alpha/Beta)
are documented in **Section 8 (Limitations & Data Gaps)** of
[`Final_Report.pdf`](./Final_Report.pdf).

---

## Known Limitations

- 5-year CAGR is not computable (only ~4.4 years of NAV history) — left as `NA`.
- Three benchmark indices (Midcap 50, Large Midcap 250, Short Term Bond) have
  no match in `benchmark_indices`.
- Some cleaned records still carry pre-2018 (pre-SEBI-recategorization)
  scheme names, pending mentor confirmation.
- Alpha/Beta and rolling-Sharpe values reflect the dataset's synthetic
  generation (near-zero Beta) and should not be read as real-market figures.

See the full report for details and recommended follow-ups.

---

## License

Internal capstone project for Bluestock Fintech. Not licensed for external
redistribution.

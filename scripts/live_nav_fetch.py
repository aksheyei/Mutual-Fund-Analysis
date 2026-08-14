"""
live_nav_fetch.py

Fetches live/current NAV history from mfapi.in for the 6 funds tracked
outside the static raw CSVs, and saves each to data/raw/.

Extracted from the "FETCHING DATA SCHEMES DATA" section of
01_data_ingestion.ipynb.

Run from anywhere:
    python scripts/live_nav_fetch.py
"""

import os
import requests
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")

os.makedirs(RAW_DIR, exist_ok=True)

# (mfapi.in scheme code, output filename)
FUNDS = [
    (119018, "live_nav_hdfc_large_cap.csv"),
    (119598, "live_nav_sbi_large_cap.csv"),
    (118632, "live_nav_nippon_large_cap.csv"),
    (120465, "live_nav_axis_large_cap.csv"),
    (120152, "live_nav_kotak_large_cap.csv"),
    (120586, "live_nav_icici_large_cap.csv"),
]

print("=" * 60)
print("Fetching live NAV data from mfapi.in")
print("=" * 60)

for scheme_code, filename in FUNDS:
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()

    fund_nav = pd.DataFrame(data["data"])
    fund_nav["scheme_code"] = scheme_code
    fund_nav["fund_name"] = data["meta"]["scheme_name"]

    out_path = os.path.join(RAW_DIR, filename)
    fund_nav.to_csv(out_path, index=False)

    print(f"{data['meta']['scheme_name']} ({scheme_code}): "
          f"{len(fund_nav)} rows -> {filename}")

print()
print("=" * 60)
print("LIVE NAV FETCH COMPLETE")
print("=" * 60)

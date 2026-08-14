
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
    print("\nTop 3 Recommended Funds for", risk_input, "Risk Appetite:")
    print(top3.to_string(index=False))

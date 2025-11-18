"""
Simple Streamlit front end to request a string from the user.

How to run:
1) Install Streamlit if needed:
   pip install streamlit

2) Launch the app (from the FY26 directory):
   streamlit run 10-K/edgarSECFrontEnd.py
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np

# SEC API requires a descriptive User-Agent; use your email per SEC guidance
headers = {'User-Agent': "jared.s.woodard@oracle.com"}

def main() -> None:
    # Create the Streamlit front end
    st.set_page_config(page_title="SEC Data Retrieval", page_icon="✍️", layout="centered")
    st.title("SEC Data Retrieval")
    st.write("Enter a stock ticker and submit to fetch its CIK, displayed below in a read-only text box.")

    # Use a form so the app only reacts when the user clicks Submit
    with st.form("ticker_input_form", clear_on_submit=False):
        # User Inputs Ticker Information
        user_input = st.text_input(
            "Ticker",
            placeholder="e.g., AAPL",
            help="Enter a stock ticker symbol (e.g., AAPL, MSFT, TSLA)."
        )
        # User Inputs Competitor Cloud Spend
        competitor_cloud_spend = st.number_input(
                        "Competitor Cloud Spend (USD)",
                        min_value=0.0,
                        step=1000000.0,
                        format="%.2f",
                        help="Enter the competitor's annual cloud spend in USD."
        )
        submitted = st.form_submit_button("Submit")

    if submitted:
        clean = user_input.strip().upper()
        if clean:
            try:
                cik = getCIK(clean)
            except Exception as e:
                st.error(f"Error looking up CIK: {e}")
                cik = None

            st.divider()
            st.subheader("Results")

            if cik:
                st.success(f"Ticker: {clean}")
                st.text_input("CIK", value=str(cik), disabled=True)

                # Start a metrics table with one row for Revenue
                column_names = ['Metric', 'Value', 'Form', 'Submission Date']
                display_table = pd.DataFrame(columns=column_names)
                
                revenue_row = getRevenue(cik)
                if len(revenue_row) == 4:
                    display_table.loc[len(display_table)] = revenue_row
                
                cost_row = getCostRevenue(cik)
                if len(cost_row) == 4:
                    display_table.loc[len(display_table)] = cost_row

                # Check that both rows are valid and share the same filed date
                if len(revenue_row) == 4 and len(cost_row) == 4 and revenue_row[-1] == cost_row[-1]:
                    gross_margin_list = ['Gross Margin', str(round((cost_row[1] / revenue_row[1])*100, 2)) + "%", revenue_row[2], revenue_row[-1]]
                    display_table.loc[len(display_table)] = np.array(gross_margin_list)


                
                profit_row = getGrossProfit(cik)
                if len(profit_row) == 4:
                    display_table.loc[len(display_table)] = profit_row
                
                

                sga_row = getSGA(cik)
                if len(sga_row) == 4:
                    display_table.loc[len(display_table)] = sga_row

                # Check that revenue and SG&A rows are valid and share the same filed date
                if len(revenue_row) == 4 and len(sga_row) == 4 and revenue_row[-1] == sga_row[-1]:
                    sga_margin_list = ['SGA Percent of Revenue', str(round((sga_row[1] / revenue_row[1])*100, 2)) + "%", revenue_row[2], revenue_row[-1]]
                    display_table.loc[len(display_table)] = np.array(sga_margin_list)
                
                if len(profit_row) == 4 and len(sga_row) == 4 and profit_row[-1] == sga_row[-1]:
                    operating_profit_list = ['Operating Profit', round(profit_row[1] - sga_row[1], 2), profit_row[2], profit_row[-1]]
                    display_table.loc[len(display_table)] = np.array(operating_profit_list)
                else:
                    operating_profit_list = []
                
                
                # Check that revenue and Operating Profit rows are valid and share the same filed date
                if len(revenue_row) == 4 and len(operating_profit_list) == 4 and revenue_row[-1] == operating_profit_list[-1]:
                    operating_profit_margin_list = ['Operating Margin', str(round((operating_profit_list[1] / revenue_row[1])*100, 2)) + "%" , revenue_row[2], revenue_row[-1]]
                    display_table.loc[len(display_table)] = np.array(operating_profit_margin_list)
                
                interest_row = getInterestExpense(cik)
                if len(interest_row) == 4:
                    display_table.loc[len(display_table)] = interest_row

                income_row = getIncomeExpense(cik)
                if len(income_row) == 4:
                    display_table.loc[len(display_table)] = income_row
                
                income_tax_row = getIncomeTax(cik)
                if len(income_tax_row) == 4:
                    display_table.loc[len(display_table)] = income_tax_row

                tax_row = getTaxRate(cik)
                if len(tax_row) == 4:
                    display_table.loc[len(display_table)] = tax_row


                # Net Income = Operating Profit - Interest Expense - Other Income (Expense) - Income Taxes
                net_income_row = []
                if (
                    len(operating_profit_list) == 4
                    and len(interest_row) == 4
                    and len(income_row) == 4
                    and len(income_tax_row) == 4
                    and operating_profit_list[-1] == interest_row[-1] == income_row[-1] == income_tax_row[-1]
                ):
                    net_income_val = int(round(
                        float(operating_profit_list[1])
                        - float(interest_row[1])
                        - float(income_row[1])
                        - float(income_tax_row[1]),
                        2
                    ))
                    net_income_row = np.array(['Net Income', net_income_val, operating_profit_list[2], operating_profit_list[-1]])
                    display_table.loc[len(display_table)] = net_income_row

                shares_row = getShares(cik)
                if len(shares_row) == 4:
                     display_table.loc[len(display_table)] = shares_row

                income_share_list = []
                if len(shares_row) == 4 and len(net_income_row) == 4 and shares_row[-1] == net_income_row[-1]:
                    income_share_list = ['Net Income per share - Diluted', round(float(net_income_row[1]) / float(shares_row[1]), 2), shares_row[2], shares_row[-1]]
                    display_table.loc[len(display_table)] = np.array(income_share_list)


                # Ensure Arrow-compatible types for Streamlit table serialization
                if 'Value' in display_table.columns:
                    display_table['Value'] = display_table['Value'].astype(str)

                st.table(display_table)

                

                # Derived table with two columns; first row shows 53% of competitor spend as OCI Spend
                spend_table = pd.DataFrame(columns=["Metric", "Value"])

                if len(sga_row) == 4:
                    percent_sga = round(float((competitor_cloud_spend / sga_row[1]))*100, 2)
                    spend_table.loc[len(spend_table)] = np.array(["% of SGA for Original Tech Spend", f"{percent_sga:,.2f}%"])
                
                oci_spend = round(float(competitor_cloud_spend) * 0.53, 2) - round(float(competitor_cloud_spend) * 0.53 *.25, 2)
                spend_table.loc[len(spend_table)] = np.array(["OCI Spend (Including Support Rewards)", f"${oci_spend:,.2f}"])

                tech_saved =  abs(oci_spend - competitor_cloud_spend)
                spend_table.loc[len(spend_table)] = np.array(["Amount Saved (Between OCI & Origional Cloud Spend)", f"${tech_saved:,.2f}"])

                if len(sga_row) == 4:
                    oci_sga = sga_row[1] - tech_saved
                    spend_table.loc[len(spend_table)] = np.array(["SGA when Using OCI", f"${oci_sga:,.2f}"])
                
                if len(revenue_row) == 4 and len(sga_row) == 4 and revenue_row[-1] == sga_row[-1]:
                    oci_sga_margin = round((oci_sga / revenue_row[1])*100, 2)
                    spend_table.loc[len(spend_table)] = np.array(["SGA percent of Revenue (with OCI)", f"{oci_sga_margin:,.2f}%"])

                    sga_change = round((sga_row[1] / revenue_row[1])*100, 2) - oci_sga_margin
                    spend_table.loc[len(spend_table)] = np.array(["Change In SGA percent of Revenue", f"{sga_change:,.2f}%"])
                
                if len(operating_profit_list) == 4:
                    oci_op_profit = operating_profit_list[1] - tech_saved
                    spend_table.loc[len(spend_table)] = np.array(["Operating Profit", f"${oci_sga:,.2f}"])
                
                if len(revenue_row) == 4 and len(operating_profit_list) == 4 and revenue_row[-1] == operating_profit_list[-1]:
                    oci_op_margin = round((oci_op_profit / revenue_row[1])*100, 2) 
                    spend_table.loc[len(spend_table)] = np.array(["Operating Profit Margin (with OCI)", f"{oci_op_margin:,.2f}%"])

                    op_margin_change = round((operating_profit_list[1] / revenue_row[1])*100, 2) - oci_op_margin
                    spend_table.loc[len(spend_table)] = np.array(["Change In Operating Margin", f"{op_margin_change:,.2f}%"])

                if len(net_income_row) == 4:
                    oci_net_income = int(net_income_val) + tech_saved
                    spend_table.loc[len(spend_table)] = np.array(["Net Income (with OCI)", f"${oci_net_income:,.2f}"])

                if len(income_share_list) == 4:
                    oci_income_shares = round(oci_net_income / float(shares_row[1]), 2)
                    oci_shares_change = abs(round(float(net_income_val) / float(shares_row[1]), 2) - oci_income_shares)

                    spend_table.loc[len(spend_table)] = np.array(["Net Income per share - Diluted (with OCI)", f"${oci_income_shares:,.2f}"])
                    spend_table.loc[len(spend_table)] = np.array(["Net Income per share - Diluted (change)", f"${oci_shares_change:,.2f}"])

                st.table(spend_table)
            else:
                st.warning("Ticker not found. Please verify the symbol.")
                st.text_input("CIK", value="Not found", disabled=True)
        else:
            st.warning("Please enter a non-empty ticker.")


def getCIK(ticker):
    companyTickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
    # Turn Dict into Data Frame
    companyData = pd.DataFrame.from_dict(companyTickers.json(), orient='index')

    # add leading zeros to CIK
    companyData['cik_str'] = companyData['cik_str'].astype(str).str.zfill(10)
    result = companyData.loc[companyData['ticker'].str.upper() == ticker.upper(), 'cik_str']
    return result.iloc[0] if not result.empty else None


def getRevenue(cik):
    """
    Return a dict for the most recent 10-K Revenue using only the filed date to determine recency.
    Keys: metric, value, date, form.
    """
    try:
        revenueJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/Revenues.json",
            headers=headers,
            timeout=30,
        )
        revenueDF = pd.DataFrame.from_dict((revenueJSON.json()['units']['USD']))
        RevenueDF_10k = revenueDF[revenueDF["form"] == "10-K"]
        RevenueDF_10k_ss = RevenueDF_10k[["val", "form", "filed"]]
        row = RevenueDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Revenue')
        return row
    except Exception:
        return []
    
def getCostRevenue(cik):
    """
    Return a dict for the most recent 10-K Revenue using only the filed date to determine recency.
    Keys: metric, value, date, form.
    """
    try:
        costJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/CostOfRevenue.json",
            headers=headers,
            timeout=30,
        )
        costDF = pd.DataFrame.from_dict((costJSON.json()['units']['USD']))
        costDF_10k = costDF[costDF["form"] == "10-K"]
        costDF_10k_ss = costDF_10k[["val", "form", "filed"]]
        row = costDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Cost Of Revenue')
        return row
    except Exception:
        return []
    


def getGrossProfit(cik):
    """
    Return a row for the most recent 10-K Gross Profit using only the filed date to determine recency.
    Returns an array: ['Gross Profit', val, form, filed]
    """
    try:
        profitJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/GrossProfit.json",
            headers=headers,
            timeout=30,
        )
        profitDF = pd.DataFrame.from_dict((profitJSON.json()['units']['USD']))
        profitDF_10k = profitDF[profitDF["form"] == "10-K"]
        profitDF_10k_ss = profitDF_10k[["val", "form", "filed"]]
        row = profitDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Gross Profit')
        return row
    except Exception:
        return []

def getSGA(cik):
    """
    Return a row for the most recent 10-K Selling, General and Administrative Expense
    using only the filed date to determine recency.
    Returns an array: ['SG&A', val, form, filed]
    """
    try:
        sgaJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/SellingGeneralAndAdministrativeExpense.json",
            headers=headers,
            timeout=30,
        )
        sgaDF = pd.DataFrame.from_dict((sgaJSON.json()['units']['USD']))
        sgaDF_10k = sgaDF[sgaDF["form"] == "10-K"]
        sgaDF_10k_ss = sgaDF_10k[["val", "form", "filed"]]
        row = sgaDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Selling, General & Admin Costs')
        return row
    except Exception:
        return []

def getInterestExpense(cik):
    """
    Return a row for the most recent 10-K Interest Expense
    using only the filed date to determine recency.
    Returns an array: ['Interest Expense', val, form, filed]
    """
    try:
        interestJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/InterestExpense.json",
            headers=headers,
            timeout=30,
        )
        interestDF = pd.DataFrame.from_dict((interestJSON.json()['units']['USD']))
        interestDF_10k = interestDF[interestDF["form"] == "10-K"]
        interestDF_10k_ss = interestDF_10k[["val", "form", "filed"]]
        row = interestDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Interest Expense')
        return row
    except Exception:
        return []

def getIncomeExpense(cik):
    """
    Return a row for the most recent 10-K Other Nonoperating Income (Expense), net
    using only the filed date to determine recency.
    Returns an array: ['Other Nonoperating Income (Expense), net', val, form, filed]
    """
    try:
        incomeExpenseJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/OtherNonoperatingIncomeExpense.json",
            headers=headers,
            timeout=30,
        )
        incomeExpenseDF = pd.DataFrame.from_dict((incomeExpenseJSON.json()['units']['USD']))
        incomeExpenseDF_10k = incomeExpenseDF[incomeExpenseDF["form"] == "10-K"]
        incomeExpenseDF_10k_ss = incomeExpenseDF_10k[["val", "form", "filed"]]
        row = incomeExpenseDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Other Nonoperating Income (Expense), net')
        row[1] = abs(row[1])
        return row
    except Exception:
        return []

def getIncomeTax(cik):
    """
    Return a row for the most recent 10-K Income Taxes Paid, Net
    using only the filed date to determine recency.
    Returns an array: ['Income Taxes Paid, Net', val, form, filed]
    """
    try:
        incomeTaxJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/IncomeTaxesPaidNet.json",
            headers=headers,
            timeout=30,
        )
        incomeTaxDF = pd.DataFrame.from_dict((incomeTaxJSON.json()['units']['USD']))
        incomeTaxDF_10k = incomeTaxDF[incomeTaxDF["form"] == "10-K"]
        incomeTaxDF_10k_ss = incomeTaxDF_10k[["val", "form", "filed"]]
        row = incomeTaxDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Income Taxes Paid, Net')
        return row
    except Exception:
        return []

def getTaxRate(cik):
    """
    Return a row for the most recent 10-K Effective Tax Rate (Continuing Operations)
    using only the filed date to determine recency.
    Returns an array: ['Effective Tax Rate', val, form, filed]
    """
    try:
        taxJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/EffectiveIncomeTaxRateContinuingOperations.json",
            headers=headers,
            timeout=30,
        )
        taxDF = pd.DataFrame.from_dict((taxJSON.json()['units']['pure']))
        taxDF_10k = taxDF[taxDF["form"] == "10-K"]
        taxDF_10k_ss = taxDF_10k[["val", "form", "filed"]]
        row = taxDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Effective Tax Rate')
        row[1] = str(row[1]*100) + "%"
        return row
    except Exception:
        return []

def getShares(cik):
    """
    Return a row for the most recent 10-K Common Stock Shares Outstanding
    using only the filed date to determine recency.
    Returns an array: ['Common Stock Shares Outstanding', val, form, filed]
    """
    try:
        sharesJSON = requests.get(
            f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/CommonStockSharesOutstanding.json",
            headers=headers,
            timeout=30,
        )
        sharesDF = pd.DataFrame.from_dict((sharesJSON.json()['units']['shares']))
        sharesDF_10k = sharesDF[sharesDF["form"] == "10-K"]
        sharesDF_10k_ss = sharesDF_10k[["val", "form", "filed"]]
        row = sharesDF_10k_ss.iloc[-1:].to_numpy()
        row = np.insert(row, 0, 'Common Stock Shares Outstanding')
        return row
    except Exception:
        return []

if __name__ == "__main__":
    main()

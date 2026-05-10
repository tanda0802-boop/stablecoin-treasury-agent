import streamlit as st
from project_manager import run_fintech_flow

st.set_page_config(page_title="AI Credit + Treasury Risk Platform", layout="wide")

st.title("AI Credit + Treasury Risk Platform")
st.write(
    "This demo combines underwriting, treasury payment review, liquidity controls, "
    "stablecoin/network risk, and execution decisioning."
)

default_input = """
Borrower requests a 25000 loan for debt consolidation.
Credit score: 680.
Annual income: 85000.
Existing monthly debt payments: 2500.
New loan payment: 3000.
Loan replaces existing debt: yes.

Treasury payment:
Send 25000 USDC on Tron.
Purpose: Loan disbursement.
Wallet address: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e.
Vendor is approved.
"""

user_input = st.text_area("Enter borrower and treasury payment details:", default_input, height=260)

if st.button("Run AI Risk Workflow"):
    try:
        result = result = run_fintech_flow()

        st.subheader("Credit Decision")
        st.write(result.get("credit_decision", "Not available"))

        st.subheader("Treasury Decision")
        treasury_result = result.get("treasury_result")
        if treasury_result:
            st.write(treasury_result.get("final_decision", "Not available"))

            st.subheader("Treasury Memo")
            st.text(treasury_result.get("memo", "No memo available"))

            if "liquidity_result" in treasury_result:
                st.subheader("Liquidity Assessment")
                st.json(treasury_result["liquidity_result"])

        st.subheader("Execution Result")
        st.json(result.get("execution_result", result))

        st.subheader("Full Result")
        st.json(result)

    except Exception as e:
        st.error("The workflow failed.")
        st.exception(e)
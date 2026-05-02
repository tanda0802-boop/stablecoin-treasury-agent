import streamlit as st
from treasury_agent import run_treasury_agent

st.title("Stablecoin Treasury Payment Agent")

st.write(
    "Paste a stablecoin payment request below. Include amount, currency, wallet address, "
    "payment purpose, vendor status, and blockchain network."
)

payment_request = st.text_area(
    "Payment request",
    value="""Pay vendor Acme Analytics 12000 USDC on Ethereum.
    Purpose: monthly data services invoice.
    Wallet address: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e.
    Vendor is approved. Payment is due today."""
)

if st.button("Run Treasury Review"):
    result = run_treasury_agent(payment_request)

    # 🎨 Decision display
    decision = result["decision"]

    st.subheader("Decision")

    if decision == "approve":
        st.success("APPROVE")
    elif decision == "flag":
        st.warning("FLAG - Review Required")
    else:
        st.error("REJECT")

    st.divider()

    # 📊 Layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parsed Data")
        st.json(result["parsed"])

    with col2:
        st.subheader("Issues")
        if result["issues"]:
            for issue in result["issues"]:
                st.write("•", issue)
        else:
            st.write("No issues identified")

    st.divider()

    # 🧾 Memo
    st.subheader("Treasury Memo")
    st.code(result["memo"])

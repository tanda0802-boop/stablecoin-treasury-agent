"""Presentation-only Streamlit dashboard for the existing Credit + Treasury workflow.

Replace the repository's app.py with this file; project_manager.py and
 treasury_agent.py remain unchanged.
"""
import streamlit as st
from project_manager import run_fintech_flow

st.set_page_config(page_title="AI Credit + Treasury Risk Platform", layout="wide")


def readable(value):
    if value is None or value == "":
        return "Not available"
    return str(value).replace("_", " ").strip().title()


def dollars(value):
    if isinstance(value, (int, float)):
        return f"${value:,.2f}"
    return "Not available"


def notice_for_decision(value, prefix):
    v = str(value or "").lower()
    msg = f"{prefix}: {readable(value)}"
    if v in ("approve", "approved"):
        st.success(msg)
    elif v in ("approve_with_conditions", "flag", "pass_with_review"):
        st.warning(msg)
    elif v in ("reject", "rejected", "fail", "breach"):
        st.error(msg)
    else:
        st.info(msg)


st.title("AI Credit + Treasury Risk Platform")
st.caption("Credit underwriting, stablecoin payment review, and execution status — demonstration")

default_input = """Borrower requests a 25000 loan for debt consolidation.
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

user_input = st.text_area("Borrower and treasury payment details", default_input, height=240)

if st.button("Run AI Risk Workflow", type="primary"):
    try:
        result = run_fintech_flow(user_input)
        underwriting = result.get("underwriting_result") or {}
        treasury = result.get("treasury_result")

        st.divider()
        st.header("1. Credit underwriting")
        notice_for_decision(result.get("credit_decision"), "Credit decision")
        a, b, c = st.columns(3)
        a.metric("Monthly income", dollars(underwriting.get("monthly_income")))
        b.metric("Post-loan monthly debt", dollars(underwriting.get("post_loan_debt")))
        dti = underwriting.get("post_loan_dti_percent")
        c.metric("Post-loan DTI", f"{dti:.1f}%" if isinstance(dti, (int, float)) else "Not available")
        st.markdown("**Underwriting rationale**")
        reasons = underwriting.get("reasons") or []
        if reasons:
            for reason in reasons:
                st.write(f"• {reason}")
        else:
            st.write("No underwriting rationale supplied.")

        st.divider()
        st.header("2. Stablecoin treasury review")
        if not treasury:
            st.info("Treasury review was not run because the credit application was rejected, or no treasury result was returned.")
        else:
            notice_for_decision(treasury.get("final_decision"), "Treasury decision")
            payment = treasury.get("parsed") or {}
            p1, p2, p3 = st.columns(3)
            amount = payment.get("amount")
            p1.metric("Payment", f"{amount:,.0f} {payment.get('currency', '')}" if isinstance(amount, (int, float)) else "Not available")
            p2.metric("Network", payment.get("network") or "Not available")
            p3.metric("Approval level", payment.get("approval_level") or "Not available")

            q1, q2, q3 = st.columns(3)
            q1.metric("Wallet risk", payment.get("wallet_risk") or "Not available")
            vendor = payment.get("vendor_approved")
            q2.metric("Vendor", "Approved" if vendor is True else "Not approved" if vendor is False else "Not available")
            q3.metric("Purpose", payment.get("purpose") or "Not available")
            if payment.get("wallet_risk_reason"):
                st.caption(f"Wallet assessment: {payment['wallet_risk_reason']}")

            st.markdown("**Issues and review requirements**")
            issues = treasury.get("issues") or []
            if issues:
                for issue in dict.fromkeys(issues):
                    st.write(f"• {issue}")
            else:
                st.success("No treasury issues reported.")

            stablecoin_analysis = treasury.get("stablecoin_analysis") or {}
            if stablecoin_analysis.get("risk_flags"):
                with st.expander("Stablecoin and network risk notes"):
                    for flag in stablecoin_analysis["risk_flags"]:
                        st.write(f"• {flag}")

            st.divider()
            st.header("3. Payment execution")
            execution = treasury.get("execution_result") or {}
            status = execution.get("transaction_status") or "Not available"
            if status == "SUBMITTED":
                st.success(f"Execution status: {readable(status)}")
            elif status == "NOT_EXECUTED":
                st.warning(f"Execution status: {readable(status)}")
            else:
                st.info(f"Execution status: {readable(status)}")
            if execution.get("reason"):
                st.write(execution["reason"])
            if execution.get("transaction_hash"):
                st.caption(f"Demonstration transaction reference: {execution['transaction_hash']}")

            with st.expander("Treasury memo"):
                st.text(treasury.get("memo") or "No memo available")

        with st.expander("Technical details (optional)"):
            st.json(result)

    except Exception as exc:
        st.error("The workflow failed.")
        st.exception(exc)

from treasury_agent import (
    run_treasury_agent,
    assess_liquidity,
    assess_counterparty_exposure
)

import re


def parse_borrower_data(text):
    credit_score_match = re.search(r"credit score:\s*(\d+)", text, re.IGNORECASE)
    annual_income_match = re.search(r"annual income:\s*(\d+)", text, re.IGNORECASE)
    existing_debt_match = re.search(r"existing monthly debt payments:\s*(\d+)", text, re.IGNORECASE)
    new_payment_match = re.search(r"new loan payment:\s*(\d+)", text, re.IGNORECASE)
    loan_amount_match = re.search(r"requests a\s*(\d+)\s*loan", text, re.IGNORECASE)
    replaces_debt_match = re.search(r"loan replaces existing debt:\s*(yes|no)", text, re.IGNORECASE)

    return {
        "credit_score": int(credit_score_match.group(1)) if credit_score_match else None,
        "annual_income": int(annual_income_match.group(1)) if annual_income_match else None,
        "existing_monthly_debt": int(existing_debt_match.group(1)) if existing_debt_match else None,
        "new_loan_payment": int(new_payment_match.group(1)) if new_payment_match else None,
        "loan_amount": int(loan_amount_match.group(1)) if loan_amount_match else None,
        "replaces_debt": replaces_debt_match.group(1).lower() == "yes" if replaces_debt_match else False,
    }


def underwrite_borrower(borrower):
    monthly_income = borrower["annual_income"] / 12

    if borrower["replaces_debt"]:
        post_loan_debt = borrower["new_loan_payment"]
    else:
        post_loan_debt = borrower["existing_monthly_debt"] + borrower["new_loan_payment"]

    dti = post_loan_debt / monthly_income
    dti_percent = round(dti * 100, 1)

    reasons = []

    if borrower["credit_score"] < 620:
        reasons.append("Credit score below minimum threshold")

    if dti > 0.50:
        reasons.append(f"Post-loan DTI is extremely high at {dti_percent}%")

    if borrower["new_loan_payment"] > monthly_income:
        reasons.append("New loan payment exceeds monthly income")

    if borrower["loan_amount"] and borrower["loan_amount"] > borrower["annual_income"]:
        reasons.append("Loan amount exceeds annual income")

    if reasons:
        decision = "reject"
    elif dti > 0.36:
        decision = "approve_with_conditions"
        reasons.append(f"Post-loan DTI is elevated at {dti_percent}%")
    else:
        decision = "approve"
        reasons.append(f"Post-loan DTI is acceptable at {dti_percent}%")

    return {
        "decision": decision,
        "monthly_income": round(monthly_income, 2),
        "post_loan_debt": post_loan_debt,
        "post_loan_dti_percent": dti_percent,
        "reasons": reasons,
    }
def choose_stablecoin(parsed):
    """
    Choose the stablecoin for loan disbursement.

    USDC is the default because it is more conservative.
    USDT is only used if specifically requested.
    """

    requested_stablecoin = parsed.get("requested_stablecoin")

    if requested_stablecoin == "USDT":
        return "USDT"

    return "USDC"


def run_fintech_flow(user_input):
    """
    Temporary project manager / orchestrator.

    Step 1: Simulate credit decision.
    Step 2: If approved, choose stablecoin.
    Step 3: Run liquidity assessment.
    Step 4: Send payment request to treasury agent.
    """
    borrower = parse_borrower_data(user_input)
    underwriting_result = underwrite_borrower(borrower)

    borrower_approved = underwriting_result["decision"] in ["approve", "approve_with_conditions"]
    if borrower_approved:

        loan_amount = 25000

        parsed = {
            "loan_amount": loan_amount,
            "requested_stablecoin": None
        }

        stablecoin = choose_stablecoin(parsed)

        payment_text = f"""
        Send {loan_amount} {stablecoin} to wallet 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
        on Tron
        Purpose: Loan disbursement
        Vendor is approved
        """

        transaction = {
            "amount": loan_amount,
            "stablecoin": stablecoin,
            "network": "Tron",
            "purpose": "Loan disbursement"
        }

        treasury_state = {
            "balances": {
                "USDC": 100000,
                "USDT": 50000,
                "USD": 200000
            },
            "pending_outflows": {
                "USDC": 40000,
                "USDT": 10000
            },
            "expected_inflows": {
                "USDC": 15000,
                "USD": 50000
            }
        }
        exposure_policy = {
            "USDC": 0.70,
            "USDT": 0.25
        }
        liquidity_policy = {
            "minimum_operating_buffer": {
                "USDC": 30000,
                "USDT": 15000,
                "USD": 100000
            },
            "stress_buffer_percent": 0.20,
            "large_payment_threshold": 50000
        }

        liquidity_result = assess_liquidity(
            transaction,
            treasury_state,
            liquidity_policy
        )

        treasury_result = run_treasury_agent(
            payment_text,
            liquidity_result=liquidity_result
        )
        counterparty_result = assess_counterparty_exposure(
            stablecoin,
            treasury_state["balances"],
            exposure_policy
        )
    else:
        treasury_result = None

    return {
        "credit_decision": underwriting_result["decision"],
    "underwriting_result": underwriting_result,
    "treasury_result": treasury_result

    }


if __name__ == "__main__":
    result = run_fintech_flow(borrower_approved=True)

    print("Credit Decision:", result["credit_decision"])

    if result["treasury_result"]:
        print(result["treasury_result"]["memo"])
        print("Execution Result:", result["treasury_result"]["execution_result"])

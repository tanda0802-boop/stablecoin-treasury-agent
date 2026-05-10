from treasury_agent import (
    run_treasury_agent,
    assess_liquidity,
    assess_counterparty_exposure
)

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


def run_fintech_flow(borrower_approved=True):
    """
    Temporary project manager / orchestrator.

    Step 1: Simulate credit decision.
    Step 2: If approved, choose stablecoin.
    Step 3: Run liquidity assessment.
    Step 4: Send payment request to treasury agent.
    """

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
        "credit_decision": "approve" if borrower_approved else "reject",
        "treasury_result": treasury_result
    }


if __name__ == "__main__":
    result = run_fintech_flow(borrower_approved=True)

    print("Credit Decision:", result["credit_decision"])

    if result["treasury_result"]:
        print(result["treasury_result"]["memo"])
        print("Execution Result:", result["treasury_result"]["execution_result"])

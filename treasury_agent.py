import re
SUPPORTED_NETWORKS = ["Ethereum", "Solana", "Tron"]
SUPPORTED_STABLECOINS = ["USDC", "USDT"]
APPROVED_WALLETS = {
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
}
BLOCKED_WALLETS = [
    "0x1111111111111111111111111111111111111111"
]

def parse_payment_request(text):
    amount_match = re.search(r'(\d+)\s*(USDC|USDT)', text)
    address_match = re.search(r'0x[a-fA-F0-9]{40}', text)
    purpose_match = re.search(r'Purpose:\s*(.*)', text)
    network_pattern = "|".join(SUPPORTED_NETWORKS)

    network_match = re.search(
        rf'on ({network_pattern})',
        text,
        re.IGNORECASE
    )
    vendor_approved = "vendor is approved" in text.lower()
   
    return {
        "amount": int(amount_match.group(1)) if amount_match else None,
        "currency": amount_match.group(2) if amount_match else None,
        "network": network_match.group(1) if network_match else None,
        "vendor_approved": vendor_approved,
        "wallet_address": address_match.group(0) if address_match else None,
        "purpose": purpose_match.group(1) if purpose_match else None,
        "raw_text": text
    }
def assess_wallet_risk(parsed):
    wallet = parsed.get("wallet_address")

    if wallet is None:
        return {
            "wallet_risk": "High",
            "wallet_risk_reason": "Wallet address is missing or invalid"
        }

    if wallet in APPROVED_WALLETS:
        return {
            "wallet_risk": "Low",
            "wallet_risk_reason": "Wallet is whitelisted"
        }

    return {
        "wallet_risk": "Medium",
        "wallet_risk_reason": "Wallet format is valid but not whitelisted"
    }
def screen_wallet(wallet_address):

    if wallet_address in BLOCKED_WALLETS:
        return "BLOCKED"

    return "CLEAR"

def analyze_stablecoin_risk(amount, stablecoin, network):
    risks = []

    if stablecoin.lower() == "usdt":
        risks.append("Higher historical depeg risk compared to USDC")
        risks.append("Regulatory transparency concerns")

    elif stablecoin.lower() == "usdc":
        risks.append("Lower depeg risk, but still subject to banking exposure")

    if network.lower() == "ethereum":
        risks.append("High gas fees may impact transaction cost")

    elif network.lower() == "tron":
        risks.append("Lower fees but higher perceived counterparty risk")

    return {
        "stablecoin": stablecoin,
        "network": network,
        "risk_flags": risks
    }

def validate_payment(parsed):
    issues = []

    # Amount / approval tier check
    if parsed["amount"] is None:
        issues.append("Missing payment amount")
        parsed["approval_level"] = "Cannot determine"
    elif parsed["amount"] <= 10000:
        parsed["approval_level"] = "Auto-approval eligible"
    elif parsed["amount"] <= 50000:
        issues.append("Manager approval required")
        parsed["approval_level"] = "Manager approval"
    else:
        issues.append("Senior approval required")
        parsed["approval_level"] = "Senior approval"

    # Wallet check
    if parsed["wallet_address"] is None:
        issues.append("Invalid or missing wallet address")
    elif parsed["wallet_address"] not in APPROVED_WALLETS:
        issues.append("Wallet not whitelisted")
    wallet_screening = screen_wallet(parsed["wallet_address"])

    if wallet_screening == "BLOCKED":
        issues.append("Wallet failed sanctions screening")
    # Network check
    if parsed.get("network") is None:
        issues.append("Missing or unsupported network")
    # Stablecoin reserve stress check
    if parsed.get("stablecoin") == "USDT":
        issues.append("Higher reserve transparency risk for long-duration holding")

    if parsed.get("reserve_bank_under_stress"):
        issues.append("Stablecoin reserve banking partner under stress")
    # Purpose check
    if parsed["purpose"] is None or len(parsed["purpose"]) < 5:
        issues.append("Unclear payment purpose")

    # Vendor check
    if not parsed.get("vendor_approved"):
        issues.append("Vendor not approved")

    return issues
def assess_liquidity(transaction, treasury_state, liquidity_policy):
    stablecoin = transaction["stablecoin"]
    amount = transaction["amount"]

    balances = treasury_state.get("balances", {})
    pending_outflows = treasury_state.get("pending_outflows", {})
    expected_inflows = treasury_state.get("expected_inflows", {})

    minimum_buffers = liquidity_policy.get("minimum_operating_buffer", {})
    stress_buffer_percent = liquidity_policy.get("stress_buffer_percent", 0)
    large_payment_threshold = liquidity_policy.get("large_payment_threshold", 50000)

    current_balance = balances.get(stablecoin, 0)
    pending_outflow = pending_outflows.get(stablecoin, 0)
    expected_inflow = expected_inflows.get(stablecoin, 0)
    minimum_buffer = minimum_buffers.get(stablecoin, 0)

    stress_buffer = amount * stress_buffer_percent

    projected_liquidity = (
        current_balance
        - pending_outflow
        + expected_inflow
        - amount
    )
    required_liquidity = minimum_buffer + stress_buffer

    liquidity_surplus_or_gap = projected_liquidity - required_liquidity

    issues = []

    if projected_liquidity < required_liquidity:
        issues.append(
            f"Projected {stablecoin} liquidity falls below required buffer."
        )

    if amount >= large_payment_threshold:
        issues.append(
            "Payment exceeds large-payment threshold and requires liquidity desk review."
        )

    if expected_inflow > 0:
        issues.append(
            "Projected liquidity depends on expected inflows; delay risk should be reviewed."
        )

    if liquidity_surplus_or_gap < 0:
        liquidity_status = "FAIL"
        escalation = "Treasury Manager Review"
    elif amount >= large_payment_threshold:
        liquidity_status = "PASS_WITH_REVIEW"
        escalation = "Liquidity Desk Review"
    else:
        liquidity_status = "PASS"
        escalation = "No escalation required"

    return {
        "stablecoin": stablecoin,
        "payment_amount": amount,
        "current_balance": current_balance,
        "pending_outflows": pending_outflow,
        "expected_inflows": expected_inflow,
        "projected_liquidity": projected_liquidity,
        "minimum_buffer": minimum_buffer,
        "stress_buffer": stress_buffer,
        "required_liquidity": required_liquidity,
        "liquidity_surplus_or_gap": liquidity_surplus_or_gap,
        "liquidity_status": liquidity_status,
        "escalation": escalation,
        "issues": issues
    }
def assess_counterparty_exposure(
    stablecoin,
    treasury_balances,
    exposure_policy
):
    total_stablecoin_reserves = (
        treasury_balances.get("USDC", 0)
        + treasury_balances.get("USDT", 0)
    )

    stablecoin_balance = treasury_balances.get(stablecoin, 0)

    if total_stablecoin_reserves == 0:
        exposure_percent = 0
    else:
        exposure_percent = (
            stablecoin_balance / total_stablecoin_reserves
        )

    max_allowed_exposure = exposure_policy.get(
        stablecoin,
        1.0
    )

    exposure_breach = (
        exposure_percent > max_allowed_exposure
    )

    if exposure_breach:
        exposure_status = "BREACH"
        escalation = "Treasury Risk Committee"
    elif exposure_percent > (max_allowed_exposure * 0.8):
        exposure_status = "ELEVATED"
        escalation = "Treasury Manager Review"
    else:
        exposure_status = "NORMAL"
        escalation = "No escalation required"

    return {
        "stablecoin": stablecoin,
        "stablecoin_balance": stablecoin_balance,
        "total_stablecoin_reserves": total_stablecoin_reserves,
        "exposure_percent": round(exposure_percent, 3),
        "max_allowed_exposure": max_allowed_exposure,
        "exposure_breach": exposure_breach,
        "exposure_status": exposure_status,
        "escalation": escalation
    }


def make_decision(issues):
    if not issues:
        return "approve"
    elif "Invalid or missing wallet address" in issues:
        return "reject"
    else:
        return "flag"
def execute_payment(parsed, final_decision):
    if final_decision != "APPROVE":
        return {
            "transaction_status": "NOT_EXECUTED",
            "transaction_hash": None,
            "reason": "Payment requires review or was rejected"
        }

    return {
        "transaction_status": "SUBMITTED",
        "transaction_hash": "0xFAKE_TRANSACTION_HASH_123",
        "reason": "Payment submitted to blockchain network"
    }

def generate_memo(parsed, issues, decision, liquidity_result=None):
    memo = f"""
Treasury Payment Assessment

Amount: {parsed['amount']} {parsed['currency']}
Approval Level: {parsed.get('approval_level')}
Network: {parsed.get('network')}
Wallet: {parsed['wallet_address']}
Wallet Risk: {parsed.get('wallet_risk')}
Wallet Risk Reason: {parsed.get('wallet_risk_reason')}
Purpose: {parsed['purpose']}
Issues Identified:
{', '.join(issues) if issues else 'None'}
Liquidity Assessment:
Status: {liquidity_result["liquidity_status"] if liquidity_result else "Not assessed"}
Projected Liquidity: {liquidity_result["projected_liquidity"] if liquidity_result else "N/A"}
Required Liquidity: {liquidity_result["required_liquidity"] if liquidity_result else "N/A"}
Liquidity Surplus / Gap: {liquidity_result["liquidity_surplus_or_gap"] if liquidity_result else "N/A"}
Escalation: {liquidity_result["escalation"] if liquidity_result else "N/A"}
Final Decision: {decision.upper()}
"""
    return memo


def run_treasury_agent(payment_text, liquidity_result=None):
    parsed = parse_payment_request(payment_text)
    parsed["reserve_bank_under_stress"] = True
    wallet_risk = assess_wallet_risk(parsed)
    parsed.update(wallet_risk)

    payment_issues = validate_payment(parsed)

    stablecoin_issues = analyze_stablecoin_risk(
        amount=parsed["amount"],
        stablecoin=parsed["currency"],
        network=parsed["network"]
    )

    issues = payment_issues + stablecoin_issues["risk_flags"]
    issues = payment_issues + stablecoin_issues["risk_flags"]

    if liquidity_result:
        liquidity_status = liquidity_result["liquidity_status"]

        if liquidity_status == "FAIL":
            issues.append("Liquidity check failed: projected liquidity is below required buffer.")

        elif liquidity_status == "PASS_WITH_REVIEW":
            issues.append("Liquidity desk review required before execution.")

        elif liquidity_status == "PASS":

            pass            
    if issues:
        final_decision = "FLAG"
    else:
        final_decision = "APPROVE"

    decision = make_decision(issues)
    execution_result = execute_payment(parsed, final_decision)    
    memo = generate_memo(parsed, issues, decision, liquidity_result)
    if liquidity_result:
        if liquidity_result["liquidity_status"] == "FAIL":
            issues.append("Liquidity check failed")
            final_decision = "FLAG"
        elif liquidity_result["liquidity_status"] == "PASS_WITH_REVIEW":
            issues.append("Liquidity desk review required")
    return {
        "parsed": parsed,
        "issues": issues,
        "final_decision": final_decision,
        "execution_result": execution_result,

        "memo": memo,
        "stablecoin_analysis": stablecoin_issues
    }

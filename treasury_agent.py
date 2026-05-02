import re

APPROVED_WALLETS = {
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
}


def parse_payment_request(text):
    amount_match = re.search(r'(\d+)\s*(USDC|USDT)', text)
    address_match = re.search(r'0x[a-fA-F0-9]{40}', text)
    purpose_match = re.search(r'Purpose:\s*(.*)', text)
    network_match = re.search(r'on (Ethereum|Solana)', text, re.IGNORECASE)
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

    # Network check
    if parsed.get("network") is None:
        issues.append("Missing or unsupported network")

    # Purpose check
    if parsed["purpose"] is None or len(parsed["purpose"]) < 5:
        issues.append("Unclear payment purpose")

    # Vendor check
    if not parsed.get("vendor_approved"):
        issues.append("Vendor not approved")

    return issues


def make_decision(issues):
    if not issues:
        return "approve"
    elif "Invalid or missing wallet address" in issues:
        return "reject"
    else:
        return "flag"


def generate_memo(parsed, issues, decision):
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

Final Decision: {decision.upper()}
"""
    return memo


def run_treasury_agent(text):
    parsed = parse_payment_request(text)

    wallet_risk = assess_wallet_risk(parsed)
    parsed.update(wallet_risk)

    issues = validate_payment(parsed)
    decision = make_decision(issues)
    memo = generate_memo(parsed, issues, decision)

    return {
        "parsed": parsed,
        "issues": issues,
        "decision": decision,
        "memo": memo
    }

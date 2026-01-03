import requests
import os
from app.core.config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET

PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" # Change to api-m.paypal.com for production

def get_access_token():
    try:
        if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
            return None
        
        response = requests.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            data={"grant_type": "client_credentials"}
        )
        return response.json().get("access_token")
    except Exception as e:
        print(f"PayPal Auth Error: {e}")
        return None

def create_paypal_order(user_id: int):
    token = get_access_token()
    if not token:
        # Fallback to a fake link if credentials are missing
        return "https://www.paypal.com/checkoutnow?token=mock_token_for_user_" + str(user_id)

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": "5.00"
                },
                "description": f"Premium Subscription for user {user_id}"
            }],
            "application_context": {
                "return_url": "https://yourapp.com/api/payments/paypal/success",
                "cancel_url": "https://yourapp.com/api/payments/paypal/cancel"
            }
        }
        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers=headers,
            json=order_data
        )
        data = response.json()
        for link in data.get("links", []):
            if link["rel"] == "approve":
                return link["href"]
        return "https://www.paypal.com"
    except Exception as e:
        print(f"PayPal Order Error: {e}")
        return "https://www.paypal.com"

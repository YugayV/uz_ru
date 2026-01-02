import stripe
from datetime import date, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout(user_id: int):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Premium Subscription"},
                    "recurring": {"interval": "month"},
                    "unit_amount": 500,
                },
                "quantity": 1,
            }],
            success_url="https://yourapp.com/success",
            cancel_url="https://yourapp.com/cancel",
            metadata={"user_id": user_id}
        )
        return session.url
    except Exception as e:
        print(f"⚠️ Stripe Error: {e}")
        return "https://checkout.stripe.com/pay/cs_test_fake123"

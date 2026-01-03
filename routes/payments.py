from fastapi import APIRouter
from services.stripe_service import create_checkout
from services.paypal_service import create_paypal_order
import stripe
import os

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/stripe/checkout/{user_id}")
def stripe_checkout(user_id: int):
    url = create_checkout(user_id)
    return {"checkout_url": url}

@router.post("/paypal/checkout/{user_id}")
def paypal_checkout(user_id: int):
    url = create_paypal_order(user_id)
    return {"checkout_url": url}

@router.post("/checkout")
def create_checkout(plan: str, chat_id: int):
    price_id = {
        "pro": os.getenv("PRICE_ID_PRO"),
        "family": os.getenv("PRICE_ID_FAMILY")
    }[plan]

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="https://yourapp/success",
        cancel_url="https://yourapp/cancel",
        metadata={"chat_id": chat_id, "plan": plan}
    )
    return {"url": session.url}
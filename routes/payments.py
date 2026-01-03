from fastapi import APIRouter
from app.services.stripe_service import create_checkout
from services.paypal_service import create_paypal_order

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/stripe/checkout/{user_id}")
def stripe_checkout(user_id: int):
    url = create_checkout(user_id)
    return {"checkout_url": url}

@router.post("/paypal/checkout/{user_id}")
def paypal_checkout(user_id: int):
    url = create_paypal_order(user_id)
    return {"checkout_url": url}

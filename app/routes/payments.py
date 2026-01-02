from fastapi import APIRouter
from app.services.stripe_service import create_checkout

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/stripe/checkout/{user_id}")
def stripe_checkout(user_id: int):
    url = create_checkout(user_id)
    return {"checkout_url": url}

import stripe
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.models.user import User
from app.services.premium import activate_premium
from fastapi import APIRouter, Depends, HTTPException 


router = APIRouter()

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    event = stripe.Webhook.construct_event(
        payload,
        sig_header,
        "STRIPE_WEBHOOK_SECRET"
    )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]

        user = db.query(User).get(user_id)
        activate_premium(user)
        db.commit()

    return {"status": "ok"}

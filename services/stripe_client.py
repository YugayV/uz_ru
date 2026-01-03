import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

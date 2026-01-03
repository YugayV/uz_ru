import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv("ini") # Load the new ini file as well

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

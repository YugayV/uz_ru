from datetime import date, timedelta 

PREMIUM_DAYS = 30 

def activate_premium(user): 
    today = date.today()
    user.is_premium = True 
    user.premium_until = today + timedelta(days=PREMIUM_DAYS)

def check_premium(user): 
    if not user.is_premium: 
        return False

    if user.premium_until and user.premium_until < date.today(): 
        user.is_premium = False 
        user.premium_until = None 
        return False 

    return True

# Mock storage for premium users
_premium_users = set()

def is_premium(user_id: int) -> bool:
    """Check if user_id is in premium set."""
    return user_id in _premium_users

def enable_premium(user_id: int):
    """Add user_id to premium set."""
    _premium_users.add(user_id)

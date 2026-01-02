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

    if not user.is_premium:
        show_ad = True

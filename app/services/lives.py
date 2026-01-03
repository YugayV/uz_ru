from datetime import datetime

MAX_LIVES = 6 
RESTORE_MINUTES = 30 # 1live 30minutes 

def restore_lives_if_needed(user): 
    if user.is_premium: 
        user.lives = MAX_LIVES 
        return 

    now = datetime.utcnow()
    if user.last_life_restore is None:
        user.last_life_restore = now

    diff = now - user.last_life_restore 
    restored = diff.seconds // (RESTORE_MINUTES * 60)

    if restored > 0: 
        user.lives = min(MAX_LIVES, user.lives + restored)
        user.last_life_restore = now 

def lose_life(user): 
    if user.is_premium: 
        return 

    if user.lives > 0: 
        user.lives -= 1

        
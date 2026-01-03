SUBSCRIPTIONS = {}

def get_plan(chat_id):
    return SUBSCRIPTIONS.get(chat_id, "free")

def set_plan(chat_id, plan):
    SUBSCRIPTIONS[chat_id] = plan

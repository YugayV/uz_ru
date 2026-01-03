REPORTS = {}

def log(chat_id, text):
    REPORTS.setdefault(chat_id, []).append(text)

def get_report(chat_id):
    return REPORTS.get(chat_id, [])

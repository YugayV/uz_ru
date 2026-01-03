FORBIDDEN = [
    "убей", "кровь", "секс", "оружие",
    "плохой", "дурак"
]

def is_safe(text: str) -> bool:
    text = text.lower()
    return not any(word in text for word in FORBIDDEN)

def limit_length(text: str, max_words=10):
    words = text.split()
    return " ".join(words[:max_words])

import random

def math_game():
    return {
        "question": "🦫 What is 2 + 2?",
        "answer": "4"
    }

def kids_riddle_game():
    riddles = [
        {"question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?", "answer": "A map"},
        {"question": "What has to be broken before you can use it?", "answer": "An egg"},
        {"question": "What is full of holes but still holds water?", "answer": "A sponge"},
    ]
    return random.choice(riddles)

def adult_logic_game():
    questions = [
        {"question": "A man is looking at a portrait. Someone asks him whose portrait he is looking at. He replies, 'Brothers and sisters I have none, but that man's father is my father's son.' Who is in the portrait?", "answer": "His son"},
        {"question": "What is special about these words: 'Job', 'Polish', 'Herb'?", "answer": "They are capitalized"},
        {"question": "What comes once in a minute, twice in a moment, but never in a thousand years?", "answer": "The letter M"},
    ]
    return random.choice(questions)

def guess_word_game():
    words = [
        {"question": "What animal is this: `E _ e _ _ a _ t`?", "answer": "Elephant"},
        {"question": "What fruit is this: `_ p p _ e`?", "answer": "Apple"},
        {"question": "What color is this: `_ l u _`?", "answer": "Blue"},
    ]
    return random.choice(words)

def associations_game():
    options = [
        {"question": "Which word doesn't belong? `Apple`, `Banana`, `Carrot`, `Orange`", "answer": "Carrot"},
        {"question": "Which word doesn't belong? `Run`, `Swim`, `Fly`, `Sleep`", "answer": "Sleep"},
        {"question": "Which word doesn't belong? `Dog`, `Cat`, `Table`, `Hamster`", "answer": "Table"},
    ]
    return random.choice(options)

def get_random_game(is_kid=True):
    if is_kid:
        return random.choice([math_game, kids_riddle_game, guess_word_game])()
    else:
        return random.choice([adult_logic_game, associations_game])()

"""Generate starter game JSON files and placeholder SVG assets.

Run this script locally to populate content/games with starter data.
"""
import json
from pathlib import Path
import random

OUT = Path(__file__).parent
ASSETS = OUT / "assets"
ASSETS.mkdir(exist_ok=True)

WORDS = ["яблоко", "собака", "кот", "мяч", "дом", "солнце", "дерево", "машина", "книга", "утка"]

SVG_TEMPLATE = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><rect width="100%" height="100%" fill="#f0f0f0"/><text x="50%" y="50%" font-size="24" text-anchor="middle" dominant-baseline="middle">{text}</text></svg>'


def create_placeholder_svg(name: str):
    svg_path = ASSETS / f"{name}.svg"
    svg_path.write_text(SVG_TEMPLATE.format(text=name))
    return str(svg_path.relative_to(OUT.parent))


def generate(count: int = 50):
    for i in range(count):
        t = random.choice(["guess_word", "associations", "memory", "quiz"])
        if t == "guess_word":
            w = random.choice(WORDS)
            q = f"Угадай слово: _ {' '.join(['_' for _ in w])}"
            answer = w
            options = None
        elif t == "associations":
            q = "Что не подходит: Яблоко, Банан, Морковь, Апельсин"
            answer = "Морковь"
            options = ["Яблоко", "Банан", "Морковь", "Апельсин"]
        elif t == "memory":
            q = "Найди пару для слова"
            answer = None
            options = None
        else:
            q = "Сколько будет 2+2?"
            answer = "4"
            options = ["3", "4", "5"]

        gid = f"game_{i:03d}"
        img = create_placeholder_svg(gid)
        data = {"id": gid, "type": t, "question": q, "options": options, "answer": answer, "image": img}
        (OUT / f"{gid}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Generated {count} games in {OUT}")


if __name__ == "__main__":
    generate(50)

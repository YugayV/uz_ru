This folder contains JSON manifests for child-friendly games used by the Telegram bot.

- To generate starter games, run: `python content/games/generate_games.py` from the repo root.
- Files are stored as `game_*.json` and optional SVG assets are in `content/games/assets/`.
- Each JSON contains: `id`, `type`, `question`, `options` (nullable), `answer`, `image` (optional).

Example:
{
  "id": "game_001",
  "type": "quiz",
  "question": "Что растёт на дереве?",
  "options": ["машина", "яблоко", "стол"],
  "answer": "яблоко",
  "image": "games/assets/game_001.svg"
}

Tests:
- `tests/test_games_loader.py` expects at least one game JSON file in this directory.

If you want 50 starter games, run the generator script locally or in CI; the repo currently includes a small set of example game manifests.
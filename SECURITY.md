# Security & Key Rotation

This document explains how to handle exposed keys and how to rotate/revoke them safely.

## Immediate steps if a secret was exposed
1. Revoke the compromised key immediately from the provider dashboard (OpenAI, Telegram, Stripe, DeepSeek).
2. Generate a new key and update your deployment secrets (do NOT put the key in the repo).
3. If key was ever committed:
   - Remove it from the working tree: `git rm --cached path/to/file` and replace with a placeholder.
   - Purge it from history using `git filter-repo` or the BFG repo-cleaner (see below).

## Removing secrets from Git history (recommended steps)
- Using BFG (easier):
  1. Install BFG: https://rtyley.github.io/bfg-repo-cleaner/
  2. Run: `bfg --replace-text passwords.txt` (prepare `passwords.txt` with patterns)
  3. Run `git reflog expire --expire=now --all && git gc --prune=now --aggressive`
  4. Force-push to remote: `git push --force`

- Using git filter-repo (more flexible):
  1. `pip install git-filter-repo`
  2. `git filter-repo --replace-text replacements.txt`

**Important:** After history rewrite, rotate (revoke/generate) keys and update hosting secrets.

## How to store secrets safely
- Use your hosting provider secret store (GitHub Actions secrets / Render / Heroku config vars / Azure Key Vault).
- Keep `.env.example` in the repo (placeholders only).
- Add `services/.env` and `.env` to `.gitignore` (already done).

## How to add secrets to GitHub Actions
- Go to your repo > Settings > Secrets and variables > Actions > New repository secret.
- Add keys: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `DEEPSEEK_API_KEY`, `STRIPE_SECRET_KEY`.

## Contact
If you'd like, I can help rotate keys and scrub repo history safely.

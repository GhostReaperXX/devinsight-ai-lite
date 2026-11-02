# DevInsight AI Lite

An intelligent software issue tracker, built step by step during the field training.

This version connects the model to the application and secures it: accounts, access rules,
category suggestions, related issues and duplicate detection.

## Getting started

```bash
git clone https://github.com/YOUR-USERNAME/devinsight-ai-lite.git
cd devinsight-ai-lite
python -m venv .venv
source .venv/Scripts/activate    # Git Bash on Windows
pip install -r requirements.txt
```

## Configure

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"    # paste the result as SECRET_KEY
```

## Run it

```bash
python -m scripts.seed_demo --reset
uvicorn app.main:app --reload
```

Log in as `admin@devinsight.example` or `lina@devinsight.example` with the password `Training#2026`.
These accounts are for demonstration only.

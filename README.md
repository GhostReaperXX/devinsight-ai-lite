# DevInsight AI Lite

An intelligent software issue tracker, built step by step during the field training.

This version adds automated tests, continuous integration, logging, a health check, and
everything needed to run on Render with a PostgreSQL database on Neon.

## Getting started

```bash
git clone https://github.com/YOUR-USERNAME/devinsight-ai-lite.git
cd devinsight-ai-lite
python -m venv .venv
source .venv/Scripts/activate    # Git Bash on Windows
pip install -r requirements-dev.txt
```

## Configure and run

```bash
cp .env.example .env
python -m scripts.seed_demo --reset
uvicorn app.main:app --reload
```

## Quality checks

```bash
pytest --cov --cov-report=term-missing
ruff check .
```

The same checks run on GitHub for every push and pull request. See `.github/workflows/ci.yml`.

## Deployment settings on Render

| Setting | Value |
|---|---|
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --forwarded-allow-ips="*"` |
| Health check path | `/health` |
| Environment variables | `ENVIRONMENT=production`, `DATABASE_URL`, `SECRET_KEY`, `SEED_PASSWORD` |

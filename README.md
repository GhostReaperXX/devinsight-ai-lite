# DevInsight AI Lite

An intelligent software issue tracker, built step by step during the field training.

This version adds the backend: a FastAPI service with a relational database. The command line
utility from Week 1 is still in `issue_tool/`.

## Getting started

```bash
git clone https://github.com/YOUR-USERNAME/devinsight-ai-lite.git
cd devinsight-ai-lite
python -m venv .venv
source .venv/Scripts/activate    # Git Bash on Windows
pip install -r requirements.txt
```

## Run it

```bash
python -m scripts.seed_demo --reset     # create tables and demonstration data
uvicorn app.main:app --reload           # start the server
```

Open <http://127.0.0.1:8000/docs> to try every endpoint in the browser.

## Layout

| Path | Purpose |
|---|---|
| `app/main.py` | Creates the application and connects its parts |
| `app/database.py` | Engine, sessions and the `get_db` dependency |
| `app/models.py` | Tables, as SQLAlchemy classes |
| `app/schemas.py` | The shape of the data entering and leaving the API |
| `app/errors.py` | Business errors, independent of HTTP |
| `app/services/` | Business rules |
| `app/routers/` | HTTP endpoints |
| `scripts/seed_demo.py` | Demonstration data |

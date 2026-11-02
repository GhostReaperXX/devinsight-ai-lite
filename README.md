# DevInsight AI Lite

An intelligent software issue tracker, built step by step during the field training.

This version adds the web interface: server-rendered pages with Jinja2 and Bootstrap, and small
JavaScript files that talk to the REST API.

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
python -m scripts.seed_demo --reset
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> for the application and <http://127.0.0.1:8000/docs> for the API.

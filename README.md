# DevInsight AI Lite

An intelligent software issue tracker. Teams report, track and analyse software issues in one
place. A lightweight machine learning component suggests a category for each report and points
out reports that may be duplicates. People always make the final decision.

**Live demonstration:** <https://devinsight-ai-lite.onrender.com>
(on the free plan the first request after a quiet period can take about a minute)

## Features

- Issue creation, editing, status tracking, filtering, search and paging
- Projects, comments and a dashboard that updates without reloading the page
- Accounts with hashed passwords, a signed login token and access rules
- A category suggestion with a confidence value while you type (macro F1 0.907 on unseen reports)
- Related issues and a review page for likely duplicates, using TF-IDF and cosine similarity
- A documented REST API at `/docs`
- 105 automated tests with 91 percent coverage, and a GitHub Actions workflow to run them

## Technology

| Area | Tools |
|---|---|
| Language | Python 3.14 |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite for development, PostgreSQL (Neon) online |
| Interface | Jinja2, Bootstrap 5, plain JavaScript |
| Machine learning | scikit-learn, TF-IDF, logistic regression, cosine similarity |
| Quality | pytest, Ruff, GitHub Actions |
| Hosting | Render |

## Run it on your computer

You need Python 3.14 or newer and Git.

```bash
git clone https://github.com/GhostReaperXX/devinsight-ai-lite.git
cd devinsight-ai-lite
python -m venv .venv
source .venv/Scripts/activate       # Git Bash on Windows
# source .venv/bin/activate         # macOS and Linux
pip install -r requirements-dev.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"   # paste the result as SECRET_KEY in .env
python -m scripts.seed_demo --reset
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000> and log in as `admin@devinsight.example` with the password
`Training#2026`. These demonstration accounts exist only on your computer unless you create them
elsewhere. On the live demonstration, register an account of your own.

## Configuration

Settings are read from environment variables, or from a local `.env` file that is never committed.

| Variable | Purpose | Default |
|---|---|---|
| `ENVIRONMENT` | `development`, `test` or `production` | `development` |
| `DATABASE_URL` | SQLite path or PostgreSQL URL | `sqlite:///./devinsight.db` |
| `SECRET_KEY` | Signs login tokens. Required in production, at least 32 characters | development value |
| `ACCESS_TOKEN_MINUTES` | How long a login stays valid | `120` |
| `SEED_PASSWORD` | Password for demonstration accounts. Required in production | `Training#2026` |
| `LOG_LEVEL` | Logging detail | `INFO` |

## Common tasks

```bash
pytest --cov --cov-report=term-missing     # run the tests
ruff check .                               # check code style and common mistakes
python -m ml.train                         # retrain and re-evaluate the model
python -m ml.evaluate_similarity           # choose the duplicate threshold from labeled pairs
```

## Project structure

| Path | Purpose |
|---|---|
| `app/main.py` | Creates the application and connects its parts |
| `app/config.py` | Settings from the environment |
| `app/database.py` | Engine and sessions |
| `app/models.py` | Tables |
| `app/schemas.py` | Validation of data entering and leaving the API |
| `app/security.py` | Password hashing and login tokens |
| `app/deps.py` | Shared dependencies: database session, current user, model |
| `app/services/` | Business rules |
| `app/routers/` | HTTP endpoints and pages |
| `app/ml/` | Using the trained model at run time |
| `app/templates/`, `app/static/` | The web interface |
| `ml/` | Training and evaluating models, offline |
| `data/` | Prepared datasets |
| `tests/` | Automated tests |
| `docs/` | SRS, architecture, schema, API, model evaluation, test report, defect log, deployment |
| `issue_tool/` | The command line utility from Chapter 1 |

## Documentation

- [Software requirements specification](docs/SRS.md)
- [Product backlog](docs/backlog.md)
- [Architecture](docs/architecture.md)
- [Database schema](docs/erd.md)
- [API reference](docs/api.md)
- [Model evaluation](docs/model_evaluation.md)
- [Test report](docs/test_report.md)
- [Defect log](docs/defect_log.md)
- [Deployment guide](docs/deployment.md)

## Known limits

Free hosting sleeps when idle. Login attempts are not rate limited yet. A logged-out token stays valid
until it expires, because tokens are not stored on the server. Duplicate detection compares words,
not meaning.

## Team

| Member | Main responsibilities | GitHub |
|---|---|---|
| Abdelrahman Alfaqih | Reference implementation | @GhostReaperXX |

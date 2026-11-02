# Deployment guide

The application runs as one web service on Render, with its database on Neon.

## 1. Database on Neon

1. Create a project, and copy the connection string from the project dashboard.
2. Keep it private. It contains a password.

## 2. Fill the hosted database

Run once from your computer, in Git Bash, with your own values:

```bash
export ENVIRONMENT=production
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export SEED_PASSWORD="choose-a-private-demo-password"
export DATABASE_URL="postgresql://your_user:your_password@ep-example-123456.eu-central-1.aws.neon.tech/neondb?sslmode=require"
python -m scripts.seed_demo --reset
```

Close the terminal afterwards, so these values do not remain in its environment.

## 3. Web service on Render

Create a new Web Service from the GitHub repository, with these settings:

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --forwarded-allow-ips="*"` |
| Instance type | Free |
| Health check path | `/health` |

Environment variables:

| Name | Value |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | The Neon connection string |
| `SECRET_KEY` | A new random value, at least 32 characters |
| `SEED_PASSWORD` | The private demo password |

`--forwarded-allow-ips="*"` tells Uvicorn to trust the proxy's `X-Forwarded-Proto` header. Without it
the application thinks it is on plain HTTP, and it builds `http://` links to its own static files,
which browsers then block on an HTTPS page.

## 4. Verify after every deployment

| Check | How | Expected |
|---|---|---|
| Health | Open `/health` | `status` is `ok`, `database` is `ok`, `model` is `loaded` |
| Pages load with styles | Open `/login` | The page is styled, and the browser console shows no blocked content |
| Login | Log in with a demo account | The dashboard appears with numbers |
| Write | Create an issue | It appears in the list, and survives a redeploy |
| AI | Type a report in the form | A suggestion and related issues appear |
| Access | Log in as a member and try to delete | Refused |
| Secure cookie | In DevTools, open Application, then Cookies | `HttpOnly`, `Secure` and `SameSite=Lax` are set |

## 5. If something goes wrong

| Symptom | Likely cause | What to do |
|---|---|---|
| Build fails on a package | Wrong Python version | Check `.python-version` and the build log |
| Service starts, then exits | A missing or weak `SECRET_KEY` | Read the log, set the variable |
| `/health` returns 503 | Wrong `DATABASE_URL`, or the database is suspended | Check the value, then try again after a few seconds |
| Pages have no styles | Mixed content | Check the start command includes `--forwarded-allow-ips` |
| First request takes about a minute | The free plan sleeps when idle | Expected behaviour |

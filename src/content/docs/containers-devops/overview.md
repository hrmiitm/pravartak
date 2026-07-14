---
title: Containers & DevOps
description: Small, repeatable patterns for scheduled jobs, feedback loops, CI/CD, and demos.
sidebar:
  order: 1
---

# Small automation and delivery loops

The goal is a short, safe loop: **schedule or change → verify → observe → improve**. Keep every step easy to run again.

## Crontab: schedule a small job

Cron runs a command on a schedule. Edit the current user's jobs with `crontab -e`:

```text
# minute hour day-of-month month day-of-week
0 9 * * 1-5 /home/user/app/scripts/report.sh >> /home/user/app/logs/report.log 2>&1
```

- Use absolute paths and send output to a log.
- Test the command in a shell first; cron has a minimal environment.
- Make jobs idempotent: a retry should not create duplicate work.
- Do not put secrets in the crontab. Read them from a protected environment or secret store.

## Loop engineering: improve with evidence

An engineering loop is deliberately small:

1. Define one measurable outcome (for example, “the API stays below 300 ms”).
2. Make the smallest change.
3. Run a repeatable check.
4. Inspect logs, tests, or user feedback.
5. Keep, adjust, or revert — then repeat.

> Automation makes a bad loop faster. Put a check and a clear owner around every scheduled or deployed task.

## CI/CD with GitHub Actions

CI validates each pull request; CD releases a verified revision. This repository’s Pages workflow already runs lint, tests, and a production build. A minimal Python API workflow can look like this:

```yaml
name: API checks
on: [pull_request, push]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: examples/huggingface-fastapi
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: examples/huggingface-fastapi/requirements.txt
      - run: pip install -r requirements.txt
      - run: python -c "from app import app; assert app.title == 'Hello FastAPI'"
```

Protect the main branch so the checks must pass before merge. Deploy only from that protected branch, and keep deployment tokens in GitHub Secrets.

## Hugging Face Space: small FastAPI demo

Hugging Face Spaces can build a Docker app. Copy the repository's `examples/huggingface-fastapi/` directory into a new **Docker** Space repository, then push it. The `README.md` declares `sdk: docker` and port `7860`; the container starts FastAPI with Uvicorn.

```bash
cd examples/huggingface-fastapi
uvicorn app:app --reload --port 7860
```

Open `http://127.0.0.1:7860/docs` locally, then use `GET /api/greet?name=Pravartak` to verify the deployment. Store credentials in the Space’s Secrets settings, never in `app.py`.

[Open the companion slides](../../slides/automation-delivery/)

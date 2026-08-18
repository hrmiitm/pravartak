---
title: Hello FastAPI
emoji: "🚀"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# Hello FastAPI

A tiny FastAPI Docker Space.

- `GET /health` returns the service status.
- `GET /api/greet?name=Pravartak` returns a greeting.
- `/docs` provides the generated API documentation.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

---
marp: true
title: Hugging Face Spaces
description: Publish a small FastAPI Docker demo
theme: default
size: 16:9
paginate: true
---

# Hugging Face Spaces

Publish a small FastAPI demo with Docker.

---

## FastAPI endpoint

```python
@app.get("/api/greet")
def greet(name: str = "world"):
    return {"message": f"Hello, {name}!"}
```

---

## Deploy in five steps

1. Create a **Docker** Space.
2. Add `app.py`, `requirements.txt`, and `Dockerfile`.
3. Set `app_port: 7860` in `README.md`.
4. Push the repository.
5. Open `/docs` and test the API.

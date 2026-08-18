---
marp: true
title: Hugging Face Spaces
description: Publish a small FastAPI Docker demo
theme: default
size: 16:9
paginate: true
---

# Hugging Face Spaces

Publish a small FastAPI Docker demo.

---

## Choose Docker for FastAPI

| Space type | Best use |
| --- | --- |
| Gradio | Quick Python UI |
| Static | Frontend-only site |
| Docker | FastAPI and custom servers |

FastAPI needs a Docker Space.

---

## Four project files

```text
README.md         Space settings
Dockerfile        container instructions
requirements.txt  Python packages
app.py            API endpoints
```

---

## FastAPI endpoint

```python
@app.get("/api/greet")
def greet(name: str = "world"):
    return {"message": f"Hello, {name}!"}
```

Also add `/health`; FastAPI gives you `/docs`.

---

## Configure the Space

```yaml
---
sdk: docker
app_port: 7860
---
```

The Docker server must also listen on port `7860`.

---

## Build and run

```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

```bash
uvicorn app:app --reload --port 7860
curl http://127.0.0.1:7860/health
```

Test locally before you push.

---

## Deploy and troubleshoot

1. Create a **Docker** Space.
2. Add `app.py`, `requirements.txt`, and `Dockerfile`.
3. Set `app_port: 7860` in `README.md`.
4. Push the repository.
5. Open `/docs` and test the API.

Secrets belong in Space settings, never in Git.

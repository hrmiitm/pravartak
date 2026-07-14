---
title: Hugging Face Spaces with FastAPI
description: Deploy a tiny Docker-based FastAPI demo.
sidebar:
  order: 5
---

# Hugging Face Spaces with FastAPI

Hugging Face Spaces are Git repositories that host small demos. FastAPI works in a **Docker Space**.

## Files you need

Use the small example in `examples/huggingface-fastapi/`. Its API is only two endpoints:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/greet")
def greet(name: str = "world"):
    return {"message": f"Hello, {name}!"}
```

The Space `README.md` needs this header:

```yaml
---
sdk: docker
app_port: 7860
---
```

## Deploy in five steps

1. Create a new Space and choose **Docker** as its SDK.
2. Copy the example files into the Space repository.
3. Commit and push the files.
4. Wait for the build to finish.
5. Open `/docs` for the API page, then test `/api/greet?name=Pravartak`.

## Run before deploying

```bash
cd examples/huggingface-fastapi
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

Open `http://127.0.0.1:7860/docs`. Add API keys only through the Space **Secrets** settings.

[Read Hugging Face's official Docker Spaces guide](https://huggingface.co/docs/hub/en/spaces-sdks-docker)

[Open the Hugging Face Spaces slides](../../slides/huggingface-spaces/)

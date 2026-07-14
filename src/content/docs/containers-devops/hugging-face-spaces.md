---
title: Hugging Face Spaces with FastAPI
description: Deploy a tiny Docker-based FastAPI demo.
sidebar:
  order: 5
---

# Hugging Face Spaces with FastAPI

Hugging Face Spaces are Git repositories that host small demos. A Space rebuilds when you push a commit. FastAPI works in a **Docker Space**, where you provide the application and its Dockerfile.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>7 slides · drawing tools · PDF</small></p>
  <a href="../../slides/huggingface-spaces/">Open slide deck →</a>
</div>

## 1. Choose the right Space type

| Type | Best for | Do you write a Dockerfile? |
| --- | --- | --- |
| Gradio | Quick Python user interfaces | No |
| Static | HTML, CSS, and JavaScript sites | No |
| Docker | FastAPI, custom servers, or system packages | Yes |

Choose **Docker** for FastAPI because FastAPI is an HTTP server, not a Gradio interface.

## 2. Understand the project files

Use the small example in `examples/huggingface-fastapi/` as a starting point.

```text
huggingface-fastapi/
├── README.md          # Space settings and instructions
├── Dockerfile         # how to build and start the container
├── requirements.txt   # Python packages
└── app.py             # FastAPI endpoints
```

`app.py` defines the web API:

```python
from fastapi import FastAPI

app = FastAPI(title="Hello FastAPI")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/greet")
def greet(name: str = "world"):
    return {"message": f"Hello, {name}!"}
```

- `/health` is a simple endpoint for checking that the server started.
- `/api/greet?name=Asha` reads a query value and returns JSON.
- FastAPI automatically creates interactive documentation at `/docs`.

## 3. Configure the Space

At the top of the Space `README.md`, add a YAML configuration block:

```yaml
---
title: Hello FastAPI
emoji: "🚀"
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---
```

`sdk: docker` tells Spaces to build your Dockerfile. `app_port: 7860` must match the port that your application listens on.

## 4. Build the container

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
```

| Docker instruction | What it does |
| --- | --- |
| `FROM` | Selects the starting Python image |
| `WORKDIR` | Sets `/app` as the folder for later commands |
| `COPY` | Copies a project file into the image |
| `RUN` | Runs a command while building the image |
| `CMD` | Starts the server when the container runs |

`--host 0.0.0.0` lets the Space reach Uvicorn inside the container. Do not use `--reload` in the deployed command; it is for local development.

## 5. Run locally first

Run Python directly for the quickest feedback:

```bash
cd examples/huggingface-fastapi
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

Then test three URLs:

```bash
curl http://127.0.0.1:7860/health
curl "http://127.0.0.1:7860/api/greet?name=Pravartak"
```

Open `http://127.0.0.1:7860/docs` in a browser to try the generated documentation.

To test the container itself:

```bash
docker build -t hello-fastapi .
docker run --rm -p 7860:7860 hello-fastapi
```

## 6. Deploy in five steps

1. Create a new Space and choose **Docker** as its SDK.
2. Copy the example files into the Space repository.
3. Commit and push the files.
4. Wait for the build to finish.
5. Open `/docs` for the API page, then test `/api/greet?name=Pravartak`.

The Space build log is the first place to look when a deployment fails. Read the first error: it commonly points to a missing file, package, or incorrect port.

## 7. Use variables and secrets correctly

Use a normal Space variable for a non-sensitive setting and a Space secret for a token. Read either value from the environment:

```python
import os

model_name = os.getenv("MODEL_NAME", "small-demo-model")
api_token = os.getenv("API_TOKEN")
```

- Add `MODEL_NAME` in the Space **Variables** settings.
- Add `API_TOKEN` in the Space **Secrets** settings.
- Never commit `.env` files, tokens, or private URLs.

## 8. Common problems

| Problem | First check |
| --- | --- |
| Space never starts | `sdk: docker` and `app_port: 7860` in README |
| Build cannot find a file | File names and Dockerfile `COPY` commands |
| Site opens but API fails | `/docs`, `/health`, and the Space runtime logs |
| Port error | Uvicorn port and `app_port` are both `7860` |
| Secret is `None` | Add it in Space settings, then restart/rebuild |

## Practice

Add a `GET /api/version` endpoint that returns `{"version": "1.0"}`. Test it locally, test it in Docker, then push it to a Docker Space.

[Read Hugging Face's official Docker Spaces guide](https://huggingface.co/docs/hub/en/spaces-sdks-docker)

[Read the Space configuration reference](https://huggingface.co/docs/hub/spaces-config-reference)

[Open the Hugging Face Spaces slides](../../slides/huggingface-spaces/)

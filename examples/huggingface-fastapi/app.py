from fastapi import FastAPI

app = FastAPI(title="Hello FastAPI", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/greet")
def greet(name: str = "world") -> dict[str, str]:
    cleaned_name = name.strip() or "world"
    return {"message": f"Hello, {cleaned_name}!"}

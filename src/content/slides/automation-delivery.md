---
marp: true
title: Small Automation & Delivery Loops
description: Cron, iterative engineering, GitHub Actions, and a FastAPI Space
theme: default
size: 16:9
paginate: true
---

<!-- _class: lead -->
<!-- _paginate: false -->

# Small automation & delivery loops

Schedule · verify · observe · improve

---

## Crontab: predictable scheduled work

```cron
0 9 * * 1-5 /app/report.sh >> /app/report.log 2>&1
```

- Absolute paths
- Log output
- Test before scheduling
- Safe to retry

<!-- notes
Cron is useful for small, well-understood recurring work. Emphasize that retry-safe jobs and logs are more important than clever schedules.
-->

---

## Loop engineering

```text
Measure → small change → automated check → observe → decide → repeat
```

One loop, one outcome:

> “Can the API respond in under 300 ms?”

<!-- notes
The loop should create evidence, not simply activity. Keep changes small enough to revert.
-->

---

## CI/CD with GitHub Actions

```text
Pull request → lint + test + build → review → protected main → deploy
```

- CI proves a revision is ready to review
- CD releases an already-verified revision
- Secrets stay in repository or platform settings

---

## FastAPI on Hugging Face Spaces

```text
Git push → Docker Space build → Uvicorn :7860 → /docs + /api/greet
```

```python
@app.get("/api/greet")
def greet(name: str = "world"):
    return {"message": f"Hello, {name}!"}
```

Small demos deserve the same loop: test, deploy, check, observe.

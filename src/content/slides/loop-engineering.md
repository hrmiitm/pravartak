---
marp: true
title: Loop Engineering
description: Small changes and fast feedback
theme: default
size: 16:9
paginate: true
---

# Loop engineering

Make progress with small changes and real evidence.

---

## Start with one outcome

```text
Too vague: “Make the API better”
Useful: “/health returns HTTP 200”
```

An outcome needs a signal: a test, a request, a log, or a timing measurement.

---

## The engineering loop

```text
Understand → plan → small change → check → observe → decide → repeat
```

Choose the expected result before changing code.

---

## Make one repeatable check

```bash
curl "http://127.0.0.1:7860/api/greet?name=Asha"
```

- Did it return the expected greeting?
- If not, change one thing and run the same check again.

---

## Use the right feedback level

| Level | Example |
| --- | --- |
| Code | lint, formatter, unit test |
| App | curl, API test, browser check |
| Build | `npm run build`, Docker build |
| Production | logs, latency, user reports |

Start with the fastest check that can prove the change.

---

## Record the result

```text
Goal: /health returns 200.
Change: added health endpoint.
Check: curl /health.
Result: passed locally; ready for CI.
```

Small records make review, debugging, and handoffs easier.

---
title: Loop engineering
description: Improve software through small changes and fast feedback.
sidebar:
  order: 3
---

# Loop engineering

Loop engineering means working in a short cycle: **understand → change → check → observe → learn → repeat**. It turns vague work such as “make it better” into small decisions supported by evidence.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>6 slides · drawing tools · PDF</small></p>
  <a href="../../slides/loop-engineering/">Open slide deck →</a>
</div>

## 1. Start with one outcome

Do not start by changing five things. Start with one statement you can check:

| Too vague | Better outcome |
| --- | --- |
| “Make the API better” | “`/health` returns HTTP 200” |
| “Make it faster” | “The greeting endpoint responds in under 300 ms locally” |
| “Fix deployment” | “The Docker image builds and `/docs` opens” |

An outcome needs a **signal**. A signal can be a test result, an HTTP status, a log line, a time measurement, or user feedback.

## 2. Run the engineering loop

1. **Understand** — read the requirement, current code, and last error.
2. **Plan** — choose the smallest useful change and the check that proves it.
3. **Change** — modify one function, configuration value, or file.
4. **Check** — run a test, build, lint command, or manual request.
5. **Observe** — inspect output, logs, timing, and unexpected effects.
6. **Decide** — keep, improve, or revert the change; then begin the next loop.

```text
Expected result → small change → repeatable check → evidence → next decision
```

## 3. Use a repeatable check

For a small FastAPI endpoint, a manual check can be enough at first:

```bash
curl "http://127.0.0.1:7860/api/greet?name=Asha"
# {"message":"Hello, Asha!"}
```

For a site change, use the same build command every loop:

```bash
npm run lint
npm run test
npm run build
```

The check is useful only when you know what success looks like. Write the expected result before you run it.

## 4. Work through a complete example

**Goal:** Add a greeting endpoint without breaking the app.

1. Expected result: `GET /api/greet?name=Asha` returns a JSON greeting.
2. Change: add only the `greet()` route in `app.py`.
3. Check: run Uvicorn and use `curl`.
4. Observe: if the response is `404`, confirm the route path and restart the server.
5. Improve: add a test after the manual check works.

This is intentionally slower than guessing, but it becomes much faster than debugging many unknown changes together.

## 5. Add feedback at the right level

| Level | Feedback example | When to use it |
| --- | --- | --- |
| Code | Formatter, linter, unit test | Every small code change |
| Application | `curl`, API test, browser check | When a feature crosses components |
| Build | `npm run build`, Docker build | Before a pull request or deployment |
| Production | Logs, errors, latency, user reports | After release |

Start close to the code. A unit test is faster than a full deployment. Move to broader checks only when the smaller check passes.

## 6. Keep a small engineering record

For a feature or bug, record four lines in an issue, pull request, or notes file:

```text
Goal: /health returns 200.
Change: added a FastAPI health endpoint.
Check: curl /health returns {"status":"ok"}.
Result: passed locally; ready for CI.
```

This makes handoffs easier and helps you avoid repeating failed experiments.

## Good habits

- Keep each change small enough to understand and revert.
- Use the same check every time so results are comparable.
- Write down the expected result before testing.
- Automate a useful check once you run it often.
- Stop and investigate when a result surprises you; do not hide it with another change.

## Practice

Choose one improvement to the FastAPI example: add `/api/version`, validate an empty name, or add a health-check test. Write the expected result, make the smallest change, run the same check twice, and record the outcome.

[Read Google's introduction to monitoring and feedback signals](https://sre.google/sre-book/monitoring-distributed-systems/)

[Read the Google SRE workbook chapter on service level objectives](https://sre.google/workbook/implementing-slos/)

[Open the loop engineering slides](../../slides/loop-engineering/)

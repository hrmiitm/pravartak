---
title: Loop engineering
description: Improve software through small changes and fast feedback.
sidebar:
  order: 3
---

# Loop engineering

Loop engineering means working in a short cycle: **measure → change → check → learn → repeat**. It helps beginners avoid making many changes without knowing what helped.

## A simple loop

1. Choose one small goal: “The greeting API should return a response.”
2. Make one small change.
3. Run one check, such as a test or a manual request.
4. Read the result and logs.
5. Keep the change, improve it, or undo it.

## Example

```bash
curl "http://127.0.0.1:7860/api/greet?name=Asha"
# {"message":"Hello, Asha!"}
```

If the response is wrong, change only the greeting function, run the same command again, and compare the result.

## Good habits

- Keep each change small enough to understand and revert.
- Use the same check every time so results are comparable.
- Write down the expected result before testing.
- Automate a useful check once you run it often.

[Read Google's introduction to monitoring and feedback signals](https://sre.google/sre-book/monitoring-distributed-systems/)

[Open the loop engineering slides](../../slides/loop-engineering/)

---
marp: true
title: Loop Engineering
description: Small changes and fast feedback
theme: default
size: 16:9
paginate: true
---

# Loop engineering

Improve one small thing at a time.

---

## The loop

```text
Measure → small change → check → learn → repeat
```

Choose one expected result before changing code.

---

## Example check

```bash
curl "http://127.0.0.1:7860/api/greet?name=Asha"
```

- Did it return the expected greeting?
- If not, change one thing and run the same check again.

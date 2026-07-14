---
marp: true
title: CI/CD with GitHub Actions
description: Check code before it is deployed
theme: default
size: 16:9
paginate: true
---

# CI/CD with GitHub Actions

Check first. Deploy verified code.

---

## The path to deployment

```text
Branch → pull request → test + build → review → merge → deploy
```

- **CI** checks every change.
- **CD** releases a checked change.

---

## A tiny workflow

```yaml
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: npm ci && npm run build
```

Use protected branches to require checks before merge.

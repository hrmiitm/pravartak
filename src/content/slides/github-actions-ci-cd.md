---
marp: true
title: CI/CD with GitHub Actions
description: Check code before it is deployed
theme: default
size: 16:9
paginate: true
---

# CI/CD with GitHub Actions

From a push to a safe deployment.

---

## The delivery path

```text
Branch → pull request → CI checks → review → protected branch → deploy
```

- **CI** checks every change.
- **CD** releases a checked change.

---

## Where workflows live

```text
repository/
└── .github/
    └── workflows/
        └── api-checks.yml
```

Each workflow contains events, jobs, and steps.

---

## Trigger a workflow

```yaml
on:
  pull_request:
  push:
    branches: [dev]
```

- `pull_request` checks proposed changes
- `push` checks changes already on `dev`

---

## A beginner workflow

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run build
```

---

## Read the key words

| Word | Meaning |
| --- | --- |
| `on` | event that starts a workflow |
| `jobs` | groups of work |
| `runs-on` | temporary machine |
| `uses` | reusable action |
| `run` | shell command |

---

## Deploy only verified code

```yaml
deploy:
  needs: test
  if: github.ref == 'refs/heads/dev'
```

- Require checks with branch protection
- Put tokens in GitHub Secrets
- Read the first failed log line and reproduce it locally

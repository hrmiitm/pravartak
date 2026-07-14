---
title: CI/CD with GitHub Actions
description: Run checks automatically and deploy only verified code.
sidebar:
  order: 4
---

# CI/CD with GitHub Actions

**Continuous integration (CI)** runs checks when code changes. **Continuous delivery/deployment (CD)** releases code after those checks pass.

## Basic flow

1. Create a branch and make a change.
2. Push it and open a pull request.
3. GitHub Actions runs linting, tests, and a build.
4. Review the pull request.
5. Merge only when required checks pass; the deployment workflow can then run.

## Small Python check

Create `.github/workflows/api-checks.yml`:

```yaml
name: API checks
on: [pull_request, push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r examples/huggingface-fastapi/requirements.txt
      - run: python -c "import sys; sys.path.insert(0, 'examples/huggingface-fastapi'); from app import app; assert app.title == 'Hello FastAPI'"
```

## Beginner checklist

- Run the same commands locally before pushing.
- Keep CI focused on checks: lint, test, and build.
- Use branch protection to require passing checks before merge.
- Store deployment tokens in GitHub Secrets, not workflow files.

[Read GitHub's official Python workflow guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)

[Open the GitHub Actions slides](../../slides/github-actions-ci-cd/)

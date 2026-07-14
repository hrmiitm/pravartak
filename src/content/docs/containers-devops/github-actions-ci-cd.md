---
title: CI/CD with GitHub Actions
description: Run checks automatically and deploy only verified code.
sidebar:
  order: 4
---

# CI/CD with GitHub Actions

**Continuous integration (CI)** runs checks when code changes. **Continuous delivery/deployment (CD)** releases a version only after those checks pass. GitHub Actions stores workflows as YAML files in `.github/workflows/`.

## 1. See the delivery path

1. Create a branch and make a change.
2. Push it and open a pull request.
3. GitHub Actions runs linting, tests, and a build.
4. Review the pull request.
5. Merge only when required checks pass; the deployment workflow can then run.

```text
Developer → branch → pull request → CI checks → review → protected branch → deploy
```

CI answers: “Is this revision safe to review?” CD answers: “Can this verified revision be released?”

## 2. Your first workflow

Create `.github/workflows/api-checks.yml`:

```yaml
name: API checks

on:
  pull_request:
  push:
    branches: [dev]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: examples/huggingface-fastapi/requirements.txt
      - run: pip install -r examples/huggingface-fastapi/requirements.txt
      - run: python -c "import sys; sys.path.insert(0, 'examples/huggingface-fastapi'); from app import app; assert app.title == 'Hello FastAPI'"
```

### What each part means

| YAML part | Purpose |
| --- | --- |
| `name` | A readable name shown in the Actions tab |
| `on` | Events that start the workflow |
| `pull_request` | Run when a pull request changes |
| `push.branches` | Run after a push to the named branch |
| `jobs` | Independent groups of work |
| `runs-on` | The temporary machine type |
| `steps` | Commands or reusable actions run in order |
| `uses` | Run an existing action, such as checkout |
| `run` | Run a shell command |

`actions/checkout` downloads the repository onto the runner. `actions/setup-python` installs a predictable Python version. The pip cache makes repeated workflows faster; it does not cache your application code.

## 3. Add lint, test, and build checks

A web project commonly has separate checks:

```yaml
- name: Install JavaScript dependencies
  run: npm ci
- name: Lint
  run: npm run lint
- name: Test
  run: npm run test
- name: Build
  run: npm run build
```

Use `npm ci` in CI because it installs exactly the versions in `package-lock.json`. Run these same commands locally before you push.

## 4. Use inputs, variables, and secrets safely

Put a non-secret value in an environment variable:

```yaml
env:
  APP_ENV: test

steps:
  - run: echo "Running in $APP_ENV"
```

Put passwords, API keys, and deployment tokens in **Settings → Secrets and variables → Actions**. Use a secret without printing it:

```yaml
- name: Deploy
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./scripts/deploy.sh
```

Never hard-code a secret in YAML, source code, a commit message, or log output. GitHub masks many secret values, but masking is not a replacement for careful commands.

## 5. Run multiple versions with a matrix

Use a matrix when a project supports more than one runtime:

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

GitHub creates one job for each matrix value. Start with one version; add a matrix only when you need compatibility coverage.

## 6. Add a simple deployment gate

Deployment should depend on a successful build and should run only from the delivery branch:

```yaml
deploy:
  needs: test
  if: github.ref == 'refs/heads/dev'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v6
    - run: ./scripts/deploy.sh
```

- `needs: test` prevents deployment when the test job fails.
- `if` prevents deployment from a pull-request branch.
- Add repository branch protection so a pull request cannot merge while required checks fail.

## 7. Debug a failed workflow

1. Open the failed run in the **Actions** tab.
2. Open the failed step and read the first error, not only the last line.
3. Run the same command locally.
4. Fix the smallest cause and push again.
5. Keep logs useful, but never print secrets.

## Practice

Create a pull request that changes a README line. Confirm your workflow appears in the Actions tab and passes before merging it.

[Read GitHub's official Python workflow guide](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)

[Read GitHub's workflow syntax reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)

[Open the GitHub Actions slides](../../slides/github-actions-ci-cd/)

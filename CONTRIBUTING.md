# Contributing

## Workflow

1. Pick an issue, or open one first if the work isn't tracked yet. Assign it to yourself.
2. Branch off `main`:
   ```bash
   git switch main && git pull
   git switch -c <your-name>/<short-description>    # e.g. diana/passport-csv-import
   ```
3. Commit small, focused changes with a clear message in the imperative:
   `Add PASSPort CSV parser`, not `stuff` or `fixed things`.
4. Push and open a pull request. Fill in the template, including your time estimate
   versus actual.
5. Get at least one approving review. CI (lint and tests) must pass.
6. Squash and merge. Delete the branch.

Nobody pushes directly to `main`.

## Reviews

Everyone reviews at least one teammate's pull request each week. Review within 24 hours
when you're requested. Comment on what's wrong and why; approve when it's good enough to
build on, not when it's perfect.

## Running checks locally

```bash
cd backend
source .venv/bin/activate
ruff check . && ruff format --check .
pytest
```

`ruff format .` fixes formatting for you.

## Data

Never commit real nonprofit data, PASSPort exports, credentials or `.env` files. Use
made-up data in tests and fixtures. `data/` and `uploads/` are git-ignored for this reason.

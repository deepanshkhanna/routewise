# Contributing

## Before you change code

1. Read [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md).
2. Skim [docs/PROJECT_FILE_GUIDE.md](docs/PROJECT_FILE_GUIDE.md).
3. Keep honesty labels intact: never blur `SOFTWARE_SIMULATION` and `REAL_LAB`.

## Dev loop

```bash
# backend
cd backend && source .venv/bin/activate   # or Windows Activate.ps1
pytest -q
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# frontend
cd frontend && npm run dev
```

## Rules of thumb

- No arbitrary shell from API clients — keep Docker/`vtysh` allow-lists.
- Do not commit `.env`, `backend/data/`, `*.db`, or `lab/clab-*` runtime artifacts.
- Prefer small, focused PRs with conventional commits: `feat|fix|docs|refactor|test|chore(scope): summary`.
- After frontend changes: `npm run build`. After backend changes: `pytest -q`.

## Docs

Update [docs/README.md](docs/README.md) if you add a new guide. Keep the UI tour in [docs/UI_BROWSING_GUIDE.md](docs/UI_BROWSING_GUIDE.md) in sync with routes in `frontend/src/App.jsx`.

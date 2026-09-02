# Contributing

Thanks for your interest in improving CareerPilot AI! This guide explains how to set up your development environment, run the tests, and submit a change.

## Code of conduct

Be respectful. Assume good intent. Help others learn. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) (or open an issue to discuss adding one).

## Development environment

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| Git | 2.30+ |
| Docker (optional) | 24+ |

### Setup

```bash
# 1. Fork and clone
git clone https://github.com/your-username/career-pilot-ai.git
cd career-pilot-ai

# 2. Backend
cd backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env

# 3. Frontend
cd ../frontend
npm install
cp .env.example .env

# 4. (Optional) Install pre-commit hooks
pip install pre-commit
cd ..
pre-commit install
```

### Run the dev stack

```bash
# Terminal 1 – backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 – frontend
cd frontend
npm run dev
```

App is live at http://localhost:3000.

## Branching & commits

### Branch naming

```
feat/short-description       # new feature
fix/short-description        # bug fix
docs/short-description       # docs only
refactor/short-description   # code refactor (no behavior change)
test/short-description       # tests only
chore/short-description      # tooling, deps, etc.
```

### Commit messages (Conventional Commits)

```
<type>(<scope>): <short summary>

<optional body explaining the why>

<optional footer with issue references>
```

Examples:

```
feat(resume): add DOCX export to analysis endpoint
fix(upload): sanitize filenames containing path separators
docs(readme): clarify Docker setup steps
chore(deps): bump FastAPI to 0.115
```

## Tests

### Backend

```bash
cd backend
pytest                              # run all tests
pytest -v                           # verbose
pytest tests/test_resume_service.py # single file
pytest -k "test_score"              # by keyword
pytest --cov=app --cov-report=term-missing   # with coverage
```

### Frontend

```bash
cd frontend
npm run test                  # run once
npm run test:watch            # watch mode
npm run test:coverage         # with coverage
```

### Linting & type checking

Run these before every commit:

```bash
# Backend
cd backend
ruff check app tests
black --check app tests
mypy app

# Frontend
cd frontend
npm run lint
npm run typecheck
```

## Pull request workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout main
   git pull
   git checkout -b feat/your-feature
   ```

2. **Make your changes** — write code, add tests, update docs

3. **Run the full check suite**:
   ```bash
   # Backend
   cd backend
   ruff check app tests && black --check app tests && mypy app && pytest

   # Frontend
   cd ../frontend
   npm run lint && npm run typecheck && npm run test
   ```

4. **Commit** with a Conventional Commit message

5. **Push** and **open a Pull Request** against `main`:
   - Use the PR template (auto-populated)
   - Describe what & why
   - Link any related issues (`Closes #123`)
   - Add screenshots for UI changes

6. **Address review feedback** — push additional commits to your branch

7. **Squash & merge** once approved (the maintainer will do this)

## Style guide

### Python (backend)

- **PEP 8** with `black` (line length 88)
- **Type hints** on all public functions (mypy strict)
- **Docstrings** (Google style) for all public modules, classes, functions
- Use `pathlib.Path` not `os.path`
- Prefer composition over inheritance
- Raise specific exceptions, not bare `Exception`
- Use `logging.getLogger(__name__)` per module

### TypeScript (frontend)

- **TypeScript strict mode** — no `any` unless necessary
- **Functional components** with hooks (no class components)
- **Props interfaces** named `<Component>Props`
- **Export only what's used** — barrel files are fine but tree-shake
- Use `const` for everything that's not reassigned
- Prefer named exports over default exports (except page components)

### File organization

- One component per file
- File name matches the component name (`Button.tsx` → `export function Button`)
- Co-locate tests with components when small (`Button.test.tsx`)
- Group utility functions in `utils/`, not scattered

## Adding a new feature

1. **Open an issue first** — describe the use case, get feedback
2. **Get approval** before writing significant code
3. **Add tests** for new functionality
4. **Update documentation** (README, docs/, JSDoc)
5. **Open a PR** with screenshots/demos for visual changes

## Adding a new API endpoint

1. **Define the Pydantic schema** in `app/schemas/`
2. **Add the service function** in `app/services/` (pure business logic)
3. **Add the route handler** in `app/api/<resource>.py`
4. **Include the router** in `app/api/router.py`
5. **Add tests** in `tests/test_<resource>_service.py`
6. **Update the API table** in `README.md`

## Adding a new page

1. **Create the page component** in `frontend/src/pages/`
2. **Add a route** in `frontend/src/App.tsx`
3. **Add a nav link** in `frontend/src/components/NavBar.tsx`
4. **Add a smoke test** in `frontend/src/__tests__/`
5. **Document** any new API calls in `docs/ARCHITECTURE.md`

## Releases

We follow [Semantic Versioning](https://semver.org/):

- **Major** (v2.0.0) — breaking changes
- **Minor** (v1.1.0) — new features, backwards compatible
- **Patch** (v1.0.1) — bug fixes

Releases are created by pushing a tag: `git tag v1.0.1 && git push --tags`.

## Questions?

- Open a [Discussion](https://github.com/your-org/career-pilot-ai/discussions)
- Join our community chat (TBD)
- Email maintainers (see git log)

Thanks for contributing! 🎉

# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

- **Goal:** Python FastAPI Backend for Korea Investment & Securities (KIS) Stock Trading
- **Tech Stack:** FastAPI, Pydantic, SQLModel, SQLite
- **External API:** KIS Open API (RESTful)

## Critical Rules

### 1. Code Organization

- Clean Architecture: api → services → clients
- High cohesion, low coupling
- 200-400 lines typical, 800 max per file
- Isolate all KIS-specific logic in `app/clients/kis_client.py`

### 2. Code Style

- PEP 8 compliance
- Type hints mandatory for all function signatures
- Docstrings for complex logic (in Korean)
- No hardcoded secrets - use environment variables
- Input validation with Pydantic

### 3. Security

- NEVER log `APP_KEY`, `APP_SECRET`, `ACCESS_TOKEN`
- Token caching required to avoid API rate limits
- Environment variables via `pydantic-settings`
- `.env` and `token.json` must be in `.gitignore`

### 4. Testing

- Mock all KIS API calls
- Use fixtures instead of `.env` in tests
- Naming: `test_{method}_{scenario}`
- Run `pytest` before every commit

## File Structure

```
kis_api_backend/
├── app/
│   ├── api/endpoints/    # Route definitions
│   ├── services/         # Business logic
│   ├── clients/          # External API adapters (KIS)
│   ├── schemas/          # Pydantic models (DTOs)
│   ├── models/           # SQLModel database models
│   └── core/             # Config, security, exceptions
├── tests/
│   ├── test_kis_client.py
│   └── test_api/
└── .env
```

## Key Patterns

### API Response Format

```python
# Success
{"success": True, "data": {...}}

# Error
{"success": False, "error": "User-friendly message"}
```

### Error Handling

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail=f"KIS API 호출 실패: {str(e)}"
)
```

### Exception Hierarchy

```python
class KISAPIError(Exception): pass
class TokenExpiredError(KISAPIError): pass
class InvalidAccountError(KISAPIError): pass
```

## Environment Variables

```bash
# Required - KIS API
KIS_APP_KEY=
KIS_APP_SECRET=
KIS_ACCOUNT_NUMBER=
KIS_ACCOUNT_PRODUCT_CODE=

# Required - App
SECRET_KEY=
ENVIRONMENT=virtual  # or "real"

# Optional
DEBUG=false
```

## Development Workflow

**Important:** Follow `.claude/rules/devlog.md` for detailed workflow.

1. Check issue and create devlog with implementation plan
2. **Wait for user approval** before writing code
3. Create feature branch: `feature/issue-{number}-{description}`
4. Implement with tests (update devlog in real-time)
5. Run `pytest` before commit
6. Commit (Korean, conventional commits) and push
7. Create PR with `gh pr create`

See `.claude/rules/git-workflow.md` for detailed git conventions.

## Expected Outputs

Before completing any task, verify:
- All tests pass: `pytest` shows "XX passed"
- No console.log or debug prints in production code
- Health endpoint returns: `{"status":"healthy"}`
- API docs accessible at `/docs`
- Code passes `/code-review` or `/python-review`

See `.claude/rules/testing.md` for detailed verification criteria.

## Context Management

- Use `/compact` when context usage >50%
- Use `/clear` when starting new issue
- Delegate codebase exploration to Explore agent
- Use planner agent for complex features

See `.claude/rules/context-management.md` for strategies.

## Available Commands

- `/plan` - Create implementation plan
- `/code-review` - Review code quality
- `/python-review` - Python-specific code review
- `/tdd` - Test-driven development workflow

## Detailed Guidelines

All detailed rules are in `.claude/rules/`:
- `devlog.md` - Development workflow and devlog format
- `git-workflow.md` - Git branching, commits, PR templates
- `testing.md` - Testing requirements and verification
- `coding-style.md` - Code organization and patterns
- `security.md` - Security guidelines
- `context-management.md` - Context optimization strategies

---

**Last Updated:** 2026-02-04

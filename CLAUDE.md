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

## Available Commands

- `/plan` - Create implementation plan
- `/code-review` - Review code quality
- `/python-review` - Python-specific code review
- `/tdd` - Test-driven development workflow
- `/verify` - Verify implementation
- `/build-fix` - Fix build errors
- `/test-coverage` - Check test coverage
- `/update-docs` - Update documentation

## Git Workflow

### Branching

```bash
git checkout main && git pull origin main
git checkout -b feature/issue-{number}-{description}
```

### Commit Style (Korean)

```bash
git commit -m "feat: KIS 인증 토큰 발급 로직 구현

- OAuth2 접근 토큰 발급 및 갱신 로직 추가
- 토큰 파일 캐싱 구현

Relates to #1

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Prefixes:** `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

### Pull Request

```bash
gh pr create --title "feat: {Title} (#{IssueNumber})" --body "$(cat <<'EOF'
## Summary
{간략한 요약}

## Changes
- {변경사항}

## Test plan
- [ ] {테스트 항목}

Closes #{IssueNumber}
EOF
)"
```

## Development Workflow

**Important:** Follow `.claude/rules/devlog.md` for detailed devlog workflow.

1. `gh issue view {number}` - Check issue
2. Create devlog in `docs/devlog/YYYY-MM-DD.md` with implementation plan
3. **Wait for user approval** before writing code
4. Create feature branch
5. Implement with tests (update devlog in real-time)
6. `pytest` - Run tests
7. Commit and push
8. `gh pr create` - Create PR
9. Wait for review and merge

## Quick Reference

```bash
# Dev server
cd kis_api_backend
source venv/bin/activate
uvicorn app.main:app --reload

# Tests
pytest
pytest --cov=app --cov-report=html

# API Docs
# http://localhost:8000/docs (Swagger)
# http://localhost:8000/redoc (ReDoc)
```

---

**Last Updated:** 2026-02-03

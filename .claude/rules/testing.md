# Testing Requirements

## Minimum Test Coverage: 80%

Test Types (ALL required):
1. **Unit Tests** - Individual functions, utilities, components
2. **Integration Tests** - API endpoints, database operations
3. **E2E Tests** - Critical user flows (Playwright)

## Test-Driven Development

MANDATORY workflow:
1. Write test first (RED)
2. Run test - it should FAIL
3. Write minimal implementation (GREEN)
4. Run test - it should PASS
5. Refactor (IMPROVE)
6. Verify coverage (80%+)

## Troubleshooting Test Failures

1. Use **tdd-guide** agent
2. Check test isolation
3. Verify mocks are correct
4. Fix implementation, not tests (unless tests are wrong)

## Success Criteria

Before marking any task complete, verify:

### Test Results
- All tests pass: Look for `===== XX passed =====` in pytest output
- Test coverage ≥80%: Run `pytest --cov=app --cov-report=term`
- No warnings about missing fixtures or deprecated features

### Code Quality
- No `console.log`, `print()`, or debug statements in production code
- No commented-out code blocks
- All imports used (no unused imports)
- Type hints present for all function signatures

### API Verification
- Health endpoint returns: `{"status":"healthy"}`
- API docs accessible at `/docs` (Swagger UI)
- All new endpoints return proper status codes:
  - 200 for success
  - 400 for validation errors
  - 401 for auth failures
  - 500 for server errors

### Deployment Verification
- GitHub Actions tests pass (green checkmark)
- Cloud Run deployment succeeds
- Deployed service responds to health check
- New endpoints accessible on production URL

### Example Success Output

```bash
# Pytest
===== 39 passed, 201 warnings in 3.14s =====

# Health Check
$ curl https://kis-api-backend-cudfz6ybdq-du.a.run.app/health
{"status":"healthy"}

# Coverage
app/services/stats_service.py    95%
app/api/v1/endpoints/stats.py    88%
TOTAL                             82%
```

## Agent Support

- **tdd-guide** - Use PROACTIVELY for new features, enforces write-tests-first
- **e2e-runner** - Playwright E2E testing specialist

# CLAUDE.md

This file provides guidance to **Claude Code** (Anthropic's CLI Agent) when working with code in this repository.

## 🚨 0. PRIMARY WORKFLOW (MANDATORY)

**Claude Code must follow this "Devlog + Git Flow" hybrid workflow for EVERY non-trivial task.**

### Phase 1: Analyze & Plan (Devlog)
1.  **Fetch Issue:** Use `gh issue view {issue_number}` to understand requirements.
2.  **Check/Create Devlog:**
    - Directory: `docs/devlog/`
    - Filename: `YYYY-MM-DD-NN-task-name.md` (e.g., `2026-01-23-01-auth-feature.md`)
    - Content: Objective, Requirements Analysis, Step-by-Step Plan, Testing Strategy.
3.  **User Approval:** **WAIT** for the user to approve the plan in the devlog before writing code.

### Phase 2: Branch & Execute (Git Flow)
1.  **Create Branch:** `git checkout -b feature/issue-{number}-{description}`.
2.  **Implement:** Write code according to the Devlog plan.
3.  **Verify:** Run tests (`pytest`) and check `git diff` to ensure quality.

### Phase 3: Commit & PR
1.  **Commit:** Use Conventional Commits (See below).
2.  **Push:** `git push -u origin feature/...`
3.  **Create PR:** Use `gh pr create` with the detailed template provided below.
4.  **Wait for Review:** Notify the user and wait for the merge command.

---

# 📘 Claude Code Development Guide

## 🏗 Project Context

### Project Overview
- **Goal:** Build a Python FastAPI Backend for **Korea Investment & Securities (KIS) Stock Trading**.
- **Developer & Client:** This system is built and primarily used by **Claude Code (AI Agent)**.
- **External System:** KIS Open API (RESTful).

### Architecture (Clean Architecture)
- **app/api/** – Routers (Endpoints)
  - `endpoints/`: Route definitions (e.g., `auth.py`, `balance.py`, `order.py`).
- **app/services/** – Business Logic
  - Orchestrates calls between API adapter and data processing.
- **app/clients/** – External API Adapters
  - `kis_client.py`: Wrapper for KIS Open API. **Isolate all KIS-specific logic here.**
- **app/schemas/** – Pydantic Models (DTOs)
  - Strict typing for JSON data exchange.
- **app/core/** – Configuration (`.env`) & Security.

### Key Constraints
1.  **Token Caching:** KIS Access Token **MUST** be cached (file/memory) to avoid API rate limits.
2.  **Security:** NEVER log `APP_KEY`, `APP_SECRET` or `ACCESS_TOKEN` in the console or files.
3.  **Environment:** Support both **Real (실전)** and **Virtual (모의)** domains via config.

---

## 🛠 Git & GitHub Workflow (Detailed)

### 1. Issue & Branching
Always start with a GitHub Issue.

```bash
# Check issues
gh issue list

# Create Feature Branch
git checkout main
git pull origin main
git checkout -b feature/issue-{number}-{description}
```

### 2. Commit Style (Korean)
Commits must be in Korean and follow Conventional Commits.

```bash
git commit -m "feat: KIS 인증 토큰 발급 로직 구현

- OAuth2 접근 토큰 발급 및 갱신 로직 추가
- 토큰 파일 캐싱(token.json) 구현
- .gitignore에 토큰 파일 추가

Relates to #1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Commit Prefix (Korean):**
- `feat:` - 새로운 기능 추가
- `fix:` - 버그 수정
- `docs:` - 문서 작성/수정
- `refactor:` - 코드 리팩토링
- `test:` - 테스트 추가/수정
- `chore:` - 빌드, 패키지 매니저 설정

### 3. Pull Request (PR)
Use `gh` to create detailed PRs.

```bash
gh pr create --title "feat: {Title} (#{IssueNumber})" --body "$(cat <<'EOF'
## Summary
{간략한 요약}

## Changes
- {변경사항 1}
- {변경사항 2}

## Test plan
- [ ] {테스트 항목 1}
- [ ] {테스트 항목 2}

## Related Issues
Closes #{IssueNumber}

🤖 Generated with Claude Code
EOF
)"
```

---

## ⚡ Claude Code Specific Guidelines

### Tool Usage
- **Read Before Edit:** Always use `ls`, `cat`, or `grep` to understand the codebase before editing.
- **Devlog First:** Do not skip the `docs/devlog/` step. It is the "brain" of the project.
- **Run Tests:** Use `pytest` or `python -m pytest` frequently.

### Code Style
- **Python:** PEP 8 compliance.
- **Type Hints:** Mandatory for all function signatures (Pydantic style).
- **Docstrings:** Required for complex logic (in Korean).

### Communication
- **Language:** Use Korean for all Devlogs, Commits, and PR descriptions.
- **Tone:** Professional, technical, and concise.

---

## 🧪 Testing Guidelines

### Test Structure
```
kis_api_backend/
├── tests/
│   ├── __init__.py
│   ├── test_kis_client.py      # KIS API 클라이언트 테스트
│   ├── test_token_manager.py   # 토큰 관리 테스트
│   └── test_api/
│       ├── __init__.py
│       └── test_account.py     # API 엔드포인트 테스트
```

### Test Commands
```bash
# 모든 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_kis_client.py

# 커버리지 확인
pytest --cov=app --cov-report=html

# 특정 테스트만 실행
pytest tests/test_kis_client.py::test_get_balance -v
```

### Test Writing Rules
1. **Mock External APIs:** KIS API 호출은 항상 mock 처리
2. **Environment Variables:** 테스트에서는 `.env` 대신 fixture 사용
3. **Test Naming:** `test_{method}_{scenario}` 형식 (e.g., `test_get_balance_success`)

---

## 📝 API Documentation

### FastAPI Auto-Docs
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Endpoint Documentation Rules
```python
@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    account_service: AccountService = Depends(get_account_service)
):
    """
    계좌 잔고 조회

    KIS API를 통해 계좌의 잔고 정보를 조회합니다.

    Returns:
        BalanceResponse: 총 자산, 예수금, 손익, 보유 종목 정보

    Raises:
        HTTPException: KIS API 호출 실패 시 500 에러
    """
    return account_service.get_balance()
```

---

## 🚨 Error Handling

### Exception Hierarchy
```python
# app/core/exceptions.py
class KISAPIError(Exception):
    """KIS API 관련 기본 예외"""
    pass

class TokenExpiredError(KISAPIError):
    """토큰 만료 예외"""
    pass

class InvalidAccountError(KISAPIError):
    """유효하지 않은 계좌 정보"""
    pass
```

### API Error Response
```python
from fastapi import HTTPException, status

# Bad Request (400)
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="잘못된 요청입니다."
)

# Unauthorized (401)
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증이 필요합니다."
)

# Internal Server Error (500)
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail=f"KIS API 호출 실패: {str(e)}"
)
```

---

## 📊 Logging

### Logging Configuration
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 사용 예시
logger.info("토큰 발급 성공")
logger.warning("토큰 만료 임박")
logger.error(f"API 호출 실패: {error}")
```

### Logging Rules
1. **민감 정보 금지:** `APP_KEY`, `APP_SECRET`, `ACCESS_TOKEN` 절대 로그에 남기지 않음
2. **로그 레벨:**
   - `DEBUG`: 개발 중 디버깅 정보
   - `INFO`: 일반적인 동작 흐름
   - `WARNING`: 경고 (토큰 만료 임박 등)
   - `ERROR`: 에러 발생

---

## 🔐 Security Checklist

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] `token.json` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] 민감 정보가 로그에 출력되지 않는가?
- [ ] API 키가 코드에 하드코딩되지 않았는가?
- [ ] 환경 변수가 `pydantic-settings`로 관리되는가?

---

## 🔄 Development Cycle Summary

```
1. Issue 확인 (gh issue view)
   ↓
2. Devlog 작성 (docs/devlog/)
   ↓
3. 사용자 승인 대기
   ↓
4. Branch 생성 (feature/issue-X-description)
   ↓
5. 코드 구현
   ↓
6. 테스트 실행 (pytest)
   ↓
7. Commit (Korean + Conventional Commits)
   ↓
8. Push & PR 생성
   ↓
9. 리뷰 & Merge
   ↓
10. Branch 정리
```

---

## 📚 Quick Reference

### Essential Commands
```bash
# 개발 서버 실행
cd kis_api_backend
source venv/bin/activate  # or: source ../venv/bin/activate
uvicorn app.main:app --reload

# 테스트 실행
pytest

# 이슈 & PR
gh issue list
gh issue view {number}
gh pr create
gh pr list

# Git 기본
git status
git diff
git log --oneline -10
```

### Environment Setup
```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r kis_api_backend/requirements.txt

# 환경 변수 설정
cp kis_api_backend/.env.example kis_api_backend/.env
# .env 파일을 편집하여 실제 값 입력
```

---

**Last Updated:** 2026-01-23
**Maintained By:** Claude Code & Human Developer
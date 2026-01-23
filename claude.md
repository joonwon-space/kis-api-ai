# Claude AI 개발 가이드

이 문서는 Claude AI를 사용하여 프로젝트를 개발할 때 따라야 할 워크플로우와 규칙을 정의합니다.

## Git 워크플로우

### 1. 이슈 기반 개발

모든 작업은 GitHub Issue를 기반으로 진행합니다.

```bash
# 1. 현재 이슈 확인
gh issue list

# 2. 특정 이슈 상세 보기
gh issue view [issue_number]
```

### 2. Feature 브랜치 생성

새로운 작업을 시작할 때는 항상 feature 브랜치를 생성합니다.

```bash
# main 브랜치에서 시작
git checkout main
git pull origin main

# feature 브랜치 생성 (네이밍: feature/issue-{번호}-{간단한-설명})
git checkout -b feature/issue-2-stock-order-api

# 또는
git checkout -b feature/issue-3-websocket-realtime
```

**브랜치 네이밍 규칙:**
- `feature/issue-{번호}-{설명}` - 새로운 기능
- `fix/issue-{번호}-{설명}` - 버그 수정
- `refactor/issue-{번호}-{설명}` - 리팩토링
- `docs/issue-{번호}-{설명}` - 문서 작업

### 3. 개발 및 커밋

작업을 진행하고 의미 있는 단위로 커밋합니다.

```bash
# 변경사항 확인
git status
git diff

# 파일 스테이징
git add [files...]

# 커밋 (Conventional Commits 형식 사용)
git commit -m "feat: Add stock order API endpoint

- Implement buy/sell order functionality
- Add order validation logic
- Update API documentation

Relates to #2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**커밋 메시지 형식:**
- `feat:` - 새로운 기능
- `fix:` - 버그 수정
- `docs:` - 문서 변경
- `refactor:` - 코드 리팩토링
- `test:` - 테스트 추가/수정
- `chore:` - 빌드 프로세스, 의존성 업데이트 등

### 4. 브랜치 푸시

로컬 브랜치를 원격 저장소에 푸시합니다.

```bash
# 첫 푸시 시 upstream 설정
git push -u origin feature/issue-2-stock-order-api

# 이후 푸시
git push
```

### 5. Pull Request 생성

브랜치를 푸시한 후 PR을 생성합니다.

```bash
# GitHub CLI를 사용한 PR 생성
gh pr create --title "feat: Implement stock order API (#2)" --body "$(cat <<'EOF'
## Summary
주식 매수/매도 API 엔드포인트 구현

## Changes
- 매수/매도 주문 API 엔드포인트 추가
- 주문 검증 로직 구현
- API 문서 업데이트

## Test plan
- [ ] 매수 주문 테스트
- [ ] 매도 주문 테스트
- [ ] 잘못된 입력값 검증 테스트
- [ ] 모의투자 계좌에서 실제 주문 테스트

## Related Issues
Closes #2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

# 또는 간단하게
gh pr create
# (대화형으로 제목과 본문 입력)
```

**PR 제목 형식:**
- `feat: [기능 설명] (#이슈번호)`
- `fix: [버그 설명] (#이슈번호)`
- `docs: [문서 설명] (#이슈번호)`

### 6. 코드 리뷰 및 수정

PR 생성 후 리뷰를 받고 필요시 수정합니다.

```bash
# 리뷰 피드백 반영 후 추가 커밋
git add [files...]
git commit -m "fix: Address review feedback"
git push

# PR 상태 확인
gh pr status

# PR 코멘트 확인
gh pr view [pr_number]
```

### 7. PR 병합 및 이슈 종료

리뷰가 완료되면 PR을 병합합니다.

```bash
# PR 병합 (GitHub CLI)
gh pr merge [pr_number] --squash

# 또는 웹에서 "Squash and merge" 버튼 클릭
```

**PR 본문에 다음 키워드를 사용하면 자동으로 이슈가 닫힙니다:**
- `Closes #이슈번호`
- `Fixes #이슈번호`
- `Resolves #이슈번호`

### 8. 브랜치 정리

PR이 병합된 후 로컬 브랜치를 정리합니다.

```bash
# main 브랜치로 전환
git checkout main

# main 브랜치 업데이트
git pull origin main

# 병합된 브랜치 삭제
git branch -d feature/issue-2-stock-order-api

# 원격 브랜치도 삭제 (자동으로 삭제되지 않은 경우)
git push origin --delete feature/issue-2-stock-order-api
```

## 빠른 참조

### 전체 워크플로우 요약

```bash
# 1. 이슈 확인 및 브랜치 생성
git checkout main
git pull origin main
git checkout -b feature/issue-X-description

# 2. 작업 및 커밋
# ... 코드 작성 ...
git add .
git commit -m "feat: Description"

# 3. 푸시 및 PR 생성
git push -u origin feature/issue-X-description
gh pr create

# 4. 병합 후 정리
git checkout main
git pull origin main
git branch -d feature/issue-X-description
```

### 유용한 Git 명령어

```bash
# 현재 브랜치 확인
git branch

# 브랜치 전환
git checkout [branch_name]

# 변경사항 임시 저장
git stash
git stash pop

# 최근 커밋 수정
git commit --amend

# 로그 확인
git log --oneline -10

# 원격 저장소 동기화
git fetch origin
git pull origin main
```

### GitHub CLI 명령어

```bash
# 이슈 관리
gh issue list
gh issue view [number]
gh issue create
gh issue close [number]

# PR 관리
gh pr list
gh pr view [number]
gh pr create
gh pr merge [number]
gh pr status

# 저장소 확인
gh repo view
```

## 개발 규칙

### 1. 코드 스타일
- Python: PEP 8 스타일 가이드 준수
- 함수/변수명: snake_case 사용
- 클래스명: PascalCase 사용
- 상수: UPPER_SNAKE_CASE 사용

### 2. 커밋 규칙
- 하나의 커밋은 하나의 논리적 변경사항만 포함
- 커밋 메시지는 명확하고 구체적으로 작성
- Co-Authored-By 태그로 Claude 기여 명시

### 3. PR 규칙
- 하나의 PR은 하나의 이슈와 연결
- PR 제목은 변경사항을 명확하게 표현
- PR 본문에 변경사항, 테스트 계획, 관련 이슈 명시
- 리뷰 가능한 크기로 PR 분할 (500줄 이하 권장)

### 4. 이슈 관리
- 작업 시작 전 이슈 생성
- 이슈에 작업 계획과 완료 조건 명시
- 개발 로그는 `docs/devlog/` 디렉토리에 마크다운 파일로 작성

## 참고 자료

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Git 브랜치 전략](https://nvie.com/posts/a-successful-git-branching-model/)

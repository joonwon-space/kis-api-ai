# 2026-02-04 Devlog #4: Instruction 개선

## [작업 시작] Instruction 구성 개선

### 요청 사항
- CLAUDE.md 및 .claude/rules/ 구성을 everything-claude-code 권장사항에 맞게 개선
- 더 간결하고 효과적인 instruction 구성

### 구현 계획
- [x] **CLAUDE.md 슬림화** (193줄 → 160줄)
  - Git Workflow 섹션 축소 (상세 내용은 git-workflow.md에 있음)
  - Development Workflow 간소화 (devlog.md 참조로 대체)
  - Quick Reference 제거 (개발자용 정보)
  - Expected Outputs 섹션 추가 (검증 기준)
  - Context Management 섹션 추가
  - Detailed Guidelines 섹션으로 다른 파일 참조

- [x] **검증 기준 강화**
  - `.claude/rules/testing.md`에 Success Criteria 섹션 추가 (46줄 증가)
  - 구체적인 테스트 통과 기준 명시 (pytest 출력 예시)
  - API 검증 기준 (health check, /docs 접근성)
  - 배포 후 검증 체크리스트
  - 실제 성공 출력 예시 포함

- [x] **컨텍스트 관리 가이드 추가**
  - `.claude/rules/context-management.md` 신규 파일 생성 (137줄)
  - `/compact`, `/clear` 사용 시점 명시
  - Subagent 활용 전략 정리 (Explore, Planner, Code Reviewer, TDD Guide)
  - 병렬 태스크 실행 가이드
  - 세션 관리 베스트 프랙티스

### 예상 변경 파일
- `CLAUDE.md` — 슬림화 (193줄 → ~120줄)
- `.claude/rules/testing.md` — Success Criteria 추가
- `.claude/rules/context-management.md` — 신규 생성

### 의사결정

#### 1. CLAUDE.md에서 제거할 내용
- **Git Workflow 섹션 (30줄)**: 이미 `.claude/rules/git-workflow.md`에 상세히 있음
  - 간단한 참조만 남기고 상세 내용 제거
- **Development Workflow 섹션 (13줄)**: devlog.md 참조로 대체
- **Quick Reference 섹션 (15줄)**: 개발자가 직접 보는 정보이므로 CLAUDE.md에 불필요
  - README.md에 이미 있거나 있어야 할 내용

#### 2. 추가할 검증 기준
- 테스트 통과 기준: "XX tests passed" 형식
- Health check 기대값: `{"status":"healthy"}`
- API docs 접근성: `/docs` 엔드포인트
- 배포 확인: Cloud Run URL 응답 확인

#### 3. 컨텍스트 관리 전략
- Context >50% 시 /compact 사용
- 새 이슈 시작 시 /clear 권장
- 코드베이스 탐색은 Explore agent 활용
- 구현 전 계획은 planner agent 활용

### 예상 결과
- CLAUDE.md: 193줄 → ~120줄 (약 40% 감소)
- 더 명확한 검증 기준으로 Claude의 자체 검증 능력 향상
- 컨텍스트 관리로 세션 효율성 증가

### 리스크/주의사항
- 너무 많이 제거하면 필요한 정보가 부족할 수 있음
- 중복처럼 보여도 중요한 내용은 유지
- 기존 워크플로우가 잘 작동하므로 조심스럽게 개선

## [작업 완료]

### 결과
- CLAUDE.md 슬림화: 193줄 → 160줄 (17% 감소)
- testing.md 강화: 30줄 → 76줄 (Success Criteria 추가)
- context-management.md 신규: 137줄 (컨텍스트 관리 전략)

### 실제 변경 내용

#### 1. CLAUDE.md 개선
- ✅ Git Workflow 상세 제거 (git-workflow.md 참조로 대체)
- ✅ Development Workflow 간소화
- ✅ Quick Reference 제거 (개발자 정보)
- ✅ Expected Outputs 섹션 추가 (자체 검증 기준)
- ✅ Context Management 섹션 추가
- ✅ Detailed Guidelines 참조 목록 추가

#### 2. testing.md 강화
- ✅ Success Criteria 섹션 추가
  - Test Results: pytest 출력 형식, coverage 기준
  - Code Quality: 금지 패턴 (console.log, print 등)
  - API Verification: health check, /docs 접근성
  - Deployment Verification: CI/CD, Cloud Run
  - 실제 성공 출력 예시

#### 3. context-management.md 신규 생성
- ✅ Core Constraint 설명
- ✅ /compact 사용 시점 (>50% context)
- ✅ /clear 사용 시점 (새 이슈, >75% context)
- ✅ Subagent 전략 (Explore, Planner, Code Reviewer, TDD Guide)
- ✅ 병렬 실행 패턴
- ✅ Session Hygiene 베스트 프랙티스
- ✅ 워크플로우 예시

### 개선 효과

#### 1. CLAUDE.md 가독성 향상
- 핵심 정보만 남겨 스캔 속도 향상
- 상세 내용은 별도 파일로 분리
- 명확한 참조 체계 구축

#### 2. 자체 검증 능력 강화
- Claude가 작업 완료 전 스스로 체크 가능
- 구체적인 기대값 제시 (pytest 출력, API 응답)
- 배포 검증 자동화 가능

#### 3. 컨텍스트 효율성 증대
- 언제 /compact, /clear를 써야 하는지 명확
- Subagent 활용으로 메인 컨텍스트 절약
- 세션 관리 전략으로 품질 유지

### 계획 대비 변경점
- CLAUDE.md 목표 120줄 → 실제 160줄
  - 이유: Expected Outputs, Context Management 섹션 추가
  - 판단: 160줄도 충분히 간결하고, 추가된 내용이 가치 있음

### 메트릭
- **Before**: CLAUDE.md 193줄, rules 471줄, 총 664줄
- **After**: CLAUDE.md 160줄, rules 608줄, 총 768줄
- **CLAUDE.md 개선**: -17% (더 간결)
- **전체 증가**: +16% (상세 가이드 추가로 인한 합리적 증가)

### 다음 할 일
- 실제 사용하면서 효과 측정
- 필요 시 추가 최적화
- 새로운 best practice 발견 시 반영

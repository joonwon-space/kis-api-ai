# 2026-02-04 개발 로그 - Cloud Run Startup Timeout 추가 수정

## [20:40] 작업 계획

### 요청 사항
- PR #18 머지 후에도 Cloud Run 배포 실패 지속
- 에러: "The user-provided container failed to start and listen on the port"
- 로컬에서는 초기화가 0.17초만에 완료되어 문제 없음

### 원인 분석
- 백그라운드 초기화는 정상 작동
- Cloud Run의 startup probe timeout 및 CPU 제한이 문제일 가능성
- Cloud Run 환경에서 네트워크 지연이나 리소스 제약이 있을 수 있음

### 구현 계획
- [x] Cloud Run 배포 설정에 `--startup-cpu-boost` 추가
  - 컨테이너 시작 시 추가 CPU 제공
- [x] `--timeout=300` 추가
  - 요청 타임아웃을 5분으로 설정

### 예상 변경 파일
- `.github/workflows/deploy.yml` — Cloud Run 배포 플래그 추가

### 의사결정
- **startup-cpu-boost 추가 이유:**
  - 컨테이너 시작 시 더 많은 CPU 할당
  - 초기화 속도 향상
- **timeout 연장:**
  - 기본값보다 여유있는 타임아웃 설정
  - 네트워크 지연 대응

### 리스크/주의사항
- startup-cpu-boost는 추가 비용 없음 (시작 시에만 적용)
- timeout 증가는 요청 타임아웃이며 startup과는 별개 (그러나 일반적으로 권장됨)

## [20:45] 작업 완료

### 결과
- deploy.yml에 `--startup-cpu-boost`와 `--timeout=300` 추가

### 실제 변경 파일
- `.github/workflows/deploy.yml` — Cloud Run 배포 플래그 추가

### 다음 할 일
- main 브랜치에 직접 푸시
- GitHub Actions 배포 결과 확인

---

## [20:47] 추가 수정

### 발견된 문제
- `--startup-cpu-boost` 플래그 이름 오류 → `--cpu-boost`로 수정
- 여전히 배포 실패: 환경 변수 누락 발견
  - `ENCRYPTION_KEY` (required field)
  - `SECRET_KEY`

### 해결
- [x] Cloud Run 플래그 수정: `--cpu-boost`
- [x] GitHub Secrets에 `SECRET_KEY`, `ENCRYPTION_KEY` 추가
- [x] deploy.yml에 환경 변수 추가

### 최종 결과
✅ **배포 성공!** (Run ID: 21670175003)
- 모든 단계 완료
- Cloud Run 서비스 정상 실행

### 교훈
- Cloud Run 배포 실패 시 필수 환경 변수 확인 필요
- 로컬에서 작동해도 프로덕션 환경 변수 설정은 별도로 관리
- 에러 로그만으로는 환경 변수 누락을 파악하기 어려움

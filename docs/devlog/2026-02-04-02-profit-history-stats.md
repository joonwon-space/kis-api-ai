# 2026-02-04 개발 로그 - 수익률 히스토리 및 통계 API

## [20:37] 작업 계획

### 요청 사항
- Issue #13: 수익률 히스토리 관리 및 통계(일/월/연) API 구현
- 일별 자산 스냅샷 저장
- 일간/월간/연간 수익률 통계 제공

### 구현 계획
- [x] **DailyAsset 모델 정의**
  - `app/db/models.py`에 DailyAsset 테이블 추가
  - 필드: user_id, date, total_asset, profit_loss, return_rate, created_at
  - 제약조건: user_id + date unique index (하루에 하나의 스냅샷만)
- [x] **스냅샷 저장 로직 구현**
  - `app/services/asset_snapshot_service.py` 생성
  - 당일 스냅샷이 없으면 현재 자산 상태를 DB에 저장
  - dashboard 조회 시 자동으로 스냅샷 생성
- [x] **통계 API 엔드포인트 구현**
  - `app/api/v1/endpoints/stats.py` 생성
  - `GET /api/v1/stats/daily`: 최근 30일 일별 자산 변동 추이
  - `GET /api/v1/stats/monthly`: 월별 누적 수익금 및 수익률
  - `GET /api/v1/stats/yearly`: 연도별 수익률
- [x] **통계 서비스 구현**
  - `app/services/stats_service.py` 생성
  - 일/월/연 통계 계산 로직
- [x] **Pydantic 스키마 정의**
  - `app/schemas/stats.py` 생성
  - DailyAssetResponse, MonthlyStatResponse, YearlyStatResponse
- [x] **테스트 작성**
  - 가상 데이터로 테스트
  - API 응답 검증

### 예상 변경 파일
- `app/db/models.py` — DailyAsset 모델 추가
- `app/services/asset_snapshot_service.py` — 스냅샷 저장 로직 (신규)
- `app/services/stats_service.py` — 통계 계산 로직 (신규)
- `app/api/v1/endpoints/stats.py` — 통계 API 엔드포인트 (신규)
- `app/schemas/stats.py` — 통계 응답 스키마 (신규)
- `app/main.py` — stats router 추가
- `tests/test_api/test_stats.py` — 테스트 코드 (신규)

### 의사결정
- **스냅샷 생성 시점**: Dashboard 조회 시 자동 생성 (별도 스케줄러 없이)
  - 장점: 간단한 구현, 실제 사용자 활동 시점에 데이터 수집
  - 단점: 사용자가 조회하지 않으면 데이터 누락 (나중에 스케줄러 추가 가능)
- **날짜 기준**: UTC 기준 date 필드 사용
- **초기 자산 기준**: 첫 스냅샷을 기준으로 수익률 계산

### 리스크/주의사항
- 스냅샷 중복 방지 (user_id + date unique constraint)
- 수익률 계산 시 분모가 0인 경우 처리
- 첫 스냅샷이 없는 경우 수익률 계산 불가 (초기 데이터 필요)
- 월별/연별 통계는 일별 데이터를 집계하여 계산

## [23:45] 작업 완료

### 결과
- 수익률 히스토리 및 통계 API 구현 완료
- DailyAsset 모델, 서비스, API 엔드포인트 전체 구현
- 대시보드 조회 시 자동 스냅샷 저장 기능 추가
- 전체 테스트 39개 통과 (신규 6개 포함)

### 실제 변경 파일
- `app/db/models.py` - DailyAsset 모델 추가 (unique index 포함)
- `app/schemas/stats.py` - 통계 응답 스키마 정의
- `app/services/asset_snapshot_service.py` - 스냅샷 CRUD 서비스
- `app/services/stats_service.py` - 일별/월별/연도별 통계 계산
- `app/api/v1/endpoints/stats.py` - 통계 API 엔드포인트
- `app/api/v1/endpoints/dashboard.py` - 자동 스냅샷 저장 추가
- `app/main.py` - stats router 등록
- `tests/test_stats_service.py` - 통계 서비스 테스트

### 계획 대비 변경점
- 없음 (계획대로 구현 완료)
- DashboardSummary 필드가 문자열이라 float 변환 로직 추가
- 스냅샷 저장 실패 시에도 dashboard 응답 정상 반환하도록 예외 처리

### 주요 기술 구현
1. **DailyAsset 모델**: unique constraint (user_id, snapshot_date)
2. **자동 스냅샷**: Dashboard 조회 시 try-except로 안전하게 저장
3. **문자열 → Float 변환**: `float(value.replace(",", ""))`
4. **파생 값 계산**: stock_evaluation, total_purchase_amount
5. **통계 집계**: SQLModel의 `func`를 활용한 GROUP BY 쿼리

### 다음 할 일
- PR 리뷰 및 머지
- 배포 후 API 동작 확인
- Swagger UI에서 통계 API 테스트

### 완료 정보
- **PR**: #19 (https://github.com/joonwon-space/kis-api-ai/pull/19)
- **커밋**: 67eb2f0
- **테스트**: 39개 통과 ✅

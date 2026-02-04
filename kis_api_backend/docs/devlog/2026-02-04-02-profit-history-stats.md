# 2026-02-04 Devlog #2: Profit History & Statistics API

## [작업 시작] Issue #13 구현

### 요청 사항
- 일별/월별/연도별 자산 통계 API 구현
- 대시보드 조회 시 자동 스냅샷 저장
- 수익률 히스토리 데이터 제공

### 구현 계획
- [x] DailyAsset 모델 생성 (user_id, snapshot_date unique constraint)
- [x] AssetSnapshotService 구현 (저장/조회)
- [x] StatsService 구현 (일별/월별/연도별 집계)
- [x] Stats API 엔드포인트 생성 (/stats/daily, /monthly, /yearly)
- [x] Dashboard에 자동 스냅샷 저장 로직 추가
- [x] 테스트 코드 작성

### 변경 파일
- `app/db/models.py` - DailyAsset 모델 추가
- `app/schemas/stats.py` - 통계 응답 스키마 (신규)
- `app/services/asset_snapshot_service.py` - 스냅샷 서비스 (신규)
- `app/services/stats_service.py` - 통계 서비스 (신규)
- `app/api/v1/endpoints/stats.py` - 통계 API (신규)
- `app/api/v1/endpoints/dashboard.py` - 자동 저장 로직 추가
- `app/main.py` - stats router 추가
- `tests/test_stats_service.py` - 테스트 (신규)

### 주요 의사결정

1. **스냅샷 저장 시점**: Dashboard 조회 시 자동 저장
   - 장점: 사용자가 앱을 사용하면 자연스럽게 데이터 축적
   - 중복 저장 방지: get_snapshot으로 기존 데이터 체크

2. **날짜 타입**: `date` 타입 사용 (시간 정보 불필요)
   - 하루에 하나의 스냅샷만 저장
   - unique constraint: (user_id, snapshot_date)

3. **DashboardSummary → DailyAsset 변환**
   - 문자열 필드를 float로 변환 (`replace(",", "")`)
   - 파생 값 계산: stock_evaluation, total_purchase_amount

4. **통계 집계 방식**
   - 일별: DailyAsset 직접 조회
   - 월별: GROUP BY year-month, 집계 계산
   - 연도별: GROUP BY year, 집계 계산

### 리스크/주의사항
- DashboardSummary 필드가 문자열이라 변환 필요
- 스냅샷 저장 실패 시 dashboard 응답은 정상 반환 (logger.warning)
- 월/연도별 통계는 최소 데이터가 있어야 의미 있음

## [작업 완료]

### 결과
- 일별/월별/연도별 통계 API 구현 완료
- 대시보드 조회 시 자동 스냅샷 저장
- 전체 테스트 39개 통과 (신규 6개 포함)

### 실제 변경 내용
1. **DailyAsset 모델**: unique index (user_id, snapshot_date) 추가
2. **AssetSnapshotService**: save/get/get_range/get_latest 메서드
3. **StatsService**: daily/monthly/yearly 통계 집계 로직
4. **Stats API**: JWT 인증 + Query 파라미터 검증
5. **Dashboard 통합**: try-except로 스냅샷 저장 실패 처리
6. **테스트**: 스냅샷 저장/조회, 통계 계산 검증

### 계획 대비 변경점
- 없음 (계획대로 구현 완료)

### 다음 할 일
- PR 생성 및 코드 리뷰
- 머지 후 배포 확인

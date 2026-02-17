# 대기업 채용공고 수집/영구저장 확장 계획 (JobLog)

## 1) 목표
- 네카라쿠배당토직야몰두센 등 국내 주요 IT 기업 채용공고를 한 곳에서 조회 가능하게 통합한다.
- 공고 원문을 변경 이력까지 포함해 영구 저장한다(삭제/마감 이후에도 이력 보존).
- 현재 MVP 구조(FastAPI + Postgres + 스케줄러)를 유지하면서 소스 확장 가능한 구조로 개편한다.

---

## 2) 대상 기업군(초안)
- 네이버, 카카오, 라인/라인플러스
- 쿠팡, 배달의민족(우아한형제들), 당근
- 토스(비바리퍼블리카), 직방, 야놀자
- 몰로코, 두나무, 센드버드

> 운영 시에는 `company_master`에 기업코드/공식 채용 URL을 관리하고, 우선순위 높은 기업부터 단계적으로 연결한다.

---

## 3) 수집 전략 (우선순위)
1. **공식 API/JSON 피드 우선**
   - 안정성/정확성이 높고 파싱 실패율이 낮다.
2. **공식 채용 페이지 HTML 파싱**
   - API 부재 시 CSS selector 기반 추출.
3. **플랫폼 보조 수집(원티드/사람인 등)**
   - 공식 공고 누락 보완 및 중복 검증용.

### 운영 원칙
- 소스별 요청 간격, 타임아웃, 재시도 횟수를 분리 설정한다.
- 실패는 소스 단위로 격리하여 전체 파이프라인 중단을 방지한다.
- robots/이용약관 준수, 과도한 요청 금지, 원문 재배포 범위 검토를 선행한다.

---

## 4) 아키텍처 확장 포인트

### 4-1. Adapter 패턴 도입
- 인터페이스: `SourceAdapter.fetch() -> list[RawJob]`
- 구현체: 기업별 어댑터 (`naver_adapter`, `kakao_adapter` ...)
- 공통 파이프라인:
  1) 수집
  2) 정규화
  3) 중복판정
  4) 저장(원문 + 최신 상태)
  5) 이벤트 기록

### 4-2. 저장 계층 2트랙
- **최신 상태 테이블**: 현재 조회용 (`jobs`)
- **영구 이력 테이블**: 변경 추적/보존용 (`job_snapshots`, `job_events`)

---

## 5) 데이터 모델 확장안

### 5-1. 신규/확장 테이블
- `company_master`
  - `company_code` (unique), `company_name`, `career_url`, `tier`, `is_active`
- `source_targets`
  - `source_code`, `company_code`, `target_url`, `crawl_interval_min`, `parser_type`
- `job_snapshots` (append-only)
  - `job_id`, `snapshot_hash`, `raw_payload_json`, `captured_at`
- `job_events`
  - `job_id`, `event_type(created|updated|closed|reopened)`, `diff_json`, `created_at`

### 5-2. 중복 제거 키 전략
- 1차: `(source_id, source_job_id)`
- 2차: `canonical_url` 정규화
- 3차: `(company_code, normalized_title, posted_date)` 유사도

---

## 6) 분류/검색 확장
- 기존 `employment/role/score` 룰 유지 + 아래 추가
  - `company_group` (네카라쿠배당토직야몰두센)
  - `job_family` (backend/platform/data/ai/devops)
  - `seniority` (intern/new_grad/experienced)
- 검색 필터 확장
  - `company_code`, `company_group`, `is_major_it`, `event_type`, `updated_after`

---

## 7) 실행 단계 (4주 플랜)

## Week 1: 기반 작업
- `company_master`, `source_targets`, `job_snapshots` 마이그레이션
- 어댑터 인터페이스/공통 유틸 추가
- 상위 2개 기업 어댑터 구현

## Week 2: 수집 확장
- 5~6개 기업으로 확장
- 중복 제거/변경 이벤트 기록 안정화
- 실패 재시도/소스별 로그 대시보드

## Week 3: 조회/분류 개선
- 회사군 필터 API 추가
- 분류 룰 확장(`company_group`, `job_family`)
- 프론트 필터(회사군/마감임박/신입 우선) 반영

## Week 4: 운영 안정화
- 백업 자동화(일단위 DB dump + 보관정책)
- 모니터링/알림(수집 실패율, 신규 공고 수 급감 감지)
- 약관/robots 준수 점검 및 요청량 튜닝

---

## 8) API 확장 초안
- `GET /api/v1/jobs?company_code=&company_group=&employment_type=&role_type=`
- `GET /api/v1/jobs/{job_id}/history` (snapshot/event 이력)
- `GET /api/v1/companies` (기업 목록/활성상태)
- `POST /api/v1/admin/crawl/run?company_code=`

---

## 9) 완료 기준 (Definition of Done)
- 주요 기업군 10개 이상 소스 연결
- 하루 2회 이상 자동 수집 + 실패율 5% 이하
- 공고 변경 발생 시 `job_events`와 `job_snapshots`에 이력 누적
- 회사군/신입필터/마감임박 조회가 1초 내 응답(캐시 제외 기준)

---

## 10) 리스크와 대응
- 페이지 구조 변경: selector versioning + 소스별 장애 격리
- 법적 이슈: robots/ToS 점검 체크리스트 + 요청량 제한
- 중복 공고 증가: 3단계 dedupe + 수동 병합 도구 마련
- 운영비 증가: 수집 주기 차등 + 오래된 스냅샷 압축 보관

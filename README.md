# JobLog


## 0) Step 1 구현 상태 (완료)

- FastAPI 엔트리포인트(`app/main.py`) 추가
- 환경설정 로더(`app/core/config.py`) 추가
- SQLAlchemy DB 연결/헬스체크(`app/core/db.py`) 추가
- 헬스 엔드포인트(`GET /api/v1/health`) 추가
- 실행에 필요한 `pyproject.toml`, `.env.example` 추가

### 빠른 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```


## 0-2) Step 2 구현 상태 (완료)

- Alembic 초기 구성 추가 (`alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`)
- 초기 마이그레이션 추가: `20260216_01_step2_core_schema.py`
  - enum 3종: `employment_type_enum`, `role_type_enum`, `run_status_enum`
  - core 테이블 4종: `sources`, `jobs`, `classification_rules`, `job_classifications`
  - 핵심 인덱스/유니크/체크 제약 반영
- seed SQL 추가
  - `app/seeds/sources_seed.sql`
  - `app/seeds/classification_rules_v1.sql`

### 마이그레이션/시드 실행
```bash
alembic upgrade head
psql "$DATABASE_URL" -f app/seeds/sources_seed.sql
psql "$DATABASE_URL" -f app/seeds/classification_rules_v1.sql
```

한국 신입 백엔드 개발자 관점에서 **체험형 인턴 / 채용연계형 인턴 / 신입 / 경력 공고**를 한곳에 모아 보는 개인용 채용 보드 설계 문서입니다.

오늘 안에 바이브코딩으로 MVP를 끝내기 위한 기준으로 작성했습니다.

---

## 1) 목표 (MVP)

- 여러 채용 사이트의 공고를 주기적으로 수집
- 공고를 공통 스키마로 정규화
- 룰 기반으로 고용형태/직무 분류
- 빠르게 필터링 가능한 API 제공
- 개인 서버(Docker Compose)에서 운영

---

## 2) 추천 기술 스택 (Python)

- API: **FastAPI + Uvicorn**
- DB: **PostgreSQL**
- ORM/마이그레이션: **SQLAlchemy + Alembic**
- 배치/스케줄링: **APScheduler** (확장 시 Celery + Redis)
- 배포: **Docker Compose**

---

## 3) 프로젝트 구조 (권장)

```text
joblog/
  app/
    main.py
    core/
      config.py
      db.py
    models/
      source.py
      job.py
      classification.py
      bookmark.py
      application.py
      crawl_run.py
    schemas/
      job.py
      bookmark.py
      application.py
      admin.py
    repositories/
      job_repo.py
      classification_repo.py
      bookmark_repo.py
      application_repo.py
    services/
      crawler/
        base.py
        wanted.py
        saramin.py
      classifier/
        rule_engine.py
      jobs_service.py
      admin_service.py
    api/
      v1/
        jobs.py
        bookmarks.py
        applications.py
        admin.py
    workers/
      scheduler.py
      tasks.py
    seeds/
      sources_seed.sql
      classification_rules_v1.sql
  alembic/
    versions/
  tests/
  docker-compose.yml
  Dockerfile
  pyproject.toml
  .env.example
```

---

## 4) DB 스키마 초안 (PostgreSQL)

아래 핵심 테이블부터 시작합니다.

### 4-1. enum
- `employment_type_enum`: `intern_experience`, `intern_convertible`, `new_grad`, `experienced`, `unknown`
- `role_type_enum`: `backend`, `frontend`, `fullstack`, `data`, `mobile`, `devops`, `unknown`
- `run_status_enum`: `running`, `success`, `partial_fail`, `failed`

### 4-2. 테이블
- `sources`: 수집 소스 메타 정보
- `jobs`: 정규화된 공고 원본
- `job_classifications`: 분류 결과(버전 관리)
- `classification_rules`: 키워드 기반 룰 저장
- `crawl_runs`: 수집 실행 로그
- `job_events`: 공고 변경 이벤트(created/updated/closed/reopened)
- `bookmarks`: 북마크
- `applications`: 지원 상태

### 4-3. 인덱스/제약 핵심
- `jobs(canonical_url)` 유니크
- `jobs(source_id, source_job_id)` 유니크
- `jobs(posted_at, deadline_at, is_active)` 인덱스
- `job_classifications(employment_type, role_type, new_grad_score)` 인덱스

---

## 5) 분류 룰 설계 (키워드/우선순위)

룰 저장 위치: `classification_rules`

컬럼 예시:
- `rule_version` (예: `v1.0.0`)
- `category` (`employment` / `role` / `exclude` / `score`)
- `target_value` (예: `intern_convertible`, `backend`)
- `keyword`
- `match_type` (`contains`, `regex`, `exact`)
- `priority` (작을수록 우선)
- `weight` (점수 가감)
- `is_negation`

### 5-1. 고용형태 우선순위
1. `intern_convertible` (채용연계형)
2. `intern_experience` (체험형)
3. `experienced` (경력)
4. `new_grad` (신입)
5. `unknown`

### 5-2. 대표 키워드
- 채용연계형: `채용연계형`, `정규직 전환`, `전환형 인턴`
- 체험형: `체험형 인턴`, `직무체험`, `현장실습`
- 신입: `신입`, `경력무관`, `졸업예정`
- 경력: `3년 이상`, `경력 n년`
- 백엔드: `백엔드`, `backend`, `server`, `api`, `spring`, `java`, `kotlin`, `django`, `fastapi`, `node`, `go`
- 제외: `디자이너`, `마케터` 등

### 5-3. 신입 적합도 점수 (`new_grad_score`)
- 시작점 50
- `신입 가능`, `경력무관` 같은 문구 가점
- `3년 이상` 같은 문구 감점
- 결과를 0~100으로 클램프

---

## 6) API 명세 (v1)

Base URL: `/api/v1`

### 6-1. Jobs
- `GET /jobs`
  - 필터: `employment_type`, `role_type`, `q`, `posted_from`, `posted_to`, `deadline_before`, `is_active`
  - 정렬: `posted_at_desc`, `deadline_asc`, `score_desc`
  - 페이지: `page`, `size`
- `GET /jobs/today`
  - 오늘 올라온 공고 조회
- `GET /jobs/{job_id}`
  - 상세 + 분류 근거(`matched_keywords`, `reasoning`)

### 6-2. Bookmarks
- `POST /bookmarks`
- `GET /bookmarks`
- `DELETE /bookmarks/{job_id}`

### 6-3. Applications
- `PUT /applications/{job_id}`
- `GET /applications`

### 6-4. Admin
- `POST /admin/crawl/run` (수집 즉시 실행)
- `POST /admin/classify/run` (재분류 실행)
- `GET /admin/runs` (실행 이력)

---

## 7) 구현 순서 (오늘 끝내는 기준)

### Step 1 (1~2시간)
- FastAPI 프로젝트 뼈대 생성
- DB 연결 및 Alembic 초기화

### Step 2 (2~3시간)
- enum + `sources`, `jobs`, `classification_rules`, `job_classifications` 마이그레이션
- seed SQL 작성

### Step 3 (2~3시간)
- `GET /jobs`, `GET /jobs/{job_id}`, `GET /jobs/today` 구현
- 기본 필터/정렬/페이지네이션 구현

### Step 4 (2~3시간)
- 수집기 1개 연결(가장 쉬운 소스부터)
- `crawl_runs` 기록

### Step 5 (2시간)
- 룰 엔진 구현(키워드 매칭 + 우선순위 + 점수)
- `job_classifications` 저장

### Step 6 (1~2시간)
- 북마크/지원 상태 API
- Docker Compose로 로컬 배포

---

## 8) 운영 체크리스트

- 실패 재시도/타임아웃/소스별 격리
- 일 2~4회 스케줄 수집
- DB 백업(cron)
- 간단 알림(webhook)
- 룰 버전(`rule_version`) 고정 운영

---

## 9) 비기능 요구사항 (MVP 수준)

- 응답시간: `/jobs` P95 500ms 이내(인덱스 기준)
- 안정성: 특정 소스 실패 시 전체 배치 중단 금지
- 추적성: 분류 결과에 `matched_keywords`, `rule_version` 저장
- 중복제거: URL 유니크 + 소스 내부 ID 유니크

---

## 10) 다음 작업 TODO

- [ ] Alembic 리비전 1차 생성 (enum + core tables)
- [ ] seed SQL 분리 (`sources`, `classification_rules_v1`)
- [ ] Job 조회 API 3종 구현
- [ ] crawler 1개 사이트 연결
- [ ] rule_engine v1 적용
- [ ] docker-compose up까지 확인

---

이 문서는 “방향 제시” 목적의 설계 초안입니다. 구현 시 사이트별 이용약관/robots 정책을 확인해서 수집 정책을 조정하세요.

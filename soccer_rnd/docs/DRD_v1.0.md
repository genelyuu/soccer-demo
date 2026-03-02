# Database Design Review Document (DRD) v1.0

## 훈련·웰니스·HRV 스키마 확장에 대한 데이터베이스 설계 리뷰

---

### 문서 정보

| 항목 | 내용 |
|------|------|
| **문서 ID** | DRD-2026-001 |
| **버전** | 1.0 |
| **작성일** | 2026-02-11 |
| **최종 수정** | 2026-02-11 |
| **작성** | DB Architecture팀 (DBA), Data Engineering팀 (DE) |
| **검토 대상** | `00003_training_wellness_schema.sql`, `00004_etl_views.sql`, `seed.sql` 확장부 |
| **관련 프로젝트** | `soccer` (서비스 MVP), `soccer_rnd` (R&D 분석 파이프라인) |
| **배포 범위** | 사내 전체 (개발팀, PM, 보안팀) |

---

### 문서 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|:----:|------|--------|-----------|
| 0.1 | 2026-02-11 | DE | db_bug_report.md 초안 작성 |
| 1.0 | 2026-02-11 | DBA + DE | 공동 리뷰 결과 통합, 수정 SQL 확정, 마이그레이션 계획 수립 |

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [리뷰 범위 및 방법론](#2-리뷰-범위-및-방법론)
3. [현행 아키텍처 개요](#3-현행-아키텍처-개요)
4. [심각도 분류 기준](#4-심각도-분류-기준)
5. [발견 사항 총괄](#5-발견-사항-총괄)
6. [상세 분석 — P0 치명적 결함](#6-상세-분석--p0-치명적-결함)
7. [상세 분석 — P1 비즈니스 로직 오류](#7-상세-분석--p1-비즈니스-로직-오류)
8. [상세 분석 — P2 구조적 비효율](#8-상세-분석--p2-구조적-비효율)
9. [상세 분석 — P3 컨벤션·문서화](#9-상세-분석--p3-컨벤션문서화)
10. [횡단 관심사 분석](#10-횡단-관심사-분석)
11. [긍정적 평가](#11-긍정적-평가)
12. [수정 마이그레이션 계획](#12-수정-마이그레이션-계획)
13. [리스크 매트릭스](#13-리스크-매트릭스)
14. [권고 사항 및 후속 조치](#14-권고-사항-및-후속-조치)
15. [부록](#15-부록)

---

## 1. Executive Summary

### 1.1 리뷰 배경

`soccer` 서비스 MVP(PostgreSQL/Supabase)에 훈련·웰니스·HRV 데이터 수집 체계를 확장하여, `soccer_rnd` R&D 분석 파이프라인(ACWR, Monotony, 혼합효과모형, LOSO CV)과 통합하는 PoV 데이터베이스가 설계되었다. 본 리뷰는 해당 스키마의 정합성, 성능, 보안, 운영 안정성을 종합 평가한다.

### 1.2 핵심 결론

| 구분 | 수치 |
|------|:----:|
| 총 발견 사항 | **19건** |
| P0 치명 | **2건** |
| P1 높음 | **4건** |
| P2 중간 | **8건** |
| P3 낮음 | **5건** |

**P0 2건은 운영 환경 적용 시 즉각적인 장애를 유발**하며, 수정 마이그레이션(`00005`) 없이는 프로덕션 배포가 불가하다. P1 4건은 분석 결과 왜곡 또는 핵심 기능 차단을 유발하여 PoV 목적 달성에 직접적 장애가 된다.

### 1.3 즉시 조치 필요 사항

| 순위 | ID | 제목 | 예상 공수 |
|:----:|:--:|------|:---------:|
| 1 | B-01 | UNIQUE 제약이 훈련 세션을 사용자당 1개로 제한 | 0.5h |
| 2 | B-04 | ETL 뷰에서 REST일 누락 → ACWR 전체 왜곡 | 0.5h |
| 3 | B-02 | user_id 이중 저장 → 데이터 불일치 가능 | 2h |
| 4 | B-05 | RLS 정책이 코치의 선수 데이터 조회를 차단 | 3h |

---

## 2. 리뷰 범위 및 방법론

### 2.1 리뷰 대상

| 파일 | 위치 | 내용 |
|------|------|------|
| `00003_training_wellness_schema.sql` | `soccer/supabase/migrations/` | ENUM 5종, 테이블 8개, RLS 정책 16개, 인덱스 9개 |
| `00004_etl_views.sql` | `soccer/supabase/migrations/` | ETL 뷰 2개 (`v_rnd_track_a`, `v_rnd_track_b`) |
| `seed.sql` (확장부) | `soccer/supabase/` | 신규 10명 사용자, 15명 프로필 |
| `generate_seed_data.py` | `soccer_rnd/scripts/` | 합성 데이터 생성 (15명 × 120일) |
| `export_seed_sql.py` | `soccer_rnd/scripts/` | DataFrame → INSERT SQL 변환 |

### 2.2 참조 문서

| 문서 | 역할 |
|------|------|
| `00001_initial_schema.sql` | 기존 스키마 컨벤션 기준 |
| `00002_rls_write_policies.sql` | 기존 RLS 패턴 기준 |
| `docs/data_migration.md` | 설계 의도 및 DDL 원안 |
| `docs/DECISIONS.md` | ADR-001 ~ ADR-011 |
| `CLAUDE.md` | 품질 기준 (재현성, 추적성, reviewer-safe 톤) |

### 2.3 리뷰 방법론

| 단계 | 방법 | 관점 |
|------|------|------|
| 1. 정적 DDL 분석 | SQL 구문·제약·인덱스 구조 검증 | DBA |
| 2. 정규화 검증 | 3NF 위반, 갱신 이상, 삽입 이상 점검 | DBA |
| 3. 도메인 정합성 | R&D 파이프라인 입출력 스키마와의 호환성 검증 | DE |
| 4. ETL 흐름 검증 | 뷰 → 파이프라인 → 모형 적합 end-to-end 추적 | DE |
| 5. 보안 감사 | RLS 정책, 암호화 요건, 권한 범위 검토 | DBA |
| 6. 성능 예측 | 예상 데이터 볼륨 기반 인덱스·TOAST 효율 평가 | DBA + DE |
| 7. 기존 컨벤션 대조 | 00001/00002 마이그레이션과의 패턴 일관성 검증 | DBA |

---

## 3. 현행 아키텍처 개요

### 3.1 테이블 인벤토리

| # | 테이블 | 마이그레이션 | 예상 행 수 | FK 의존 | 핵심 제약 |
|:-:|--------|:-----------:|:----------:|---------|-----------|
| 1 | `users` | 00001 | 15 | — | PK, UNIQUE(email) |
| 2 | `teams` | 00001 | 1 | → users | PK |
| 3 | `team_members` | 00001 | 15 | → teams, users | UNIQUE(team_id, user_id) |
| 4 | `matches` | 00001 | 2 | → teams, users | PK |
| 5 | `attendances` | 00001 | 10 | → matches, users | UNIQUE(match_id, user_id) |
| 6 | `record_rooms` | 00001 | 0 | → matches | UNIQUE(match_id) |
| 7 | `match_records` | 00001 | 0 | → record_rooms, users | UNIQUE(room_id, user_id) |
| 8 | `user_profiles` | **00003** | 15 | → users | UNIQUE(user_id) |
| 9 | `training_sessions` | **00003** | ~1,800 | → users, teams, matches | **UNIQUE NULLS NOT DISTINCT** (B-01) |
| 10 | `pre_session_wellness` | **00003** | ~1,300 | → sessions, users | UNIQUE(session_id), GENERATED(hooper_index) |
| 11 | `post_session_feedback` | **00003** | ~1,300 | → sessions, users | UNIQUE(session_id) |
| 12 | `next_day_reviews` | **00003** | ~1,300 | → sessions, users | UNIQUE(session_id) |
| 13 | `computed_load_metrics` | **00003** | ~1,800 | → users | UNIQUE(user_id, metric_date) |
| 14 | `hrv_measurements` | **00003** | ~1,800 | → users, sessions | GENERATED(rr_count) |
| 15 | `daily_hrv_metrics` | **00003** | ~1,800 | → users, hrv_measurements | UNIQUE(user_id, metric_date) |

### 3.2 ENUM 타입 인벤토리

| ENUM | 값 목록 | 사용 테이블 |
|------|---------|-------------|
| `team_role` (00001) | ADMIN, MANAGER, MEMBER, GUEST | team_members |
| `match_status` (00001) | OPEN, CONFIRMED, COMPLETED, CANCELLED | matches |
| `attendance_status` (00001) | PENDING, ACCEPTED, DECLINED, MAYBE | attendances |
| `record_room_status` (00001) | OPEN, CLOSED | record_rooms |
| `session_type` (00003) | TRAINING, MATCH, REST, OTHER | training_sessions |
| `post_condition` (00003) | VERY_BAD, BAD, NEUTRAL, GOOD, VERY_GOOD | post_session_feedback |
| `next_day_condition` (00003) | WORSE, SAME, BETTER | next_day_reviews |
| `hrv_source` (00003) | CHEST_STRAP, SMARTWATCH, FINGER_SENSOR, APP_MANUAL, EXTERNAL_IMPORT | hrv_measurements |
| `hrv_context` (00003) | MORNING_REST, PRE_SESSION, POST_SESSION, DURING_SESSION, NIGHT_SLEEP, OTHER | hrv_measurements |

### 3.3 ETL 뷰 인벤토리

| 뷰 | 마이그레이션 | 소스 테이블 | 대상 파이프라인 |
|----|:-----------:|-------------|-----------------|
| `v_rnd_track_b` | 00004 | training_sessions + pre/post/next_day | R&D 트랙 B (부하 + 웰니스) |
| `v_rnd_track_a` | 00004 | daily_hrv_metrics + computed_load_metrics | R&D 트랙 A (HRV + 부하) |

### 3.4 데이터 흐름도

```
[서비스 입력]                    [DB 테이블]                     [ETL 뷰]              [R&D 파이프라인]

사용자 앱 ──→ training_sessions ──┐
            pre_session_wellness ─┤
            post_session_feedback ┤──→ v_rnd_track_b ──→ load_seed_track_b()
            next_day_reviews ─────┘                       → compute_daily_load_metrics()
                                                          → lag_correlation_table()
                                                          → fit_random_intercept()
                                                          → loso_cv()

웨어러블 ──→ hrv_measurements ──→ daily_hrv_metrics ─┐
            computed_load_metrics ────────────────────┤──→ v_rnd_track_a ──→ load_seed_track_a()
                                                                            → fit_random_intercept()
```

---

## 4. 심각도 분류 기준

| 등급 | 명칭 | 정의 | SLA |
|:----:|------|------|:---:|
| **P0** | 치명 | 데이터 손실, INSERT 실패, 무결성 파괴. 운영 환경 적용 즉시 장애. | 수정 마이그레이션 없이 배포 금지 |
| **P1** | 높음 | 비즈니스 로직 오류, 분석 결과 왜곡, 핵심 기능 차단. | PoV 데모 전 수정 필수 |
| **P2** | 중간 | 구조적 비효율, 유지보수 비용 증가, 기술 부채. | 다음 마이그레이션(00006)에서 처리 |
| **P3** | 낮음 | 컨벤션 불일치, 문서-구현 괴리, 가독성 저하. | 백로그 등록 후 순차 처리 |

---

## 5. 발견 사항 총괄

### 5.1 심각도별 분포

```
P0 치명  ████████████████████████████████████  2건  (10.5%)
P1 높음  ████████████████████████████████████████████████████████████████████████  4건  (21.1%)
P2 중간  ████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████  8건  (42.1%)
P3 낮음  ██████████████████████████████████████████████████████████████████████████████████████  5건  (26.3%)
```

### 5.2 분류별 분포

| 분류 | 건수 | 해당 ID |
|------|:----:|---------|
| 무결성·제약 | 2 | B-01, B-02 |
| 비즈니스 로직·의미론 | 2 | B-04, B-06 |
| 보안·RLS | 3 | B-05, B-18, B-19 |
| 정규화·모델링 | 4 | B-03, B-07, B-08, B-10 |
| 추적성 | 1 | B-09 |
| 성능·인덱스 | 3 | B-11, B-12, B-13 |
| 운영 | 1 | B-14 |
| 컨벤션·명명 | 3 | B-15, B-16, B-17 |

### 5.3 전체 발견 사항 목록

| ID | 심각도 | 분류 | 제목 | 대상 | 수정 난이도 |
|:--:|:------:|------|------|------|:----------:|
| B-01 | **P0** | 무결성 | NULLS NOT DISTINCT — 훈련 세션 사용자당 1개 제한 | 00003 L61 | 낮음 |
| B-02 | **P0** | 무결성 | user_id 이중 저장 — 크로스 사용자 불일치 가능 | 00003 L81,110,135 | 중간 |
| B-03 | **P1** | 정규화 | has_* 플래그 — 트리거 없는 파생 데이터 동기화 불능 | 00003 L54-56 | 중간 |
| B-04 | **P1** | 의미론 | v_rnd_track_b에서 REST일 제외 → ACWR 산출 왜곡 | 00004 L42 | 낮음 |
| B-05 | **P1** | 보안 | RLS "본인만" — 코치/매니저의 선수 데이터 조회 불가 | 00003 전체 RLS | 중간 |
| B-06 | **P1** | 도메인 | session_rpe CHECK 1~10 — CR-10의 0 누락 | 00003 L112 | 낮음 |
| B-07 | **P2** | 정규화 | user_profiles 1:1 분리 — JOIN 비용 대비 실익 부족 | 00003 L18-31 | 중간 |
| B-08 | **P2** | 정규화 | Surrogate Key 남용 — 3개 테이블에 불필요한 id UUID | 00003 L79,107,132 | 중간 |
| B-09 | **P2** | 추적성 | computed_load_metrics — 산출 파라미터·버전·이력 없음 | 00003 L156-180 | 중간 |
| B-10 | **P2** | 모델링 | daily_hrv_metrics.measurement_id — 대표 측정 선택 기준 부재 | 00003 L230 | 낮음 |
| B-11 | **P2** | 성능 | rr_intervals_ms FLOAT[] — 배열 크기 제한 없음 | 00003 L203 | 낮음 |
| B-12 | **P2** | 성능 | ETL 뷰 ORDER BY — SQL 표준상 보장 없는 무의미한 정렬 | 00004 L43,73 | 낮음 |
| B-13 | **P2** | 성능 | session_date 단독 인덱스 누락 — 날짜 범위 쿼리 비효율 | 00003 L64 | 낮음 |
| B-14 | **P2** | 운영 | updated_at 자동 갱신 트리거 부재 | 00003 L30,58 | 낮음 |
| B-15 | **P3** | 컨벤션 | ENUM vs CHECK 혼재 — 값 제한 패턴 불통일 | 00003 L9,23 | 낮음 |
| B-16 | **P3** | 컨벤션 | strain vs strain_value — R&D 파이프라인과 명명 불일치 | 00003 L170 | 낮음 |
| B-17 | **P3** | 컨벤션 | soreness vs doms — 동일 개념 이름 분기 | 00003 L84 | 낮음 |
| B-18 | **P3** | 보안 | phone TEXT 평문 — data_migration.md 암호화 요건 미반영 | 00003 L22 | 중간 |
| B-19 | **P3** | 보안 | computed_load_metrics UPDATE 정책 없음 — 배치 갱신 불가 | 00003 L184-188 | 낮음 |

---

## 6. 상세 분석 — P0 치명적 결함

### 6.1 B-01: NULLS NOT DISTINCT — 훈련 세션 사용자당 1개 제한

#### 현황

| 항목 | 내용 |
|------|------|
| **위치** | `00003_training_wellness_schema.sql` Line 61 |
| **현재 DDL** | `UNIQUE NULLS NOT DISTINCT (user_id, match_id)` |
| **설계 의도** | 동일 사용자가 같은 경기(match)에 중복 세션을 생성하는 것을 방지 |

#### 문제 분석

`NULLS NOT DISTINCT`(PostgreSQL 15+)는 UNIQUE 제약에서 NULL 값을 동등하게 취급한다. 따라서 `(user_id='A', match_id=NULL)` 쌍이 테이블 전체에서 **최대 1건**만 허용된다.

TRAINING, REST, OTHER 타입의 세션은 모두 `match_id = NULL`이므로, **한 사용자가 경기 외 세션을 전체 기간 통틀어 단 1개만 생성 가능**하다.

```
-- 기대 동작: 120일 × 6일/주 ≈ 약 103개 훈련 세션 INSERT 가능
-- 실제 동작: 두 번째 INSERT부터 unique_violation 발생

INSERT INTO training_sessions (user_id, session_type, session_date)
VALUES ('user_A', 'TRAINING', '2025-09-01');  -- 성공

INSERT INTO training_sessions (user_id, session_type, session_date)
VALUES ('user_A', 'TRAINING', '2025-09-02');  -- 실패! (user_A, NULL) 중복
```

#### 영향 범위

| 영향 대상 | 세부 내용 |
|-----------|-----------|
| training_sessions | 15명 × ~103일(경기 제외) = ~1,545행이 필요하나 15행만 삽입 가능 |
| 하위 3개 테이블 | session 부재로 wellness/feedback/review도 생성 불가 |
| computed_load_metrics | 부하 지표 산출 데이터 부족 |
| ETL 뷰 | 거의 빈 결과 반환 |
| R&D 파이프라인 전체 | ACWR/Monotony/혼합효과모형 실행 불가 |

#### 미발견 원인

합성 데이터 생성(`generate_seed_data.py`)이 **CSV 직접 생성** 방식이라 PostgreSQL 제약을 거치지 않았다. `export_seed_sql.py`의 INSERT를 실제 DB에 실행하면 즉시 발견된다.

#### 수정안 (DBA + DE 합의)

```sql
-- 00005_fix_critical.sql

-- B-01: UNIQUE NULLS NOT DISTINCT 제거 → Partial Unique Index로 교체
ALTER TABLE training_sessions DROP CONSTRAINT IF EXISTS training_sessions_user_id_match_id_key;

CREATE UNIQUE INDEX idx_sessions_user_match
  ON training_sessions(user_id, match_id)
  WHERE match_id IS NOT NULL;
```

**설계 원칙**: "같은 경기에 대한 중복 세션 방지"와 "다수 훈련 세션 허용"을 **분리된 제약**으로 처리한다. Partial Unique Index는 `match_id IS NOT NULL`인 행에만 유일성을 강제하므로, `match_id = NULL`인 훈련/휴식 세션은 자유롭게 생성 가능하다.

#### 검증 방법

```sql
-- 동일 사용자로 match_id=NULL 행 2개 INSERT 성공 확인
INSERT INTO training_sessions (user_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001', 'TRAINING', '2025-09-01');
INSERT INTO training_sessions (user_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001', 'TRAINING', '2025-09-02');
-- 두 행 모두 성공해야 함

-- 동일 경기에 대한 중복은 여전히 차단
INSERT INTO training_sessions (user_id, match_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 'MATCH', '2026-02-15');
INSERT INTO training_sessions (user_id, match_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 'MATCH', '2026-02-15');
-- 두 번째 INSERT에서 unique_violation 발생해야 함
```

---

### 6.2 B-02: user_id 이중 저장 — 크로스 사용자 불일치 가능

#### 현황

| 항목 | 내용 |
|------|------|
| **위치** | `00003` Line 81, 110, 135 |
| **해당 테이블** | `pre_session_wellness`, `post_session_feedback`, `next_day_reviews` |
| **현재 DDL** | 세 테이블 모두 `session_id FK` + `user_id FK` 동시 보유 |

#### 문제 분석

`session_id`를 통해 `training_sessions.user_id`를 JOIN으로 파생할 수 있으므로, 하위 테이블의 `user_id`는 **비정규화된 파생 데이터**이다.

```
training_sessions.user_id = 'A'
         │
         ↓ (session_id FK)
pre_session_wellness.user_id = 'B'   ← DB가 허용함 (무결성 위반)
```

두 `user_id`의 일치를 강제하는 **CHECK 제약, 트리거, 복합 FK가 없으므로**, 다음 시나리오가 가능하다:

| 시나리오 | 발생 조건 | 결과 |
|----------|-----------|------|
| 크로스 사용자 삽입 | 사용자 B가 사용자 A의 session에 `user_id='B'`로 wellness INSERT | DB 수용, 논리적 오류 |
| RLS 우회 | RLS가 `user_id = auth.uid()`이므로, B가 A의 세션에 자신의 데이터를 연결 가능 | 보안 위반 |
| R&D 집계 왜곡 | `GROUP BY user_id` 시 세션 소유자와 웰니스 작성자가 불일치 | 분석 왜곡 |

#### 수정안 비교 (DBA + DE 토론 결과)

| 방안 | 접근 | 장점 | 단점 |
|:----:|------|------|------|
| **A (정규화)** | `user_id` 컬럼 제거, RLS를 JOIN 기반으로 전환 | 근본 해결, 불일치 원천 차단 | RLS 서브쿼리 추가 |
| **B (트리거)** | `BEFORE INSERT` 트리거로 session.user_id와 일치 검증 | 기존 구조 유지 | 트리거 유지보수 비용 |
| **C (복합 FK)** | `(session_id, user_id)` 복합 FK → sessions의 `(id, user_id)` | DB 레벨 강제 | sessions에 UNIQUE(id, user_id) 추가 필요 |

#### 합의 결론: 방안 A (정규화) 채택

```sql
-- 00005_fix_critical.sql

-- B-02-a: pre_session_wellness에서 user_id 제거
ALTER TABLE pre_session_wellness DROP COLUMN user_id;

-- B-02-b: RLS 정책 재작성 (session 경유)
DROP POLICY IF EXISTS "pre_wellness_read_own" ON pre_session_wellness;
DROP POLICY IF EXISTS "pre_wellness_insert_own" ON pre_session_wellness;
DROP POLICY IF EXISTS "pre_wellness_update_own" ON pre_session_wellness;

CREATE POLICY "pre_wellness_read_own" ON pre_session_wellness FOR SELECT
  USING (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));
CREATE POLICY "pre_wellness_insert_own" ON pre_session_wellness FOR INSERT
  WITH CHECK (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));
CREATE POLICY "pre_wellness_update_own" ON pre_session_wellness FOR UPDATE
  USING (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));

-- post_session_feedback, next_day_reviews에도 동일 적용 (생략)
```

**성능 영향 평가** (DBA): `session_id`에 UNIQUE 인덱스가 존재하므로 서브쿼리는 Index Unique Scan → O(1). Supabase 인증 컨텍스트에서 `auth.uid()` 호출 1회 + UNIQUE 조회 1회로 기존 `user_id = auth.uid()` 직접 비교와 실측 차이 무시 가능.

---

## 7. 상세 분석 — P1 비즈니스 로직 오류

### 7.1 B-03: has_* 플래그 — 트리거 없는 파생 데이터

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L54-56 |
| **컬럼** | `has_pre_wellness`, `has_post_feedback`, `has_next_day_review` |
| **근본 문제** | 하위 테이블의 행 존재 여부를 나타내는 파생 데이터인데, INSERT/DELETE 시 자동 갱신 메커니즘이 없음 |

| 상태 | 플래그 값 | 실제 상태 | 불일치 |
|------|:---------:|:---------:|:------:|
| wellness INSERT 성공, 플래그 UPDATE 실패 | FALSE | 행 존재 | 불일치 |
| wellness DELETE 후, 플래그 UPDATE 누락 | TRUE | 행 없음 | 불일치 |
| 트랜잭션 부분 실패 | 불확정 | 불확정 | 불확정 |

**DBA 의견**: 플래그 3개를 제거하고, 조회 시 `EXISTS` 서브쿼리를 사용하는 것이 데이터 정합성을 구조적으로 보장하는 유일한 방법이다. UNIQUE 인덱스 덕에 `EXISTS` 비용은 O(1)이며, 푸시 알림 판별에도 동일하게 사용 가능하다.

**DE 의견**: R&D 파이프라인은 하위 테이블을 직접 JOIN하므로 플래그에 의존하지 않는다. 서비스 측 UI가 플래그에 의존하는 경우에만 마이그레이션 영향이 있다.

```sql
-- 00005 수정안
ALTER TABLE training_sessions
  DROP COLUMN has_pre_wellness,
  DROP COLUMN has_post_feedback,
  DROP COLUMN has_next_day_review;
```

---

### 7.2 B-04: v_rnd_track_b에서 REST일 제외 → ACWR 왜곡

| 항목 | 내용 |
|------|------|
| **위치** | `00004_etl_views.sql` L42 |
| **현재 조건** | `WHERE ps.session_rpe IS NOT NULL` |
| **문제** | REST 세션은 `post_session_feedback` 행이 없으므로 `ps.session_rpe IS NULL` → 뷰에서 완전히 제외 |

#### ACWR 왜곡 시뮬레이션

```
실제 7일 부하 시퀀스: [500, 400, 450, 0, 500, 600, 0]   (일=REST=0)
올바른 ATL = mean = 350.0

REST 누락 시 시퀀스:  [500, 400, 450, 500, 600]          (5일만 포함)
왜곡된 ATL = mean = 490.0                                 (+40% 과대추정)
```

`data_migration.md` 5.2절에도 명시: "session_type='REST', sRPE=0 (의도적 0, 결측 아님)".

```sql
-- 00005 수정안: v_rnd_track_b 재정의
CREATE OR REPLACE VIEW v_rnd_track_b AS
SELECT
  ts.user_id::text AS athlete_id,
  ts.session_date AS date,
  ps.session_rpe AS rpe,
  ts.duration_min,
  COALESCE(ps.session_rpe * ts.duration_min, 0) AS srpe,
  pw.fatigue,
  pw.stress,
  pw.soreness AS doms,
  pw.sleep,
  pw.hooper_index,
  ts.session_type::text AS session_type,
  CASE WHEN ts.match_id IS NOT NULL THEN TRUE ELSE FALSE END AS match_day,
  CASE nd.condition
    WHEN 'WORSE'  THEN 3
    WHEN 'SAME'   THEN 2
    WHEN 'BETTER' THEN 1
    ELSE NULL
  END AS next_day_score
FROM training_sessions ts
LEFT JOIN pre_session_wellness pw ON pw.session_id = ts.id
LEFT JOIN post_session_feedback ps ON ps.session_id = ts.id
LEFT JOIN next_day_reviews nd ON nd.session_id = ts.id
WHERE ps.session_rpe IS NOT NULL
   OR ts.session_type = 'REST';
```

---

### 7.3 B-05: RLS "본인만" 정책 — 팀 기능 차단

| 항목 | 내용 |
|------|------|
| **기존 패턴 (00001)** | `matches_read_team`: "같은 팀이면 조회 가능" |
| **신규 패턴 (00003)** | `sessions_read_own`: "본인만 조회 가능" |
| **불일치** | 8개 신규 테이블 전부가 기존 팀 기반 패턴과 충돌 |

| 역할 | 기존 테이블 조회 | 신규 테이블 조회 | 기대 동작 |
|------|:----------------:|:----------------:|:---------:|
| ADMIN (코치) | 같은 팀 전체 | 본인만 | 같은 팀 전체 |
| MANAGER | 같은 팀 전체 | 본인만 | 같은 팀 전체 |
| MEMBER (선수) | 같은 팀 전체 | 본인만 | 본인만 |

**DE 의견**: 팀 수준 부하 모니터링은 PoV의 핵심 시연 기능이다. 코치가 선수의 ACWR 추이를 볼 수 없으면 대시보드 구현이 불가능하다.

**DBA 의견**: 하위 테이블(wellness, feedback 등)에 `team_id`가 없으므로, `training_sessions.team_id`를 경유하는 서브쿼리가 필요하다. RLS 서브쿼리 성능은 `idx_sessions_team` 인덱스로 보장된다.

```sql
-- training_sessions 수정안 (B-02 정규화 적용 후 기준)
DROP POLICY IF EXISTS "sessions_read_own" ON training_sessions;
CREATE POLICY "sessions_read_own_or_team" ON training_sessions FOR SELECT
  USING (
    user_id = auth.uid()
    OR team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid()
        AND role IN ('ADMIN', 'MANAGER')
    )
  );

-- 하위 테이블 예시 (pre_session_wellness, B-02 user_id 제거 후)
DROP POLICY IF EXISTS "pre_wellness_read_own" ON pre_session_wellness;
CREATE POLICY "pre_wellness_read_own_or_team" ON pre_session_wellness FOR SELECT
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE user_id = auth.uid()
       OR team_id IN (
         SELECT team_id FROM team_members
         WHERE user_id = auth.uid()
           AND role IN ('ADMIN', 'MANAGER')
       )
  ));
```

---

### 7.4 B-06: session_rpe CHECK 범위 — CR-10 스케일의 0 누락

| 항목 | 내용 |
|------|------|
| **현재** | `CHECK (session_rpe BETWEEN 1 AND 10)` |
| **Borg CR-10 정의** | 0 = Nothing at all, 1 = Very, very easy, ..., 10 = Maximal |
| **참조** | Foster et al. (2001), "A New Approach to Monitoring Exercise Training" |
| **영향** | "참석했으나 거의 활동 없음"(RPE=0)을 기록 불가. sRPE=0×duration을 표현 불가. |

```sql
-- 00005 수정안
ALTER TABLE post_session_feedback
  DROP CONSTRAINT IF EXISTS post_session_feedback_session_rpe_check;
ALTER TABLE post_session_feedback
  ADD CONSTRAINT post_session_feedback_session_rpe_check
  CHECK (session_rpe BETWEEN 0 AND 10);
```

---

## 8. 상세 분석 — P2 구조적 비효율

### 8.1 종합 비교표

| ID | 제목 | 현상 | 영향 | 수정 방향 |
|:--:|------|------|------|-----------|
| B-07 | user_profiles 1:1 분리 | users와 1:1, phone+position 두 컬럼만 보유 | 매 조회마다 LEFT JOIN 필요 | users에 컬럼 추가 또는 ADR로 분리 근거 문서화 |
| B-08 | Surrogate Key 남용 | 3개 테이블에 `id UUID PK` + `session_id UNIQUE` | 인덱스 2개 유지, FK 참조 혼란 | `session_id`를 PK로 승격 (Supabase 호환 확인 후) |
| B-09 | 산출 파라미터 미기록 | ACWR window, EWMA span 등 추적 불가 | 재산출 시 이전 결과 비교 불가, 추적성 위반 | `pipeline_version TEXT`, `params JSONB` 추가 |
| B-10 | 대표 측정 선택 기준 부재 | 일별 HRV 1행인데 하루 다수 측정 가능 | 구현자마다 다른 기준 적용 위험 | `COMMENT ON COLUMN` 또는 `selection_rule` 컬럼 |
| B-11 | 배열 크기 제한 없음 | FLOAT[] 무제한 | NIGHT_SLEEP 8시간 = ~240KB/행 | `CHECK (array_length(...) BETWEEN 1 AND 50000)` |
| B-12 | 뷰 ORDER BY | SQL 표준상 보장 없음 | 무의미한 정렬 비용, 잘못된 기대 | ORDER BY 제거 |
| B-13 | session_date 단독 인덱스 누락 | 복합 인덱스만 존재 | 날짜 범위 쿼리 비효율 | 단독 인덱스 추가 |
| B-14 | updated_at 트리거 부재 | UPDATE 시 갱신 안 됨 | 변경 이력 추적 불가 | 공용 트리거 함수 + 테이블별 트리거 |

### 8.2 B-09 상세: computed_load_metrics 추적성 위반

**CLAUDE.md 품질 기준**: "모든 지표/그림/표는 산출 코드 위치와 파라미터를 역추적 가능"

현재 `computed_load_metrics`는 다음을 기록하지 않는다:

| 누락 정보 | 추적 불가 질문 |
|-----------|----------------|
| ATL window (7? 14?) | "이 ACWR은 어떤 window로 산출한 건가?" |
| EWMA span (7? 10?) | "EWMA 파라미터가 바뀌었는가?" |
| pipeline 버전 | "언제, 어떤 코드로 산출했는가?" |
| 이전 값 | "재산출 전후 차이가 얼마인가?" |

**수정안 (최소)**:

```sql
ALTER TABLE computed_load_metrics
  ADD COLUMN pipeline_version TEXT DEFAULT 'v1.0',
  ADD COLUMN params JSONB DEFAULT '{"atl_window": 7, "ctl_window": 28, "ewma_atl_span": 7, "ewma_ctl_span": 28}'::jsonb;
```

---

## 9. 상세 분석 — P3 컨벤션·문서화

### 9.1 종합 비교표

| ID | 제목 | 현상 | 수정 방향 |
|:--:|------|------|-----------|
| B-15 | ENUM vs CHECK 혼재 | session_type=ENUM, position=CHECK. 판단 기준 부재. | ADR 추가: 값 변경 가능성 기준으로 패턴 선택 |
| B-16 | strain vs strain_value | R&D `strain`, DB `strain_value`. ETL 매핑 누락. | DB 컬럼명을 `strain`으로 통일 |
| B-17 | soreness vs doms | 서비스 `soreness`, R&D `doms`. 뷰에서 alias 변환. | DATA_SCHEMA_MAPPING.md에 매핑 명시 또는 컬럼명 통일 |
| B-18 | phone 평문 | data_migration.md에 AES-256 요건. DDL은 TEXT 평문. | pgcrypto 도입 또는 COMMENT ON COLUMN 경고 |
| B-19 | UPDATE 정책 없음 | computed_load_metrics에 INSERT만. 배치 UPSERT 불가. | UPDATE 정책 추가 또는 service_role 전제 문서화 |

### 9.2 B-15 상세: ENUM vs CHECK 기준안

DBA와 DE의 토론 결과 다음 기준을 제안한다:

| 기준 | ENUM 적합 | CHECK IN 적합 |
|------|-----------|---------------|
| 값의 변경 빈도 | 거의 변경 없음 (상태 머신) | 향후 추가/변경 가능 |
| 값의 의미론 | 상태 전이가 명확 | 단순 열거형 목록 |
| PostgreSQL 제약 | ADD VALUE 가능, 삭제 불가 | 자유로운 변경 |
| **적용 예** | session_type, match_status | position (포지션 신설 가능) |

이 기준을 ADR-012로 `docs/DECISIONS.md`에 추가할 것을 권장한다.

### 9.3 B-16/B-17 상세: 명명 매핑 전략

| 서비스 측 (DB) | R&D 측 (Python) | ETL 뷰 변환 | 권장 |
|----------------|-----------------|:-----------:|------|
| `soreness` | `doms` | `pw.soreness AS doms` | 서비스: `soreness` 유지, 매핑 문서화 |
| `strain_value` | `strain` | 변환 없음 (누락) | **DB 컬럼명을 `strain`으로 변경** |
| `hooper_index` | `hooper_index` | 동일 | 변경 불필요 |

---

## 10. 횡단 관심사 분석

### 10.1 정규화 수준 평가

| 테이블 | 정규형 | 위반 사항 |
|--------|:------:|-----------|
| user_profiles | 3NF | B-07: 1:1 분리 정당성 미문서화 |
| training_sessions | 2NF | B-03: has_* 파생 플래그 (1NF 위반은 아니나 갱신 이상 유발) |
| pre_session_wellness | **비정규** | B-02: user_id 이중 저장 (이행적 종속 위반) |
| post_session_feedback | **비정규** | B-02: 동일 |
| next_day_reviews | **비정규** | B-02: 동일 |
| computed_load_metrics | 3NF | B-09: 추적성 컬럼 부족 (정규화 자체는 문제 없음) |
| hrv_measurements | 1NF | B-11: FLOAT[] 크기 제한 없음 (1NF 경계 논쟁) |
| daily_hrv_metrics | 3NF | B-10: 선택 기준 미문서화 |

### 10.2 RLS 일관성 매트릭스

| 테이블 | SELECT | INSERT | UPDATE | DELETE | 패턴 |
|--------|:------:|:------:|:------:|:------:|:----:|
| users (00001) | 본인 | 본인 | 본인 | — | 본인 |
| teams (00001) | 팀 멤버 | 인증 | ADMIN | ADMIN | 역할 기반 |
| matches (00001) | 팀 멤버 | ADMIN/MGR | ADMIN/MGR | ADMIN | 역할 기반 |
| **training_sessions** (00003) | **본인** | **본인** | **본인** | — | **본인** (B-05) |
| **pre_session_wellness** (00003) | **본인** | **본인** | **본인** | — | **본인** (B-05) |
| **computed_load_metrics** (00003) | **본인** | **본인** | **없음** | — | **불완전** (B-19) |

**패턴 불일치**: 기존 테이블은 역할 기반 계층적 접근, 신규 테이블은 단순 본인 제한. 팀 스포츠의 코치 역할이 반영되지 않았다.

### 10.3 인덱스 커버리지 분석

| 쿼리 패턴 | 필요 인덱스 | 현재 상태 |
|-----------|-------------|:---------:|
| 사용자별 세션 조회 (일반) | `(user_id, session_date)` | 있음 |
| 날짜 범위 세션 조회 (ETL 배치) | `(session_date)` | **없음** (B-13) |
| 팀별 세션 조회 (대시보드) | `(team_id)` | 있음 |
| 사용자별 부하 지표 (시계열) | `(user_id, metric_date DESC)` | 있음 |
| 사용자별 HRV (시계열) | `(user_id, metric_date DESC)` | 있음 |
| HRV 측정 → 세션 연결 | `(session_id)` | 있음 |

### 10.4 CASCADE 체인 위험도

```
users 삭제 시 CASCADE 전파 경로:

users
  ├─ user_profiles (CASCADE)
  ├─ training_sessions (CASCADE)
  │   ├─ pre_session_wellness (CASCADE)
  │   ├─ post_session_feedback (CASCADE)
  │   ├─ next_day_reviews (CASCADE)
  │   └─ hrv_measurements (SET NULL: session_id)
  ├─ computed_load_metrics (CASCADE)
  ├─ hrv_measurements (CASCADE: user_id)
  └─ daily_hrv_metrics (CASCADE)
```

**위험**: 사용자 1명 삭제 시 최대 ~1,000행 이상이 CASCADE 삭제된다. 의도된 동작이나, **soft delete 미도입** 상태에서 실수로 삭제 시 복구 불가.

---

## 11. 긍정적 평가

비판과 함께, 현재 설계에서 적절하게 구현된 부분도 기록한다.

| 항목 | 평가 | 근거 |
|------|------|------|
| **GENERATED STORED 활용** | 우수 | `hooper_index`, `rr_count`를 DB 레벨에서 자동 산출. 애플리케이션 산출 부담 제거, 일관성 보장. |
| **ON DELETE CASCADE 일관 적용** | 우수 | 부모 삭제 시 고아 행 방지. FK 체인 전체에 적용됨. |
| **UNIQUE 제약으로 멱등성** | 우수 | `UNIQUE(user_id, metric_date)` 등으로 중복 삽입 방지. UPSERT 패턴 기반 지원. |
| **ETL 뷰 분리** | 우수 | 서비스 스키마 ↔ R&D 스키마 변환을 뷰로 캡슐화. 양측 독립 진화 가능. |
| **ENUM 상태 제한** | 양호 | 자유 텍스트 대비 입력 오류 방지, 인덱스 효율 향상. |
| **시드 ON CONFLICT DO NOTHING** | 양호 | 멱등 시드 — 반복 실행 안전. |
| **3단계 입력 구조** | 양호 | 훈련 전→후→다음날의 시계열 흐름을 테이블 분리로 구조화. R&D lag 분석과 자연스럽게 정합. |
| **HRV 원시 배열 저장** | 양호 | RR 간격을 FLOAT[]로 저장하여, R&D `filter_rr_outliers()` → `rmssd()`/`sdnn()` 파이프라인과 직접 호환. |

---

## 12. 수정 마이그레이션 계획

### 12.1 마이그레이션 파일 구성

모든 수정을 **`00005_schema_fixes.sql`** 단일 파일로 통합한다.

| 순서 | 대상 | 수정 내용 | 관련 ID |
|:----:|------|-----------|:-------:|
| 1 | training_sessions | UNIQUE 제약 제거 → Partial Index 교체 | B-01 |
| 2 | training_sessions | has_* 플래그 3개 DROP | B-03 |
| 3 | pre_session_wellness | user_id DROP + RLS 재작성 | B-02, B-05 |
| 4 | post_session_feedback | user_id DROP + RLS 재작성 + CHECK 수정 | B-02, B-05, B-06 |
| 5 | next_day_reviews | user_id DROP + RLS 재작성 | B-02, B-05 |
| 6 | training_sessions | RLS 팀 기반 확장 | B-05 |
| 7 | computed_load_metrics | strain_value → strain, UPDATE 정책 추가, 추적성 컬럼 | B-16, B-19, B-09 |
| 8 | hrv_measurements | FLOAT[] CHECK 추가 | B-11 |
| 9 | training_sessions | session_date 단독 인덱스 추가 | B-13 |
| 10 | v_rnd_track_b | REST일 포함하도록 재정의 | B-04 |
| 11 | v_rnd_track_a/b | ORDER BY 제거 | B-12 |
| 12 | 공용 트리거 | updated_at 자동 갱신 | B-14 |

### 12.2 수정 SQL 전문

```sql
-- =================================================================
-- 00005_schema_fixes.sql
-- DRD v1.0 기반 수정 마이그레이션
-- 의존: 00003, 00004 적용 후 실행
-- =================================================================

-- -----------------------------------------------------------------
-- [B-01] UNIQUE NULLS NOT DISTINCT → Partial Unique Index
-- -----------------------------------------------------------------
ALTER TABLE training_sessions
  DROP CONSTRAINT IF EXISTS training_sessions_user_id_match_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_user_match
  ON training_sessions(user_id, match_id)
  WHERE match_id IS NOT NULL;

-- -----------------------------------------------------------------
-- [B-03] has_* 파생 플래그 제거
-- -----------------------------------------------------------------
ALTER TABLE training_sessions
  DROP COLUMN IF EXISTS has_pre_wellness,
  DROP COLUMN IF EXISTS has_post_feedback,
  DROP COLUMN IF EXISTS has_next_day_review;

-- -----------------------------------------------------------------
-- [B-02] user_id 이중 저장 제거 (3개 테이블)
-- -----------------------------------------------------------------
ALTER TABLE pre_session_wellness DROP COLUMN IF EXISTS user_id;
ALTER TABLE post_session_feedback DROP COLUMN IF EXISTS user_id;
ALTER TABLE next_day_reviews DROP COLUMN IF EXISTS user_id;

-- -----------------------------------------------------------------
-- [B-05] RLS 정책 재작성 — 팀 기반 + 본인
-- -----------------------------------------------------------------

-- training_sessions
DROP POLICY IF EXISTS "sessions_read_own" ON training_sessions;
DROP POLICY IF EXISTS "sessions_insert_own" ON training_sessions;
DROP POLICY IF EXISTS "sessions_update_own" ON training_sessions;

CREATE POLICY "sessions_read_own_or_team" ON training_sessions FOR SELECT
  USING (
    user_id = auth.uid()
    OR team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role IN ('ADMIN', 'MANAGER')
    )
  );
CREATE POLICY "sessions_insert_own" ON training_sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "sessions_update_own" ON training_sessions FOR UPDATE
  USING (user_id = auth.uid());

-- pre_session_wellness (user_id 제거 후, session 경유)
DROP POLICY IF EXISTS "pre_wellness_read_own" ON pre_session_wellness;
DROP POLICY IF EXISTS "pre_wellness_insert_own" ON pre_session_wellness;
DROP POLICY IF EXISTS "pre_wellness_update_own" ON pre_session_wellness;

CREATE POLICY "pre_wellness_read_own_or_team" ON pre_session_wellness FOR SELECT
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE user_id = auth.uid()
       OR team_id IN (
         SELECT team_id FROM team_members
         WHERE user_id = auth.uid() AND role IN ('ADMIN', 'MANAGER')
       )
  ));
CREATE POLICY "pre_wellness_insert_own" ON pre_session_wellness FOR INSERT
  WITH CHECK (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));
CREATE POLICY "pre_wellness_update_own" ON pre_session_wellness FOR UPDATE
  USING (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));

-- post_session_feedback (동일 패턴)
DROP POLICY IF EXISTS "post_feedback_read_own" ON post_session_feedback;
DROP POLICY IF EXISTS "post_feedback_insert_own" ON post_session_feedback;
DROP POLICY IF EXISTS "post_feedback_update_own" ON post_session_feedback;

CREATE POLICY "post_feedback_read_own_or_team" ON post_session_feedback FOR SELECT
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE user_id = auth.uid()
       OR team_id IN (
         SELECT team_id FROM team_members
         WHERE user_id = auth.uid() AND role IN ('ADMIN', 'MANAGER')
       )
  ));
CREATE POLICY "post_feedback_insert_own" ON post_session_feedback FOR INSERT
  WITH CHECK (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));
CREATE POLICY "post_feedback_update_own" ON post_session_feedback FOR UPDATE
  USING (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));

-- next_day_reviews (동일 패턴)
DROP POLICY IF EXISTS "next_day_read_own" ON next_day_reviews;
DROP POLICY IF EXISTS "next_day_insert_own" ON next_day_reviews;
DROP POLICY IF EXISTS "next_day_update_own" ON next_day_reviews;

CREATE POLICY "next_day_read_own_or_team" ON next_day_reviews FOR SELECT
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE user_id = auth.uid()
       OR team_id IN (
         SELECT team_id FROM team_members
         WHERE user_id = auth.uid() AND role IN ('ADMIN', 'MANAGER')
       )
  ));
CREATE POLICY "next_day_insert_own" ON next_day_reviews FOR INSERT
  WITH CHECK (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));
CREATE POLICY "next_day_update_own" ON next_day_reviews FOR UPDATE
  USING (session_id IN (
    SELECT id FROM training_sessions WHERE user_id = auth.uid()
  ));

-- computed_load_metrics (팀 기반 SELECT + UPDATE 추가)
DROP POLICY IF EXISTS "metrics_read_own" ON computed_load_metrics;

CREATE POLICY "metrics_read_own_or_team" ON computed_load_metrics FOR SELECT
  USING (
    user_id = auth.uid()
    OR user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role IN ('ADMIN', 'MANAGER')
    )
  );
CREATE POLICY "metrics_update_own" ON computed_load_metrics FOR UPDATE
  USING (user_id = auth.uid());

-- hrv_measurements (팀 기반 SELECT)
DROP POLICY IF EXISTS "hrv_read_own" ON hrv_measurements;

CREATE POLICY "hrv_read_own_or_team" ON hrv_measurements FOR SELECT
  USING (
    user_id = auth.uid()
    OR user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role IN ('ADMIN', 'MANAGER')
    )
  );

-- daily_hrv_metrics (팀 기반 SELECT)
DROP POLICY IF EXISTS "daily_hrv_read_own" ON daily_hrv_metrics;

CREATE POLICY "daily_hrv_read_own_or_team" ON daily_hrv_metrics FOR SELECT
  USING (
    user_id = auth.uid()
    OR user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role IN ('ADMIN', 'MANAGER')
    )
  );

-- -----------------------------------------------------------------
-- [B-06] session_rpe CHECK 범위 수정 (0~10)
-- -----------------------------------------------------------------
ALTER TABLE post_session_feedback
  DROP CONSTRAINT IF EXISTS post_session_feedback_session_rpe_check;
ALTER TABLE post_session_feedback
  ADD CONSTRAINT post_session_feedback_session_rpe_check
  CHECK (session_rpe BETWEEN 0 AND 10);

-- -----------------------------------------------------------------
-- [B-09, B-16] computed_load_metrics 추적성 + 명명 수정
-- -----------------------------------------------------------------
ALTER TABLE computed_load_metrics
  RENAME COLUMN strain_value TO strain;
ALTER TABLE computed_load_metrics
  ADD COLUMN IF NOT EXISTS pipeline_version TEXT DEFAULT 'v1.0',
  ADD COLUMN IF NOT EXISTS params JSONB DEFAULT '{
    "atl_window": 7, "ctl_window": 28,
    "ewma_atl_span": 7, "ewma_ctl_span": 28
  }'::jsonb;

-- -----------------------------------------------------------------
-- [B-11] rr_intervals_ms 배열 크기 제한
-- -----------------------------------------------------------------
ALTER TABLE hrv_measurements
  ADD CONSTRAINT hrv_rr_array_size
  CHECK (array_length(rr_intervals_ms, 1) BETWEEN 1 AND 50000);

-- -----------------------------------------------------------------
-- [B-13] session_date 단독 인덱스 추가
-- -----------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sessions_date
  ON training_sessions(session_date);

-- -----------------------------------------------------------------
-- [B-04, B-12] ETL 뷰 재정의 (REST 포함 + ORDER BY 제거)
-- -----------------------------------------------------------------
CREATE OR REPLACE VIEW v_rnd_track_b AS
SELECT
  ts.user_id::text AS athlete_id,
  ts.session_date AS date,
  ps.session_rpe AS rpe,
  ts.duration_min,
  COALESCE(ps.session_rpe * ts.duration_min, 0) AS srpe,
  pw.fatigue,
  pw.stress,
  pw.soreness AS doms,
  pw.sleep,
  pw.hooper_index,
  ts.session_type::text AS session_type,
  CASE WHEN ts.match_id IS NOT NULL THEN TRUE ELSE FALSE END AS match_day,
  CASE nd.condition
    WHEN 'WORSE'  THEN 3
    WHEN 'SAME'   THEN 2
    WHEN 'BETTER' THEN 1
    ELSE NULL
  END AS next_day_score
FROM training_sessions ts
LEFT JOIN pre_session_wellness pw ON pw.session_id = ts.id
LEFT JOIN post_session_feedback ps ON ps.session_id = ts.id
LEFT JOIN next_day_reviews nd ON nd.session_id = ts.id
WHERE ps.session_rpe IS NOT NULL
   OR ts.session_type = 'REST';

CREATE OR REPLACE VIEW v_rnd_track_a AS
SELECT
  h.user_id::text AS subject_id,
  h.metric_date AS date,
  h.rmssd,
  h.sdnn,
  h.ln_rmssd,
  h.ln_rmssd_7d,
  h.mean_hr,
  h.nn_count,
  m.acwr_rolling,
  m.acwr_ewma,
  m.monotony,
  m.daily_load AS srpe
FROM daily_hrv_metrics h
LEFT JOIN computed_load_metrics m
  ON m.user_id = h.user_id AND m.metric_date = h.metric_date
WHERE h.valid = TRUE;

-- -----------------------------------------------------------------
-- [B-14] updated_at 자동 갱신 트리거
-- -----------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_user_profiles_updated
  BEFORE UPDATE ON user_profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_sessions_updated
  BEFORE UPDATE ON training_sessions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 12.3 마이그레이션 실행 체크리스트

| # | 단계 | 검증 |
|:-:|------|------|
| 1 | 로컬 DB에 00001~00004 순차 적용 | 에러 없이 완료 |
| 2 | seed.sql 실행 | 15명 사용자, 15 프로필, 15 팀멤버 |
| 3 | 00005_schema_fixes.sql 적용 | 에러 없이 완료 |
| 4 | export_seed_sql.py의 INSERT 실행 | ~1,800 세션 삽입 성공 (B-01 수정 확인) |
| 5 | 크로스 사용자 삽입 시도 | RLS 차단 확인 (B-02 수정 확인) |
| 6 | ADMIN 역할로 타 선수 데이터 조회 | 조회 성공 확인 (B-05 수정 확인) |
| 7 | v_rnd_track_b에서 REST 행 존재 확인 | session_type='REST', srpe=0 (B-04 수정 확인) |
| 8 | RPE=0 INSERT 시도 | 성공 확인 (B-06 수정 확인) |

---

## 13. 리스크 매트릭스

### 13.1 수정 전 리스크

| ID | 발생 가능성 | 영향도 | 리스크 수준 | 비고 |
|:--:|:----------:|:------:|:----------:|------|
| B-01 | **확실** | **치명** | **극심** | 실제 DB 적용 시 100% 발현 |
| B-02 | 중간 | 높음 | **높음** | 악의적 입력 또는 클라이언트 버그 시 |
| B-04 | **확실** | 높음 | **높음** | ETL 뷰 사용 시 100% 발현 |
| B-05 | **확실** | 중간 | **높음** | 코치 대시보드 구현 시 100% 발현 |
| B-03 | 중간 | 중간 | 중간 | 트랜잭션 부분 실패 시 |
| B-06 | 낮음 | 낮음 | 낮음 | RPE=0 입력 빈도 낮음 |
| B-11 | 낮음 | 중간 | 중간 | NIGHT_SLEEP 대량 데이터 유입 시 |

### 13.2 수정 후 잔여 리스크

| 영역 | 잔여 리스크 | 대응 |
|------|-------------|------|
| CASCADE 삭제 | 사용자 삭제 시 대량 행 소실 | soft delete 도입 검토 (다음 마이그레이션) |
| RLS 서브쿼리 성능 | 팀 규모 확대 시 team_members 스캔 증가 | materialized 역할 뷰 또는 캐싱 검토 |
| phone 평문 | 개인정보 보호 | pgcrypto 또는 앱 레벨 암호화 (B-18, P3) |
| Surrogate Key | 불필요한 인덱스 유지 | Supabase 호환성 확인 후 처리 (B-08, P2) |

---

## 14. 권고 사항 및 후속 조치

### 14.1 즉시 조치 (00005 마이그레이션)

| # | 조치 | 담당 | 기한 |
|:-:|------|:----:|:----:|
| 1 | 00005_schema_fixes.sql 작성 및 로컬 검증 | DBA | 즉시 |
| 2 | export_seed_sql.py에서 user_id 제거 반영 (B-02) | DE | 즉시 |
| 3 | generate_seed_data.py에서 REST일 sRPE=0 명시 검증 (B-04) | DE | 즉시 |
| 4 | 기존 87개 + 신규 12개 테스트 통과 재확인 | DE | 즉시 |

### 14.2 단기 조치 (다음 스프린트)

| # | 조치 | 담당 |
|:-:|------|:----:|
| 1 | ADR-012 (ENUM vs CHECK 기준) 작성 | DBA + DE |
| 2 | DATA_SCHEMA_MAPPING.md에 soreness↔doms 매핑 명시 | DE |
| 3 | user_profiles 분리 정당성 ADR 또는 users 병합 결정 | DBA |
| 4 | Surrogate Key 정책 결정 (Supabase id 컨벤션 확인) | DBA |

### 14.3 중기 조치 (다음 마이그레이션)

| # | 조치 | 담당 |
|:-:|------|:----:|
| 1 | soft delete 패턴 도입 검토 (CASCADE 위험 완화) | DBA |
| 2 | phone 암호화 구현 (pgcrypto 또는 앱 레벨) | DBA + 보안 |
| 3 | computed_load_metrics 이력 테이블 설계 | DE |
| 4 | daily_hrv_metrics 대표 측정 선택 규칙 문서화 | DE |

---

## 15. 부록

### 15.1 용어 정의

| 용어 | 정의 |
|------|------|
| **ACWR** | Acute:Chronic Workload Ratio. ATL/CTL. |
| **ATL** | Acute Training Load. 7일 평균 부하. |
| **CTL** | Chronic Training Load. 28일 평균 부하. |
| **sRPE** | Session Rating of Perceived Exertion. RPE × 운동 시간(분). |
| **Hooper Index** | fatigue + soreness + stress + sleep (4~28). |
| **Monotony** | 7일 부하 평균 / 표준편차. 단조성 지표. |
| **Strain** | 주간 총 부하 × Monotony. |
| **rMSSD** | Root Mean Square of Successive Differences. HRV 시간 영역 지표. |
| **SDNN** | Standard Deviation of NN intervals. |
| **RLS** | Row Level Security. PostgreSQL 행 수준 보안. |
| **LOSO** | Leave-One-Subject-Out. 교차 검증 방식. |
| **Partial Unique Index** | WHERE 조건부 유일성 인덱스. |
| **GENERATED STORED** | PostgreSQL 생성 컬럼 (저장형). |
| **TOAST** | The Oversized-Attribute Storage Technique. PostgreSQL 대형 값 저장. |

### 15.2 참조 문서

| 문서 | 경로 |
|------|------|
| 초기 스키마 | `soccer/supabase/migrations/00001_initial_schema.sql` |
| RLS 정책 | `soccer/supabase/migrations/00002_rls_write_policies.sql` |
| 훈련·웰니스 스키마 | `soccer/supabase/migrations/00003_training_wellness_schema.sql` |
| ETL 뷰 | `soccer/supabase/migrations/00004_etl_views.sql` |
| 시드 데이터 | `soccer/supabase/seed.sql` |
| 통합 설계서 | `soccer_rnd/docs/data_migration.md` |
| 아키텍처 결정 | `soccer_rnd/docs/DECISIONS.md` (ADR-001 ~ ADR-011) |
| 버그 리포트 원본 | `soccer_rnd/docs/db_bug_report.md` |
| 품질 기준 | `soccer_rnd/CLAUDE.md` |
| 스키마 매핑 | `soccer_rnd/docs/DATA_SCHEMA_MAPPING.md` |
| 지표 수식 | `soccer_rnd/docs/METRICS_FORMULAS.md` |

### 15.3 관련 ADR

| ADR | 제목 | DRD 관련 항목 |
|-----|------|:------------:|
| ADR-004 | 결측 처리 원칙 | B-04 (REST일 sRPE=0) |
| ADR-007 | 합성 데모 데이터 전략 | B-01 (CSV 방식으로 미발견) |
| ADR-012 (신규 제안) | ENUM vs CHECK 기준 | B-15 |

---

*본 문서는 DB Architecture팀과 Data Engineering팀의 공동 리뷰 결과를 기록한다. 00005 수정 마이그레이션 적용 전까지 00003/00004의 프로덕션 배포를 보류할 것을 권고한다.*

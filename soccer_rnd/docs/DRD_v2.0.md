# Database Design Review Document (DRD) v2.0

## 훈련·웰니스·HRV 스키마 확장에 대한 데이터베이스 설계 리뷰

---

### 문서 정보

| 항목 | 내용 |
|------|------|
| **문서 ID** | DRD-2026-001 |
| **버전** | 2.0 |
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
| **2.0** | **2026-02-11** | **DBA + DE** | **신규 6건 발견(B-20~B-25), data_migration.md 컴플라이언스 감사, ER 다이어그램, 성능 모델링, 롤백 절차 추가, 00005 SQL 트랜잭션 안전성 강화** |

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [리뷰 범위 및 방법론](#2-리뷰-범위-및-방법론)
3. [현행 아키텍처 개요](#3-현행-아키텍처-개요)
4. [data_migration.md 컴플라이언스 감사](#4-data_migrationmd-컴플라이언스-감사)
5. [심각도 분류 기준](#5-심각도-분류-기준)
6. [발견 사항 총괄](#6-발견-사항-총괄)
7. [상세 분석 — P0 치명적 결함](#7-상세-분석--p0-치명적-결함)
8. [상세 분석 — P1 비즈니스 로직 오류](#8-상세-분석--p1-비즈니스-로직-오류)
9. [상세 분석 — P2 구조적 비효율](#9-상세-분석--p2-구조적-비효율)
10. [상세 분석 — P3 컨벤션·문서화](#10-상세-분석--p3-컨벤션문서화)
11. [횡단 관심사 분석](#11-횡단-관심사-분석)
12. [성능 모델링](#12-성능-모델링)
13. [긍정적 평가](#13-긍정적-평가)
14. [수정 마이그레이션 계획](#14-수정-마이그레이션-계획)
15. [롤백 절차](#15-롤백-절차)
16. [리스크 매트릭스](#16-리스크-매트릭스)
17. [검증 매트릭스 및 테스트 전략](#17-검증-매트릭스-및-테스트-전략)
18. [권고 사항 및 후속 조치](#18-권고-사항-및-후속-조치)
19. [부록](#19-부록)

---

## 1. Executive Summary

### 1.1 리뷰 배경

`soccer` 서비스 MVP(PostgreSQL 15+ / Supabase)에 훈련·웰니스·HRV 데이터 수집 체계를 확장하여, `soccer_rnd` R&D 분석 파이프라인(ACWR, Monotony, 혼합효과모형, LOSO CV)과 통합하는 PoV 데이터베이스가 설계되었다. 본 DRD v2.0은 v1.0의 19건 발견사항에 추가로 **6건의 신규 결함을 식별**하고, `data_migration.md` 원안 대비 구현 차이를 체계적으로 감사하며, 성능 모델링과 롤백 절차를 보강한 종합 리뷰이다.

### 1.2 핵심 결론

| 구분 | v1.0 | **v2.0** | 변동 |
|------|:----:|:--------:|:----:|
| 총 발견 사항 | 19건 | **25건** | +6 |
| P0 치명 | 2건 | **2건** | — |
| P1 높음 | 4건 | **5건** | +1 |
| P2 중간 | 8건 | **10건** | +2 |
| P3 낮음 | 5건 | **8건** | +3 |

**P0 2건은 운영 환경 적용 시 즉각적인 장애를 유발**하며, 수정 마이그레이션(`00005`) 없이는 프로덕션 배포가 불가하다. v2.0에서 새로 식별된 **B-20(ETL 익명화 미구현)**은 P1로서, 프로덕션 전환 시 개인정보 보호법 위반 위험을 수반한다.

### 1.3 v2.0 신규 발견 사항 요약

| ID | 심각도 | 제목 | 핵심 영향 |
|:--:|:------:|------|-----------|
| B-20 | **P1** | ETL 뷰 익명화 미구현 | data_migration.md SHA-256 요건 미충족, 개인정보 노출 |
| B-21 | **P2** | DELETE 정책 전면 부재 | 사용자 데이터 삭제권(GDPR/개인정보보호법) 미보장 |
| B-22 | **P2** | computed_load_metrics 사장 컬럼 | dcwr/tsb/hooper 3컬럼이 ETL 미노출, 사장 데이터화 |
| B-23 | **P3** | hrv_measurements FK CASCADE 불일치 | 세션 삭제 시 HRV만 고아 행으로 잔류 |
| B-24 | **P3** | v_rnd_track_a strain 미노출 | Monotony-Strain 복합 분석 불가 |
| B-25 | **P3** | daily_hrv_metrics.valid DEFAULT 부재 | 미지정 시 NULL → WHERE valid=TRUE에서 자동 제외 |

### 1.4 즉시 조치 필요 사항 (갱신)

| 순위 | ID | 제목 | 예상 공수 |
|:----:|:--:|------|:---------:|
| 1 | B-01 | UNIQUE 제약이 훈련 세션을 사용자당 1개로 제한 | 0.5h |
| 2 | B-04 | ETL 뷰에서 REST일 누락 → ACWR 전체 왜곡 | 0.5h |
| 3 | B-02 | user_id 이중 저장 → 데이터 불일치 가능 | 2h |
| 4 | B-05 | RLS 정책이 코치의 선수 데이터 조회를 차단 | 3h |
| 5 | B-20 | ETL 뷰 익명화 미구현 (프로덕션 전환 필수) | 2h |

---

## 2. 리뷰 범위 및 방법론

### 2.1 리뷰 대상

| 파일 | 위치 | 내용 | 라인 수 |
|------|------|------|:-------:|
| `00003_training_wellness_schema.sql` | `soccer/supabase/migrations/` | ENUM 5종, 테이블 8개, RLS 정책 16개, 인덱스 9개 | 257 |
| `00004_etl_views.sql` | `soccer/supabase/migrations/` | ETL 뷰 2개 (`v_rnd_track_a`, `v_rnd_track_b`) | 74 |
| `seed.sql` (확장부) | `soccer/supabase/` | 신규 10명 사용자, 15명 프로필 | 103 |
| `generate_seed_data.py` | `soccer_rnd/scripts/` | 합성 데이터 생성 (15명 × 120일) | ~450 |
| `export_seed_sql.py` | `soccer_rnd/scripts/` | DataFrame → INSERT SQL 변환 | 291 |

### 2.2 참조 문서

| 문서 | 역할 | v2.0 활용 |
|------|------|-----------|
| `00001_initial_schema.sql` | 기존 스키마 컨벤션 기준 | RLS 패턴 비교, FK 전략 대조 |
| `00002_rls_write_policies.sql` | 기존 RLS 패턴 기준 | 역할 기반 정책 참조, DELETE 정책 존재 확인 |
| `docs/data_migration.md` | 설계 의도 및 DDL 원안 | **v2.0 컴플라이언스 감사 기준** |
| `docs/DECISIONS.md` | ADR-001 ~ ADR-011 | 지표 정의·결측 처리 근거 |
| `CLAUDE.md` | 품질 기준 | 재현성·추적성 검증 기준 |

### 2.3 리뷰 방법론 (v2.0 확장)

| 단계 | 방법 | 관점 | v2.0 추가 |
|------|------|------|:---------:|
| 1. 정적 DDL 분석 | SQL 구문·제약·인덱스 구조 검증 | DBA | — |
| 2. 정규화 검증 | 3NF 위반, 갱신 이상, 삽입 이상 점검 | DBA | — |
| 3. 도메인 정합성 | R&D 파이프라인 입출력 스키마와의 호환성 검증 | DE | — |
| 4. ETL 흐름 검증 | 뷰 → 파이프라인 → 모형 적합 end-to-end 추적 | DE | — |
| 5. 보안 감사 | RLS 정책, 암호화 요건, 권한 범위 검토 | DBA | — |
| 6. 성능 예측 | 예상 데이터 볼륨 기반 인덱스·TOAST 효율 평가 | DBA + DE | — |
| 7. 기존 컨벤션 대조 | 00001/00002 마이그레이션과의 패턴 일관성 검증 | DBA | — |
| **8. 설계서 컴플라이언스** | **data_migration.md 원안 대비 구현 차이 체계 감사** | **DBA + DE** | **신규** |
| **9. 성능 모델링** | **예상 데이터 볼륨별 쿼리 비용 추정, TOAST 분석** | **DBA** | **신규** |
| **10. 롤백 영향 분석** | **수정 마이그레이션 실패 시 복구 경로 검증** | **DBA** | **신규** |
| **11. 데이터 리니지 추적** | **입력 → DB → ETL → R&D 전 경로 컬럼 매핑** | **DE** | **신규** |

---

## 3. 현행 아키텍처 개요

### 3.1 ER 다이어그램

```
┌─────────────────┐
│     users        │ (00001)
│─────────────────│
│ id UUID PK       │
│ email UNIQUE     │
│ name, avatar_url │
│ created_at       │
│ updated_at       │
└────────┬────────┘
         │
    ┌────┼─────────────────────────────────────────────────────────────────┐
    │    │                                                                 │
    │    │ 1:1                     1:N                                     │
    ▼    ▼                         ▼                                       │
┌──────────────┐  ┌───────────────────────────────┐                        │
│user_profiles │  │   training_sessions            │ (00003)               │
│──────────────│  │───────────────────────────────│                        │
│id UUID PK    │  │id UUID PK                     │                        │
│user_id FK UQ │  │user_id FK → users             │                        │
│phone TEXT    │  │team_id FK → teams              │                        │
│position CHECK│  │match_id FK → matches (NULL OK) │                        │
│created_at    │  │session_type ENUM               │                        │
│updated_at    │  │session_date DATE               │                        │
└──────────────┘  │duration_min FLOAT              │                        │
                  │has_pre/post/next_day BOOL ⚠B-03│                        │
                  │UNIQUE(user,match) ⚠B-01        │                        │
                  └───┬──────────┬──────────┬──────┘                        │
                      │          │          │                               │
          ┌───────────┘  ┌───────┘  ┌───────┘                               │
          ▼ 1:1          ▼ 1:1      ▼ 1:1                                   │
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐              │
│pre_session_      │ │post_session_     │ │next_day_         │              │
│wellness          │ │feedback          │ │reviews           │              │
│──────────────────│ │──────────────────│ │──────────────────│              │
│id UUID PK        │ │id UUID PK        │ │id UUID PK        │              │
│session_id FK UQ  │ │session_id FK UQ  │ │session_id FK UQ  │              │
│user_id FK ⚠B-02  │ │user_id FK ⚠B-02  │ │user_id FK ⚠B-02  │              │
│fatigue [1-7]     │ │session_rpe [1-10]│ │condition ENUM    │              │
│soreness [1-7]    │ │  ⚠B-06 (0 누락)  │ │ (WORSE/SAME/     │              │
│stress [1-7]      │ │condition ENUM    │ │  BETTER)         │              │
│sleep [1-7]       │ │memo TEXT         │ │memo TEXT         │              │
│hooper_index GEN  │ └──────────────────┘ └──────────────────┘              │
└──────────────────┘                                                        │
                                                                            │
    ┌───────────────────────────────────────────────────────────────────────┘
    │         1:N                          1:N
    ▼                                      ▼
┌───────────────────────┐  ┌───────────────────────────┐
│ hrv_measurements      │  │ computed_load_metrics      │
│───────────────────────│  │───────────────────────────│
│ id UUID PK            │  │ id UUID PK                │
│ user_id FK → users    │  │ user_id FK → users        │
│ session_id FK → sess  │  │ metric_date DATE          │
│   ⚠ON DELETE SET NULL │  │ UNIQUE(user,date)         │
│   ⚠B-23 (불일치)      │  │ daily_load, atl/ctl/acwr  │
│ source ENUM           │  │ monotony, strain_value    │
│ context ENUM          │  │   ⚠B-16 (strain 불일치)   │
│ rr_intervals_ms []    │  │ dcwr, tsb, hooper ⚠B-22   │
│   ⚠B-11 (크기무제한)  │  │ pipeline_ver 없음 ⚠B-09   │
│ rr_count GENERATED    │  │ UPDATE 정책 없음 ⚠B-19    │
│ quality_flag          │  └───────────────────────────┘
└───────────┬───────────┘
            │ N:1 (measurement_id)
            ▼
┌───────────────────────┐
│ daily_hrv_metrics     │
│───────────────────────│
│ id UUID PK            │
│ user_id FK → users    │
│ measurement_id FK     │
│   ⚠B-10 (선택기준?)   │
│ metric_date DATE      │
│ UNIQUE(user,date)     │
│ rmssd, sdnn           │
│ ln_rmssd, ln_rmssd_7d │
│ valid BOOLEAN         │
│   ⚠B-25 (DEFAULT 없음)│
└───────────────────────┘

[ETL 뷰]
┌─────────────────────────────────────────────────────────────┐
│ v_rnd_track_b (00004)         │ v_rnd_track_a (00004)       │
│ sessions + pre/post/next_day  │ daily_hrv + computed_metrics│
│ ⚠B-04: REST 누락              │ ⚠B-24: strain 미노출        │
│ ⚠B-12: ORDER BY 무의미        │ ⚠B-12: ORDER BY 무의미      │
│ ⚠B-20: 익명화 미구현          │ ⚠B-20: 익명화 미구현        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 테이블 인벤토리

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
| 9 | `training_sessions` | **00003** | ~1,800 | → users, teams, matches | **UNIQUE NULLS NOT DISTINCT** ⚠B-01 |
| 10 | `pre_session_wellness` | **00003** | ~1,300 | → sessions, users | UNIQUE(session_id), GENERATED(hooper) |
| 11 | `post_session_feedback` | **00003** | ~1,300 | → sessions, users | UNIQUE(session_id) |
| 12 | `next_day_reviews` | **00003** | ~1,300 | → sessions, users | UNIQUE(session_id) |
| 13 | `computed_load_metrics` | **00003** | ~1,800 | → users | UNIQUE(user_id, metric_date) |
| 14 | `hrv_measurements` | **00003** | ~1,800 | → users, sessions | GENERATED(rr_count) |
| 15 | `daily_hrv_metrics` | **00003** | ~1,800 | → users, hrv_measurements | UNIQUE(user_id, metric_date) |

### 3.3 ENUM 타입 인벤토리

| ENUM | 값 목록 | 사용 테이블 | 마이그레이션 |
|------|---------|-------------|:-----------:|
| `team_role` | ADMIN, MANAGER, MEMBER, GUEST | team_members | 00001 |
| `match_status` | OPEN, CONFIRMED, COMPLETED, CANCELLED | matches | 00001 |
| `attendance_status` | PENDING, ACCEPTED, DECLINED, MAYBE | attendances | 00001 |
| `record_room_status` | OPEN, CLOSED | record_rooms | 00001 |
| `session_type` | TRAINING, MATCH, REST, OTHER | training_sessions | 00003 |
| `post_condition` | VERY_BAD, BAD, NEUTRAL, GOOD, VERY_GOOD | post_session_feedback | 00003 |
| `next_day_condition` | WORSE, SAME, BETTER | next_day_reviews | 00003 |
| `hrv_source` | CHEST_STRAP, SMARTWATCH, FINGER_SENSOR, APP_MANUAL, EXTERNAL_IMPORT | hrv_measurements | 00003 |
| `hrv_context` | MORNING_REST, PRE_SESSION, POST_SESSION, DURING_SESSION, NIGHT_SLEEP, OTHER | hrv_measurements | 00003 |

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

### 3.5 데이터 리니지 — 컬럼 수준 추적 (v2.0 신규)

#### Track B 리니지

```
[서비스 DB 컬럼]                    [ETL 변환]                [R&D 스키마]             [파이프라인 출력]
─────────────────────────────────────────────────────────────────────────────────────────────────────
ts.user_id (UUID)           ──→  ::text AS athlete_id  ──→  athlete_id (str)    ──→  GROUP BY key
                                 ⚠B-20: SHA-256 미적용
ts.session_date (DATE)      ──→  AS date               ──→  date (datetime)     ──→  시계열 인덱스
ps.session_rpe (SMALLINT)   ──→  AS rpe                ──→  rpe (float, NaN OK) ──→  ×duration→srpe
ts.duration_min (FLOAT)     ──→  AS duration_min       ──→  duration_min        ──→  ×rpe→srpe
ps.session_rpe×ts.duration  ──→  COALESCE(...,0) AS srpe──→ srpe (float, 0=REST)──→  ATL/CTL/ACWR
pw.fatigue (SMALLINT)       ──→  AS fatigue            ──→  fatigue [1-7]       ──→  hooper_index
pw.soreness (SMALLINT)      ──→  AS doms ⚠B-17         ──→  doms [1-7]          ──→  hooper_index
pw.stress (SMALLINT)        ──→  AS stress             ──→  stress [1-7]        ──→  hooper_index
pw.sleep (SMALLINT)         ──→  AS sleep              ──→  sleep [1-7]         ──→  hooper_index
                                                            ─── 파이프라인 산출 ───
                                                            atl_rolling          ──→  ACWR 분자
                                                            ctl_rolling          ──→  ACWR 분모
                                                            acwr_rolling         ──→  혼합효과모형 X
                                                            monotony             ──→  혼합효과모형 X
                                                            strain               ──→  보조 지표
```

#### Track A 리니지

```
[서비스 DB 컬럼]                    [ETL 변환]                [R&D 스키마]             [파이프라인 출력]
─────────────────────────────────────────────────────────────────────────────────────────────────────
h.user_id (UUID)            ──→  ::text AS subject_id  ──→  subject_id (str)    ──→  GROUP BY key
                                 ⚠B-20: SHA-256 미적용
h.metric_date (DATE)        ──→  AS date               ──→  date (datetime)     ──→  시계열 인덱스
h.rmssd (FLOAT)             ──→  AS rmssd              ──→  rmssd               ──→  HRV 원시값
h.sdnn (FLOAT)              ──→  AS sdnn               ──→  sdnn                ──→  HRV 원시값
h.ln_rmssd (FLOAT)          ──→  AS ln_rmssd           ──→  ln_rmssd            ──→  혼합효과모형 Y
h.ln_rmssd_7d (FLOAT)       ──→  AS ln_rmssd_7d        ──→  ln_rmssd_7d         ──→  평활 추세
m.acwr_rolling (FLOAT)      ──→  AS acwr_rolling       ──→  acwr_rolling        ──→  혼합효과모형 X
m.acwr_ewma (FLOAT)         ──→  AS acwr_ewma          ──→  acwr_ewma           ──→  민감도 비교
m.monotony (FLOAT)          ──→  AS monotony           ──→  monotony            ──→  보조 지표
m.daily_load (FLOAT)        ──→  AS srpe               ──→  srpe                ──→  부하 원시값
m.strain (strain_value)     ──→  (미노출 ⚠B-24)        ──→  —                   ──→  —
m.dcwr_rolling              ──→  (미노출 ⚠B-22)        ──→  —                   ──→  —
m.tsb_rolling               ──→  (미노출 ⚠B-22)        ──→  —                   ──→  —
```

---

## 4. data_migration.md 컴플라이언스 감사 (v2.0 신규)

`data_migration.md`는 본 스키마 확장의 **원안 설계서**이다. 실제 구현(`00003`, `00004`)이 원안의 요구사항을 얼마나 충족하는지 항목별로 감사한다.

### 4.1 기능 요구사항 컴플라이언스

| # | data_migration.md 요구사항 | 구현 상태 | 적합 | 비고 |
|:-:|---------------------------|:---------:|:----:|------|
| F-01 | 8개 핵심 테이블 DDL | 8/8 구현 | ✅ | 완전 적합 |
| F-02 | ENUM 5종 (session_type 외) | 5/5 구현 | ✅ | 완전 적합 |
| F-03 | Hooper Index GENERATED STORED | 구현됨 | ✅ | fatigue+soreness+stress+sleep |
| F-04 | rr_count GENERATED STORED | 구현됨 | ✅ | array_length(rr_intervals_ms, 1) |
| F-05 | ETL 뷰 v_rnd_track_b | 구현됨 | ⚠️ | B-04: REST 누락, B-20: 익명화 미적용 |
| F-06 | ETL 뷰 v_rnd_track_a | 구현됨 | ⚠️ | B-24: strain 미노출, B-20: 익명화 미적용 |
| F-07 | REST일 sRPE=0 처리 | 미구현 | ❌ | B-04: WHERE 조건이 REST를 제외 |
| F-08 | RLS 전 테이블 활성화 | 구현됨 | ✅ | 8개 테이블 모두 RLS ENABLE |
| F-09 | ON DELETE CASCADE 체인 | 구현됨 | ⚠️ | B-23: hrv_measurements만 SET NULL |
| F-10 | UNIQUE 제약으로 멱등성 | 구현됨 | ⚠️ | B-01: NULLS NOT DISTINCT 오류 |

### 4.2 보안 요구사항 컴플라이언스

| # | data_migration.md 요구사항 | 구현 상태 | 적합 | 관련 버그 |
|:-:|---------------------------|:---------:|:----:|:---------:|
| S-01 | phone AES-256 암호화 | TEXT 평문 | ❌ | B-18 |
| S-02 | R&D 익명화: SHA-256(UUID‖salt) | user_id::text 직접 노출 | ❌ | **B-20** |
| S-03 | RLS USING (user_id = auth.uid()) | 구현됨 | ⚠️ | B-05: 팀 기반 패턴 누락 |
| S-04 | 개별 대시보드만, 집계 팀 리포트 | 구현 안 됨 (RLS 차단) | ❌ | B-05 |
| S-05 | 웰니스 뷰 읽기 전용 | 뷰 자체는 읽기 전용 | ✅ | — |

### 4.3 데이터 품질 요구사항 컴플라이언스

| # | data_migration.md 요구사항 | 구현 상태 | 적합 | 관련 버그 |
|:-:|---------------------------|:---------:|:----:|:---------:|
| Q-01 | Hooper 항목 1~7 CHECK | 구현됨 | ✅ | — |
| Q-02 | session_rpe Borg CR-10 (0~10) | CHECK 1~10 | ❌ | B-06 |
| Q-03 | position 14종 CHECK | 구현됨 | ✅ | — |
| Q-04 | nn_count ≥ 150 유효성 기준 | valid BOOLEAN으로 위임 | ⚠️ | B-25: DEFAULT 없음 |
| Q-05 | 결측은 NULL 유지 (ADR-004) | 구현됨 | ✅ | — |

### 4.4 컴플라이언스 요약

```
                         적합  부분적합  미적합
기능 요구사항 (10항목)     5     4        1      ████████████████░░░░ 50% 완전적합
보안 요구사항  (5항목)     1     1        3      ████░░░░░░░░░░░░░░░░ 20% 완전적합
품질 요구사항  (5항목)     3     1        1      ████████████░░░░░░░░ 60% 완전적합
──────────────────────────────────────────────────────────────────────
전체          (20항목)     9     6        5      ██████████░░░░░░░░░░ 45% 완전적합
```

**결론**: 기능적 골격은 대부분 구현되었으나, **보안 요구사항 적합률이 20%로 가장 취약**하다. 특히 S-02(익명화)와 S-01(암호화)은 프로덕션 전환의 필수 선행 조건이다.

---

## 5. 심각도 분류 기준

| 등급 | 명칭 | 정의 | SLA |
|:----:|------|------|:---:|
| **P0** | 치명 | 데이터 손실, INSERT 실패, 무결성 파괴. 운영 환경 적용 즉시 장애. | 수정 마이그레이션 없이 배포 금지 |
| **P1** | 높음 | 비즈니스 로직 오류, 분석 결과 왜곡, 핵심 기능 차단, 개인정보 위반. | PoV 데모 전 수정 필수 |
| **P2** | 중간 | 구조적 비효율, 유지보수 비용 증가, 기술 부채. | 다음 마이그레이션(00006)에서 처리 |
| **P3** | 낮음 | 컨벤션 불일치, 문서-구현 괴리, 가독성 저하. | 백로그 등록 후 순차 처리 |

---

## 6. 발견 사항 총괄

### 6.1 심각도별 분포

```
P0 치명  ██████████████████  2건  ( 8.0%)
P1 높음  █████████████████████████████████████████████  5건  (20.0%)
P2 중간  ██████████████████████████████████████████████████████████████████████████████████████████  10건 (40.0%)
P3 낮음  ████████████████████████████████████████████████████████████████████████  8건  (32.0%)
```

### 6.2 분류별 분포

| 분류 | 건수 | 해당 ID |
|------|:----:|---------|
| 무결성·제약 | 2 | B-01, B-02 |
| 비즈니스 로직·의미론 | 2 | B-04, B-06 |
| 보안·RLS·프라이버시 | 5 | B-05, B-18, B-19, **B-20**, **B-21** |
| 정규화·모델링 | 4 | B-03, B-07, B-08, B-10 |
| 추적성 | 1 | B-09 |
| 성능·인덱스 | 3 | B-11, B-12, B-13 |
| 운영 | 1 | B-14 |
| 컨벤션·명명 | 3 | B-15, B-16, B-17 |
| ETL·리니지 | 2 | **B-22**, **B-24** |
| 스키마 기본값 | 2 | **B-23**, **B-25** |

### 6.3 전체 발견 사항 목록

| ID | 심각도 | 분류 | 제목 | 대상 | v2.0 |
|:--:|:------:|------|------|------|:----:|
| B-01 | **P0** | 무결성 | NULLS NOT DISTINCT — 훈련 세션 사용자당 1개 제한 | 00003 L61 | — |
| B-02 | **P0** | 무결성 | user_id 이중 저장 — 크로스 사용자 불일치 가능 | 00003 L81,110,135 | — |
| B-03 | **P1** | 정규화 | has_* 플래그 — 트리거 없는 파생 데이터 동기화 불능 | 00003 L54-56 | — |
| B-04 | **P1** | 의미론 | v_rnd_track_b에서 REST일 제외 → ACWR 산출 왜곡 | 00004 L42 | — |
| B-05 | **P1** | 보안 | RLS "본인만" — 코치/매니저의 선수 데이터 조회 불가 | 00003 전체 RLS | — |
| B-06 | **P1** | 도메인 | session_rpe CHECK 1~10 — CR-10의 0 누락 | 00003 L112 | — |
| B-07 | **P2** | 정규화 | user_profiles 1:1 분리 — JOIN 비용 대비 실익 부족 | 00003 L18-31 | — |
| B-08 | **P2** | 정규화 | Surrogate Key 남용 — 3개 테이블에 불필요한 id UUID | 00003 L79,107,132 | — |
| B-09 | **P2** | 추적성 | computed_load_metrics — 산출 파라미터·버전·이력 없음 | 00003 L156-180 | — |
| B-10 | **P2** | 모델링 | daily_hrv_metrics.measurement_id — 대표 측정 선택 기준 부재 | 00003 L230 | — |
| B-11 | **P2** | 성능 | rr_intervals_ms FLOAT[] — 배열 크기 제한 없음 | 00003 L203 | — |
| B-12 | **P2** | 성능 | ETL 뷰 ORDER BY — SQL 표준상 보장 없는 무의미한 정렬 | 00004 L43,73 | — |
| B-13 | **P2** | 성능 | session_date 단독 인덱스 누락 — 날짜 범위 쿼리 비효율 | 00003 L64 | — |
| B-14 | **P2** | 운영 | updated_at 자동 갱신 트리거 부재 | 00003 L30,58 | — |
| B-15 | **P3** | 컨벤션 | ENUM vs CHECK 혼재 — 값 제한 패턴 불통일 | 00003 L9,23 | — |
| B-16 | **P3** | 컨벤션 | strain vs strain_value — R&D 파이프라인과 명명 불일치 | 00003 L170 | — |
| B-17 | **P3** | 컨벤션 | soreness vs doms — 동일 개념 이름 분기 | 00003 L84 | — |
| B-18 | **P3** | 보안 | phone TEXT 평문 — data_migration.md 암호화 요건 미반영 | 00003 L22 | — |
| B-19 | **P3** | 보안 | computed_load_metrics UPDATE 정책 없음 — 배치 갱신 불가 | 00003 L184-188 | — |
| **B-20** | **P1** | **프라이버시** | **ETL 뷰 익명화 미구현 — SHA-256 요건 미충족** | **00004 L17,56** | **신규** |
| **B-21** | **P2** | **보안** | **DELETE 정책 전면 부재 — 데이터 삭제권 미보장** | **00003 전체** | **신규** |
| **B-22** | **P2** | **ETL** | **computed_load_metrics 사장 컬럼 — ETL 미노출** | **00003 L168-172** | **신규** |
| **B-23** | **P3** | **FK** | **hrv_measurements.session_id ON DELETE SET NULL 불일치** | **00003 L198** | **신규** |
| **B-24** | **P3** | **ETL** | **v_rnd_track_a strain 미노출** | **00004 L51-73** | **신규** |
| **B-25** | **P3** | **기본값** | **daily_hrv_metrics.valid DEFAULT 부재** | **00003 L245** | **신규** |

---

## 7. 상세 분석 — P0 치명적 결함

### 7.1 B-01: NULLS NOT DISTINCT — 훈련 세션 사용자당 1개 제한

#### 현황

| 항목 | 내용 |
|------|------|
| **위치** | `00003_training_wellness_schema.sql` Line 61 |
| **현재 DDL** | `UNIQUE NULLS NOT DISTINCT (user_id, match_id)` |
| **설계 의도** | 동일 사용자가 같은 경기(match)에 중복 세션을 생성하는 것을 방지 |

#### 문제 분석

`NULLS NOT DISTINCT`(PostgreSQL 15+)는 UNIQUE 제약에서 NULL 값을 동등하게 취급한다. 따라서 `(user_id='A', match_id=NULL)` 쌍이 테이블 전체에서 **최대 1건**만 허용된다.

TRAINING, REST, OTHER 타입의 세션은 모두 `match_id = NULL`이므로, **한 사용자가 경기 외 세션을 전체 기간 통틀어 단 1개만 생성 가능**하다.

```sql
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
| training_sessions | 15명 × ~103일(경기 제외) = ~1,545행 필요 → 15행만 삽입 가능 |
| 하위 3개 테이블 | session 부재로 wellness/feedback/review도 생성 불가 |
| computed_load_metrics | 부하 지표 산출 데이터 부족 |
| ETL 뷰 | 거의 빈 결과 반환 |
| R&D 파이프라인 전체 | ACWR/Monotony/혼합효과모형 실행 불가 |

#### 미발견 원인

합성 데이터 생성(`generate_seed_data.py`)이 **CSV 직접 생성** 방식이라 PostgreSQL 제약을 거치지 않았다. `export_seed_sql.py`의 INSERT를 실제 DB에 실행하면 즉시 발견된다.

#### 수정안 (DBA + DE 합의)

```sql
-- B-01: UNIQUE NULLS NOT DISTINCT 제거 → Partial Unique Index로 교체
ALTER TABLE training_sessions
  DROP CONSTRAINT IF EXISTS training_sessions_user_id_match_id_key;

CREATE UNIQUE INDEX idx_sessions_user_match
  ON training_sessions(user_id, match_id)
  WHERE match_id IS NOT NULL;
```

**설계 원칙**: "같은 경기에 대한 중복 세션 방지"와 "다수 훈련 세션 허용"을 **분리된 제약**으로 처리한다. Partial Unique Index는 `match_id IS NOT NULL`인 행에만 유일성을 강제하므로, `match_id = NULL`인 훈련/휴식 세션은 자유롭게 생성 가능하다.

#### 검증 SQL

```sql
-- 테스트 1: 동일 사용자, match_id=NULL → 2건 모두 성공
INSERT INTO training_sessions (user_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001', 'TRAINING', '2025-09-01');
INSERT INTO training_sessions (user_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001', 'TRAINING', '2025-09-02');

-- 테스트 2: 동일 사용자, 동일 match_id → 두 번째 실패
INSERT INTO training_sessions (user_id, match_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001', 'MATCH', '2026-02-15');
INSERT INTO training_sessions (user_id, match_id, session_type, session_date)
VALUES ('00000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001', 'MATCH', '2026-02-15');
-- unique_violation 기대
```

---

### 7.2 B-02: user_id 이중 저장 — 크로스 사용자 불일치 가능

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

두 `user_id`의 일치를 강제하는 **CHECK 제약, 트리거, 복합 FK가 없으므로**, 크로스 사용자 삽입이 가능하다.

| 시나리오 | 발생 조건 | 결과 |
|----------|-----------|------|
| 크로스 사용자 삽입 | B가 A의 session에 `user_id='B'`로 wellness INSERT | DB 수용, 논리적 오류 |
| RLS 우회 | B가 A의 세션에 자신의 데이터를 연결 가능 | 보안 위반 |
| R&D 집계 왜곡 | `GROUP BY user_id` 시 세션 소유자와 웰니스 작성자 불일치 | 분석 왜곡 |

#### 수정안 비교 (DBA + DE 토론 결과)

| 방안 | 접근 | 장점 | 단점 |
|:----:|------|------|------|
| **A (정규화)** | `user_id` 컬럼 제거, RLS를 JOIN 기반으로 전환 | 근본 해결, 불일치 원천 차단 | RLS 서브쿼리 추가 |
| B (트리거) | `BEFORE INSERT` 트리거로 일치 검증 | 기존 구조 유지 | 트리거 유지보수 비용 |
| C (복합 FK) | `(session_id, user_id)` 복합 FK | DB 레벨 강제 | sessions에 UNIQUE 추가 필요 |

#### 합의 결론: 방안 A (정규화) 채택

**성능 영향 평가** (DBA): `session_id`에 UNIQUE 인덱스가 존재하므로 서브쿼리는 Index Unique Scan → O(1). Supabase 인증 컨텍스트에서 `auth.uid()` 호출 1회 + UNIQUE 조회 1회로 기존 직접 비교와 실측 차이 무시 가능.

---

## 8. 상세 분석 — P1 비즈니스 로직 오류

### 8.1 B-03: has_* 플래그 — 트리거 없는 파생 데이터

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L54-56 |
| **컬럼** | `has_pre_wellness`, `has_post_feedback`, `has_next_day_review` |
| **근본 문제** | 하위 테이블의 행 존재 여부를 나타내는 파생 데이터인데, INSERT/DELETE 시 자동 갱신 메커니즘 없음 |

| 상태 | 플래그 값 | 실제 상태 | 불일치 |
|------|:---------:|:---------:|:------:|
| wellness INSERT 성공, 플래그 UPDATE 실패 | FALSE | 행 존재 | 불일치 |
| wellness DELETE 후, 플래그 UPDATE 누락 | TRUE | 행 없음 | 불일치 |
| 트랜잭션 부분 실패 | 불확정 | 불확정 | 불확정 |

**DBA 의견**: 플래그 3개를 제거하고 `EXISTS` 서브쿼리로 동적 판별. UNIQUE 인덱스 기반 O(1) 비용.

**DE 의견**: R&D 파이프라인은 하위 테이블을 직접 JOIN하므로 플래그에 의존하지 않음.

```sql
ALTER TABLE training_sessions
  DROP COLUMN has_pre_wellness,
  DROP COLUMN has_post_feedback,
  DROP COLUMN has_next_day_review;
```

---

### 8.2 B-04: v_rnd_track_b에서 REST일 제외 → ACWR 왜곡

| 항목 | 내용 |
|------|------|
| **위치** | `00004_etl_views.sql` L42 |
| **현재 조건** | `WHERE ps.session_rpe IS NOT NULL` |
| **문제** | REST 세션은 `post_session_feedback` 행이 없음 → 뷰에서 완전히 제외 |

#### ACWR 왜곡 시뮬레이션

```
실제 7일 부하 시퀀스: [500, 400, 450, 0, 500, 600, 0]   (일=REST=0)
올바른 ATL = mean = 350.0

REST 누락 시 시퀀스:  [500, 400, 450, 500, 600]          (5일만 포함)
왜곡된 ATL = mean = 490.0                                 (+40% 과대추정)
```

**data_migration.md 5.2절 명시**: "session_type='REST', sRPE=0 (의도적 0, 결측 아님)".

```sql
-- v_rnd_track_b WHERE 절 수정
WHERE ps.session_rpe IS NOT NULL
   OR ts.session_type = 'REST';
```

---

### 8.3 B-05: RLS "본인만" 정책 — 팀 기능 차단

| 항목 | 내용 |
|------|------|
| **기존 패턴 (00001/00002)** | `matches_read_team`: 같은 팀이면 조회. ADMIN/MANAGER는 수정 가능. |
| **신규 패턴 (00003)** | `sessions_read_own`: 본인만 조회 가능 |
| **불일치** | 8개 신규 테이블 전부가 기존 팀 기반 패턴과 충돌 |

| 역할 | 기존 테이블 조회 | 신규 테이블 조회 | 기대 동작 |
|------|:----------------:|:----------------:|:---------:|
| ADMIN (코치) | 같은 팀 전체 | 본인만 | 같은 팀 전체 |
| MANAGER | 같은 팀 전체 | 본인만 | 같은 팀 전체 |
| MEMBER (선수) | 같은 팀 전체 | 본인만 | 본인만 |

**DE 의견**: 팀 수준 부하 모니터링은 PoV 핵심 시연 기능. 코치가 선수 ACWR 추이를 볼 수 없으면 대시보드 불가.

**DBA 의견**: `training_sessions.team_id`를 경유하는 서브쿼리로 해결. `idx_sessions_team` 인덱스로 성능 보장.

---

### 8.4 B-06: session_rpe CHECK 범위 — CR-10 스케일의 0 누락

| 항목 | 내용 |
|------|------|
| **현재** | `CHECK (session_rpe BETWEEN 1 AND 10)` |
| **Borg CR-10 정의** | 0 = Nothing at all, ..., 10 = Maximal |
| **참조** | Foster et al. (2001), "A New Approach to Monitoring Exercise Training" |
| **영향** | RPE=0 기록 불가. sRPE=0×duration 표현 불가. |

```sql
ALTER TABLE post_session_feedback
  DROP CONSTRAINT IF EXISTS post_session_feedback_session_rpe_check;
ALTER TABLE post_session_feedback
  ADD CONSTRAINT post_session_feedback_session_rpe_check
  CHECK (session_rpe BETWEEN 0 AND 10);
```

---

### 8.5 B-20: ETL 뷰 익명화 미구현 — SHA-256 요건 미충족 (v2.0 신규)

| 항목 | 내용 |
|------|------|
| **위치** | `00004_etl_views.sql` L17 (`user_id::text AS athlete_id`), L56 (`user_id::text AS subject_id`) |
| **data_migration.md 요건** | §4.3: "SHA-256(UUID ‖ salt_v1) → hex 문자열로 익명화. 서비스 UUID가 R&D에 직접 노출되지 않아야 한다." |
| **현재 구현** | `user_id::text` — UUID를 평문 텍스트로 직접 변환하여 R&D에 전달 |

#### 위험 분석

| 시나리오 | 영향 |
|----------|------|
| R&D 파이프라인 결과물(노트북, 보고서)에 UUID 노출 | 서비스 DB 직접 참조 가능 → 개인 식별 |
| 외부 공유(논문, 컨퍼런스) 시 UUID 포함 | 사용자 식별 + 데이터 재연결 위험 |
| 시드 데이터 CSV에 UUID 포함 | Git 이력에 영구 기록 |

#### PoV 예외 사항

현재 PoV 계획서에 "PoV 단계에서는 pgcrypto 없이 user_id::text를 직접 식별자로 사용"으로 명시되어 있다. 그러나:

1. **예외의 범위가 문서화되지 않음** — PoV → 프로덕션 전환 시 자동으로 익명화가 활성화되는 메커니즘 없음
2. **시드 CSV에 UUID가 이미 기록** — `data/seed/seed_track_b.csv`의 `athlete_id`가 UUID 직접 텍스트
3. **R&D 노트북·보고서에 UUID 노출** — 재현성 근거로 보존되어야 하는 결과물에 개인 식별 정보 포함

#### 수정안 (단계별)

**Phase 1 (PoV 즉시)**: 뷰 정의에 `-- TODO: 프로덕션 전환 시 SHA-256 적용 필수` 주석 + ADR 기록

**Phase 2 (프로덕션 전환)**: pgcrypto 확장 + salt 테이블 적용

```sql
-- Phase 2 수정안
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE VIEW v_rnd_track_b AS
SELECT
  encode(digest(ts.user_id::text || '_salt_v1', 'sha256'), 'hex') AS athlete_id,
  -- ... 이하 동일
```

---

## 9. 상세 분석 — P2 구조적 비효율

### 9.1 기존 발견 종합표 (B-07 ~ B-14)

| ID | 제목 | 현상 | 영향 | 수정 방향 |
|:--:|------|------|------|-----------|
| B-07 | user_profiles 1:1 분리 | users와 1:1, 두 컬럼만 보유 | 매 조회마다 LEFT JOIN | users에 컬럼 추가 또는 ADR로 근거 문서화 |
| B-08 | Surrogate Key 남용 | 3개 테이블에 `id UUID PK` + `session_id UNIQUE` | 인덱스 2개 유지 | `session_id`를 PK로 승격 (Supabase 호환 확인 후) |
| B-09 | 산출 파라미터 미기록 | ACWR window 등 추적 불가 | 재산출 시 이전 결과 비교 불가 | `pipeline_version`, `params JSONB` 추가 |
| B-10 | 대표 측정 선택 기준 부재 | 일별 HRV 1행인데 다수 측정 가능 | 구현자마다 다른 기준 적용 위험 | `COMMENT ON COLUMN` 또는 `selection_rule` 컬럼 |
| B-11 | 배열 크기 제한 없음 | FLOAT[] 무제한 | NIGHT_SLEEP 8시간 = ~240KB/행 | `CHECK (array_length(...) BETWEEN 1 AND 50000)` |
| B-12 | 뷰 ORDER BY | SQL 표준상 보장 없음 | 무의미한 정렬 비용 | ORDER BY 제거 |
| B-13 | session_date 단독 인덱스 누락 | 복합 인덱스만 존재 | 날짜 범위 쿼리 비효율 | 단독 인덱스 추가 |
| B-14 | updated_at 트리거 부재 | UPDATE 시 갱신 안 됨 | 변경 이력 추적 불가 | 공용 트리거 함수 |

### 9.2 B-09 상세: computed_load_metrics 추적성 위반

**CLAUDE.md 품질 기준**: "모든 지표/그림/표는 산출 코드 위치와 파라미터를 역추적 가능"

| 누락 정보 | 추적 불가 질문 |
|-----------|----------------|
| ATL window (7? 14?) | "이 ACWR은 어떤 window로 산출한 건가?" |
| EWMA span (7? 10?) | "EWMA 파라미터가 바뀌었는가?" |
| pipeline 버전 | "언제, 어떤 코드로 산출했는가?" |
| 이전 값 | "재산출 전후 차이가 얼마인가?" |

```sql
ALTER TABLE computed_load_metrics
  ADD COLUMN IF NOT EXISTS pipeline_version TEXT DEFAULT 'v1.0',
  ADD COLUMN IF NOT EXISTS params JSONB DEFAULT '{
    "atl_window": 7, "ctl_window": 28,
    "ewma_atl_span": 7, "ewma_ctl_span": 28
  }'::jsonb;
```

---

### 9.3 B-21: DELETE 정책 전면 부재 — 데이터 삭제권 미보장 (v2.0 신규)

| 항목 | 내용 |
|------|------|
| **위치** | `00003` 전체 — 8개 신규 테이블 |
| **현상** | SELECT, INSERT, UPDATE 정책만 존재. DELETE 정책이 **단 하나도 없음** |
| **기존 00002 패턴** | `matches_delete_admin`, `team_members_delete_admin` 등 ADMIN/MANAGER별 DELETE 정책 존재 |

#### 영향 분석

| 시나리오 | 현재 결과 |
|----------|-----------|
| 선수가 잘못 입력한 웰니스 기록 삭제 요청 | RLS에 의해 DELETE 차단 |
| 코치가 중복 세션 삭제 | RLS에 의해 DELETE 차단 |
| GDPR/개인정보보호법 "삭제권" 행사 | 앱 레벨에서 처리 불가 (service_role 필요) |
| 데이터 보정을 위한 관리자 삭제 | service_role bypass 필요 |

#### 의도 판별

**가능성 A (의도적 감사 추적)**: 웰니스/HRV 데이터는 시계열 무결성이 중요하므로 삭제를 원천 차단하고, 보정은 soft delete(별도 `is_deleted` 플래그)로 처리하려는 설계. → 그렇다면 문서화 필요.

**가능성 B (단순 누락)**: 00002에 DELETE 정책이 있는 패턴을 00003에서 반영하지 않음. → 수정 필요.

#### 수정안

```sql
-- 방안 A: 본인 삭제 허용
CREATE POLICY "sessions_delete_own" ON training_sessions FOR DELETE
  USING (user_id = auth.uid());

-- 방안 B: ADMIN만 삭제 허용 (00002 패턴 준수)
CREATE POLICY "sessions_delete_admin" ON training_sessions FOR DELETE
  USING (
    team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role = 'ADMIN'
    )
  );
```

**DBA 의견**: 시계열 데이터 특성상 방안 B(ADMIN만) 권장. 일반 사용자의 실수 삭제를 방지하면서 관리자 보정 경로를 확보.

---

### 9.4 B-22: computed_load_metrics 사장 컬럼 — ETL 미노출 (v2.0 신규)

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L168-172 (`dcwr_rolling`, `tsb_rolling`, `hooper_index`) |
| **현상** | 3개 컬럼이 computed_load_metrics에 정의되어 있으나, `v_rnd_track_a`에도 `v_rnd_track_b`에도 노출되지 않음 |

#### ADR 참조

| 컬럼 | ADR 근거 | ETL 노출 | 파이프라인 사용 |
|------|----------|:--------:|:--------------:|
| `dcwr_rolling` | ADR-011 (DCWR 대안 지표) | ❌ | `src/metrics/dcwr.py` 모듈 존재 |
| `tsb_rolling` | ADR-011 (TSB 대안 지표) | ❌ | `src/metrics/dcwr.py` 모듈 존재 |
| `hooper_index` | 웰니스 복합 지표 | ❌ | `pre_session_wellness`에서 이미 GENERATED |

#### 문제점

1. **DCWR/TSB**: ADR-011에서 정의한 대안 지표가 DB에 캐싱되지만, R&D 파이프라인이 이를 조회할 경로가 없음
2. **hooper_index 중복**: `pre_session_wellness.hooper_index`(GENERATED STORED)와 `computed_load_metrics.hooper_index`(수동 입력)가 이중 존재. 어느 것이 정본인지 모호
3. **사장 데이터**: INSERT는 되지만 조회 경로가 없으면 무의미한 저장 비용

#### 수정안

```sql
-- v_rnd_track_a에 DCWR/TSB 추가
CREATE OR REPLACE VIEW v_rnd_track_a AS
SELECT
  -- ... 기존 컬럼 ...
  m.dcwr_rolling,
  m.tsb_rolling
FROM daily_hrv_metrics h
LEFT JOIN computed_load_metrics m
  ON m.user_id = h.user_id AND m.metric_date = h.metric_date
WHERE h.valid = TRUE;
```

`computed_load_metrics.hooper_index`는 `pre_session_wellness`의 GENERATED 컬럼과 중복이므로, 사용 용도를 명확히 하거나 제거를 검토.

---

## 10. 상세 분석 — P3 컨벤션·문서화

### 10.1 기존 발견 종합표 (B-15 ~ B-19)

| ID | 제목 | 현상 | 수정 방향 |
|:--:|------|------|-----------|
| B-15 | ENUM vs CHECK 혼재 | session_type=ENUM, position=CHECK. 기준 부재. | ADR-012 추가 |
| B-16 | strain vs strain_value | R&D `strain`, DB `strain_value` | DB 컬럼명을 `strain`으로 변경 |
| B-17 | soreness vs doms | 서비스 `soreness`, R&D `doms` | 매핑 문서화 또는 통일 |
| B-18 | phone 평문 | AES-256 요건 미반영 | pgcrypto 또는 COMMENT ON COLUMN 경고 |
| B-19 | UPDATE 정책 없음 | computed_load_metrics 배치 UPSERT 불가 | UPDATE 정책 추가 |

### 10.2 B-15 상세: ENUM vs CHECK 기준안

| 기준 | ENUM 적합 | CHECK IN 적합 |
|------|-----------|---------------|
| 값의 변경 빈도 | 거의 변경 없음 (상태 머신) | 향후 추가/변경 가능 |
| 값의 의미론 | 상태 전이가 명확 | 단순 열거형 목록 |
| PostgreSQL 제약 | ADD VALUE 가능, 삭제 불가 | 자유로운 변경 |
| **적용 예** | session_type, match_status | position (포지션 신설 가능) |

### 10.3 B-23: hrv_measurements.session_id FK CASCADE 불일치 (v2.0 신규)

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L198 |
| **현상** | `session_id UUID REFERENCES training_sessions(id) ON DELETE SET NULL` |
| **대조** | wellness/feedback/reviews는 모두 `ON DELETE CASCADE` |

#### 불일치 결과

| 이벤트 | pre_session_wellness | post_session_feedback | next_day_reviews | hrv_measurements |
|--------|:--------------------:|:---------------------:|:----------------:|:----------------:|
| 세션 삭제 | **CASCADE 삭제** | **CASCADE 삭제** | **CASCADE 삭제** | **session_id=NULL** (고아) |

세션 삭제 후 HRV 데이터만 `session_id=NULL`로 남아 고아 행이 된다. `user_id` FK는 별도로 존재하므로 사용자 삭제 시에는 CASCADE로 제거되지만, **세션 삭제 시에만 비대칭 동작**이 발생한다.

**DBA 의견**: HRV 측정은 세션 외 독립 측정(MORNING_REST 등)이 가능하므로 SET NULL이 적합할 수 있다. 그러나 이 설계 의도가 문서화되어 있지 않다.

**수정안**: `COMMENT ON COLUMN`으로 SET NULL 선택 근거 명시.

```sql
COMMENT ON COLUMN hrv_measurements.session_id IS
  'FK → training_sessions. ON DELETE SET NULL: 세션 삭제 시에도 독립 측정(MORNING_REST, NIGHT_SLEEP) 데이터를 보존하기 위한 의도적 선택.';
```

---

### 10.4 B-24: v_rnd_track_a strain 미노출 (v2.0 신규)

| 항목 | 내용 |
|------|------|
| **위치** | `00004_etl_views.sql` L51-73 |
| **현상** | `v_rnd_track_a`가 `acwr_rolling`, `acwr_ewma`, `monotony`, `srpe`를 노출하지만 `strain`(또는 `strain_value`)을 포함하지 않음 |
| **영향** | R&D Track A 혼합효과모형에서 Monotony-Strain 복합 분석 시 별도 JOIN 필요 |

```sql
-- v_rnd_track_a 수정: strain 추가
m.strain AS strain  -- B-16 수정 후 컬럼명
```

---

### 10.5 B-25: daily_hrv_metrics.valid DEFAULT 부재 (v2.0 신규)

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L245 |
| **현상** | `valid BOOLEAN` — DEFAULT 없음, NOT NULL 없음 |
| **영향** | INSERT 시 `valid`를 명시하지 않으면 NULL 저장 → `WHERE valid = TRUE` 조건에서 자동 제외 |

#### 구체적 문제

```sql
-- valid 미지정 INSERT
INSERT INTO daily_hrv_metrics (user_id, metric_date, rmssd, sdnn, ln_rmssd, ln_rmssd_7d)
VALUES ('user_A', '2025-09-01', 45.2, 52.1, 3.81, 3.75);
-- valid = NULL (DEFAULT 없음)

-- ETL 뷰 쿼리
SELECT * FROM v_rnd_track_a;  -- WHERE h.valid = TRUE
-- 위 행이 제외됨! NULL != TRUE
```

```sql
-- 수정안
ALTER TABLE daily_hrv_metrics
  ALTER COLUMN valid SET DEFAULT TRUE,
  ALTER COLUMN valid SET NOT NULL;

-- 기존 NULL 행 보정
UPDATE daily_hrv_metrics SET valid = TRUE WHERE valid IS NULL;
```

---

## 11. 횡단 관심사 분석

### 11.1 정규화 수준 평가

| 테이블 | 정규형 | 위반 사항 | 관련 ID |
|--------|:------:|-----------|:-------:|
| user_profiles | 3NF | B-07: 1:1 분리 정당성 미문서화 | B-07 |
| training_sessions | 2NF | B-03: has_* 파생 플래그 (갱신 이상) | B-03 |
| pre_session_wellness | **비정규** | B-02: user_id 이행적 종속 위반 | B-02 |
| post_session_feedback | **비정규** | B-02: 동일 | B-02 |
| next_day_reviews | **비정규** | B-02: 동일 | B-02 |
| computed_load_metrics | 3NF | B-09: 추적성 컬럼 부족 (정규화 자체는 문제 없음) | B-09 |
| hrv_measurements | 1NF | B-11: FLOAT[] 크기 미제한 (1NF 경계 논쟁) | B-11 |
| daily_hrv_metrics | 3NF | B-10: 선택 기준 미문서화 | B-10 |

### 11.2 RLS 일관성 매트릭스 (v2.0 확장)

| 테이블 | SELECT | INSERT | UPDATE | DELETE | 패턴 | 비고 |
|--------|:------:|:------:|:------:|:------:|:----:|------|
| users (00001) | 본인 | 본인 | 본인 | — | 본인 | |
| teams (00001) | 팀 멤버 | 인증 | ADMIN | ADMIN | 역할 기반 | |
| matches (00001) | 팀 멤버 | ADMIN/MGR | ADMIN/MGR | ADMIN | 역할 기반 | |
| team_members (00001) | — | ADMIN/MGR | ADMIN | ADMIN | 역할 기반 | |
| attendances (00001) | — | ADMIN/MGR | 본인+MGR | — | 혼합 | |
| record_rooms (00001) | — | MGR+ | MGR+ | — | 역할 기반 | |
| match_records (00001) | — | MGR+ | MGR+ | — | 역할 기반 | |
| **training_sessions** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-05,B-21 |
| **pre_session_wellness** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-05,B-21 |
| **post_session_feedback** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-05,B-21 |
| **next_day_reviews** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-05,B-21 |
| **computed_load_metrics** (00003) | **본인** | **본인** | **없음** | **없음** | **불완전** | ⚠B-19,B-21 |
| **hrv_measurements** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-05,B-21 |
| **daily_hrv_metrics** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-05,B-21 |
| **user_profiles** (00003) | **본인** | **본인** | **본인** | **없음** | **본인** | ⚠B-21 |

**패턴 불일치 요약**: 기존 테이블(00001/00002)은 역할 기반 계층적 접근(ADMIN > MANAGER > MEMBER). 신규 테이블(00003)은 단순 본인 제한 + DELETE 정책 전면 부재. 팀 스포츠의 코치 역할이 반영되지 않았다.

### 11.3 인덱스 커버리지 분석

| 쿼리 패턴 | 필요 인덱스 | 현재 상태 | 비고 |
|-----------|-------------|:---------:|------|
| 사용자별 세션 조회 (일반) | `(user_id, session_date)` | ✅ 있음 | |
| 날짜 범위 세션 조회 (ETL 배치) | `(session_date)` | ❌ **없음** | B-13 |
| 팀별 세션 조회 (대시보드) | `(team_id)` | ✅ 있음 | |
| 사용자별 부하 지표 (시계열) | `(user_id, metric_date DESC)` | ✅ 있음 | |
| 사용자별 HRV (시계열) | `(user_id, metric_date DESC)` | ✅ 있음 | |
| HRV 측정 → 세션 연결 | `(session_id)` | ✅ 있음 | |
| 경기별 세션 조회 | `(match_id)` | ⚠️ Partial Index만 | B-01 수정 후 |
| RLS 팀 기반 서브쿼리 | `(team_id, user_id, role)` on team_members | ⚠️ 부분 커버 | B-05 수정 시 중요 |

### 11.4 CASCADE 체인 위험도

```
users 삭제 시 CASCADE 전파 경로:

users
  ├─ user_profiles (CASCADE)                    ─── 1행
  ├─ training_sessions (CASCADE)                ─── ~120행
  │   ├─ pre_session_wellness (CASCADE)         ─── ~100행
  │   ├─ post_session_feedback (CASCADE)        ─── ~100행
  │   ├─ next_day_reviews (CASCADE)             ─── ~100행
  │   └─ hrv_measurements (SET NULL: session_id)─── 세션 연결만 해제
  ├─ computed_load_metrics (CASCADE)            ─── ~120행
  ├─ hrv_measurements (CASCADE: user_id)        ─── ~120행
  └─ daily_hrv_metrics (CASCADE)                ─── ~120행
                                                ────────────
                                         합계:  ~780행 CASCADE 삭제
```

**위험**: 사용자 1명 삭제 시 최대 ~780행이 CASCADE 삭제. soft delete 미도입 상태에서 실수 삭제 시 복구 불가.

### 11.5 FK 동작 일관성 매트릭스 (v2.0 신규)

| 자식 테이블 | FK 컬럼 | 부모 테이블 | ON DELETE | 비고 |
|-------------|---------|-------------|:---------:|------|
| user_profiles | user_id | users | CASCADE | |
| training_sessions | user_id | users | CASCADE | |
| training_sessions | team_id | teams | CASCADE | |
| training_sessions | match_id | matches | SET NULL | match 삭제 시 세션 보존 |
| pre_session_wellness | session_id | training_sessions | CASCADE | |
| pre_session_wellness | user_id | users | CASCADE | ⚠B-02: 제거 대상 |
| post_session_feedback | session_id | training_sessions | CASCADE | |
| post_session_feedback | user_id | users | CASCADE | ⚠B-02: 제거 대상 |
| next_day_reviews | session_id | training_sessions | CASCADE | |
| next_day_reviews | user_id | users | CASCADE | ⚠B-02: 제거 대상 |
| hrv_measurements | user_id | users | CASCADE | |
| hrv_measurements | session_id | training_sessions | **SET NULL** | ⚠B-23: 비대칭 |
| daily_hrv_metrics | user_id | users | CASCADE | |
| daily_hrv_metrics | measurement_id | hrv_measurements | SET NULL | 측정 삭제 시 일별 보존 |
| computed_load_metrics | user_id | users | CASCADE | |

---

## 12. 성능 모델링 (v2.0 신규)

### 12.1 데이터 볼륨 예측

PoV (15명 × 120일) 기준 및 프로덕션 시나리오(100명 × 365일)에서의 예상 볼륨:

| 테이블 | PoV 행 수 | 프로덕션 1년 | 프로덕션 3년 | 행 크기 추정 |
|--------|:---------:|:----------:|:----------:|:----------:|
| users | 15 | 100 | 300 | ~200B |
| training_sessions | 1,800 | 31,200 | 93,600 | ~250B |
| pre_session_wellness | 1,300 | 24,000 | 72,000 | ~150B |
| post_session_feedback | 1,300 | 24,000 | 72,000 | ~150B |
| next_day_reviews | 1,300 | 24,000 | 72,000 | ~180B |
| computed_load_metrics | 1,800 | 36,500 | 109,500 | ~300B |
| hrv_measurements | 1,800 | 36,500 | 109,500 | **~120KB** |
| daily_hrv_metrics | 1,800 | 36,500 | 109,500 | ~200B |

**주의**: `hrv_measurements`의 `rr_intervals_ms FLOAT[]`가 행당 ~120KB (300 beats × 8B × TOAST 오버헤드). 프로덕션 3년 기준 **~12.5GB** (B-11 관련).

### 12.2 주요 쿼리 패턴 성능 추정

#### 패턴 1: 대시보드 — 팀 전체 최근 7일 부하 현황

```sql
SELECT athlete_id, date, srpe, acwr_rolling
FROM v_rnd_track_b
WHERE date >= CURRENT_DATE - INTERVAL '7 days';
```

| 단계 | PoV | 프로덕션 3년 | 인덱스 |
|------|:---:|:----------:|:------:|
| training_sessions scan | ~7×15=105행 | ~7×300=2,100행 | idx_sessions_date (B-13 추가 후) |
| LEFT JOIN 3개 | 각 ~70행 | 각 ~1,600행 | session_id UNIQUE index |
| **총 예상 시간** | **<10ms** | **<50ms** | |

**B-13 미수정 시**: `idx_sessions_user_date` 복합 인덱스가 `date` 단독 조건에 비효율 → Seq Scan 가능 → 프로덕션 3년에서 **~500ms**.

#### 패턴 2: R&D — 전체 선수 ACWR 시계열 (120일)

```sql
SELECT * FROM v_rnd_track_b
WHERE athlete_id = 'user_A'
ORDER BY date;
```

| 단계 | PoV | 프로덕션 3년 | 인덱스 |
|------|:---:|:----------:|:------:|
| training_sessions scan | ~120행 | ~1,095행 | idx_sessions_user_date |
| LEFT JOIN 3개 | ~100행 | ~900행 | session_id UNIQUE index |
| **총 예상 시간** | **<5ms** | **<20ms** | |

#### 패턴 3: B-05 수정 후 — RLS 팀 기반 서브쿼리

```sql
-- RLS 내부에서 실행되는 서브쿼리
SELECT team_id FROM team_members
WHERE user_id = auth.uid() AND role IN ('ADMIN', 'MANAGER');
```

| team_members 행 수 | 인덱스 | 예상 시간 |
|:------------------:|:------:|:---------:|
| 15 (PoV) | idx_team_members_user | <1ms |
| 1,000 (프로덕션) | idx_team_members_user | <1ms |

**결론**: B-05 수정(팀 기반 RLS)의 서브쿼리 추가 비용은 무시할 수 있음. `team_members`의 `user_id` 인덱스가 이미 존재.

### 12.3 TOAST 영향 분석

`hrv_measurements.rr_intervals_ms` FLOAT[] 컬럼:

| 컨텍스트 | 예상 beat 수 | 배열 크기 | TOAST 처리 |
|----------|:-----------:|:--------:|:----------:|
| MORNING_REST (5분) | ~350 | ~2.8KB | 인라인 저장 가능 |
| PRE_SESSION (2분) | ~150 | ~1.2KB | 인라인 저장 |
| POST_SESSION (2분) | ~150 | ~1.2KB | 인라인 저장 |
| **NIGHT_SLEEP (8시간)** | **~30,000** | **~240KB** | **TOAST 외부 저장** |
| **악의적 입력 (제한 없음)** | **100만+** | **~8MB** | **TOAST + 심각한 I/O** |

**B-11 수정(CHECK 50,000 제한)**으로 최대 ~400KB/행. NIGHT_SLEEP 8시간은 허용하면서 악의적 입력을 차단.

---

## 13. 긍정적 평가

비판과 함께, 현재 설계에서 적절하게 구현된 부분을 기록한다.

| 항목 | 평가 | 근거 |
|------|------|------|
| **GENERATED STORED 활용** | 우수 | `hooper_index`, `rr_count`를 DB 레벨에서 자동 산출. 일관성 보장. |
| **ON DELETE CASCADE 일관 적용** | 우수 | 부모 삭제 시 고아 행 방지. FK 체인 전체에 적용 (B-23 SET NULL 예외는 의도적일 수 있음). |
| **UNIQUE 제약으로 멱등성** | 우수 | `UNIQUE(user_id, metric_date)` 등으로 중복 삽입 방지. UPSERT 패턴 기반. |
| **ETL 뷰 분리 아키텍처** | 우수 | 서비스 스키마 ↔ R&D 스키마 변환을 뷰로 캡슐화. 양측 독립 진화 가능. |
| **ENUM 상태 제한** | 양호 | 자유 텍스트 대비 입력 오류 방지, 인덱스 효율 향상. |
| **시드 ON CONFLICT DO NOTHING** | 양호 | 멱등 시드 — 반복 실행 안전. |
| **3단계 입력 구조** | 양호 | 훈련 전→후→다음날의 시계열 흐름을 테이블 분리로 구조화. R&D lag 분석과 자연스럽게 정합. |
| **HRV 원시 배열 저장** | 양호 | RR 간격을 FLOAT[]로 저장. `filter_rr_outliers()` → `rmssd()` 파이프라인과 직접 호환. |
| **컨텍스트 ENUM 풍부** | 양호 | `hrv_context` 6종으로 측정 맥락을 세분화. 향후 분석에서 MORNING_REST vs POST_SESSION 비교 가능. |
| **인덱스 DESC 방향 지정** | 양호 | 시계열 조회의 최신 데이터 우선 접근 최적화 (`metric_date DESC`). |

---

## 14. 수정 마이그레이션 계획

### 14.1 마이그레이션 파일 구성

모든 수정을 **`00005_schema_fixes.sql`** 단일 파일로 통합한다. v2.0에서 추가된 B-20~B-25 수정을 포함한다.

| 순서 | 대상 | 수정 내용 | 관련 ID |
|:----:|------|-----------|:-------:|
| 1 | training_sessions | UNIQUE 제약 제거 → Partial Index 교체 | B-01 |
| 2 | training_sessions | has_* 플래그 3개 DROP | B-03 |
| 3 | pre_session_wellness | user_id DROP + RLS 재작성 | B-02, B-05 |
| 4 | post_session_feedback | user_id DROP + RLS 재작성 + CHECK 수정 | B-02, B-05, B-06 |
| 5 | next_day_reviews | user_id DROP + RLS 재작성 | B-02, B-05 |
| 6 | training_sessions | RLS 팀 기반 확장 + DELETE 정책 | B-05, B-21 |
| 7 | computed_load_metrics | strain_value → strain, UPDATE 정책, 추적성 컬럼 | B-16, B-19, B-09 |
| 8 | hrv_measurements | FLOAT[] CHECK, RLS 팀 확장, DELETE 정책 | B-11, B-05, B-21 |
| 9 | daily_hrv_metrics | valid DEFAULT/NOT NULL, RLS 팀 확장 | B-25, B-05 |
| 10 | training_sessions | session_date 단독 인덱스 추가 | B-13 |
| 11 | v_rnd_track_b | REST일 포함, ORDER BY 제거, 익명화 TODO 주석 | B-04, B-12, B-20 |
| 12 | v_rnd_track_a | ORDER BY 제거, strain 추가, DCWR/TSB 추가 | B-12, B-24, B-22 |
| 13 | user_profiles | DELETE 정책 추가 | B-21 |
| 14 | 공용 트리거 | updated_at 자동 갱신 | B-14 |
| 15 | hrv_measurements | COMMENT ON session_id FK 근거 | B-23 |

### 14.2 수정 SQL 전문 — `00005_schema_fixes.sql`

```sql
-- =================================================================
-- 00005_schema_fixes.sql
-- DRD v2.0 기반 수정 마이그레이션
-- 의존: 00003, 00004 적용 후 실행
-- 작성: DBA + DE 공동 (DRD-2026-001 v2.0)
--
-- 트랜잭션 안전: 전체를 단일 트랜잭션으로 실행.
-- 실패 시 ROLLBACK으로 원상 복구 가능.
-- =================================================================

BEGIN;

-- =================================================================
-- Phase 1: 치명적 결함 수정 (P0)
-- =================================================================

-- -----------------------------------------------------------------
-- [B-01] UNIQUE NULLS NOT DISTINCT → Partial Unique Index
-- 위험: 미수정 시 훈련 세션 INSERT 전면 실패
-- -----------------------------------------------------------------
ALTER TABLE training_sessions
  DROP CONSTRAINT IF EXISTS training_sessions_user_id_match_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_user_match
  ON training_sessions(user_id, match_id)
  WHERE match_id IS NOT NULL;

-- -----------------------------------------------------------------
-- [B-02] user_id 이중 저장 제거 (3개 하위 테이블)
-- 위험: 미수정 시 크로스 사용자 데이터 불일치
-- 주의: 기존 데이터가 있으면 user_id 컬럼 값을 session 경유로
--       검증한 뒤 DROP해야 함. 시드 데이터만 있는 PoV에서는 안전.
-- -----------------------------------------------------------------
ALTER TABLE pre_session_wellness DROP COLUMN IF EXISTS user_id;
ALTER TABLE post_session_feedback DROP COLUMN IF EXISTS user_id;
ALTER TABLE next_day_reviews DROP COLUMN IF EXISTS user_id;

-- =================================================================
-- Phase 2: 비즈니스 로직 수정 (P1)
-- =================================================================

-- -----------------------------------------------------------------
-- [B-03] has_* 파생 플래그 제거
-- -----------------------------------------------------------------
ALTER TABLE training_sessions
  DROP COLUMN IF EXISTS has_pre_wellness,
  DROP COLUMN IF EXISTS has_post_feedback,
  DROP COLUMN IF EXISTS has_next_day_review;

-- -----------------------------------------------------------------
-- [B-06] session_rpe CHECK 범위 수정 (Borg CR-10: 0~10)
-- -----------------------------------------------------------------
ALTER TABLE post_session_feedback
  DROP CONSTRAINT IF EXISTS post_session_feedback_session_rpe_check;
ALTER TABLE post_session_feedback
  ADD CONSTRAINT post_session_feedback_session_rpe_check
  CHECK (session_rpe BETWEEN 0 AND 10);

-- =================================================================
-- Phase 3: RLS 정책 재구축 (B-05, B-21)
-- =================================================================

-- -----------------------------------------------------------------
-- training_sessions: 팀 기반 SELECT + 본인 INSERT/UPDATE + ADMIN DELETE
-- -----------------------------------------------------------------
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
CREATE POLICY "sessions_delete_admin" ON training_sessions FOR DELETE
  USING (
    team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role = 'ADMIN'
    )
  );

-- -----------------------------------------------------------------
-- pre_session_wellness: session 경유 RLS (B-02 user_id 제거 후)
-- -----------------------------------------------------------------
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
CREATE POLICY "pre_wellness_delete_admin" ON pre_session_wellness FOR DELETE
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role = 'ADMIN'
    )
  ));

-- -----------------------------------------------------------------
-- post_session_feedback: 동일 패턴
-- -----------------------------------------------------------------
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
CREATE POLICY "post_feedback_delete_admin" ON post_session_feedback FOR DELETE
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role = 'ADMIN'
    )
  ));

-- -----------------------------------------------------------------
-- next_day_reviews: 동일 패턴
-- -----------------------------------------------------------------
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
CREATE POLICY "next_day_delete_admin" ON next_day_reviews FOR DELETE
  USING (session_id IN (
    SELECT id FROM training_sessions
    WHERE team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid() AND role = 'ADMIN'
    )
  ));

-- -----------------------------------------------------------------
-- computed_load_metrics: 팀 SELECT + UPDATE + DELETE
-- -----------------------------------------------------------------
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
CREATE POLICY "metrics_delete_admin" ON computed_load_metrics FOR DELETE
  USING (
    user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role = 'ADMIN'
    )
  );

-- -----------------------------------------------------------------
-- hrv_measurements: 팀 SELECT + DELETE
-- -----------------------------------------------------------------
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
CREATE POLICY "hrv_delete_admin" ON hrv_measurements FOR DELETE
  USING (
    user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role = 'ADMIN'
    )
  );

-- -----------------------------------------------------------------
-- daily_hrv_metrics: 팀 SELECT + DELETE
-- -----------------------------------------------------------------
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
CREATE POLICY "daily_hrv_delete_admin" ON daily_hrv_metrics FOR DELETE
  USING (
    user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role = 'ADMIN'
    )
  );

-- -----------------------------------------------------------------
-- user_profiles: DELETE 정책 추가
-- -----------------------------------------------------------------
CREATE POLICY "profiles_delete_own" ON user_profiles FOR DELETE
  USING (user_id = auth.uid());

-- =================================================================
-- Phase 4: 구조 개선 (P2)
-- =================================================================

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
-- [B-25] daily_hrv_metrics.valid DEFAULT + NOT NULL
-- -----------------------------------------------------------------
UPDATE daily_hrv_metrics SET valid = TRUE WHERE valid IS NULL;
ALTER TABLE daily_hrv_metrics
  ALTER COLUMN valid SET DEFAULT TRUE;
ALTER TABLE daily_hrv_metrics
  ALTER COLUMN valid SET NOT NULL;

-- =================================================================
-- Phase 5: ETL 뷰 재정의 (B-04, B-12, B-20, B-22, B-24)
-- =================================================================

-- -----------------------------------------------------------------
-- v_rnd_track_b: REST 포함 + ORDER BY 제거 + 익명화 TODO
-- -----------------------------------------------------------------
CREATE OR REPLACE VIEW v_rnd_track_b AS
SELECT
  -- TODO [B-20]: 프로덕션 전환 시 아래를 SHA-256 익명화로 교체
  -- encode(digest(ts.user_id::text || '_salt_v1', 'sha256'), 'hex') AS athlete_id
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

-- -----------------------------------------------------------------
-- v_rnd_track_a: ORDER BY 제거 + strain 추가 + DCWR/TSB 추가
-- -----------------------------------------------------------------
CREATE OR REPLACE VIEW v_rnd_track_a AS
SELECT
  -- TODO [B-20]: 프로덕션 전환 시 SHA-256 익명화로 교체
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
  m.strain,
  m.dcwr_rolling,
  m.tsb_rolling,
  m.daily_load AS srpe
FROM daily_hrv_metrics h
LEFT JOIN computed_load_metrics m
  ON m.user_id = h.user_id AND m.metric_date = h.metric_date
WHERE h.valid = TRUE;

-- =================================================================
-- Phase 6: 운영 개선 (P3)
-- =================================================================

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

-- -----------------------------------------------------------------
-- [B-23] hrv_measurements.session_id FK 선택 근거 문서화
-- -----------------------------------------------------------------
COMMENT ON COLUMN hrv_measurements.session_id IS
  'FK → training_sessions. ON DELETE SET NULL: 세션 삭제 시에도 독립 측정(MORNING_REST, NIGHT_SLEEP) 데이터를 보존하기 위한 의도적 선택. DRD v2.0 B-23 참조.';

-- -----------------------------------------------------------------
-- [B-10] daily_hrv_metrics.measurement_id 선택 기준 문서화
-- -----------------------------------------------------------------
COMMENT ON COLUMN daily_hrv_metrics.measurement_id IS
  'FK → hrv_measurements. 동일 날짜 다수 측정 시 MORNING_REST 우선, 동일 컨텍스트면 rr_count 최대 측정을 대표로 선택. DRD v2.0 B-10 참조.';

COMMIT;
```

### 14.3 마이그레이션 실행 체크리스트

| # | 단계 | 검증 | 관련 버그 |
|:-:|------|------|:---------:|
| 1 | 로컬 DB에 00001~00004 순차 적용 | 에러 없이 완료 | — |
| 2 | seed.sql 실행 | 15명 사용자, 15 프로필, 15 팀멤버 | — |
| 3 | `BEGIN;` ~ `COMMIT;` 전체 실행 | 에러 없이 완료 | 전체 |
| 4 | export_seed_sql.py INSERT 실행 | ~1,800 세션 삽입 성공 | B-01 |
| 5 | 동일 사용자 match_id=NULL 2건 INSERT | 성공 | B-01 |
| 6 | 크로스 사용자 웰니스 삽입 시도 | session_id 경유 RLS 차단 | B-02 |
| 7 | ADMIN 역할로 타 선수 데이터 조회 | 조회 성공 | B-05 |
| 8 | MEMBER 역할로 타 선수 데이터 조회 | 조회 차단 | B-05 |
| 9 | v_rnd_track_b에서 REST 행 존재 확인 | session_type='REST', srpe=0 | B-04 |
| 10 | RPE=0 INSERT 시도 | 성공 | B-06 |
| 11 | valid 미지정 HRV INSERT | valid=TRUE (DEFAULT 적용) | B-25 |
| 12 | v_rnd_track_a에서 strain, dcwr, tsb 확인 | 값 존재 | B-22, B-24 |
| 13 | ADMIN이 세션 DELETE 시도 | 성공 | B-21 |
| 14 | MEMBER가 세션 DELETE 시도 | 차단 | B-21 |
| 15 | `python -m pytest tests/ -v` | 99개 전체 통과 | — |

---

## 15. 롤백 절차 (v2.0 신규)

### 15.1 롤백 전략

00005 마이그레이션은 `BEGIN` ~ `COMMIT` 트랜잭션으로 래핑되어 있다. **실행 중 오류 발생 시 자동 ROLLBACK**되어 00003/00004 상태로 복원된다.

그러나 **COMMIT 이후** 문제가 발견되어 원복이 필요한 경우를 대비하여, 명시적 롤백 SQL을 제공한다.

### 15.2 롤백 SQL — `00005_rollback.sql`

```sql
-- =================================================================
-- 00005_rollback.sql
-- 00005_schema_fixes.sql COMMIT 이후 원복이 필요한 경우
-- 주의: seed_insert.sql 실행 전에만 안전. 데이터 삽입 후에는
--       user_id 복원에 추가 작업 필요.
-- =================================================================

BEGIN;

-- Phase 6 롤백: 트리거/코멘트
DROP TRIGGER IF EXISTS trg_sessions_updated ON training_sessions;
DROP TRIGGER IF EXISTS trg_user_profiles_updated ON user_profiles;
DROP FUNCTION IF EXISTS update_updated_at();
COMMENT ON COLUMN hrv_measurements.session_id IS NULL;
COMMENT ON COLUMN daily_hrv_metrics.measurement_id IS NULL;

-- Phase 5 롤백: ETL 뷰 원복 (00004 원본)
CREATE OR REPLACE VIEW v_rnd_track_b AS
SELECT
  ts.user_id::text AS athlete_id,
  ts.session_date AS date,
  ps.session_rpe AS rpe,
  ts.duration_min,
  ps.session_rpe * ts.duration_min AS srpe,
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
ORDER BY ts.user_id, ts.session_date;

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
WHERE h.valid = TRUE
ORDER BY h.user_id, h.metric_date;

-- Phase 4 롤백: 구조 개선 원복
ALTER TABLE daily_hrv_metrics ALTER COLUMN valid DROP NOT NULL;
ALTER TABLE daily_hrv_metrics ALTER COLUMN valid DROP DEFAULT;
DROP INDEX IF EXISTS idx_sessions_date;
ALTER TABLE hrv_measurements DROP CONSTRAINT IF EXISTS hrv_rr_array_size;
ALTER TABLE computed_load_metrics DROP COLUMN IF EXISTS params;
ALTER TABLE computed_load_metrics DROP COLUMN IF EXISTS pipeline_version;
ALTER TABLE computed_load_metrics RENAME COLUMN strain TO strain_value;

-- Phase 3 롤백: RLS 원복 (00003 원본 패턴)
-- training_sessions
DROP POLICY IF EXISTS "sessions_read_own_or_team" ON training_sessions;
DROP POLICY IF EXISTS "sessions_insert_own" ON training_sessions;
DROP POLICY IF EXISTS "sessions_update_own" ON training_sessions;
DROP POLICY IF EXISTS "sessions_delete_admin" ON training_sessions;
CREATE POLICY "sessions_read_own" ON training_sessions FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "sessions_insert_own" ON training_sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "sessions_update_own" ON training_sessions FOR UPDATE
  USING (user_id = auth.uid());

-- (pre_wellness, post_feedback, next_day도 동일 패턴으로 원복 — 생략)

-- Phase 2 롤백
ALTER TABLE post_session_feedback
  DROP CONSTRAINT IF EXISTS post_session_feedback_session_rpe_check;
ALTER TABLE post_session_feedback
  ADD CONSTRAINT post_session_feedback_session_rpe_check
  CHECK (session_rpe BETWEEN 1 AND 10);

-- Phase 1 롤백: has_* 플래그, user_id 복원은 데이터 손실 위험
-- ⚠ user_id 재추가 + 기존 데이터로부터 값 복원 필요
-- ⚠ has_* 플래그 재추가 + 기존 데이터로부터 값 복원 필요
-- → 이 단계는 seed_insert.sql 실행 전에만 안전

ALTER TABLE pre_session_wellness
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE post_session_feedback
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE next_day_reviews
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE training_sessions
  ADD COLUMN IF NOT EXISTS has_pre_wellness BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS has_post_feedback BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS has_next_day_review BOOLEAN DEFAULT FALSE;

-- Phase 0 롤백: UNIQUE 제약 원복
DROP INDEX IF EXISTS idx_sessions_user_match;
ALTER TABLE training_sessions
  ADD CONSTRAINT training_sessions_user_id_match_id_key
  UNIQUE NULLS NOT DISTINCT (user_id, match_id);

COMMIT;
```

### 15.3 롤백 주의사항

| 조건 | 롤백 안전성 | 비고 |
|------|:----------:|------|
| 00005 실행 직후, 데이터 미삽입 | ✅ 안전 | 스키마 변경만 원복 |
| seed_insert.sql 실행 후 | ⚠️ 부분 안전 | user_id 복원에 JOIN 기반 UPDATE 필요 |
| 서비스 앱에서 실제 데이터 입력 후 | ❌ 위험 | has_* 플래그 값 복원 불가, user_id 재매핑 필요 |

---

## 16. 리스크 매트릭스

### 16.1 수정 전 리스크

| ID | 발생 가능성 | 영향도 | 리스크 수준 | 비고 |
|:--:|:----------:|:------:|:----------:|------|
| B-01 | **확실** | **치명** | **극심** | 실제 DB 적용 시 100% 발현 |
| B-02 | 중간 | 높음 | **높음** | 악의적 입력 또는 클라이언트 버그 시 |
| B-04 | **확실** | 높음 | **높음** | ETL 뷰 사용 시 100% 발현 |
| B-05 | **확실** | 중간 | **높음** | 코치 대시보드 구현 시 100% 발현 |
| B-20 | **확실** | 중간 | **높음** | 프로덕션 전환 시 100% 발현 (PoV에서는 허용) |
| B-03 | 중간 | 중간 | 중간 | 트랜잭션 부분 실패 시 |
| B-06 | 낮음 | 낮음 | 낮음 | RPE=0 입력 빈도 낮음 |
| B-11 | 낮음 | 중간 | 중간 | NIGHT_SLEEP 대량 데이터 유입 시 |
| B-21 | 중간 | 중간 | 중간 | 데이터 삭제 요청 시 |
| B-25 | 중간 | 중간 | 중간 | valid 미지정 INSERT 시 |

### 16.2 수정 후 잔여 리스크

| 영역 | 잔여 리스크 | 대응 |
|------|-------------|------|
| CASCADE 삭제 | 사용자 삭제 시 대량 행 소실 | soft delete 도입 검토 (다음 마이그레이션) |
| RLS 서브쿼리 성능 | 팀 규모 확대 시 team_members 스캔 증가 | materialized 역할 뷰 또는 캐싱 검토 |
| phone 평문 | 개인정보 보호 | pgcrypto 또는 앱 레벨 암호화 (B-18, P3) |
| 익명화 미적용 | PoV 단계에서 UUID 직접 노출 | Phase 2에서 SHA-256 적용 필수 (B-20) |
| Surrogate Key | 불필요한 인덱스 유지 | Supabase 호환성 확인 후 처리 (B-08, P2) |

---

## 17. 검증 매트릭스 및 테스트 전략 (v2.0 신규)

### 17.1 버그별 검증 매트릭스

| ID | 검증 유형 | 검증 SQL/명령 | 기대 결과 | 자동화 |
|:--:|:---------:|-------------|-----------|:------:|
| B-01 | 삽입 테스트 | match_id=NULL 2건 INSERT | 둘 다 성공 | SQL |
| B-01 | 중복 방지 | 동일 match_id 2건 INSERT | 두 번째 실패 | SQL |
| B-02 | 무결성 | user_id 컬럼 부재 확인 | `\d pre_session_wellness`에 user_id 없음 | SQL |
| B-03 | 스키마 | has_* 컬럼 부재 확인 | `\d training_sessions`에 has_* 없음 | SQL |
| B-04 | ETL 결과 | `SELECT * FROM v_rnd_track_b WHERE session_type='REST'` | 행 존재, srpe=0 | SQL |
| B-05 | RLS | ADMIN으로 타 사용자 세션 조회 | 성공 | SQL |
| B-05 | RLS | MEMBER로 타 사용자 세션 조회 | 차단 (0행) | SQL |
| B-06 | 삽입 | RPE=0 INSERT | 성공 | SQL |
| B-09 | 스키마 | pipeline_version, params 컬럼 확인 | 존재 | SQL |
| B-11 | 삽입 | 60,000개 배열 INSERT | CHECK 실패 | SQL |
| B-12 | ETL | `EXPLAIN SELECT * FROM v_rnd_track_b` | Sort 단계 없음 | SQL |
| B-13 | 인덱스 | `EXPLAIN SELECT * FROM training_sessions WHERE session_date = ...` | Index Scan 사용 | SQL |
| B-14 | 트리거 | UPDATE 후 updated_at 변경 확인 | updated_at > created_at | SQL |
| B-20 | ETL | TODO 주석 존재 확인 | 뷰 정의에 SHA-256 TODO 포함 | SQL |
| B-21 | RLS | ADMIN DELETE 시도 | 성공 | SQL |
| B-21 | RLS | MEMBER DELETE 시도 | 차단 | SQL |
| B-22 | ETL | `SELECT dcwr_rolling FROM v_rnd_track_a LIMIT 1` | 컬럼 존재 | SQL |
| B-24 | ETL | `SELECT strain FROM v_rnd_track_a LIMIT 1` | 컬럼 존재 | SQL |
| B-25 | 삽입 | valid 미지정 INSERT | DEFAULT TRUE 적용 | SQL |
| 전체 | 파이프라인 | `python -m pytest tests/ -v` | 99개 통과 | pytest |

### 17.2 R&D 파이프라인 통합 테스트

| 단계 | 명령 | 기대 결과 |
|------|------|-----------|
| 1 | `python scripts/generate_seed_data.py` | CSV 5개 생성 |
| 2 | `python scripts/export_seed_sql.py` | seed_insert.sql 생성 |
| 3 | DB에 seed_insert.sql 적용 | ~1,800 세션 삽입 성공 |
| 4 | `SELECT COUNT(*) FROM v_rnd_track_b` | ~1,800행 (REST 포함) |
| 5 | `SELECT COUNT(*) FROM v_rnd_track_a` | ~1,800행 |
| 6 | `load_seed_track_b()` → `compute_daily_load_metrics()` | ACWR/Monotony 산출 |
| 7 | `lag_correlation_table()` | lag 0~7 상관 테이블 |
| 8 | `fit_random_intercept("hooper ~ acwr + monotony", ...)` | 모형 적합 성공 |
| 9 | `loso_cv()` | LOSO CV 완료, 15 fold |

---

## 18. 권고 사항 및 후속 조치

### 18.1 즉시 조치 (00005 마이그레이션)

| # | 조치 | 담당 | 기한 |
|:-:|------|:----:|:----:|
| 1 | 00005_schema_fixes.sql 작성 및 로컬 검증 | DBA | 즉시 |
| 2 | export_seed_sql.py에서 user_id 제거 반영 (B-02) | DE | 즉시 |
| 3 | generate_seed_data.py에서 REST일 sRPE=0 명시 검증 (B-04) | DE | 즉시 |
| 4 | supabase_loader.py에서 v_rnd_track_a 확장 컬럼 반영 (B-22, B-24) | DE | 즉시 |
| 5 | 기존 87개 + 신규 12개 테스트 통과 재확인 | DE | 즉시 |

### 18.2 단기 조치 (다음 스프린트)

| # | 조치 | 담당 |
|:-:|------|:----:|
| 1 | ADR-012 (ENUM vs CHECK 기준) 작성 | DBA + DE |
| 2 | DATA_SCHEMA_MAPPING.md에 soreness↔doms 매핑 명시 | DE |
| 3 | user_profiles 분리 정당성 ADR 또는 users 병합 결정 | DBA |
| 4 | Surrogate Key 정책 결정 (Supabase id 컨벤션 확인) | DBA |
| 5 | 00005_rollback.sql 로컬 검증 (순방향/역방향 반복 테스트) | DBA |

### 18.3 중기 조치 (프로덕션 전환 전)

| # | 조치 | 담당 | 관련 |
|:-:|------|:----:|:----:|
| 1 | **SHA-256 익명화 구현** (pgcrypto + salt 테이블) | DBA + DE | B-20 |
| 2 | phone 암호화 구현 (pgcrypto 또는 앱 레벨) | DBA + 보안 | B-18 |
| 3 | soft delete 패턴 도입 검토 (CASCADE 위험 완화) | DBA | — |
| 4 | computed_load_metrics 이력 테이블 설계 | DE | B-09 |
| 5 | daily_hrv_metrics 대표 측정 선택 규칙 문서화 + 자동화 | DE | B-10 |
| 6 | RLS 서브쿼리 성능 벤치마크 (100명+ 시나리오) | DBA | B-05 |

---

## 19. 부록

### 19.1 용어 정의

| 용어 | 정의 |
|------|------|
| **ACWR** | Acute:Chronic Workload Ratio. ATL/CTL. |
| **ATL** | Acute Training Load. 7일 평균 부하. |
| **CTL** | Chronic Training Load. 28일 평균 부하. |
| **sRPE** | Session Rating of Perceived Exertion. RPE × 운동 시간(분). |
| **DCWR** | Differential ACWR. ATL − CTL 차분 방식. |
| **TSB** | Training Stress Balance. CTL − ATL. 양수=회복 상태. |
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
| **pgcrypto** | PostgreSQL 암호화 확장. SHA-256, AES 등 제공. |
| **CASCADE** | FK ON DELETE CASCADE. 부모 행 삭제 시 자식 행 자동 삭제. |
| **SET NULL** | FK ON DELETE SET NULL. 부모 행 삭제 시 자식의 FK 컬럼을 NULL로. |

### 19.2 참조 문서

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
| DRD v1.0 | `soccer_rnd/docs/DRD_v1.0.md` |
| 품질 기준 | `soccer_rnd/CLAUDE.md` |

### 19.3 관련 ADR

| ADR | 제목 | DRD 관련 항목 |
|-----|------|:------------:|
| ADR-004 | 결측 처리 원칙 | B-04 (REST일 sRPE=0) |
| ADR-007 | 합성 데모 데이터 전략 | B-01 (CSV 방식으로 미발견) |
| ADR-011 | 대안 지표 DCWR/TSB | B-22 (사장 컬럼) |
| ADR-012 (신규 제안) | ENUM vs CHECK 기준 | B-15 |
| ADR-013 (신규 제안) | 익명화 전략 및 PoV 예외 범위 | B-20 |
| ADR-014 (신규 제안) | DELETE 정책 기준 (감사 추적 vs 삭제 허용) | B-21 |

### 19.4 v1.0 → v2.0 변경 추적

| 섹션 | v1.0 | v2.0 변경 |
|------|------|-----------|
| 1. Executive Summary | 19건 발견 | **25건 발견**, v2.0 신규 사항 요약표 추가 |
| 2. 방법론 | 7단계 | **11단계** (컴플라이언스, 성능 모델링, 롤백, 리니지 추가) |
| 3. 아키텍처 | 테이블 목록 | **ER 다이어그램**, 데이터 리니지 (컬럼 수준 추적) 추가 |
| 4. 컴플라이언스 | 없음 | **신규**: data_migration.md 대비 20항목 감사 |
| 6. 발견 총괄 | 19건 | **25건** (B-20~B-25 추가) |
| 8. P1 상세 | B-03~B-06 | **B-20 추가** (ETL 익명화 미구현) |
| 9. P2 상세 | B-07~B-14 | **B-21, B-22 추가** (DELETE 정책, 사장 컬럼) |
| 10. P3 상세 | B-15~B-19 | **B-23, B-24, B-25 추가** (FK 불일치, strain 미노출, valid DEFAULT) |
| 11. 횡단 관심사 | RLS 매트릭스 | **FK 일관성 매트릭스** 추가 |
| 12. 성능 모델링 | 없음 | **신규**: 볼륨 예측, 쿼리 비용, TOAST 분석 |
| 14. 마이그레이션 | 12단계 | **15단계**, `BEGIN`~`COMMIT` 트랜잭션 래핑, B-20~B-25 수정 포함 |
| 15. 롤백 | 없음 | **신규**: 역방향 SQL + 조건별 안전성 분석 |
| 17. 검증 | 체크리스트 8개 | **20항목 검증 매트릭스** + R&D 통합 테스트 9단계 |
| 18. 권고 | 12항목 | **16항목** (B-20 프로덕션 전환 로드맵 포함) |
| 19. 부록 | 용어 15개, ADR 3개 | **용어 19개, ADR 6개** (신규 제안 3개) |

---

*본 문서는 DB Architecture팀과 Data Engineering팀의 공동 리뷰 결과를 기록한다. 00005 수정 마이그레이션 적용 전까지 00003/00004의 프로덕션 배포를 보류할 것을 권고한다. 특히 B-20(익명화)은 프로덕션 전환의 필수 선행 조건으로, PoV 단계에서의 예외를 ADR-013으로 공식 기록할 것을 제안한다.*

# Database Design Review Document (DRD) v3.0

## 훈련·웰니스·HRV 스키마 — DB EDA 종합 다이어그램 및 에이전트 팀 리뷰

---

### 문서 정보

| 항목 | 내용 |
|------|------|
| **문서 ID** | DRD-2026-001 |
| **버전** | 3.0 |
| **작성일** | 2026-02-11 |
| **최종 수정** | 2026-02-11 |
| **작성** | DB Architecture팀 (DBA Senior), Data Engineering팀 (DE Senior), Team Leader |
| **검토 대상** | `00003_training_wellness_schema.sql`, `00004_etl_views.sql`, `00005_schema_fixes.sql` |
| **관련 프로젝트** | `soccer` (서비스 MVP), `soccer_rnd` (R&D 분석 파이프라인) |
| **배포 범위** | 사내 전체 (개발팀, PM, 보안팀) |

---

### 문서 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|:----:|------|--------|-----------|
| 0.1 | 2026-02-11 | DE | db_bug_report.md 초안 작성 |
| 1.0 | 2026-02-11 | DBA + DE | 공동 리뷰 결과 통합, 수정 SQL 확정, 마이그레이션 계획 수립 |
| 2.0 | 2026-02-11 | DBA + DE | 신규 6건 발견(B-20~B-25), 컴플라이언스 감사, ER 다이어그램, 성능 모델링, 롤백 절차 |
| **3.0** | **2026-02-11** | **Team Leader + DBA Sr. + DE Sr.** | **Mermaid EDA 전체 다이어그램 체계화, 에이전트 팀 구성 JSON, 횡단 관심사 시각화, 수정 후 목표 아키텍처 ER, 데이터 리니지 시각화** |

---

## 목차

1. [에이전트 팀 구성](#1-에이전트-팀-구성)
2. [DB EDA — 현행 ER 다이어그램 (Mermaid)](#2-db-eda--현행-er-다이어그램)
3. [DB EDA — 수정 후 목표 ER 다이어그램 (Mermaid)](#3-db-eda--수정-후-목표-er-다이어그램)
4. [데이터 흐름도 (Mermaid)](#4-데이터-흐름도)
5. [데이터 리니지 — Track B (Mermaid)](#5-데이터-리니지--track-b)
6. [데이터 리니지 — Track A (Mermaid)](#6-데이터-리니지--track-a)
7. [RLS 정책 매트릭스 (Mermaid)](#7-rls-정책-매트릭스)
8. [CASCADE 체인 시각화 (Mermaid)](#8-cascade-체인-시각화)
9. [버그 심각도 분포 (Mermaid)](#9-버그-심각도-분포)
10. [마이그레이션 위상 의존성 (Mermaid)](#10-마이그레이션-위상-의존성)
11. [성능 모델링 시각화 (Mermaid)](#11-성능-모델링-시각화)
12. [ENUM 타입 관계도 (Mermaid)](#12-enum-타입-관계도)
13. [팀 리뷰 결론](#13-팀-리뷰-결론)

---

## 1. 에이전트 팀 구성

### 1.1 팀 구조

```mermaid
graph TD
    TL["🎯 Team Leader<br/>총괄 지휘·의사결정"]
    TL --> DBA_SR["🛡️ DBA Senior<br/>DB 아키텍처·보안·성능"]
    TL --> DE_SR["⚙️ DE Senior<br/>데이터 엔지니어링·ETL·파이프라인"]
    DBA_SR --> DBA1["DBA-1<br/>스키마·제약·정규화"]
    DBA_SR --> DBA2["DBA-2<br/>RLS·보안·암호화"]
    DBA_SR --> DBA3["DBA-3<br/>성능·인덱스·TOAST"]
    DE_SR --> DE1["DE-1<br/>ETL 뷰·데이터 리니지"]
    DE_SR --> DE2["DE-2<br/>파이프라인 통합·검증"]
    DE_SR --> DE3["DE-3<br/>시드 데이터·재현성"]
```

### 1.2 에이전트 팀 JSON

```json
{
  "team": {
    "name": "Soccer DB Architecture Review Team",
    "version": "3.0",
    "project": "soccer / soccer_rnd",
    "created": "2026-02-11",
    "leader": {
      "id": "TL-001",
      "role": "Team Leader",
      "name": "팀 리더",
      "responsibilities": [
        "리뷰 방향 총괄 지휘",
        "DBA·DE 간 의견 조율 및 최종 의사결정",
        "마이그레이션 승인·롤백 판단",
        "리스크 매트릭스 최종 서명",
        "프로덕션 배포 게이트 관리"
      ],
      "authority": "FINAL_DECISION",
      "reports_to": "CTO"
    },
    "members": [
      {
        "id": "DBA-SR-001",
        "role": "DBA Senior",
        "name": "시니어 DBA",
        "specialty": "DB Architecture & Security",
        "reports_to": "TL-001",
        "responsibilities": [
          "스키마 설계 리뷰 총괄 (정규화, 제약, FK 전략)",
          "RLS 정책 설계 및 보안 감사",
          "성능 모델링 및 인덱스 전략",
          "마이그레이션 SQL 작성 및 트랜잭션 안전성 검증",
          "롤백 절차 설계 및 테스트",
          "CASCADE 체인 위험도 분석"
        ],
        "tools": ["PostgreSQL 15+", "pgcrypto", "EXPLAIN ANALYZE", "pg_stat"],
        "team": [
          {
            "id": "DBA-001",
            "role": "DBA Specialist",
            "name": "DBA-1 스키마·정규화",
            "focus": [
              "정적 DDL 분석 (P0: B-01, B-02)",
              "정규화 검증 (B-07, B-08)",
              "UNIQUE 제약 및 Partial Index 설계",
              "GENERATED STORED 컬럼 검증",
              "ENUM vs CHECK 기준 수립 (B-15)"
            ],
            "assigned_bugs": ["B-01", "B-02", "B-03", "B-07", "B-08", "B-15"]
          },
          {
            "id": "DBA-002",
            "role": "DBA Specialist",
            "name": "DBA-2 보안·RLS",
            "focus": [
              "RLS 정책 일관성 감사 (B-05)",
              "팀 기반 역할 계층 RLS 설계",
              "DELETE 정책 설계 (B-21)",
              "phone 암호화 요건 (B-18)",
              "SHA-256 익명화 전략 (B-20)"
            ],
            "assigned_bugs": ["B-05", "B-18", "B-19", "B-20", "B-21"]
          },
          {
            "id": "DBA-003",
            "role": "DBA Specialist",
            "name": "DBA-3 성능·인덱스",
            "focus": [
              "인덱스 커버리지 분석 (B-13)",
              "TOAST 영향 분석 (B-11)",
              "쿼리 비용 추정 (EXPLAIN 기반)",
              "RLS 서브쿼리 성능 벤치마크",
              "볼륨별 성능 예측 (PoV → 프로덕션)"
            ],
            "assigned_bugs": ["B-11", "B-12", "B-13", "B-14"]
          }
        ]
      },
      {
        "id": "DE-SR-001",
        "role": "DE Senior",
        "name": "시니어 데이터 엔지니어",
        "specialty": "Data Engineering & ETL Pipeline",
        "reports_to": "TL-001",
        "responsibilities": [
          "ETL 뷰 설계 리뷰 총괄",
          "데이터 리니지 추적 (컬럼 수준)",
          "R&D 파이프라인 통합 검증",
          "data_migration.md 컴플라이언스 감사",
          "합성 데이터 생성·검증 전략",
          "파이프라인 추적성 (CLAUDE.md 품질 기준)"
        ],
        "tools": ["Python", "pandas", "SQLAlchemy", "pytest", "statsmodels"],
        "team": [
          {
            "id": "DE-001",
            "role": "DE Specialist",
            "name": "DE-1 ETL·리니지",
            "focus": [
              "v_rnd_track_b REST일 포함 (B-04)",
              "v_rnd_track_a strain/DCWR/TSB 노출 (B-22, B-24)",
              "컬럼 수준 데이터 리니지 추적",
              "ETL 뷰 ORDER BY 제거 (B-12)",
              "soreness↔doms 매핑 문서화 (B-17)"
            ],
            "assigned_bugs": ["B-04", "B-12", "B-17", "B-22", "B-24"]
          },
          {
            "id": "DE-002",
            "role": "DE Specialist",
            "name": "DE-2 파이프라인·통합",
            "focus": [
              "load_seed_track_a/b() 통합 검증",
              "ACWR/Monotony/Strain 산출 정합성",
              "혼합효과모형 적합 테스트",
              "LOSO CV 15 fold 완료 검증",
              "파이프라인 버전 추적 (B-09)"
            ],
            "assigned_bugs": ["B-06", "B-09", "B-10", "B-16"]
          },
          {
            "id": "DE-003",
            "role": "DE Specialist",
            "name": "DE-3 시드·재현성",
            "focus": [
              "generate_seed_data.py 검증",
              "export_seed_sql.py user_id 제거 반영",
              "합성 데이터 품질 (REST sRPE=0 명시)",
              "시드 데이터 멱등성 테스트",
              "valid DEFAULT 반영 (B-25)"
            ],
            "assigned_bugs": ["B-23", "B-25"]
          }
        ]
      }
    ],
    "workflow": {
      "phases": [
        {
          "phase": 1,
          "name": "정적 분석",
          "lead": "DBA-SR-001",
          "participants": ["DBA-001", "DBA-002", "DBA-003"],
          "deliverable": "DDL 결함 목록 + 정규화 리포트"
        },
        {
          "phase": 2,
          "name": "ETL·리니지 분석",
          "lead": "DE-SR-001",
          "participants": ["DE-001", "DE-002", "DE-003"],
          "deliverable": "ETL 결함 목록 + 리니지 매핑"
        },
        {
          "phase": 3,
          "name": "보안·RLS 감사",
          "lead": "DBA-SR-001",
          "participants": ["DBA-002", "DE-001"],
          "deliverable": "RLS 매트릭스 + 보안 권고"
        },
        {
          "phase": 4,
          "name": "성능 모델링",
          "lead": "DBA-SR-001",
          "participants": ["DBA-003", "DE-002"],
          "deliverable": "쿼리 비용 추정 + TOAST 분석"
        },
        {
          "phase": 5,
          "name": "컴플라이언스 감사",
          "lead": "DE-SR-001",
          "participants": ["DBA-001", "DE-001"],
          "deliverable": "data_migration.md 대비 적합률 리포트"
        },
        {
          "phase": 6,
          "name": "수정 마이그레이션",
          "lead": "DBA-SR-001",
          "participants": ["ALL"],
          "deliverable": "00005_schema_fixes.sql + 롤백 SQL"
        },
        {
          "phase": 7,
          "name": "통합 검증",
          "lead": "DE-SR-001",
          "participants": ["ALL"],
          "deliverable": "20항목 검증 매트릭스 + 99 pytest 통과"
        },
        {
          "phase": 8,
          "name": "Mermaid EDA 시각화",
          "lead": "TL-001",
          "participants": ["DBA-SR-001", "DE-SR-001"],
          "deliverable": "DRD v3.0 Mermaid 다이어그램 전체"
        }
      ],
      "decision_protocol": {
        "minor": "DBA Sr. 또는 DE Sr. 단독 결정",
        "major": "DBA Sr. + DE Sr. 합의 → TL 승인",
        "critical": "TL 직접 판단 + CTO 보고"
      }
    },
    "bug_assignments": {
      "total": 25,
      "by_severity": {
        "P0_critical": { "count": 2, "ids": ["B-01", "B-02"], "owner": "DBA-SR-001" },
        "P1_high":     { "count": 5, "ids": ["B-03", "B-04", "B-05", "B-06", "B-20"], "owner": "DBA-SR-001 + DE-SR-001" },
        "P2_medium":   { "count": 10, "ids": ["B-07", "B-08", "B-09", "B-10", "B-11", "B-12", "B-13", "B-14", "B-21", "B-22"], "owner": "분산" },
        "P3_low":      { "count": 8, "ids": ["B-15", "B-16", "B-17", "B-18", "B-19", "B-23", "B-24", "B-25"], "owner": "분산" }
      }
    }
  }
}
```

---

## 2. DB EDA — 현행 ER 다이어그램

### 2.1 전체 ER 다이어그램 (현행 — 00003/00004 기준)

> DBA Senior 분석: 현행 스키마의 15개 테이블, 5개 ENUM, FK 체인, 버그 위치를 시각화한다.

```mermaid
erDiagram
    %% ============================================================
    %% 기존 테이블 (00001 마이그레이션)
    %% ============================================================

    users {
        UUID id PK "기본키"
        TEXT email UK "UNIQUE"
        TEXT name
        TEXT avatar_url
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    teams {
        UUID id PK
        TEXT name
        UUID created_by FK "→ users"
        TIMESTAMPTZ created_at
    }

    team_members {
        UUID id PK
        UUID team_id FK "→ teams"
        UUID user_id FK "→ users"
        team_role role "ENUM: ADMIN MANAGER MEMBER GUEST"
        TIMESTAMPTZ created_at
    }

    matches {
        UUID id PK
        UUID team_id FK "→ teams"
        UUID created_by FK "→ users"
        match_status status "ENUM"
        DATE match_date
        TEXT location
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    attendances {
        UUID id PK
        UUID match_id FK "→ matches"
        UUID user_id FK "→ users"
        attendance_status status "ENUM"
    }

    record_rooms {
        UUID id PK
        UUID match_id FK UK "→ matches UNIQUE"
        record_room_status status "ENUM"
    }

    match_records {
        UUID id PK
        UUID room_id FK "→ record_rooms"
        UUID user_id FK "→ users"
    }

    %% ============================================================
    %% 신규 테이블 (00003 마이그레이션)
    %% ============================================================

    user_profiles {
        UUID id PK
        UUID user_id FK UK "→ users UNIQUE (1:1)"
        TEXT phone "B-18: 평문 저장"
        TEXT position "CHECK 14종"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at "B-14: 트리거 없음"
    }

    training_sessions {
        UUID id PK
        UUID user_id FK "→ users"
        UUID team_id FK "→ teams"
        UUID match_id FK "→ matches NULL OK"
        session_type session_type "ENUM"
        DATE session_date
        FLOAT duration_min
        BOOLEAN has_pre_wellness "B-03: 파생 플래그"
        BOOLEAN has_post_feedback "B-03: 파생 플래그"
        BOOLEAN has_next_day_review "B-03: 파생 플래그"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    pre_session_wellness {
        UUID id PK
        UUID session_id FK UK "→ training_sessions UNIQUE"
        UUID user_id FK "B-02: 이중 저장"
        SMALLINT fatigue "CHECK 1-7"
        SMALLINT soreness "CHECK 1-7 B-17: doms 불일치"
        SMALLINT stress "CHECK 1-7"
        SMALLINT sleep "CHECK 1-7"
        INT hooper_index "GENERATED STORED"
    }

    post_session_feedback {
        UUID id PK
        UUID session_id FK UK "→ training_sessions UNIQUE"
        UUID user_id FK "B-02: 이중 저장"
        SMALLINT session_rpe "CHECK 1-10 B-06: 0 누락"
        post_condition condition "ENUM"
        TEXT memo
    }

    next_day_reviews {
        UUID id PK
        UUID session_id FK UK "→ training_sessions UNIQUE"
        UUID user_id FK "B-02: 이중 저장"
        next_day_condition condition "ENUM"
        TEXT memo
    }

    hrv_measurements {
        UUID id PK
        UUID user_id FK "→ users CASCADE"
        UUID session_id FK "→ sessions SET NULL B-23"
        hrv_source source "ENUM 5종"
        hrv_context context "ENUM 6종"
        FLOAT_ARRAY rr_intervals_ms "B-11: 크기 무제한"
        INT rr_count "GENERATED STORED"
        TEXT quality_flag
        TIMESTAMPTZ measured_at
    }

    daily_hrv_metrics {
        UUID id PK
        UUID user_id FK "→ users CASCADE"
        UUID measurement_id FK "→ hrv_measurements SET NULL B-10"
        DATE metric_date
        FLOAT rmssd
        FLOAT sdnn
        FLOAT ln_rmssd
        FLOAT ln_rmssd_7d
        FLOAT mean_hr
        INT nn_count
        BOOLEAN valid "B-25: DEFAULT 없음"
    }

    computed_load_metrics {
        UUID id PK
        UUID user_id FK "→ users CASCADE"
        DATE metric_date
        FLOAT daily_load
        FLOAT atl_rolling
        FLOAT ctl_rolling
        FLOAT acwr_rolling
        FLOAT atl_ewma
        FLOAT ctl_ewma
        FLOAT acwr_ewma
        FLOAT monotony
        FLOAT strain_value "B-16: strain과 불일치"
        FLOAT dcwr_rolling "B-22: ETL 미노출"
        FLOAT tsb_rolling "B-22: ETL 미노출"
        FLOAT hooper_index "B-22: 중복"
    }

    %% ============================================================
    %% ETL 뷰 (00004 마이그레이션)
    %% ============================================================

    v_rnd_track_b {
        TEXT athlete_id "B-20: UUID 평문"
        DATE date
        SMALLINT rpe
        FLOAT duration_min
        FLOAT srpe
        SMALLINT fatigue
        SMALLINT stress
        SMALLINT doms
        SMALLINT sleep
        INT hooper_index
        TEXT session_type
        BOOLEAN match_day
        INT next_day_score
    }

    v_rnd_track_a {
        TEXT subject_id "B-20: UUID 평문"
        DATE date
        FLOAT rmssd
        FLOAT sdnn
        FLOAT ln_rmssd
        FLOAT ln_rmssd_7d
        FLOAT mean_hr
        INT nn_count
        FLOAT acwr_rolling
        FLOAT acwr_ewma
        FLOAT monotony
        FLOAT srpe
    }

    %% ============================================================
    %% 관계 정의
    %% ============================================================

    users ||--o| user_profiles : "1:1"
    users ||--o{ training_sessions : "1:N"
    users ||--o{ hrv_measurements : "1:N"
    users ||--o{ daily_hrv_metrics : "1:N"
    users ||--o{ computed_load_metrics : "1:N"
    users ||--o{ team_members : "1:N"
    users ||--o{ attendances : "1:N"
    users ||--o{ match_records : "1:N"

    teams ||--o{ team_members : "1:N"
    teams ||--o{ training_sessions : "1:N"
    teams ||--o{ matches : "1:N"

    matches ||--o| record_rooms : "1:1"
    matches ||--o{ attendances : "1:N"
    matches ||--o{ training_sessions : "0:N match_id NULL OK"

    record_rooms ||--o{ match_records : "1:N"

    training_sessions ||--o| pre_session_wellness : "1:1"
    training_sessions ||--o| post_session_feedback : "1:1"
    training_sessions ||--o| next_day_reviews : "1:1"
    training_sessions ||--o{ hrv_measurements : "1:N SET NULL"

    hrv_measurements ||--o| daily_hrv_metrics : "N:1 대표 측정"

    %% ETL 뷰 소스
    training_sessions }|--|| v_rnd_track_b : "ETL 소스"
    pre_session_wellness }|--|| v_rnd_track_b : "LEFT JOIN"
    post_session_feedback }|--|| v_rnd_track_b : "LEFT JOIN"
    next_day_reviews }|--|| v_rnd_track_b : "LEFT JOIN"

    daily_hrv_metrics }|--|| v_rnd_track_a : "ETL 소스"
    computed_load_metrics }|--|| v_rnd_track_a : "LEFT JOIN"
```

### 2.2 핵심 테이블 상세 ER (00003 스키마 집중)

```mermaid
erDiagram
    TRAINING_SESSIONS {
        UUID id PK
        UUID user_id FK
        UUID team_id FK
        UUID match_id FK "NULL 허용"
        session_type type "TRAINING MATCH REST OTHER"
        DATE session_date
        FLOAT duration_min
        BOOLEAN has_pre_wellness "삭제 대상 B-03"
        BOOLEAN has_post_feedback "삭제 대상 B-03"
        BOOLEAN has_next_day_review "삭제 대상 B-03"
    }

    PRE_SESSION_WELLNESS {
        UUID id PK "B-08: 불필요 surrogate"
        UUID session_id FK_UK "UNIQUE"
        UUID user_id FK "B-02: 제거 대상"
        SMALLINT fatigue "1-7"
        SMALLINT soreness "1-7"
        SMALLINT stress "1-7"
        SMALLINT sleep "1-7"
        INT hooper_index "GENERATED = sum(4항목)"
    }

    POST_SESSION_FEEDBACK {
        UUID id PK "B-08: 불필요 surrogate"
        UUID session_id FK_UK "UNIQUE"
        UUID user_id FK "B-02: 제거 대상"
        SMALLINT session_rpe "CHECK 1-10 → 0-10"
        post_condition condition
        TEXT memo
    }

    NEXT_DAY_REVIEWS {
        UUID id PK "B-08: 불필요 surrogate"
        UUID session_id FK_UK "UNIQUE"
        UUID user_id FK "B-02: 제거 대상"
        next_day_condition condition "WORSE SAME BETTER"
        TEXT memo
    }

    TRAINING_SESSIONS ||--o| PRE_SESSION_WELLNESS : "1:1 CASCADE"
    TRAINING_SESSIONS ||--o| POST_SESSION_FEEDBACK : "1:1 CASCADE"
    TRAINING_SESSIONS ||--o| NEXT_DAY_REVIEWS : "1:1 CASCADE"
```

---

## 3. DB EDA — 수정 후 목표 ER 다이어그램

> Team Leader 지시: 00005_schema_fixes.sql 적용 후의 목표 상태를 별도 다이어그램으로 시각화하라.

```mermaid
erDiagram
    %% ============================================================
    %% 수정 후 목표 상태 (00005 적용 후)
    %% ============================================================

    users {
        UUID id PK
        TEXT email UK
        TEXT name
        TEXT avatar_url
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    teams {
        UUID id PK
        TEXT name
        UUID created_by FK
    }

    team_members {
        UUID id PK
        UUID team_id FK
        UUID user_id FK
        team_role role
    }

    matches {
        UUID id PK
        UUID team_id FK
        UUID created_by FK
        match_status status
        DATE match_date
    }

    user_profiles {
        UUID id PK
        UUID user_id FK_UK "1:1"
        TEXT phone "TODO: AES-256 암호화"
        TEXT position "CHECK 14종"
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at "트리거 자동 갱신"
    }

    training_sessions {
        UUID id PK
        UUID user_id FK
        UUID team_id FK
        UUID match_id FK "NULL OK"
        session_type type "ENUM"
        DATE session_date "단독 인덱스 추가"
        FLOAT duration_min
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at "트리거 자동 갱신"
    }

    pre_session_wellness {
        UUID id PK
        UUID session_id FK_UK "UNIQUE - RLS 경유"
        SMALLINT fatigue "1-7"
        SMALLINT soreness "1-7"
        SMALLINT stress "1-7"
        SMALLINT sleep "1-7"
        INT hooper_index "GENERATED"
    }

    post_session_feedback {
        UUID id PK
        UUID session_id FK_UK "UNIQUE - RLS 경유"
        SMALLINT session_rpe "CHECK 0-10 Borg CR-10"
        post_condition condition
        TEXT memo
    }

    next_day_reviews {
        UUID id PK
        UUID session_id FK_UK "UNIQUE - RLS 경유"
        next_day_condition condition
        TEXT memo
    }

    hrv_measurements {
        UUID id PK
        UUID user_id FK "CASCADE"
        UUID session_id FK "SET NULL 의도적"
        hrv_source source
        hrv_context context
        FLOAT_ARRAY rr_intervals_ms "CHECK 1-50000"
        INT rr_count "GENERATED"
        TEXT quality_flag
    }

    daily_hrv_metrics {
        UUID id PK
        UUID user_id FK
        UUID measurement_id FK "SET NULL"
        DATE metric_date UK
        FLOAT rmssd
        FLOAT sdnn
        FLOAT ln_rmssd
        FLOAT ln_rmssd_7d
        FLOAT mean_hr
        INT nn_count
        BOOLEAN valid "DEFAULT TRUE NOT NULL"
    }

    computed_load_metrics {
        UUID id PK
        UUID user_id FK
        DATE metric_date UK
        FLOAT daily_load
        FLOAT atl_rolling
        FLOAT ctl_rolling
        FLOAT acwr_rolling
        FLOAT atl_ewma
        FLOAT ctl_ewma
        FLOAT acwr_ewma
        FLOAT monotony
        FLOAT strain "이름 통일"
        FLOAT dcwr_rolling
        FLOAT tsb_rolling
        FLOAT hooper_index
        TEXT pipeline_version "추적성 추가"
        JSONB params "파라미터 기록"
    }

    v_rnd_track_b_fixed {
        TEXT athlete_id "TODO SHA-256"
        DATE date
        SMALLINT rpe
        FLOAT duration_min
        FLOAT srpe "COALESCE 0"
        SMALLINT fatigue
        SMALLINT stress
        SMALLINT doms
        SMALLINT sleep
        INT hooper_index
        TEXT session_type "REST 포함"
        BOOLEAN match_day
        INT next_day_score
    }

    v_rnd_track_a_fixed {
        TEXT subject_id "TODO SHA-256"
        DATE date
        FLOAT rmssd
        FLOAT sdnn
        FLOAT ln_rmssd
        FLOAT ln_rmssd_7d
        FLOAT mean_hr
        INT nn_count
        FLOAT acwr_rolling
        FLOAT acwr_ewma
        FLOAT monotony
        FLOAT strain "추가"
        FLOAT dcwr_rolling "추가"
        FLOAT tsb_rolling "추가"
        FLOAT srpe
    }

    %% 관계 (수정 후)
    users ||--o| user_profiles : "1:1"
    users ||--o{ training_sessions : "1:N"
    users ||--o{ hrv_measurements : "1:N"
    users ||--o{ daily_hrv_metrics : "1:N"
    users ||--o{ computed_load_metrics : "1:N"

    teams ||--o{ team_members : "1:N"
    teams ||--o{ training_sessions : "1:N"

    matches ||--o{ training_sessions : "0:N"

    training_sessions ||--o| pre_session_wellness : "1:1 CASCADE"
    training_sessions ||--o| post_session_feedback : "1:1 CASCADE"
    training_sessions ||--o| next_day_reviews : "1:1 CASCADE"
    training_sessions ||--o{ hrv_measurements : "1:N SET NULL"

    hrv_measurements ||--o| daily_hrv_metrics : "N:1"

    training_sessions }|--|| v_rnd_track_b_fixed : "ETL"
    pre_session_wellness }|--|| v_rnd_track_b_fixed : "JOIN"
    post_session_feedback }|--|| v_rnd_track_b_fixed : "JOIN"
    next_day_reviews }|--|| v_rnd_track_b_fixed : "JOIN"

    daily_hrv_metrics }|--|| v_rnd_track_a_fixed : "ETL"
    computed_load_metrics }|--|| v_rnd_track_a_fixed : "JOIN"
```

---

## 4. 데이터 흐름도

### 4.1 서비스 입력 → DB → ETL → R&D 파이프라인

```mermaid
flowchart LR
    subgraph INPUT["서비스 입력"]
        APP["사용자 앱<br/>(훈련·웰니스)"]
        WEAR["웨어러블<br/>(HRV 측정)"]
        BATCH["배치 파이프라인<br/>(부하 지표 산출)"]
    end

    subgraph DB["PostgreSQL / Supabase"]
        TS["training_sessions"]
        PW["pre_session_wellness"]
        PF["post_session_feedback"]
        ND["next_day_reviews"]
        HRV["hrv_measurements"]
        DHM["daily_hrv_metrics"]
        CLM["computed_load_metrics"]
    end

    subgraph ETL["ETL 뷰 계층"]
        VB["v_rnd_track_b<br/>(부하+웰니스)"]
        VA["v_rnd_track_a<br/>(HRV+부하)"]
    end

    subgraph RND["R&D 파이프라인"]
        LB["load_seed_track_b()"]
        LA["load_seed_track_a()"]
        COMPUTE["compute_daily_load_metrics()"]
        LAG["lag_correlation_table()"]
        FIT_B["fit_random_intercept()<br/>hooper ~ acwr + monotony"]
        FIT_A["fit_random_intercept()<br/>HRV ~ ACWR"]
        LOSO["loso_cv()"]
        REPORT["PoV 보고서"]
    end

    APP --> TS
    APP --> PW
    APP --> PF
    APP --> ND
    WEAR --> HRV
    HRV --> DHM
    BATCH --> CLM

    TS --> VB
    PW --> VB
    PF --> VB
    ND --> VB

    DHM --> VA
    CLM --> VA

    VB --> LB
    LB --> COMPUTE
    COMPUTE --> LAG
    LAG --> FIT_B
    FIT_B --> LOSO

    VA --> LA
    LA --> FIT_A
    FIT_A --> LOSO

    LOSO --> REPORT
```

### 4.2 RLS 보안 계층

```mermaid
flowchart TB
    subgraph AUTH["인증 계층"]
        UID["auth.uid()"]
    end

    subgraph RLS_CHECK["RLS 정책 평가"]
        OWN["본인 확인<br/>user_id = auth.uid()"]
        TEAM["팀 확인<br/>team_members 서브쿼리"]
        ROLE["역할 확인<br/>ADMIN / MANAGER"]
    end

    subgraph TABLES["테이블 접근"]
        S_OWN["SELECT 본인 데이터"]
        S_TEAM["SELECT 팀 데이터"]
        I_OWN["INSERT 본인 데이터"]
        U_OWN["UPDATE 본인 데이터"]
        D_ADMIN["DELETE ADMIN만"]
    end

    UID --> OWN
    UID --> TEAM
    TEAM --> ROLE

    OWN -->|일치| S_OWN
    OWN -->|일치| I_OWN
    OWN -->|일치| U_OWN
    ROLE -->|ADMIN/MGR| S_TEAM
    ROLE -->|ADMIN| D_ADMIN
```

---

## 5. 데이터 리니지 — Track B

> DE Senior 분석: 서비스 DB 컬럼 → ETL 변환 → R&D 스키마 → 파이프라인 출력까지 추적.

```mermaid
flowchart LR
    subgraph SVC_DB["서비스 DB 컬럼"]
        TS_UID["ts.user_id<br/>(UUID)"]
        TS_DATE["ts.session_date<br/>(DATE)"]
        TS_DUR["ts.duration_min<br/>(FLOAT)"]
        TS_TYPE["ts.session_type<br/>(ENUM)"]
        PS_RPE["ps.session_rpe<br/>(SMALLINT)"]
        PW_FAT["pw.fatigue<br/>(SMALLINT 1-7)"]
        PW_SOR["pw.soreness<br/>(SMALLINT 1-7)"]
        PW_STR["pw.stress<br/>(SMALLINT 1-7)"]
        PW_SLP["pw.sleep<br/>(SMALLINT 1-7)"]
        ND_COND["nd.condition<br/>(ENUM)"]
    end

    subgraph ETL_TRANSFORM["ETL 변환"]
        ANON["::text AS athlete_id<br/>TODO: SHA-256"]
        DATE_MAP["AS date"]
        RPE_MAP["AS rpe"]
        DUR_MAP["AS duration_min"]
        SRPE_CALC["COALESCE(rpe * dur, 0)<br/>AS srpe"]
        FAT_MAP["AS fatigue"]
        SOR_MAP["AS doms<br/>B-17: 이름 변환"]
        STR_MAP["AS stress"]
        SLP_MAP["AS sleep"]
        SCORE["CASE WORSE=3<br/>SAME=2 BETTER=1"]
    end

    subgraph RND_SCHEMA["R&D 스키마"]
        R_AID["athlete_id (str)"]
        R_DATE["date (datetime)"]
        R_RPE["rpe (float)"]
        R_SRPE["srpe (float)"]
        R_FAT["fatigue [1-7]"]
        R_DOMS["doms [1-7]"]
        R_STR["stress [1-7]"]
        R_SLP["sleep [1-7]"]
        R_NDS["next_day_score"]
    end

    subgraph PIPELINE["파이프라인 출력"]
        P_GROUP["GROUP BY key"]
        P_ATL["ATL (7일)"]
        P_CTL["CTL (28일)"]
        P_ACWR["ACWR = ATL/CTL"]
        P_MONO["Monotony"]
        P_STRAIN["Strain"]
        P_HOOPER["Hooper Index"]
        P_MODEL["혼합효과모형"]
    end

    TS_UID --> ANON --> R_AID --> P_GROUP
    TS_DATE --> DATE_MAP --> R_DATE
    PS_RPE --> RPE_MAP --> R_RPE
    TS_DUR --> DUR_MAP
    RPE_MAP --> SRPE_CALC
    DUR_MAP --> SRPE_CALC
    SRPE_CALC --> R_SRPE --> P_ATL --> P_ACWR --> P_MODEL
    R_SRPE --> P_CTL --> P_ACWR
    R_SRPE --> P_MONO --> P_MODEL
    P_MONO --> P_STRAIN
    PW_FAT --> FAT_MAP --> R_FAT --> P_HOOPER
    PW_SOR --> SOR_MAP --> R_DOMS --> P_HOOPER
    PW_STR --> STR_MAP --> R_STR --> P_HOOPER
    PW_SLP --> SLP_MAP --> R_SLP --> P_HOOPER
    ND_COND --> SCORE --> R_NDS
```

---

## 6. 데이터 리니지 — Track A

```mermaid
flowchart LR
    subgraph SVC_DB["서비스 DB 컬럼"]
        H_UID["h.user_id<br/>(UUID)"]
        H_DATE["h.metric_date<br/>(DATE)"]
        H_RMSSD["h.rmssd<br/>(FLOAT)"]
        H_SDNN["h.sdnn<br/>(FLOAT)"]
        H_LN["h.ln_rmssd<br/>(FLOAT)"]
        H_LN7["h.ln_rmssd_7d<br/>(FLOAT)"]
        M_ACWR_R["m.acwr_rolling"]
        M_ACWR_E["m.acwr_ewma"]
        M_MONO["m.monotony"]
        M_STRAIN["m.strain<br/>B-24: 미노출"]
        M_DCWR["m.dcwr_rolling<br/>B-22: 미노출"]
        M_TSB["m.tsb_rolling<br/>B-22: 미노출"]
        M_LOAD["m.daily_load"]
    end

    subgraph ETL["ETL 변환"]
        ANON_A["::text AS subject_id<br/>TODO: SHA-256"]
        PASS["직접 매핑"]
        SRPE_MAP["daily_load AS srpe"]
        STRAIN_ADD["strain 노출 추가"]
        DCWR_ADD["dcwr/tsb 노출 추가"]
    end

    subgraph RND["R&D 스키마"]
        R_SID["subject_id"]
        R_RMSSD["rmssd"]
        R_SDNN["sdnn"]
        R_LN["ln_rmssd"]
        R_LN7["ln_rmssd_7d"]
        R_ACWR["acwr_rolling"]
        R_ACWRE["acwr_ewma"]
        R_MONO["monotony"]
        R_STRAIN["strain"]
        R_DCWR["dcwr_rolling"]
        R_TSB["tsb_rolling"]
        R_SRPE["srpe"]
    end

    subgraph PIPELINE["파이프라인"]
        MODEL_A["혼합효과모형<br/>HRV_t+1 ~ ACWR_t"]
        SENS["ACWR_RA vs ACWR_EWMA<br/>민감도 비교"]
        TREND["평활 추세 분석"]
    end

    H_UID --> ANON_A --> R_SID
    H_DATE --> PASS
    H_RMSSD --> PASS --> R_RMSSD
    H_SDNN --> PASS --> R_SDNN
    H_LN --> PASS --> R_LN --> MODEL_A
    H_LN7 --> PASS --> R_LN7 --> TREND
    M_ACWR_R --> PASS --> R_ACWR --> MODEL_A
    M_ACWR_E --> PASS --> R_ACWRE --> SENS
    M_MONO --> PASS --> R_MONO
    M_STRAIN --> STRAIN_ADD --> R_STRAIN
    M_DCWR --> DCWR_ADD --> R_DCWR
    M_TSB --> DCWR_ADD --> R_TSB
    M_LOAD --> SRPE_MAP --> R_SRPE
```

---

## 7. RLS 정책 매트릭스

### 7.1 현행 vs 수정 후 RLS 비교

```mermaid
block-beta
    columns 7

    space:1 block:header:6
        columns 6
        h1["SELECT"] h2["INSERT"] h3["UPDATE"] h4["DELETE"] h5["패턴"] h6["상태"]
    end

    block:row_users:7
        columns 7
        t1["users (00001)"]
        s1["본인"] i1["본인"] u1["본인"] d1["---"] p1["본인"] st1["OK"]
    end

    block:row_teams:7
        columns 7
        t2["teams (00001)"]
        s2["팀"] i2["인증"] u2["ADMIN"] d2["ADMIN"] p2["역할"] st2["OK"]
    end

    block:row_sessions_before:7
        columns 7
        t3["sessions 현행"]
        s3["본인"] i3["본인"] u3["본인"] d3["없음"] p3["본인만"] st3["B-05,21"]
    end

    block:row_sessions_after:7
        columns 7
        t4["sessions 수정후"]
        s4["팀기반"] i4["본인"] u4["본인"] d4["ADMIN"] p4["역할"] st4["OK"]
    end

    style row_sessions_before fill:#ffcccc
    style row_sessions_after fill:#ccffcc
```

### 7.2 RLS 팀 기반 접근 흐름도

```mermaid
flowchart TD
    REQ["데이터 접근 요청"]
    AUTH["auth.uid() 확인"]
    IS_OWN{"본인 데이터?<br/>user_id = auth.uid()"}
    IS_TEAM{"같은 팀?<br/>team_members 조회"}
    IS_ADMIN{"역할 확인<br/>ADMIN / MANAGER?"}

    GRANT_READ["SELECT 허용"]
    GRANT_WRITE["INSERT/UPDATE 허용"]
    GRANT_DELETE["DELETE 허용"]
    DENY["접근 거부"]

    REQ --> AUTH --> IS_OWN
    IS_OWN -->|예| GRANT_READ
    IS_OWN -->|예| GRANT_WRITE
    IS_OWN -->|아니오| IS_TEAM
    IS_TEAM -->|아니오| DENY
    IS_TEAM -->|예| IS_ADMIN
    IS_ADMIN -->|ADMIN/MGR| GRANT_READ
    IS_ADMIN -->|ADMIN| GRANT_DELETE
    IS_ADMIN -->|MEMBER| DENY
```

---

## 8. CASCADE 체인 시각화

> DBA Senior 경고: 사용자 1명 삭제 시 최대 ~780행 CASCADE 삭제.

```mermaid
flowchart TD
    USER_DEL["users DELETE<br/>1행"]

    UP["user_profiles<br/>CASCADE → 1행 삭제"]
    TS["training_sessions<br/>CASCADE → ~120행 삭제"]
    CLM["computed_load_metrics<br/>CASCADE → ~120행 삭제"]
    HRV_U["hrv_measurements<br/>CASCADE(user_id) → ~120행 삭제"]
    DHM["daily_hrv_metrics<br/>CASCADE → ~120행 삭제"]

    PW["pre_session_wellness<br/>CASCADE → ~100행 삭제"]
    PF["post_session_feedback<br/>CASCADE → ~100행 삭제"]
    ND["next_day_reviews<br/>CASCADE → ~100행 삭제"]
    HRV_S["hrv_measurements<br/>SET NULL(session_id)"]

    USER_DEL --> UP
    USER_DEL --> TS
    USER_DEL --> CLM
    USER_DEL --> HRV_U
    USER_DEL --> DHM

    TS --> PW
    TS --> PF
    TS --> ND
    TS --> HRV_S

    TOTAL["합계: ~780행 CASCADE 삭제<br/>soft delete 미도입 상태"]

    PW --> TOTAL
    PF --> TOTAL
    ND --> TOTAL
    CLM --> TOTAL
    HRV_U --> TOTAL
    DHM --> TOTAL

    style USER_DEL fill:#ff6b6b,color:#fff
    style TOTAL fill:#ff6b6b,color:#fff
    style HRV_S fill:#ffd93d
```

---

## 9. 버그 심각도 분포

### 9.1 심각도별 분포

```mermaid
pie title 발견 사항 심각도 분포 (25건)
    "P0 치명 (2건)" : 2
    "P1 높음 (5건)" : 5
    "P2 중간 (10건)" : 10
    "P3 낮음 (8건)" : 8
```

### 9.2 분류별 분포

```mermaid
pie title 발견 사항 분류별 분포 (25건)
    "보안·RLS·프라이버시 (5건)" : 5
    "정규화·모델링 (4건)" : 4
    "성능·인덱스 (3건)" : 3
    "무결성·제약 (2건)" : 2
    "비즈니스 로직 (2건)" : 2
    "컨벤션·명명 (3건)" : 3
    "ETL·리니지 (2건)" : 2
    "추적성 (1건)" : 1
    "운영 (1건)" : 1
    "스키마 기본값 (2건)" : 2
```

### 9.3 버전별 발견 추이

```mermaid
xychart-beta
    title "버전별 발견 사항 누적"
    x-axis ["v1.0", "v2.0"]
    y-axis "건수" 0 --> 30
    bar [19, 25]
    line [19, 25]
```

---

## 10. 마이그레이션 위상 의존성

> Team Leader 지시: 00005 수정 마이그레이션의 15단계 위상 의존성을 시각화하라.

```mermaid
flowchart TD
    subgraph P1["Phase 1: P0 치명 수정"]
        B01["1. B-01<br/>UNIQUE → Partial Index"]
        B02["2. B-02<br/>user_id 이중 저장 제거"]
    end

    subgraph P2["Phase 2: P1 비즈니스 로직"]
        B03["3. B-03<br/>has_* 플래그 제거"]
        B06["4. B-06<br/>RPE CHECK 0-10"]
    end

    subgraph P3["Phase 3: RLS 재구축"]
        RLS_TS["5. training_sessions<br/>팀 기반 RLS"]
        RLS_PW["6. pre_session_wellness<br/>session 경유 RLS"]
        RLS_PF["7. post_session_feedback<br/>session 경유 RLS"]
        RLS_ND["8. next_day_reviews<br/>session 경유 RLS"]
        RLS_CLM["9. computed_load_metrics<br/>팀 SELECT + UPDATE"]
        RLS_HRV["10. hrv_measurements<br/>팀 SELECT + DELETE"]
        RLS_DHM["11. daily_hrv_metrics<br/>팀 SELECT + DELETE"]
        RLS_UP["12. user_profiles<br/>DELETE 추가"]
    end

    subgraph P4["Phase 4: 구조 개선"]
        B09["13. B-09/B-16<br/>추적성 + strain 이름"]
        B11["14. B-11<br/>배열 크기 제한"]
        B13["15. B-13<br/>session_date 인덱스"]
        B25["16. B-25<br/>valid DEFAULT"]
    end

    subgraph P5["Phase 5: ETL 뷰"]
        VB_FIX["17. v_rnd_track_b<br/>REST 포함 + ORDER BY 제거"]
        VA_FIX["18. v_rnd_track_a<br/>strain/DCWR/TSB 추가"]
    end

    subgraph P6["Phase 6: 운영"]
        TRIGGER["19. updated_at 트리거"]
        COMMENT["20. FK 근거 COMMENT"]
    end

    %% 의존성
    B01 --> B03
    B02 --> RLS_PW
    B02 --> RLS_PF
    B02 --> RLS_ND
    B03 --> RLS_TS
    B06 --> VB_FIX
    RLS_TS --> VB_FIX
    RLS_TS --> VA_FIX
    B09 --> VA_FIX
    B25 --> VA_FIX
    VB_FIX --> TRIGGER
    VA_FIX --> TRIGGER
    TRIGGER --> COMMENT

    style P1 fill:#ff6b6b22,stroke:#ff6b6b
    style P2 fill:#ffa50022,stroke:#ffa500
    style P3 fill:#4dabf722,stroke:#4dabf7
    style P4 fill:#51cf6622,stroke:#51cf66
    style P5 fill:#cc5de822,stroke:#cc5de8
    style P6 fill:#86868622,stroke:#868686
```

---

## 11. 성능 모델링 시각화

### 11.1 데이터 볼륨 예측

```mermaid
xychart-beta
    title "테이블별 예상 행 수 (로그 스케일 아님)"
    x-axis ["users", "sessions", "wellness", "feedback", "reviews", "load_metrics", "hrv_meas", "daily_hrv"]
    y-axis "행 수 (PoV)" 0 --> 2000
    bar [15, 1800, 1300, 1300, 1300, 1800, 1800, 1800]
```

### 11.2 TOAST 저장 영향 — hrv_measurements

```mermaid
flowchart LR
    subgraph CONTEXT["HRV 측정 컨텍스트"]
        MR["MORNING_REST<br/>5분 = ~350 beats"]
        PRE["PRE_SESSION<br/>2분 = ~150 beats"]
        POST["POST_SESSION<br/>2분 = ~150 beats"]
        NIGHT["NIGHT_SLEEP<br/>8시간 = ~30,000 beats"]
        MALICIOUS["악의적 입력<br/>제한 없음 = 100만+"]
    end

    subgraph SIZE["배열 크기"]
        S1["~2.8KB"]
        S2["~1.2KB"]
        S3["~1.2KB"]
        S4["~240KB"]
        S5["~8MB"]
    end

    subgraph STORAGE["저장 방식"]
        INLINE["인라인 저장"]
        TOAST["TOAST 외부 저장"]
        DANGER["심각한 I/O 부하"]
    end

    MR --> S1 --> INLINE
    PRE --> S2 --> INLINE
    POST --> S3 --> INLINE
    NIGHT --> S4 --> TOAST
    MALICIOUS --> S5 --> DANGER

    subgraph FIX["B-11 수정"]
        CHECK["CHECK 1~50,000<br/>최대 ~400KB/행"]
    end

    DANGER -.->|차단| CHECK

    style DANGER fill:#ff6b6b,color:#fff
    style CHECK fill:#51cf66,color:#fff
```

---

## 12. ENUM 타입 관계도

```mermaid
flowchart TD
    subgraph ENUM_00001["기존 ENUM (00001)"]
        TR["team_role<br/>ADMIN MANAGER<br/>MEMBER GUEST"]
        MS["match_status<br/>OPEN CONFIRMED<br/>COMPLETED CANCELLED"]
        AS_E["attendance_status<br/>PENDING ACCEPTED<br/>DECLINED MAYBE"]
        RRS["record_room_status<br/>OPEN CLOSED"]
    end

    subgraph ENUM_00003["신규 ENUM (00003)"]
        ST["session_type<br/>TRAINING MATCH<br/>REST OTHER"]
        PC["post_condition<br/>VERY_BAD BAD NEUTRAL<br/>GOOD VERY_GOOD"]
        NDC["next_day_condition<br/>WORSE SAME BETTER"]
        HS["hrv_source<br/>CHEST_STRAP SMARTWATCH<br/>FINGER_SENSOR APP_MANUAL<br/>EXTERNAL_IMPORT"]
        HC["hrv_context<br/>MORNING_REST PRE_SESSION<br/>POST_SESSION DURING_SESSION<br/>NIGHT_SLEEP OTHER"]
    end

    subgraph CHECK_CONST["CHECK 제약 (B-15: 혼재)"]
        POS["position<br/>CHECK IN 14종<br/>GK CB LB RB ...]"]
        HOOPER["fatigue/soreness<br/>stress/sleep<br/>CHECK 1-7"]
        RPE["session_rpe<br/>CHECK 0-10"]
    end

    TR --> |team_members| TM_TABLE["team_members.role"]
    MS --> |matches| M_TABLE["matches.status"]
    AS_E --> |attendances| A_TABLE["attendances.status"]
    RRS --> |record_rooms| RR_TABLE["record_rooms.status"]
    ST --> |training_sessions| TS_TABLE["training_sessions.session_type"]
    PC --> |post_feedback| PF_TABLE["post_session_feedback.condition"]
    NDC --> |next_day| ND_TABLE["next_day_reviews.condition"]
    HS --> |hrv| HRV_TABLE["hrv_measurements.source"]
    HC --> |hrv| HRV_TABLE2["hrv_measurements.context"]
    POS --> |user_profiles| UP_TABLE["user_profiles.position"]

    style ENUM_00001 fill:#e3f2fd
    style ENUM_00003 fill:#e8f5e9
    style CHECK_CONST fill:#fff3e0
```

---

## 13. 팀 리뷰 결론

### 13.1 Team Leader 총평

```mermaid
flowchart TD
    subgraph STATUS["DRD v3.0 종합 상태"]
        direction TB
        TOTAL["총 25건 발견<br/>v1.0: 19건 → v2.0: 25건"]
        P0["P0 치명: 2건<br/>B-01, B-02<br/>프로덕션 배포 차단"]
        P1["P1 높음: 5건<br/>B-03~B-06, B-20<br/>PoV 데모 전 수정 필수"]
        P2["P2 중간: 10건<br/>B-07~B-14, B-21, B-22<br/>00006에서 처리"]
        P3["P3 낮음: 8건<br/>B-15~B-19, B-23~B-25<br/>백로그"]
    end

    subgraph COMPLIANCE["컴플라이언스"]
        FUNC["기능: 50% 완전적합"]
        SEC["보안: 20% 완전적합"]
        QUAL["품질: 60% 완전적합"]
    end

    subgraph ACTION["조치 계획"]
        IMM["즉시: 00005 마이그레이션<br/>15단계 수정 SQL"]
        SHORT["단기: ADR-012~014 작성<br/>매핑 문서화"]
        MID["중기: SHA-256 익명화<br/>phone 암호화<br/>soft delete"]
    end

    TOTAL --> P0
    TOTAL --> P1
    TOTAL --> P2
    TOTAL --> P3

    P0 --> IMM
    P1 --> IMM
    P2 --> SHORT
    P3 --> SHORT

    SEC --> MID

    style P0 fill:#ff6b6b,color:#fff
    style P1 fill:#ffa500,color:#fff
    style SEC fill:#ff6b6b,color:#fff
```

### 13.2 DBA Senior 결론

| 영역 | 평가 | 비고 |
|------|:----:|------|
| 스키마 골격 | 양호 | 8개 핵심 테이블 구조 적절, GENERATED STORED 활용 우수 |
| 무결성 | **치명 결함** | B-01 UNIQUE NULLS NOT DISTINCT, B-02 user_id 이중 저장 |
| 보안 (RLS) | **취약** | 00001 역할 기반 패턴과 00003 본인 전용 패턴 불일치, DELETE 전면 부재 |
| 성능 | 양호 | PoV 규모에서 문제 없음, 프로덕션 확장 시 B-11/B-13 수정 필수 |
| CASCADE | 주의 | 사용자 삭제 시 ~780행 연쇄 삭제, soft delete 검토 필요 |

### 13.3 DE Senior 결론

| 영역 | 평가 | 비고 |
|------|:----:|------|
| ETL 뷰 아키텍처 | 우수 | 서비스 ↔ R&D 분리 캡슐화 적절 |
| REST일 처리 | **결함** | B-04 ACWR 40% 과대추정 위험 |
| 데이터 리니지 | 부분 완성 | B-22/B-24 사장 컬럼, strain 미노출 |
| 익명화 | **미구현** | B-20 프로덕션 전환 필수 선행 조건 |
| 추적성 | 부족 | B-09 파이프라인 버전/파라미터 미기록, CLAUDE.md 품질 기준 위반 |
| R&D 정합성 | 양호 | Track A/B 파이프라인과 스키마 구조 호환 |

### 13.4 최종 판정

> **Team Leader 판정**: 00005_schema_fixes.sql 미적용 상태에서 프로덕션 배포를 **금지**한다.
> P0 2건(B-01, B-02)은 운영 환경 적용 즉시 장애를 유발하며, P1 5건은 PoV 목적 달성을 직접 저해한다.
> DBA Senior와 DE Senior는 00005 마이그레이션을 즉시 작성·검증하고, 20항목 검증 매트릭스를 통과한 후 TL에게 승인을 요청할 것.

---

*본 문서는 Team Leader 지휘 하에 DBA Senior 팀(3명)과 DE Senior 팀(3명)이 공동 작성한 DB EDA 종합 다이어그램 및 리뷰 결과이다. 모든 Mermaid 다이어그램은 DRD v2.0의 25건 발견 사항과 수정 마이그레이션 계획을 시각적으로 추적할 수 있도록 설계되었다.*

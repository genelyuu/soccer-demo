# 데이터 통합 마이그레이션 계획

> **대상**: `C:\dev\soccer` (서비스 MVP) ↔ `C:\dev\soccer_rnd` (R&D 분석)
> **작성일**: 2026-02-10
> **목적**: 두 프로젝트의 데이터 구조를 통합하여, 서비스에서 수집한 훈련·웰니스 데이터가 R&D 분석 파이프라인으로 자연스럽게 흐르는 단일 데이터 아키텍처를 설계한다.

---

## 1. 현황 진단

### 1.1 soccer (서비스 MVP) — 현재 스키마

| 테이블 | 핵심 컬럼 | 역할 |
|--------|-----------|------|
| `users` | id(UUID), email, name, avatar_url | 사용자 식별 |
| `teams` | id, name, created_by(FK→users) | 팀 관리 |
| `team_members` | team_id, user_id, role(ENUM) | 역할 기반 멤버십 |
| `matches` | id, team_id, match_date, status(ENUM) | 경기 운영 |
| `attendances` | match_id, user_id, status(ENUM) | 출석 투표 |
| `record_rooms` | match_id(UNIQUE), status | 경기 기록실 |
| `match_records` | record_room_id, user_id, goals, assists, cards | 경기 성적 기록 |

**기술 스택**: PostgreSQL(Supabase), Next.js 15, TypeScript, NextAuth, Zod

**현재 부재 요소**:
- 훈련 세션(training session) 개념 자체가 없음
- 주관적 상태(웰니스/컨디션) 수집 체계 없음
- HRV(심박 변이도) 데이터 수집/저장 체계 없음
- 선수 포지션 등 프로필 확장 필드 없음
- 부하 지표(ACWR, Monotony 등) 산출 기반 없음

### 1.2 soccer_rnd (R&D) — 현재 데이터 구조

| 스키마 | 핵심 컬럼 | 역할 |
|--------|-----------|------|
| 트랙 A 표준 | subject_id, session_id, rr_interval_ms, power_watts | HRV + 운동 부하 |
| 트랙 B 표준 | athlete_id, date, rpe, duration_min, srpe, fatigue/stress/doms/sleep | 부하 + 웰니스 |

**지표 모듈**: ACWR(Rolling/EWMA), Monotony, Strain, sRPE, Hooper Index, DCWR, TSB, ACWR Uncoupled
**분석 모듈**: 다중 시차(lag 0~7), 혼합효과모형(랜덤 절편/기울기), LOSO 교차 검증

**현재 부재 요소**:
- 실제 사용자 인증/식별 체계 없음 (익명 ID만 사용)
- 팀/경기/역할 맥락 없음
- 실시간 데이터 수집 인터페이스 없음

### 1.3 갭(Gap) 분석 요약

| 영역 | soccer (서비스) | soccer_rnd (R&D) | 통합 필요 |
|------|:--:|:--:|:--:|
| 사용자 식별 | **있음** (UUID, email) | **없음** (익명 ID) | 매핑 필요 |
| 포지션 | **없음** | **없음** | **신규 추가** |
| 휴대폰 번호 | **없음** | **없음** | **신규 추가** |
| 팀 구조 | **있음** | **없음** | 서비스 측 활용 |
| 경기 관리 | **있음** | **없음** | 서비스 측 유지 |
| 훈련 세션 | **없음** | 합성 데이터만 | **신규 테이블** |
| 훈련 전 상태 | **없음** | Hooper 4항목 (트랙 B) | **신규 테이블** |
| 훈련 후 상태 | **없음** | sRPE (트랙 B) | **신규 테이블** |
| 다음 날 회고 | **없음** | lag-1 구조만 분석 | **신규 테이블** |
| HRV 원시 데이터 | **없음** | RR 간격 (트랙 A) | **신규 테이블** |
| HRV 일별 지표 | **없음** | rMSSD, SDNN, ln_rMSSD (트랙 A) | **신규 테이블** |
| 부하 지표 산출 | **없음** | **완비** (9모듈, 42함수+) | 연동 파이프라인 필요 |

---

## 2. 통합 데이터 모델 설계

### 2.1 설계 원칙

1. **자가 인식 중심**: MVP 단계에서는 사용자의 주관적 인식을 가장 신뢰 가능한 데이터로 간주한다.
2. **상태 변화 기록**: 단일 수치가 아닌, 훈련 전–후–다음 날의 흐름을 하나의 묶음으로 관리한다.
3. **입력 부담 최소화**: 모든 입력은 짧고 직관적인 선택 또는 한 줄 텍스트를 원칙으로 한다.
4. **확장 가능한 구조**: 현재는 단순한 주관 데이터이지만, 향후 자동 데이터·분석 로직 확장이 가능하도록 설계한다.
5. **R&D 호환성**: soccer_rnd의 트랙 B 표준 스키마(`athlete_id, date, rpe, duration_min, srpe, fatigue, stress, doms, sleep`)로 자연스럽게 변환 가능해야 한다.

### 2.2 ER 다이어그램 (통합)

```
┌──────────────────────────────────────────────────────────────────┐
│                    기존 soccer (서비스 MVP)                        │
│  ┌─────────┐    ┌──────────────┐    ┌─────────┐                  │
│  │  users   │───│ team_members │───│  teams   │                  │
│  │  (UUID)  │    │ (role ENUM)  │    │         │                  │
│  └────┬─────┘    └──────────────┘    └────┬────┘                  │
│       │                                   │                       │
│       │         ┌──────────┐              │                       │
│       ├────────│ matches   │─────────────┘                       │
│       │         │ (status)  │                                     │
│       │         └─────┬─────┘                                     │
│       │               │                                           │
│       │    ┌──────────┴──────────┐                                │
│       │    │                     │                                │
│       │  ┌─┴───────────┐  ┌─────┴──────────┐                     │
│       ├──│ attendances  │  │ record_rooms   │                     │
│       │  └─────────────┘  └──────┬─────────┘                     │
│       │                          │                                │
│       │                    ┌─────┴──────────┐                     │
│       └────────────────────│ match_records  │                     │
│                            └────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                  신규 추가 (훈련 + 웰니스)                          │
│                                                                   │
│  ┌───────────────────┐      ┌──────────────────────┐              │
│  │ user_profiles     │      │ training_sessions    │              │
│  │ (포지션, 휴대폰)   │      │ (훈련 세션 단위)       │              │
│  └────────┬──────────┘      └──────────┬───────────┘              │
│           │                            │                          │
│     users.id (FK)              users.id + teams.id (FK)          │
│                                        │                          │
│                  ┌─────────────────────┼────────────────────┐     │
│                  │                     │                    │     │
│          ┌───────┴─────────┐  ┌────────┴────────┐  ┌───────┴──┐  │
│          │ pre_session_    │  │ post_session_   │  │ next_day_ │  │
│          │ wellness        │  │ feedback        │  │ review    │  │
│          │ (훈련 전 상태)   │  │ (훈련 후 상태)    │  │ (다음날)   │  │
│          └─────────────────┘  └─────────────────┘  └──────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │ computed_load_metrics (산출 지표 — R&D 트랙 B 결과)        │     │
│  │ ACWR, Monotony, Strain, DCWR, TSB, Hooper Index          │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                   │
│  ┌──────────────────────┐      ┌─────────────────────────┐       │
│  │ hrv_measurements     │      │ daily_hrv_metrics       │       │
│  │ (RR 간격 원시 데이터)  │─────→│ (일별 rMSSD/SDNN/ln 등) │       │
│  │ 웨어러블/앱 연동       │      │ R&D 트랙 A 호환         │       │
│  └──────────────────────┘      └─────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 신규 테이블 정의

### 3.1 사용자 프로필 확장 — `user_profiles`

> **필요성**: 서비스 내에서 사용자를 구분하고, 훈련 데이터 및 상태 기록을 연속적으로 연결하기 위한 최소 식별 정보.

```sql
CREATE TABLE user_profiles (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- ① 사용자 기본 식별 및 맥락 데이터
  phone       TEXT,                       -- 휴대폰 번호 (AES-256 암호화, 출력 시 마스킹)
  position    TEXT CHECK (position IN (   -- 포지션 (Enum)
                'GK', 'CB', 'LB', 'RB', 'WB',
                'CDM', 'CM', 'CAM', 'LM', 'RM',
                'LW', 'RW', 'CF', 'ST'
              )),

  created_at  TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- RLS: 본인만 읽기/수정
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_profiles_own ON user_profiles
  USING (user_id = auth.uid());
```

| 항목 | 수집 방법 | 처리 방식 | 활용 |
|------|-----------|-----------|------|
| user_id | 시스템 자동 (users.id FK) | UUID, Primary 참조 | 모든 데이터의 기준 식별자 |
| phone | 사용자 직접 입력 (SMS 인증) | AES-256 암호화, 출력 시 마스킹 | 본인 인증 및 계정 복구 |
| position | 사전 정의 목록 선택 | Enum (14개 포지션) | 훈련 맥락 해석, 추천 분기 기준 |

**R&D 매핑**: `user_id` → `athlete_id` (또는 `subject_id`). 분석 시 UUID를 해시하여 익명화 ID 생성.

---

### 3.2 훈련 세션 — `training_sessions`

> **필요성**: 각 훈련을 "얼마나 했는가"가 아니라, **"어떤 상태에서 시작했고, 어떻게 느꼈는가"**로 기록하여 사용자 스스로의 컨디션 패턴과 회복 흐름을 인식할 수 있도록 한다.

```sql
CREATE TYPE session_type AS ENUM ('TRAINING', 'MATCH', 'REST', 'OTHER');

CREATE TABLE training_sessions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  team_id     UUID REFERENCES teams(id) ON DELETE SET NULL,
  match_id    UUID REFERENCES matches(id) ON DELETE SET NULL,

  -- 세션 기본 정보
  session_type  session_type NOT NULL DEFAULT 'TRAINING',
  session_date  DATE NOT NULL,
  duration_min  FLOAT,                -- 훈련/경기 시간 (분)

  -- 상태 플래그
  has_pre_wellness   BOOLEAN DEFAULT FALSE,
  has_post_feedback  BOOLEAN DEFAULT FALSE,
  has_next_day_review BOOLEAN DEFAULT FALSE,

  created_at  TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT now() NOT NULL,

  -- 사용자별 날짜당 세션은 복수 가능 (오전/오후 훈련)
  -- 하지만 같은 match_id에 대한 중복 세션은 방지
  UNIQUE NULLS NOT DISTINCT (user_id, match_id)
);

CREATE INDEX idx_sessions_user_date ON training_sessions(user_id, session_date);
CREATE INDEX idx_sessions_team ON training_sessions(team_id);
```

**설계 포인트**:
- `match_id` 연결: 경기(match) 세션은 기존 경기 테이블과 연결되어 맥락 보존
- `team_id` 연결: 팀 훈련인지, 개인 훈련인지 구분
- `has_*` 플래그: 3단계 입력(전/후/다음날) 완료 여부 추적 → 푸시 알림 트리거

---

### 3.3 훈련 전 데이터 — `pre_session_wellness`

> **필요성**: 각 훈련 세션에서 사용자가 느끼는 준비 상태를 기록. 서비스의 피드백·리포트·추천 기능의 기반이 되는 핵심 데이터.

```sql
CREATE TABLE pre_session_wellness (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- Hooper Index 호환 4항목 (1-7 스케일)
  fatigue     SMALLINT NOT NULL CHECK (fatigue BETWEEN 1 AND 7),
  soreness    SMALLINT NOT NULL CHECK (soreness BETWEEN 1 AND 7),   -- = DOMS
  stress      SMALLINT NOT NULL CHECK (stress BETWEEN 1 AND 7),
  sleep       SMALLINT NOT NULL CHECK (sleep BETWEEN 1 AND 7),      -- 높을수록 나쁨

  -- 산출 필드
  hooper_index SMALLINT GENERATED ALWAYS AS (fatigue + soreness + stress + sleep) STORED,

  -- 맥락 보완
  memo        TEXT,                    -- 훈련 전 컨디션 메모 (선택)

  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_pre_wellness_user ON pre_session_wellness(user_id, recorded_at);
```

| 항목 | 수집 방법 | 처리 | R&D 매핑 |
|------|-----------|------|----------|
| fatigue | 1-7점 척도 선택 | Integer | → `fatigue` (트랙 B) |
| soreness (근육통) | 1-7점 척도 선택 | Integer | → `doms` (트랙 B) |
| stress | 1-7점 척도 선택 | Integer | → `stress` (트랙 B) |
| sleep (수면 만족도) | 1-7점 척도 선택 | Integer | → `sleep` (트랙 B) |
| hooper_index | 자동 산출 | Integer (4-28) | → `hooper_index` (트랙 B) |
| memo | 선택적 텍스트 | Text | 정성 분석용 |

**R&D 호환성**: 이 테이블의 4항목은 soccer_rnd의 `hooper_index()` 함수(`src/metrics/monotony_strain.py`)와 완전히 호환된다.

---

### 3.4 훈련 후 데이터 — `post_session_feedback`

```sql
CREATE TYPE post_condition AS ENUM ('VERY_BAD', 'BAD', 'NEUTRAL', 'GOOD', 'VERY_GOOD');

CREATE TABLE post_session_feedback (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- 핵심 부하 지표
  session_rpe SMALLINT NOT NULL CHECK (session_rpe BETWEEN 1 AND 10),  -- CR-10 스케일

  -- 훈련 후 전체 컨디션 (5단계)
  condition   post_condition NOT NULL,

  -- 맥락 보완
  memo        TEXT,                    -- 훈련 후 메모 (선택)

  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_post_feedback_user ON post_session_feedback(user_id, recorded_at);
```

| 항목 | 수집 방법 | 처리 | R&D 매핑 |
|------|-----------|------|----------|
| session_rpe | 1-10점 척도 선택 | Integer (CR-10) | → `rpe` (트랙 B) |
| condition | 1-5단계 선택 | Enum | 추가 분석 변수 |
| memo | 한 줄 텍스트 | Text | 정성 분석용 |

**sRPE 산출**: `training_sessions.duration_min × post_session_feedback.session_rpe`로 계산.
이 값이 soccer_rnd의 `srpe()` 함수 결과와 동일하다.

---

### 3.5 다음 날 회고 — `next_day_reviews`

```sql
CREATE TYPE next_day_condition AS ENUM ('WORSE', 'SAME', 'BETTER');

CREATE TABLE next_day_reviews (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  -- 다음 날 컨디션 회고 (3단계)
  condition   next_day_condition NOT NULL,

  -- 맥락 보완
  memo        TEXT,                    -- 회복 관련 메모 (선택)

  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_next_day_user ON next_day_reviews(user_id, recorded_at);
```

| 항목 | 수집 방법 | 처리 | R&D 매핑 |
|------|-----------|------|----------|
| condition | 푸시 알림 → 3단계 선택 | Enum (WORSE/SAME/BETTER) | lag-1 종속변수 |
| memo | 선택적 텍스트 | Text | 회복 지연 맥락 |

**R&D 활용**: 이 데이터는 soccer_rnd의 시차 분석(`lag_analysis.py`)에서 `outcome_col`로 활용된다. `condition`을 수치화(WORSE=3, SAME=2, BETTER=1)하여 Hooper Index와 함께 종속변수로 사용할 수 있다.

---

### 3.6 산출 지표 캐시 — `computed_load_metrics`

> R&D 파이프라인의 산출물을 서비스 DB에 캐시하여 실시간 대시보드에 활용.

```sql
CREATE TABLE computed_load_metrics (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,

  -- 일별 부하 지표 (src/metrics/acwr.py 산출물)
  daily_load    FLOAT,          -- sRPE
  atl_rolling   FLOAT,          -- 급성 부하 (7일 Rolling)
  ctl_rolling   FLOAT,          -- 만성 부하 (28일 Rolling)
  acwr_rolling  FLOAT,          -- ACWR (Rolling)
  atl_ewma      FLOAT,          -- 급성 부하 (EWMA)
  ctl_ewma      FLOAT,          -- 만성 부하 (EWMA)
  acwr_ewma     FLOAT,          -- ACWR (EWMA)

  -- 단조성/부담 (src/metrics/monotony_strain.py 산출물)
  monotony      FLOAT,          -- 7일 Monotony
  strain_value  FLOAT,          -- Weekly Strain

  -- 대안 지표 (src/metrics/alternative_load.py 산출물)
  dcwr_rolling  FLOAT,          -- DCWR (Rolling)
  tsb_rolling   FLOAT,          -- TSB (Rolling)

  -- 웰니스 (pre_session_wellness 기반)
  hooper_index  SMALLINT,       -- 당일 Hooper Index

  -- 메타
  computed_at   TIMESTAMPTZ DEFAULT now() NOT NULL,

  UNIQUE(user_id, metric_date)
);

CREATE INDEX idx_metrics_user_date ON computed_load_metrics(user_id, metric_date DESC);
```

**산출 파이프라인**: 매일 배치 또는 세션 완료 시 트리거로 `src/data/preprocess.py::compute_daily_load_metrics()` 호출.

---

### 3.7 HRV 원시 측정 — `hrv_measurements` (트랙 A)

> **필요성**: 웨어러블 디바이스(심박 센서, 가슴 스트랩, 스마트워치)에서 수집한 RR 간격 원시 데이터를 저장하여, R&D 트랙 A 파이프라인(`filter_rr_outliers`, `compute_daily_hrv`)과 연동한다.

```sql
CREATE TYPE hrv_source AS ENUM (
  'CHEST_STRAP',     -- Polar H10 등 가슴 스트랩
  'SMARTWATCH',      -- Apple Watch, Garmin 등
  'FINGER_SENSOR',   -- Oura Ring 등
  'APP_MANUAL',      -- 앱에서 수동 입력
  'EXTERNAL_IMPORT'  -- CSV/API 외부 연동
);

CREATE TYPE hrv_context AS ENUM (
  'MORNING_REST',    -- 기상 후 안정 시 측정 (권장)
  'PRE_SESSION',     -- 훈련 전 측정
  'POST_SESSION',    -- 훈련 후 측정
  'DURING_SESSION',  -- 훈련 중 연속 측정
  'NIGHT_SLEEP',     -- 수면 중 측정
  'OTHER'
);

CREATE TABLE hrv_measurements (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id    UUID REFERENCES training_sessions(id) ON DELETE SET NULL,

  -- 측정 맥락
  source        hrv_source NOT NULL,
  context       hrv_context NOT NULL DEFAULT 'MORNING_REST',
  measured_at   TIMESTAMPTZ NOT NULL,
  duration_sec  INT,                    -- 측정 시간 (초)

  -- RR 간격 원시 데이터 (배열 형태로 저장)
  rr_intervals_ms  FLOAT[] NOT NULL,    -- beat-to-beat RR 간격 배열 (ms 단위)
  rr_count         INT GENERATED ALWAYS AS (array_length(rr_intervals_ms, 1)) STORED,

  -- 측정 품질 메타데이터
  device_name   TEXT,                   -- 디바이스명 (예: "Polar H10")
  firmware_ver  TEXT,                   -- 펌웨어 버전
  quality_flag  BOOLEAN DEFAULT TRUE,   -- 품질 필터 통과 여부

  created_at    TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_hrv_user_date ON hrv_measurements(user_id, measured_at DESC);
CREATE INDEX idx_hrv_session ON hrv_measurements(session_id);
```

| 항목 | 수집 방법 | R&D 매핑 |
|------|-----------|----------|
| rr_intervals_ms | 웨어러블 BLE/API 자동 전송 | → `rr_interval_ms` (트랙 A 표준) |
| source | 디바이스 연결 시 자동 설정 | 데이터 품질 판별용 |
| context | 사용자 선택 또는 세션 연동 자동 | → `session_id` / `phase` (트랙 A) |
| measured_at | 디바이스 타임스탬프 | → `timestamp` (트랙 A) |

**R&D 호환성**:
- `rr_intervals_ms` 배열을 `np.array`로 변환하면 `src/data/preprocess.py::filter_rr_outliers()`에 직접 입력 가능
- `rr_count >= 150`인 측정만 `src/metrics/hrv_features.py`의 `rmssd()`, `sdnn()`, `ln_rmssd()` 산출 가능 (min_count=150 규칙)
- `context='MORNING_REST'` 측정이 Plews et al. (2013)이 권장하는 표준 HRV 모니터링 프로토콜과 일치

**저장 전략**:
- RR 간격은 PostgreSQL ARRAY 타입으로 저장 (일반적으로 1~5분 측정 = 60~500개 값, ~4KB)
- 장시간 연속 측정(수면 중 등)은 별도 청크 분할 고려
- `quality_flag`는 `filter_rr_outliers()` 적용 후 이상치 비율 > 20%이면 FALSE 처리

---

### 3.8 일별 HRV 지표 — `daily_hrv_metrics` (트랙 A)

> **필요성**: `hrv_measurements`의 원시 RR 간격에서 `compute_daily_hrv()`로 산출한 일별 HRV 지표를 캐시. 서비스 대시보드와 R&D 시차 분석 양쪽에서 활용.

```sql
CREATE TABLE daily_hrv_metrics (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,

  -- 원본 측정 참조
  measurement_id UUID REFERENCES hrv_measurements(id) ON DELETE SET NULL,

  -- HRV 시간 영역 지표 (src/metrics/hrv_features.py 산출물)
  rmssd         FLOAT,          -- rMSSD (ms)
  sdnn          FLOAT,          -- SDNN (ms)
  ln_rmssd      FLOAT,          -- ln(rMSSD)
  mean_rr       FLOAT,          -- 평균 RR 간격 (ms)
  mean_hr       FLOAT,          -- 평균 심박수 (bpm) = 60000 / mean_rr

  -- Rolling 지표
  ln_rmssd_7d   FLOAT,          -- ln(rMSSD) 7일 Rolling Average

  -- 트랙 A 분석을 위한 부하 컨텍스트 (해당 세션이 있는 경우)
  session_load_watts FLOAT,     -- 세션 평균 power (W)

  -- 품질 메타
  nn_count      INT,            -- 유효 NN 간격 수
  valid         BOOLEAN DEFAULT TRUE,  -- nn_count >= 150 여부

  computed_at   TIMESTAMPTZ DEFAULT now() NOT NULL,

  UNIQUE(user_id, metric_date)
);

CREATE INDEX idx_daily_hrv_user ON daily_hrv_metrics(user_id, metric_date DESC);
```

| 항목 | 산출 방법 | R&D 함수 |
|------|-----------|----------|
| rmssd | `hrv_features.rmssd(nn, min_count=150)` | → 트랙 A EDA/통계 종속변수 |
| sdnn | `hrv_features.sdnn(nn, min_count=150)` | → 보조 HRV 지표 |
| ln_rmssd | `hrv_features.ln_rmssd(nn, min_count=150)` | → **핵심 종속변수** (정규화 HRV) |
| ln_rmssd_7d | `hrv_features.ln_rmssd_rolling(series, 7)` | → 추세 파악, SWC 모니터링 |
| mean_hr | `60000 / mean(rr_intervals_ms)` | → 보조 지표 |
| valid | `nn_count >= 150` | → 분석 포함/제외 필터 |

**R&D 트랙 A 직접 호환**: 이 테이블의 `(user_id, metric_date, ln_rmssd)` + `computed_load_metrics`의 `(acwr_rolling, acwr_ewma)` 조합이 트랙 A 통계 모형의 입력이 된다:

```
ln_rmssd(t+1) ~ acwr_rolling(t) + (1|user_id)
```

---

### 3.9 테이블 간 관계 요약 — 트랙 A + 트랙 B 통합

```
[트랙 A 데이터 흐름 — HRV 기반]

웨어러블 디바이스 ─→ hrv_measurements (RR 원시)
                         │
                    filter_rr_outliers()
                         │
                    compute_daily_hrv()
                         ↓
                    daily_hrv_metrics (rMSSD, SDNN, ln_rMSSD)
                         │
                    ln_rmssd_rolling() → ln_rmssd_7d
                         │
                         ↓
              ┌──────────┴──────────┐
              │ 트랙 A 통계 분석     │
              │ ln_rmssd(t+1)       │
              │   ~ acwr(t)         │←── computed_load_metrics.acwr
              │   + (1|user)        │
              └─────────────────────┘


[트랙 B 데이터 흐름 — 주관적 웰니스 기반]

사용자 앱 입력 ─→ pre_session_wellness (Hooper 4항목)
                  post_session_feedback (RPE)
                  next_day_reviews (회고)
                         │
                    sRPE = RPE × duration
                    compute_daily_load_metrics()
                         ↓
                    computed_load_metrics (ACWR, Monotony, Strain)
                         │
                         ↓
              ┌──────────┴──────────┐
              │ 트랙 B 통계 분석     │
              │ hooper(t+1)         │
              │   ~ acwr(t)         │
              │   + monotony(t)     │
              │   + (1|user)        │
              └─────────────────────┘


[트랙 A+B 교차 분석 — 향후 확장]

daily_hrv_metrics.ln_rmssd + pre_session_wellness.hooper_index
                    ↓
       객관적(HRV) + 주관적(Hooper) 이중 검증
       부하 → HRV 감소 → 다음날 Hooper 악화?
       다변량 혼합효과모형:
         hooper(t+1) ~ acwr(t) + ln_rmssd(t) + monotony(t) + (1|user)
```

---

## 4. 데이터 매핑 — soccer ↔ soccer_rnd

### 4.1 사용자 식별자 매핑

```
soccer.users.id (UUID)
    │
    ├──→ soccer_rnd 트랙 B: athlete_id
    │    매핑: SHA-256(users.id + salt) → "A001", "A002", ...
    │    (분석 시 익명화, 원본 UUID는 서비스 내부에서만 사용)
    │
    └──→ soccer_rnd 트랙 A: subject_id
         매핑: 동일 방식
```

### 4.2 세션-날짜 매핑 (서비스 → R&D)

```
training_sessions (서비스)             │  트랙 B 표준 스키마 (R&D)
───────────────────────────────────── │ ──────────────────────────────
user_id                               → athlete_id (익명화)
session_date                          → date
session_type                          → session_type
duration_min                          → duration_min
                                      │
pre_session_wellness.fatigue          → fatigue
pre_session_wellness.soreness         → doms
pre_session_wellness.stress           → stress
pre_session_wellness.sleep            → sleep
pre_session_wellness.hooper_index     → hooper_index
                                      │
post_session_feedback.session_rpe     → rpe
(duration_min × session_rpe)          → srpe (산출)
                                      │
next_day_reviews.condition            → 신규: next_day_condition (추가 종속변수)
```

### 4.3 트랙 A 매핑 (서비스 → R&D)

```
hrv_measurements (서비스)              │  트랙 A 표준 스키마 (R&D)
───────────────────────────────────── │ ──────────────────────────────
user_id                               → subject_id (SHA-256 익명화)
session_id (nullable)                 → session_id (pre/post/morning 등)
measured_at                           → timestamp (측정 시작 기준)
rr_intervals_ms[]                     → rr_interval_ms (배열 → 행 전개)
                                      │
daily_hrv_metrics (서비스)             │
───────────────────────────────────── │
metric_date                           → date (일별 집계)
rmssd                                 → rmssd
sdnn                                  → sdnn
ln_rmssd                              → ln_rmssd
ln_rmssd_7d                           → ln_rmssd_7d (rolling 산출)
session_load_watts                    → power_watts (세션 부하)
nn_count                              → 유효 NN 간격 수 (min_count 필터)
                                      │
computed_load_metrics.acwr_*          → acwr_rolling / acwr_ewma (독립변수)
```

**ETL 변환 뷰 — 트랙 A**:

```sql
-- 서비스 DB에서 R&D 트랙 A 일별 분석용 데이터로 변환
CREATE VIEW v_rnd_track_a AS
SELECT
  encode(digest(h.user_id::text || 'salt_v1', 'sha256'), 'hex')
    AS subject_id,
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
WHERE h.valid = TRUE   -- nn_count >= 150 인 데이터만
ORDER BY h.user_id, h.metric_date;
```

이 뷰를 통해 트랙 A 핵심 모형을 직접 적합할 수 있다:
```
ln_rmssd(t+1) ~ acwr_rolling(t) + (1|subject_id)
```

### 4.4 경기 데이터 연결

```
soccer.matches                        │  training_sessions
─────────────────────────────────────  │ ──────────────────────
match_date, opponent, location         → session_type = 'MATCH'
match_records (goals, assists, cards)  → 성과 지표 (향후 확장)
attendances (투표 결과)                 → 참여 여부 필터
```

경기 세션은 `training_sessions.match_id`로 연결되므로, R&D 분석에서 "경기일 vs 훈련일" 구분이 자동으로 가능하다.

---

## 5. 데이터 흐름 아키텍처

### 5.1 수집 → 저장 → 분석 파이프라인

```
[사용자 입력 흐름]

① 훈련 시작 시
   ┌─────────────────────────────────────┐
   │ 훈련 종류 선택 (TRAINING/MATCH/...)  │
   │ 피로도 (1-7)     ← 슬라이더/칩       │
   │ 근육통 (1-7)     ← 슬라이더/칩       │
   │ 스트레스 (1-7)   ← 슬라이더/칩       │
   │ 수면 만족도 (1-7) ← 슬라이더/칩      │
   │ 컨디션 메모 (선택) ← 한 줄 텍스트     │
   └────────────────┬────────────────────┘
                    ↓
          training_sessions + pre_session_wellness
                    ↓
② 훈련 종료 후 (30분~2시간 후 푸시)
   ┌─────────────────────────────────────┐
   │ Session-RPE (1-10) ← 숫자 선택      │
   │ 전체 컨디션 (5단계) ← 이모지/칩      │
   │ 훈련 메모 (선택) ← 한 줄 텍스트      │
   └────────────────┬────────────────────┘
                    ↓
          post_session_feedback
                    ↓
                    ↓ sRPE = RPE × duration 자동 산출
                    ↓
③ 다음 날 아침 (푸시 알림)
   ┌─────────────────────────────────────┐
   │ 어제 훈련 후 컨디션이... (3단계)     │
   │  [더 나빠짐] [비슷함] [좋아짐]       │
   │ 메모 (선택) ← 한 줄 텍스트           │
   └────────────────┬────────────────────┘
                    ↓
          next_day_reviews
                    ↓

[HRV 수집 흐름 — 트랙 A]

④ 매일 아침 (기상 후 안정 시) 또는 세션 전후
   ┌─────────────────────────────────────┐
   │ 웨어러블 디바이스 → BLE/API 자동 전송 │
   │ 또는 앱에서 HRV 측정 시작 버튼       │
   │ (1~5분 측정, RR 간격 자동 수집)       │
   └────────────────┬────────────────────┘
                    ↓
          hrv_measurements (RR 원시 배열)
                    │
           filter_rr_outliers() — 중앙값 ±20% 필터
           compute_daily_hrv() — rMSSD, SDNN, ln_rMSSD 산출
                    ↓
          daily_hrv_metrics (일별 HRV 지표)
                    ↓
           ln_rmssd_rolling() — 7일 이동평균
                    ↓

[산출 파이프라인 (배치/트리거)]

          computed_load_metrics (트랙 B)
                    │
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
 ACWR 산출     Monotony 산출   Hooper 추적
 (acwr.py)     (monotony_     (monotony_
               strain.py)     strain.py)
                    │
          daily_hrv_metrics (트랙 A)
                    │
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
 rMSSD 추이    ln_rMSSD 7d    SWC 판별
 (hrv_         (hrv_          (개인 내
 features.py)  features.py)   변동 모니터링)
                    │
                    ↓
         [R&D 분석 파이프라인]
         lag_analysis.py    — 다중 시차 (lag 0~7)
         mixed_effects.py   — 혼합효과모형
         cross_validation.py — LOSO CV
                    │
                    ↓
         [대시보드 / 리포트]
         - ACWR 추이 차트
         - HRV(ln_rMSSD) 추이 + 7일 이동평균
         - 부하-HRV 시차 관계 (트랙 A)
         - 부하-웰니스 시차 관계 (트랙 B)
         - 개인별 최적 부하 구간
         - 과부하 조기 경고 (ACWR>1.5 또는 HRV 급락)
```

### 5.2 ETL 변환 쿼리 (서비스 DB → R&D 표준 스키마)

```sql
-- 서비스 DB에서 R&D 트랙 B 표준 스키마로 변환하는 뷰
CREATE VIEW v_rnd_track_b AS
SELECT
  -- 식별자 (익명화)
  encode(digest(ts.user_id::text || 'salt_v1', 'sha256'), 'hex')
    AS athlete_id,

  -- 날짜
  ts.session_date AS date,

  -- 부하
  ps.session_rpe AS rpe,
  ts.duration_min,
  (ps.session_rpe * ts.duration_min) AS srpe,

  -- 웰니스 (Hooper 4항목)
  pw.fatigue,
  pw.stress,
  pw.soreness AS doms,
  pw.sleep,
  pw.hooper_index,

  -- 세션 맥락
  ts.session_type::text AS session_type,
  CASE WHEN ts.match_id IS NOT NULL THEN TRUE ELSE FALSE END AS match_day,

  -- 다음 날 회고 (수치화)
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
WHERE ps.session_rpe IS NOT NULL  -- 최소한 RPE가 있어야 유효
ORDER BY ts.user_id, ts.session_date;
```

이 뷰의 출력은 `src/data/loader.py::load_track_b()`가 기대하는 스키마와 정확히 일치한다.

---

## 6. 마이그레이션 실행 계획

### 6.1 Phase 1: 스키마 확장 (서비스 측)

```
supabase/migrations/00003_user_profiles.sql
  → user_profiles 테이블 + RLS 정책

supabase/migrations/00004_training_sessions.sql
  → training_sessions 테이블 + 인덱스

supabase/migrations/00005_wellness_feedback.sql
  → pre_session_wellness
  → post_session_feedback
  → next_day_reviews

supabase/migrations/00006_computed_metrics.sql
  → computed_load_metrics 테이블
  → v_rnd_track_b 뷰
```

### 6.2 Phase 2: TypeScript 타입 확장 (서비스 측)

```typescript
// src/lib/types.ts에 추가

export type SessionType = 'TRAINING' | 'MATCH' | 'REST' | 'OTHER';
export type PostCondition = 'VERY_BAD' | 'BAD' | 'NEUTRAL' | 'GOOD' | 'VERY_GOOD';
export type NextDayCondition = 'WORSE' | 'SAME' | 'BETTER';

export interface UserProfile {
  id: string;
  user_id: string;
  phone: string | null;
  position: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrainingSession {
  id: string;
  user_id: string;
  team_id: string | null;
  match_id: string | null;
  session_type: SessionType;
  session_date: string;
  duration_min: number | null;
  has_pre_wellness: boolean;
  has_post_feedback: boolean;
  has_next_day_review: boolean;
  created_at: string;
  updated_at: string;
}

export interface PreSessionWellness {
  id: string;
  session_id: string;
  user_id: string;
  fatigue: number;      // 1-7
  soreness: number;     // 1-7 (= DOMS)
  stress: number;       // 1-7
  sleep: number;        // 1-7
  hooper_index: number; // 4-28 (자동 산출)
  memo: string | null;
  recorded_at: string;
}

export interface PostSessionFeedback {
  id: string;
  session_id: string;
  user_id: string;
  session_rpe: number;  // 1-10 (CR-10)
  condition: PostCondition;
  memo: string | null;
  recorded_at: string;
}

export interface NextDayReview {
  id: string;
  session_id: string;
  user_id: string;
  condition: NextDayCondition;
  memo: string | null;
  recorded_at: string;
}

// --- 트랙 A: HRV 데이터 ---
export type HrvSource = 'CHEST_STRAP' | 'SMARTWATCH' | 'FINGER_SENSOR' | 'APP_MANUAL' | 'EXTERNAL_IMPORT';
export type HrvContext = 'MORNING_REST' | 'PRE_SESSION' | 'POST_SESSION' | 'DURING_SESSION' | 'NIGHT_SLEEP' | 'OTHER';

export interface HrvMeasurement {
  id: string;
  user_id: string;
  session_id: string | null;
  source: HrvSource;
  context: HrvContext;
  measured_at: string;
  duration_sec: number | null;
  rr_intervals_ms: number[];    // RR 간격 원시 배열
  rr_count: number;
  device_name: string | null;
  quality_flag: boolean;
  created_at: string;
}

export interface DailyHrvMetrics {
  id: string;
  user_id: string;
  metric_date: string;
  measurement_id: string | null;
  rmssd: number | null;         // ms
  sdnn: number | null;          // ms
  ln_rmssd: number | null;      // 자연 로그
  mean_rr: number | null;       // ms
  mean_hr: number | null;       // bpm
  ln_rmssd_7d: number | null;   // 7일 Rolling Average
  session_load_watts: number | null;
  nn_count: number | null;
  valid: boolean;
  computed_at: string;
}
```

### 6.3 Phase 3: Zod 검증 스키마 (서비스 측)

```typescript
// src/features/training/schemas.ts

import { z } from 'zod';

export const preWellnessSchema = z.object({
  session_type: z.enum(['TRAINING', 'MATCH', 'REST', 'OTHER']),
  fatigue: z.number().int().min(1).max(7),
  soreness: z.number().int().min(1).max(7),
  stress: z.number().int().min(1).max(7),
  sleep: z.number().int().min(1).max(7),
  memo: z.string().max(200).optional(),
});

export const postFeedbackSchema = z.object({
  session_rpe: z.number().int().min(1).max(10),
  condition: z.enum(['VERY_BAD', 'BAD', 'NEUTRAL', 'GOOD', 'VERY_GOOD']),
  duration_min: z.number().positive().optional(),
  memo: z.string().max(200).optional(),
});

export const nextDayReviewSchema = z.object({
  condition: z.enum(['WORSE', 'SAME', 'BETTER']),
  memo: z.string().max(200).optional(),
});
```

### 6.4 Phase 4: R&D 파이프라인 연동 (분석 측)

```python
# src/data/loader.py 확장 — Supabase 뷰에서 직접 로드

def load_from_service_db(
    supabase_url: str,
    supabase_key: str,
    team_id: str | None = None,
) -> pd.DataFrame:
    """
    서비스 DB의 v_rnd_track_b 뷰에서 데이터를 로드한다.
    반환 DataFrame은 트랙 B 표준 스키마와 호환된다.
    """
    ...
```

---

## 7. 데이터 품질 및 일관성 보장

### 7.1 스케일 방향 통일

| 항목 | 서비스 입력 방향 | R&D 표준 방향 | 변환 |
|------|:--:|:--:|:--:|
| fatigue | 1(최상)~7(최악) | 1(최상)~7(최악) | 동일 |
| soreness | 1(최상)~7(최악) | 1(최상)~7(최악) | 동일 (soreness → doms) |
| stress | 1(최상)~7(최악) | 1(최상)~7(최악) | 동일 |
| sleep | 1(최상)~7(최악) | 1(최상)~7(최악) | 동일 |
| session_rpe | 1(매우 쉬움)~10(최대) | 1~10 (CR-10) | 동일 |
| hooper_index | 4(최상)~28(최악) | 4~28 | 자동 산출, 동일 |

### 7.2 결측 처리 원칙 (ADR-004 준수)

| 상황 | 처리 |
|------|------|
| 훈련 전 미입력 | pre_session_wellness 행 없음 → Hooper = NULL |
| 훈련 후 미입력 | post_session_feedback 행 없음 → sRPE = NULL |
| 다음 날 미응답 | next_day_reviews 행 없음 → next_day_score = NULL |
| duration 미입력 | sRPE = NULL (RPE × NULL = NULL) |
| 휴식일 | session_type='REST', sRPE=0 (의도적 0, 결측 아님) |

### 7.3 데이터 검증 규칙

```sql
-- CHECK 제약으로 DB 레벨 검증
fatigue BETWEEN 1 AND 7
soreness BETWEEN 1 AND 7
stress BETWEEN 1 AND 7
sleep BETWEEN 1 AND 7
session_rpe BETWEEN 1 AND 10
duration_min > 0 (NULL 허용)
```

---

## 8. 통합 후 분석 시나리오

### 8.1 개인 부하-웰니스 대시보드

```
[사용자 A의 최근 28일 대시보드]

┌─────────────────────────────────────────┐
│ ACWR 추이                    현재: 1.25  │
│ ████████████████████▓▓▓▓░░░░           │
│ 0.8 ──── 1.0 ──── 1.3 ──── 1.5        │
│       최적 구간                          │
├─────────────────────────────────────────┤
│ Hooper Index 추이            현재: 14    │
│ ■■■■■■■□□□□□□□□□□□□□□□□□□□□□          │
│ 4                    28                  │
├─────────────────────────────────────────┤
│ Monotony (7일)               현재: 1.8   │
│ ● 정상 (< 2.0)                          │
├─────────────────────────────────────────┤
│ 다음 날 회고 패턴                         │
│ 최근 7회: 😊😊😐😊😟😊😐              │
└─────────────────────────────────────────┘
```

### 8.2 팀 수준 분석

```python
# 서비스 DB → R&D 분석 파이프라인
df = load_from_service_db(url, key, team_id="team_uuid")

# 1. 개인별 부하 지표 산출
df = compute_daily_load_metrics(df, athlete_col="athlete_id")

# 2. 다중 시차 분석
corr = lag_correlation_table(df, "acwr_rolling", "hooper_index", "athlete_id", max_lag=7)
best_lag = optimal_lag(lag_mixed_effects_comparison(df, ...))

# 3. LOSO 교차 검증으로 일반화 성능 확인
cv = loso_cv("hooper_index ~ acwr_rolling + monotony", df, "athlete_id", "hooper_index")
summary = loso_summary(cv)

# 4. 과부하 조기 경고
high_risk = df[(df['acwr_rolling'] > 1.5) | (df['monotony'] > 2.0)]
```

---

## 9. 보안 및 개인정보 보호

| 항목 | 서비스 측 | R&D 측 |
|------|-----------|--------|
| 사용자 식별 | UUID (서비스 내부) | SHA-256 익명화 ID |
| 휴대폰 번호 | AES-256 암호화 저장 | **접근 불가** |
| 웰니스 데이터 | Supabase RLS (본인만) | 집계/분석만 허용 |
| 데이터 전송 | HTTPS, Supabase 인증 | 로컬 전용 또는 암호화 전송 |
| 분석 결과 | 개인 대시보드만 | 팀 수준 집계만 외부 공개 |

---

## 10. 마이그레이션 체크리스트

### Phase 1: 스키마 (1주)
- [ ] `user_profiles` 마이그레이션 SQL 작성 및 적용
- [ ] `training_sessions` 마이그레이션 SQL 작성 및 적용
- [ ] `pre_session_wellness` 마이그레이션 SQL 작성 및 적용
- [ ] `post_session_feedback` 마이그레이션 SQL 작성 및 적용
- [ ] `next_day_reviews` 마이그레이션 SQL 작성 및 적용
- [ ] `hrv_measurements` 마이그레이션 SQL 작성 및 적용 (트랙 A)
- [ ] `daily_hrv_metrics` 마이그레이션 SQL 작성 및 적용 (트랙 A)
- [ ] `computed_load_metrics` 마이그레이션 SQL 작성 및 적용 (트랙 B)
- [ ] `v_rnd_track_a` 뷰 생성 (HRV + 부하 조인)
- [ ] `v_rnd_track_b` 뷰 생성 (웰니스 + 부하 조인)
- [ ] RLS 정책 설정 (모든 신규 테이블)

### Phase 2: 서비스 코드 (2주)
- [ ] TypeScript 타입 정의 (`types.ts`)
- [ ] Zod 검증 스키마
- [ ] API 라우트: `POST /api/training/sessions` (세션 생성)
- [ ] API 라우트: `POST /api/training/sessions/[id]/pre-wellness` (훈련 전 입력)
- [ ] API 라우트: `POST /api/training/sessions/[id]/post-feedback` (훈련 후 입력)
- [ ] API 라우트: `POST /api/training/sessions/[id]/next-day-review` (다음 날 회고)
- [ ] API 라우트: `GET /api/training/metrics/[userId]` (산출 지표 조회)
- [ ] 푸시 알림: 훈련 후 30분 → post_feedback, 다음 날 08:00 → next_day_review
- [ ] 프론트엔드: 훈련 입력 UI (3단계 플로우)

### Phase 3: R&D 연동 (1주)
- [ ] `src/data/loader.py`에 `load_from_service_db()` 추가 (트랙 B)
- [ ] `src/data/loader.py`에 `load_hrv_from_service_db()` 추가 (트랙 A)
- [ ] ETL 배치: 서비스 DB → computed_load_metrics (트랙 B)
- [ ] ETL 배치: hrv_measurements → daily_hrv_metrics (트랙 A)
- [ ] 기존 87개 테스트 + 연동 테스트 추가
- [ ] 대시보드 프로토타입 (HRV 추이 + Hooper/ACWR 추이)

### Phase 4: 검증 (1주)
- [ ] 시드 데이터로 전체 파이프라인 검증
- [ ] LOSO CV로 모형 일반화 성능 확인
- [ ] 스케일 방향 일관성 최종 확인
- [ ] 개인정보 보호 검토

---

*본 문서는 `C:\dev\soccer` (서비스 MVP)와 `C:\dev\soccer_rnd` (R&D 분석) 프로젝트의 데이터 통합 계획을 기술한다.*
*모든 신규 테이블 설계는 soccer_rnd의 트랙 B 표준 스키마 및 분석 파이프라인과의 호환성을 최우선으로 고려하였다.*

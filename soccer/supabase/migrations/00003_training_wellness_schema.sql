-- 훈련·웰니스·HRV 스키마 확장
-- 목적: soccer_rnd 트랙 A/B 파이프라인과 호환되는 훈련 데이터 수집 체계 구축
-- 의존: 00001_initial_schema.sql (users, teams, matches 테이블)

-- ============================================================
-- 1. ENUM 타입 정의
-- ============================================================

CREATE TYPE session_type AS ENUM ('TRAINING', 'MATCH', 'REST', 'OTHER');
CREATE TYPE post_condition AS ENUM ('VERY_BAD', 'BAD', 'NEUTRAL', 'GOOD', 'VERY_GOOD');
CREATE TYPE next_day_condition AS ENUM ('WORSE', 'SAME', 'BETTER');
CREATE TYPE hrv_source AS ENUM ('CHEST_STRAP', 'SMARTWATCH', 'FINGER_SENSOR', 'APP_MANUAL', 'EXTERNAL_IMPORT');
CREATE TYPE hrv_context AS ENUM ('MORNING_REST', 'PRE_SESSION', 'POST_SESSION', 'DURING_SESSION', 'NIGHT_SLEEP', 'OTHER');

-- ============================================================
-- 2. user_profiles (사용자 프로필 확장)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profiles (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  phone       TEXT,
  position    TEXT CHECK (position IN (
                'GK', 'CB', 'LB', 'RB', 'WB',
                'CDM', 'CM', 'CAM', 'LM', 'RM',
                'LW', 'RW', 'CF', 'ST'
              )),

  created_at  TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_profiles_read_own" ON user_profiles FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "user_profiles_update_own" ON user_profiles FOR UPDATE
  USING (user_id = auth.uid());
CREATE POLICY "user_profiles_insert_own" ON user_profiles FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- ============================================================
-- 3. training_sessions (훈련 세션)
-- ============================================================
CREATE TABLE IF NOT EXISTS training_sessions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  team_id     UUID REFERENCES teams(id) ON DELETE SET NULL,
  match_id    UUID REFERENCES matches(id) ON DELETE SET NULL,

  session_type  session_type NOT NULL DEFAULT 'TRAINING',
  session_date  DATE NOT NULL,
  duration_min  FLOAT,

  has_pre_wellness    BOOLEAN DEFAULT FALSE,
  has_post_feedback   BOOLEAN DEFAULT FALSE,
  has_next_day_review BOOLEAN DEFAULT FALSE,

  created_at  TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at  TIMESTAMPTZ DEFAULT now() NOT NULL,

  UNIQUE NULLS NOT DISTINCT (user_id, match_id)
);

CREATE INDEX idx_sessions_user_date ON training_sessions(user_id, session_date);
CREATE INDEX idx_sessions_team ON training_sessions(team_id);

ALTER TABLE training_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "sessions_read_own" ON training_sessions FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "sessions_insert_own" ON training_sessions FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "sessions_update_own" ON training_sessions FOR UPDATE
  USING (user_id = auth.uid());

-- ============================================================
-- 4. pre_session_wellness (훈련 전 웰니스 — Hooper 4항목)
-- ============================================================
CREATE TABLE IF NOT EXISTS pre_session_wellness (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  fatigue     SMALLINT NOT NULL CHECK (fatigue BETWEEN 1 AND 7),
  soreness    SMALLINT NOT NULL CHECK (soreness BETWEEN 1 AND 7),
  stress      SMALLINT NOT NULL CHECK (stress BETWEEN 1 AND 7),
  sleep       SMALLINT NOT NULL CHECK (sleep BETWEEN 1 AND 7),

  hooper_index SMALLINT GENERATED ALWAYS AS (fatigue + soreness + stress + sleep) STORED,

  memo        TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_pre_wellness_user ON pre_session_wellness(user_id, recorded_at);

ALTER TABLE pre_session_wellness ENABLE ROW LEVEL SECURITY;
CREATE POLICY "pre_wellness_read_own" ON pre_session_wellness FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "pre_wellness_insert_own" ON pre_session_wellness FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "pre_wellness_update_own" ON pre_session_wellness FOR UPDATE
  USING (user_id = auth.uid());

-- ============================================================
-- 5. post_session_feedback (훈련 후 피드백 — sRPE)
-- ============================================================
CREATE TABLE IF NOT EXISTS post_session_feedback (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  session_rpe SMALLINT NOT NULL CHECK (session_rpe BETWEEN 1 AND 10),
  condition   post_condition NOT NULL,

  memo        TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_post_feedback_user ON post_session_feedback(user_id, recorded_at);

ALTER TABLE post_session_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY "post_feedback_read_own" ON post_session_feedback FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "post_feedback_insert_own" ON post_session_feedback FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "post_feedback_update_own" ON post_session_feedback FOR UPDATE
  USING (user_id = auth.uid());

-- ============================================================
-- 6. next_day_reviews (다음 날 회고)
-- ============================================================
CREATE TABLE IF NOT EXISTS next_day_reviews (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id  UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

  condition   next_day_condition NOT NULL,

  memo        TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_next_day_user ON next_day_reviews(user_id, recorded_at);

ALTER TABLE next_day_reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "next_day_read_own" ON next_day_reviews FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "next_day_insert_own" ON next_day_reviews FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "next_day_update_own" ON next_day_reviews FOR UPDATE
  USING (user_id = auth.uid());

-- ============================================================
-- 7. computed_load_metrics (산출 지표 캐시)
-- ============================================================
CREATE TABLE IF NOT EXISTS computed_load_metrics (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  metric_date   DATE NOT NULL,

  daily_load    FLOAT,
  atl_rolling   FLOAT,
  ctl_rolling   FLOAT,
  acwr_rolling  FLOAT,
  atl_ewma      FLOAT,
  ctl_ewma      FLOAT,
  acwr_ewma     FLOAT,

  monotony      FLOAT,
  strain_value  FLOAT,

  dcwr_rolling  FLOAT,
  tsb_rolling   FLOAT,

  hooper_index  SMALLINT,

  computed_at   TIMESTAMPTZ DEFAULT now() NOT NULL,

  UNIQUE(user_id, metric_date)
);

CREATE INDEX idx_metrics_user_date ON computed_load_metrics(user_id, metric_date DESC);

ALTER TABLE computed_load_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "metrics_read_own" ON computed_load_metrics FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "metrics_insert_own" ON computed_load_metrics FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- ============================================================
-- 8. hrv_measurements (HRV 원시 측정 — 트랙 A)
-- ============================================================
CREATE TABLE IF NOT EXISTS hrv_measurements (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id      UUID REFERENCES training_sessions(id) ON DELETE SET NULL,

  source          hrv_source NOT NULL,
  context         hrv_context NOT NULL DEFAULT 'MORNING_REST',
  measured_at     TIMESTAMPTZ NOT NULL,
  duration_sec    INT,

  rr_intervals_ms FLOAT[] NOT NULL,
  rr_count        INT GENERATED ALWAYS AS (array_length(rr_intervals_ms, 1)) STORED,

  device_name     TEXT,
  firmware_ver    TEXT,
  quality_flag    BOOLEAN DEFAULT TRUE,

  created_at      TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX idx_hrv_user_date ON hrv_measurements(user_id, measured_at DESC);
CREATE INDEX idx_hrv_session ON hrv_measurements(session_id);

ALTER TABLE hrv_measurements ENABLE ROW LEVEL SECURITY;
CREATE POLICY "hrv_read_own" ON hrv_measurements FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "hrv_insert_own" ON hrv_measurements FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- ============================================================
-- 9. daily_hrv_metrics (일별 HRV 지표 — 트랙 A)
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_hrv_metrics (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  metric_date     DATE NOT NULL,

  measurement_id  UUID REFERENCES hrv_measurements(id) ON DELETE SET NULL,

  rmssd           FLOAT,
  sdnn            FLOAT,
  ln_rmssd        FLOAT,
  mean_rr         FLOAT,
  mean_hr         FLOAT,

  ln_rmssd_7d     FLOAT,

  session_load_watts FLOAT,

  nn_count        INT,
  valid           BOOLEAN DEFAULT TRUE,

  computed_at     TIMESTAMPTZ DEFAULT now() NOT NULL,

  UNIQUE(user_id, metric_date)
);

CREATE INDEX idx_daily_hrv_user ON daily_hrv_metrics(user_id, metric_date DESC);

ALTER TABLE daily_hrv_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "daily_hrv_read_own" ON daily_hrv_metrics FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "daily_hrv_insert_own" ON daily_hrv_metrics FOR INSERT
  WITH CHECK (user_id = auth.uid());

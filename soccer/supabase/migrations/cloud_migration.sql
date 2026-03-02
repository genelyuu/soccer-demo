-- =================================================================
-- Cloud Supabase 통합 마이그레이션 스크립트
-- 대상: https://supabase.com/dashboard/project/pmdukumyboceykjlggpx
-- 포함: 00001 ~ 00005 + seed.sql (auth.uid() 스텁 제외)
-- 생성일: 2026-03-02
--
-- 실행 방법: Supabase Dashboard > SQL Editor에서 실행
-- 주의: 이미 테이블이 있는 경우 충돌 발생 가능
-- =================================================================

BEGIN;

-- =================================================================
-- ██ 00001: 초기 스키마 (MVP)
-- =================================================================

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. Teams
CREATE TABLE IF NOT EXISTS teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  logo_url TEXT,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 3. Team Members
DO $$ BEGIN
  CREATE TYPE team_role AS ENUM ('ADMIN', 'MANAGER', 'MEMBER', 'GUEST');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role team_role NOT NULL DEFAULT 'MEMBER',
  joined_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(team_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_team_members_team ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user ON team_members(user_id);

-- 4. Matches
DO $$ BEGIN
  CREATE TYPE match_status AS ENUM ('OPEN', 'CONFIRMED', 'COMPLETED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS matches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  match_date TIMESTAMPTZ NOT NULL,
  location TEXT,
  opponent TEXT,
  status match_status NOT NULL DEFAULT 'OPEN',
  created_by UUID NOT NULL REFERENCES users(id),
  confirmed_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_matches_team ON matches(team_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);

-- 5. Attendances
DO $$ BEGIN
  CREATE TYPE attendance_status AS ENUM ('PENDING', 'ACCEPTED', 'DECLINED', 'MAYBE');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS attendances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status attendance_status NOT NULL DEFAULT 'PENDING',
  voted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(match_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_attendances_match ON attendances(match_id);
CREATE INDEX IF NOT EXISTS idx_attendances_user ON attendances(user_id);

-- 6. Record Rooms
DO $$ BEGIN
  CREATE TYPE record_room_status AS ENUM ('OPEN', 'CLOSED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS record_rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id UUID UNIQUE NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  status record_room_status NOT NULL DEFAULT 'OPEN',
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  closed_at TIMESTAMPTZ
);

-- 7. Match Records
CREATE TABLE IF NOT EXISTS match_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  record_room_id UUID NOT NULL REFERENCES record_rooms(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id),
  goals INT NOT NULL DEFAULT 0,
  assists INT NOT NULL DEFAULT 0,
  yellow_cards INT NOT NULL DEFAULT 0,
  red_cards INT NOT NULL DEFAULT 0,
  memo TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(record_room_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_match_records_room ON match_records(record_room_id);
CREATE INDEX IF NOT EXISTS idx_match_records_user ON match_records(user_id);

-- RLS 활성화 (00001)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendances ENABLE ROW LEVEL SECURITY;
ALTER TABLE record_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_records ENABLE ROW LEVEL SECURITY;

-- 기본 RLS 정책 (00001)
CREATE POLICY "users_read_own" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_update_own" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "teams_read_member" ON teams FOR SELECT
  USING (id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

CREATE POLICY "team_members_read" ON team_members FOR SELECT
  USING (team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

CREATE POLICY "matches_read_team" ON matches FOR SELECT
  USING (team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

CREATE POLICY "attendances_read_team" ON attendances FOR SELECT
  USING (match_id IN (
    SELECT m.id FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE tm.user_id = auth.uid()
  ));

CREATE POLICY "record_rooms_read" ON record_rooms FOR SELECT
  USING (match_id IN (
    SELECT m.id FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE tm.user_id = auth.uid()
  ));

CREATE POLICY "match_records_read" ON match_records FOR SELECT
  USING (record_room_id IN (
    SELECT rr.id FROM record_rooms rr
    JOIN matches m ON m.id = rr.match_id
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE tm.user_id = auth.uid()
  ));

-- =================================================================
-- ██ 00002: RLS 쓰기 정책
-- =================================================================

CREATE POLICY "users_insert_own" ON users FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "teams_insert_authenticated" ON teams FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);
CREATE POLICY "teams_update_admin" ON teams FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = teams.id
      AND team_members.user_id = auth.uid()
      AND team_members.role = 'ADMIN'
  ));
CREATE POLICY "teams_delete_admin" ON teams FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = teams.id
      AND team_members.user_id = auth.uid()
      AND team_members.role = 'ADMIN'
  ));

CREATE POLICY "team_members_insert_admin_manager" ON team_members FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM team_members AS tm
    WHERE tm.team_id = team_members.team_id
      AND tm.user_id = auth.uid()
      AND tm.role IN ('ADMIN', 'MANAGER')
  ));
CREATE POLICY "team_members_delete_admin" ON team_members FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM team_members AS tm
    WHERE tm.team_id = team_members.team_id
      AND tm.user_id = auth.uid()
      AND tm.role = 'ADMIN'
  ));
CREATE POLICY "team_members_update_admin" ON team_members FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM team_members AS tm
    WHERE tm.team_id = team_members.team_id
      AND tm.user_id = auth.uid()
      AND tm.role = 'ADMIN'
  ));

CREATE POLICY "matches_insert_manager" ON matches FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = matches.team_id
      AND team_members.user_id = auth.uid()
      AND team_members.role IN ('ADMIN', 'MANAGER')
  ));
CREATE POLICY "matches_update_manager" ON matches FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = matches.team_id
      AND team_members.user_id = auth.uid()
      AND team_members.role IN ('ADMIN', 'MANAGER')
  ));
CREATE POLICY "matches_delete_admin" ON matches FOR DELETE
  USING (EXISTS (
    SELECT 1 FROM team_members
    WHERE team_members.team_id = matches.team_id
      AND team_members.user_id = auth.uid()
      AND team_members.role = 'ADMIN'
  ));

CREATE POLICY "attendances_insert_manager" ON attendances FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE m.id = attendances.match_id
      AND tm.user_id = auth.uid()
      AND tm.role IN ('ADMIN', 'MANAGER')
  ));
CREATE POLICY "attendances_update_own_vote" ON attendances FOR UPDATE
  USING (
    attendances.user_id = auth.uid()
    AND EXISTS (
      SELECT 1 FROM matches m
      JOIN team_members tm ON tm.team_id = m.team_id
      WHERE m.id = attendances.match_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER', 'MEMBER')
    )
  );

CREATE POLICY "record_rooms_insert_manager" ON record_rooms FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE m.id = record_rooms.match_id
      AND tm.user_id = auth.uid()
      AND tm.role IN ('ADMIN', 'MANAGER')
  ));
CREATE POLICY "record_rooms_update_manager" ON record_rooms FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE m.id = record_rooms.match_id
      AND tm.user_id = auth.uid()
      AND tm.role IN ('ADMIN', 'MANAGER')
  ));

CREATE POLICY "match_records_insert_manager" ON match_records FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM record_rooms rr
    JOIN matches m ON m.id = rr.match_id
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE rr.id = match_records.record_room_id
      AND tm.user_id = auth.uid()
      AND tm.role IN ('ADMIN', 'MANAGER')
  ));
CREATE POLICY "match_records_update_manager" ON match_records FOR UPDATE
  USING (EXISTS (
    SELECT 1 FROM record_rooms rr
    JOIN matches m ON m.id = rr.match_id
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE rr.id = match_records.record_room_id
      AND tm.user_id = auth.uid()
      AND tm.role IN ('ADMIN', 'MANAGER')
  ));

-- =================================================================
-- ██ 00003: 훈련·웰니스·HRV 스키마
-- =================================================================

DO $$ BEGIN CREATE TYPE session_type AS ENUM ('TRAINING', 'MATCH', 'REST', 'OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE post_condition AS ENUM ('VERY_BAD', 'BAD', 'NEUTRAL', 'GOOD', 'VERY_GOOD'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE next_day_condition AS ENUM ('WORSE', 'SAME', 'BETTER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE hrv_source AS ENUM ('CHEST_STRAP', 'SMARTWATCH', 'FINGER_SENSOR', 'APP_MANUAL', 'EXTERNAL_IMPORT'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE hrv_context AS ENUM ('MORNING_REST', 'PRE_SESSION', 'POST_SESSION', 'DURING_SESSION', 'NIGHT_SLEEP', 'OTHER'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- user_profiles
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  phone TEXT,
  position TEXT CHECK (position IN (
    'GK', 'CB', 'LB', 'RB', 'WB',
    'CDM', 'CM', 'CAM', 'LM', 'RM',
    'LW', 'RW', 'CF', 'ST'
  )),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_profiles_read_own" ON user_profiles FOR SELECT
  USING (user_id = auth.uid());
CREATE POLICY "user_profiles_update_own" ON user_profiles FOR UPDATE
  USING (user_id = auth.uid());
CREATE POLICY "user_profiles_insert_own" ON user_profiles FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- training_sessions (B-01 수정: UNIQUE NULLS NOT DISTINCT 대신 partial index 사용)
CREATE TABLE IF NOT EXISTS training_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  team_id UUID REFERENCES teams(id) ON DELETE SET NULL,
  match_id UUID REFERENCES matches(id) ON DELETE SET NULL,
  session_type session_type NOT NULL DEFAULT 'TRAINING',
  session_date DATE NOT NULL,
  duration_min FLOAT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- B-01: Partial unique index (NULLS NOT DISTINCT 대신)
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_user_match
  ON training_sessions(user_id, match_id)
  WHERE match_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sessions_user_date ON training_sessions(user_id, session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_team ON training_sessions(team_id);
-- B-13: session_date 단독 인덱스
CREATE INDEX IF NOT EXISTS idx_sessions_date ON training_sessions(session_date);

ALTER TABLE training_sessions ENABLE ROW LEVEL SECURITY;

-- pre_session_wellness (B-02: user_id 제거됨 - session 경유)
CREATE TABLE IF NOT EXISTS pre_session_wellness (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  fatigue SMALLINT NOT NULL CHECK (fatigue BETWEEN 1 AND 7),
  soreness SMALLINT NOT NULL CHECK (soreness BETWEEN 1 AND 7),
  stress SMALLINT NOT NULL CHECK (stress BETWEEN 1 AND 7),
  sleep SMALLINT NOT NULL CHECK (sleep BETWEEN 1 AND 7),
  hooper_index SMALLINT GENERATED ALWAYS AS (fatigue + soreness + stress + sleep) STORED,
  memo TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE pre_session_wellness ENABLE ROW LEVEL SECURITY;

-- post_session_feedback (B-02: user_id 제거, B-06: RPE 0~10)
CREATE TABLE IF NOT EXISTS post_session_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  session_rpe SMALLINT NOT NULL CHECK (session_rpe BETWEEN 0 AND 10),
  condition post_condition NOT NULL,
  memo TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE post_session_feedback ENABLE ROW LEVEL SECURITY;

-- next_day_reviews (B-02: user_id 제거)
CREATE TABLE IF NOT EXISTS next_day_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID UNIQUE NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
  condition next_day_condition NOT NULL,
  memo TEXT,
  recorded_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE next_day_reviews ENABLE ROW LEVEL SECURITY;

-- computed_load_metrics (B-09/B-16: strain 명명, pipeline_version, params)
CREATE TABLE IF NOT EXISTS computed_load_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  daily_load FLOAT,
  atl_rolling FLOAT,
  ctl_rolling FLOAT,
  acwr_rolling FLOAT,
  atl_ewma FLOAT,
  ctl_ewma FLOAT,
  acwr_ewma FLOAT,
  monotony FLOAT,
  strain FLOAT,
  dcwr_rolling FLOAT,
  tsb_rolling FLOAT,
  hooper_index SMALLINT,
  pipeline_version TEXT DEFAULT 'v1.0',
  params JSONB DEFAULT '{
    "atl_window": 7, "ctl_window": 28,
    "ewma_atl_span": 7, "ewma_ctl_span": 28
  }'::jsonb,
  computed_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(user_id, metric_date)
);

CREATE INDEX IF NOT EXISTS idx_metrics_user_date ON computed_load_metrics(user_id, metric_date DESC);

ALTER TABLE computed_load_metrics ENABLE ROW LEVEL SECURITY;

-- hrv_measurements (B-11: array size constraint)
CREATE TABLE IF NOT EXISTS hrv_measurements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id UUID REFERENCES training_sessions(id) ON DELETE SET NULL,
  source hrv_source NOT NULL,
  context hrv_context NOT NULL DEFAULT 'MORNING_REST',
  measured_at TIMESTAMPTZ NOT NULL,
  duration_sec INT,
  rr_intervals_ms FLOAT[] NOT NULL,
  rr_count INT GENERATED ALWAYS AS (array_length(rr_intervals_ms, 1)) STORED,
  device_name TEXT,
  firmware_ver TEXT,
  quality_flag BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  CONSTRAINT hrv_rr_array_size CHECK (array_length(rr_intervals_ms, 1) BETWEEN 1 AND 50000)
);

CREATE INDEX IF NOT EXISTS idx_hrv_user_date ON hrv_measurements(user_id, measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_hrv_session ON hrv_measurements(session_id);

ALTER TABLE hrv_measurements ENABLE ROW LEVEL SECURITY;

-- daily_hrv_metrics (B-25: valid DEFAULT TRUE NOT NULL)
CREATE TABLE IF NOT EXISTS daily_hrv_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  measurement_id UUID REFERENCES hrv_measurements(id) ON DELETE SET NULL,
  rmssd FLOAT,
  sdnn FLOAT,
  ln_rmssd FLOAT,
  mean_rr FLOAT,
  mean_hr FLOAT,
  ln_rmssd_7d FLOAT,
  session_load_watts FLOAT,
  nn_count INT,
  valid BOOLEAN NOT NULL DEFAULT TRUE,
  computed_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(user_id, metric_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_hrv_user ON daily_hrv_metrics(user_id, metric_date DESC);

ALTER TABLE daily_hrv_metrics ENABLE ROW LEVEL SECURITY;

-- =================================================================
-- ██ RLS 정책 (00005 통합: 팀 기반 + 세션 경유)
-- =================================================================

-- training_sessions: 팀 기반 SELECT + 본인 INSERT/UPDATE + ADMIN DELETE
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

-- pre_session_wellness: session 경유 RLS
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

-- post_session_feedback: session 경유 RLS
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

-- next_day_reviews: session 경유 RLS
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

-- computed_load_metrics: 팀 기반 SELECT + UPDATE + DELETE
CREATE POLICY "metrics_read_own_or_team" ON computed_load_metrics FOR SELECT
  USING (
    user_id = auth.uid()
    OR user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role IN ('ADMIN', 'MANAGER')
    )
  );
CREATE POLICY "metrics_insert_own" ON computed_load_metrics FOR INSERT
  WITH CHECK (user_id = auth.uid());
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

-- hrv_measurements: 팀 기반 SELECT + INSERT + DELETE
CREATE POLICY "hrv_read_own_or_team" ON hrv_measurements FOR SELECT
  USING (
    user_id = auth.uid()
    OR user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role IN ('ADMIN', 'MANAGER')
    )
  );
CREATE POLICY "hrv_insert_own" ON hrv_measurements FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "hrv_delete_admin" ON hrv_measurements FOR DELETE
  USING (
    user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role = 'ADMIN'
    )
  );

-- daily_hrv_metrics: 팀 기반 SELECT + INSERT + DELETE
CREATE POLICY "daily_hrv_read_own_or_team" ON daily_hrv_metrics FOR SELECT
  USING (
    user_id = auth.uid()
    OR user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role IN ('ADMIN', 'MANAGER')
    )
  );
CREATE POLICY "daily_hrv_insert_own" ON daily_hrv_metrics FOR INSERT
  WITH CHECK (user_id = auth.uid());
CREATE POLICY "daily_hrv_delete_admin" ON daily_hrv_metrics FOR DELETE
  USING (
    user_id IN (
      SELECT tm2.user_id FROM team_members tm1
      JOIN team_members tm2 ON tm1.team_id = tm2.team_id
      WHERE tm1.user_id = auth.uid() AND tm1.role = 'ADMIN'
    )
  );

-- user_profiles: DELETE 정책 추가
CREATE POLICY "profiles_delete_own" ON user_profiles FOR DELETE
  USING (user_id = auth.uid());

-- =================================================================
-- ██ ETL 뷰 (00005 통합: B-04, B-12, B-20, B-22, B-24)
-- =================================================================

-- v_rnd_track_b: REST 포함 + ORDER BY 제거
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

-- v_rnd_track_a: strain, dcwr, tsb 추가 + ORDER BY 제거
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
  m.strain,
  m.dcwr_rolling,
  m.tsb_rolling,
  m.daily_load AS srpe
FROM daily_hrv_metrics h
LEFT JOIN computed_load_metrics m
  ON m.user_id = h.user_id AND m.metric_date = h.metric_date
WHERE h.valid = TRUE;

-- =================================================================
-- ██ 운영 개선 (00005 Phase 6)
-- =================================================================

-- B-14: updated_at 자동 갱신 트리거
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

-- B-23: hrv_measurements.session_id FK 문서화
COMMENT ON COLUMN hrv_measurements.session_id IS
  'FK → training_sessions. ON DELETE SET NULL: 세션 삭제 시에도 독립 측정(MORNING_REST, NIGHT_SLEEP) 데이터를 보존하기 위한 의도적 선택. DRD v2.0 B-23 참조.';

-- B-10: daily_hrv_metrics.measurement_id 선택 기준 문서화
COMMENT ON COLUMN daily_hrv_metrics.measurement_id IS
  'FK → hrv_measurements. 동일 날짜 다수 측정 시 MORNING_REST 우선, 동일 컨텍스트면 rr_count 최대 측정을 대표로 선택. DRD v2.0 B-10 참조.';

COMMIT;

-- =================================================================
-- ██ 시드 데이터
-- =================================================================

-- 데모 사용자
INSERT INTO users (id, email, name) VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin@demo.com', '관리자 김철수'),
  ('00000000-0000-0000-0000-000000000002', 'manager@demo.com', '매니저 이영희'),
  ('00000000-0000-0000-0000-000000000003', 'player1@demo.com', '선수 박민수'),
  ('00000000-0000-0000-0000-000000000004', 'player2@demo.com', '선수 정수진'),
  ('00000000-0000-0000-0000-000000000005', 'player3@demo.com', '선수 최동현')
ON CONFLICT (id) DO NOTHING;

-- 데모 팀
INSERT INTO teams (id, name, description, created_by) VALUES
  ('10000000-0000-0000-0000-000000000001', 'FC 번개', '주말 축구 동호회', '00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- 팀 멤버
INSERT INTO team_members (team_id, user_id, role) VALUES
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'ADMIN'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'MANAGER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000005', 'MEMBER')
ON CONFLICT (team_id, user_id) DO NOTHING;

-- 데모 경기
INSERT INTO matches (id, team_id, title, match_date, location, opponent, status, created_by) VALUES
  ('20000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001',
   '주말 리그전', '2026-02-15T14:00:00+09:00', '잠실 운동장', 'FC 태풍', 'OPEN',
   '00000000-0000-0000-0000-000000000001'),
  ('20000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001',
   '연습 경기', '2026-02-22T10:00:00+09:00', '올림픽공원', NULL, 'OPEN',
   '00000000-0000-0000-0000-000000000002')
ON CONFLICT (id) DO NOTHING;

-- 출석 투표 (첫 번째 경기)
INSERT INTO attendances (match_id, user_id, status, voted_at) VALUES
  ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'ACCEPTED', now()),
  ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'ACCEPTED', now()),
  ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'ACCEPTED', now()),
  ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000004', 'PENDING', NULL),
  ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000005', 'DECLINED', now())
ON CONFLICT (match_id, user_id) DO NOTHING;

-- 두 번째 경기 출석 투표
INSERT INTO attendances (match_id, user_id, status) VALUES
  ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'PENDING'),
  ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000002', 'PENDING'),
  ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003', 'PENDING'),
  ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000004', 'PENDING'),
  ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000005', 'PENDING')
ON CONFLICT (match_id, user_id) DO NOTHING;

-- 추가 사용자 (006~015)
INSERT INTO users (id, email, name) VALUES
  ('00000000-0000-0000-0000-000000000006', 'player4@demo.com',  '선수 한지민'),
  ('00000000-0000-0000-0000-000000000007', 'player5@demo.com',  '선수 오세훈'),
  ('00000000-0000-0000-0000-000000000008', 'player6@demo.com',  '선수 김도윤'),
  ('00000000-0000-0000-0000-000000000009', 'player7@demo.com',  '선수 이서연'),
  ('00000000-0000-0000-0000-000000000010', 'player8@demo.com',  '선수 박준혁'),
  ('00000000-0000-0000-0000-000000000011', 'player9@demo.com',  '선수 최예린'),
  ('00000000-0000-0000-0000-000000000012', 'player10@demo.com', '선수 강민준'),
  ('00000000-0000-0000-0000-000000000013', 'player11@demo.com', '선수 윤서아'),
  ('00000000-0000-0000-0000-000000000014', 'player12@demo.com', '선수 임태윤'),
  ('00000000-0000-0000-0000-000000000015', 'player13@demo.com', '선수 조하늘')
ON CONFLICT (id) DO NOTHING;

-- 추가 멤버 등록
INSERT INTO team_members (team_id, user_id, role) VALUES
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000006', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000007', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000008', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000009', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000013', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000014', 'MEMBER'),
  ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000015', 'MEMBER')
ON CONFLICT (team_id, user_id) DO NOTHING;

-- 사용자 프로필 (포지션 배정)
INSERT INTO user_profiles (user_id, position) VALUES
  ('00000000-0000-0000-0000-000000000001', 'GK'),
  ('00000000-0000-0000-0000-000000000002', 'CB'),
  ('00000000-0000-0000-0000-000000000003', 'ST'),
  ('00000000-0000-0000-0000-000000000004', 'CM'),
  ('00000000-0000-0000-0000-000000000005', 'CAM'),
  ('00000000-0000-0000-0000-000000000006', 'LW'),
  ('00000000-0000-0000-0000-000000000007', 'RB'),
  ('00000000-0000-0000-0000-000000000008', 'CDM'),
  ('00000000-0000-0000-0000-000000000009', 'LB'),
  ('00000000-0000-0000-0000-000000000010', 'RW'),
  ('00000000-0000-0000-0000-000000000011', 'CF'),
  ('00000000-0000-0000-0000-000000000012', 'CM'),
  ('00000000-0000-0000-0000-000000000013', 'RM'),
  ('00000000-0000-0000-0000-000000000014', 'CB'),
  ('00000000-0000-0000-0000-000000000015', 'WB')
ON CONFLICT (user_id) DO NOTHING;

-- =================================================================
-- 00005_schema_fixes.sql
-- DRD v2.0/v3.0 기반 수정 마이그레이션
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
-- [B-02] user_id 이중 저장 제거 준비: 의존 객체 선제거
-- 위험: RLS 정책과 인덱스가 user_id에 의존하므로 먼저 제거
-- -----------------------------------------------------------------

-- 3개 하위 테이블의 기존 RLS 정책 제거 (user_id 의존)
DROP POLICY IF EXISTS "pre_wellness_read_own" ON pre_session_wellness;
DROP POLICY IF EXISTS "pre_wellness_insert_own" ON pre_session_wellness;
DROP POLICY IF EXISTS "pre_wellness_update_own" ON pre_session_wellness;

DROP POLICY IF EXISTS "post_feedback_read_own" ON post_session_feedback;
DROP POLICY IF EXISTS "post_feedback_insert_own" ON post_session_feedback;
DROP POLICY IF EXISTS "post_feedback_update_own" ON post_session_feedback;

DROP POLICY IF EXISTS "next_day_read_own" ON next_day_reviews;
DROP POLICY IF EXISTS "next_day_insert_own" ON next_day_reviews;
DROP POLICY IF EXISTS "next_day_update_own" ON next_day_reviews;

-- user_id 의존 인덱스 제거
DROP INDEX IF EXISTS idx_pre_wellness_user;
DROP INDEX IF EXISTS idx_post_feedback_user;
DROP INDEX IF EXISTS idx_next_day_user;

-- [B-02] user_id 컬럼 제거
-- 주의: 기존 데이터가 있으면 user_id 컬럼 값을 session 경유로
--       검증한 뒤 DROP해야 함. 시드 데이터만 있는 PoV에서는 안전.
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
-- 기존 정책은 Phase 1(B-02 준비)에서 이미 제거됨
-- -----------------------------------------------------------------
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
-- 기존 정책은 Phase 1(B-02 준비)에서 이미 제거됨
-- -----------------------------------------------------------------
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
-- 기존 정책은 Phase 1(B-02 준비)에서 이미 제거됨
-- -----------------------------------------------------------------
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
-- DROP 필요: 기존 뷰에 없는 컬럼(strain, dcwr_rolling, tsb_rolling) 추가
-- -----------------------------------------------------------------
DROP VIEW IF EXISTS v_rnd_track_a;
CREATE VIEW v_rnd_track_a AS
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

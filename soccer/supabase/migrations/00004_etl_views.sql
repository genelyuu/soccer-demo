-- ETL 뷰: soccer_rnd 트랙 A/B 표준 스키마로 변환
-- 의존: 00003_training_wellness_schema.sql
-- PoV 단계에서는 pgcrypto 없이 user_id::text를 직접 식별자로 사용

-- ============================================================
-- 1. v_rnd_track_b — 트랙 B 표준 스키마 (부하 + 웰니스)
-- ============================================================
-- 출력 스키마: athlete_id, date, rpe, duration_min, srpe,
--             fatigue, stress, doms, sleep, hooper_index,
--             session_type, match_day, next_day_score

CREATE OR REPLACE VIEW v_rnd_track_b AS
SELECT
  ts.user_id::text AS athlete_id,

  ts.session_date AS date,

  ps.session_rpe AS rpe,
  ts.duration_min,
  (ps.session_rpe * ts.duration_min) AS srpe,

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

-- ============================================================
-- 2. v_rnd_track_a — 트랙 A 표준 스키마 (HRV + 부하)
-- ============================================================
-- 출력 스키마: subject_id, date, rmssd, sdnn, ln_rmssd, ln_rmssd_7d,
--             mean_hr, nn_count, acwr_rolling, acwr_ewma, monotony, srpe

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

-- RLS 쓰기 정책 세분화 (INSERT / UPDATE / DELETE)
-- 기존 00001에서 SELECT 정책만 정의됨 → 쓰기 정책 추가

-- ============================================================
-- 1. users — 인증된 사용자 본인만 INSERT/UPDATE
-- ============================================================
CREATE POLICY "users_insert_own" ON users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- users_update_own은 이미 00001에서 정의됨

-- ============================================================
-- 2. teams — 인증된 사용자 INSERT, ADMIN만 UPDATE/DELETE
-- ============================================================
CREATE POLICY "teams_insert_authenticated" ON teams FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "teams_update_admin" ON teams FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = teams.id
        AND team_members.user_id = auth.uid()
        AND team_members.role = 'ADMIN'
    )
  );

CREATE POLICY "teams_delete_admin" ON teams FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = teams.id
        AND team_members.user_id = auth.uid()
        AND team_members.role = 'ADMIN'
    )
  );

-- ============================================================
-- 3. team_members — ADMIN INSERT/DELETE, MANAGER INSERT
-- ============================================================
CREATE POLICY "team_members_insert_admin_manager" ON team_members FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM team_members AS tm
      WHERE tm.team_id = team_members.team_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

CREATE POLICY "team_members_delete_admin" ON team_members FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM team_members AS tm
      WHERE tm.team_id = team_members.team_id
        AND tm.user_id = auth.uid()
        AND tm.role = 'ADMIN'
    )
  );

CREATE POLICY "team_members_update_admin" ON team_members FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM team_members AS tm
      WHERE tm.team_id = team_members.team_id
        AND tm.user_id = auth.uid()
        AND tm.role = 'ADMIN'
    )
  );

-- ============================================================
-- 4. matches — MANAGER+ INSERT/UPDATE (팀 소속 확인)
-- ============================================================
CREATE POLICY "matches_insert_manager" ON matches FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = matches.team_id
        AND team_members.user_id = auth.uid()
        AND team_members.role IN ('ADMIN', 'MANAGER')
    )
  );

CREATE POLICY "matches_update_manager" ON matches FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = matches.team_id
        AND team_members.user_id = auth.uid()
        AND team_members.role IN ('ADMIN', 'MANAGER')
    )
  );

CREATE POLICY "matches_delete_admin" ON matches FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = matches.team_id
        AND team_members.user_id = auth.uid()
        AND team_members.role = 'ADMIN'
    )
  );

-- ============================================================
-- 5. attendances — MEMBER+ 본인 투표만 UPDATE
-- ============================================================
CREATE POLICY "attendances_insert_manager" ON attendances FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM matches m
      JOIN team_members tm ON tm.team_id = m.team_id
      WHERE m.id = attendances.match_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

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

-- ============================================================
-- 6. record_rooms — MANAGER+ INSERT
-- ============================================================
CREATE POLICY "record_rooms_insert_manager" ON record_rooms FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM matches m
      JOIN team_members tm ON tm.team_id = m.team_id
      WHERE m.id = record_rooms.match_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

CREATE POLICY "record_rooms_update_manager" ON record_rooms FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM matches m
      JOIN team_members tm ON tm.team_id = m.team_id
      WHERE m.id = record_rooms.match_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

-- ============================================================
-- 7. match_records — MANAGER+ INSERT/UPDATE
-- ============================================================
CREATE POLICY "match_records_insert_manager" ON match_records FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM record_rooms rr
      JOIN matches m ON m.id = rr.match_id
      JOIN team_members tm ON tm.team_id = m.team_id
      WHERE rr.id = match_records.record_room_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

CREATE POLICY "match_records_update_manager" ON match_records FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM record_rooms rr
      JOIN matches m ON m.id = rr.match_id
      JOIN team_members tm ON tm.team_id = m.team_id
      WHERE rr.id = match_records.record_room_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

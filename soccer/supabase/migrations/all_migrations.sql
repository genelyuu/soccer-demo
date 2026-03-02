-- ============================================================
-- 전체 마이그레이션 스크립트
-- Supabase Dashboard > SQL Editor에서 실행하세요
-- ============================================================

-- ============================================================
-- 마이그레이션 1: 초기 스키마
-- ============================================================

-- 초기 스키마: 축구 동호회 운영 루프 MVP
-- 엔터티: users, teams, team_members, matches, attendances, record_rooms, match_records

-- ============================================================
-- 1. Users (사용자)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================
-- 2. Teams (팀)
-- ============================================================
CREATE TABLE IF NOT EXISTS teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  logo_url TEXT,
  created_by UUID NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- ============================================================
-- 3. Team Members (팀 멤버)
-- ============================================================
CREATE TYPE IF NOT EXISTS team_role AS ENUM ('ADMIN', 'MANAGER', 'MEMBER', 'GUEST');

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

-- ============================================================
-- 4. Matches (경기)
-- ============================================================
CREATE TYPE IF NOT EXISTS match_status AS ENUM ('OPEN', 'CONFIRMED', 'COMPLETED', 'CANCELLED');

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

-- ============================================================
-- 5. Attendances (출석/투표)
-- ============================================================
CREATE TYPE IF NOT EXISTS attendance_status AS ENUM ('PENDING', 'ACCEPTED', 'DECLINED', 'MAYBE');

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

-- ============================================================
-- 6. Record Rooms (기록실)
-- ============================================================
CREATE TYPE IF NOT EXISTS record_room_status AS ENUM ('OPEN', 'CLOSED');

CREATE TABLE IF NOT EXISTS record_rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id UUID UNIQUE NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
  status record_room_status NOT NULL DEFAULT 'OPEN',
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  closed_at TIMESTAMPTZ
);

-- match_id에 UNIQUE 제약 → 경기당 기록실 1개만 (멱등성 보장)

-- ============================================================
-- 7. Match Records (경기 기록)
-- ============================================================
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

-- ============================================================
-- RLS (Row Level Security) 기본 정책
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendances ENABLE ROW LEVEL SECURITY;
ALTER TABLE record_rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_records ENABLE ROW LEVEL SECURITY;

-- 기본 RLS 정책: 인증된 사용자만 읽기 가능
-- (MVP 단계 최소 정책 — 추후 팀 기반 세분화 필요)
DROP POLICY IF EXISTS "users_read_own" ON users;
CREATE POLICY "users_read_own" ON users FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "users_update_own" ON users;
CREATE POLICY "users_update_own" ON users FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "teams_read_member" ON teams;
CREATE POLICY "teams_read_member" ON teams FOR SELECT
  USING (id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "team_members_read" ON team_members;
CREATE POLICY "team_members_read" ON team_members FOR SELECT
  USING (team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "matches_read_team" ON matches;
CREATE POLICY "matches_read_team" ON matches FOR SELECT
  USING (team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "attendances_read_team" ON attendances;
CREATE POLICY "attendances_read_team" ON attendances FOR SELECT
  USING (match_id IN (
    SELECT m.id FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE tm.user_id = auth.uid()
  ));

DROP POLICY IF EXISTS "record_rooms_read" ON record_rooms;
CREATE POLICY "record_rooms_read" ON record_rooms FOR SELECT
  USING (match_id IN (
    SELECT m.id FROM matches m
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE tm.user_id = auth.uid()
  ));

DROP POLICY IF EXISTS "match_records_read" ON match_records;
CREATE POLICY "match_records_read" ON match_records FOR SELECT
  USING (record_room_id IN (
    SELECT rr.id FROM record_rooms rr
    JOIN matches m ON m.id = rr.match_id
    JOIN team_members tm ON tm.team_id = m.team_id
    WHERE tm.user_id = auth.uid()
  ));

-- ============================================================
-- 마이그레이션 2: RLS 쓰기 정책 세분화
-- ============================================================

-- ============================================================
-- 1. users — 인증된 사용자 본인만 INSERT/UPDATE
-- ============================================================
DROP POLICY IF EXISTS "users_insert_own" ON users;
CREATE POLICY "users_insert_own" ON users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- users_update_own은 이미 위에서 정의됨

-- ============================================================
-- 2. teams — 인증된 사용자 INSERT, ADMIN만 UPDATE/DELETE
-- ============================================================
DROP POLICY IF EXISTS "teams_insert_authenticated" ON teams;
CREATE POLICY "teams_insert_authenticated" ON teams FOR INSERT
  WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "teams_update_admin" ON teams;
CREATE POLICY "teams_update_admin" ON teams FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = teams.id
        AND team_members.user_id = auth.uid()
        AND team_members.role = 'ADMIN'
    )
  );

DROP POLICY IF EXISTS "teams_delete_admin" ON teams;
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
DROP POLICY IF EXISTS "team_members_insert_admin_manager" ON team_members;
CREATE POLICY "team_members_insert_admin_manager" ON team_members FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM team_members AS tm
      WHERE tm.team_id = team_members.team_id
        AND tm.user_id = auth.uid()
        AND tm.role IN ('ADMIN', 'MANAGER')
    )
  );

DROP POLICY IF EXISTS "team_members_delete_admin" ON team_members;
CREATE POLICY "team_members_delete_admin" ON team_members FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM team_members AS tm
      WHERE tm.team_id = team_members.team_id
        AND tm.user_id = auth.uid()
        AND tm.role = 'ADMIN'
    )
  );

DROP POLICY IF EXISTS "team_members_update_admin" ON team_members;
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
DROP POLICY IF EXISTS "matches_insert_manager" ON matches;
CREATE POLICY "matches_insert_manager" ON matches FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = matches.team_id
        AND team_members.user_id = auth.uid()
        AND team_members.role IN ('ADMIN', 'MANAGER')
    )
  );

DROP POLICY IF EXISTS "matches_update_manager" ON matches;
CREATE POLICY "matches_update_manager" ON matches FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM team_members
      WHERE team_members.team_id = matches.team_id
        AND team_members.user_id = auth.uid()
        AND team_members.role IN ('ADMIN', 'MANAGER')
    )
  );

DROP POLICY IF EXISTS "matches_delete_admin" ON matches;
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
DROP POLICY IF EXISTS "attendances_insert_manager" ON attendances;
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

DROP POLICY IF EXISTS "attendances_update_own_vote" ON attendances;
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
DROP POLICY IF EXISTS "record_rooms_insert_manager" ON record_rooms;
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

DROP POLICY IF EXISTS "record_rooms_update_manager" ON record_rooms;
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
DROP POLICY IF EXISTS "match_records_insert_manager" ON match_records;
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

DROP POLICY IF EXISTS "match_records_update_manager" ON match_records;
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

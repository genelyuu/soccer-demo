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

CREATE INDEX idx_users_email ON users(email);

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
CREATE TYPE team_role AS ENUM ('ADMIN', 'MANAGER', 'MEMBER', 'GUEST');

CREATE TABLE IF NOT EXISTS team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role team_role NOT NULL DEFAULT 'MEMBER',
  joined_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  UNIQUE(team_id, user_id)
);

CREATE INDEX idx_team_members_team ON team_members(team_id);
CREATE INDEX idx_team_members_user ON team_members(user_id);

-- ============================================================
-- 4. Matches (경기)
-- ============================================================
CREATE TYPE match_status AS ENUM ('OPEN', 'CONFIRMED', 'COMPLETED', 'CANCELLED');

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

CREATE INDEX idx_matches_team ON matches(team_id);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_date ON matches(match_date);

-- ============================================================
-- 5. Attendances (출석/투표)
-- ============================================================
CREATE TYPE attendance_status AS ENUM ('PENDING', 'ACCEPTED', 'DECLINED', 'MAYBE');

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

CREATE INDEX idx_attendances_match ON attendances(match_id);
CREATE INDEX idx_attendances_user ON attendances(user_id);

-- ============================================================
-- 6. Record Rooms (기록실)
-- ============================================================
CREATE TYPE record_room_status AS ENUM ('OPEN', 'CLOSED');

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

CREATE INDEX idx_match_records_room ON match_records(record_room_id);
CREATE INDEX idx_match_records_user ON match_records(user_id);

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

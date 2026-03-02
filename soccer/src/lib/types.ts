// 도메인 타입 정의 — DB 스키마(supabase/migrations/00001_initial_schema.sql) 기반

export type TeamRole = 'ADMIN' | 'MANAGER' | 'MEMBER' | 'GUEST';
export type MatchStatus = 'OPEN' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED';
export type AttendanceStatus = 'PENDING' | 'ACCEPTED' | 'DECLINED' | 'MAYBE';
export type RecordRoomStatus = 'OPEN' | 'CLOSED';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: string;
  name: string;
  description: string | null;
  logo_url: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: TeamRole;
  joined_at: string;
}

export interface Match {
  id: string;
  team_id: string;
  title: string;
  description: string | null;
  match_date: string;
  location: string | null;
  opponent: string | null;
  status: MatchStatus;
  created_by: string;
  confirmed_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Attendance {
  id: string;
  match_id: string;
  user_id: string;
  status: AttendanceStatus;
  voted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecordRoom {
  id: string;
  match_id: string;
  status: RecordRoomStatus;
  created_at: string;
  closed_at: string | null;
}

export interface MatchRecord {
  id: string;
  record_room_id: string;
  user_id: string;
  goals: number;
  assists: number;
  yellow_cards: number;
  red_cards: number;
  memo: string | null;
  created_at: string;
  updated_at: string;
}

/** match_records JOIN users — 기록실 조회 시 유저 정보 포함 */
export interface RecordWithUser extends MatchRecord {
  users: { id: string; name: string; avatar_url: string | null };
}

// User 도메인 전용 타입 — DRD v3.0 users 테이블 기반
// 기존 User 인터페이스는 src/lib/types.ts에서 재사용

export type { User } from "@/lib/types";
import type { User } from "@/lib/types";

export interface CreateUserInput {
  email: string;
  name: string;
  avatar_url?: string;
}

export interface UpdateUserInput {
  name?: string;
  avatar_url?: string | null;
}

export interface UsersListOptions {
  page?: number;
  limit?: number;
  orderBy?: "created_at" | "name" | "email";
  ascending?: boolean;
}

export interface UserResult {
  data: User | null;
  error: string | null;
}

export interface UsersListResult {
  data: User[];
  count: number;
  error: string | null;
}

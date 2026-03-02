import "server-only";

import { createPureClient } from "@/lib/supabase/server";
import type {
  CreateUserInput,
  UpdateUserInput,
  UsersListOptions,
  UserResult,
  UsersListResult,
} from "@/lib/supabase/types/user";

const USER_COLUMNS = "id, email, name, avatar_url, created_at, updated_at" as const;

/**
 * 사용자 생성 — 원자적 단일 insert.
 * email UNIQUE 제약에 의해 중복 시 즉시 실패.
 */
export async function createUser(input: CreateUserInput): Promise<UserResult> {
  const supabase = await createPureClient();

  const { data, error } = await supabase
    .from("users")
    .insert({
      email: input.email,
      name: input.name,
      avatar_url: input.avatar_url ?? null,
    })
    .select(USER_COLUMNS)
    .single();

  if (error) {
    return { data: null, error: error.message };
  }
  return { data, error: null };
}

/**
 * ID로 사용자 단건 조회.
 */
export async function getUserById(id: string): Promise<UserResult> {
  const supabase = await createPureClient();

  const { data, error } = await supabase
    .from("users")
    .select(USER_COLUMNS)
    .eq("id", id)
    .single();

  if (error) {
    return { data: null, error: error.message };
  }
  return { data, error: null };
}

/**
 * 이메일로 사용자 단건 조회.
 */
export async function getUserByEmail(email: string): Promise<UserResult> {
  const supabase = await createPureClient();

  const { data, error } = await supabase
    .from("users")
    .select(USER_COLUMNS)
    .eq("email", email)
    .single();

  if (error) {
    return { data: null, error: error.message };
  }
  return { data, error: null };
}

/**
 * 사용자 목록 조회 — 페이지네이션 지원.
 * 기본값: page=1, limit=20, orderBy=created_at DESC.
 */
export async function getUsers(options?: UsersListOptions): Promise<UsersListResult> {
  const page = options?.page ?? 1;
  const limit = options?.limit ?? 20;
  const orderBy = options?.orderBy ?? "created_at";
  const ascending = options?.ascending ?? false;

  const from = (page - 1) * limit;
  const to = from + limit - 1;

  const supabase = await createPureClient();

  const { data, count, error } = await supabase
    .from("users")
    .select(USER_COLUMNS, { count: "exact" })
    .order(orderBy, { ascending })
    .range(from, to);

  if (error) {
    return { data: [], count: 0, error: error.message };
  }
  return { data: data ?? [], count: count ?? 0, error: null };
}

/**
 * 사용자 수정 — 원자적 단일 update.
 * updated_at을 서버 타임스탬프로 강제 갱신.
 */
export async function updateUser(id: string, input: UpdateUserInput): Promise<UserResult> {
  const supabase = await createPureClient();

  const { data, error } = await supabase
    .from("users")
    .update({
      ...input,
      updated_at: new Date().toISOString(),
    })
    .eq("id", id)
    .select(USER_COLUMNS)
    .single();

  if (error) {
    return { data: null, error: error.message };
  }
  return { data, error: null };
}

/**
 * 사용자 삭제 — 원자적 단일 delete.
 * DRD v3.0 경고: CASCADE 체인으로 최대 ~780행 연쇄 삭제 발생.
 */
export async function deleteUser(id: string): Promise<{ error: string | null }> {
  const supabase = await createPureClient();

  const { error } = await supabase
    .from("users")
    .delete()
    .eq("id", id);

  if (error) {
    return { error: error.message };
  }
  return { error: null };
}

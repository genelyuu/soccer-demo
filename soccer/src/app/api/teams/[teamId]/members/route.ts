import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";
import { canModifyMembers } from "@/features/team/lib/authorization";
import type { TeamRole } from "@/lib/types";

const addMemberSchema = z.object({
  email: z.string().email("유효한 이메일을 입력해주세요"),
  role: z.enum(["MANAGER", "MEMBER", "GUEST"]).default("MEMBER"),
});

// GET /api/teams/[teamId]/members — 팀 멤버 목록
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ teamId: string }> }
) {
  const { teamId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  // 소속 확인
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!membership) {
    return NextResponse.json({ error: "팀에 소속되어 있지 않습니다" }, { status: 403 });
  }

  const { data: members } = await supabase
    .from("team_members")
    .select("id, role, joined_at, users:user_id(id, name, email, avatar_url)")
    .eq("team_id", teamId);

  return NextResponse.json({ members: members ?? [], my_role: membership.role });
}

// POST /api/teams/[teamId]/members — 멤버 추가 (이메일로 초대)
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ teamId: string }> }
) {
  const { teamId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = addMemberSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 권한 확인: ADMIN/MANAGER만 멤버 추가 가능
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !canModifyMembers(membership.role as TeamRole)) {
    return NextResponse.json({ error: "멤버 추가 권한이 없습니다" }, { status: 403 });
  }

  // 이메일로 사용자 조회
  const { data: user } = await supabase
    .from("users")
    .select("id")
    .eq("email", parsed.data.email)
    .single();

  if (!user) {
    return NextResponse.json({ error: "해당 이메일의 사용자를 찾을 수 없습니다" }, { status: 404 });
  }

  // 멤버 추가
  const { error } = await supabase
    .from("team_members")
    .insert({
      team_id: teamId,
      user_id: user.id,
      role: parsed.data.role,
    });

  if (error) {
    if (error.code === "23505") {
      return NextResponse.json({ error: "이미 팀에 소속된 사용자입니다" }, { status: 409 });
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ message: "멤버가 추가되었습니다" }, { status: 201 });
}

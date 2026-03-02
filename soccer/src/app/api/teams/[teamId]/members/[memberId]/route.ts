import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";
import { canChangeRole, canRemoveMember } from "@/features/team/lib/authorization";
import type { TeamRole } from "@/lib/types";

const updateRoleSchema = z.object({
  role: z.enum(["ADMIN", "MANAGER", "MEMBER", "GUEST"], {
    errorMap: () => ({ message: "유효하지 않은 역할입니다" }),
  }),
});

type RouteContext = { params: Promise<{ teamId: string; memberId: string }> };

// PATCH /api/teams/[teamId]/members/[memberId] — 역할 변경 (ADMIN만)
export async function PATCH(
  request: NextRequest,
  { params }: RouteContext,
) {
  const { teamId, memberId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = updateRoleSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 요청자 권한 확인
  const { data: actorMembership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!actorMembership || !canChangeRole(actorMembership.role as TeamRole)) {
    return NextResponse.json({ error: "역할 변경 권한이 없습니다" }, { status: 403 });
  }

  const { error } = await supabase
    .from("team_members")
    .update({ role: parsed.data.role })
    .eq("id", memberId)
    .eq("team_id", teamId);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ message: "역할이 변경되었습니다" });
}

// DELETE /api/teams/[teamId]/members/[memberId] — 멤버 제거
export async function DELETE(
  _request: NextRequest,
  { params }: RouteContext,
) {
  const { teamId, memberId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  // 요청자 권한 확인
  const { data: actorMembership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!actorMembership) {
    return NextResponse.json({ error: "팀에 소속되어 있지 않습니다" }, { status: 403 });
  }

  // 대상 멤버 조회
  const { data: targetMember } = await supabase
    .from("team_members")
    .select("role")
    .eq("id", memberId)
    .eq("team_id", teamId)
    .single();

  if (!targetMember) {
    return NextResponse.json({ error: "멤버를 찾을 수 없습니다" }, { status: 404 });
  }

  if (
    !canRemoveMember(
      actorMembership.role as TeamRole,
      targetMember.role as TeamRole,
    )
  ) {
    return NextResponse.json({ error: "해당 멤버를 제거할 권한이 없습니다" }, { status: 403 });
  }

  const { error } = await supabase
    .from("team_members")
    .delete()
    .eq("id", memberId)
    .eq("team_id", teamId);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ message: "멤버가 제거되었습니다" });
}

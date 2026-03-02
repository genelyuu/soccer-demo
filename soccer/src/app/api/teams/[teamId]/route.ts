import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";
import { canModifyTeam, canDeleteTeam } from "@/features/team/lib/authorization";
import type { TeamRole } from "@/lib/types";

const updateTeamSchema = z.object({
  name: z.string().min(1, "팀명을 입력해주세요").optional(),
  description: z.string().optional(),
});

type RouteContext = { params: Promise<{ teamId: string }> };

// GET /api/teams/[teamId] — 팀 상세 + myRole
export async function GET(
  _request: NextRequest,
  { params }: RouteContext,
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

  const { data: team, error } = await supabase
    .from("teams")
    .select("*")
    .eq("id", teamId)
    .single();

  if (error || !team) {
    return NextResponse.json({ error: "팀을 찾을 수 없습니다" }, { status: 404 });
  }

  return NextResponse.json({ team, my_role: membership.role });
}

// PATCH /api/teams/[teamId] — 팀 수정 (ADMIN/MANAGER)
export async function PATCH(
  request: NextRequest,
  { params }: RouteContext,
) {
  const { teamId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = updateTeamSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 권한 확인
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !canModifyTeam(membership.role as TeamRole)) {
    return NextResponse.json({ error: "팀 수정 권한이 없습니다" }, { status: 403 });
  }

  const { data: team, error } = await supabase
    .from("teams")
    .update({ ...parsed.data, updated_at: new Date().toISOString() })
    .eq("id", teamId)
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ team });
}

// DELETE /api/teams/[teamId] — 팀 삭제 (ADMIN)
export async function DELETE(
  _request: NextRequest,
  { params }: RouteContext,
) {
  const { teamId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  // 권한 확인
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !canDeleteTeam(membership.role as TeamRole)) {
    return NextResponse.json({ error: "팀 삭제 권한이 없습니다" }, { status: 403 });
  }

  const { error } = await supabase.from("teams").delete().eq("id", teamId);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ message: "팀이 삭제되었습니다" });
}

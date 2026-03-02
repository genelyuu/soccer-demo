import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { canVoteAttendance } from "@/features/team/lib/authorization";
import { z } from "zod";

const voteSchema = z.object({
  status: z.enum(["ACCEPTED", "DECLINED", "MAYBE"]),
});

// PATCH /api/matches/[id]/attendance — 출석 투표
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: matchId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = voteSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: "유효하지 않은 투표 상태입니다" }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 경기 조회 (team_id 포함)
  const { data: match } = await supabase
    .from("matches")
    .select("team_id, status")
    .eq("id", matchId)
    .single();

  if (!match) {
    return NextResponse.json({ error: "경기를 찾을 수 없습니다" }, { status: 404 });
  }

  if (match.status !== "OPEN") {
    return NextResponse.json({ error: "투표가 마감되었습니다" }, { status: 409 });
  }

  // 권한 확인: ADMIN/MANAGER/MEMBER만 투표 가능 (GUEST 차단)
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", match.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !canVoteAttendance(membership.role)) {
    return NextResponse.json({ error: "출석 투표 권한이 없습니다" }, { status: 403 });
  }

  // 출석 레코드 업데이트
  const { data: attendance, error } = await supabase
    .from("attendances")
    .update({
      status: parsed.data.status,
      voted_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("match_id", matchId)
    .eq("user_id", session.user.id)
    .select()
    .single();

  if (error || !attendance) {
    return NextResponse.json({ error: "투표에 실패했습니다" }, { status: 500 });
  }

  return NextResponse.json({ attendance });
}

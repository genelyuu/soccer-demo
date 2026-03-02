import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";

// PATCH /api/matches/[id]/record/close — 기록실 마감 + 경기 COMPLETED 전이
export async function PATCH(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: matchId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  // 경기 조회
  const { data: match } = await supabase
    .from("matches")
    .select("id, team_id, status")
    .eq("id", matchId)
    .single();

  if (!match) {
    return NextResponse.json({ error: "경기를 찾을 수 없습니다" }, { status: 404 });
  }

  // 권한 확인: MANAGER 이상
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", match.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !["ADMIN", "MANAGER"].includes(membership.role)) {
    return NextResponse.json({ error: "기록실 마감 권한이 없습니다" }, { status: 403 });
  }

  // 기록실 조회
  const { data: recordRoom } = await supabase
    .from("record_rooms")
    .select("*")
    .eq("match_id", matchId)
    .single();

  if (!recordRoom) {
    return NextResponse.json({ error: "기록실을 찾을 수 없습니다" }, { status: 404 });
  }

  // 이미 마감된 경우 멱등하게 기존 데이터 반환
  if (recordRoom.status === "CLOSED") {
    return NextResponse.json({
      record_room: recordRoom,
      match,
      message: "기록실이 이미 마감되었습니다",
    }, { status: 409 });
  }

  // 경기가 CONFIRMED 상태여야 마감 가능
  if (match.status !== "CONFIRMED") {
    return NextResponse.json(
      { error: "CONFIRMED 상태의 경기만 마감할 수 있습니다" },
      { status: 409 }
    );
  }

  const now = new Date().toISOString();

  // 기록실 CLOSED 처리
  const { data: closedRoom, error: roomError } = await supabase
    .from("record_rooms")
    .update({
      status: "CLOSED",
      closed_at: now,
    })
    .eq("id", recordRoom.id)
    .select()
    .single();

  if (roomError) {
    return NextResponse.json({ error: "기록실 마감에 실패했습니다" }, { status: 500 });
  }

  // 경기 COMPLETED 전이
  const { data: updatedMatch, error: matchError } = await supabase
    .from("matches")
    .update({
      status: "COMPLETED",
      completed_at: now,
      updated_at: now,
    })
    .eq("id", matchId)
    .select()
    .single();

  if (matchError) {
    return NextResponse.json({ error: "경기 상태 변경에 실패했습니다" }, { status: 500 });
  }

  return NextResponse.json({
    record_room: closedRoom,
    match: updatedMatch,
  });
}

import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";

// PATCH /api/matches/[id]/confirm — 경기 확정 + 기록실 자동 생성
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

  // 이미 확정된 경기는 멱등하게 처리 (중복 확정 방지)
  if (match.status === "CONFIRMED" || match.status === "COMPLETED") {
    const { data: existingRoom } = await supabase
      .from("record_rooms")
      .select("id")
      .eq("match_id", matchId)
      .single();

    return NextResponse.json({
      match: { ...match },
      record_room: existingRoom,
      message: "이미 확정된 경기입니다",
    });
  }

  if (match.status !== "OPEN") {
    return NextResponse.json({ error: "OPEN 상태의 경기만 확정할 수 있습니다" }, { status: 409 });
  }

  // 권한 확인: MANAGER 이상
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", match.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !["ADMIN", "MANAGER"].includes(membership.role)) {
    return NextResponse.json({ error: "경기 확정 권한이 없습니다" }, { status: 403 });
  }

  // 경기 상태를 CONFIRMED로 변경
  const { data: updatedMatch, error: matchError } = await supabase
    .from("matches")
    .update({
      status: "CONFIRMED",
      confirmed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
    .eq("id", matchId)
    .select()
    .single();

  if (matchError) {
    return NextResponse.json({ error: "경기 확정에 실패했습니다" }, { status: 500 });
  }

  // 기록실(RecordRoom) 자동 생성
  // UNIQUE(match_id) 제약이 있으므로 중복 시 INSERT 실패 → 멱등성 보장
  const { data: recordRoom, error: roomError } = await supabase
    .from("record_rooms")
    .insert({
      match_id: matchId,
      status: "OPEN",
    })
    .select()
    .single();

  if (roomError) {
    // UNIQUE 위반(중복)인 경우 기존 기록실 반환
    const { data: existingRoom } = await supabase
      .from("record_rooms")
      .select("*")
      .eq("match_id", matchId)
      .single();

    return NextResponse.json({
      match: updatedMatch,
      record_room: existingRoom,
    });
  }

  return NextResponse.json({
    match: updatedMatch,
    record_room: recordRoom,
  });
}

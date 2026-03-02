import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";

const recordSchema = z.object({
  user_id: z.string().uuid(),
  goals: z.number().int().min(0).default(0),
  assists: z.number().int().min(0).default(0),
  yellow_cards: z.number().int().min(0).default(0),
  red_cards: z.number().int().min(0).default(0),
  memo: z.string().optional(),
});

// GET /api/matches/[id]/record — 기록실 조회
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: matchId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  // 기록실 조회
  const { data: recordRoom } = await supabase
    .from("record_rooms")
    .select("*")
    .eq("match_id", matchId)
    .single();

  if (!recordRoom) {
    return NextResponse.json({ error: "기록실이 없습니다. 경기가 확정되지 않았습니다." }, { status: 404 });
  }

  // 기록 조회
  const { data: records } = await supabase
    .from("match_records")
    .select("*, users:user_id(id, name, avatar_url)")
    .eq("record_room_id", recordRoom.id);

  return NextResponse.json({
    record_room: recordRoom,
    records: records ?? [],
  });
}

// POST /api/matches/[id]/record — 기록 입력/수정
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: matchId } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = recordSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 경기 확인 및 권한 체크
  const { data: match } = await supabase
    .from("matches")
    .select("team_id, status")
    .eq("id", matchId)
    .single();

  if (!match) {
    return NextResponse.json({ error: "경기를 찾을 수 없습니다" }, { status: 404 });
  }

  // MANAGER 이상만 기록 입력 가능
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", match.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !["ADMIN", "MANAGER"].includes(membership.role)) {
    return NextResponse.json({ error: "기록 입력 권한이 없습니다" }, { status: 403 });
  }

  // 기록실 조회
  const { data: recordRoom } = await supabase
    .from("record_rooms")
    .select("id, status")
    .eq("match_id", matchId)
    .single();

  if (!recordRoom) {
    return NextResponse.json({ error: "기록실이 없습니다" }, { status: 404 });
  }

  if (recordRoom.status === "CLOSED") {
    return NextResponse.json({ error: "기록실이 마감되었습니다" }, { status: 409 });
  }

  // UPSERT: 이미 존재하면 업데이트
  const { data: record, error } = await supabase
    .from("match_records")
    .upsert(
      {
        record_room_id: recordRoom.id,
        user_id: parsed.data.user_id,
        goals: parsed.data.goals,
        assists: parsed.data.assists,
        yellow_cards: parsed.data.yellow_cards,
        red_cards: parsed.data.red_cards,
        memo: parsed.data.memo,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "record_room_id,user_id" }
    )
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: "기록 저장에 실패했습니다" }, { status: 500 });
  }

  return NextResponse.json({ record }, { status: 201 });
}

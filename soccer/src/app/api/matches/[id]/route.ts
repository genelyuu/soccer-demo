import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";

const updateMatchSchema = z.object({
  title: z.string().min(1).optional(),
  description: z.string().optional(),
  match_date: z.string().datetime().optional(),
  location: z.string().optional(),
  opponent: z.string().optional(),
});

// GET /api/matches/[id] — 경기 상세 조회
export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  const { data: match, error } = await supabase
    .from("matches")
    .select("*")
    .eq("id", id)
    .single();

  if (error || !match) {
    return NextResponse.json({ error: "경기를 찾을 수 없습니다" }, { status: 404 });
  }

  // 소속 팀 확인
  const { data: membership } = await supabase
    .from("team_members")
    .select("id")
    .eq("team_id", match.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership) {
    return NextResponse.json({ error: "접근 권한이 없습니다" }, { status: 403 });
  }

  // 출석 투표 현황 함께 조회
  const { data: attendances } = await supabase
    .from("attendances")
    .select("*, users:user_id(id, name, avatar_url)")
    .eq("match_id", id);

  return NextResponse.json({ match, attendances: attendances ?? [] });
}

// PATCH /api/matches/[id] — 경기 수정
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = updateMatchSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0].message },
      { status: 400 }
    );
  }

  const supabase = await createPureClient();

  // 경기 조회
  const { data: match } = await supabase
    .from("matches")
    .select("team_id, status")
    .eq("id", id)
    .single();

  if (!match) {
    return NextResponse.json({ error: "경기를 찾을 수 없습니다" }, { status: 404 });
  }

  if (match.status !== "OPEN") {
    return NextResponse.json({ error: "OPEN 상태의 경기만 수정할 수 있습니다" }, { status: 409 });
  }

  // 권한 확인
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", match.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !["ADMIN", "MANAGER"].includes(membership.role)) {
    return NextResponse.json({ error: "수정 권한이 없습니다" }, { status: 403 });
  }

  const { data: updated, error } = await supabase
    .from("matches")
    .update({ ...parsed.data, updated_at: new Date().toISOString() })
    .eq("id", id)
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ match: updated });
}

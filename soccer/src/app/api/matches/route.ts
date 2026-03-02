import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";

const createMatchSchema = z.object({
  team_id: z.string().uuid(),
  title: z.string().min(1, "경기명을 입력해주세요"),
  description: z.string().optional(),
  match_date: z.string().datetime(),
  location: z.string().optional(),
  opponent: z.string().optional(),
});

// GET /api/matches?team_id=xxx — 경기 목록 조회
export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const teamId = request.nextUrl.searchParams.get("team_id");
  if (!teamId) {
    return NextResponse.json({ error: "team_id가 필요합니다" }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 소속 팀 확인
  const { data: membership } = await supabase
    .from("team_members")
    .select("id")
    .eq("team_id", teamId)
    .eq("user_id", session.user.id)
    .single();

  if (!membership) {
    return NextResponse.json({ error: "팀에 소속되어 있지 않습니다" }, { status: 403 });
  }

  const status = request.nextUrl.searchParams.get("status");
  const sort = request.nextUrl.searchParams.get("sort") ?? "desc";
  const limitParam = request.nextUrl.searchParams.get("limit");
  const limit = limitParam ? Math.min(Math.max(parseInt(limitParam, 10) || 50, 1), 200) : 50;

  let query = supabase
    .from("matches")
    .select("*")
    .eq("team_id", teamId);

  if (status) {
    query = query.eq("status", status);
  }

  query = query.order("match_date", { ascending: sort === "asc" });
  query = query.limit(limit);

  const { data: matches, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ matches });
}

// POST /api/matches — 경기 생성
export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = createMatchSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0].message },
      { status: 400 }
    );
  }

  const supabase = await createPureClient();

  // 권한 확인: MANAGER 이상만 경기 생성 가능
  const { data: membership } = await supabase
    .from("team_members")
    .select("role")
    .eq("team_id", parsed.data.team_id)
    .eq("user_id", session.user.id)
    .single();

  if (!membership || !["ADMIN", "MANAGER"].includes(membership.role)) {
    return NextResponse.json({ error: "경기 생성 권한이 없습니다" }, { status: 403 });
  }

  // 경기 생성
  const { data: match, error: matchError } = await supabase
    .from("matches")
    .insert({
      ...parsed.data,
      status: "OPEN",
      created_by: session.user.id,
    })
    .select()
    .single();

  if (matchError) {
    return NextResponse.json({ error: matchError.message }, { status: 500 });
  }

  // 팀 멤버 전원에 대해 출석 레코드 자동 생성
  const { data: members } = await supabase
    .from("team_members")
    .select("user_id")
    .eq("team_id", parsed.data.team_id);

  if (members && members.length > 0) {
    const attendances = members.map((m) => ({
      match_id: match.id,
      user_id: m.user_id,
      status: "PENDING" as const,
    }));

    await supabase.from("attendances").insert(attendances);
  }

  return NextResponse.json({ match }, { status: 201 });
}

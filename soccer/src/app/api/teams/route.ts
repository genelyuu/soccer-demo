import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";

const createTeamSchema = z.object({
  name: z.string().min(1, "팀명을 입력해주세요"),
  description: z.string().optional(),
});

// GET /api/teams — 내가 소속된 팀 목록
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  const { data: memberships } = await supabase
    .from("team_members")
    .select("team_id, role, teams:team_id(id, name, description, logo_url, created_at)")
    .eq("user_id", session.user.id);

  const teams = (memberships ?? []).map((m) => ({
    ...(m as any).teams,
    my_role: m.role,
  }));

  return NextResponse.json({ teams });
}

// POST /api/teams — 팀 생성
export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = createTeamSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
  }

  const supabase = await createPureClient();

  // 팀 생성
  const { data: team, error: teamError } = await supabase
    .from("teams")
    .insert({
      name: parsed.data.name,
      description: parsed.data.description,
      created_by: session.user.id,
    })
    .select()
    .single();

  if (teamError) {
    return NextResponse.json({ error: teamError.message }, { status: 500 });
  }

  // 생성자를 ADMIN으로 자동 추가
  await supabase.from("team_members").insert({
    team_id: team.id,
    user_id: session.user.id,
    role: "ADMIN",
  });

  return NextResponse.json({ team }, { status: 201 });
}

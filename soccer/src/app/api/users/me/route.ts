import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";

const profileUpdateSchema = z.object({
  name: z.string().min(1, "이름은 필수입니다"),
  avatar_url: z
    .union([z.string().url("올바른 URL 형식이 아닙니다"), z.literal("")])
    .optional(),
});

// GET /api/users/me — 프로필 조회
export async function GET() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();

  const { data: user, error } = await supabase
    .from("users")
    .select("id, email, name, avatar_url, created_at, updated_at")
    .eq("id", session.user.id)
    .single();

  if (error || !user) {
    return NextResponse.json({ error: "사용자를 찾을 수 없습니다" }, { status: 404 });
  }

  return NextResponse.json({ user });
}

// PATCH /api/users/me — 프로필 수정 (이름, 아바타)
export async function PATCH(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = profileUpdateSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0].message },
      { status: 400 }
    );
  }

  const supabase = await createPureClient();

  const updateData: { name: string; avatar_url?: string | null; updated_at: string } = {
    name: parsed.data.name,
    updated_at: new Date().toISOString(),
  };

  // avatar_url이 빈 문자열이면 null로 저장, 값이 있으면 저장
  if (parsed.data.avatar_url !== undefined) {
    updateData.avatar_url = parsed.data.avatar_url === "" ? null : parsed.data.avatar_url;
  }

  const { data: user, error } = await supabase
    .from("users")
    .update(updateData)
    .eq("id", session.user.id)
    .select("id, email, name, avatar_url, created_at, updated_at")
    .single();

  if (error || !user) {
    return NextResponse.json({ error: "프로필 수정에 실패했습니다" }, { status: 500 });
  }

  return NextResponse.json({ user });
}

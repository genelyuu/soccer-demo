import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { createPureClient } from "@/lib/supabase/server";

export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const supabase = await createPureClient();
  const { data: user, error } = await supabase
    .from("users")
    .select("id, email, name, avatar_url, created_at")
    .eq("id", session.user.id)
    .single();

  if (error || !user) {
    return NextResponse.json({ error: "사용자를 찾을 수 없습니다" }, { status: 404 });
  }

  return NextResponse.json({ user });
}

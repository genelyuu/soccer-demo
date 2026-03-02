import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { z } from "zod";
import { getUsers, createUser } from "@/lib/supabase/users";

const createPlayerSchema = z.object({
  email: z.string().email("올바른 이메일 형식이 아닙니다"),
  name: z.string().min(1, "이름은 필수입니다"),
  avatar_url: z
    .union([z.string().url("올바른 URL 형식이 아닙니다"), z.literal("")])
    .optional(),
});

// GET /api/players — 사용자 목록 조회
export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const page = Number(searchParams.get("page") ?? "1");
  const limit = Number(searchParams.get("limit") ?? "20");
  const orderBy = (searchParams.get("orderBy") ?? "created_at") as "created_at" | "name" | "email";
  const ascending = searchParams.get("ascending") === "true";

  const result = await getUsers({ page, limit, orderBy, ascending });

  if (result.error) {
    return NextResponse.json({ error: result.error }, { status: 500 });
  }

  return NextResponse.json({
    players: result.data,
    count: result.count,
    page,
    limit,
  });
}

// POST /api/players — 사용자 생성
export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = createPlayerSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0].message },
      { status: 400 },
    );
  }

  const result = await createUser({
    email: parsed.data.email,
    name: parsed.data.name,
    avatar_url: parsed.data.avatar_url || undefined,
  });

  if (result.error) {
    const isDuplicate = result.error.includes("duplicate") || result.error.includes("unique");
    return NextResponse.json(
      { error: isDuplicate ? "이미 등록된 이메일입니다" : result.error },
      { status: isDuplicate ? 409 : 500 },
    );
  }

  return NextResponse.json({ player: result.data }, { status: 201 });
}

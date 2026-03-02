import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { z } from "zod";
import { getUserById, updateUser, deleteUser } from "@/lib/supabase/users";

const updatePlayerSchema = z.object({
  name: z.string().min(1, "이름은 필수입니다").optional(),
  avatar_url: z
    .union([z.string().url("올바른 URL 형식이 아닙니다"), z.literal(""), z.null()])
    .optional(),
});

type RouteContext = { params: Promise<{ id: string }> };

// GET /api/players/[id] — 단건 조회
export async function GET(
  _request: NextRequest,
  { params }: RouteContext,
) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const result = await getUserById(id);

  if (result.error || !result.data) {
    return NextResponse.json(
      { error: "사용자를 찾을 수 없습니다" },
      { status: 404 },
    );
  }

  return NextResponse.json({ player: result.data });
}

// PATCH /api/players/[id] — 수정
export async function PATCH(
  request: NextRequest,
  { params }: RouteContext,
) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  const body = await request.json();
  const parsed = updatePlayerSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0].message },
      { status: 400 },
    );
  }

  const updateData: { name?: string; avatar_url?: string | null } = {};
  if (parsed.data.name !== undefined) {
    updateData.name = parsed.data.name;
  }
  if (parsed.data.avatar_url !== undefined) {
    updateData.avatar_url = parsed.data.avatar_url === "" ? null : parsed.data.avatar_url;
  }

  const result = await updateUser(id, updateData);

  if (result.error || !result.data) {
    return NextResponse.json(
      { error: "프로필 수정에 실패했습니다" },
      { status: 500 },
    );
  }

  return NextResponse.json({ player: result.data });
}

// DELETE /api/players/[id] — 삭제
// DRD v3.0 경고: CASCADE 체인으로 최대 ~780행 연쇄 삭제
export async function DELETE(
  _request: NextRequest,
  { params }: RouteContext,
) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    return NextResponse.json({ error: "인증이 필요합니다" }, { status: 401 });
  }

  // 본인 확인: 자기 자신만 삭제 가능
  if (session.user.id !== id) {
    return NextResponse.json(
      { error: "본인 계정만 삭제할 수 있습니다" },
      { status: 403 },
    );
  }

  const result = await deleteUser(id);

  if (result.error) {
    return NextResponse.json(
      { error: "사용자 삭제에 실패했습니다" },
      { status: 500 },
    );
  }

  return NextResponse.json({ message: "사용자가 삭제되었습니다" });
}

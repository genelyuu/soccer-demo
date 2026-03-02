import { NextRequest, NextResponse } from "next/server";
import { createPureClient } from "@/lib/supabase/server";
import { z } from "zod";

const signupSchema = z.object({
  email: z.string().email("유효한 이메일을 입력해주세요"),
  password: z.string().min(6, "비밀번호는 최소 6자 이상이어야 합니다"),
  name: z.string().min(1, "이름을 입력해주세요"),
});

export async function POST(request: NextRequest) {
  const body = await request.json();
  const parsed = signupSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0].message },
      { status: 400 }
    );
  }

  const { email, password, name } = parsed.data;
  const supabase = await createPureClient();

  // Supabase Auth로 사용자 생성
  const { data: authData, error: authError } = await supabase.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
  });

  if (authError) {
    return NextResponse.json(
      { error: authError.message },
      { status: 409 }
    );
  }

  // users 테이블에 프로필 생성
  const { error: profileError } = await supabase
    .from("users")
    .insert({
      id: authData.user.id,
      email,
      name,
    });

  if (profileError) {
    return NextResponse.json(
      { error: "프로필 생성에 실패했습니다" },
      { status: 500 }
    );
  }

  return NextResponse.json(
    { user: { id: authData.user.id, email, name } },
    { status: 201 }
  );
}

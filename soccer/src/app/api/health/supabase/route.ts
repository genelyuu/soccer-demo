import { createPureClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    // 환경 변수 확인
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
      return NextResponse.json(
        {
          status: "error",
          message: "환경 변수가 설정되지 않았습니다",
          hasUrl: !!supabaseUrl,
          hasServiceRoleKey: !!serviceRoleKey,
        },
        { status: 500 }
      );
    }

    const supabase = await createPureClient();
    
    // 간단한 연결 테스트: RPC 호출 또는 간단한 쿼리
    const { data, error } = await supabase.rpc("version");

    // RPC가 없을 수 있으므로, 테이블 목록 조회로 대체
    if (error) {
      // 테이블 조회 시도
      const { error: tableError } = await supabase
        .from("teams")
        .select("id")
        .limit(1);

      if (tableError) {
        return NextResponse.json(
          {
            status: "partial",
            message: "Supabase 클라이언트는 생성되었지만 쿼리 실행 실패",
            connected: true,
            url: supabaseUrl,
            rpcError: error.message,
            tableError: tableError.message,
          },
          { status: 200 }
        );
      }
    }

    return NextResponse.json({
      status: "success",
      message: "Supabase 연결 성공",
      connected: true,
      url: supabaseUrl,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "error",
        message: "Supabase 연결 중 오류 발생",
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined,
      },
      { status: 500 }
    );
  }
}

"use client";

import { Suspense, useState } from "react";
import { Users } from "lucide-react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { PageTransition, StaggerList, StaggerItem } from "@/components/motion";
import { usePlayers } from "@/features/player/hooks/use-players";

export default function PlayersPage() {
  return (
    <Suspense
      fallback={
        <div className="container py-6 text-center text-muted-foreground">
          로딩 중...
        </div>
      }
    >
      <PlayersContent />
    </Suspense>
  );
}

function PlayersContent() {
  const { status } = useSession();
  const [page, setPage] = useState(1);
  const limit = 20;
  const { data, isLoading } = usePlayers(page, limit);

  if (status === "unauthenticated") {
    return (
      <div className="container py-6 space-y-6">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-2xl font-bold">회원 목록</h1>
        </div>
        <Card>
          <CardContent className="py-12 text-center space-y-4">
            <p className="text-muted-foreground">
              회원 목록을 보려면 로그인이 필요합니다.
            </p>
            <Link href="/auth/signin">
              <Button>로그인</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="container py-6 text-center text-muted-foreground">
        회원 목록을 불러오는 중...
      </div>
    );
  }

  const players = data?.players ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.ceil(totalCount / limit);

  return (
    <PageTransition className="container py-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <h1 className="text-2xl font-bold">회원 목록</h1>
          <span className="text-sm text-muted-foreground">({totalCount}명)</span>
        </div>
      </div>

      {/* 리스트 */}
      {players.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            등록된 회원이 없습니다.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">전체 회원</CardTitle>
          </CardHeader>
          <CardContent>
            <StaggerList className="divide-y">
              {players.map((player) => (
                <StaggerItem key={player.id}>
                  <div className="flex items-center gap-4 py-3">
                    <Avatar className="h-10 w-10">
                      <AvatarFallback className="text-sm">
                        {player.name.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{player.name}</p>
                      <p className="text-sm text-muted-foreground truncate">
                        {player.email}
                      </p>
                    </div>
                    <div className="text-xs text-muted-foreground hidden sm:block">
                      {new Date(player.created_at).toLocaleDateString("ko-KR")}
                    </div>
                  </div>
                </StaggerItem>
              ))}
            </StaggerList>
          </CardContent>
        </Card>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            이전
          </Button>
          <span className="text-sm text-muted-foreground">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            다음
          </Button>
        </div>
      )}
    </PageTransition>
  );
}

"use client";

import { Plus } from "lucide-react";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MatchList } from "@/features/match/components/match-list";
import { PageTransition } from "@/components/motion";
import { useTeamStore } from "@/lib/stores/team-store";
import { useMyRole } from "@/features/team/hooks/use-my-role";
import { canManageMatch } from "@/features/team/lib/authorization";
import Link from "next/link";

export default function MatchesPage() {
  const { status } = useSession();
  const selectedTeamId = useTeamStore((s) => s.selectedTeamId);
  const { role } = useMyRole();

  if (status === "unauthenticated") {
    return (
      <div className="container py-6 space-y-6">
        <h1 className="text-2xl font-bold">경기 일정</h1>
        <Card>
          <CardContent className="py-12 text-center space-y-4">
            <p className="text-muted-foreground">
              경기 일정을 보려면 로그인이 필요합니다.
            </p>
            <Link href="/auth/signin">
              <Button>로그인</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!selectedTeamId) {
    return (
      <div className="container py-6 space-y-6">
        <h1 className="text-2xl font-bold">경기 일정</h1>
        <p className="text-muted-foreground">
          팀을 선택해주세요. 상단 헤더에서 소속 팀을 선택할 수 있습니다.
        </p>
      </div>
    );
  }

  return (
    <PageTransition className="container py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">경기 일정</h1>
        {role && canManageMatch(role) && (
          <Link href="/matches/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              새 경기
            </Button>
          </Link>
        )}
      </div>
      <MatchList teamId={selectedTeamId} />
    </PageTransition>
  );
}

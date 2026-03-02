"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { differenceInCalendarDays, isSameMonth } from "date-fns";
import { Calendar, ChevronRight, Plus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PageTransition, StaggerList, StaggerItem } from "@/components/motion";
import { MatchCard } from "@/features/match/components/match-card";
import { useTeams } from "@/features/team/hooks/use-team";
import { useMatches } from "@/features/match/hooks/use-matches";
import { useTeamStore } from "@/lib/stores/team-store";

function GuestLanding() {
  return (
    <PageTransition className="container flex min-h-[60vh] flex-col items-center justify-center space-y-6 text-center">
      <h1 className="text-4xl font-bold tracking-tight">축구 동호회</h1>
      <p className="max-w-md text-lg text-muted-foreground">
        경기 일정 관리, 출석 투표, 기록까지 한곳에서 관리하세요.
      </p>
      <div className="flex gap-3">
        <Link href="/auth/signin">
          <Button size="lg" variant="outline">
            로그인
          </Button>
        </Link>
        <Link href="/auth/signup">
          <Button size="lg">회원가입</Button>
        </Link>
      </div>
    </PageTransition>
  );
}

function NoTeamCta() {
  return (
    <div className="container py-6 space-y-6">
      <h1 className="text-2xl font-bold">대시보드</h1>
      <Card>
        <CardHeader className="text-center">
          <Users className="mx-auto h-12 w-12 text-muted-foreground" />
          <CardTitle className="text-xl">소속된 팀이 없습니다</CardTitle>
          <CardDescription>
            팀을 생성하거나 초대를 받아 시작하세요.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Link href="/team">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              팀 만들기
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

function KpiCards({ teamId }: { teamId: string }) {
  const { data, isLoading } = useMatches(teamId);

  if (isLoading) {
    return (
      <div className="grid gap-4 grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  const matches = data?.matches ?? [];
  const now = new Date();

  // 이번 달 경기 수
  const thisMonthCount = matches.filter((m) =>
    isSameMonth(new Date(m.match_date), now),
  ).length;

  // 다음 경기 D-day
  const upcomingMatch = matches
    .filter((m) => m.status === "OPEN" || m.status === "CONFIRMED")
    .filter((m) => new Date(m.match_date) >= new Date(now.toDateString()))
    .sort(
      (a, b) =>
        new Date(a.match_date).getTime() - new Date(b.match_date).getTime(),
    )[0];

  let dDayLabel = "-";
  if (upcomingMatch) {
    const diff = differenceInCalendarDays(
      new Date(upcomingMatch.match_date),
      now,
    );
    dDayLabel = diff === 0 ? "오늘" : `D-${diff}`;
  }

  return (
    <div className="grid gap-4 grid-cols-3">
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">이번 달 경기</p>
          <p className="text-2xl font-bold font-mono">{thisMonthCount}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">다음 경기</p>
          <p className="text-2xl font-bold font-mono">{dDayLabel}</p>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <p className="text-sm text-muted-foreground">팀 멤버</p>
          <p className="text-2xl font-bold font-mono">-</p>
        </CardContent>
      </Card>
    </div>
  );
}

function UpcomingMatches({ teamId }: { teamId: string }) {
  const { data, isLoading } = useMatches(teamId);

  const upcoming = (data?.matches ?? [])
    .filter((m) => m.status === "OPEN" || m.status === "CONFIRMED")
    .sort(
      (a, b) =>
        new Date(a.match_date).getTime() - new Date(b.match_date).getTime(),
    )
    .slice(0, 3);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-lg bg-muted"
          />
        ))}
      </div>
    );
  }

  if (upcoming.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center py-8 text-center">
          <Calendar className="mb-2 h-10 w-10 text-muted-foreground" />
          <p className="text-muted-foreground">예정된 경기가 없습니다.</p>
          <Link href="/matches/new" className="mt-3">
            <Button variant="outline" size="sm">
              <Plus className="mr-2 h-4 w-4" />
              경기 만들기
            </Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <StaggerList className="space-y-3">
      {upcoming.map((match) => (
        <StaggerItem key={match.id}>
          <MatchCard match={match} />
        </StaggerItem>
      ))}
    </StaggerList>
  );
}

function TeamList() {
  const { data } = useTeams();
  const teams = data?.teams ?? [];

  if (teams.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">내 팀</CardTitle>
      </CardHeader>
      <CardContent>
        <StaggerList className="space-y-2">
          {teams.map((team) => (
            <StaggerItem key={team.id}>
              <Link
                href="/team"
                className="flex items-center justify-between rounded-md p-2 text-sm transition-colors hover:bg-muted"
              >
                <span className="font-medium">{team.name}</span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </Link>
            </StaggerItem>
          ))}
        </StaggerList>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const { data: teamsData, isLoading: teamsLoading } = useTeams();
  const selectedTeamId = useTeamStore((s) => s.selectedTeamId);

  const teams = teamsData?.teams ?? [];

  if (teamsLoading) {
    return (
      <div className="container py-6 space-y-6">
        <div className="h-8 w-40 animate-pulse rounded bg-muted" />
        <div className="grid gap-6 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (teams.length === 0) {
    return <NoTeamCta />;
  }

  return (
    <PageTransition className="container py-6 space-y-6">
      <h1 className="text-2xl font-bold">대시보드</h1>

      {selectedTeamId && <KpiCards teamId={selectedTeamId} />}

      <div className="grid gap-6 md:grid-cols-3">
        {/* 다가오는 경기 */}
        <div className="md:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">다가오는 경기</h2>
            <Link href="/matches">
              <Button variant="ghost" size="sm">
                전체 보기
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
          {selectedTeamId ? (
            <UpcomingMatches teamId={selectedTeamId} />
          ) : (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground">
                  팀을 선택해주세요.
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 사이드바: 팀 목록 */}
        <div className="space-y-4">
          <TeamList />
        </div>
      </div>
    </PageTransition>
  );
}

export default function HomePage() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return (
      <div className="container py-6">
        <div className="h-8 w-40 animate-pulse rounded bg-muted" />
      </div>
    );
  }

  if (!session?.user) {
    return <GuestLanding />;
  }

  return <Dashboard />;
}

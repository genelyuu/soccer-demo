"use client";

import { use } from "react";
import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { Calendar, MapPin, Users, ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition, StaggerList, StaggerItem } from "@/components/motion";
import { useMatch } from "@/features/match/hooks/use-matches";
import { VoteButtons } from "@/features/attendance/components/vote-buttons";
import { ConfirmButton } from "@/features/attendance/components/confirm-button";
import { useMyRole } from "@/features/team/hooks/use-my-role";
import { canManageMatch, canVoteAttendance } from "@/features/team/lib/authorization";
import { MATCH_STATUS_LABEL, MATCH_STATUS_COLOR } from "@/features/match/constants";
import { useSession } from "next-auth/react";
import Link from "next/link";

export default function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, isLoading, error } = useMatch(id);
  const { role } = useMyRole();
  const { data: session } = useSession();

  if (isLoading) {
    return <div className="container py-6 text-center text-muted-foreground">경기 정보를 불러오는 중...</div>;
  }

  if (error || !data) {
    return <div className="container py-6 text-center text-destructive">경기 정보를 불러오는데 실패했습니다</div>;
  }

  const { match, attendances } = data;
  const acceptedCount = attendances.filter((a) => a.status === "ACCEPTED").length;
  const declinedCount = attendances.filter((a) => a.status === "DECLINED").length;
  const pendingCount = attendances.filter((a) => a.status === "PENDING").length;

  const currentUserId = (session?.user as any)?.id;
  const myAttendance = attendances.find((a) => a.user_id === currentUserId);

  return (
    <PageTransition className="container py-6 space-y-6">
      <Link href="/matches">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="mr-2 h-4 w-4" />
          목록으로
        </Button>
      </Link>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-2xl">{match.title}</CardTitle>
            <Badge className={MATCH_STATUS_COLOR[match.status]} variant="secondary">
              {MATCH_STATUS_LABEL[match.status]}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-5 w-5" />
            <span>{format(new Date(match.match_date), "yyyy년 M월 d일 (EEE) HH:mm", { locale: ko })}</span>
          </div>
          {match.location && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <MapPin className="h-5 w-5" />
              <span>{match.location}</span>
            </div>
          )}
          {match.opponent && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Users className="h-5 w-5" />
              <span>vs {match.opponent}</span>
            </div>
          )}
          {match.description && (
            <p className="text-muted-foreground">{match.description}</p>
          )}
        </CardContent>
      </Card>

      {/* 출석 투표 (MEMBER 이상, OPEN 상태에서만) */}
      {match.status === "OPEN" && role && canVoteAttendance(role) && myAttendance && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">내 출석 투표</CardTitle>
          </CardHeader>
          <CardContent>
            <VoteButtons matchId={match.id} currentStatus={myAttendance.status} />
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>출석 투표 현황</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <span className="text-green-600 font-medium">참석 {acceptedCount}명</span>
            <span className="text-red-600 font-medium">불참 {declinedCount}명</span>
            <span className="text-yellow-600 font-medium">대기 {pendingCount}명</span>
          </div>
          {attendances.length === 0 ? (
            <p className="text-muted-foreground">투표 기록이 없습니다</p>
          ) : (
            <StaggerList className="space-y-2">
              {attendances.map((a) => (
                <StaggerItem key={a.id}>
                  <div className="flex items-center justify-between py-1 border-b last:border-0">
                    <span className="text-sm">{(a as any).users?.name ?? "알 수 없음"}</span>
                    <Badge variant="outline">
                      {a.status === "ACCEPTED" && "참석"}
                      {a.status === "DECLINED" && "불참"}
                      {a.status === "MAYBE" && "보류"}
                      {a.status === "PENDING" && "미응답"}
                    </Badge>
                  </div>
                </StaggerItem>
              ))}
            </StaggerList>
          )}
        </CardContent>
      </Card>

      {/* 경기 확정 버튼 (MANAGER 이상, OPEN 상태에서만) */}
      {match.status === "OPEN" && role && canManageMatch(role) && (
        <ConfirmButton matchId={match.id} />
      )}

      {match.status === "CONFIRMED" && (
        <Link href={`/matches/${match.id}/record`}>
          <Button className="w-full">기록실 바로가기</Button>
        </Link>
      )}
    </PageTransition>
  );
}

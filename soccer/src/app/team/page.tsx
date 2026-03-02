"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus } from "lucide-react";
import { PageTransition, StaggerList, StaggerItem } from "@/components/motion";
import { SkeletonCardGrid } from "@/components/ui/skeleton-card";
import { useTeams, useCreateTeam, useUpdateTeam, useDeleteTeam } from "@/features/team/hooks/use-team";
import { toast } from "@/hooks/use-toast";
import { TeamInfoCard } from "@/features/team/components/team-info-card";
import { TeamEditForm } from "@/features/team/components/team-edit-form";

export default function TeamPage() {
  const { status } = useSession();
  const { data, isLoading } = useTeams();
  const createTeam = useCreateTeam();
  const updateTeam = useUpdateTeam();
  const deleteTeam = useDeleteTeam();

  const [showCreate, setShowCreate] = useState(false);
  const [editingTeamId, setEditingTeamId] = useState<string | null>(null);

  if (status === "unauthenticated") {
    return (
      <div className="container py-6 space-y-6">
        <h1 className="text-2xl font-bold">내 팀</h1>
        <Card>
          <CardContent className="py-12 text-center space-y-4">
            <p className="text-muted-foreground">
              팀 정보를 보려면 로그인이 필요합니다.
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
      <div className="container py-6 space-y-6">
        <h1 className="text-2xl font-bold">내 팀</h1>
        <SkeletonCardGrid count={4} />
      </div>
    );
  }

  const teams = data?.teams ?? [];

  return (
    <PageTransition className="container py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">내 팀</h1>
        <Button size="sm" onClick={() => setShowCreate((v) => !v)}>
          <Plus className="mr-2 h-4 w-4" />
          팀 만들기
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>새 팀 만들기</CardTitle>
          </CardHeader>
          <CardContent>
            <TeamEditForm
              submitLabel="만들기"
              isPending={createTeam.isPending}
              onSubmit={(values) => {
                createTeam.mutate({ name: values.name, description: values.description }, {
                  onSuccess: () => {
                    setShowCreate(false);
                    toast({ title: "팀 생성 완료", description: "새 팀이 생성되었습니다." });
                  },
                  onError: () => {
                    toast({ title: "팀 생성 실패", description: "팀 생성 중 오류가 발생했습니다.", variant: "destructive" });
                  },
                });
              }}
            />
          </CardContent>
        </Card>
      )}

      {teams.length === 0 && !showCreate ? (
        <p className="text-muted-foreground">소속된 팀이 없습니다</p>
      ) : (
        <StaggerList className="grid gap-4 md:grid-cols-2">
          {teams.map((team) =>
            editingTeamId === team.id ? (
              <StaggerItem key={team.id}>
                <Card>
                  <CardHeader>
                    <CardTitle>팀 수정</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <TeamEditForm
                      defaultValues={{ name: team.name, description: team.description ?? "" }}
                      isPending={updateTeam.isPending}
                      onSubmit={({ name, description }) => {
                        updateTeam.mutate(
                          { teamId: team.id, name, description },
                          {
                            onSuccess: () => {
                              setEditingTeamId(null);
                              toast({ title: "팀 수정 완료", description: "팀 정보가 수정되었습니다." });
                            },
                            onError: () => {
                              toast({ title: "팀 수정 실패", description: "팀 수정 중 오류가 발생했습니다.", variant: "destructive" });
                            },
                          },
                        );
                      }}
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      onClick={() => setEditingTeamId(null)}
                    >
                      취소
                    </Button>
                  </CardContent>
                </Card>
              </StaggerItem>
            ) : (
              <StaggerItem key={team.id}>
                <TeamInfoCard
                  team={team}
                  onEdit={() => setEditingTeamId(team.id)}
                  onDelete={() => {
                    if (confirm("정말 이 팀을 삭제하시겠습니까?")) {
                      deleteTeam.mutate(team.id, {
                        onSuccess: () => {
                          toast({ title: "팀 삭제 완료", description: "팀이 삭제되었습니다." });
                        },
                        onError: () => {
                          toast({ title: "팀 삭제 실패", description: "팀 삭제 중 오류가 발생했습니다.", variant: "destructive" });
                        },
                      });
                    }
                  }}
                />
              </StaggerItem>
            ),
          )}
        </StaggerList>
      )}
    </PageTransition>
  );
}

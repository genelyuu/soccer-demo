"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/motion";
import { useMembers, useAddMember, useUpdateMemberRole, useRemoveMember } from "@/features/team/hooks/use-members";
import { MemberList } from "@/features/team/components/member-list";
import { MemberAddForm } from "@/features/team/components/member-add-form";
import { canModifyMembers } from "@/features/team/lib/authorization";
import { toast } from "@/hooks/use-toast";
import Link from "next/link";

export default function MembersPage() {
  return (
    <Suspense fallback={<div className="container py-6 text-center text-muted-foreground">로딩 중...</div>}>
      <MembersContent />
    </Suspense>
  );
}

function MembersContent() {
  const searchParams = useSearchParams();
  const teamId = searchParams.get("team_id") ?? "";

  const { data, isLoading } = useMembers(teamId);
  const addMember = useAddMember(teamId);
  const updateRole = useUpdateMemberRole(teamId);
  const removeMember = useRemoveMember(teamId);

  const [addError, setAddError] = useState("");

  if (!teamId) {
    return (
      <div className="container py-6 text-center text-destructive">
        팀 ID가 필요합니다
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="container py-6 text-center text-muted-foreground">
        멤버 목록을 불러오는 중...
      </div>
    );
  }

  const members = data?.members ?? [];
  const myRole = data?.my_role;
  const canManage = myRole ? canModifyMembers(myRole) : false;

  return (
    <PageTransition className="container py-6 space-y-6">
      <Link href="/team">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="mr-2 h-4 w-4" />
          팀 목록으로
        </Button>
      </Link>

      {myRole && (
        <MemberList
          members={members}
          myRole={myRole}
          onRoleChange={(memberId, role) => updateRole.mutate({ memberId, role }, {
            onSuccess: () => toast({ title: "역할 변경 완료", description: "멤버 역할이 변경되었습니다." }),
            onError: () => toast({ title: "역할 변경 실패", description: "역할 변경 중 오류가 발생했습니다.", variant: "destructive" }),
          })}
          onRemove={(memberId) => {
            if (confirm("이 멤버를 제거하시겠습니까?")) {
              removeMember.mutate(memberId, {
                onSuccess: () => toast({ title: "멤버 제거 완료", description: "멤버가 제거되었습니다." }),
                onError: () => toast({ title: "멤버 제거 실패", description: "멤버 제거 중 오류가 발생했습니다.", variant: "destructive" }),
              });
            }
          }}
        />
      )}

      {canManage && (
        <MemberAddForm
          isPending={addMember.isPending}
          error={addError}
          onSubmit={(email) => {
            setAddError("");
            addMember.mutate(
              { email },
              {
                onSuccess: () => {
                  toast({ title: "멤버 추가 완료", description: "멤버가 추가되었습니다." });
                },
                onError: (err: any) => {
                  setAddError(err.response?.data?.error ?? "멤버 추가에 실패했습니다");
                  toast({ title: "멤버 추가 실패", description: "멤버 추가 중 오류가 발생했습니다.", variant: "destructive" });
                },
              },
            );
          }}
        />
      )}
    </PageTransition>
  );
}

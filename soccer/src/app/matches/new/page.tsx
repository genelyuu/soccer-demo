"use client";

import { CreateMatchForm } from "@/features/match/components/create-match-form";
import { useTeamStore } from "@/lib/stores/team-store";

export default function NewMatchPage() {
  const selectedTeamId = useTeamStore((s) => s.selectedTeamId);

  if (!selectedTeamId) {
    return (
      <div className="container py-6">
        <p className="text-muted-foreground">
          팀을 선택해주세요. 상단 헤더에서 소속 팀을 선택할 수 있습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="container py-6">
      <CreateMatchForm teamId={selectedTeamId} />
    </div>
  );
}

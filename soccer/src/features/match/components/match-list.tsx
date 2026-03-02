"use client";

import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import { StaggerList, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SkeletonCardGrid } from "@/components/ui/skeleton-card";
import { useMatches } from "../hooks/use-matches";
import { MatchCard } from "./match-card";
import { MATCH_STATUS_LABEL } from "../constants";
import type { MatchStatus } from "@/lib/types";

type StatusFilter = "ALL" | MatchStatus;

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "ALL", label: "전체" },
  { value: "OPEN", label: MATCH_STATUS_LABEL.OPEN },
  { value: "CONFIRMED", label: MATCH_STATUS_LABEL.CONFIRMED },
  { value: "COMPLETED", label: MATCH_STATUS_LABEL.COMPLETED },
  { value: "CANCELLED", label: MATCH_STATUS_LABEL.CANCELLED },
];

interface MatchListProps {
  teamId: string;
}

export function MatchList({ teamId }: MatchListProps) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  const { data, isLoading, error } = useMatches(teamId, {
    status: statusFilter === "ALL" ? undefined : statusFilter,
    sort: sortOrder,
  });

  const matches = data?.matches ?? [];

  if (isLoading) {
    return <SkeletonCardGrid count={6} />;
  }

  if (error) {
    return <div className="text-center py-8 text-destructive">경기 목록을 불러오는데 실패했습니다</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-1">
          {STATUS_OPTIONS.map((opt) => (
            <Badge
              key={opt.value}
              variant={statusFilter === opt.value ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setStatusFilter(opt.value)}
            >
              {opt.label}
            </Badge>
          ))}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="ml-auto"
          onClick={() => setSortOrder((prev) => (prev === "desc" ? "asc" : "desc"))}
        >
          <ArrowUpDown className="mr-1 h-4 w-4" />
          {sortOrder === "desc" ? "최신순" : "오래된순"}
        </Button>
      </div>

      {matches.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          {statusFilter === "ALL" ? "등록된 경기가 없습니다" : "해당 조건의 경기가 없습니다"}
        </div>
      ) : (
        <StaggerList className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {matches.map((match) => (
            <StaggerItem key={match.id}>
              <MatchCard match={match} />
            </StaggerItem>
          ))}
        </StaggerList>
      )}
    </div>
  );
}

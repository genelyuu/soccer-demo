"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, X, HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { voteAttendance } from "../api";
import type { AttendanceStatus } from "@/lib/types";

interface VoteButtonsProps {
  matchId: string;
  currentStatus: AttendanceStatus;
}

export function VoteButtons({ matchId, currentStatus }: VoteButtonsProps) {
  const queryClient = useQueryClient();

  const voteMutation = useMutation({
    mutationFn: (status: "ACCEPTED" | "DECLINED" | "MAYBE") =>
      voteAttendance(matchId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["match", matchId] });
      toast({ title: "투표 완료", description: "출석 투표가 반영되었습니다." });
    },
    onError: () => {
      toast({ title: "투표 실패", description: "투표 처리 중 오류가 발생했습니다.", variant: "destructive" });
    },
  });

  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        variant={currentStatus === "ACCEPTED" ? "default" : "outline"}
        onClick={() => voteMutation.mutate("ACCEPTED")}
        disabled={voteMutation.isPending}
      >
        <Check className="mr-1 h-4 w-4" />
        참석
      </Button>
      <Button
        size="sm"
        variant={currentStatus === "DECLINED" ? "destructive" : "outline"}
        onClick={() => voteMutation.mutate("DECLINED")}
        disabled={voteMutation.isPending}
      >
        <X className="mr-1 h-4 w-4" />
        불참
      </Button>
      <Button
        size="sm"
        variant={currentStatus === "MAYBE" ? "secondary" : "outline"}
        onClick={() => voteMutation.mutate("MAYBE")}
        disabled={voteMutation.isPending}
      >
        <HelpCircle className="mr-1 h-4 w-4" />
        보류
      </Button>
    </div>
  );
}

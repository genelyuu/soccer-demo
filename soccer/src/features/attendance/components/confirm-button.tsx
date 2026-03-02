"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";
import { confirmMatch } from "../api";

interface ConfirmButtonProps {
  matchId: string;
}

export function ConfirmButton({ matchId }: ConfirmButtonProps) {
  const queryClient = useQueryClient();

  const confirmMutation = useMutation({
    mutationFn: () => confirmMatch(matchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["match", matchId] });
      toast({ title: "경기 확정", description: "경기가 확정되고 기록실이 생성되었습니다." });
    },
    onError: () => {
      toast({ title: "경기 확정 실패", description: "경기 확정 중 오류가 발생했습니다.", variant: "destructive" });
    },
  });

  return (
    <Button
      onClick={() => confirmMutation.mutate()}
      disabled={confirmMutation.isPending}
      className="w-full"
    >
      <CheckCircle className="mr-2 h-4 w-4" />
      {confirmMutation.isPending ? "확정 중..." : "경기 확정 (기록실 자동 생성)"}
    </Button>
  );
}

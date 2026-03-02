"use client";

import { use, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Lock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { PageTransition } from "@/components/motion";
import { toast } from "@/hooks/use-toast";
import { getRecordRoom, submitRecord, closeRecordRoom, type RecordPayload } from "@/features/record/api";
import { useMyRole } from "@/features/team/hooks/use-my-role";
import { canWriteRecord } from "@/features/team/lib/authorization";
import Link from "next/link";

export default function RecordRoomPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: matchId } = use(params);
  const queryClient = useQueryClient();
  const { role } = useMyRole();
  const canEdit = role ? canWriteRecord(role) : false;

  const { data, isLoading, error } = useQuery({
    queryKey: ["record-room", matchId],
    queryFn: () => getRecordRoom(matchId),
  });

  const submitMutation = useMutation({
    mutationFn: (payload: RecordPayload) => submitRecord(matchId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["record-room", matchId] });
      setEditingUserId(null);
      toast({ title: "기록 저장 완료", description: "선수 기록이 저장되었습니다." });
    },
    onError: () => {
      toast({ title: "기록 저장 실패", description: "기록 저장 중 오류가 발생했습니다.", variant: "destructive" });
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => closeRecordRoom(matchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["record-room", matchId] });
      queryClient.invalidateQueries({ queryKey: ["match", matchId] });
      toast({ title: "기록실 마감 완료", description: "기록실이 마감되고 경기가 완료 처리되었습니다." });
    },
    onError: () => {
      toast({ title: "기록실 마감 실패", description: "기록실 마감 중 오류가 발생했습니다.", variant: "destructive" });
    },
  });

  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [form, setForm] = useState<RecordPayload>({
    user_id: "",
    goals: 0,
    assists: 0,
    yellow_cards: 0,
    red_cards: 0,
    memo: "",
  });

  if (isLoading) {
    return <div className="container py-6 text-center text-muted-foreground">기록실을 불러오는 중...</div>;
  }

  if (error || !data) {
    return (
      <div className="container py-6 text-center">
        <p className="text-destructive mb-4">기록실이 아직 생성되지 않았습니다. 경기를 먼저 확정해주세요.</p>
        <Link href={`/matches/${matchId}`}>
          <Button variant="outline">경기 상세로 돌아가기</Button>
        </Link>
      </div>
    );
  }

  const { record_room, records } = data;

  const startEdit = (userId: string, userName: string) => {
    const existing = records.find((r) => r.user_id === userId);
    setEditingUserId(userId);
    setForm({
      user_id: userId,
      goals: existing?.goals ?? 0,
      assists: existing?.assists ?? 0,
      yellow_cards: existing?.yellow_cards ?? 0,
      red_cards: existing?.red_cards ?? 0,
      memo: existing?.memo ?? "",
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitMutation.mutate(form);
  };

  return (
    <PageTransition className="container py-6 space-y-6">
      <Link href={`/matches/${matchId}`}>
        <Button variant="ghost" size="sm">
          <ArrowLeft className="mr-2 h-4 w-4" />
          경기 상세로
        </Button>
      </Link>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>기록실</CardTitle>
            <Badge variant={record_room.status === "OPEN" ? "default" : "secondary"}>
              {record_room.status === "OPEN" ? "입력 가능" : "마감됨"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {records.length === 0 ? (
            <p className="text-muted-foreground">아직 입력된 기록이 없습니다</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-left">선수</TableHead>
                  <TableHead className="text-center">득점</TableHead>
                  <TableHead className="text-center">어시스트</TableHead>
                  <TableHead className="text-center">경고</TableHead>
                  <TableHead className="text-center">퇴장</TableHead>
                  <TableHead className="text-left">메모</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {records.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{r.users?.name ?? "알 수 없음"}</TableCell>
                    <TableCell className="text-center">{r.goals}</TableCell>
                    <TableCell className="text-center">{r.assists}</TableCell>
                    <TableCell className="text-center">{r.yellow_cards}</TableCell>
                    <TableCell className="text-center">{r.red_cards}</TableCell>
                    <TableCell className="text-muted-foreground">{r.memo || "-"}</TableCell>
                    <TableCell>
                      {record_room.status === "OPEN" && canEdit && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => startEdit(r.user_id, r.users?.name)}
                        >
                          수정
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {record_room.status === "OPEN" && canEdit && editingUserId && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">기록 입력</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>득점</Label>
                  <Input
                    type="number"
                    min={0}
                    value={form.goals}
                    onChange={(e) => setForm({ ...form, goals: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>어시스트</Label>
                  <Input
                    type="number"
                    min={0}
                    value={form.assists}
                    onChange={(e) => setForm({ ...form, assists: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>경고</Label>
                  <Input
                    type="number"
                    min={0}
                    value={form.yellow_cards}
                    onChange={(e) => setForm({ ...form, yellow_cards: parseInt(e.target.value) || 0 })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>퇴장</Label>
                  <Input
                    type="number"
                    min={0}
                    value={form.red_cards}
                    onChange={(e) => setForm({ ...form, red_cards: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>메모</Label>
                <Textarea
                  value={form.memo}
                  onChange={(e) => setForm({ ...form, memo: e.target.value })}
                  placeholder="경기 메모"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit" disabled={submitMutation.isPending}>
                  {submitMutation.isPending ? "저장 중..." : "저장"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setEditingUserId(null)}>
                  취소
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {record_room.status === "OPEN" && canEdit && (
        <Button
          variant="destructive"
          className="w-full"
          onClick={() => {
            if (confirm("기록실을 마감하시겠습니까? 마감 후에는 기록을 수정할 수 없으며, 경기가 완료 상태로 전환됩니다.")) {
              closeMutation.mutate();
            }
          }}
          disabled={closeMutation.isPending}
        >
          <Lock className="mr-2 h-4 w-4" />
          {closeMutation.isPending ? "마감 처리 중..." : "기록실 마감 (경기 완료)"}
        </Button>
      )}
    </PageTransition>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/hooks/use-toast";
import { useCreateMatch } from "../hooks/use-matches";

const formSchema = z.object({
  title: z.string().min(1, "경기명을 입력해주세요"),
  description: z.string().optional(),
  match_date: z.string().min(1, "경기 일시를 선택해주세요"),
  location: z.string().optional(),
  opponent: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateMatchFormProps {
  teamId: string;
}

export function CreateMatchForm({ teamId }: CreateMatchFormProps) {
  const router = useRouter();
  const createMatch = useCreateMatch();
  const [error, setError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (values: FormValues) => {
    setError("");
    try {
      const matchDate = new Date(values.match_date).toISOString();
      await createMatch.mutateAsync({
        team_id: teamId,
        title: values.title,
        description: values.description,
        match_date: matchDate,
        location: values.location,
        opponent: values.opponent,
      });
      toast({ title: "경기 생성 완료", description: "새 경기가 등록되었습니다." });
      router.push("/matches");
    } catch (err: any) {
      setError(err.response?.data?.error ?? "경기 생성에 실패했습니다");
      toast({ title: "경기 생성 실패", description: "경기 생성 중 오류가 발생했습니다.", variant: "destructive" });
    }
  };

  return (
    <Card className="max-w-lg mx-auto">
      <CardHeader>
        <CardTitle>새 경기 등록</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">경기명 *</Label>
            <Input id="title" {...register("title")} placeholder="예: 주말 리그전" />
            {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="match_date">경기 일시 *</Label>
            <Input id="match_date" type="datetime-local" {...register("match_date")} />
            {errors.match_date && <p className="text-sm text-destructive">{errors.match_date.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">장소</Label>
            <Input id="location" {...register("location")} placeholder="예: 잠실 운동장" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="opponent">상대팀</Label>
            <Input id="opponent" {...register("opponent")} placeholder="예: FC 태풍" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">설명</Label>
            <Textarea id="description" {...register("description")} placeholder="경기에 대한 추가 정보" />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex gap-2">
            <Button type="submit" disabled={createMatch.isPending}>
              {createMatch.isPending ? "생성 중..." : "경기 등록"}
            </Button>
            <Button type="button" variant="outline" onClick={() => router.back()}>
              취소
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            * 경기 생성 시 팀 멤버 전원에게 출석 투표가 자동으로 생성됩니다
          </p>
        </form>
      </CardContent>
    </Card>
  );
}

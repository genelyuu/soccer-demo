"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format } from "date-fns";
import { ko } from "date-fns/locale";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage,
} from "@/components/ui/form";
import { toast } from "@/hooks/use-toast";
import { PageTransition } from "@/components/motion";
import type { User } from "@/lib/types";

const profileSchema = z.object({
  name: z.string().min(1, "이름을 입력해주세요"),
  avatar_url: z.union([z.string().url("올바른 URL 형식이 아닙니다"), z.literal("")]).optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

async function getProfile(): Promise<{ user: User }> {
  const { data } = await axios.get("/api/users/me");
  return data;
}

async function updateProfile(payload: ProfileFormValues): Promise<{ user: User }> {
  const { data } = await axios.patch("/api/users/me", payload);
  return data;
}

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["profile"],
    queryFn: getProfile,
  });

  const updateMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: (result) => {
      queryClient.setQueryData(["profile"], result);
      toast({ title: "프로필 수정 완료", description: "프로필 정보가 저장되었습니다." });
    },
    onError: () => {
      toast({ title: "프로필 수정 실패", description: "프로필 저장 중 오류가 발생했습니다.", variant: "destructive" });
    },
  });

  if (isLoading) {
    return (
      <div className="container py-6 max-w-lg mx-auto space-y-6">
        <Skeleton className="h-8 w-32" />
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div className="flex items-center gap-4">
              <Skeleton className="h-16 w-16 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-48" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container py-6 text-center text-destructive">
        프로필을 불러올 수 없습니다. 로그인이 필요합니다.
      </div>
    );
  }

  return (
    <PageTransition className="container py-6 max-w-lg mx-auto space-y-6">
      <h1 className="text-2xl font-bold">내 정보</h1>
      <ProfileInfo user={data.user} />
      <ProfileEditForm
        user={data.user}
        isPending={updateMutation.isPending}
        onSubmit={(values) => updateMutation.mutate(values)}
      />
    </PageTransition>
  );
}

function ProfileInfo({ user }: { user: User }) {
  const initials = user.name.slice(0, 2);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">프로필 정보</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            {user.avatar_url && <AvatarImage src={user.avatar_url} alt={user.name} />}
            <AvatarFallback className="text-lg">{initials}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium text-lg">{user.name}</p>
            <p className="text-sm text-muted-foreground">{user.email}</p>
          </div>
        </div>
        <div className="text-sm text-muted-foreground">
          가입일: {format(new Date(user.created_at), "yyyy년 M월 d일", { locale: ko })}
        </div>
      </CardContent>
    </Card>
  );
}

function ProfileEditForm({
  user,
  isPending,
  onSubmit,
}: {
  user: User;
  isPending: boolean;
  onSubmit: (values: ProfileFormValues) => void;
}) {
  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user.name,
      avatar_url: user.avatar_url ?? "",
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">프로필 수정</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>이름</FormLabel>
                  <FormControl>
                    <Input placeholder="이름을 입력하세요" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="avatar_url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>아바타 URL</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="https://example.com/avatar.jpg"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={isPending}>
              {isPending ? "저장 중..." : "저장"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}

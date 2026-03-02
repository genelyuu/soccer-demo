"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import { useQuery } from "@tanstack/react-query";
import { getMe } from "../api";

export function useAuth() {
  const { data: session, status } = useSession();

  const { data: profile } = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    enabled: status === "authenticated",
  });

  return {
    session,
    profile: profile?.user ?? null,
    isAuthenticated: status === "authenticated",
    isLoading: status === "loading",
    signIn,
    signOut,
  };
}

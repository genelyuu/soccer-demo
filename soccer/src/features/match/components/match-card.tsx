"use client";

import { format } from "date-fns";
import { ko } from "date-fns/locale";
import { Calendar, MapPin, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MATCH_STATUS_LABEL, MATCH_STATUS_COLOR } from "../constants";
import type { Match } from "@/lib/types";
import Link from "next/link";

interface MatchCardProps {
  match: Match;
}

export function MatchCard({ match }: MatchCardProps) {
  return (
    <Link href={`/matches/${match.id}`}>
      <Card className="cursor-pointer transition-shadow hover:shadow-md">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{match.title}</CardTitle>
            <Badge className={MATCH_STATUS_COLOR[match.status]} variant="secondary">
              {MATCH_STATUS_LABEL[match.status]}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            <span>{format(new Date(match.match_date), "yyyy년 M월 d일 (EEE) HH:mm", { locale: ko })}</span>
          </div>
          {match.location && (
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              <span>{match.location}</span>
            </div>
          )}
          {match.opponent && (
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span>vs {match.opponent}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

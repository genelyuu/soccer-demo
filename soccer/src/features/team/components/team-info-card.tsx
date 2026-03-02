"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users, Settings, Trash2 } from "lucide-react";
import { ROLE_LABEL, ROLE_COLOR } from "../constants";
import type { TeamWithRole } from "../api";
import type { TeamRole } from "@/lib/types";
import { canModifyTeam, canDeleteTeam } from "../lib/authorization";
import Link from "next/link";

interface TeamInfoCardProps {
  team: TeamWithRole;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function TeamInfoCard({ team, onEdit, onDelete }: TeamInfoCardProps) {
  const role = team.my_role;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{team.name}</CardTitle>
          <Badge className={ROLE_COLOR[role]} variant="secondary">
            {ROLE_LABEL[role] ?? role}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {team.description && (
          <p className="text-sm text-muted-foreground">{team.description}</p>
        )}
        <div className="flex items-center gap-2 flex-wrap">
          <Link href={`/team/members?team_id=${team.id}`}>
            <Button variant="outline" size="sm">
              <Users className="mr-2 h-4 w-4" />
              멤버 관리
            </Button>
          </Link>
          {canModifyTeam(role) && onEdit && (
            <Button variant="outline" size="sm" onClick={onEdit}>
              <Settings className="mr-2 h-4 w-4" />
              팀 수정
            </Button>
          )}
          {canDeleteTeam(role) && onDelete && (
            <Button variant="destructive" size="sm" onClick={onDelete}>
              <Trash2 className="mr-2 h-4 w-4" />
              팀 삭제
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

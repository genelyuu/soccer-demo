"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StaggerList, StaggerItem } from "@/components/motion";
import { Trash2 } from "lucide-react";
import { ROLE_LABEL, ROLE_COLOR } from "../constants";
import { MemberRoleSelect } from "./member-role-select";
import { canChangeRole, canRemoveMember } from "../lib/authorization";
import type { MemberWithUser } from "../api";
import type { TeamRole } from "@/lib/types";

interface MemberListProps {
  members: MemberWithUser[];
  myRole: TeamRole;
  onRoleChange?: (memberId: string, role: TeamRole) => void;
  onRemove?: (memberId: string) => void;
}

export function MemberList({ members, myRole, onRoleChange, onRemove }: MemberListProps) {
  const isAdmin = canChangeRole(myRole);

  return (
    <Card>
      <CardHeader>
        <CardTitle>멤버 목록 ({members.length}명)</CardTitle>
      </CardHeader>
      <CardContent>
        <StaggerList className="space-y-3">
          {members.map((m) => (
            <StaggerItem key={m.id}>
              <div className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <span className="font-medium">{m.users?.name ?? "알 수 없음"}</span>
                  <span className="text-sm text-muted-foreground ml-2">{m.users?.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  {isAdmin && onRoleChange ? (
                    <MemberRoleSelect
                      value={m.role as TeamRole}
                      onValueChange={(role) => onRoleChange(m.id, role)}
                    />
                  ) : (
                    <Badge className={ROLE_COLOR[m.role as TeamRole]} variant="secondary">
                      {ROLE_LABEL[m.role as TeamRole] ?? m.role}
                    </Badge>
                  )}
                  {canRemoveMember(myRole, m.role as TeamRole) && onRemove && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onRemove(m.id)}
                      className="h-8 w-8 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerList>
      </CardContent>
    </Card>
  );
}

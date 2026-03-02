"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ROLE_OPTIONS } from "../constants";
import type { TeamRole } from "@/lib/types";

interface MemberRoleSelectProps {
  value: TeamRole;
  onValueChange: (role: TeamRole) => void;
  disabled?: boolean;
}

export function MemberRoleSelect({
  value,
  onValueChange,
  disabled,
}: MemberRoleSelectProps) {
  return (
    <Select
      value={value}
      onValueChange={(v) => onValueChange(v as TeamRole)}
      disabled={disabled}
    >
      <SelectTrigger className="w-[120px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {ROLE_OPTIONS.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

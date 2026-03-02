import axios from "axios";
import type { Attendance, AttendanceStatus } from "@/lib/types";

export async function voteAttendance(
  matchId: string,
  status: Exclude<AttendanceStatus, "PENDING">
): Promise<{ attendance: Attendance }> {
  const { data } = await axios.patch(`/api/matches/${matchId}/attendance`, { status });
  return data;
}

export async function confirmMatch(matchId: string) {
  const { data } = await axios.patch(`/api/matches/${matchId}/confirm`);
  return data;
}
